# FastAction Worklog / 工作日志

This file is append-only. It exists so work can resume after an interrupted terminal session.

本文档按时间追加记录，目标是在终端或会话意外中断后，可以根据日志继续工作。

## Resume Protocol / 续接协议

```bash
cd fastaction-ai
git status --short --untracked-files=all
git log --oneline -5
python3 scripts/validate_fastaction_boundaries.py
PYTHONPATH=src python -m pytest tests/fastaction -q
cd frontend/workbench && npm run build
```

If the Python virtualenv from a host project is needed:

```bash
cd fastaction-ai
PYTHONPATH=src /path/to/host/.venv/bin/python -m pytest tests/fastaction -q
```

Before committing:

```bash
cd fastaction-ai
python3 scripts/validate_fastaction_boundaries.py
git diff --check
```

Expected result: boundary validation should pass.

预期结果：边界校验应通过。

## 2026-06-06 Standalone Migration / 独立仓库迁移

```text
Goal:
  Move the FastAction engine and generic workbench from the host project into the
  standalone open-source repository fastaction-ai.

Boundary:
  FastAction owns engine/protocol/workbench.
  Host applications own business API registrations, real context, real tokens,
  real files, business adapters, and actual API execution.
```

```text
目标：
  将 FastAction 引擎和通用工作台从宿主工程迁入独立开源仓库 fastaction-ai。

边界：
  FastAction 负责引擎、协议和通用工作台。
  宿主业务系统负责业务 API 注册数据、真实上下文、真实 token、
  真实文件、业务 adapter 和实际 API 执行。
```

Implemented:

```text
Python package:
  - pyproject.toml
  - src/fastaction
  - tests/fastaction
  - scripts/validate_fastaction_boundaries.py

Generic engine:
  - schemas
  - registries
  - planner
  - provider plugins
  - Qwen balanced model-pool adapter
  - auth policy checks
  - field binding
  - optional persistence models
  - FastAPI router under /fastaction

Generic workbench:
  - frontend/workbench
  - API Registry page
  - Test Bench page
  - provider and identity settings
  - card preview
  - debug trace

Documentation:
  - README.md
  - README.zh-CN.md
  - docs/ARCHITECTURE.md
  - docs/WORKBENCH.md
  - docs/DEVELOPMENT_PLAN.md
  - docs/MIGRATION_BOUNDARY.md
```

Verification:

```text
python3 scripts/validate_fastaction_boundaries.py
  Result: passed.

PYTHONPATH=src /path/to/host/.venv/bin/python -m pytest tests/fastaction -q
  Result: 33 passed.

npm run build in frontend/workbench
  Result: passed.

git diff --check
  Result: passed.

Import smoke:
  fastaction.__version__ = 0.1.0
  router.prefix = /fastaction
  route count = 36
```

Commit:

```text
4338879 feat: 迁移 FastAction 引擎与工作台
Remote: git@github.com:NullinZ/fastaction-ai.git
Branch: main
```

## Next Work / 下一步

```text
1. In the host project, replace local engine imports with the fastaction-ai package.
2. Move host business registration data into a host adapter.
3. Keep business samples and host-specific guides in the host project.
4. Wire the host executor for real API execution with current user tokens.
5. Wire context providers for current user, tenant/workspace, current page, and accessible entity lists.
6. Run route compatibility tests and user-facing AI smoke tests.
7. Only after those checks pass, delete the old host-local FastAction implementation.
```

```text
1. 在宿主工程中改为依赖 fastaction-ai 包。
2. 将宿主业务注册数据放入 host adapter。
3. 业务样例和宿主专用指引留在宿主工程。
4. 接入 Host Executor，用当前用户 token 执行真实 API。
5. 接入 Context Provider，提供当前用户、租户/工作区、当前页面和可访问实体列表。
6. 跑路由兼容测试和用户侧 AI 冒烟测试。
7. 以上通过后，再删除宿主工程里的旧 FastAction 实现。
```

Do not:

```text
- Do not copy host business registration data into this repository.
- Do not store real user tokens in FastAction.
- Do not let the model call arbitrary unregistered URLs.
- Do not delete host-local FastAction code before host package integration passes.
```

## 2026-06-06 Quickstart Documentation / 快速指引文档

```text
Goal:
  Add a step-by-step FastAction setup and API integration guide for open-source
  adopters.

Scope:
  Generic package installation, router mounting, workbench startup, provider
  settings, API registration, context/entity preparation, write confirmation,
  host execution, and test-bench verification.

Boundary:
  The guide must not include host business account data, real project names,
  real tokens, or private provider keys. Host-specific examples stay in each
  host application's own documentation.
```

```text
目标：
  增加一篇面向开源使用者的 FastAction 设置和 API 接入快速指引。

范围：
  通用包安装、路由挂载、工作台启动、Provider 设置、API 注册、上下文和实体准备、
  写操作确认、宿主执行器以及测试台验证。

边界：
  文档不得包含宿主业务账号、真实项目名、真实 token 或私有 Provider key。
  宿主业务样例留在宿主应用文档中。
```

Completed:

```text
docs/QUICKSTART.md
docs/QUICKSTART.zh-CN.md

README.md and README.zh-CN.md now link to both quickstart files.
The quickstart covers install, router mounting, API registration, context/entity
preparation, planning, write confirmation, host execution, execution result
write-back, workbench startup, and verification commands.
```

已完成：

```text
docs/QUICKSTART.md
docs/QUICKSTART.zh-CN.md

README.md 和 README.zh-CN.md 已挂载两份快速指引。
快速指引覆盖安装、路由挂载、API 注册、上下文和实体准备、自然语言规划、
写操作确认、宿主执行、ExecutionResult 回写、工作台启动和验证命令。
```

## 2026-06-06 Mentioned Entity Resolution / 显式提及实体校准

```text
Issue:
  When a user mentions a target entity in text, such as "test workspace 0501",
  the parameter resolver could still use current context first and select the
  wrong current resource.

Fix:
  For parameters with resolve_entity, ParameterResolver now tries to match the
  user text against host-provided candidate lists before falling back to
  context.current_* sources.

Candidate keys:
  available_<entity>s
  accessible_<entity>s
  <entity>_candidates
  available_entities.<entity>
  entity_candidates.<entity>

Matching:
  exact compact text match
  numeric zero-normalized match
  lightweight fuzzy score with ambiguity guard
```

```text
问题：
  用户文本里明确提到目标实体时，例如“测试工作区 0501”，参数解析仍可能先使用
  当前上下文里的 current resource，导致选错对象。

修复：
  对声明了 resolve_entity 的参数，ParameterResolver 会先用用户原文匹配
  Host App 提供的候选实体列表，再回退到 context.current_*。

候选来源：
  available_<entity>s
  accessible_<entity>s
  <entity>_candidates
  available_entities.<entity>
  entity_candidates.<entity>

匹配方式：
  紧凑文本精确匹配
  数字去前导零匹配
  带歧义保护的轻量 fuzzy 匹配
```

Verification:

```text
PYTHONPATH=src /path/to/host/.venv/bin/python -m pytest tests/fastaction -q
  Result: 34 passed.

python3 scripts/validate_fastaction_boundaries.py
  Result: passed.
```
