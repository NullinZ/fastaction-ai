from __future__ import annotations

from uuid import uuid4

from pydantic import Field

from fastaction.domain.enums import InstructionAction, NoApiHitStrategy, OperationType, RiskLevel
from fastaction.schemas.common import FastActionModel, JsonObject, LocalizedText


class ChatRequest(FastActionModel):
    text: str = Field(..., min_length=1, max_length=12000)
    context: JsonObject = Field(default_factory=dict)
    params: JsonObject = Field(default_factory=dict)
    host_app: str = "default"
    locale: str = "zh-CN"
    conversation_id: str | None = None
    trace_id: str | None = None
    identity_id: str | None = None
    planner_mode: str = "deterministic"
    provider_id: str | None = None
    no_api_hit_strategy: NoApiHitStrategy = NoApiHitStrategy.HYBRID


class InstructionAPIRef(FastActionModel):
    id: str
    operation_type: OperationType
    method: str
    endpoint: str


class InstructionProviderRef(FastActionModel):
    id: str
    provider: str
    model: str
    runtime_model: str | None = None


class InstructionRender(FastActionModel):
    card_type: str = "generic_data_card"
    state: str = "loading"
    fallback_card_type: str | None = None
    field_bindings: dict[str, str] = Field(default_factory=dict)


class ClarifyPayload(FastActionModel):
    missing_params: list[str] = Field(default_factory=list)
    options_api: str | None = None
    card_type: str = "picker_card"


class PendingInstruction(FastActionModel):
    action: InstructionAction
    api_id: str | None = None
    params: JsonObject = Field(default_factory=dict)


class CandidateSummary(FastActionModel):
    api_id: str
    score: float
    reason: str


class Instruction(FastActionModel):
    type: str = "instruction"
    action: InstructionAction
    instruction_id: str = Field(default_factory=lambda: f"ins_{uuid4().hex}")
    run_id: str = Field(default_factory=lambda: f"run_{uuid4().hex}")
    confidence: float = Field(0.0, ge=0, le=1)
    decision_reason: LocalizedText = ""
    api: InstructionAPIRef | None = None
    provider: InstructionProviderRef | None = None
    params: JsonObject = Field(default_factory=dict)
    risk: RiskLevel | None = None
    render: InstructionRender | None = None
    reply: LocalizedText = ""
    clarify: ClarifyPayload | None = None
    pending_instruction: PendingInstruction | None = None
    candidates: list[CandidateSummary] = Field(default_factory=list)
