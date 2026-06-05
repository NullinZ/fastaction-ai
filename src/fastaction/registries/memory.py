from __future__ import annotations

from fastaction.domain.enums import AuthMode, OperationType, ProviderKind, ProviderType, RiskLevel
from fastaction.registries.base import InMemoryRegistry
from fastaction.schemas import (
    APIDefinition,
    CardBinding,
    CardDefinition,
    IdentityDefinition,
    KnowledgeDefinition,
    ProviderConfig,
)


class FastActionRuntime:
    def __init__(self):
        self.api_definitions = InMemoryRegistry[APIDefinition](lambda item: item.id)
        self.card_definitions = InMemoryRegistry[CardDefinition](lambda item: item.card_type)
        self.card_bindings = InMemoryRegistry[CardBinding](
            lambda item: item.id or f"{item.host_app}:{item.card_type}:{item.component_key}"
        )
        self.provider_configs = InMemoryRegistry[ProviderConfig](lambda item: item.id)
        self.identity_definitions = InMemoryRegistry[IdentityDefinition](lambda item: item.id)
        self.knowledge_definitions = InMemoryRegistry[KnowledgeDefinition](lambda item: item.id)

    def seed_defaults(self) -> None:
        for api_definition in default_api_definitions():
            self.api_definitions.upsert(api_definition)
        for card in default_card_definitions():
            self.card_definitions.upsert(card)
        for provider in default_provider_presets():
            self.provider_configs.upsert(provider)
        for identity in default_identity_definitions():
            self.identity_definitions.upsert(identity)


def default_api_definitions() -> list[APIDefinition]:
    return [
        APIDefinition(
            id="tasks.my_todos",
            name={"zh": "我的待办任务", "en": "My todo tasks"},
            operation_type=OperationType.LIST,
            intent={
                "description": {
                    "zh": "查询当前登录用户的待办任务列表。",
                    "en": "List todo tasks visible to the current signed-in user.",
                },
                "examples": {
                    "zh": ["我有哪些待办任务", "查看我的待办", "今天有什么任务要处理"],
                    "en": ["Show my todo tasks", "What tasks do I need to handle"],
                },
                "keywords": {
                    "zh": ["待办", "任务", "我的任务", "todo"],
                    "en": ["todo", "task", "my tasks"],
                },
            },
            request={
                "method": "GET",
                "endpoint": "/api/v1/tasks/my-todos",
                "auth_mode": AuthMode.USER_TOKEN,
                "auth": {
                    "mode": AuthMode.USER_TOKEN,
                    "token_context_path": "auth.access_token",
                },
            },
            parameters={
                "type": "object",
                "required": [],
                "properties": {
                    "workspace_id": {
                        "type": "string",
                        "default": "all",
                        "source": ["context.current_workspace.id", "context.workspace_id"],
                        "resolve_entity": "workspace",
                        "description": "Workspace ID. Use all to query all accessible workspaces.",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 50,
                        "source": ["context.limit"],
                        "description": "返回条数。",
                    },
                },
            },
            response={
                "data_path": "$.data.tasks",
                "exposed_fields": ["id", "name", "status", "workspace_name", "due_date"],
                "prompt_visible_fields": ["name", "status", "workspace_name", "due_date"],
                "sensitive_fields": [],
                "log_redaction": [],
            },
            policy={
                "risk": RiskLevel.READ,
                "requires_confirmation": False,
                "permissions": ["tasks:read"],
                "idempotency": "safe",
            },
            render={
                "card_type": "list_card",
                "fallback_card_type": "generic_data_card",
                "field_bindings": {
                    "title": "我的待办任务",
                    "items": "$.data.tasks",
                },
            },
            metadata={
                "host_app": "example",
                "source": "seed_default",
                "sample": True,
            },
        ),
    ]


def default_card_definitions() -> list[CardDefinition]:
    return [
        CardDefinition(
            card_type="list_card",
            name={"zh": "通用列表卡", "en": "Generic list card"},
            data_contract={
                "type": "object",
                "required": ["title", "items"],
                "properties": {"title": {"type": "string"}, "items": {"type": "array"}},
            },
        ),
        CardDefinition(
            card_type="detail_card",
            name={"zh": "通用详情卡", "en": "Generic detail card"},
            data_contract={"type": "object", "required": ["title"], "properties": {}},
        ),
        CardDefinition(
            card_type="metric_card",
            name={"zh": "通用指标卡", "en": "Generic metric card"},
            data_contract={"type": "object", "required": ["label", "value"], "properties": {}},
        ),
        CardDefinition(
            card_type="confirm_card",
            name={"zh": "通用确认卡", "en": "Generic confirm card"},
            data_contract={"type": "object", "required": ["title", "action"], "properties": {}},
        ),
        CardDefinition(
            card_type="result_card",
            name={"zh": "通用结果卡", "en": "Generic result card"},
            data_contract={"type": "object", "required": ["status"], "properties": {}},
        ),
        CardDefinition(
            card_type="generic_data_card",
            name={"zh": "通用数据卡", "en": "Generic data card"},
            data_contract={"type": "object", "properties": {}},
        ),
    ]


def default_provider_presets() -> list[ProviderConfig]:
    return [
        ProviderConfig(
            id="openai-default",
            provider=ProviderKind.OPENAI,
            type=ProviderType.LLM,
            base_url="https://api.openai.com/v1",
            model="gpt-4.1-mini",
            capabilities=["chat", "json_schema", "tools"],
            credentials={"mode": "server_secret", "secret_ref": "OPENAI_API_KEY"},
        ),
        ProviderConfig(
            id="anthropic-default",
            provider=ProviderKind.ANTHROPIC,
            type=ProviderType.LLM,
            base_url="https://api.anthropic.com",
            model="claude-sonnet-4-5-20250929",
            capabilities=["chat", "tools"],
            credentials={"mode": "server_secret", "secret_ref": "ANTHROPIC_API_KEY"},
        ),
        ProviderConfig(
            id="qwen-default",
            provider=ProviderKind.QWEN,
            type=ProviderType.LLM,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            capabilities=["chat", "json_schema", "tools"],
            credentials={"mode": "server_secret", "secret_ref": "DASHSCOPE_API_KEY"},
        ),
        ProviderConfig(
            id="qwen-balanced-service",
            provider=ProviderKind.QWEN,
            type=ProviderType.LLM,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="auto",
            capabilities=["chat", "json_schema", "model_pool", "balanced_routing"],
            routing={"tasks": ["planning", "chat"], "priority": 6},
            credentials={"mode": "server_secret", "secret_ref": "DASHSCOPE_API_KEY"},
            extra={
                "service": "qwen_balanced_model_pool",
                "quota_source": "local_estimate",
                "session_idle_minutes": 5,
            },
        ),
        ProviderConfig(
            id="doubao-default",
            provider=ProviderKind.DOUBAO,
            type=ProviderType.LLM,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model="doubao-seed-1-6",
            capabilities=["chat", "json_schema", "tools"],
            credentials={"mode": "server_secret", "secret_ref": "VOLCENGINE_ARK_API_KEY"},
        ),
        ProviderConfig(
            id="mimo-default",
            provider=ProviderKind.MIMO,
            type=ProviderType.LLM,
            base_url="https://api.mimo-v2.com/v1",
            model="mimo-v2.5-pro",
            capabilities=["chat", "json_schema"],
            credentials={"mode": "server_secret", "secret_ref": "MIMO_API_KEY"},
        ),
        ProviderConfig(
            id="deepseek-default",
            provider=ProviderKind.DEEPSEEK,
            type=ProviderType.LLM,
            base_url="https://api.deepseek.com",
            model="deepseek-v4-flash",
            capabilities=["chat", "json_schema", "tools"],
            credentials={"mode": "server_secret", "secret_ref": "DEEPSEEK_API_KEY"},
        ),
    ]


def default_identity_definitions() -> list[IdentityDefinition]:
    return [
        IdentityDefinition(
            id="example-admin",
            name={"zh": "示例管理员", "en": "Example admin"},
            host_app="example",
            actor_type="admin",
            role_aliases=["admin", "super_admin", "manager"],
            permissions=["*"],
            system_prompt={
                "zh": "你是 FastAction 管理员身份，可在权限允许范围内编排业务 API。",
                "en": "You are a FastAction admin identity that orchestrates business APIs within policy.",
            },
            metadata={"source": "seed_default"},
        ),
        IdentityDefinition(
            id="example-operator",
            name={"zh": "示例操作员", "en": "Example operator"},
            host_app="example",
            actor_type="operator",
            role_aliases=["operator", "user"],
            permissions=["tasks:read", "tasks:write"],
            system_prompt={
                "zh": "你是示例业务操作员，只能在授权范围内编排 API。",
                "en": "You are an example business operator and may only orchestrate authorized APIs.",
            },
            metadata={"source": "seed_default"},
        ),
        IdentityDefinition(
            id="example-viewer",
            name={"zh": "示例只读用户", "en": "Example viewer"},
            host_app="example",
            actor_type="viewer",
            role_aliases=["viewer", "guest"],
            permissions=["tasks:read"],
            system_prompt={
                "zh": "你是示例只读用户，只能查询授权数据。",
                "en": "You are an example read-only viewer and may only query authorized data.",
            },
            metadata={"source": "seed_default"},
        ),
    ]


runtime = FastActionRuntime()
runtime.seed_defaults()
