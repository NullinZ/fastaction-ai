from types import SimpleNamespace

from fastaction.adapters import (
    api_definition_from_unified_api_config,
    provider_config_from_ai_config,
)


def test_legacy_ai_config_maps_to_fastaction_provider_without_extra_secret_leak():
    config = SimpleNamespace(
        id="legacy-qwen-id",
        provider_name="qwen",
        api_key="real-key",
        api_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_name="qwen-plus",
        is_active=True,
        config={"timeout": 30, "backup_token": "do-not-copy"},
    )

    provider = provider_config_from_ai_config(config)

    assert provider is not None
    assert provider.id == "legacy-ai-qwen"
    assert provider.provider == "qwen"
    assert provider.credentials.mode == "legacy_ai_config"
    assert provider.credentials.api_key == "real-key"
    assert provider.extra["source"] == "legacy_ai_configs"
    assert "backup_token" not in provider.extra


def test_unified_api_config_maps_to_fastaction_api_definition_with_field_policy():
    field_configs = [
        SimpleNamespace(field_name="name", is_included=True, is_required_for_ai=True),
        SimpleNamespace(field_name="phone", is_included=False, is_required_for_ai=False),
    ]
    config = SimpleNamespace(
        id="legacy-api-id",
        name="查询任务",
        description="查询当前任务",
        category="tasks",
        intent_name="tasks.query",
        intent_keywords=["任务", "待办"],
        intent_description="用户查询任务列表",
        endpoint="/api/v1/tasks",
        method="GET",
        parameters={"properties": {"limit": {"type": "integer"}}},
        response_schema={"type": "object"},
        is_dangerous=False,
        is_active=True,
        action_type="query",
        version="1.0.0",
        render_hint="todo_card",
        rollout_percent=100,
        field_configs=field_configs,
    )

    api_definition = api_definition_from_unified_api_config(config)

    assert api_definition.id == "tasks.query"
    assert api_definition.operation_type == "list"
    assert api_definition.policy.risk == "read"
    assert api_definition.request.auth.mode == "user_token"
    assert api_definition.response.prompt_visible_fields == ["name"]
    assert api_definition.response.sensitive_fields == ["phone"]
    assert api_definition.render.card_type == "todo_card"
    assert api_definition.metadata["source"] == "legacy_unified_api_configs"
