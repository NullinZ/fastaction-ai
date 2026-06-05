from __future__ import annotations

from collections.abc import Callable
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from fastaction.domain.enums import InstructionAction
from fastaction.domain.errors import RegistryNotFoundError
from fastaction.executor import apply_field_bindings
from fastaction.observability import audit_recorder
from fastaction.planner import DeterministicPlanner, LLMPlanner
from fastaction.persistence import (
    clear_test_messages,
    delete_api_definition as persist_delete_api_definition,
    delete_card_binding as persist_delete_card_binding,
    delete_card_definition as persist_delete_card_definition,
    delete_identity_definition as persist_delete_identity_definition,
    delete_knowledge_definition as persist_delete_knowledge_definition,
    delete_provider_config as persist_delete_provider_config,
    is_initialized as fastaction_persistence_initialized,
    list_execution_results,
    list_run_records as list_persisted_run_records,
    list_test_messages,
    persist_api_definition,
    persist_card_binding,
    persist_card_definition,
    persist_execution_result,
    persist_identity_definition,
    persist_knowledge_definition,
    persist_provider_config,
    record_test_message,
)
from fastaction.providers import (
    ProviderMessage,
    build_provider,
    provider_presets,
    provider_secret_status,
)
from fastaction.providers.qwen_model_pool import (
    QWEN_FREE_QUOTA_MODEL_NAMES,
    qwen_free_quota_expires_at,
    serialize_qwen_usage,
    select_qwen_candidates,
)
from fastaction.registries import runtime
from fastaction.schemas import (
    APIDefinition,
    CardBinding,
    CardDefinition,
    ChatRequest,
    ExecutionResult,
    IdentityDefinition,
    Instruction,
    KnowledgeDefinition,
    ProviderConfig,
    RenderResult,
    RunRecord,
)
from fastaction.schemas.instruction import CandidateSummary, ClarifyPayload

router = APIRouter(prefix="/fastaction", tags=["FastAction"])
planner = DeterministicPlanner()
llm_planner = LLMPlanner(deterministic_planner=planner)
ContextPolicyHook = Callable[[APIDefinition, IdentityDefinition | None, dict[str, Any]], bool | None]
ContextUnavailableInstructionHook = Callable[
    [APIDefinition, IdentityDefinition | None, ChatRequest, CandidateSummary, dict[str, Any]],
    Instruction | None,
]
_context_policy_hook: ContextPolicyHook | None = None
_context_unavailable_instruction_hook: ContextUnavailableInstructionHook | None = None


def set_context_policy_hook(hook: ContextPolicyHook | None) -> None:
    """Register a host-owned context policy hook.

    The hook may return True/False to decide availability, or None to let
    FastAction's default policy continue.
    """

    global _context_policy_hook
    _context_policy_hook = hook


def set_context_unavailable_instruction_hook(
    hook: ContextUnavailableInstructionHook | None,
) -> None:
    """Register a host-owned response hook for context policy denials."""

    global _context_unavailable_instruction_hook
    _context_unavailable_instruction_hook = hook


class CardPreviewRequest(BaseModel):
    binding: CardBinding
    data: dict[str, Any] | list[Any]
    state: str = "success"


class ProviderPayloadPreviewRequest(BaseModel):
    provider: ProviderConfig
    messages: list[dict[str, str]] = Field(
        default_factory=lambda: [{"role": "user", "content": "Return JSON."}]
    )
    json_schema: dict[str, Any] | None = None
    temperature: float = 0.2
    max_tokens: int = 1024


class ProviderTestRequest(BaseModel):
    messages: list[dict[str, str]] = Field(
        default_factory=lambda: [{"role": "user", "content": "Return {\"ok\": true} as JSON."}]
    )
    json_schema: dict[str, Any] | None = None
    temperature: float = 0.2
    max_tokens: int = 512
    live: bool = False


class TestMessageCreate(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=160)
    role: str = Field(..., min_length=1, max_length=40)
    content: str = Field(..., max_length=12000)
    conversation_id: str | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.get("/health")
def health():
    return {"status": "healthy", "engine": "FastAction"}


@router.post("/chat")
async def chat(request: ChatRequest):
    started = time.time()
    identity = _resolve_identity(request)
    all_apis = runtime.api_definitions.list()
    available_apis = _filter_apis_for_identity(all_apis, identity, request.context)
    provider = _select_provider(request.provider_id) if request.planner_mode in {"hybrid", "llm"} else None
    identity_prompt = _localized_text(identity.system_prompt) if identity else ""
    contextual_instruction = _contextual_unavailable_instruction(
        request,
        identity,
        all_apis=all_apis,
        available_apis=available_apis,
    )
    if contextual_instruction:
        instruction = contextual_instruction
    elif request.planner_mode in {"hybrid", "llm"}:
        instruction = await llm_planner.plan(
            request,
            available_apis,
            provider,
            system_prompt=identity_prompt,
            strict=request.planner_mode == "llm",
        )
    else:
        instruction = planner.plan(request, available_apis)
    audit_recorder.record_run(
        RunRecord(
            id=instruction.run_id,
            conversation_id=request.conversation_id,
            host_app=request.host_app,
            user_context_summary={
                **_summarize_context(request.context),
                "identity_id": identity.id if identity else None,
                "planner_mode": request.planner_mode,
                "provider_id": provider.id if provider else None,
                "no_api_hit_strategy": request.no_api_hit_strategy,
            },
            input_text=request.text,
            selected_api_id=instruction.api.id if instruction.api else None,
            selected_card_type=instruction.render.card_type if instruction.render else None,
            instruction=instruction.model_dump(mode="json"),
            confidence=instruction.confidence,
            decision_reason=str(instruction.decision_reason),
            status="planned",
            latency_ms=int((time.time() - started) * 1000),
        )
    )
    _record_test_bench_messages(request, instruction)
    return instruction


@router.get("/api-definitions")
def list_api_definitions():
    return runtime.api_definitions.list()


@router.post("/api-definitions")
def upsert_api_definition(payload: APIDefinition):
    saved = runtime.api_definitions.upsert(payload)
    persist_api_definition(saved)
    return saved


@router.get("/api-definitions/{api_id}")
def get_api_definition(api_id: str):
    return _get_or_404(runtime.api_definitions, api_id)


@router.put("/api-definitions/{api_id}")
def update_api_definition(api_id: str, payload: APIDefinition):
    if payload.id != api_id:
        raise HTTPException(status_code=400, detail="payload id must match path id")
    saved = runtime.api_definitions.upsert(payload)
    persist_api_definition(saved)
    return saved


@router.delete("/api-definitions/{api_id}")
def delete_api_definition(api_id: str):
    _delete_or_404(runtime.api_definitions, api_id)
    persist_delete_api_definition(api_id)
    return {"deleted": True}


@router.get("/card-definitions")
def list_card_definitions():
    return runtime.card_definitions.list()


@router.post("/card-definitions")
def upsert_card_definition(payload: CardDefinition):
    saved = runtime.card_definitions.upsert(payload)
    persist_card_definition(saved)
    return saved


@router.get("/card-bindings")
def list_card_bindings():
    return runtime.card_bindings.list()


@router.post("/card-bindings")
def upsert_card_binding(payload: CardBinding):
    saved = runtime.card_bindings.upsert(payload)
    persist_card_binding(saved)
    return saved


@router.post("/card-bindings/preview")
def preview_card_binding(payload: CardPreviewRequest):
    props = apply_field_bindings(payload.data, payload.binding.field_bindings)
    return RenderResult(
        run_id="preview",
        card_type=payload.binding.card_type,
        component_key=payload.binding.component_key,
        state=payload.state,
        props=props,
    )


@router.get("/provider-presets")
def list_provider_presets():
    return provider_presets()


@router.get("/provider-configs")
def list_provider_configs():
    return [_provider_public_dump(item) for item in runtime.provider_configs.list()]


@router.post("/provider-configs")
def upsert_provider_config(payload: ProviderConfig):
    saved = runtime.provider_configs.upsert(payload)
    persist_provider_config(saved)
    return saved


@router.get("/provider-configs/{provider_id}")
def get_provider_config(provider_id: str):
    return _provider_public_dump(_get_or_404(runtime.provider_configs, provider_id))


@router.put("/provider-configs/{provider_id}")
def update_provider_config(provider_id: str, payload: ProviderConfig):
    if payload.id != provider_id:
        raise HTTPException(status_code=400, detail="payload id must match path id")
    saved = runtime.provider_configs.upsert(payload)
    persist_provider_config(saved)
    return _provider_public_dump(saved)


@router.delete("/provider-configs/{provider_id}")
def delete_provider_config(provider_id: str):
    _delete_or_404(runtime.provider_configs, provider_id)
    persist_delete_provider_config(provider_id)
    return {"deleted": True}


@router.post("/provider-configs/payload-preview")
def preview_provider_payload(payload: ProviderPayloadPreviewRequest):
    provider = build_provider(payload.provider)
    messages = [
        ProviderMessage(role=item.get("role", "user"), content=item.get("content", ""))
        for item in payload.messages
    ]
    return {
        "provider": payload.provider.provider,
        "url": getattr(provider, "chat_url", getattr(provider, "messages_url", lambda: ""))(),
        "secret": provider_secret_status(payload.provider),
        "payload": provider.build_payload(
            messages,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            json_schema=payload.json_schema,
        ),
    }


@router.post("/provider-configs/{provider_id}/payload-preview")
def preview_saved_provider_payload(provider_id: str, payload: ProviderTestRequest):
    config = _get_or_404(runtime.provider_configs, provider_id)
    return preview_provider_payload(
        ProviderPayloadPreviewRequest(
            provider=config,
            messages=payload.messages,
            json_schema=payload.json_schema,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )
    )


@router.post("/provider-configs/{provider_id}/test")
async def test_provider_config(provider_id: str, payload: ProviderTestRequest):
    config = _get_or_404(runtime.provider_configs, provider_id)
    provider = build_provider(config)
    messages = [
        ProviderMessage(role=item.get("role", "user"), content=item.get("content", ""))
        for item in payload.messages
    ]
    preview = {
        "provider": config.provider,
        "model": config.model,
        "url": getattr(provider, "chat_url", getattr(provider, "messages_url", lambda: ""))(),
        "secret": provider_secret_status(config),
        "payload": provider.build_payload(
            messages,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            json_schema=payload.json_schema,
        ),
    }
    if not payload.live:
        return {"mode": "preview", "ok": True, **preview}
    response = await provider.complete(
        messages,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        json_schema=payload.json_schema,
    )
    return {"mode": "live", "ok": True, **preview, "response": response}


@router.get("/provider-configs/qwen-balanced-service/model-pool")
def get_qwen_balanced_model_pool_status():
    expires_at = qwen_free_quota_expires_at()
    candidates = select_qwen_candidates()
    return {
        "provider_id": "qwen-balanced-service",
        "expires_at": expires_at.isoformat() if expires_at else None,
        "models": [serialize_qwen_usage(item) for item in candidates],
        "model_count": len(QWEN_FREE_QUOTA_MODEL_NAMES),
    }


@router.post("/audio/transcriptions")
async def transcribe_audio_placeholder():
    raise HTTPException(
        status_code=501,
        detail=(
            "ASR provider is not configured in FastAction core. "
            "Register an ASR provider or handle transcription in the host adapter."
        ),
    )


@router.get("/identity-definitions")
def list_identity_definitions():
    return runtime.identity_definitions.list()


@router.post("/identity-definitions")
def upsert_identity_definition(payload: IdentityDefinition):
    saved = runtime.identity_definitions.upsert(payload)
    persist_identity_definition(saved)
    return saved


@router.get("/identity-definitions/{identity_id}")
def get_identity_definition(identity_id: str):
    return _get_or_404(runtime.identity_definitions, identity_id)


@router.put("/identity-definitions/{identity_id}")
def update_identity_definition(identity_id: str, payload: IdentityDefinition):
    if payload.id != identity_id:
        raise HTTPException(status_code=400, detail="payload id must match path id")
    saved = runtime.identity_definitions.upsert(payload)
    persist_identity_definition(saved)
    return saved


@router.delete("/identity-definitions/{identity_id}")
def delete_identity_definition(identity_id: str):
    _delete_or_404(runtime.identity_definitions, identity_id)
    persist_delete_identity_definition(identity_id)
    return {"deleted": True}


@router.get("/knowledge-definitions")
def list_knowledge_definitions():
    return runtime.knowledge_definitions.list()


@router.post("/knowledge-definitions")
def upsert_knowledge_definition(payload: KnowledgeDefinition):
    saved = runtime.knowledge_definitions.upsert(payload)
    persist_knowledge_definition(saved)
    return saved


@router.post("/execution-results")
def accept_execution_result(payload: ExecutionResult):
    persist_execution_result(payload)
    return {"accepted": True, "run_id": payload.run_id, "status": payload.status}


@router.get("/execution-results")
def get_execution_results(
    run_id: str | None = Query(None, max_length=160),
    limit: int = Query(100, ge=1, le=500),
):
    return list_execution_results(run_id=run_id, limit=limit)


@router.get("/runs")
def list_runs(limit: int = Query(100, ge=1, le=500)):
    if fastaction_persistence_initialized():
        return list_persisted_run_records(limit=limit)
    return audit_recorder.list_runs(limit=limit)


@router.get("/test-messages")
def get_test_messages(
    session_id: str | None = Query(None, max_length=160),
    limit: int = Query(100, ge=1, le=500),
):
    return list_test_messages(session_id=session_id, limit=limit)


@router.post("/test-messages")
def create_test_message(payload: TestMessageCreate):
    saved = record_test_message(
        session_id=payload.session_id,
        conversation_id=payload.conversation_id,
        role=payload.role,
        content=payload.content,
        attachments=payload.attachments,
        result=payload.result,
        metadata=payload.metadata,
    )
    return saved or {"accepted": True, "session_id": payload.session_id}


@router.delete("/test-messages")
def delete_test_messages(session_id: str = Query(..., min_length=1, max_length=160)):
    return {"deleted": clear_test_messages(session_id)}


def _get_or_404(registry, item_id: str):
    try:
        return registry.get(item_id)
    except RegistryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _delete_or_404(registry, item_id: str):
    try:
        registry.delete(item_id)
    except RegistryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _summarize_context(context: dict[str, Any]) -> dict[str, Any]:
    allowed_keys = {"host_app", "user", "tenant", "page", "current_resource", "locale"}
    return {key: value for key, value in context.items() if key in allowed_keys}


def _resolve_identity(request: ChatRequest) -> IdentityDefinition | None:
    if request.identity_id:
        try:
            identity = runtime.identity_definitions.get(request.identity_id)
            return identity if identity.is_active else None
        except RegistryNotFoundError:
            return None
    context_identity = request.context.get("identity")
    if isinstance(context_identity, dict):
        identity_id = context_identity.get("id")
        if identity_id:
            try:
                identity = runtime.identity_definitions.get(str(identity_id))
                return identity if identity.is_active else None
            except RegistryNotFoundError:
                pass
    roles = _extract_roles(request.context)
    if not roles:
        return None
    for identity in runtime.identity_definitions.list():
        if identity.is_active and set(roles).intersection(set(identity.role_aliases)):
            return identity
    return None


def _extract_roles(context: dict[str, Any]) -> list[str]:
    user = context.get("user")
    raw_roles: Any = None
    if isinstance(user, dict):
        raw_roles = user.get("roles") or user.get("role")
    if raw_roles is None:
        raw_roles = context.get("roles") or context.get("role")
    if isinstance(raw_roles, str):
        return [raw_roles]
    if isinstance(raw_roles, list):
        return [str(item) for item in raw_roles]
    return []


def _filter_apis_for_identity(
    apis: list[APIDefinition],
    identity: IdentityDefinition | None,
    context: dict[str, Any] | None = None,
) -> list[APIDefinition]:
    if not identity:
        return [api for api in apis if _is_api_allowed_by_context(api, None, context or {})]
    if "*" in identity.permissions:
        allowed = apis
    else:
        permission_set = set(identity.permissions)
        allowed = [
            api
            for api in apis
            if not api.policy.permissions or set(api.policy.permissions).issubset(permission_set)
        ]
    if identity.allowed_api_ids:
        allowed_ids = set(identity.allowed_api_ids)
        allowed = [api for api in allowed if api.id in allowed_ids]
    if identity.denied_api_ids:
        denied_ids = set(identity.denied_api_ids)
        allowed = [api for api in allowed if api.id not in denied_ids]
    return [api for api in allowed if _is_api_allowed_by_context(api, identity, context or {})]


def _is_api_allowed_by_context(
    api: APIDefinition,
    identity: IdentityDefinition | None,
    context: dict[str, Any],
) -> bool:
    if _context_policy_hook:
        result = _context_policy_hook(api, identity, context)
        if result is not None:
            return bool(result)
    return True


def _contextual_unavailable_instruction(
    request: ChatRequest,
    identity: IdentityDefinition | None,
    *,
    all_apis: list[APIDefinition],
    available_apis: list[APIDefinition],
):
    available_ids = {api.id for api in available_apis}
    blocked_apis = [api for api in all_apis if api.id not in available_ids]
    blocked_candidates = planner.retriever.retrieve(request.text, blocked_apis, limit=3)
    if not blocked_candidates:
        return None
    available_candidates = planner.retriever.retrieve(request.text, available_apis, limit=1)
    if available_candidates and available_candidates[0].score >= blocked_candidates[0].score:
        return None
    best_blocked = blocked_candidates[0]
    summary = CandidateSummary(
        api_id=best_blocked.api.id,
        score=best_blocked.score,
        reason=best_blocked.reason,
    )
    reason = _api_unavailable_reason(best_blocked.api, identity, request.context)
    if reason.get("type") == "context" and _context_unavailable_instruction_hook:
        instruction = _context_unavailable_instruction_hook(
            best_blocked.api,
            identity,
            request,
            summary,
            reason,
        )
        if instruction is not None:
            return instruction
    return _role_unavailable_instruction(best_blocked.api, identity, request, summary, reason)


def _api_unavailable_reason(
    api: APIDefinition,
    identity: IdentityDefinition | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    if not identity:
        return {"type": "no_identity", "missing_permissions": []}
    if api.id in set(identity.denied_api_ids):
        return {"type": "denied_api", "missing_permissions": []}
    if identity.allowed_api_ids and api.id not in set(identity.allowed_api_ids):
        return {"type": "not_in_allowlist", "missing_permissions": []}
    if "*" not in identity.permissions:
        missing_permissions = [
            permission
            for permission in api.policy.permissions
            if permission not in set(identity.permissions)
        ]
        if missing_permissions:
            return {"type": "missing_permissions", "missing_permissions": missing_permissions}
    if not _is_api_allowed_by_context(api, identity, context):
        return {"type": "context", "missing_permissions": []}
    return {"type": "unknown", "missing_permissions": []}


def _role_unavailable_instruction(
    api: APIDefinition,
    identity: IdentityDefinition | None,
    request: ChatRequest,
    summary: CandidateSummary,
    reason: dict[str, Any],
) -> Instruction:
    api_name = _localized_text(api.name) or api.id
    current_identity = _identity_label(identity) if identity else "当前用户身份"
    missing_permissions = reason.get("missing_permissions") or []
    callable_labels = _callable_identity_labels(api, request.context, request.host_app)
    callable_text = "、".join(callable_labels) if callable_labels else "当前未配置可调用角色"
    reason_text = _permission_reason_text(reason, missing_permissions)
    next_step = (
        f"请切换到 {callable_text}，或联系对应角色处理。"
        if callable_labels
        else "请在 FastAction 身份配置中补充可调用角色或调整 API 权限策略。"
    )
    required_text = (
        f"该能力需要权限：{', '.join(str(item) for item in api.policy.permissions)}。"
        if api.policy.permissions
        else "该能力没有声明额外权限，但当前身份策略不允许调用。"
    )
    return Instruction(
        action=InstructionAction.REJECT,
        confidence=min(0.95, summary.score / 5.0),
        decision_reason={
            "zh": f"已命中 API，但当前身份不可调用。原因：{reason_text}",
            "en": f"API matched, but the current identity is not allowed to call it. Reason: {reason.get('type')}",
        },
        reply={
            "zh": (
                f"已识别为「{api_name}」，但「{current_identity}」不能调用这个能力。"
                f"{reason_text}{required_text}可调用角色：{callable_text}。{next_step}"
            ),
            "en": (
                f"I recognized this as \"{api_name}\", but \"{current_identity}\" cannot call it. "
                f"Required permissions: {', '.join(str(item) for item in api.policy.permissions) or 'none declared'}. "
                f"Allowed identities: {', '.join(callable_labels) or 'none configured'}."
            ),
        },
        candidates=[summary],
    )


def _permission_reason_text(reason: dict[str, Any], missing_permissions: list[str]) -> str:
    reason_type = reason.get("type")
    if reason_type == "denied_api":
        return "当前角色被配置为禁止调用该 API。"
    if reason_type == "not_in_allowlist":
        return "当前角色的 API 白名单不包含该能力。"
    if reason_type == "missing_permissions":
        return f"当前角色缺少权限：{', '.join(str(item) for item in missing_permissions)}。"
    if reason_type == "context":
        return "当前业务上下文不允许这个角色调用该能力。"
    if reason_type == "no_identity":
        return "当前请求没有解析到可用身份。"
    return "当前身份策略不允许调用。"


def _callable_identity_labels(
    api: APIDefinition,
    context: dict[str, Any],
    host_app: str,
) -> list[str]:
    labels: list[str] = []
    for candidate in runtime.identity_definitions.list():
        if not candidate.is_active:
            continue
        if candidate.host_app not in {host_app, "default", api.metadata.get("host_app", candidate.host_app)}:
            continue
        if not _identity_policy_allows_api(api, candidate):
            continue
        if not _is_api_allowed_by_context(api, candidate, context):
            continue
        labels.append(_identity_label(candidate))
    return _dedupe_preserve_order(labels)[:5]


def _identity_policy_allows_api(api: APIDefinition, identity: IdentityDefinition) -> bool:
    if api.id in set(identity.denied_api_ids):
        return False
    if identity.allowed_api_ids and api.id not in set(identity.allowed_api_ids):
        return False
    if "*" in identity.permissions:
        return True
    if not api.policy.permissions:
        return True
    return set(api.policy.permissions).issubset(set(identity.permissions))


def _identity_label(identity: IdentityDefinition | None) -> str:
    if not identity:
        return "未识别身份"
    name = _localized_text(identity.name) or identity.id
    return f"{name}（{identity.actor_type}）" if identity.actor_type else name


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _select_provider(provider_id: str | None) -> ProviderConfig | None:
    configs = [item for item in runtime.provider_configs.list() if item.is_active]
    if provider_id:
        for item in configs:
            if item.id == provider_id:
                return item
        return None
    planning_configs = [
        item for item in configs if "planning" in item.routing.tasks or "chat" in item.capabilities
    ]
    if not planning_configs:
        return None
    return sorted(planning_configs, key=lambda item: item.routing.priority)[0]


def _record_test_bench_messages(request: ChatRequest, instruction) -> None:
    session_id = str(request.context.get("test_session_id") or "").strip()
    if not session_id:
        return
    attachments = request.context.get("attachments") if isinstance(request.context, dict) else []
    if not isinstance(attachments, list):
        attachments = []
    instruction_payload = instruction.model_dump(mode="json")
    record_test_message(
        session_id=session_id,
        conversation_id=request.conversation_id,
        role="user",
        content=request.text,
        attachments=attachments,
        metadata={
            "host_app": request.host_app,
            "identity_id": request.identity_id,
            "planner_mode": request.planner_mode,
            "provider_id": request.provider_id,
        },
    )
    record_test_message(
        session_id=session_id,
        conversation_id=request.conversation_id,
        role="assistant",
        content=_localized_text(instruction.reply),
        result=instruction_payload,
        metadata={
            "run_id": instruction.run_id,
            "action": instruction.action,
            "selected_api_id": instruction.api.id if instruction.api else None,
            "pending_api_id": instruction.pending_instruction.api_id if instruction.pending_instruction else None,
        },
    )


def _provider_public_dump(config: ProviderConfig) -> dict[str, Any]:
    data = config.model_dump(mode="json")
    credentials = data.get("credentials") or {}
    credentials["api_key"] = None
    data["credentials"] = credentials
    data["secret"] = provider_secret_status(config)
    return data


def _localized_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("zh") or value.get("en") or next(iter(value.values()), ""))
    return ""
