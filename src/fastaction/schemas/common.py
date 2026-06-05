from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

LocalizedText = str | dict[str, str]
JsonObject = dict[str, Any]


class FastActionModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class IntentDefinition(FastActionModel):
    description: LocalizedText = ""
    examples: list[str] | dict[str, list[str]] = Field(default_factory=list)
    keywords: list[str] | dict[str, list[str]] = Field(default_factory=list)

    def all_examples(self) -> list[str]:
        return _flatten_string_list(self.examples)

    def all_keywords(self) -> list[str]:
        return _flatten_string_list(self.keywords)


def _flatten_string_list(value: list[str] | dict[str, list[str]] | None) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    result: list[str] = []
    for items in value.values():
        result.extend(str(item).strip() for item in items if str(item).strip())
    return result


def text_value(value: LocalizedText | None, preferred_locale: str = "zh") -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if preferred_locale in value:
        return str(value[preferred_locale])
    if "zh" in value:
        return str(value["zh"])
    if "en" in value:
        return str(value["en"])
    return str(next(iter(value.values()), ""))
