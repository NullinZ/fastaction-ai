export const defaultFastActionTestScenario = {
  id: 'example_workspace',
  name: 'Generic demo scenario',
  hostApp: 'example',
  locale: 'zh-CN',
  context: {
    auth: { access_token: '__admin_runtime_token__' },
    workspace_id: 'all',
    current_workspace: { id: 'demo_workspace', name: 'Demo Workspace' },
    available_entities: {
      workspace: [
        { id: 'demo_workspace', name: 'Demo Workspace', aliases: ['演示空间', '默认空间'] }
      ]
    },
    limit: 5,
    locale: 'zh-CN'
  },
  quickQuestions: [
    '我有哪些待办任务',
    '把状态改成完成',
    '查询本周统计',
    '上传附件并创建记录'
  ],
  preferredProviderCapabilities: ['model_pool', 'balanced_routing', 'chat']
}
