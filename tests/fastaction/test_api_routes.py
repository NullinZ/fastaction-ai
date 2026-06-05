from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastaction.interfaces.api import (
    router,
    set_context_policy_hook,
    set_context_unavailable_instruction_hook,
)


def make_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_fastaction_router_health():
    response = make_client().get("/fastaction/health")

    assert response.status_code == 200
    assert response.json()["engine"] == "FastAction"


def test_fastaction_default_api_definitions_include_my_todos():
    response = make_client().get("/fastaction/api-definitions")

    assert response.status_code == 200
    api_ids = {item["id"] for item in response.json()}
    assert "tasks.my_todos" in api_ids


def test_fastaction_default_my_todos_can_be_planned():
    response = make_client().post(
        "/fastaction/chat",
        json={
            "text": "我有哪些待办任务",
            "context": {
                "auth": {"access_token": "test-token"},
                "workspace_id": "all",
                "limit": 5,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "invoke_api"
    assert payload["api"]["id"] == "tasks.my_todos"
    assert payload["params"] == {"workspace_id": "all", "limit": 5}


def test_fastaction_default_identities_are_registered():
    response = make_client().get("/fastaction/identity-definitions")

    assert response.status_code == 200
    identity_ids = {item["id"] for item in response.json()}
    assert {"example-admin", "example-operator", "example-viewer"}.issubset(identity_ids)


def test_fastaction_identity_filters_disallowed_apis():
    client = make_client()

    payload = {
        "id": "admin.secure_write_test",
        "name": {"zh": "管理写入测试", "en": "Admin write test"},
        "operation_type": "update",
        "intent": {
            "description": {"zh": "执行管理写入测试", "en": "Run admin write test"},
            "keywords": {"zh": ["管理写入测试"], "en": ["admin write test"]},
            "examples": [],
        },
        "request": {
            "method": "POST",
            "endpoint": "/api/v1/admin/secure-write-test",
            "auth_mode": "user_token",
            "auth": {"mode": "user_token", "token_context_path": "auth.access_token"},
        },
        "parameters": {"type": "object", "properties": {}},
        "policy": {
            "risk": "write",
            "requires_confirmation": False,
            "permissions": ["admin:write"],
            "idempotency": "unsafe",
        },
        "render": {"card_type": "result_card", "fallback_card_type": "generic_data_card"},
    }
    assert client.post("/fastaction/api-definitions", json=payload).status_code == 200

    operator_response = client.post(
        "/fastaction/chat",
        json={"text": "管理写入测试", "identity_id": "example-operator"},
    )
    assert operator_response.status_code == 200
    operator_payload = operator_response.json()
    assert operator_payload["action"] == "reject"
    assert "缺少权限：admin:write" in operator_payload["reply"]["zh"]
    assert "示例管理员" in operator_payload["reply"]["zh"]

    admin_response = client.post(
        "/fastaction/chat",
        json={"text": "管理写入测试", "identity_id": "example-admin"},
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["api"]["id"] == "admin.secure_write_test"

    client.delete("/fastaction/api-definitions/admin.secure_write_test")


def test_fastaction_identity_denied_api_explains_allowed_callers():
    client = make_client()

    identity_payload = {
        "id": "test-denied-tasks-reader",
        "name": {"zh": "测试被禁用角色", "en": "Test denied role"},
        "host_app": "example",
        "actor_type": "viewer",
        "role_aliases": ["test_denied_role"],
        "permissions": ["tasks:read"],
        "denied_api_ids": ["tasks.my_todos"],
        "system_prompt": {"zh": "测试身份", "en": "Test identity"},
    }
    assert client.post("/fastaction/identity-definitions", json=identity_payload).status_code == 200

    response = client.post(
        "/fastaction/chat",
        json={"text": "我有哪些待办任务", "identity_id": "test-denied-tasks-reader"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "reject"
    assert "被配置为禁止调用" in payload["reply"]["zh"]
    assert "可调用角色" in payload["reply"]["zh"]
    assert "示例管理员" in payload["reply"]["zh"]

    client.delete("/fastaction/identity-definitions/test-denied-tasks-reader")


def test_fastaction_host_context_policy_hook_can_block_api():
    client = make_client()
    payload = {
        "id": "context.secure_test",
        "name": {"zh": "上下文策略测试", "en": "Context policy test"},
        "operation_type": "action",
        "intent": {
            "description": {"zh": "上下文策略测试", "en": "Context policy test"},
            "keywords": {"zh": ["上下文策略测试"], "en": ["context policy test"]},
            "examples": [],
        },
        "request": {
            "method": "POST",
            "endpoint": "/api/v1/context-policy-test",
            "auth_mode": "user_token",
            "auth": {"mode": "user_token", "token_context_path": "auth.access_token"},
        },
        "parameters": {"type": "object", "properties": {}},
        "policy": {"risk": "read", "requires_confirmation": False, "permissions": []},
        "render": {"card_type": "result_card", "fallback_card_type": "generic_data_card"},
    }
    assert client.post("/fastaction/api-definitions", json=payload).status_code == 200

    def context_policy(api, identity, context):
        if api.id == "context.secure_test" and context.get("blocked"):
            return False
        return None

    try:
        set_context_policy_hook(context_policy)
        response = client.post(
            "/fastaction/chat",
            json={
                "text": "上下文策略测试",
                "identity_id": "example-admin",
                "context": {"blocked": True},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "reject"
        assert "当前业务上下文不允许" in data["reply"]["zh"]
    finally:
        set_context_policy_hook(None)
        set_context_unavailable_instruction_hook(None)
        client.delete("/fastaction/api-definitions/context.secure_test")


def test_fastaction_provider_preview_masks_secret():
    response = make_client().post("/fastaction/provider-configs/mimo-default/test", json={"live": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "preview"
    assert payload["provider"] == "mimo"
    assert payload["secret"]["secret_ref"] == "MIMO_API_KEY"
    assert payload["payload"]["model"] == "mimo-v2.5-pro"
