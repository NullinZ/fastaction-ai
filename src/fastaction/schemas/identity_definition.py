from __future__ import annotations

from pydantic import Field

from fastaction.schemas.common import FastActionModel, JsonObject, LocalizedText


class IdentityDefinition(FastActionModel):
    id: str
    name: LocalizedText
    host_app: str = "default"
    actor_type: str = "user"
    role_aliases: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    allowed_api_ids: list[str] = Field(default_factory=list)
    denied_api_ids: list[str] = Field(default_factory=list)
    system_prompt: LocalizedText = ""
    context_schema: JsonObject = Field(default_factory=dict)
    risk_overrides: JsonObject = Field(default_factory=dict)
    metadata: JsonObject = Field(default_factory=dict)
    is_active: bool = True
