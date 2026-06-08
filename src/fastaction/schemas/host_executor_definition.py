from __future__ import annotations

from typing import Literal

from pydantic import Field

from fastaction.schemas.common import FastActionModel, JsonObject, LocalizedText


HostExecutorKind = Literal[
    "host_proxy",
    "browser_fetch",
    "browser_multipart_upload",
    "server_webhook",
    "manual",
]


class HostExecutorMatcher(FastActionModel):
    api_ids: list[str] = Field(default_factory=list)
    operation_types: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    endpoint_patterns: list[str] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)


class HostExecutorDefinition(FastActionModel):
    id: str = Field(..., min_length=1, max_length=160)
    name: LocalizedText
    host_app: str = Field("default", min_length=1, max_length=120)
    kind: HostExecutorKind = "host_proxy"
    description: LocalizedText = ""
    matcher: HostExecutorMatcher = Field(default_factory=HostExecutorMatcher)
    input_contract: JsonObject = Field(default_factory=dict)
    output_contract: JsonObject = Field(default_factory=dict)
    runtime: JsonObject = Field(default_factory=dict)
    ui: JsonObject = Field(default_factory=dict)
    metadata: JsonObject = Field(default_factory=dict)
    is_active: bool = True
