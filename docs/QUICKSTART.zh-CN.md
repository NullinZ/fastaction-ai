# FastAction 快速指引

这篇文档说明如何把企业既有系统 API 接入 FastAction，让 AI 智能体可以通过自然语言安全地编排业务 API。

## 1. 安装

```bash
python -m pip install fastaction-ai
```

本地源码开发：

```bash
git clone git@github.com:NullinZ/fastaction-ai.git
cd fastaction-ai
python -m pip install -e .
```

## 2. 挂载 API

FastAction 提供 FastAPI router。宿主系统负责挂载路由，并把真实业务执行留在宿主系统内。

```python
from fastapi import FastAPI
from fastaction.interfaces import router as fastaction_router
from fastaction.registries import runtime
from fastaction.schemas import APIDefinition
from fastaction.domain.enums import AuthMode, OperationType, RiskLevel

app = FastAPI()
app.include_router(fastaction_router, prefix="/api/v1/fastaction")
```

## 3. 注册业务 API

把既有 API 注册为一个自然语言可调用能力。FastAction 只保存能力元数据、参数结构、权限策略和卡片绑定，不允许模型自由调用未注册 URL。

```python
runtime.api_definitions.upsert(
    APIDefinition(
        id="tasks.my_todos",
        name={"zh": "我的待办任务"},
        operation_type=OperationType.LIST,
        intent={
            "examples": {"zh": ["帮我看一下我的待办任务", "今天有哪些任务需要处理"]},
            "keywords": {"zh": ["待办", "任务", "处理"]},
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

## 4. 准备上下文

宿主系统在调用 FastAction 时传入运行上下文。常见内容包括当前用户、租户、页面、当前资源、可访问实体列表、字典枚举和附件占位符。

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
    "name": "华北区域"
  },
  "available_workspaces": [
    { "id": "workspace_001", "name": "华北区域" },
    { "id": "workspace_002", "name": "华南区域" }
  ]
}
```

如果某个参数需要从用户原文里校准真实业务对象，在 API 参数里声明 `resolve_entity`。

```json
{
  "workspace_id": {
    "type": "string",
    "resolve_entity": "workspace",
    "source": ["context.current_workspace.id", "context.workspace_id"]
  }
}
```

## 5. 自然语言规划

```bash
curl -X POST http://localhost:8000/api/v1/fastaction/chat \
  -H "Content-Type: application/json" \
  -d '{
    "text": "帮我看一下我的待办任务",
    "identity_id": "manager",
    "planner_mode": "deterministic",
    "context": {
      "auth": { "access_token": "__host_runtime_token__" }
    }
  }'
```

读操作通常直接返回 `invoke_api`：

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

写操作通常返回 `confirm`，由宿主界面让用户确认后再执行：

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

## 6. 宿主系统执行

FastAction 返回结构化指令；真实 API 调用由宿主系统用真实用户身份完成。

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

执行完成后，把结果回写给 FastAction，用于审计、Trace 和卡片渲染。

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

## 7. 启动工作台

仓库内置通用工作台，用于注册和调试。

```bash
cd frontend/workbench
npm install
npm run dev
```

工作台用于查看 API 定义、Provider、身份、卡片绑定、Planner Trace 和执行结果。

常用入口：

```text
/fastaction
  API 注册页。

/fastaction/test
  测试台，用于验证 Planner 行为和 Provider 配置。

/fastaction/cards
  卡片库，用于预览卡片，并复制 CardDefinition、render 字段绑定和示例响应。
```

工作台必须保持宿主无关：只使用通用样例和模拟执行结果。真实企业 API 调用应由宿主系统通过 Host Executor Adapter 接入。

## 8. 验证

```bash
python3 scripts/validate_fastaction_boundaries.py
PYTHONPATH=src python -m pytest tests/fastaction -q
cd frontend/workbench && npm run build
```

预期结果：

```text
边界校验通过
测试通过
前端构建通过
```
