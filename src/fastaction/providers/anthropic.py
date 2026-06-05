from __future__ import annotations

import time
from typing import Any

import httpx

from fastaction.domain.errors import ProviderError
from fastaction.providers.base import LLMProvider, ProviderMessage, ProviderResponse


class AnthropicMessagesProvider(LLMProvider):
    """Provider for Anthropic Messages API."""

    def messages_url(self) -> str:
        return f"{(self.config.base_url or 'https://api.anthropic.com').rstrip('/')}/v1/messages"

    def build_payload(
        self,
        messages: list[ProviderMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_schema: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        system_parts = [item.content for item in messages if item.role == "system"]
        user_messages = [
            {"role": item.role, "content": item.content}
            for item in messages
            if item.role in {"user", "assistant"}
        ]
        system = "\n\n".join(system_parts)
        if json_schema:
            system = (
                f"{system}\n\n" if system else ""
            ) + "Return only valid JSON that matches the requested schema. Do not include markdown."
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": user_messages or [{"role": "user", "content": ""}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }
        if system:
            payload["system"] = system
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
            "x-api-key": self.api_key,
            "anthropic-version": str(self.config.extra.get("anthropic_version", "2023-06-01")),
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
                response = await client.post(self.messages_url(), headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise ProviderError(f"provider request failed: {self.config.id}: {exc}") from exc

        if response.status_code >= 400:
            raise ProviderError(
                f"provider http {response.status_code}: {self.config.id}: {response.text[:300]}"
            )
        data = response.json()
        text = "".join(
            item.get("text", "")
            for item in data.get("content", [])
            if item.get("type") == "text"
        ).strip()
        return ProviderResponse(
            text=text,
            provider=str(self.config.provider),
            model=self.config.model,
            usage=data.get("usage") or {},
            latency_ms=int((time.time() - started) * 1000),
            raw={"id": data.get("id"), "stop_reason": data.get("stop_reason")},
        )
