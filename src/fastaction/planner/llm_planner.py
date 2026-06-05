from __future__ import annotations

import json
from typing import Any

from fastaction.domain.enums import InstructionAction, NoApiHitStrategy
from fastaction.domain.errors import ProviderError
from fastaction.planner.candidate_retriever import CandidateRetriever
from fastaction.planner.planner import DeterministicPlanner
from fastaction.providers import ProviderMessage, ProviderResponse, build_provider
from fastaction.schemas import (
    APIDefinition,
    ChatRequest,
    Instruction,
    InstructionProviderRef,
    ProviderConfig,
)


class LLMPlanner:
    def __init__(
        self,
        *,
        deterministic_planner: DeterministicPlanner | None = None,
        retriever: CandidateRetriever | None = None,
    ):
        self.deterministic_planner = deterministic_planner or DeterministicPlanner()
        self.retriever = retriever or CandidateRetriever()

    async def plan(
        self,
        request: ChatRequest,
        apis: list[APIDefinition],
        provider_config: ProviderConfig | None,
        *,
        system_prompt: str = "",
        strict: bool = False,
    ) -> Instruction:
        if not provider_config or not provider_config.is_active:
            return self._fallback(request, apis, "未找到可用的大模型 Provider。", strict)

        candidates = [item.api for item in self.retriever.retrieve(request.text, apis, limit=8)]
        if not candidates:
            return await self._answer_no_api_hit(
                request,
                apis,
                provider_config,
                system_prompt=system_prompt,
                strict=strict,
            )

        provider = build_provider(provider_config)
        messages = [
            ProviderMessage(
                role="system",
                content=_build_system_prompt(system_prompt),
            ),
            ProviderMessage(
                role="user",
                content=_build_user_prompt(request, candidates),
            ),
        ]
        try:
            response = await provider.complete(
                messages,
                temperature=0.1,
                max_tokens=1200,
                json_schema=_planner_response_schema(),
            )
        except ProviderError as exc:
            return self._fallback(request, apis, f"Provider 调用失败：{exc}", strict)

        parsed = _parse_json(response.text)
        api_id = str(parsed.get("api_id") or "")
        if api_id not in {api.id for api in candidates}:
            return self._fallback(request, apis, "大模型返回的 API 不在候选集中。", strict)

        api = next(item for item in candidates if item.id == api_id)
        merged_params = {**request.params, **_safe_dict(parsed.get("params"))}
        planned = self.deterministic_planner.plan(
            request.model_copy(update={"params": merged_params}),
            [api],
        )
        if parsed.get("reply"):
            planned.reply = {"zh": str(parsed["reply"]), "en": str(parsed["reply"])}
        planned.provider = _provider_ref(provider_config, response)
        planned.decision_reason = {
            "zh": f"大模型选择 API 后由 FastAction 策略校验通过。Provider: {provider_config.id}",
            "en": f"LLM selected the API and FastAction policy validation passed. Provider: {provider_config.id}",
        }
        planned.confidence = max(planned.confidence, float(parsed.get("confidence") or 0.0))
        return planned

    async def _answer_no_api_hit(
        self,
        request: ChatRequest,
        apis: list[APIDefinition],
        provider_config: ProviderConfig | None,
        *,
        system_prompt: str,
        strict: bool,
    ) -> Instruction:
        if request.no_api_hit_strategy == NoApiHitStrategy.FIXED:
            return self.deterministic_planner.plan(request, apis)

        if not provider_config or not provider_config.is_active:
            if request.no_api_hit_strategy == NoApiHitStrategy.HYBRID:
                return self._fallback(
                    request,
                    apis,
                    "未命中 API，且未找到可用的大模型 Provider。",
                    strict=False,
                )
            return Instruction(
                action=InstructionAction.REJECT,
                confidence=0.0,
                decision_reason={
                    "zh": "未命中 API，且未找到可用的大模型 Provider。",
                    "en": "No API matched, and no available LLM provider was found.",
                },
                reply={"zh": "大模型回答暂时不可用，未执行 API 编排。", "en": "LLM answer is unavailable."},
            )

        provider = build_provider(provider_config)
        messages = [
            ProviderMessage(role="system", content=_build_answer_system_prompt(system_prompt)),
            ProviderMessage(role="user", content=_build_answer_user_prompt(request)),
        ]
        try:
            response = await provider.complete(
                messages,
                temperature=0.2,
                max_tokens=700,
            )
        except ProviderError as exc:
            if request.no_api_hit_strategy == NoApiHitStrategy.HYBRID:
                return self._fallback(request, apis, f"未命中 API 后大模型回答失败：{exc}", strict=False)
            return Instruction(
                action=InstructionAction.REJECT,
                confidence=0.0,
                decision_reason={
                    "zh": f"未命中 API，且大模型回答失败：{exc}",
                    "en": f"No API matched, and LLM answer failed: {exc}",
                },
                reply={"zh": "大模型回答暂时不可用，未执行 API 编排。", "en": "LLM answer is unavailable."},
            )

        answer = response.text.strip()
        if not answer:
            if request.no_api_hit_strategy == NoApiHitStrategy.HYBRID:
                return self._fallback(request, apis, "未命中 API 后大模型返回空回答。", strict=False)
            return Instruction(
                action=InstructionAction.REJECT,
                confidence=0.0,
                decision_reason={
                    "zh": "未命中 API，且大模型返回空回答。",
                    "en": "No API matched, and LLM returned an empty answer.",
                },
                reply={"zh": "暂时没有可用回答，未执行 API 编排。", "en": "No answer is available."},
            )

        return Instruction(
            action=InstructionAction.ANSWER,
            confidence=0.0,
            decision_reason={
                "zh": f"未命中已注册 API，已使用 Provider 自然语言回答。Provider: {provider_config.id}",
                "en": f"No registered API matched; answered with an LLM provider. Provider: {provider_config.id}",
            },
            provider=_provider_ref(provider_config, response),
            reply={"zh": answer, "en": answer},
            candidates=[],
        )

    def _fallback(
        self,
        request: ChatRequest,
        apis: list[APIDefinition],
        reason: str,
        strict: bool,
    ) -> Instruction:
        if strict:
            return Instruction(
                action=InstructionAction.REJECT,
                confidence=0.0,
                decision_reason={"zh": reason, "en": reason},
                reply={"zh": "大模型规划不可用，未执行 API 编排。", "en": "LLM planning is unavailable."},
            )
        planned = self.deterministic_planner.plan(request, apis)
        planned.decision_reason = {
            "zh": f"{reason} 已回退到确定性规划。",
            "en": f"{reason} Fell back to deterministic planning.",
        }
        return planned


def _build_system_prompt(identity_prompt: str) -> str:
    base = (
        "You are FastAction's planning engine. Select exactly one registered API candidate, "
        "extract safe parameters, and return strict JSON only. Do not invent API IDs. "
        "If the user needs data, choose an API; if no candidate fits, use an empty api_id."
    )
    return f"{identity_prompt}\n\n{base}" if identity_prompt else base


def _provider_ref(
    provider_config: ProviderConfig,
    response: ProviderResponse | None = None,
) -> InstructionProviderRef:
    runtime_model = response.model if response else None
    return InstructionProviderRef(
        id=provider_config.id,
        provider=str(provider_config.provider),
        model=provider_config.model,
        runtime_model=runtime_model,
    )


def _build_answer_system_prompt(identity_prompt: str) -> str:
    base = (
        "You are FastAction's natural-language fallback answer engine. "
        "No registered API matched the user's request, so you must not claim that business data "
        "was queried, updated, created, or deleted. Give a concise helpful answer, ask a clarifying "
        "question when needed, and guide the user toward a registered capability when appropriate. "
        "Do not invent API results, project facts, account data, or hidden system state."
    )
    return f"{identity_prompt}\n\n{base}" if identity_prompt else base


def _build_answer_user_prompt(request: ChatRequest) -> str:
    return json.dumps(
        {
            "user_text": request.text,
            "locale": request.locale,
            "context": request.context,
            "instruction": (
                "Answer naturally in the user's language. If the user asks for private or runtime "
                "business data, explain that no registered API matched and ask what information "
                "they want to connect or register."
            ),
        },
        ensure_ascii=False,
    )


def _build_user_prompt(request: ChatRequest, candidates: list[APIDefinition]) -> str:
    api_blocks = []
    for api in candidates:
        api_blocks.append(
            {
                "id": api.id,
                "name": api.name,
                "operation_type": api.operation_type,
                "intent": api.intent.model_dump(mode="json"),
                "parameters": api.parameters,
                "permissions": api.policy.permissions,
                "risk": api.policy.risk,
            }
        )
    return json.dumps(
        {
            "user_text": request.text,
            "context": request.context,
            "provided_params": request.params,
            "candidate_apis": api_blocks,
            "required_output": {
                "api_id": "one candidate API id or empty string",
                "params": "object",
                "confidence": "0..1",
                "reply": "short natural language response",
            },
        },
        ensure_ascii=False,
    )


def _planner_response_schema() -> dict[str, Any]:
    return {
        "name": "fastaction_planner_output",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["api_id", "params", "confidence", "reply"],
            "properties": {
                "api_id": {"type": "string"},
                "params": {"type": "object"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "reply": {"type": "string"},
            },
        },
    }


def _parse_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
