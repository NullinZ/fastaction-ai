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

## 2026-06-08 Provider Model Pool Registry UX / Provider 模型池注册体验

```text
Goal:
  Remove hidden provider-ID assumptions from the generic Test Bench so open-source
  users can understand and change model routing from visible ProviderConfig rows.

Implemented:
  - Added GET /fastaction/provider-configs/{provider_id}/model-pool.
  - The Test Bench now picks its default planner provider by capabilities:
      model_pool + balanced_routing + chat
      any active model_pool / balanced_routing provider
      any active chat provider
  - The model-pool panel is generic and no longer hard-codes
    qwen-balanced-service in the Vue component.
  - The Test Bench settings now include a Host Executor overview so registered
    execution contracts are visible without reading host code.
  - Qwen remains a Provider preset/plugin, not a special Workbench dependency.

Boundary:
  Provider-specific pool inspection belongs to provider plugins. The generic UI
  only reads ProviderConfig capabilities and provider_id.
```

```text
目标：
  移除通用测试台里隐藏的 provider_id 假设，让开源使用者能从可见的
  ProviderConfig 行理解并替换模型路由。

已实现：
  - 新增 GET /fastaction/provider-configs/{provider_id}/model-pool。
  - 测试台默认 planner provider 改为按能力选择：
      model_pool + balanced_routing + chat
      任意 active model_pool / balanced_routing provider
      任意 active chat provider
  - 模型池面板改为通用面板，不再在 Vue 组件中硬编码
    qwen-balanced-service。
  - 测试台系统设置新增 Host Executor 概览，不读宿主代码也能看到
    已注册执行契约。
  - Qwen 仍然是 Provider preset/plugin，不是 Workbench 特殊依赖。

边界：
  厂商专属模型池探测属于 provider plugin。通用 UI 只读取
  ProviderConfig capabilities 和 provider_id。
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

## 2026-06-08 Workbench Registration-Data Boundary

```text
Goal:
  Remove scattered test-bench hardcoding and make parameter prompts/provider
  templates driven by FastAction registration data.

Implemented:
  - Added MissingParamDetail.ui to the instruction protocol.
  - Deterministic planner now copies parameter ui metadata into clarify payloads.
  - Workbench provider creation templates now load /provider-presets instead of
    embedding a qwen-balanced-service payload in the Vue component.
  - Generic demo context and quick questions moved into a scenario preset file.
  - Migration boundary docs now classify what belongs in registration data and
    what must stay in host adapter code.

Boundary:
  Real business execution functions remain host adapter code. FastAction can
  describe an executor in metadata, but cannot store executable browser/File
  handling logic in API registration data.

Validation:
  - PYTHONPATH=src /path/to/host/.venv/bin/python -m pytest tests/fastaction -q
    Result: 38 passed.
  - python3 scripts/validate_fastaction_boundaries.py
    Result: passed.
  - cd frontend/workbench && npm run build
    Result: passed.
```

```text
目标：
  清理测试台散落硬编码，让补参提示和 Provider 模板来自 FastAction 注册数据。

已实现：
  - Instruction 协议新增 MissingParamDetail.ui。
  - Deterministic planner 会把参数 ui metadata 带入 clarify payload。
  - Workbench 创建 Provider 时读取 /provider-presets，不再在 Vue 组件中
    内置 qwen-balanced-service 完整配置。
  - 通用 demo 上下文和快捷问题移入 scenario preset 文件。
  - 迁移边界文档补充“注册数据 vs 宿主 adapter”规则。

边界：
  真实业务执行函数仍属于宿主 adapter。FastAction 可以用 metadata 描述执行器，
  但不把浏览器 File 处理或真实业务函数存成 API 注册数据。

验证：
  - PYTHONPATH=src /path/to/host/.venv/bin/python -m pytest tests/fastaction -q
    Result: 38 passed.
  - python3 scripts/validate_fastaction_boundaries.py
    Result: passed.
  - cd frontend/workbench && npm run build
    Result: passed.
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

## 2026-06-06 Generic Workbench Boundary / 通用工作台边界

```text
Goal:
  Keep the registry page and test bench independent enough to ship as the
  FastAction open-source workbench.

Decision:
  The generic workbench may edit FastAction definitions, preview cards, inspect
  traces, configure providers, identities, context entities, and options, and
  record simulated execution results. It must not contain host-specific routes,
  dictionaries, roles, entity names, or real business execution code.

Host-specific demos:
  End-to-end examples that execute a real enterprise API belong in the host
  application. They can embed FastAction and call its APIs, but they should not
  be copied into the generic workbench.
```

```text
目标：
  让 API 注册页和测试台足够独立，可以作为 FastAction 开源工作台发布。

决策：
  通用工作台可以编辑 FastAction 定义、预览卡片、查看 Trace、配置 Provider、
  Identity、Context Entity 和 Option，并记录模拟 ExecutionResult。它不能包含
  宿主业务路由、业务字典、业务角色、业务实体名称或真实业务执行代码。

宿主专用演示：
  会执行真实企业 API 的端到端样例应留在宿主系统中。它可以嵌入 FastAction 并调用
  FastAction API，但不应复制到通用工作台。
```

## 2026-06-06 Clarify Missing Parameter Card / 缺失参数补充卡片

```text
Goal:
  Make the clarify state actionable when an API is matched but required
  parameters are missing.

Implemented:
  - Added missing_param_details to ClarifyPayload.
  - DeterministicPlanner now returns API ref, partial params, risk, picker render
    state, missing_params, and missing_param_details for clarify instructions.
  - Missing parameter detail includes name, label, type, description, source,
    option_set, resolve_entity, and required.
  - Generic workbench test bench renders a compact missing-parameter card.
  - The card can generate a Params JSON template for debugging.

Verification:
  - PYTHONPATH=src python -m pytest tests/fastaction -q
    Result: 37 passed.
  - cd frontend/workbench && npm run build
    Result: passed.
```

```text
目标：
  当已经命中 API 但必填参数缺失时，让 clarify 状态可操作，而不是泛泛提示。

已实现：
  - ClarifyPayload 增加 missing_param_details。
  - DeterministicPlanner 在 clarify 指令中返回 API ref、部分参数、风险、
    picker 渲染状态、missing_params 和 missing_param_details。
  - 缺失参数详情包含 name、label、type、description、source、option_set、
    resolve_entity 和 required。
  - 通用工作台测试台渲染紧凑的缺失参数卡片。
  - 卡片支持生成 Params JSON 调试模板。
```

## 2026-06-06 Card Gallery / 卡片库

```text
Goal:
  Make card examples discoverable, copyable, and clearly separated from
  host-specific business UI.

Implemented:
  - Added Workbench route /fastaction/cards.
  - Added cardGalleryDefinitions.js as the card catalog data source.
  - Added CardGalleryView with group filters, search, visual previews, and copy
    buttons for CardDefinition, APIDefinition.render, and sample API response.
  - Added CardPreviewRenderer so the Gallery can show each card as a standalone
    card image and as an embedded assistant chat result.
  - Split card catalog into protocol cards, business examples, and host UI samples.
  - Added picker_card and missing_params_card to default Card Registry seeds.
  - Changed missing-parameter planner render type to missing_params_card with
    picker_card fallback.
  - Added CARD_GALLERY.md and CARD_GALLERY.zh-CN.md.

Boundary:
  Product-specific homepage cards remain host adapter examples. They are not
  FastAction core cards.
```

```text
目标：
  让卡片样例可发现、可复制，并明确区分引擎核心协议和宿主业务 UI。

已实现：
  - 新增 Workbench 路由 /fastaction/cards。
  - 新增 cardGalleryDefinitions.js 作为卡片目录数据源。
  - 新增 CardGalleryView，支持分组筛选、搜索、样式预览，以及复制
    CardDefinition、APIDefinition.render、示例 API 响应。
  - 新增 CardPreviewRenderer，让 Gallery 同时展示卡片本体和嵌入
    assistant 对话消息后的效果。
  - 卡片目录分为协议核心卡片、企业业务样例、宿主 UI 样例。
  - 默认 Card Registry 种子补充 picker_card 和 missing_params_card。
  - 缺参 Planner 渲染类型调整为 missing_params_card，并以 picker_card 兜底。
  - 新增 CARD_GALLERY.md 和 CARD_GALLERY.zh-CN.md。

边界：
  产品专属首页卡片只作为 host adapter 示例，不进入 FastAction 核心卡片。
```

## 2026-06-07 API Registry Wizard UX / API 注册向导体验

```text
Goal:
  Reduce integration burden for enterprise engineers who understand their own
  APIs but should not need to learn every FastAction registry before registering
  a capability.

Implemented:
  - Changed the API Registry page from compact tabs into an 8-step integration
    wizard:
      Basic, Intent, Request, Preparation, Policy, Result, Test, JSON.
  - Added a Preparation step that surfaces required parameters, option-set
    references, context sources, and resolver hints before editing JSON.
  - Moved permission, risk, confirmation, and idempotency into a dedicated
    Policy step instead of mixing them into the request form.
  - Moved planner validation into the Test step so it becomes part of the
    registration flow.
  - Changed the right column into an API Inspector with completion checklist,
    card preview, sample response, card choices, and recent runs.

Boundary:
  The wizard stays generic. It explains capability registration using neutral
  API, parameter, option, context, attachment, and card concepts.
```

## 2026-06-08 Host Executor Registry

```text
Goal:
  Make real execution configurable as a registry contract instead of hidden host
  code.

Implemented:
  - Added HostExecutorDefinition and HostExecutorMatcher schemas.
  - Added runtime.host_executor_definitions.
  - Added fastaction.host_executor_definitions persistence model.
  - Added /fastaction/host-executors CRUD endpoints.
  - Added APIDefinition.execution for mode, executor_id, input_mapping,
    endpoints, and metadata.
  - Bound the default tasks.my_todos sample API to example.host_proxy.
  - Updated Workbench API registration UI to show Execution Mode and Host
    Executor binding.

Boundary:
  FastAction stores the executor contract and audit trail. Host applications own
  actual runtime execution, current user auth, files, and business side effects.
```

## 2026-06-08 Explicit Entity Mention Guard

```text
Goal:
  Prevent natural-language execution from silently falling back to a current
  context entity when the user explicitly mentions a different entity that is not
  registered in available candidates.

Implemented:
  - ParameterResolver now blocks source fallback for resolve_entity parameters
    when entity candidates exist, the text mentions the entity type, and no
    candidate matches the mention.
  - Existing "current context" behavior remains available when the user does not
    explicitly name another entity or no candidates are supplied.

Validation:
  - Added planner regression coverage for "测试资源 05051" with candidates
    "测试资源 0501" and "测试资源 0510".
  - PYTHONPATH=src /path/to/host/.venv/bin/python -m pytest tests/fastaction -q
    Result: 41 passed.
```

```text
目标：
  降低企业工程师接入负担。他们了解自己的 API，但不应该先理解
  FastAction 每个 Registry 才能注册能力。

已实现：
  - API Registry 从紧凑 Tab 调整为 8 步接入向导：
    基础、意图、请求、调用准备、权限确认、返回展示、测试发布、JSON。
  - 新增调用准备步骤，在编辑 JSON 前先展示必填参数、字典引用、
    上下文来源和实体校准提示。
  - 权限、风险、确认和幂等性独立到权限确认步骤，不再混在请求表单里。
  - Planner 验证进入测试发布步骤，成为注册闭环的一部分。
  - 右侧调整为 API Inspector，展示完成度 Checklist、卡片预览、
    示例响应、卡片选择和最近 Runs。

边界：
  向导保持通用，只使用 API、参数、字典、上下文、附件和卡片等
  中性概念说明能力注册。
```

## 2026-06-07 Preparation UX and Reusable OptionSets / 调用准备与可复用字典体验

```text
Goal:
  Treat dictionaries and preparation rules as parameter value-source
  configuration instead of making enterprise integrators edit abstract JSON
  first.

Implemented:
  - Added OptionSet API loading, saving, and deleting to the open-source
    Workbench.
  - Reworked the Preparation step into a parameter matrix:
      parameter name
      business label
      type
      source kind
      option-set binding or source expression
      required flag
  - Added a shared option-set library with reuse count and one-click binding to
    the selected parameter.
  - Added an OptionSet detail editor:
      static values: code | name | aliases
      API source: source API ID, endpoint, method, list path, code field, name field
  - Added missing option-set reference warnings and completion-checklist coverage.

Boundary:
  OptionSet remains a generic FastAction resource. Host-specific values are
  registration data supplied by the host application or host adapter.
```

```text
目标：
  把字典和调用准备规则视为“参数取值来源配置”，避免企业接入者
  一上来就编辑抽象 JSON。

已实现：
  - 开源 Workbench 补齐 OptionSet 加载、保存和删除。
  - 调用准备步骤改为参数矩阵：
      参数名
      业务含义
      类型
      取值来源
      字典绑定或来源表达式
      必填状态
  - 新增共享字典库，显示复用次数，并支持一键绑定到当前参数。
  - 新增 OptionSet 详情编辑：
      静态值：code | 名称 | 别名
      API 来源：来源 API ID、endpoint、method、列表路径、code 字段、name 字段
  - 新增缺失字典引用提示，并纳入完成度检查。

边界：
  OptionSet 仍是通用 FastAction 资源。宿主业务的具体字典值由
  宿主应用或宿主适配器注册进来。
```

## 2026-06-08 Generic Attachment Format Support / 通用附件格式支持

```text
Goal:
  Make the Workbench Test Bench validate common enterprise attachment flows
  instead of assuming every attachment is an image.

Implemented:
  - Test Bench file picker accepts images, PDF, video, audio, DWG, and DXF.
  - Attachment normalization records a generic file kind and only creates
    browser previews for image files.
  - User preview and debug trace render non-image files as compact type badges.
  - Architecture docs now model accepted MIME types and extensions in the
    attachment plan.

Boundary:
  FastAction still does not store binary attachments by default. The host
  application owns upload, transaction handling, retention, virus scanning,
  and business storage.

Validation:
  - repository:
      PYTHONPATH=src python -m pytest tests/fastaction -q
      Result: 38 passed.
  - frontend/workbench:
      npm run build
      Result: passed.
  - repository:
      git diff --check
      Result: passed.
  - repository:
      python3 scripts/validate_fastaction_boundaries.py
      Result: passed.
```

```text
目标：
  让 Workbench 测试台覆盖企业常见附件流程，不再默认所有附件都是图片。

已实现：
  - 测试台文件选择支持图片、PDF、视频、音频、DWG 和 DXF。
  - 附件归一化记录通用文件类型，只对图片生成浏览器预览。
  - 用户预览和调试 Trace 对非图片文件显示紧凑类型徽标。
  - 架构文档把 MIME 类型和文件扩展名纳入附件计划。

边界：
  FastAction 默认仍不保存二进制附件。真实上传、事务、留存、病毒扫描
  和业务存储都由宿主应用负责。

验证：
  - 仓库：
      PYTHONPATH=src python -m pytest tests/fastaction -q
      结果：38 passed。
  - frontend/workbench:
      npm run build
      结果：通过。
  - 仓库：
      git diff --check
      结果：通过。
  - 仓库：
      python3 scripts/validate_fastaction_boundaries.py
      结果：通过。
```
