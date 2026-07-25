from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from fastaction.persistence.models import (
    FASTACTION_SCHEMA,
    FastActionAPIDefinitionModel,
    FastActionBase,
    FastActionCardBindingModel,
    FastActionCardDefinitionModel,
    FastActionExecutionResultModel,
    FastActionHostExecutorDefinitionModel,
    FastActionIdentityDefinitionModel,
    FastActionKnowledgeDefinitionModel,
    FastActionOptionSetModel,
    FastActionProviderConfigModel,
    FastActionRunRecordModel,
    FastActionTestMessageModel,
)
from fastaction.logging import get_logger
from fastaction.schemas import (
    APIDefinition,
    CardBinding,
    CardDefinition,
    ExecutionResult,
    HostExecutorDefinition,
    IdentityDefinition,
    KnowledgeDefinition,
    OptionSetDefinition,
    ProviderConfig,
    RunRecord,
)
from fastaction.settings import get_settings

logger = get_logger("fastaction.persistence")
settings = get_settings()

_initialized = False
_session_factory: sessionmaker | None = None


def persistence_enabled() -> bool:
    return bool(get_settings().persistence_enabled)


def is_initialized() -> bool:
    return _initialized and _session_factory is not None


def initialize_fastaction_persistence(
    runtime,
    *,
    engine: Engine | None = None,
    session_factory: sessionmaker | None = None,
) -> None:
    if not persistence_enabled() and engine is None and session_factory is None:
        logger.info("fastaction.persistence.disabled")
        return

    global _initialized, _session_factory
    if session_factory is not None:
        _session_factory = session_factory
        with _session_factory() as session:
            _seed_defaults(session, runtime)
            session.commit()
        load_runtime_from_store(runtime)
        _initialized = True
        logger.info("fastaction.persistence.initialized", mode="session_factory")
        return

    if engine is None:
        database_url = get_settings().database_url
        if not database_url:
            logger.info("fastaction.persistence.disabled", reason="missing_database_url")
            return
        engine = create_engine(database_url)

    _ensure_schema_name(FASTACTION_SCHEMA)
    if engine.dialect.name != "sqlite":
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{FASTACTION_SCHEMA}"'))
    FastActionBase.metadata.create_all(bind=engine)
    _session_factory = sessionmaker(bind=engine)

    with _session_factory() as session:
        _seed_defaults(session, runtime)
        session.commit()
    load_runtime_from_store(runtime)
    _initialized = True
    logger.info("fastaction.persistence.initialized", schema=FASTACTION_SCHEMA)


def load_runtime_from_store(runtime) -> None:
    if _session_factory is None:
        return
    with _session_factory() as session:
        runtime.api_definitions.clear()
        for row in session.query(FastActionAPIDefinitionModel).order_by(FastActionAPIDefinitionModel.id).all():
            runtime.api_definitions.upsert(APIDefinition.model_validate(row.payload))

        runtime.card_definitions.clear()
        for row in session.query(FastActionCardDefinitionModel).order_by(FastActionCardDefinitionModel.card_type).all():
            runtime.card_definitions.upsert(CardDefinition.model_validate(row.payload))

        runtime.card_bindings.clear()
        for row in session.query(FastActionCardBindingModel).order_by(FastActionCardBindingModel.id).all():
            runtime.card_bindings.upsert(CardBinding.model_validate(row.payload))

        runtime.host_executor_definitions.clear()
        for row in session.query(FastActionHostExecutorDefinitionModel).order_by(FastActionHostExecutorDefinitionModel.id).all():
            runtime.host_executor_definitions.upsert(HostExecutorDefinition.model_validate(row.payload))

        runtime.provider_configs.clear()
        for row in session.query(FastActionProviderConfigModel).order_by(FastActionProviderConfigModel.id).all():
            runtime.provider_configs.upsert(ProviderConfig.model_validate(row.payload))

        runtime.identity_definitions.clear()
        for row in session.query(FastActionIdentityDefinitionModel).order_by(FastActionIdentityDefinitionModel.id).all():
            runtime.identity_definitions.upsert(IdentityDefinition.model_validate(row.payload))

        runtime.knowledge_definitions.clear()
        for row in session.query(FastActionKnowledgeDefinitionModel).order_by(FastActionKnowledgeDefinitionModel.id).all():
            runtime.knowledge_definitions.upsert(KnowledgeDefinition.model_validate(row.payload))

        runtime.option_sets.clear()
        for row in session.query(FastActionOptionSetModel).order_by(FastActionOptionSetModel.id).all():
            runtime.option_sets.upsert(OptionSetDefinition.model_validate(row.payload))


def persist_api_definition(item: APIDefinition) -> None:
    _run_write(lambda session: _upsert_api_definition(session, item))


def delete_api_definition(item_id: str) -> None:
    _run_write(lambda session: _delete_by_pk(session, FastActionAPIDefinitionModel, item_id))


def persist_card_definition(item: CardDefinition) -> None:
    _run_write(lambda session: _upsert_card_definition(session, item))


def delete_card_definition(card_type: str) -> None:
    _run_write(lambda session: _delete_by_pk(session, FastActionCardDefinitionModel, card_type))


def persist_card_binding(item: CardBinding) -> None:
    _run_write(lambda session: _upsert_card_binding(session, item))


def delete_card_binding(item_id: str) -> None:
    _run_write(lambda session: _delete_by_pk(session, FastActionCardBindingModel, item_id))


def persist_host_executor_definition(item: HostExecutorDefinition) -> None:
    _run_write(lambda session: _upsert_host_executor_definition(session, item))


def delete_host_executor_definition(item_id: str) -> None:
    _run_write(lambda session: _delete_by_pk(session, FastActionHostExecutorDefinitionModel, item_id))


def persist_provider_config(item: ProviderConfig) -> None:
    _run_write(lambda session: _upsert_provider_config(session, item))


def delete_provider_config(item_id: str) -> None:
    _run_write(lambda session: _delete_by_pk(session, FastActionProviderConfigModel, item_id))


def persist_identity_definition(item: IdentityDefinition) -> None:
    _run_write(lambda session: _upsert_identity_definition(session, item))


def delete_identity_definition(item_id: str) -> None:
    _run_write(lambda session: _delete_by_pk(session, FastActionIdentityDefinitionModel, item_id))


def persist_knowledge_definition(item: KnowledgeDefinition) -> None:
    _run_write(lambda session: _upsert_knowledge_definition(session, item))


def delete_knowledge_definition(item_id: str) -> None:
    _run_write(lambda session: _delete_by_pk(session, FastActionKnowledgeDefinitionModel, item_id))


def persist_option_set(item: OptionSetDefinition) -> None:
    _run_write(lambda session: _upsert_option_set(session, item))


def delete_option_set(item_id: str) -> None:
    _run_write(lambda session: _delete_by_pk(session, FastActionOptionSetModel, item_id))


def persist_run_record(run: RunRecord) -> None:
    if not is_initialized():
        return
    try:
        _run_write(lambda session: _upsert_run_record(session, run))
    except Exception as exc:
        logger.warning(
            "fastaction.run_persist_failed",
            run_id=run.id,
            exception_type=type(exc).__name__,
        )


def list_run_records(limit: int = 100) -> list[dict[str, Any]]:
    if not is_initialized():
        return []
    assert _session_factory is not None
    with _session_factory() as session:
        rows = (
            session.query(FastActionRunRecordModel)
            .order_by(FastActionRunRecordModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [row.payload for row in rows]


def persist_execution_result(result: ExecutionResult) -> None:
    if not is_initialized():
        return
    _run_write(lambda session: _upsert_execution_result(session, result))


def list_execution_results(
    run_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if not is_initialized():
        return []
    assert _session_factory is not None
    with _session_factory() as session:
        query = session.query(FastActionExecutionResultModel)
        if run_id:
            query = query.filter(FastActionExecutionResultModel.run_id == run_id)
        rows = (
            query.order_by(FastActionExecutionResultModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [serialize_execution_result(row) for row in rows]


def record_test_message(
    *,
    session_id: str,
    role: str,
    content: str,
    conversation_id: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
    result: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not is_initialized():
        return None
    message_id = f"msg_{uuid4().hex}"
    row = FastActionTestMessageModel(
        id=message_id,
        session_id=session_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        attachments=attachments or [],
        result=result,
        message_metadata=metadata or {},
        created_at=datetime.utcnow(),
    )
    _run_write(lambda session: session.merge(row))
    return serialize_test_message(row)


def list_test_messages(
    session_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    if not is_initialized():
        return []
    assert _session_factory is not None
    with _session_factory() as session:
        query = session.query(FastActionTestMessageModel)
        if session_id:
            query = query.filter(FastActionTestMessageModel.session_id == session_id)
        rows = (
            query.order_by(FastActionTestMessageModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [serialize_test_message(row) for row in reversed(rows)]


def clear_test_messages(session_id: str) -> int:
    if not is_initialized():
        return 0
    deleted = 0

    def _delete(session: Session) -> None:
        nonlocal deleted
        deleted = (
            session.query(FastActionTestMessageModel)
            .filter(FastActionTestMessageModel.session_id == session_id)
            .delete()
        )

    _run_write(_delete)
    return deleted


def serialize_test_message(row: FastActionTestMessageModel) -> dict[str, Any]:
    return {
        "id": row.id,
        "session_id": row.session_id,
        "conversation_id": row.conversation_id,
        "role": row.role,
        "content": row.content,
        "attachments": row.attachments or [],
        "result": row.result,
        "metadata": row.message_metadata or {},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def serialize_execution_result(row: FastActionExecutionResultModel) -> dict[str, Any]:
    return {
        "id": row.id,
        "run_id": row.run_id,
        "instruction_id": row.instruction_id,
        "api_id": row.api_id,
        "status": row.status,
        "duration_ms": row.duration_ms,
        "request_summary": row.request_summary or {},
        "response_summary": row.response_summary or {},
        "data": row.data,
        "error": row.error,
        "render": row.render or {},
        "payload": row.payload or {},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _seed_defaults(session: Session, runtime) -> None:
    for item in runtime.api_definitions.list():
        if session.get(FastActionAPIDefinitionModel, item.id) is None:
            _upsert_api_definition(session, item)
    for item in runtime.card_definitions.list():
        if session.get(FastActionCardDefinitionModel, item.card_type) is None:
            _upsert_card_definition(session, item)
    for item in runtime.card_bindings.list():
        item_id = _card_binding_id(item)
        if session.get(FastActionCardBindingModel, item_id) is None:
            _upsert_card_binding(session, item)
    for item in runtime.host_executor_definitions.list():
        if session.get(FastActionHostExecutorDefinitionModel, item.id) is None:
            _upsert_host_executor_definition(session, item)
    for item in runtime.provider_configs.list():
        if session.get(FastActionProviderConfigModel, item.id) is None:
            _upsert_provider_config(session, item)
    for item in runtime.identity_definitions.list():
        if session.get(FastActionIdentityDefinitionModel, item.id) is None:
            _upsert_identity_definition(session, item)
    for item in runtime.knowledge_definitions.list():
        if session.get(FastActionKnowledgeDefinitionModel, item.id) is None:
            _upsert_knowledge_definition(session, item)
    for item in runtime.option_sets.list():
        if session.get(FastActionOptionSetModel, item.id) is None:
            _upsert_option_set(session, item)


def _run_write(callback) -> None:
    if not is_initialized():
        return
    assert _session_factory is not None
    with _session_factory() as session:
        callback(session)
        session.commit()


def _upsert_api_definition(session: Session, item: APIDefinition) -> None:
    payload = item.model_dump(mode="json")
    session.merge(
        FastActionAPIDefinitionModel(
            id=item.id,
            version=item.version,
            status=item.status,
            operation_type=str(item.operation_type),
            method=item.request.method,
            endpoint=item.request.endpoint,
            host_app=str(item.metadata.get("host_app") or ""),
            card_type=item.render.card_type,
            payload=payload,
            updated_at=datetime.utcnow(),
        )
    )


def _upsert_provider_config(session: Session, item: ProviderConfig) -> None:
    session.merge(
        FastActionProviderConfigModel(
            id=item.id,
            provider=str(item.provider),
            type=str(item.type),
            model_name=item.model,
            is_active=item.is_active,
            payload=item.model_dump(mode="json"),
            updated_at=datetime.utcnow(),
        )
    )


def _upsert_identity_definition(session: Session, item: IdentityDefinition) -> None:
    session.merge(
        FastActionIdentityDefinitionModel(
            id=item.id,
            host_app=item.host_app,
            actor_type=item.actor_type,
            is_active=item.is_active,
            payload=item.model_dump(mode="json"),
            updated_at=datetime.utcnow(),
        )
    )


def _upsert_card_definition(session: Session, item: CardDefinition) -> None:
    session.merge(
        FastActionCardDefinitionModel(
            card_type=item.card_type,
            category=item.category,
            payload=item.model_dump(mode="json"),
            updated_at=datetime.utcnow(),
        )
    )


def _upsert_card_binding(session: Session, item: CardBinding) -> None:
    session.merge(
        FastActionCardBindingModel(
            id=_card_binding_id(item),
            host_app=item.host_app,
            card_type=item.card_type,
            component_key=item.component_key,
            payload=item.model_dump(mode="json"),
            updated_at=datetime.utcnow(),
        )
    )


def _upsert_host_executor_definition(session: Session, item: HostExecutorDefinition) -> None:
    session.merge(
        FastActionHostExecutorDefinitionModel(
            id=item.id,
            host_app=item.host_app,
            kind=str(item.kind),
            is_active=item.is_active,
            payload=item.model_dump(mode="json"),
            updated_at=datetime.utcnow(),
        )
    )


def _upsert_knowledge_definition(session: Session, item: KnowledgeDefinition) -> None:
    session.merge(
        FastActionKnowledgeDefinitionModel(
            id=item.id,
            is_active=item.is_active,
            payload=item.model_dump(mode="json"),
            updated_at=datetime.utcnow(),
        )
    )


def _upsert_option_set(session: Session, item: OptionSetDefinition) -> None:
    session.merge(
        FastActionOptionSetModel(
            id=item.id,
            host_app=item.host_app,
            category=item.category,
            is_active=item.is_active,
            payload=item.model_dump(mode="json"),
            updated_at=datetime.utcnow(),
        )
    )


def _upsert_run_record(session: Session, run: RunRecord) -> None:
    payload = run.model_dump(mode="json")
    session.merge(
        FastActionRunRecordModel(
            id=run.id,
            conversation_id=run.conversation_id,
            host_app=run.host_app,
            input_text=run.input_text,
            selected_api_id=run.selected_api_id,
            selected_card_type=run.selected_card_type,
            status=run.status,
            confidence=run.confidence,
            latency_ms=run.latency_ms,
            error=run.error,
            user_context_summary=run.user_context_summary,
            instruction=run.instruction,
            decision_reason=str(run.decision_reason),
            payload=payload,
            created_at=run.created_at,
        )
    )


def _upsert_execution_result(session: Session, result: ExecutionResult) -> None:
    payload = result.model_dump(mode="json")
    result_id = f"{result.run_id}:{result.instruction_id}:{result.api_id}"
    session.merge(
        FastActionExecutionResultModel(
            id=result_id,
            run_id=result.run_id,
            instruction_id=result.instruction_id,
            api_id=result.api_id,
            status=str(result.status),
            duration_ms=result.duration_ms,
            request_summary=result.request_summary,
            response_summary=result.response_summary,
            data=result.data,
            error=result.error,
            render=result.render,
            payload=payload,
            created_at=datetime.utcnow(),
        )
    )


def _delete_by_pk(session: Session, model, item_id: str) -> None:
    row = session.get(model, item_id)
    if row is not None:
        session.delete(row)


def _card_binding_id(item: CardBinding) -> str:
    return item.id or f"{item.host_app}:{item.card_type}:{item.component_key}"


def _ensure_schema_name(schema: str) -> None:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
        raise ValueError(f"Invalid FastAction schema name: {schema!r}")
