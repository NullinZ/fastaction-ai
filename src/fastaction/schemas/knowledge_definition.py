from __future__ import annotations

from pydantic import Field

from fastaction.schemas.common import FastActionModel, JsonObject, LocalizedText


class KnowledgeDefinition(FastActionModel):
    id: str
    name: LocalizedText
    scope: JsonObject = Field(default_factory=dict)
    retriever: JsonObject = Field(default_factory=dict)
    citation_policy: str = "optional"
    is_active: bool = True
    metadata: JsonObject = Field(default_factory=dict)
