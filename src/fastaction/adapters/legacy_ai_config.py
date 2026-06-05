from __future__ import annotations

import re
from typing import Any

from fastaction.domain.enums import AuthMode, OperationType, ProviderKind, ProviderType, RiskLevel
from fastaction.schemas import APIDefinition, ProviderConfig

_PROVIDER_ALIASES: dict[str, ProviderKind] = {
    "openai": ProviderKind.OPENAI,
    "openai_compatible": ProviderKind.OPENAI_COMPATIBLE,
    "openai_compat": ProviderKind.OPENAI_COMPATIBLE,
    "qwen": ProviderKind.QWEN,
    "dashscope": ProviderKind.QWEN,
    "aliyun": ProviderKind.QWEN,
    "anthropic": ProviderKind.ANTHROPIC,
    "claude": ProviderKind.ANTHROPIC,
    "doubao": ProviderKind.DOUBAO,
    "volcengine": ProviderKind.DOUBAO,
    "ark": ProviderKind.DOUBAO,
    "mimo": ProviderKind.MIMO,
    "xiaomi_mimo": ProviderKind.MIMO,
    "deepseek": ProviderKind.DEEPSEEK,
}

_DEFAULT_BASE_URLS: dict[ProviderKind, str] = {
    ProviderKind.OPENAI: "https://api.openai.com/v1",
    ProviderKind.OPENAI_COMPATIBLE: "https://api.openai.com/v1",
    ProviderKind.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ProviderKind.ANTHROPIC: "https://api.anthropic.com",
    ProviderKind.DOUBAO: "https://ark.cn-beijing.volces.com/api/v3",
    ProviderKind.MIMO: "https://api.mimo-v2.com/v1",
    ProviderKind.DEEPSEEK: "https://api.deepseek.com",
}

_DEFAULT_MODELS: dict[ProviderKind, str] = {
    ProviderKind.OPENAI: "gpt-4.1-mini",
    ProviderKind.OPENAI_COMPATIBLE: "gpt-4.1-mini",
    ProviderKind.QWEN: "qwen-plus",
    ProviderKind.ANTHROPIC: "claude-sonnet-4-5-20250929",
    ProviderKind.DOUBAO: "doubao-seed-1-6",
    ProviderKind.MIMO: "mimo-v2.5-pro",
    ProviderKind.DEEPSEEK: "deepseek-v4-flash",
}

_SECRET_REFS: dict[ProviderKind, str] = {
    ProviderKind.OPENAI: "OPENAI_API_KEY",
    ProviderKind.OPENAI_COMPATIBLE: "OPENAI_API_KEY",
    ProviderKind.QWEN: "DASHSCOPE_API_KEY",
    ProviderKind.ANTHROPIC: "ANTHROPIC_API_KEY",
    ProviderKind.DOUBAO: "VOLCENGINE_ARK_API_KEY",
    ProviderKind.MIMO: "MIMO_API_KEY",
    ProviderKind.DEEPSEEK: "DEEPSEEK_API_KEY",
}

_SENSITIVE_EXTRA_NAMES = ("key", "token", "secret", "password", "credential")


def provider_config_from_ai_config(config: Any) -> ProviderConfig | None:
    """Map existing ai_configs rows into FastAction ProviderConfig.

    This generic adapter maps legacy host configuration objects into FastAction
    provider configs. Host applications may replace it with their own adapter.
    """

    provider_name = str(getattr(config, "provider_name", "") or "").strip()
    provider_key = provider_name.lower()
    extra = _as_dict(getattr(config, "config", None))
    provider_kind = _PROVIDER_ALIASES.get(provider_key)
    if provider_kind is None and extra.get("openai_compatible"):
        provider_kind = ProviderKind.OPENAI_COMPATIBLE
    if provider_kind is None:
        return None

    base_url = (
        str(getattr(config, "api_url", "") or "").strip()
        or str(extra.get("api_url") or extra.get("base_url") or "").strip()
        or _DEFAULT_BASE_URLS[provider_kind]
    )
    model = (
        str(getattr(config, "model_name", "") or "").strip()
        or str(extra.get("model") or extra.get("model_name") or "").strip()
        or _DEFAULT_MODELS[provider_kind]
    )
    legacy_id = str(getattr(config, "id", "") or "").strip()
    safe_provider = _safe_id(provider_key or str(provider_kind))

    return ProviderConfig(
        id=f"legacy-ai-{safe_provider}",
        type=ProviderType.LLM,
        provider=provider_kind,
        base_url=base_url,
        model=model,
        capabilities=_provider_capabilities(provider_kind),
        routing={"tasks": ["planning", "chat"], "priority": 8},
        credentials={
            "mode": "legacy_ai_config",
            "secret_ref": _SECRET_REFS[provider_kind],
            "api_key": getattr(config, "api_key", None) or None,
        },
        extra={
            **_safe_extra(extra),
            "source": "legacy_ai_configs",
            "legacy_id": legacy_id,
            "provider_name": provider_name,
        },
        is_active=bool(getattr(config, "is_active", True)),
    )


def api_definition_from_unified_api_config(config: Any) -> APIDefinition:
    """Map existing unified_api_configs rows into FastAction APIDefinition."""

    intent_name = str(getattr(config, "intent_name", "") or "").strip()
    name = str(getattr(config, "name", "") or intent_name).strip()
    description = (
        str(getattr(config, "intent_description", "") or "").strip()
        or str(getattr(config, "description", "") or "").strip()
        or name
    )
    field_configs = list(getattr(config, "field_configs", None) or [])
    included_fields = [
        str(getattr(item, "field_name", "") or "").strip()
        for item in field_configs
        if getattr(item, "is_included", True)
    ]
    included_fields = [item for item in included_fields if item]
    ai_required_fields = [
        str(getattr(item, "field_name", "") or "").strip()
        for item in field_configs
        if getattr(item, "is_included", True) and getattr(item, "is_required_for_ai", False)
    ]
    ai_required_fields = [item for item in ai_required_fields if item]
    hidden_fields = [
        str(getattr(item, "field_name", "") or "").strip()
        for item in field_configs
        if not getattr(item, "is_included", True)
    ]
    hidden_fields = [item for item in hidden_fields if item]

    method = str(getattr(config, "method", "") or "GET").upper()
    action_type = str(getattr(config, "action_type", "") or "query").lower()
    operation_type = _operation_type(action_type, method)
    risk = _risk_level(
        is_dangerous=bool(getattr(config, "is_dangerous", False)),
        method=method,
        operation_type=operation_type,
    )
    render_hint = str(getattr(config, "render_hint", "") or "").strip()
    category = str(getattr(config, "category", "") or "legacy").strip()

    return APIDefinition(
        id=intent_name,
        name={"zh": name, "en": name},
        version=str(getattr(config, "version", "") or "1.0.0"),
        status="active" if getattr(config, "is_active", True) else "disabled",
        operation_type=operation_type,
        intent={
            "description": {"zh": description, "en": description},
            "examples": {"zh": [], "en": []},
            "keywords": {"zh": _string_list(getattr(config, "intent_keywords", None)), "en": []},
        },
        request={
            "method": method,
            "endpoint": str(getattr(config, "endpoint", "") or "").strip(),
            "auth_mode": AuthMode.USER_TOKEN,
            "auth": {
                "mode": AuthMode.USER_TOKEN,
                "token_context_path": "auth.access_token",
            },
            "timeout_ms": 10000,
            "retry": {"enabled": False, "max_attempts": 0},
        },
        parameters=_schema_or_default(getattr(config, "parameters", None)),
        response={
            "data_path": "$",
            "exposed_fields": included_fields,
            "prompt_visible_fields": ai_required_fields or included_fields,
            "sensitive_fields": hidden_fields,
            "log_redaction": hidden_fields,
        },
        policy={
            "risk": risk,
            "requires_confirmation": risk in (RiskLevel.WRITE, RiskLevel.DESTRUCTIVE),
            "permissions": [],
            "idempotency": "safe" if risk == RiskLevel.READ else "unsafe",
        },
        render={
            "card_type": render_hint or "generic_data_card",
            "fallback_card_type": "generic_data_card",
            "field_bindings": _default_field_bindings(render_hint),
        },
        metadata={
            "source": "legacy_unified_api_configs",
            "legacy_id": str(getattr(config, "id", "") or ""),
            "category": category,
            "rollout_percent": int(getattr(config, "rollout_percent", 100) or 100),
            "response_schema": _as_dict(getattr(config, "response_schema", None)),
        },
    )


def _operation_type(action_type: str, method: str) -> OperationType:
    aliases = {
        "query": OperationType.LIST,
        "read": OperationType.LIST,
        "list": OperationType.LIST,
        "detail": OperationType.DETAIL,
        "count": OperationType.COUNT,
        "aggregate": OperationType.AGGREGATE,
        "create": OperationType.CREATE,
        "update": OperationType.UPDATE,
        "delete": OperationType.DELETE,
        "action": OperationType.ACTION,
        "workflow": OperationType.WORKFLOW,
    }
    if action_type in aliases:
        return aliases[action_type]
    if method == "DELETE":
        return OperationType.DELETE
    if method in {"POST", "PUT", "PATCH"}:
        return OperationType.UPDATE
    return OperationType.LIST


def _risk_level(*, is_dangerous: bool, method: str, operation_type: OperationType) -> RiskLevel:
    if is_dangerous or operation_type == OperationType.DELETE:
        return RiskLevel.DESTRUCTIVE
    if method in {"POST", "PUT", "PATCH"} or operation_type in {
        OperationType.CREATE,
        OperationType.UPDATE,
        OperationType.ACTION,
        OperationType.WORKFLOW,
    }:
        return RiskLevel.WRITE
    return RiskLevel.READ


def _provider_capabilities(provider: ProviderKind) -> list[str]:
    if provider == ProviderKind.ANTHROPIC:
        return ["chat", "tools"]
    return ["chat", "json_schema", "tools"]


def _default_field_bindings(render_hint: str) -> dict[str, str]:
    if render_hint in {"todo_card", "task_status_card"}:
        return {"title": "任务", "items": "$.data.items"}
    if render_hint in {"progress_card", "metric_card"}:
        return {"title": "进度", "items": "$.data.items"}
    if render_hint:
        return {"title": "结果", "items": "$.data.items"}
    return {}


def _schema_or_default(value: Any) -> dict[str, Any]:
    schema = _as_dict(value)
    if schema:
        schema.setdefault("type", "object")
        schema.setdefault("properties", {})
        return schema
    return {"type": "object", "properties": {}}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_extra(value: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        lowered = str(key).lower()
        if any(token in lowered for token in _SENSITIVE_EXTRA_NAMES):
            continue
        result[str(key)] = item
    return result


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(_string_list(item))
        return result
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in re.split(r"[,，\n]", value) if item.strip()]
    return []


def _safe_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_.-]+", "-", value.lower()).strip("-")
    return normalized or "provider"
