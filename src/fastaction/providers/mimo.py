from __future__ import annotations

from fastaction.providers.openai_compatible import OpenAICompatibleProvider


class MimoProvider(OpenAICompatibleProvider):
    """Mimo chat provider using the documented OpenAI-compatible API surface."""

    def chat_url(self) -> str:
        base_url = (self.config.base_url or "https://api.mimo-v2.com/v1").rstrip("/")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"
