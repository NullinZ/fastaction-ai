from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastaction.settings import get_settings


QWEN_FREE_QUOTA_MODEL_NAMES = """
qwen3.7-max
qwen3.7-max-2026-05-20
qwen3.7-plus
qwen3.7-plus-2026-05-26
qwen-plus
qwen-plus-latest
qwen-flash
qwen-flash-latest
qwen-turbo
qwen-turbo-latest
qwq-plus
qwen-long
qwen3-coder-plus
qwen3-coder-flash
deepseek-v4-flash
deepseek-v3.2
deepseek-r1
deepseek-r1-distill-qwen-1.5b
deepseek-r1-distill-qwen-7b
deepseek-r1-distill-qwen-14b
deepseek-r1-distill-qwen-32b
deepseek-r1-distill-llama-8b
deepseek-r1-distill-llama-70b
kimi-k2.6
kimi-k2.5
Moonshot-Kimi-K2-Instruct
glm-5.1
glm-5
MiniMax-M2.5
MiniMax-M2.1
""".split()

QWEN_SESSION_IDLE_MINUTES = 5
QWEN_MODEL_PRIORITY = {model_name: index for index, model_name in enumerate(QWEN_FREE_QUOTA_MODEL_NAMES)}


@dataclass
class QwenModelUsage:
    model_name: str
    quota_tokens: int = 1_000_000
    used_tokens: int = 0
    request_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    is_enabled: bool = True
    is_exhausted: bool = False
    last_status: str | None = None
    last_error: str | None = None
    last_latency_ms: int | None = None
    last_used_at: datetime | None = None


_MODEL_USAGE: dict[str, QwenModelUsage] = {
    model_name: QwenModelUsage(model_name=model_name) for model_name in QWEN_FREE_QUOTA_MODEL_NAMES
}


def parse_qwen_free_quota_expires_at(raw_value: str | None) -> datetime | None:
    raw = (raw_value or "").strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    if len(normalized) == 10:
        normalized = f"{normalized}T23:59:59"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def qwen_free_quota_expires_at() -> datetime | None:
    return parse_qwen_free_quota_expires_at(
        get_settings().aliyun_bailian_free_quota_expires_at,
    )


def is_qwen_free_quota_expired(
    now: datetime | None = None,
    expires_at: datetime | None = None,
) -> bool:
    expiration = expires_at if expires_at is not None else qwen_free_quota_expires_at()
    if expiration is None:
        return False
    current = now or (datetime.now(timezone.utc) if expiration.tzinfo else datetime.now())
    if expiration.tzinfo and current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    if current.tzinfo and expiration.tzinfo is None:
        current = current.replace(tzinfo=None)
    return current > expiration


def usage_total_tokens(usage: dict[str, Any] | None) -> int:
    if not usage:
        return 0
    for key in ("total_tokens", "totalTokens"):
        value = usage.get(key)
        if isinstance(value, int):
            return max(0, value)
    prompt = usage.get("prompt_tokens") or usage.get("input_tokens") or usage.get("inputTokens") or 0
    completion = (
        usage.get("completion_tokens")
        or usage.get("output_tokens")
        or usage.get("outputTokens")
        or 0
    )
    try:
        return max(0, int(prompt) + int(completion))
    except (TypeError, ValueError):
        return 0


def is_qwen_chat_routable_model(model_name: str) -> bool:
    name = (model_name or "").lower()
    non_chat_markers = (
        "embedding",
        "rerank",
        "tts",
        "realtime",
        "livetranslate",
        "-vl",
        "vl-",
        "omni",
    )
    if name.startswith("qvq") or any(marker in name for marker in non_chat_markers):
        return False
    return name.startswith(("qwen", "qwq", "deepseek", "kimi", "moonshot", "glm", "minimax", "mimo"))


def select_qwen_candidates(preferred_model: str | None = None) -> list[QwenModelUsage]:
    if is_qwen_free_quota_expired():
        return []
    active = [
        row
        for row in _MODEL_USAGE.values()
        if (
            row.is_enabled
            and not row.is_exhausted
            and is_qwen_chat_routable_model(row.model_name)
            and row.quota_tokens > row.used_tokens
        )
    ]
    preferred = (preferred_model or "").strip()
    if preferred and preferred.lower() != "auto":
        active.sort(
            key=lambda row: (
                0 if row.model_name == preferred else 1,
                row.used_tokens / max(1, row.quota_tokens),
                row.last_used_at or datetime.min,
                QWEN_MODEL_PRIORITY.get(row.model_name, 9999),
            )
        )
        return active
    active.sort(
        key=lambda row: (
            row.used_tokens / max(1, row.quota_tokens),
            row.last_used_at or datetime.min,
            row.fail_count,
            QWEN_MODEL_PRIORITY.get(row.model_name, 9999),
        )
    )
    return active


def record_qwen_success(
    row: QwenModelUsage,
    *,
    usage: dict[str, Any],
    latency_ms: int,
) -> dict[str, Any]:
    now = datetime.now()
    row.used_tokens += usage_total_tokens(usage)
    row.request_count += 1
    row.success_count += 1
    row.last_status = "success"
    row.last_error = None
    row.last_latency_ms = latency_ms
    row.last_used_at = now
    if row.used_tokens >= row.quota_tokens:
        row.is_exhausted = True
    return serialize_qwen_usage(row)


def record_qwen_failure(row: QwenModelUsage, error: Exception) -> None:
    row.request_count += 1
    row.fail_count += 1
    row.last_status = "failed"
    row.last_error = str(error)[:500]
    row.last_used_at = datetime.now()
    if is_free_quota_exhausted_error(error):
        row.is_exhausted = True
        row.used_tokens = max(row.used_tokens, row.quota_tokens)
        row.last_status = "free_quota_exhausted"
    elif is_model_unavailable_error(error):
        row.is_enabled = False
        row.last_status = "model_unavailable"


def serialize_qwen_usage(row: QwenModelUsage) -> dict[str, Any]:
    remaining = max(0, row.quota_tokens - row.used_tokens)
    return {
        "model": row.model_name,
        "quota_tokens": row.quota_tokens,
        "used_tokens": row.used_tokens,
        "remaining_tokens": remaining,
        "usage_ratio": round(row.used_tokens / max(1, row.quota_tokens), 6),
        "request_count": row.request_count,
        "success_count": row.success_count,
        "fail_count": row.fail_count,
        "is_enabled": row.is_enabled,
        "is_exhausted": row.is_exhausted,
        "last_status": row.last_status,
        "last_error": row.last_error,
        "last_latency_ms": row.last_latency_ms,
        "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None,
        "supports_chat": is_qwen_chat_routable_model(row.model_name),
    }


def is_free_quota_exhausted_error(error: Exception) -> bool:
    text = str(error)
    return "AllocationQuota.FreeTierOnly" in text or "FreeTierOnly" in text


def is_model_unavailable_error(error: Exception) -> bool:
    text = str(error).lower()
    return (
        "model" in text
        and any(
            marker in text
            for marker in (
                "not exist",
                "not found",
                "not support",
                "unsupported",
                "invalid",
                "does not",
                "no access",
                "permission",
            )
        )
    )

