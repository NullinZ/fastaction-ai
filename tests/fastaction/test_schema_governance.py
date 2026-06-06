from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastaction.persistence.models import (
    FASTACTION_SCHEMA,
    FastActionAPIDefinitionModel,
    FastActionBase,
    FastActionCardBindingModel,
    FastActionCardDefinitionModel,
    FastActionExecutionResultModel,
    FastActionIdentityDefinitionModel,
    FastActionKnowledgeDefinitionModel,
    FastActionOptionSetModel,
    FastActionProviderConfigModel,
    FastActionRunRecordModel,
    FastActionTestMessageModel,
)
from fastaction.settings import get_settings


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_FASTACTION_TABLES = {
    "api_definitions",
    "provider_configs",
    "identity_definitions",
    "card_definitions",
    "card_bindings",
    "knowledge_definitions",
    "option_sets",
    "run_records",
    "execution_results",
    "test_messages",
}


def test_fastaction_tables_are_bound_to_engine_schema():
    assert FASTACTION_SCHEMA == get_settings().db_schema
    models = [
        FastActionAPIDefinitionModel,
        FastActionProviderConfigModel,
        FastActionIdentityDefinitionModel,
        FastActionCardDefinitionModel,
        FastActionCardBindingModel,
        FastActionKnowledgeDefinitionModel,
        FastActionOptionSetModel,
        FastActionRunRecordModel,
        FastActionExecutionResultModel,
        FastActionTestMessageModel,
    ]
    assert {model.__tablename__ for model in models} == EXPECTED_FASTACTION_TABLES
    assert {model.__table__.schema for model in models} == {FASTACTION_SCHEMA}
    assert {table.schema for table in FastActionBase.metadata.tables.values()} == {FASTACTION_SCHEMA}
    assert {table.name for table in FastActionBase.metadata.tables.values()} == EXPECTED_FASTACTION_TABLES


def test_fastaction_boundary_guard_script_passes():
    result = subprocess.run(
        [sys.executable, "scripts/validate_fastaction_boundaries.py"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
