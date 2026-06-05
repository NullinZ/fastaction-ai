from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from fastaction.schemas import ProviderConfig


@dataclass(frozen=True)
class ProviderMessage:
    role: str
    content: str


@dataclass
class ProviderResponse:
    text: str
    provider: str
    model: str
    usage: dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    def __init__(self, config: ProviderConfig, api_key: str | None = None):
        self.config = config
        self.api_key = api_key or config.credentials.api_key

    @abstractmethod
    def build_payload(
        self,
        messages: list[ProviderMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_schema: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build provider request payload without performing network IO."""

    @abstractmethod
    async def complete(
        self,
        messages: list[ProviderMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_schema: dict[str, Any] | None = None,
    ) -> ProviderResponse:
        """Call provider and return complete text."""
