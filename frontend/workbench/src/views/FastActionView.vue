<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import AdminLayout from './AdminLayout.vue'
import { useToast } from '@/composables/useToast'
import {
  deleteFastActionApiDefinition,
  deleteFastActionIdentityDefinition,
  deleteFastActionProviderConfig,
  getFastActionApiDefinitions,
  getFastActionCardDefinitions,
  getFastActionHealth,
  getFastActionIdentityDefinitions,
  getFastActionKnowledgeDefinitions,
  getFastActionProviderConfigs,
  getFastActionRuns,
  planFastActionChat,
  saveFastActionApiDefinition,
  saveFastActionIdentityDefinition,
  saveFastActionProviderConfig,
  testFastActionProviderConfig
} from '@/api/fastaction'

const toast = useToast()

const operationOptions = ['list', 'detail', 'count', 'aggregate', 'create', 'update', 'delete', 'action', 'workflow']
const methodOptions = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
const authModeOptions = ['user_token', 'user_cookie', 'service_token', 'bearer_token', 'api_key', 'oauth2_client_credentials', 'basic', 'custom_header', 'mtls', 'host_proxy', 'none']
const riskOptions = ['read', 'write', 'destructive', 'external']
const statusOptions = ['active', 'disabled', 'draft']
const API_EDITOR_DRAFT_KEY = 'fastaction.workbench.apiEditorDraft.v1'
const helpTexts = {
  apiId: '唯一能力 ID，建议用 domain.action，例如 tasks.my_todos、orders.create。',
  nameZh: '给运营/管理员看的名称，例如“我的待办任务”。',
  operationType: '选择 API 行为类型：查询列表用 list，新增用 create，修改用 update，危险操作用 delete/destructive 配合确认。',
  descriptionZh: '说明用户什么意图会命中这个 API。例如“查询当前用户的待办任务列表”。',
  examplesZh: '一行一个用户说法，例如“我有哪些待办任务”。',
  keywordsZh: '一行一个关键词，例如“待办”“任务”“todo”。',
  endpoint: '真实 API 路径或宿主代理路径，例如 /api/v1/tasks/my-todos。不要填前端页面地址。',
  risk: '只读接口用 read；会写数据用 write；删除/不可逆操作用 destructive。',
  parameters: 'JSON Schema。示例：{"type":"object","required":["project_id"],"properties":{"project_id":{"type":"string","source":["context.project_id"]}}}',
  response: '控制返回数据怎么进入提示和日志。常用 data_path: "$"。',
  cardType: '选择结果展示卡片，例如 list_card 用于列表，confirm_card 用于确认。'
}

const loading = ref(true)
const saving = ref(false)
const deleting = ref(false)
const testingPlan = ref(false)
const health = ref(null)
const apiDefinitions = ref([])
const cardDefinitions = ref([])
const providerConfigs = ref([])
const identityDefinitions = ref([])
const knowledgeDefinitions = ref([])
const runs = ref([])
const selectedApiId = ref('')
const activeTab = ref('basic')
const searchText = ref('')
const operationFilter = ref('all')
const isEditing = ref(false)
const isCreating = ref(false)
const apiEditor = ref(null)
const sampleDataText = ref(defaultSampleDataText())
const planText = ref('我有哪些待办任务')
const planResult = ref(null)
const loadError = ref('')
const plannerMode = ref('deterministic')
const plannerProviderId = ref('')
const plannerIdentityId = ref('example-operator')
const providerEditor = ref(null)
const selectedProviderConfigId = ref('')
const providerSaving = ref(false)
const providerDeleting = ref(false)
const providerTesting = ref(false)
const providerTestResult = ref(null)
const identityEditor = ref(null)
const selectedIdentityConfigId = ref('')
const identitySaving = ref(false)
const identityDeleting = ref(false)
const draftSavedAt = ref('')
const apiSaveError = ref('')
const apiSaveSuccess = ref('')
const helpTooltip = ref(null)
let restoringDraft = false

const healthState = computed(() => health.value?.status || 'unknown')
const activeApis = computed(() => apiDefinitions.value.filter(item => item.status !== 'disabled'))
const selectedApi = computed(() => apiDefinitions.value.find(item => item.id === selectedApiId.value) || null)
const selectedCardType = computed(() => apiEditor.value?.cardType || selectedApi.value?.render?.card_type || 'generic_data_card')
const selectedCardDefinition = computed(() => cardDefinitions.value.find(card => card.card_type === selectedCardType.value) || null)
const selectedProviderConfig = computed(() => providerConfigs.value.find(item => item.id === selectedProviderConfigId.value) || null)
const selectedIdentityConfig = computed(() => identityDefinitions.value.find(item => item.id === selectedIdentityConfigId.value) || null)
const activeProviderConfigs = computed(() => providerConfigs.value.filter(item => item.is_active !== false))
const filteredApis = computed(() => {
  const keyword = searchText.value.trim().toLowerCase()
  return apiDefinitions.value.filter((api) => {
    const matchesOperation = operationFilter.value === 'all' || api.operation_type === operationFilter.value
    if (!matchesOperation) return false
    if (!keyword) return true
    return [
      api.id,
      textValue(api.name),
      textValue(api.intent?.description),
      api.request?.endpoint,
      api.render?.card_type
    ].some(value => String(value || '').toLowerCase().includes(keyword))
  })
})
const fieldBindings = computed(() => rowsToObject(apiEditor.value?.bindingRows || []))
const sampleData = computed(() => parseJsonSafely(sampleDataText.value, {}))
const previewProps = computed(() => applyFieldBindings(sampleData.value, fieldBindings.value))
const previewItems = computed(() => Array.isArray(previewProps.value.items) ? previewProps.value.items : [])
const canEdit = computed(() => Boolean(apiEditor.value))
const editorJsonPreview = computed(() => {
  try {
    return JSON.stringify(buildApiPayload({ silent: true }), null, 2)
  } catch {
    return '{}'
  }
})

function textValue(value) {
  if (!value) return '-'
  if (typeof value === 'string') return value
  return value.zh || value.en || Object.values(value)[0] || '-'
}

function localizedValue(value, locale) {
  if (!value) return ''
  if (typeof value === 'string') return locale === 'zh' ? value : ''
  return value[locale] || ''
}

function localizedList(value, locale) {
  if (!value) return []
  if (Array.isArray(value)) return value
  return Array.isArray(value[locale]) ? value[locale] : []
}

function splitLines(value) {
  return String(value || '')
    .split(/[\n,，]/)
    .map(item => item.trim())
    .filter(Boolean)
}

function formatJson(value) {
  return JSON.stringify(value ?? {}, null, 2)
}

function parseJsonSafely(value, fallback) {
  try {
    return JSON.parse(value || '{}')
  } catch {
    return fallback
  }
}

function parseJsonField(value, label, fallback = {}) {
  try {
    return JSON.parse(value || '{}')
  } catch (error) {
    throw new Error(`${label} 不是合法 JSON：${error.message}`)
  }
}

function saveApiEditorDraft() {
  if (restoringDraft || !apiEditor.value || !isEditing.value) return
  try {
    const payload = {
      savedAt: new Date().toISOString(),
      selectedApiId: selectedApiId.value,
      isCreating: isCreating.value,
      activeTab: activeTab.value,
      editor: apiEditor.value
    }
    localStorage.setItem(API_EDITOR_DRAFT_KEY, JSON.stringify(payload))
    draftSavedAt.value = payload.savedAt
  } catch {
    // Draft storage is best-effort; API save remains the source of truth.
  }
}

function restoreApiEditorDraft() {
  try {
    const raw = localStorage.getItem(API_EDITOR_DRAFT_KEY)
    if (!raw) return false
    const payload = JSON.parse(raw)
    if (!payload?.editor) return false
    restoringDraft = true
    selectedApiId.value = payload.selectedApiId || ''
    apiEditor.value = payload.editor
    isEditing.value = true
    isCreating.value = Boolean(payload.isCreating)
    activeTab.value = payload.activeTab || 'basic'
    draftSavedAt.value = payload.savedAt || ''
    toast.info('已恢复暂存草稿', '上次未保存的 API 注册内容已恢复')
    return true
  } catch {
    return false
  } finally {
    restoringDraft = false
  }
}

function clearApiEditorDraft() {
  try {
    localStorage.removeItem(API_EDITOR_DRAFT_KEY)
  } catch {
    // Ignore storage cleanup errors.
  }
  draftSavedAt.value = ''
}

function draftSavedLabel(value) {
  if (!value) return ''
  return new Date(value).toLocaleTimeString('zh-CN', { hour12: false })
}

function showHelp(event, text) {
  const rect = event.currentTarget?.getBoundingClientRect?.()
  const rawX = event.clientX || rect?.right || 24
  const rawY = event.clientY || rect?.bottom || 24
  const maxX = Math.max(16, window.innerWidth - 360)
  const maxY = Math.max(16, window.innerHeight - 160)
  helpTooltip.value = {
    text,
    x: Math.min(Math.max(16, rawX + 14), maxX),
    y: Math.min(Math.max(16, rawY + 14), maxY)
  }
}

function moveHelp(event) {
  if (!helpTooltip.value) return
  showHelp(event, helpTooltip.value.text)
}

function hideHelp() {
  helpTooltip.value = null
}

function makeAuthDefinition(mode) {
  if (mode === 'user_token') {
    return { mode, token_context_path: 'auth.access_token' }
  }
  return { mode }
}

function makeEditor(api = null) {
  const source = api || {
    id: '',
    name: { zh: '', en: '' },
    version: '1.0.0',
    status: 'active',
    operation_type: 'list',
    intent: { description: { zh: '', en: '' }, examples: { zh: [], en: [] }, keywords: { zh: [], en: [] } },
    request: {
      method: 'GET',
      endpoint: '',
      auth_mode: 'user_token',
      auth: makeAuthDefinition('user_token'),
      timeout_ms: 10000,
      retry: { enabled: false, max_attempts: 0 }
    },
    parameters: { type: 'object', required: [], properties: {} },
    response: { data_path: '$', exposed_fields: [], sensitive_fields: [], prompt_visible_fields: [], log_redaction: [] },
    policy: { risk: 'read', requires_confirmation: false, permissions: [], idempotency: 'safe' },
    render: { card_type: 'list_card', fallback_card_type: 'generic_data_card', field_bindings: { title: '结果列表', items: '$.data.items' } },
    metadata: { host_app: 'example' }
  }
  const authMode = source.request?.auth?.mode || source.request?.auth_mode || 'user_token'

  return {
    originalId: source.id || '',
    id: source.id || '',
    nameZh: localizedValue(source.name, 'zh'),
    nameEn: localizedValue(source.name, 'en'),
    version: source.version || '1.0.0',
    status: source.status || 'active',
    operationType: source.operation_type || 'list',
    descriptionZh: localizedValue(source.intent?.description, 'zh') || textValue(source.intent?.description),
    descriptionEn: localizedValue(source.intent?.description, 'en'),
    examplesZhText: localizedList(source.intent?.examples, 'zh').join('\n'),
    examplesEnText: localizedList(source.intent?.examples, 'en').join('\n'),
    keywordsZhText: localizedList(source.intent?.keywords, 'zh').join('\n'),
    keywordsEnText: localizedList(source.intent?.keywords, 'en').join('\n'),
    method: source.request?.method || 'GET',
    endpoint: source.request?.endpoint || '',
    authMode,
    authText: formatJson(source.request?.auth || makeAuthDefinition(authMode)),
    timeoutMs: source.request?.timeout_ms || 10000,
    retryText: formatJson(source.request?.retry || { enabled: false, max_attempts: 0 }),
    parametersText: formatJson(source.parameters || { type: 'object', required: [], properties: {} }),
    responseText: formatJson(source.response || {}),
    risk: source.policy?.risk || 'read',
    requiresConfirmation: Boolean(source.policy?.requires_confirmation),
    permissionsText: Array.isArray(source.policy?.permissions) ? source.policy.permissions.join('\n') : '',
    idempotency: source.policy?.idempotency || 'safe',
    cardType: source.render?.card_type || 'generic_data_card',
    fallbackCardType: source.render?.fallback_card_type || 'generic_data_card',
    bindingRows: objectToRows(source.render?.field_bindings || {}),
    metadataText: formatJson(source.metadata || {})
  }
}

function makeProviderEditor(provider = null) {
  const source = provider || {
    id: '',
    type: 'llm',
    provider: 'openai_compatible',
    base_url: '',
    model: '',
    capabilities: ['chat', 'json_schema'],
    routing: { tasks: ['planning'], priority: 10, fallback_provider_id: null },
    credentials: { mode: 'server_secret', secret_ref: '', api_key: null },
    default_headers: {},
    extra: {},
    is_active: true
  }
  return {
    originalId: source.id || '',
    id: source.id || '',
    type: source.type || 'llm',
    provider: source.provider || 'openai_compatible',
    baseUrl: source.base_url || '',
    model: source.model || '',
    capabilitiesText: (source.capabilities || []).join('\n'),
    routingTasksText: (source.routing?.tasks || ['planning']).join('\n'),
    routingPriority: source.routing?.priority ?? 10,
    fallbackProviderId: source.routing?.fallback_provider_id || '',
    credentialMode: source.credentials?.mode || 'server_secret',
    secretRef: source.credentials?.secret_ref || source.secret?.secret_ref || '',
    defaultHeadersText: formatJson(source.default_headers || {}),
    extraText: formatJson(source.extra || {}),
    isActive: source.is_active !== false
  }
}

function buildProviderPayload() {
  const editor = providerEditor.value
  if (!editor) throw new Error('没有可保存的 Provider')
  const id = editor.id.trim()
  if (!id) throw new Error('Provider ID 不能为空')
  if (!editor.model.trim()) throw new Error('模型名称不能为空')
  return {
    id,
    type: editor.type,
    provider: editor.provider,
    base_url: editor.baseUrl.trim() || null,
    model: editor.model.trim(),
    capabilities: splitLines(editor.capabilitiesText),
    routing: {
      tasks: splitLines(editor.routingTasksText),
      priority: Number(editor.routingPriority) || 10,
      fallback_provider_id: editor.fallbackProviderId.trim() || null
    },
    credentials: {
      mode: editor.credentialMode,
      secret_ref: editor.secretRef.trim() || null,
      api_key: null
    },
    default_headers: parseJsonField(editor.defaultHeadersText, '默认请求头'),
    extra: parseJsonField(editor.extraText, '扩展配置'),
    is_active: Boolean(editor.isActive)
  }
}

function makeIdentityEditor(identity = null) {
  const source = identity || {
    id: '',
    name: { zh: '', en: '' },
    host_app: 'example',
    actor_type: 'user',
    role_aliases: [],
    permissions: [],
    allowed_api_ids: [],
    denied_api_ids: [],
    system_prompt: { zh: '', en: '' },
    context_schema: {},
    risk_overrides: {},
    metadata: {},
    is_active: true
  }
  return {
    originalId: source.id || '',
    id: source.id || '',
    nameZh: localizedValue(source.name, 'zh') || textValue(source.name),
    nameEn: localizedValue(source.name, 'en'),
    hostApp: source.host_app || 'default',
    actorType: source.actor_type || 'user',
    roleAliasesText: (source.role_aliases || []).join('\n'),
    permissionsText: (source.permissions || []).join('\n'),
    allowedApiIdsText: (source.allowed_api_ids || []).join('\n'),
    deniedApiIdsText: (source.denied_api_ids || []).join('\n'),
    systemPromptZh: localizedValue(source.system_prompt, 'zh') || textValue(source.system_prompt),
    systemPromptEn: localizedValue(source.system_prompt, 'en'),
    contextSchemaText: formatJson(source.context_schema || {}),
    riskOverridesText: formatJson(source.risk_overrides || {}),
    metadataText: formatJson(source.metadata || {}),
    isActive: source.is_active !== false
  }
}

function buildIdentityPayload() {
  const editor = identityEditor.value
  if (!editor) throw new Error('没有可保存的身份定义')
  const id = editor.id.trim()
  if (!id) throw new Error('Identity ID 不能为空')
  if (!editor.nameZh.trim()) throw new Error('身份中文名称不能为空')
  return {
    id,
    name: { zh: editor.nameZh.trim(), en: editor.nameEn.trim() || editor.nameZh.trim() },
    host_app: editor.hostApp.trim() || 'default',
    actor_type: editor.actorType.trim() || 'user',
    role_aliases: splitLines(editor.roleAliasesText),
    permissions: splitLines(editor.permissionsText),
    allowed_api_ids: splitLines(editor.allowedApiIdsText),
    denied_api_ids: splitLines(editor.deniedApiIdsText),
    system_prompt: {
      zh: editor.systemPromptZh.trim(),
      en: editor.systemPromptEn.trim()
    },
    context_schema: parseJsonField(editor.contextSchemaText, '上下文 Schema'),
    risk_overrides: parseJsonField(editor.riskOverridesText, '风险覆盖'),
    metadata: parseJsonField(editor.metadataText, '身份元数据'),
    is_active: Boolean(editor.isActive)
  }
}

function objectToRows(value) {
  return Object.entries(value || {}).map(([target, source]) => ({
    id: `${target}_${Math.random().toString(36).slice(2)}`,
    target,
    source: String(source ?? '')
  }))
}

function rowsToObject(rows) {
  const result = {}
  for (const row of rows || []) {
    const target = String(row.target || '').trim()
    const source = String(row.source || '').trim()
    if (target && source) result[target] = source
  }
  return result
}

function buildApiPayload(options = {}) {
  const editor = apiEditor.value
  if (!editor) throw new Error('没有可保存的 API Definition')
  const id = editor.id.trim()
  if (!id) throw new Error('API ID 不能为空')
  if (!editor.nameZh.trim()) throw new Error('中文名称不能为空')
  if (!editor.descriptionZh.trim()) throw new Error('中文意图描述不能为空')
  if (!editor.endpoint.trim()) throw new Error('Endpoint 不能为空')

  const auth = parseJsonField(editor.authText, '鉴权配置', makeAuthDefinition(editor.authMode))
  if (!auth.mode) auth.mode = editor.authMode

  return {
    id,
    name: {
      zh: editor.nameZh.trim(),
      en: editor.nameEn.trim() || editor.nameZh.trim()
    },
    version: editor.version.trim() || '1.0.0',
    status: editor.status,
    operation_type: editor.operationType,
    intent: {
      description: {
        zh: editor.descriptionZh.trim(),
        en: editor.descriptionEn.trim()
      },
      examples: {
        zh: splitLines(editor.examplesZhText),
        en: splitLines(editor.examplesEnText)
      },
      keywords: {
        zh: splitLines(editor.keywordsZhText),
        en: splitLines(editor.keywordsEnText)
      }
    },
    request: {
      method: editor.method,
      endpoint: editor.endpoint.trim(),
      auth_mode: editor.authMode,
      auth,
      timeout_ms: Number(editor.timeoutMs) || 10000,
      retry: parseJsonField(editor.retryText, '重试配置', { enabled: false, max_attempts: 0 })
    },
    parameters: parseJsonField(editor.parametersText, '参数 Schema'),
    response: parseJsonField(editor.responseText, '返回配置'),
    policy: {
      risk: editor.risk,
      requires_confirmation: Boolean(editor.requiresConfirmation),
      permissions: splitLines(editor.permissionsText),
      idempotency: editor.idempotency.trim() || 'unknown'
    },
    render: {
      card_type: editor.cardType,
      fallback_card_type: editor.fallbackCardType || 'generic_data_card',
      field_bindings: rowsToObject(editor.bindingRows)
    },
    metadata: parseJsonField(editor.metadataText, '元数据')
  }
}

function selectApi(api) {
  selectedApiId.value = api.id
  apiEditor.value = makeEditor(api)
  isEditing.value = false
  isCreating.value = false
  activeTab.value = 'basic'
  planResult.value = null
  apiSaveError.value = ''
  apiSaveSuccess.value = ''
}

function startCreate() {
  selectedApiId.value = ''
  apiEditor.value = makeEditor()
  isEditing.value = true
  isCreating.value = true
  activeTab.value = 'basic'
  planResult.value = null
  apiSaveError.value = ''
  apiSaveSuccess.value = ''
  saveApiEditorDraft()
}

function startEdit() {
  if (!selectedApi.value) return
  apiEditor.value = makeEditor(selectedApi.value)
  isEditing.value = true
  isCreating.value = false
  apiSaveError.value = ''
  apiSaveSuccess.value = ''
  saveApiEditorDraft()
}

function cancelEdit() {
  clearApiEditorDraft()
  apiSaveError.value = ''
  apiSaveSuccess.value = ''
  if (selectedApi.value) {
    apiEditor.value = makeEditor(selectedApi.value)
    isEditing.value = false
    isCreating.value = false
  } else {
    apiEditor.value = null
    isEditing.value = false
    isCreating.value = false
  }
}

function addBindingRow() {
  if (!apiEditor.value) return
  apiEditor.value.bindingRows.push({
    id: `binding_${Date.now()}`,
    target: '',
    source: ''
  })
}

function removeBindingRow(index) {
  if (!apiEditor.value) return
  apiEditor.value.bindingRows.splice(index, 1)
}

function selectCard(cardType) {
  if (!apiEditor.value || !isEditing.value) return
  apiEditor.value.cardType = cardType
}

function selectProviderConfig(provider) {
  if (!provider) return
  selectedProviderConfigId.value = provider.id
  providerEditor.value = makeProviderEditor(provider)
  providerTestResult.value = null
}

function startCreateProvider() {
  selectedProviderConfigId.value = ''
  providerEditor.value = makeProviderEditor()
  providerTestResult.value = null
}

async function saveProviderConfig() {
  try {
    providerSaving.value = true
    const payload = buildProviderPayload()
    const saved = await saveFastActionProviderConfig(payload, Boolean(providerEditor.value?.originalId))
    const normalized = saved?.id ? saved : payload
    const index = providerConfigs.value.findIndex(item => item.id === normalized.id)
    if (index >= 0) providerConfigs.value.splice(index, 1, normalized)
    else providerConfigs.value.unshift(normalized)
    selectedProviderConfigId.value = normalized.id
    providerEditor.value = makeProviderEditor(normalized)
    toast.success('Provider 已保存', normalized.id)
  } catch (error) {
    toast.error('保存 Provider 失败', error.userMessage || error.message || 'Provider 配置保存失败')
  } finally {
    providerSaving.value = false
  }
}

async function deleteProviderConfig() {
  if (!selectedProviderConfig.value || !window.confirm(`确认删除 ${selectedProviderConfig.value.id}？`)) return
  try {
    providerDeleting.value = true
    await deleteFastActionProviderConfig(selectedProviderConfig.value.id)
    providerConfigs.value = providerConfigs.value.filter(item => item.id !== selectedProviderConfig.value.id)
    providerEditor.value = null
    selectedProviderConfigId.value = ''
    toast.success('Provider 已删除', '配置已移除')
  } catch (error) {
    toast.error('删除 Provider 失败', error.userMessage || error.message || 'Provider 删除失败')
  } finally {
    providerDeleting.value = false
  }
}

async function testProviderPreview() {
  const id = providerEditor.value?.id?.trim()
  if (!id) {
    toast.warning('先选择或保存 Provider', 'Provider ID 不能为空')
    return
  }
  try {
    providerTesting.value = true
    providerTestResult.value = await testFastActionProviderConfig(id, { live: false })
  } catch (error) {
    toast.error('Provider 预览失败', error.userMessage || error.message || 'Provider 测试失败')
  } finally {
    providerTesting.value = false
  }
}

function selectIdentityConfig(identity) {
  if (!identity) return
  selectedIdentityConfigId.value = identity.id
  identityEditor.value = makeIdentityEditor(identity)
}

function startCreateIdentity() {
  selectedIdentityConfigId.value = ''
  identityEditor.value = makeIdentityEditor()
}

async function saveIdentityConfig() {
  try {
    identitySaving.value = true
    const payload = buildIdentityPayload()
    const saved = await saveFastActionIdentityDefinition(payload, Boolean(identityEditor.value?.originalId))
    const index = identityDefinitions.value.findIndex(item => item.id === saved.id)
    if (index >= 0) identityDefinitions.value.splice(index, 1, saved)
    else identityDefinitions.value.unshift(saved)
    selectedIdentityConfigId.value = saved.id
    identityEditor.value = makeIdentityEditor(saved)
    toast.success('身份定义已保存', saved.id)
  } catch (error) {
    toast.error('保存身份失败', error.userMessage || error.message || '身份定义保存失败')
  } finally {
    identitySaving.value = false
  }
}

async function deleteIdentityConfig() {
  if (!selectedIdentityConfig.value || !window.confirm(`确认删除 ${selectedIdentityConfig.value.id}？`)) return
  try {
    identityDeleting.value = true
    await deleteFastActionIdentityDefinition(selectedIdentityConfig.value.id)
    identityDefinitions.value = identityDefinitions.value.filter(item => item.id !== selectedIdentityConfig.value.id)
    identityEditor.value = null
    selectedIdentityConfigId.value = ''
    toast.success('身份定义已删除', '配置已移除')
  } catch (error) {
    toast.error('删除身份失败', error.userMessage || error.message || '身份定义删除失败')
  } finally {
    identityDeleting.value = false
  }
}

async function loadPage(options = {}) {
  try {
    loading.value = true
    loadError.value = ''
    const results = await Promise.allSettled([
      getFastActionHealth(),
      getFastActionApiDefinitions(),
      getFastActionCardDefinitions(),
      getFastActionProviderConfigs(),
      getFastActionIdentityDefinitions(),
      getFastActionKnowledgeDefinitions(),
      getFastActionRuns({ limit: 30 })
    ])

    health.value = pickResult(results[0], null)
    apiDefinitions.value = ensureArray(pickResult(results[1], []))
    cardDefinitions.value = ensureArray(pickResult(results[2], []))
    providerConfigs.value = ensureArray(pickResult(results[3], []))
    identityDefinitions.value = ensureArray(pickResult(results[4], []))
    knowledgeDefinitions.value = ensureArray(pickResult(results[5], []))
    runs.value = ensureArray(pickResult(results[6], []))

    const rejected = results.find(item => item.status === 'rejected')
    if (rejected) {
      loadError.value = rejected.reason?.userMessage || rejected.reason?.message || 'FastAction 数据加载不完整'
      toast.error('加载失败', loadError.value)
    }

    if (!options.keepSelection) {
      const next = selectedApiId.value
        ? apiDefinitions.value.find(item => item.id === selectedApiId.value)
        : apiDefinitions.value[0]
      if (next) selectApi(next)
      else if (!isCreating.value) apiEditor.value = null
      if (providerConfigs.value[0]) selectProviderConfig(providerConfigs.value[0])
      if (identityDefinitions.value[0]) selectIdentityConfig(identityDefinitions.value[0])
      if (!plannerProviderId.value && activeProviderConfigs.value[0]) plannerProviderId.value = activeProviderConfigs.value[0].id
    }
  } finally {
    loading.value = false
  }
}

function pickResult(result, fallback) {
  return result.status === 'fulfilled' ? result.value : fallback
}

function ensureArray(value) {
  return Array.isArray(value) ? value : []
}

async function saveApi() {
  try {
    saving.value = true
    apiSaveError.value = ''
    apiSaveSuccess.value = ''
    const payload = buildApiPayload()
    const saved = await saveFastActionApiDefinition(payload, !isCreating.value)
    const index = apiDefinitions.value.findIndex(item => item.id === saved.id)
    if (index >= 0) apiDefinitions.value.splice(index, 1, saved)
    else apiDefinitions.value.unshift(saved)
    selectedApiId.value = saved.id
    apiEditor.value = makeEditor(saved)
    isEditing.value = false
    isCreating.value = false
    clearApiEditorDraft()
    apiSaveSuccess.value = `${saved.id} 已保存`
    toast.success('保存成功', `${saved.id} 已更新`)
  } catch (error) {
    apiSaveError.value = error.userMessage || error.message || 'API Definition 保存失败'
    toast.error('保存失败', apiSaveError.value)
  } finally {
    saving.value = false
  }
}

async function deleteApi() {
  if (!selectedApi.value || !window.confirm(`确认删除 ${selectedApi.value.id}？`)) return
  try {
    deleting.value = true
    await deleteFastActionApiDefinition(selectedApi.value.id)
    apiDefinitions.value = apiDefinitions.value.filter(item => item.id !== selectedApi.value.id)
    selectedApiId.value = ''
    apiEditor.value = null
    isEditing.value = false
    toast.success('删除成功', 'API Definition 已删除')
    if (apiDefinitions.value[0]) selectApi(apiDefinitions.value[0])
  } catch (error) {
    toast.error('删除失败', error.userMessage || error.message || 'API Definition 删除失败')
  } finally {
    deleting.value = false
  }
}

async function runPlannerTest() {
  if (!planText.value.trim()) {
    toast.warning('请输入测试语句', '例如：我有哪些待办任务')
    return
  }
  try {
    testingPlan.value = true
    planResult.value = await planFastActionChat({
      text: planText.value.trim(),
      context: {
        auth: { access_token: '__admin_runtime_token__' },
        workspace_id: 'all',
        limit: 5,
        locale: 'zh-CN'
      },
      params: {},
      host_app: 'example',
      locale: 'zh-CN',
      planner_mode: plannerMode.value,
      provider_id: plannerMode.value === 'deterministic' ? null : (plannerProviderId.value || null),
      identity_id: plannerIdentityId.value || null
    })
    runs.value = [
      {
        id: planResult.value.run_id || `local_${Date.now()}`,
        input_text: planText.value.trim(),
        selected_api_id: planResult.value.api?.id || null,
        confidence: planResult.value.confidence,
        created_at: new Date().toISOString()
      },
      ...runs.value
    ].slice(0, 30)
  } catch (error) {
    toast.error('测试失败', error.userMessage || error.message || 'Planner 测试失败')
  } finally {
    testingPlan.value = false
  }
}

function setSampleForCard() {
  sampleDataText.value = defaultSampleDataText(selectedCardType.value)
}

function readPath(data, path) {
  if (!path || path === '$') return data
  if (!path.startsWith('$.')) return undefined
  let current = data
  for (const part of path.slice(2).split('.')) {
    if (current && typeof current === 'object' && !Array.isArray(current)) {
      current = current[part]
    } else if (Array.isArray(current) && /^\d+$/.test(part)) {
      current = current[Number(part)]
    } else {
      return undefined
    }
  }
  return current
}

function writePath(target, path, value) {
  if (!path) return
  const parts = path.split('.')
  let current = target
  for (const part of parts.slice(0, -1)) {
    if (!current[part] || typeof current[part] !== 'object') current[part] = {}
    current = current[part]
  }
  current[parts[parts.length - 1]] = value
}

function applyFieldBindings(data, bindings) {
  const props = {}
  for (const [target, source] of Object.entries(bindings || {})) {
    const value = source.startsWith('$') ? readPath(data, source) : source
    writePath(props, target, value)
  }
  return props
}

function defaultSampleDataText(cardType = 'list_card') {
  const samples = {
    list_card: {
      data: {
        count: 3,
        tasks: [
          { id: 'task_001', name: '启动工作区', status: 'todo', workspace_name: 'Workspace Alpha', due_date: '2026-06-05' },
          { id: 'task_002', name: '复核执行清单', status: 'todo', workspace_name: 'Workspace Beta', due_date: '2026-06-06' },
          { id: 'task_003', name: '查看状态报告', status: 'doing', workspace_name: 'Workspace Beta', due_date: '2026-06-07' }
        ],
        items: [
          { title: '启动工作区', status: 'todo' },
          { title: '复核执行清单', status: 'todo' }
        ]
      }
    },
    detail_card: {
      data: {
        title: 'Workspace Beta',
        rows: [
          { label: '阶段', value: '施工' },
          { label: '面积', value: '150㎡' }
        ]
      }
    },
    metric_card: {
      data: { label: '待办任务', value: 3, trend: '+1' }
    },
    confirm_card: {
      data: { title: '确认执行操作', action: '更新任务状态' }
    },
    result_card: {
      data: { status: 'success', title: '操作完成', message: '任务状态已更新' }
    },
    generic_data_card: {
      data: { title: '返回数据', payload: { status: 'ok' } }
    }
  }
  return JSON.stringify(samples[cardType] || samples.list_card, null, 2)
}

function previewLabel(item, fallback = '未命名') {
  return item?.name || item?.title || item?.label || item?.id || fallback
}

function previewMeta(item) {
  return [item?.status, item?.workspace_name, item?.due_date].filter(Boolean).join(' · ')
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

watch(
  [apiEditor, isEditing, isCreating, activeTab],
  () => saveApiEditorDraft(),
  { deep: true }
)

onMounted(async () => {
  await loadPage()
  restoreApiEditorDraft()
})
</script>

<template>
  <AdminLayout>
    <div class="flex h-[calc(100vh-96px)] min-h-0 flex-col gap-4 overflow-hidden">
      <section class="rounded-2xl border border-neutral-200 bg-white/90 px-5 py-4 shadow-sm">
        <div class="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-3">
              <p class="text-xs font-semibold uppercase tracking-wider text-primary">FastAction Registry</p>
              <span class="hidden h-4 w-px bg-neutral-200 sm:block"></span>
              <p class="truncate text-sm text-neutral-500">API 能力、意图、鉴权、字段绑定和卡片预览</p>
            </div>
            <h2 class="mt-1 truncate text-2xl font-semibold text-neutral-950">自然语言 API 注册工作台</h2>
          </div>
          <div class="flex flex-col gap-2 xl:min-w-[520px]">
            <div class="grid grid-cols-3 gap-2">
              <div class="rounded-xl border border-neutral-200 bg-neutral-50 px-3 py-2.5">
                <p class="text-xs text-neutral-500">引擎</p>
                <p class="mt-0.5 text-base font-semibold" :class="healthState === 'healthy' ? 'text-success-700' : 'text-warning-700'">{{ healthState }}</p>
              </div>
              <div class="rounded-xl border border-info-200 bg-info-50 px-3 py-2.5">
                <p class="text-xs text-info-700">API</p>
                <p class="mt-0.5 text-base font-semibold text-info-700">{{ activeApis.length }}</p>
              </div>
              <div class="rounded-xl border border-success/20 bg-success-50 px-3 py-2.5">
                <p class="text-xs text-success-700">卡片</p>
                <p class="mt-0.5 text-base font-semibold text-success-700">{{ cardDefinitions.length }}</p>
              </div>
            </div>
            <div class="rounded-xl border border-neutral-200 bg-white px-3 py-2 text-xs leading-5 text-neutral-500">
              Host Adapter 可通过 Registry API 导入企业既有系统能力。
            </div>
          </div>
        </div>
        <div v-if="loadError" class="mt-2 rounded-lg border border-warning/20 bg-warning-50 px-3 py-1.5 text-xs text-warning-800">
          {{ loadError }}
        </div>
      </section>

      <div v-if="loading" class="flex flex-1 items-center justify-center rounded-lg border border-neutral-200 bg-white text-neutral-500 shadow-sm">
        <div class="text-center">
          <i class="fas fa-spinner fa-spin mb-2 text-2xl"></i>
          <p class="text-sm">加载 FastAction 引擎状态中...</p>
        </div>
      </div>

      <template v-else>
        <section class="grid flex-1 min-h-0 grid-cols-1 gap-4 overflow-hidden xl:grid-cols-[320px_minmax(0,1fr)_380px]">
          <aside class="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-sm">
            <div class="shrink-0 border-b border-neutral-100 p-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <h3 class="text-base font-semibold text-neutral-950">API Registry</h3>
                  <p class="mt-0.5 text-sm text-neutral-500">{{ filteredApis.length }} / {{ apiDefinitions.length }} 个能力</p>
                </div>
                <button class="rounded-xl bg-neutral-950 px-3 py-2 text-sm font-medium text-white hover:bg-neutral-800" @click="startCreate">
                  新增
                </button>
              </div>
              <div class="mt-3 grid grid-cols-[minmax(0,1fr)_112px] gap-2">
                <input v-model="searchText" class="w-full rounded-xl border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10" placeholder="搜索 API、路径、卡片">
                <select v-model="operationFilter" class="w-full rounded-xl border border-neutral-200 px-2 py-2 text-sm outline-none focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10">
                  <option value="all">全部</option>
                  <option v-for="item in operationOptions" :key="item" :value="item">{{ item }}</option>
                </select>
              </div>
            </div>

            <div class="min-h-0 flex-1 overflow-y-auto p-2">
              <button
                v-for="api in filteredApis"
                :key="api.id"
                class="mb-2 w-full rounded-xl border px-3 py-3 text-left transition-colors"
                :class="selectedApiId === api.id ? 'border-primary bg-primary/5' : 'border-neutral-100 hover:border-neutral-200 hover:bg-neutral-50'"
                @click="selectApi(api)"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <p class="truncate text-sm font-semibold text-neutral-900">{{ textValue(api.name) }}</p>
                    <p class="mt-1 truncate font-mono text-xs text-neutral-500">{{ api.id }}</p>
                  </div>
                  <span class="rounded-full bg-neutral-100 px-2 py-0.5 text-[11px] font-semibold text-neutral-600">{{ api.operation_type }}</span>
                </div>
                <p class="mt-2 truncate font-mono text-xs text-neutral-500">{{ api.request?.method }} {{ api.request?.endpoint }}</p>
                <div class="mt-1.5 flex flex-wrap gap-1.5">
                  <span class="rounded-md bg-info-50 px-2 py-0.5 text-[11px] text-info-700">{{ api.render?.card_type || 'generic_data_card' }}</span>
                  <span class="rounded-md bg-neutral-100 px-2 py-0.5 text-[11px] text-neutral-600">{{ api.policy?.risk || 'read' }}</span>
                </div>
              </button>
              <div v-if="!filteredApis.length" class="py-6 text-center text-xs text-neutral-500">
                <i class="fas fa-inbox mb-2 text-xl text-neutral-400"></i>
                <p>没有匹配的 API Definition。</p>
              </div>
            </div>
          </aside>

          <main class="flex min-h-0 min-w-0 flex-col overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-sm">
            <div class="shrink-0 border-b border-neutral-100 p-4">
              <div class="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
                <div class="min-w-0">
                  <p class="text-xs font-semibold uppercase tracking-wider text-neutral-400">API Definition</p>
                  <h3 class="mt-0.5 truncate text-xl font-semibold text-neutral-950">
                    {{ apiEditor ? (apiEditor.nameZh || apiEditor.id || '新 API Definition') : '选择一个 API' }}
                  </h3>
                  <p v-if="apiEditor" class="mt-1 truncate font-mono text-xs text-neutral-500">{{ apiEditor.method }} {{ apiEditor.endpoint || '-' }}</p>
                </div>
                <div class="flex flex-wrap gap-2">
                  <button class="rounded-xl border border-neutral-200 px-3 py-2 text-sm hover:bg-neutral-50" @click="loadPage({ keepSelection: true })">刷新</button>
                  <button v-if="selectedApi && !isEditing" class="rounded-xl border border-neutral-200 px-3 py-2 text-sm hover:bg-neutral-50" @click="startEdit">编辑</button>
                  <button v-if="selectedApi && !isEditing" class="rounded-xl border border-danger-200 px-3 py-2 text-sm text-danger-700 hover:bg-danger-50" :disabled="deleting" @click="deleteApi">删除</button>
                  <button v-if="isEditing" class="rounded-xl border border-neutral-200 px-3 py-2 text-sm hover:bg-neutral-50" @click="cancelEdit">取消</button>
                  <button v-if="isEditing" class="rounded-xl bg-neutral-950 px-3 py-2 text-sm font-medium text-white hover:bg-neutral-800 disabled:opacity-60" :disabled="saving" @click="saveApi">
                    {{ saving ? '保存中...' : '保存' }}
                  </button>
                </div>
              </div>

              <div v-if="apiEditor" class="mt-3 flex flex-wrap gap-1.5">
                <button
                  v-for="tabItem in [
                    ['basic', '基础'],
                    ['intent', '意图'],
                    ['request', '请求'],
                    ['schema', '参数'],
                    ['render', '卡片绑定'],
                    ['json', 'JSON']
                  ]"
                  :key="tabItem[0]"
                  class="rounded-xl px-3 py-2 text-sm"
                  :class="activeTab === tabItem[0] ? 'bg-neutral-950 text-white' : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'"
                  @click="activeTab = tabItem[0]"
                >
                  {{ tabItem[1] }}
                </button>
                <span v-if="isEditing && draftSavedAt" class="inline-flex items-center rounded-full bg-info-50 px-2.5 py-1 text-xs text-info-700">
                  已暂存 {{ draftSavedLabel(draftSavedAt) }}
                </span>
              </div>
            </div>

            <div v-if="!apiEditor" class="flex flex-1 items-center justify-center p-8 text-center text-neutral-500">
              <div>
                <i class="fas fa-diagram-project mb-2 text-2xl text-neutral-400"></i>
                <p>从左侧选择 API，或新增一个 API Definition。</p>
              </div>
            </div>

            <div v-else class="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
              <div v-if="apiSaveError" class="rounded-xl border border-danger-200 bg-danger-50 px-4 py-3 text-sm text-danger-700">
                <p class="font-semibold">保存失败</p>
                <p class="mt-1">{{ apiSaveError }}</p>
              </div>
              <div v-else-if="apiSaveSuccess" class="rounded-xl border border-success-200 bg-success-50 px-4 py-3 text-sm text-success-700">
                {{ apiSaveSuccess }}
              </div>
              <section v-show="activeTab === 'basic'" class="grid grid-cols-1 gap-4 xl:grid-cols-2">
                <label class="text-sm font-medium text-neutral-700">
                  API ID
                  <button type="button" class="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-neutral-300 text-[10px] text-neutral-500 hover:border-neutral-500 hover:text-neutral-800" @click.stop.prevent @mouseenter="showHelp($event, helpTexts.apiId)" @mousemove="moveHelp" @mouseleave="hideHelp" @focus="showHelp($event, helpTexts.apiId)" @blur="hideHelp">i</button>
                  <input v-model.trim="apiEditor.id" :disabled="!isEditing || (!isCreating && apiEditor.originalId)" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  中文名称
                  <button type="button" class="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-neutral-300 text-[10px] text-neutral-500 hover:border-neutral-500 hover:text-neutral-800" @click.stop.prevent @mouseenter="showHelp($event, helpTexts.nameZh)" @mousemove="moveHelp" @mouseleave="hideHelp" @focus="showHelp($event, helpTexts.nameZh)" @blur="hideHelp">i</button>
                  <input v-model.trim="apiEditor.nameZh" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  英文名称
                  <input v-model.trim="apiEditor.nameEn" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  版本
                  <input v-model.trim="apiEditor.version" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  状态
                  <select v-model="apiEditor.status" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                    <option v-for="item in statusOptions" :key="item" :value="item">{{ item }}</option>
                  </select>
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  操作类型
                  <button type="button" class="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-neutral-300 text-[10px] text-neutral-500 hover:border-neutral-500 hover:text-neutral-800" @click.stop.prevent @mouseenter="showHelp($event, helpTexts.operationType)" @mousemove="moveHelp" @mouseleave="hideHelp" @focus="showHelp($event, helpTexts.operationType)" @blur="hideHelp">i</button>
                  <select v-model="apiEditor.operationType" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                    <option v-for="item in operationOptions" :key="item" :value="item">{{ item }}</option>
                  </select>
                </label>
              </section>

              <section v-show="activeTab === 'intent'" class="grid grid-cols-1 gap-4 xl:grid-cols-2">
                <label class="text-sm font-medium text-neutral-700 xl:col-span-2">
                  中文意图描述
                  <button type="button" class="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-neutral-300 text-[10px] text-neutral-500 hover:border-neutral-500 hover:text-neutral-800" @click.stop.prevent @mouseenter="showHelp($event, helpTexts.descriptionZh)" @mousemove="moveHelp" @mouseleave="hideHelp" @focus="showHelp($event, helpTexts.descriptionZh)" @blur="hideHelp">i</button>
                  <textarea v-model="apiEditor.descriptionZh" :disabled="!isEditing" rows="3" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50"></textarea>
                </label>
                <label class="text-sm font-medium text-neutral-700 xl:col-span-2">
                  英文意图描述
                  <textarea v-model="apiEditor.descriptionEn" :disabled="!isEditing" rows="2" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50"></textarea>
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  中文示例
                  <button type="button" class="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-neutral-300 text-[10px] text-neutral-500 hover:border-neutral-500 hover:text-neutral-800" @click.stop.prevent @mouseenter="showHelp($event, helpTexts.examplesZh)" @mousemove="moveHelp" @mouseleave="hideHelp" @focus="showHelp($event, helpTexts.examplesZh)" @blur="hideHelp">i</button>
                  <textarea v-model="apiEditor.examplesZhText" :disabled="!isEditing" rows="5" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50"></textarea>
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  中文关键词
                  <button type="button" class="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-neutral-300 text-[10px] text-neutral-500 hover:border-neutral-500 hover:text-neutral-800" @click.stop.prevent @mouseenter="showHelp($event, helpTexts.keywordsZh)" @mousemove="moveHelp" @mouseleave="hideHelp" @focus="showHelp($event, helpTexts.keywordsZh)" @blur="hideHelp">i</button>
                  <textarea v-model="apiEditor.keywordsZhText" :disabled="!isEditing" rows="5" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50"></textarea>
                </label>
              </section>

              <section v-show="activeTab === 'request'" class="grid grid-cols-1 gap-4 xl:grid-cols-2">
                <label class="text-sm font-medium text-neutral-700">
                  Method
                  <select v-model="apiEditor.method" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                    <option v-for="item in methodOptions" :key="item" :value="item">{{ item }}</option>
                  </select>
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  鉴权模式
                  <select v-model="apiEditor.authMode" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50" @change="apiEditor.authText = formatJson(makeAuthDefinition(apiEditor.authMode))">
                    <option v-for="item in authModeOptions" :key="item" :value="item">{{ item }}</option>
                  </select>
                </label>
                <label class="text-sm font-medium text-neutral-700 xl:col-span-2">
                  Endpoint
                  <button type="button" class="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-neutral-300 text-[10px] text-neutral-500 hover:border-neutral-500 hover:text-neutral-800" @click.stop.prevent @mouseenter="showHelp($event, helpTexts.endpoint)" @mousemove="moveHelp" @mouseleave="hideHelp" @focus="showHelp($event, helpTexts.endpoint)" @blur="hideHelp">i</button>
                  <input v-model.trim="apiEditor.endpoint" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  Timeout ms
                  <input v-model.number="apiEditor.timeoutMs" :disabled="!isEditing" type="number" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  风险等级
                  <button type="button" class="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-neutral-300 text-[10px] text-neutral-500 hover:border-neutral-500 hover:text-neutral-800" @click.stop.prevent @mouseenter="showHelp($event, helpTexts.risk)" @mousemove="moveHelp" @mouseleave="hideHelp" @focus="showHelp($event, helpTexts.risk)" @blur="hideHelp">i</button>
                  <select v-model="apiEditor.risk" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                    <option v-for="item in riskOptions" :key="item" :value="item">{{ item }}</option>
                  </select>
                </label>
                <label class="flex items-center gap-2 text-sm font-medium text-neutral-700">
                  <input v-model="apiEditor.requiresConfirmation" :disabled="!isEditing" type="checkbox" class="rounded border-neutral-300 text-primary focus:ring-primary">
                  执行前需要确认
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  幂等性
                  <input v-model.trim="apiEditor.idempotency" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                </label>
                <label class="text-sm font-medium text-neutral-700 xl:col-span-2">
                  鉴权配置 JSON
                  <textarea v-model="apiEditor.authText" :disabled="!isEditing" rows="5" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50"></textarea>
                </label>
                <label class="text-sm font-medium text-neutral-700 xl:col-span-2">
                  权限标识
                  <textarea v-model="apiEditor.permissionsText" :disabled="!isEditing" rows="3" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50"></textarea>
                </label>
              </section>

              <section v-show="activeTab === 'schema'" class="grid grid-cols-1 gap-4 xl:grid-cols-2">
                <label class="text-sm font-medium text-neutral-700">
                  参数 Schema JSON
                  <button type="button" class="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-neutral-300 text-[10px] text-neutral-500 hover:border-neutral-500 hover:text-neutral-800" @click.stop.prevent @mouseenter="showHelp($event, helpTexts.parameters)" @mousemove="moveHelp" @mouseleave="hideHelp" @focus="showHelp($event, helpTexts.parameters)" @blur="hideHelp">i</button>
                  <textarea v-model="apiEditor.parametersText" :disabled="!isEditing" rows="14" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50"></textarea>
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  返回配置 JSON
                  <button type="button" class="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-neutral-300 text-[10px] text-neutral-500 hover:border-neutral-500 hover:text-neutral-800" @click.stop.prevent @mouseenter="showHelp($event, helpTexts.response)" @mousemove="moveHelp" @mouseleave="hideHelp" @focus="showHelp($event, helpTexts.response)" @blur="hideHelp">i</button>
                  <textarea v-model="apiEditor.responseText" :disabled="!isEditing" rows="14" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50"></textarea>
                </label>
                <label class="text-sm font-medium text-neutral-700 xl:col-span-2">
                  元数据 JSON
                  <textarea v-model="apiEditor.metadataText" :disabled="!isEditing" rows="5" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50"></textarea>
                </label>
              </section>

              <section v-show="activeTab === 'render'" class="space-y-4">
                <div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
                  <label class="text-sm font-medium text-neutral-700">
                    Card Type
                    <button type="button" class="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-neutral-300 text-[10px] text-neutral-500 hover:border-neutral-500 hover:text-neutral-800" @click.stop.prevent @mouseenter="showHelp($event, helpTexts.cardType)" @mousemove="moveHelp" @mouseleave="hideHelp" @focus="showHelp($event, helpTexts.cardType)" @blur="hideHelp">i</button>
                    <select v-model="apiEditor.cardType" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                      <option v-for="card in cardDefinitions" :key="card.card_type" :value="card.card_type">{{ card.card_type }}</option>
                      <option value="generic_data_card">generic_data_card</option>
                    </select>
                  </label>
                  <label class="text-sm font-medium text-neutral-700">
                    Fallback Card
                    <input v-model.trim="apiEditor.fallbackCardType" :disabled="!isEditing" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                  </label>
                </div>

                <div class="rounded-lg border border-neutral-200">
                  <div class="flex items-center justify-between border-b border-neutral-100 px-3 py-2">
                    <p class="text-sm font-semibold text-neutral-900">字段绑定</p>
                    <button class="rounded-lg border border-neutral-200 px-2.5 py-1.5 text-xs hover:bg-neutral-50 disabled:opacity-50" :disabled="!isEditing" @click="addBindingRow">新增字段</button>
                  </div>
                  <div class="divide-y divide-neutral-100">
                    <div v-for="(row, index) in apiEditor.bindingRows" :key="row.id" class="grid grid-cols-1 gap-2 p-3 xl:grid-cols-[1fr_1fr_auto]">
                      <input v-model.trim="row.target" :disabled="!isEditing" class="rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary disabled:bg-neutral-50" placeholder="props 字段，如 items">
                      <input v-model.trim="row.source" :disabled="!isEditing" class="rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary disabled:bg-neutral-50" placeholder="$.data.tasks 或字面量">
                      <button class="rounded-lg border border-danger-200 px-3 py-2 text-xs text-danger-700 hover:bg-danger-50 disabled:opacity-50" :disabled="!isEditing" @click="removeBindingRow(index)">删除</button>
                    </div>
                    <p v-if="!apiEditor.bindingRows.length" class="p-4 text-center text-sm text-neutral-500">暂无字段绑定。</p>
                  </div>
                </div>
              </section>

              <section v-show="activeTab === 'json'" class="space-y-3">
                <p class="text-sm text-neutral-500">保存前的完整 API Definition 结构。</p>
                <pre class="max-h-[620px] overflow-auto rounded-lg bg-neutral-950 p-4 text-xs leading-5 text-neutral-100">{{ editorJsonPreview }}</pre>
              </section>
            </div>
          </main>

          <aside class="min-h-0 space-y-4 overflow-y-auto pr-1">
            <section class="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <h3 class="text-base font-semibold text-neutral-950">卡片预览</h3>
                  <p class="mt-0.5 text-sm text-neutral-500">{{ selectedCardType }}</p>
                </div>
                <button class="rounded-xl border border-neutral-200 px-3 py-2 text-sm hover:bg-neutral-50" @click="setSampleForCard">样例数据</button>
              </div>

              <div class="mt-3 rounded-xl border border-neutral-200 bg-neutral-50 p-2">
                <div v-if="selectedCardType === 'list_card'" class="rounded-lg border border-neutral-200 bg-white p-4">
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <p class="font-semibold text-neutral-900">{{ previewProps.title || '列表卡片' }}</p>
                      <p class="mt-1 text-xs text-neutral-500">{{ previewItems.length }} 条记录</p>
                    </div>
                    <span class="rounded-full bg-info-50 px-2 py-1 text-xs text-info-700">list</span>
                  </div>
                  <div class="mt-3 space-y-2">
                    <div v-for="(item, index) in previewItems.slice(0, 4)" :key="item.id || index" class="rounded-lg border border-neutral-100 bg-neutral-50 px-3 py-2">
                      <p class="text-sm font-medium text-neutral-900">{{ previewLabel(item, `记录 ${index + 1}`) }}</p>
                      <p class="mt-1 text-xs text-neutral-500">{{ previewMeta(item) || '暂无附加信息' }}</p>
                    </div>
                    <p v-if="!previewItems.length" class="py-4 text-center text-sm text-neutral-400">字段绑定后显示列表数据</p>
                  </div>
                </div>

                <div v-else-if="selectedCardType === 'detail_card'" class="rounded-lg border border-neutral-200 bg-white p-4">
                  <p class="font-semibold text-neutral-900">{{ previewProps.title || sampleData.data?.title || '详情卡片' }}</p>
                  <div class="mt-3 space-y-2">
                    <div v-for="(row, index) in (previewProps.rows || sampleData.data?.rows || [])" :key="index" class="flex justify-between gap-4 rounded-lg bg-neutral-50 px-3 py-2 text-sm">
                      <span class="text-neutral-500">{{ row.label }}</span>
                      <span class="font-medium text-neutral-900">{{ row.value }}</span>
                    </div>
                  </div>
                </div>

                <div v-else-if="selectedCardType === 'metric_card'" class="rounded-lg border border-neutral-200 bg-white p-4">
                  <p class="text-sm text-neutral-500">{{ previewProps.label || sampleData.data?.label || '指标' }}</p>
                  <p class="mt-2 text-3xl font-bold text-neutral-900">{{ previewProps.value ?? sampleData.data?.value ?? '-' }}</p>
                  <p class="mt-2 text-xs text-success-700">{{ previewProps.trend || sampleData.data?.trend || '稳定' }}</p>
                </div>

                <div v-else-if="selectedCardType === 'confirm_card'" class="rounded-lg border border-warning/20 bg-white p-4">
                  <p class="font-semibold text-neutral-900">{{ previewProps.title || sampleData.data?.title || '确认操作' }}</p>
                  <p class="mt-2 text-sm text-neutral-500">{{ previewProps.action || sampleData.data?.action || '执行已注册 API' }}</p>
                  <div class="mt-4 flex gap-2">
                    <button class="rounded-lg bg-neutral-900 px-3 py-2 text-xs text-white">确认</button>
                    <button class="rounded-lg border border-neutral-200 px-3 py-2 text-xs">取消</button>
                  </div>
                </div>

                <div v-else-if="selectedCardType === 'result_card'" class="rounded-lg border border-success/20 bg-white p-4">
                  <span class="rounded-full bg-success-50 px-2 py-1 text-xs text-success-700">{{ previewProps.status || sampleData.data?.status || 'success' }}</span>
                  <p class="mt-3 font-semibold text-neutral-900">{{ previewProps.title || sampleData.data?.title || '操作完成' }}</p>
                  <p class="mt-2 text-sm text-neutral-500">{{ previewProps.message || sampleData.data?.message || '结果已返回' }}</p>
                </div>

                <div v-else class="rounded-lg border border-neutral-200 bg-white p-4">
                  <p class="font-semibold text-neutral-900">{{ previewProps.title || '通用数据卡' }}</p>
                  <pre class="mt-3 max-h-64 overflow-auto rounded-lg bg-neutral-950 p-3 text-xs text-neutral-100">{{ JSON.stringify(previewProps, null, 2) }}</pre>
                </div>
              </div>

              <label class="mt-3 block text-sm font-medium text-neutral-700">
                示例 API 响应 JSON
                <textarea v-model="sampleDataText" rows="6" class="mt-1 w-full rounded-xl border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10"></textarea>
              </label>
            </section>

            <section class="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
              <h3 class="text-base font-semibold text-neutral-950">卡片样式</h3>
              <div class="mt-2 grid max-h-48 grid-cols-1 gap-2 overflow-y-auto pr-1">
                <button
                  v-for="card in cardDefinitions"
                  :key="card.card_type"
                  class="rounded-lg border px-3 py-2 text-left transition-colors"
                  :class="selectedCardType === card.card_type ? 'border-primary bg-primary/5' : 'border-neutral-100 hover:bg-neutral-50'"
                  @click="selectCard(card.card_type)"
                >
                  <p class="text-sm font-medium text-neutral-900">{{ textValue(card.name) }}</p>
                  <p class="mt-1 font-mono text-xs text-neutral-500">{{ card.card_type }}</p>
                </button>
                <p v-if="!cardDefinitions.length" class="text-sm text-neutral-500">暂无卡片协议。</p>
              </div>
            </section>

            <section class="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
              <h3 class="text-base font-semibold text-neutral-950">Planner 测试</h3>
              <div class="mt-2 grid grid-cols-1 gap-2 md:grid-cols-3 xl:grid-cols-1 2xl:grid-cols-3">
                <label class="text-xs font-medium text-neutral-600">
                  模式
                  <select v-model="plannerMode" class="mt-1 w-full rounded-lg border border-neutral-200 px-2 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10">
                    <option value="deterministic">deterministic</option>
                    <option value="hybrid">hybrid</option>
                    <option value="llm">llm</option>
                  </select>
                </label>
                <label class="text-xs font-medium text-neutral-600">
                  身份
                  <select v-model="plannerIdentityId" class="mt-1 w-full rounded-lg border border-neutral-200 px-2 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10">
                    <option value="">不指定</option>
                    <option v-for="identity in identityDefinitions" :key="identity.id" :value="identity.id">{{ identity.id }}</option>
                  </select>
                </label>
                <label class="text-xs font-medium text-neutral-600">
                  Provider
                  <select v-model="plannerProviderId" :disabled="plannerMode === 'deterministic'" class="mt-1 w-full rounded-lg border border-neutral-200 px-2 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-neutral-50">
                    <option value="">自动选择</option>
                    <option v-for="provider in activeProviderConfigs" :key="provider.id" :value="provider.id">{{ provider.id }}</option>
                  </select>
                </label>
              </div>
              <div class="mt-3 flex gap-2">
                <input v-model="planText" class="min-w-0 flex-1 rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10" placeholder="输入一句自然语言">
                <button class="rounded-lg bg-neutral-900 px-3 py-2 text-sm text-white disabled:opacity-60" :disabled="testingPlan" @click="runPlannerTest">测试</button>
              </div>
              <div v-if="planResult" class="mt-3 rounded-lg bg-neutral-50 p-3 text-xs">
                <p><span class="text-neutral-500">Action：</span><span class="font-mono text-neutral-900">{{ planResult.action }}</span></p>
                <p class="mt-1"><span class="text-neutral-500">API：</span><span class="font-mono text-neutral-900">{{ planResult.api?.id || '-' }}</span></p>
                <pre class="mt-2 max-h-48 overflow-auto rounded-lg bg-white p-2 text-neutral-800">{{ JSON.stringify(planResult.params || {}, null, 2) }}</pre>
              </div>
            </section>

            <section class="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
              <div class="flex items-center justify-between">
                <h3 class="text-base font-semibold text-neutral-950">Runs & Audit</h3>
                <span class="text-xs text-neutral-400">{{ runs.length }} 条</span>
              </div>
              <div v-if="!runs.length" class="py-4 text-center text-xs text-neutral-500">暂无运行记录。</div>
              <div v-else class="mt-2 max-h-64 divide-y divide-neutral-100 overflow-y-auto pr-1">
                <article v-for="run in runs" :key="run.id" class="py-2">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="truncate text-xs font-medium text-neutral-900">{{ run.input_text || run.id }}</p>
                      <p class="mt-0.5 truncate text-[11px] text-neutral-500">{{ run.selected_api_id || '未命中 API' }} · confidence {{ run.confidence ?? '-' }}</p>
                    </div>
                    <span class="shrink-0 text-[10px] text-neutral-400">{{ formatDate(run.created_at) }}</span>
                  </div>
                </article>
              </div>
            </section>
          </aside>
        </section>
      </template>
    </div>
    <div
      v-if="helpTooltip"
      class="pointer-events-none fixed z-[9999] max-w-[340px] rounded-lg bg-neutral-950 px-3 py-2 text-xs leading-5 text-white shadow-lg"
      :style="{ left: `${helpTooltip.x}px`, top: `${helpTooltip.y}px` }"
    >
      {{ helpTooltip.text }}
    </div>
  </AdminLayout>
</template>
