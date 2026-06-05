from __future__ import annotations

from datetime import datetime

from pydantic import Field

from fastaction.schemas.common import FastActionModel, JsonObject


class RunRecord(FastActionModel):
    id: str
    conversation_id: str | None = None
    host_app: str = "default"
    user_context_summary: JsonObject = Field(default_factory=dict)
    input_text: str
    selected_api_id: str | None = None
    selected_card_type: str | None = None
    instruction: JsonObject = Field(default_factory=dict)
    confidence: float = 0.0
    decision_reason: str = ""
    status: str = "created"
    latency_ms: int | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
