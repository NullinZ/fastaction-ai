# FastAction Migration Boundary / 迁移边界

This document defines what was moved into the standalone FastAction project and what must remain in a host application.

本文档定义哪些内容迁入独立 FastAction 项目，哪些内容必须留在宿主业务系统。

## 1. Migrated Into FastAction / 已迁入 FastAction

```text
Engine:
  - schemas
  - registries
  - planner
  - provider adapters
  - auth policy checks
  - field binding
  - audit envelope
  - FastAPI router
  - optional persistence models

Workbench:
  - API Registry page
  - API detail editor
  - card preview
  - test bench
  - provider settings
  - identity settings
  - context input and debug trace
  - generic demo data only

Tests:
  - contract tests
  - planner tests
  - provider tests
  - auth tests
  - field mapper tests
  - API route tests
  - boundary governance tests
```

```text
引擎：
  - schema
  - registry
  - planner
  - provider adapter
  - 鉴权策略检查
  - 字段绑定
  - 审计信封
  - FastAPI router
  - 可选持久化模型

工作台：
  - API 注册页
  - API 详情编辑
  - 卡片预览
  - 测试台
  - Provider 设置
  - 身份设置
  - 上下文输入和调试 Trace
  - 仅包含通用演示数据

测试：
  - 协议测试
  - Planner 测试
  - Provider 测试
  - 鉴权测试
  - 字段映射测试
  - API 路由测试
  - 边界治理测试
```

## 2. Must Stay In Host App / 必须留在宿主系统

```text
Host-specific data:
  - real business API registrations
  - real user and tenant IDs
  - real business entity lists
  - real access tokens
  - real provider API keys
  - real uploaded files
  - business-specific prompt text
  - final business permission decisions

Host-specific code:
  - adapter that syncs existing APIs into FastAction
  - adapter that resolves current user/session/context
  - adapter that executes real APIs
  - adapter that uploads files
  - host-specific integration demo pages
  - UI shell integration and menu placement
```

```text
宿主业务数据：
  - 真实业务 API 注册数据
  - 真实用户和租户 ID
  - 真实业务实体列表
  - 真实 access token
  - 真实 Provider API key
  - 真实上传文件
  - 业务专用提示词
  - 最终业务权限判定

宿主业务代码：
  - 把既有 API 同步到 FastAction 的 adapter
  - 解析当前用户、会话和上下文的 adapter
  - 执行真实 API 的 adapter
  - 上传文件的 adapter
  - 宿主业务专用集成演示页
  - 宿主管理后台菜单和 UI 外壳集成
```

## 3. Workbench Rule / 工作台规则

```text
FastAction Workbench can be shipped as a generic demo and embedded by a host app.
It must not contain host-specific business routes, dictionaries, roles, entity
names, or real execution code. The generic test bench records simulated
ExecutionResult rows unless the host app explicitly wires its own executor.
```

```text
FastAction Workbench 可以作为通用演示随开源工程发布，也可以被宿主系统嵌入。
它不能包含宿主业务路由、业务字典、业务角色、业务实体名称或真实执行业务代码。
通用测试台默认只记录模拟 ExecutionResult；只有宿主系统显式接入自己的 executor
时，才执行真实业务 API。
```

## 4. Deletion Rule / 删除旧实现规则

```text
The old host implementation can be removed only after the host app imports this package
and all compatibility tests pass.
```

```text
只有在宿主系统改为导入该独立包，并且兼容测试通过后，才能删除宿主系统里的旧实现。
```

Required checks:

```text
1. FastAction package imports successfully.
2. Host app routes are still compatible.
3. Host business registrations load through a host adapter.
4. Existing chat/test-bench flows still work.
5. Write-confirmation and permission-denial states are verified.
6. No production route depends on deleted host files.
```

必要检查：

```text
1. FastAction 包可以成功导入。
2. 宿主系统路由仍然兼容。
3. 宿主业务注册数据通过 adapter 加载。
4. 既有聊天和测试台流程仍然可用。
5. 写操作确认和权限拒绝状态已验证。
6. 没有生产路由依赖被删除的宿主文件。
```

## 5. Registration Data vs Host Adapter / 注册数据与宿主适配器

```text
Store as registration data:
  - API IDs, names, intent examples, keywords
  - request method, endpoint, auth mode, timeout, retry policy
  - parameter schema, required fields, labels, user hints, UI input type
  - OptionSets and entity resolution sources
  - risk level, confirmation policy, permissions
  - response field exposure, redaction, card binding
  - provider presets and identity definitions
  - test scenario presets for demo context and quick questions

Keep in host adapter code:
  - real API execution functions
  - browser File / Blob / FormData handling
  - token extraction from the host runtime
  - host-specific network fallback and gateway selection
  - final business transaction handling
```

```text
应该作为注册数据：
  - API ID、名称、意图示例、关键词
  - 请求方法、路径、鉴权模式、超时、重试策略
  - 参数 schema、必填字段、业务标签、用户提示、输入控件类型
  - 字典 OptionSet 和实体校准来源
  - 风险等级、确认策略、权限
  - 返回字段暴露、脱敏、卡片绑定
  - Provider 预设和身份定义
  - 测试场景 preset 中的演示上下文和快捷问题

应该留在宿主 adapter 代码：
  - 真实 API 执行函数
  - 浏览器 File / Blob / FormData 处理
  - 从宿主运行时读取 token
  - 宿主系统特有的网络 fallback 和网关选择
  - 最终业务事务处理
```
