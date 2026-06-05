# FastAction Worklog / 工作日志

This file is append-only. It exists so work can resume after an interrupted terminal session.

本文档按时间追加记录，目标是在终端或会话意外中断后，可以根据日志继续工作。

## Resume Protocol / 续接协议

```bash
cd /Users/nullin/GitHub/fastaction-ai
git status --short --untracked-files=all
git log --oneline -5
python3 scripts/validate_fastaction_boundaries.py
PYTHONPATH=src python -m pytest tests/fastaction -q
cd frontend/workbench && npm run build
```

If the Python virtualenv from a host project is needed:

```bash
cd /Users/nullin/GitHub/fastaction-ai
PYTHONPATH=src /path/to/host/.venv/bin/python -m pytest tests/fastaction -q
```

Before committing:

```bash
cd /Users/nullin/GitHub/fastaction-ai
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
