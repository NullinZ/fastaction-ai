from __future__ import annotations

from pydantic import Field

from fastaction.domain.enums import ResultStatus
from fastaction.schemas.common import FastActionModel, JsonObject, LocalizedText


class ExecutionResult(FastActionModel):
    type: str = "execution_result"
    run_id: str
    instruction_id: str
    api_id: str
    status: ResultStatus
    duration_ms: int | None = Field(None, ge=0)
    request_summary: JsonObject = Field(default_factory=dict)
    response_summary: JsonObject = Field(default_factory=dict)
    data: JsonObject | list | None = None
    error: str | None = None
    render: JsonObject = Field(default_factory=dict)


class RenderResult(FastActionModel):
    type: str = "render_result"
    run_id: str
    card_type: str
    component_key: str | None = None
    state: str = "success"
    props: JsonObject = Field(default_factory=dict)
    reply: LocalizedText = ""
    error: str | None = None
