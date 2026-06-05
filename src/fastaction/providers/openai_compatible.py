from __future__ import annotations

import time
from typing import Any

import httpx

from fastaction.domain.errors import ProviderError
from fastaction.providers.base import LLMProvider, ProviderMessage, ProviderResponse


class OpenAICompatibleProvider(LLMProvider):
    """Provider for OpenAI Chat Completions compatible APIs."""

    def chat_url(self) -> str:
        base_url = (self.config.base_url or "").rstrip("/")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"

    def build_payload(
        self,
        messages: list[ProviderMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_schema: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        if json_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": json_schema.get("name", "fastaction_planner_output"),
                    "strict": True,
                    "schema": json_schema.get("schema", json_schema),
                },
            }
        elif "json_schema" in self.config.capabilities:
            payload["response_format"] = {"type": "json_object"}
        payload.update(self.config.extra.get("extra_body", {}))
        return payload

    async def complete(
        self,
        messages: list[ProviderMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_schema: dict[str, Any] | None = None,
    ) -> ProviderResponse:
        if not self.api_key:
            raise ProviderError(f"provider {self.config.id} has no API key")
        started = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.config.default_headers,
        }
        payload = self.build_payload(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_schema=json_schema,
            stream=False,
        )
        try:
            async with httpx.AsyncClient(timeout=float(self.config.extra.get("timeout", 30))) as client:
                response = await client.post(self.chat_url(), headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise ProviderError(f"provider request failed: {self.config.id}: {exc}") from exc

        if response.status_code >= 400:
            raise ProviderError(
                f"provider http {response.status_code}: {self.config.id}: {response.text[:300]}"
            )
        data = response.json()
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        text = (message.get("content") or "").strip()
        return ProviderResponse(
            text=text,
            provider=str(self.config.provider),
            model=self.config.model,
            usage=data.get("usage") or {},
            latency_ms=int((time.time() - started) * 1000),
            raw={"id": data.get("id"), "finish_reason": choice.get("finish_reason")},
        )
