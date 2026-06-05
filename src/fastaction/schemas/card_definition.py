from __future__ import annotations

from pydantic import Field

from fastaction.schemas.common import FastActionModel, JsonObject, LocalizedText


class CardDefinition(FastActionModel):
    card_type: str = Field(..., min_length=1, max_length=120)
    name: LocalizedText
    category: str = "protocol"
    data_contract: JsonObject = Field(default_factory=dict)
    states: list[str] = Field(default_factory=lambda: ["loading", "success", "empty", "error"])
    fallback: dict[str, str] = Field(default_factory=lambda: {"card_type": "generic_data_card"})
    metadata: JsonObject = Field(default_factory=dict)


class CardActionDefinition(FastActionModel):
    id: str
    type: str
    label: LocalizedText | None = None
    route: str | None = None
    payload: JsonObject = Field(default_factory=dict)


class CardBinding(FastActionModel):
    id: str | None = None
    host_app: str = Field(..., min_length=1, max_length=120)
    card_type: str = Field(..., min_length=1, max_length=120)
    component_key: str = Field(..., min_length=1, max_length=160)
    field_bindings: dict[str, str] = Field(default_factory=dict)
    actions: list[CardActionDefinition] = Field(default_factory=list)
    sample_data: JsonObject = Field(default_factory=dict)
    metadata: JsonObject = Field(default_factory=dict)
