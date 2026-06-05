from __future__ import annotations

from fastaction.domain.enums import ProviderKind
from fastaction.providers.anthropic import AnthropicMessagesProvider
from fastaction.providers.base import LLMProvider
from fastaction.providers.mimo import MimoProvider
from fastaction.providers.openai_compatible import OpenAICompatibleProvider
from fastaction.providers.qwen_balanced import QwenBalancedProvider
from fastaction.providers.credentials import resolve_provider_api_key
from fastaction.registries.memory import default_provider_presets
from fastaction.schemas import ProviderConfig


def build_provider(config: ProviderConfig, api_key: str | None = None) -> LLMProvider:
    resolved_key = api_key if api_key is not None else resolve_provider_api_key(config)
    if config.provider == ProviderKind.ANTHROPIC:
        return AnthropicMessagesProvider(config, api_key=resolved_key)
    if config.provider == ProviderKind.QWEN and config.extra.get("service") == "qwen_balanced_model_pool":
        return QwenBalancedProvider(config, api_key=resolved_key)
    if config.provider == ProviderKind.MIMO:
        return MimoProvider(config, api_key=resolved_key)
    return OpenAICompatibleProvider(config, api_key=resolved_key)


def provider_presets() -> list[ProviderConfig]:
    return default_provider_presets()
