from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from fastaction.domain.errors import ProviderError
from fastaction.providers.base import LLMProvider, ProviderMessage, ProviderResponse
from fastaction.providers.qwen_model_pool import (
    QWEN_SESSION_IDLE_MINUTES,
    is_qwen_free_quota_expired,
    record_qwen_failure,
    record_qwen_success,
    select_qwen_candidates,
)
from fastaction.settings import get_settings


class QwenBalancedProvider(LLMProvider):
    """Qwen model-pool provider with process-local quota estimates."""

    def build_payload(
        self,
        messages: list[ProviderMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_schema: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        return {
            "service": "qwen_balanced_model_pool",
            "model": self.config.model or "auto",
            "messages": [{"role": item.role, "content": item.content} for item in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            "json_schema_requested": bool(json_schema),
            "quota_source": "local_estimate",
            "session_idle_minutes": QWEN_SESSION_IDLE_MINUTES,
            **self.config.extra.get("extra_body", {}),
        }

    async def complete(
        self,
        messages: list[ProviderMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_schema: dict[str, Any] | None = None,
    ) -> ProviderResponse:
        started = time.time()
        attempts: list[dict[str, Any]] = []
        last_error: Exception | None = None
        try:
            api_key = self.api_key
            if not api_key:
                raise ProviderError("DASHSCOPE_API_KEY is not configured")
            if is_qwen_free_quota_expired():
                raise ProviderError(
                    "Qwen free quota expired; update ALIYUN_BAILIAN_FREE_QUOTA_EXPIRES_AT "
                    "or disable free-quota routing"
                )

            runtime_base_url = self.config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
            candidates = select_qwen_candidates(_preferred_model(self.config.model, self.config.extra))
            if not candidates:
                raise ProviderError("No enabled Qwen model with local remaining quota")

            provider_messages = [{"role": item.role, "content": item.content} for item in messages]
            for row in candidates:
                candidate_model = row.model_name
                try:
                    result = await _call_qwen_completion(
                        api_key=api_key,
                        base_url=runtime_base_url,
                        model=candidate_model,
                        messages=provider_messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    model_usage = record_qwen_success(
                        row,
                        usage=result["usage"],
                        latency_ms=result["latency_ms"],
                    )
                    attempts.append({"model": candidate_model, "status": "success"})
                    return ProviderResponse(
                        text=result["reply"],
                        provider="qwen_balanced",
                        model=candidate_model,
                        usage=result["usage"],
                        latency_ms=int((time.time() - started) * 1000),
                        raw={
                            "id": f"qwen_balanced_{uuid4().hex}",
                            "routing": "balanced_local_quota",
                            "attempts": attempts,
                            "base_url": runtime_base_url,
                            "key_source": self.config.credentials.secret_ref,
                            "model_usage": model_usage,
                            "json_schema_requested": bool(json_schema),
                        },
                    )
                except Exception as exc:
                    last_error = exc
                    record_qwen_failure(row, exc)
                    attempts.append(
                        {
                            "model": candidate_model,
                            "status": "failed",
                            "error": str(exc)[:300],
                        }
                    )

            raise ProviderError(f"All Qwen balanced candidates failed: {last_error}")
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"qwen balanced provider failed: {exc}") from exc


def _preferred_model(model: str | None, extra: dict[str, Any]) -> str | None:
    preferred = str(extra.get("preferred_model") or "").strip()
    if preferred:
        return preferred
    configured = str(model or "").strip()
    if not configured or configured.lower() in {"auto", "*"}:
        return None
    return configured


async def _call_qwen_completion(
    *,
    api_key: str,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    from openai import AsyncOpenAI

    started = time.time()
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=get_settings().qwen_timeout_seconds,
    )
    completion = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    reply = (completion.choices[0].message.content or "").strip()
    if not reply:
        raise ProviderError("Qwen returned empty content")
    usage = completion.usage.model_dump() if completion.usage else {}
    return {
        "reply": reply,
        "usage": usage,
        "latency_ms": int((time.time() - started) * 1000),
    }
