from __future__ import annotations

from pydantic import Field, model_validator

from fastaction.domain.enums import ProviderKind, ProviderType
from fastaction.schemas.common import FastActionModel, JsonObject


class ProviderCredentials(FastActionModel):
    mode: str = "server_secret"
    secret_ref: str | None = None
    api_key: str | None = None


class ProviderRouting(FastActionModel):
    tasks: list[str] = Field(default_factory=lambda: ["planning"])
    priority: int = 10
    fallback_provider_id: str | None = None


class ProviderConfig(FastActionModel):
    id: str
    type: ProviderType = ProviderType.LLM
    provider: ProviderKind = ProviderKind.OPENAI_COMPATIBLE
    base_url: str | None = None
    model: str
    capabilities: list[str] = Field(default_factory=lambda: ["chat", "json_schema"])
    routing: ProviderRouting = Field(default_factory=ProviderRouting)
    credentials: ProviderCredentials = Field(default_factory=ProviderCredentials)
    default_headers: dict[str, str] = Field(default_factory=dict)
    extra: JsonObject = Field(default_factory=dict)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_base_url(self):
        if self.provider != ProviderKind.MIMO and not self.base_url:
            raise ValueError("base_url is required for this provider")
        return self
