# FastAction Development Plan / 开发计划

This plan is for the standalone `fastaction-ai` open-source project.

本文档面向独立的 `fastaction-ai` 开源项目。

## 1. Current Direction / 当前方向

```text
FastAction = AI-powered API Orchestration Framework

Goal:
  Connect existing enterprise APIs to AI agents with registry, context,
  authorization, preparation, confirmation, execution boundary, cards, and audit.

Non-goal:
  Store host business data, replace host authorization, or execute arbitrary URLs
  chosen by the model.
```

```text
FastAction = AI 驱动的 API 编排框架

目标：
  通过注册、上下文、鉴权协同、调用准备、确认、执行边界、卡片和审计，
  把企业既有 API 接入 AI 智能体。

非目标：
  保存宿主业务数据、替代宿主鉴权，或让模型自由选择任意 URL 调用。
```

## 2. Module Layout / 模块划分

```text
src/fastaction/
  adapters/
    legacy_ai_config.py

  domain/
    enums.py
    errors.py

  executor/
    auth.py
    field_mapper.py

  interfaces/
    api.py

  observability/
    audit.py

  persistence/
    models.py
    store.py

  planner/
    candidate_retriever.py
    llm_planner.py
    parameter_resolver.py
    planner.py
    policy_checker.py

  providers/
    base.py
    credentials.py
    factory.py
    openai_compatible.py
    anthropic.py
    mimo.py
    qwen_balanced.py
    qwen_model_pool.py

  registries/
    base.py
    memory.py

  schemas/
    api_definition.py
    card_definition.py
    common.py
    execution_result.py
    identity_definition.py
    instruction.py
    knowledge_definition.py
    provider_config.py
    run.py

frontend/workbench/
  Standalone Vue workbench and test bench.

tests/fastaction/
  Contract, planner, provider, registry, auth, and API route tests.
```

## 3. Development Phases / 开发阶段

### Phase 1: Foundation / 基础工程

```text
Status:
  Implemented as standalone package foundation.

Scope:
  - package metadata
  - core schemas
  - in-memory registry
  - FastAPI router
  - planner
  - provider factory
  - field mapper
  - auth policy checks
  - tests
  - boundary validation script
```

### Phase 2: Workbench / 工作台

```text
Status:
  Migrated as standalone frontend foundation.

Scope:
  - API Registry page
  - API detail editor
  - card preview
  - test bench
  - two-phone preview
  - debug trace
  - provider and identity settings
  - attachment metadata input
```

### Phase 3: Persistence / 持久化

```text
Goal:
  Add production-grade persistence while keeping in-memory mode available.

Work:
  - database migrations
  - repository interfaces
  - fastaction schema/table namespace
  - registry versioning
  - test message persistence
  - run trace persistence
  - export/import definitions
```

### Phase 4: Context Preparation / 上下文准备层

```text
Goal:
  Make API invocation preparation explicit and configurable.

Work:
  - Context Entity Definition
  - Context Provider Definition
  - Option Definition
  - Entity Resolver
  - Option Resolver
  - Attachment Plan Builder
  - Query Builder
  - Preflight Checker
  - Confirmation Summary Builder
```

### Phase 5: Provider Plugins / Provider 插件

```text
Goal:
  Support mainstream model providers through safe plugin boundaries.

Default providers:
  - OpenAI
  - Anthropic
  - Qwen
  - Doubao
  - Mimo
  - DeepSeek

Rules:
  - secrets are referenced by secret_ref
  - provider plugins do not own business execution
  - provider failures must be visible in trace
  - model version should be recorded in run output
```

### Phase 6: Host SDK and Adapters / 宿主 SDK 和适配器

```text
Goal:
  Let existing systems adopt FastAction without moving business data into it.

Work:
  - Python host executor interface
  - OpenAPI import
  - registry sync adapter
  - auth context adapter
  - file upload adapter protocol
  - callback hooks for confirmation and execution
```

### Phase 7: Observability and Hardening / 可观测性和加固

```text
Work:
  - structured logs
  - trace IDs
  - planner candidate snapshots
  - provider latency and error metrics
  - policy denial metrics
  - schema governance tests
  - prompt redaction tests
  - load tests for registry retrieval
```

## 4. Acceptance Gates / 验收标准

```text
Code boundary:
  - No dependency on any host business module.
  - No host business vocabulary in engine source or tests.
  - No long-term user token storage.

Protocol:
  - API, card, provider, identity, context, option, instruction, and run schemas are stable.
  - Read/write/destructive risk policies are represented.
  - no_match, clarify, confirm, answer, invoke_api, reject are distinct.

Runtime:
  - deterministic mode works without model provider.
  - hybrid mode uses bounded candidates.
  - provider failure is observable.
  - permission denial is not treated as no-match.

Workbench:
  - API details can be opened and edited.
  - field binding can be previewed.
  - test bench can send text and attachment metadata.
  - debug trace shows provider, model, action, params, confidence, and run ID.

Tests:
  - Python test suite passes.
  - frontend build passes.
  - boundary validation passes.
```

## 5. Verification Commands / 验证命令

```bash
python3 scripts/validate_fastaction_boundaries.py
```

```bash
PYTHONPATH=src python -m pytest tests/fastaction -q
```

```bash
cd frontend/workbench
npm install
npm run build
```

```bash
git diff --check
```

## 6. Migration Rule / 迁移规则

```text
Do not delete the host application's old implementation immediately after copy.

Deletion is safe only after:
  1. The standalone package is installable.
  2. The host application imports FastAction from this package.
  3. The host adapter owns business API registrations.
  4. Route compatibility tests pass.
  5. User-facing AI flows pass smoke tests.
```

```text
不要在复制完成后立即删除宿主系统里的旧实现。

只有满足以下条件后，才适合删除旧实现：
  1. 独立包可以安装。
  2. 宿主系统从该包导入 FastAction。
  3. 宿主 adapter 负责业务 API 注册数据。
  4. 路由兼容测试通过。
  5. 用户侧 AI 流程冒烟测试通过。
```
