from __future__ import annotations

from fastaction.domain.enums import InstructionAction
from fastaction.planner.candidate_retriever import CandidateRetriever
from fastaction.planner.parameter_resolver import ParameterResolver
from fastaction.planner.policy_checker import PolicyChecker
from fastaction.schemas import APIDefinition, ChatRequest, Instruction
from fastaction.schemas.instruction import (
    CandidateSummary,
    ClarifyPayload,
    InstructionAPIRef,
    InstructionRender,
    MissingParamDetail,
    PendingInstruction,
)


class DeterministicPlanner:
    def __init__(
        self,
        *,
        retriever: CandidateRetriever | None = None,
        parameter_resolver: ParameterResolver | None = None,
        policy_checker: PolicyChecker | None = None,
        min_confidence: float = 0.2,
    ):
        self.retriever = retriever or CandidateRetriever()
        self.parameter_resolver = parameter_resolver or ParameterResolver()
        self.policy_checker = policy_checker or PolicyChecker()
        self.min_confidence = min_confidence

    def plan(self, request: ChatRequest, apis: list[APIDefinition]) -> Instruction:
        candidates = self.retriever.retrieve(request.text, apis)
        summaries = [
            CandidateSummary(api_id=item.api.id, score=item.score, reason=item.reason)
            for item in candidates
        ]
        if not candidates:
            return Instruction(
                action=InstructionAction.REJECT,
                confidence=0.0,
                decision_reason={
                    "zh": "没有命中任何已注册 API。",
                    "en": "No registered API matched the user request.",
                },
                reply={
                    "zh": "当前没有可执行的已注册能力。",
                    "en": "No registered capability can handle this request.",
                },
                candidates=[],
            )

        best = candidates[0]
        confidence = min(1.0, best.score / 5.0)
        if confidence < self.min_confidence:
            return Instruction(
                action=InstructionAction.CLARIFY,
                confidence=confidence,
                decision_reason={
                    "zh": "候选能力置信度不足，需要澄清。",
                    "en": "Candidate confidence is too low; clarification is required.",
                },
                reply={"zh": "您想让我处理哪类信息？", "en": "What kind of information should I handle?"},
                candidates=summaries,
            )

        api = best.api
        api_ref = _api_ref(api)
        params, missing = self.parameter_resolver.resolve(
            api,
            context=request.context,
            provided_params=request.params,
            text=request.text,
        )
        if missing:
            return Instruction(
                action=InstructionAction.CLARIFY,
                confidence=confidence,
                decision_reason={
                    "zh": "已命中 API，但缺少必填参数。",
                    "en": "API matched, but required parameters are missing.",
                },
                reply={"zh": "还需要补充一些信息。", "en": "I need a bit more information."},
                api=api_ref,
                params=params,
                risk=api.policy.risk,
                render=InstructionRender(
                    card_type="missing_params_card",
                    fallback_card_type="picker_card",
                    state="missing_params",
                ),
                clarify=ClarifyPayload(
                    missing_params=missing,
                    missing_param_details=_missing_param_details(api, missing),
                    options_api=_find_options_api(missing[0], apis),
                ),
                pending_instruction=PendingInstruction(
                    action=InstructionAction.INVOKE_API,
                    api_id=api.id,
                    params=params,
                ),
                candidates=summaries,
            )

        render = InstructionRender(
            card_type=api.render.card_type,
            fallback_card_type=api.render.fallback_card_type,
            field_bindings=api.render.field_bindings,
        )

        if self.policy_checker.requires_confirmation(api):
            return Instruction(
                action=InstructionAction.CONFIRM,
                confidence=confidence,
                decision_reason={
                    "zh": "该 API 风险策略要求执行前确认。",
                    "en": "The API policy requires confirmation before execution.",
                },
                api=api_ref,
                params=params,
                risk=api.policy.risk,
                render=InstructionRender(card_type="confirm_card", state="success"),
                reply={"zh": "这个操作需要您确认后再执行。", "en": "Please confirm before I execute this action."},
                pending_instruction=PendingInstruction(
                    action=InstructionAction.INVOKE_API,
                    api_id=api.id,
                    params=params,
                ),
                candidates=summaries,
            )

        return Instruction(
            action=InstructionAction.INVOKE_API,
            confidence=confidence,
            decision_reason={
                "zh": "命中已注册 API，参数已补齐，策略允许直接执行。",
                "en": "A registered API matched, parameters are resolved, and policy allows execution.",
            },
            api=api_ref,
            params=params,
            risk=api.policy.risk,
            render=render,
            reply={"zh": "我来处理这个请求。", "en": "I will handle this request."},
            candidates=summaries,
        )


def _api_ref(api: APIDefinition) -> InstructionAPIRef:
    return InstructionAPIRef(
        id=api.id,
        operation_type=api.operation_type,
        method=api.request.method,
        endpoint=api.request.endpoint,
    )


def _missing_param_details(api: APIDefinition, missing: list[str]) -> list[MissingParamDetail]:
    properties = api.parameters.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}
    details: list[MissingParamDetail] = []
    for name in missing:
        definition = properties.get(name, {})
        if not isinstance(definition, dict):
            definition = {}
        details.append(
            MissingParamDetail(
                name=name,
                label=_localized_value(
                    definition.get("label")
                    or definition.get("title")
                    or definition.get("name")
                    or definition.get("x-label"),
                    name,
                ),
                type=_string_or_none(definition.get("type")),
                description=_localized_value(definition.get("description"), ""),
                source=_string_list(definition.get("source")),
                option_set=_string_or_none(definition.get("option_set")),
                resolve_entity=_string_or_none(definition.get("resolve_entity")),
            )
        )
    return details


def _find_options_api(parameter_name: str, apis: list[APIDefinition]) -> str | None:
    normalized = parameter_name.lower()
    if normalized.endswith("id"):
        resource_name = normalized[:-2]
        for api in apis:
            if api.operation_type == "list" and resource_name in api.id.lower():
                return api.id
    return None


def _localized_value(value: object, default: str) -> str | dict[str, str]:
    if isinstance(value, dict):
        result = {str(key): str(item) for key, item in value.items() if str(item).strip()}
        return result or default
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []
