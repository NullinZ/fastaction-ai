from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import declarative_base

from fastaction.settings import get_settings


FastActionBase = declarative_base()
FASTACTION_SCHEMA = get_settings().db_schema or "fastaction"


class FastActionAPIDefinitionModel(FastActionBase):
    __tablename__ = "api_definitions"
    __table_args__ = {"schema": FASTACTION_SCHEMA}

    id = Column(String(160), primary_key=True)
    version = Column(String(40), nullable=False, default="1.0.0")
    status = Column(String(40), nullable=False, index=True, default="active")
    operation_type = Column(String(40), nullable=False, index=True)
    method = Column(String(20), nullable=False)
    endpoint = Column(String(800), nullable=False)
    host_app = Column(String(120), nullable=True, index=True)
    card_type = Column(String(120), nullable=True, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class FastActionProviderConfigModel(FastActionBase):
    __tablename__ = "provider_configs"
    __table_args__ = {"schema": FASTACTION_SCHEMA}

    id = Column(String(160), primary_key=True)
    provider = Column(String(80), nullable=False, index=True)
    type = Column(String(40), nullable=False, index=True)
    model_name = Column(String(180), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class FastActionIdentityDefinitionModel(FastActionBase):
    __tablename__ = "identity_definitions"
    __table_args__ = {"schema": FASTACTION_SCHEMA}

    id = Column(String(160), primary_key=True)
    host_app = Column(String(120), nullable=False, index=True, default="default")
    actor_type = Column(String(80), nullable=False, index=True, default="user")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class FastActionCardDefinitionModel(FastActionBase):
    __tablename__ = "card_definitions"
    __table_args__ = {"schema": FASTACTION_SCHEMA}

    card_type = Column(String(120), primary_key=True)
    category = Column(String(80), nullable=False, index=True, default="protocol")
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class FastActionCardBindingModel(FastActionBase):
    __tablename__ = "card_bindings"
    __table_args__ = {"schema": FASTACTION_SCHEMA}

    id = Column(String(320), primary_key=True)
    host_app = Column(String(120), nullable=False, index=True)
    card_type = Column(String(120), nullable=False, index=True)
    component_key = Column(String(160), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class FastActionHostExecutorDefinitionModel(FastActionBase):
    __tablename__ = "host_executor_definitions"
    __table_args__ = {"schema": FASTACTION_SCHEMA}

    id = Column(String(160), primary_key=True)
    host_app = Column(String(120), nullable=False, index=True, default="default")
    kind = Column(String(80), nullable=False, index=True, default="host_proxy")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class FastActionKnowledgeDefinitionModel(FastActionBase):
    __tablename__ = "knowledge_definitions"
    __table_args__ = {"schema": FASTACTION_SCHEMA}

    id = Column(String(160), primary_key=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class FastActionOptionSetModel(FastActionBase):
    __tablename__ = "option_sets"
    __table_args__ = {"schema": FASTACTION_SCHEMA}

    id = Column(String(160), primary_key=True)
    host_app = Column(String(120), nullable=False, index=True, default="default")
    category = Column(String(80), nullable=False, index=True, default="enum")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class FastActionRunRecordModel(FastActionBase):
    __tablename__ = "run_records"
    __table_args__ = {"schema": FASTACTION_SCHEMA}

    id = Column(String(160), primary_key=True)
    conversation_id = Column(String(160), nullable=True, index=True)
    host_app = Column(String(120), nullable=False, index=True, default="default")
    input_text = Column(Text, nullable=False)
    selected_api_id = Column(String(160), nullable=True, index=True)
    selected_card_type = Column(String(120), nullable=True, index=True)
    status = Column(String(60), nullable=False, index=True, default="created")
    confidence = Column(Float, nullable=False, default=0.0)
    latency_ms = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    user_context_summary = Column(JSON, nullable=False, default=dict)
    instruction = Column(JSON, nullable=False, default=dict)
    decision_reason = Column(Text, nullable=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class FastActionExecutionResultModel(FastActionBase):
    __tablename__ = "execution_results"
    __table_args__ = {"schema": FASTACTION_SCHEMA}

    id = Column(String(180), primary_key=True)
    run_id = Column(String(160), nullable=False, index=True)
    instruction_id = Column(String(160), nullable=False, index=True)
    api_id = Column(String(160), nullable=False, index=True)
    status = Column(String(60), nullable=False, index=True)
    duration_ms = Column(Integer, nullable=True)
    request_summary = Column(JSON, nullable=False, default=dict)
    response_summary = Column(JSON, nullable=False, default=dict)
    data = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    render = Column(JSON, nullable=False, default=dict)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class FastActionTestMessageModel(FastActionBase):
    __tablename__ = "test_messages"
    __table_args__ = {"schema": FASTACTION_SCHEMA}

    id = Column(String(80), primary_key=True)
    session_id = Column(String(160), nullable=False, index=True)
    conversation_id = Column(String(160), nullable=True, index=True)
    role = Column(String(40), nullable=False, index=True)
    content = Column(Text, nullable=False)
    attachments = Column(JSON, nullable=False, default=list)
    result = Column(JSON, nullable=True)
    message_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
