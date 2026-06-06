# FastAction Quickstart

This guide shows the minimum path for connecting an existing enterprise API to an AI agent with FastAction.

## 1. Install

```bash
python -m pip install fastaction-ai
```

For local development from source:

```bash
git clone git@github.com:NullinZ/fastaction-ai.git
cd fastaction-ai
python -m pip install -e .
```

## 2. Mount The API

FastAction exposes a FastAPI router. Your host application mounts it and keeps business execution inside the host.

```python
from fastapi import FastAPI
from fastaction.interfaces import router as fastaction_router
from fastaction.registries import runtime
from fastaction.schemas import APIDefinition
from fastaction.domain.enums import AuthMode, OperationType, RiskLevel

app = FastAPI()
app.include_router(fastaction_router, prefix="/api/v1/fastaction")
```

## 3. Register A Business API

Register your existing API as a capability. FastAction stores metadata, schemas, policy, and card bindings. It does not execute arbitrary URLs chosen by the model.

```python
runtime.api_definitions.upsert(
    APIDefinition(
        id="tasks.my_todos",
        name={"en": "My todo tasks"},
        operation_type=OperationType.LIST,
        intent={
            "examples": {"en": ["show my todo tasks", "what should I handle today"]},
            "keywords": {"en": ["todo", "task", "pending"]},
        },
        request={
            "method": "GET",
            "endpoint": "/api/v1/tasks/my-todos",
            "auth_mode": AuthMode.USER_TOKEN,
            "auth": {
                "mode": AuthMode.USER_TOKEN,
                "placement": "header",
                "scheme": "Bearer",
                "token_context_path": "auth.access_token",
            },
        },
        parameters={"type": "object", "properties": {}},
        policy={"risk": RiskLevel.READ, "requires_confirmation": False, "permissions": ["tasks:read"]},
        render={"card_type": "list_card", "field_bindings": {"items": "$.data.items"}},
    )
)
```

## 4. Prepare Context

The host application provides runtime context. This is where business systems pass current user, tenant, page, selected resource, accessible entity lists, dictionaries, and attachment placeholders.

```json
{
  "auth": {
    "access_token": "__host_runtime_token__"
  },
  "user": {
    "id": "user_001",
    "roles": ["manager"]
  },
  "tenant": {
    "id": "tenant_001"
  },
  "current_workspace": {
    "id": "workspace_001",
    "name": "North Region"
  },
  "available_workspaces": [
    { "id": "workspace_001", "name": "North Region" },
    { "id": "workspace_002", "name": "South Region" }
  ]
}
```

For parameters that should be calibrated from user text, declare `resolve_entity` in the API definition.

```json
{
  "workspace_id": {
    "type": "string",
    "resolve_entity": "workspace",
    "source": ["context.current_workspace.id", "context.workspace_id"]
  }
}
```

## 5. Plan From Natural Language

```bash
curl -X POST http://localhost:8000/api/v1/fastaction/chat \
  -H "Content-Type: application/json" \
  -d '{
    "text": "show my todo tasks",
    "identity_id": "manager",
    "planner_mode": "deterministic",
    "context": {
      "auth": { "access_token": "__host_runtime_token__" }
    }
  }'
```

Typical read result:

```json
{
  "action": "invoke_api",
  "api": {
    "id": "tasks.my_todos",
    "method": "GET",
    "endpoint": "/api/v1/tasks/my-todos"
  },
  "params": {},
  "render": {
    "card_type": "list_card"
  }
}
```

Typical write result:

```json
{
  "action": "confirm",
  "api": {
    "id": "documents.upload",
    "method": "POST",
    "endpoint": "/api/v1/documents"
  },
  "params": {
    "workspace_id": "workspace_001",
    "file": "__host_file__"
  },
  "pending_instruction": {
    "action": "invoke_api",
    "api_id": "documents.upload"
  }
}
```

## 6. Execute In The Host App

FastAction returns an instruction. The host app executes the real API with the real user identity.

```python
def execute_instruction(instruction, user_token, files):
    if instruction.action == "confirm":
        return {"status": "waiting_for_user_confirmation"}

    api = instruction.api
    headers = {"Authorization": f"Bearer {user_token}"}
    return host_http_client.request(
        api.method,
        api.endpoint,
        headers=headers,
        json=instruction.params,
        files=files,
    )
```

After execution, write the result back for audit and UI rendering.

```bash
curl -X POST http://localhost:8000/api/v1/fastaction/execution-results \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "run_001",
    "instruction_id": "ins_001",
    "api_id": "tasks.my_todos",
    "status": "success",
    "duration_ms": 120,
    "request_summary": { "method": "GET", "endpoint": "/api/v1/tasks/my-todos" },
    "response_summary": { "count": 3 },
    "data": { "items": [] },
    "render": { "card_type": "list_card" }
  }'
```

## 7. Start The Workbench

The repository includes a generic workbench for registration and debugging.

```bash
cd frontend/workbench
npm install
npm run dev
```

Use it to inspect API definitions, provider settings, identities, card bindings, planner traces, and execution results.

## 8. Verify

```bash
python3 scripts/validate_fastaction_boundaries.py
PYTHONPATH=src python -m pytest tests/fastaction -q
cd frontend/workbench && npm run build
```

Expected result:

```text
boundary validation passed
tests passed
frontend build passed
```
