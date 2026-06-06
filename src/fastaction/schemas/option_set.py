from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from fastaction.schemas.common import FastActionModel, JsonObject, LocalizedText


class OptionItem(FastActionModel):
    value: str = Field(..., min_length=1, max_length=160)
    label: LocalizedText = Field(default_factory=dict)
    aliases: list[str] = Field(default_factory=list)
    description: LocalizedText = Field(default_factory=dict)
    is_active: bool = True
    metadata: JsonObject = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def accept_code_name_aliases(cls, data: Any):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "value" not in normalized and "code" in normalized:
            normalized["value"] = normalized["code"]
        if "label" not in normalized and "name" in normalized:
            normalized["label"] = normalized["name"]
        normalized.pop("code", None)
        normalized.pop("name", None)
        return normalized

    @property
    def code(self) -> str:
        return self.value

    @property
    def name(self) -> LocalizedText:
        return self.label


class OptionSetDefinition(FastActionModel):
    id: str = Field(..., min_length=1, max_length=160)
    name: LocalizedText
    host_app: str = Field("default", min_length=1, max_length=120)
    category: str = Field("enum", min_length=1, max_length=80)
    version: str = "1.0.0"
    is_active: bool = True
    source: JsonObject = Field(default_factory=dict)
    options: list[OptionItem] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)
