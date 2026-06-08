<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AdminLayout from './AdminLayout.vue'
import { useToast } from '@/composables/useToast'
import {
  clearFastActionTestMessages,
  deleteFastActionIdentityDefinition,
  deleteFastActionProviderConfig,
  getFastActionHealth,
  getFastActionHostExecutors,
  getFastActionIdentityDefinitions,
  getFastActionKnowledgeDefinitions,
  getFastActionProviderModelPoolStatus,
  getFastActionProviderConfigs,
  getFastActionProviderPresets,
  getFastActionTestMessages,
  planFastActionChat,
  saveFastActionIdentityDefinition,
  saveFastActionProviderConfig,
  testFastActionProviderConfig,
  transcribeFastActionAudio
} from '@/api/fastaction'
import { defaultFastActionTestScenario } from '@/testScenarios'

const toast = useToast()
const MAX_ATTACHMENTS = 6
const MAX_ATTACHMENT_SIZE = 30 * 1024 * 1024
const ATTACHMENT_ACCEPT = 'image/*,application/pdf,.pdf,video/*,audio/*,.dwg,.dxf'
const ATTACHMENT_KIND_LABELS = {
  image: '图片',
  pdf: 'PDF',
  video: '视频',
  audio: '音频',
  dwg: 'DWG'
}
const USER_PHONE_WIDTH = 360
const DEBUG_TRACE_WIDTH = 520
const PHONE_HEIGHT = 782
const PHONE_GAP = 12
const PREVIEW_RESIZE_HANDLE_WIDTH = 14
const RUN_CONTROL_MIN_WIDTH = 300
const PREVIEW_LEFT_MIN_WIDTH = 420
const MIN_PHONE_SCALE = 0.42
const MAX_PHONE_SCALE = 1.5
const FASTACTION_TEST_SESSION_KEY = 'fastaction_test_session_id'
const FASTACTION_TEST_SPLIT_KEY = 'fastaction_test_preview_split_ratio'

const loading = ref(true)
const health = ref(null)
const providerConfigs = ref([])
const providerPresets = ref([])
const hostExecutorDefinitions = ref([])
const identityDefinitions = ref([])
const knowledgeDefinitions = ref([])
const modelPoolStatus = ref(null)
const loadError = ref('')

const selectedProviderId = ref('')
const providerEditor = ref(null)
const providerSaving = ref(false)
const providerDeleting = ref(false)
const providerTesting = ref(false)
const providerTestResult = ref(null)

const selectedIdentityId = ref('')
const identityEditor = ref(null)
const identitySaving = ref(false)
const identityDeleting = ref(false)

const plannerMode = ref('hybrid')
const noApiHitStrategy = ref('hybrid')
const plannerProviderId = ref('')
const plannerIdentityId = ref('')
const testInput = ref('')
const testSending = ref(false)
const testResult = ref(null)
const systemSettingsCollapsed = ref(false)
const fileInputRef = ref(null)
const selectedAttachments = ref([])
const composerNotice = ref('')
const testSessionId = ref(resolveTestSessionId())
const voiceSupported = ref(false)
const isRecording = ref(false)
const voiceBusy = ref(false)
const previewStageRef = ref(null)
const phoneViewportRef = ref(null)
const userPreviewScrollRef = ref(null)
const debugTraceScrollRef = ref(null)
const phoneScale = ref(1)
const previewLeftWidth = ref(null)
const previewSplitRatio = ref(resolvePreviewSplitRatio())
const isPreviewResizing = ref(false)
const contextText = ref(formatJson(defaultFastActionTestScenario.context))
const paramsText = ref(formatJson({}))
const chatMessages = ref(defaultChatMessages())
const quickQuestions = defaultFastActionTestScenario.quickQuestions
let mediaRecorder = null
let mediaStream = null
let recordingTimer = null
let audioChunks = []
let previewResizeObserver = null
let previewScrollSyncing = false

const healthState = computed(() => health.value?.status || 'unknown')
const selectedProvider = computed(() => providerConfigs.value.find(item => item.id === selectedProviderId.value) || null)
const selectedIdentity = computed(() => identityDefinitions.value.find(item => item.id === selectedIdentityId.value) || null)
const activeProviderConfigs = computed(() => providerConfigs.value.filter(item => item.is_active !== false))
const providerOptions = computed(() => {
  const values = new Set([
    ...providerPresets.value.map(item => item.provider).filter(Boolean),
    ...providerConfigs.value.map(item => item.provider).filter(Boolean)
  ])
  return Array.from(values)
})
const modelPoolRegisteredProvider = computed(() => pickModelPoolProvider(providerConfigs.value))
const modelPoolProvider = computed(() => modelPoolRegisteredProvider.value || pickModelPoolProvider(providerPresets.value) || null)
const modelPoolModels = computed(() => Array.isArray(modelPoolStatus.value?.models) ? modelPoolStatus.value.models : [])
const modelPoolChatModels = computed(() => modelPoolModels.value.filter(item => item.supports_chat))
const modelPoolUsableModels = computed(() => modelPoolChatModels.value.filter(item => item.is_enabled && !item.is_exhausted))
const modelPoolServiceLabel = computed(() => {
  const provider = modelPoolProvider.value
  if (!provider) return '未注册支持 model_pool 的 Provider'
  const service = provider.extra?.service || provider.provider || 'provider'
  return `${provider.id} · ${service}`
})
const activeHostExecutorDefinitions = computed(() => hostExecutorDefinitions.value.filter(item => item.is_active !== false && item.status !== 'disabled'))
const testProviderLabel = computed(() => {
  if (plannerMode.value === 'deterministic') return '本地规则'
  return plannerProviderId.value || '未选择'
})
const userPhoneShellStyle = computed(() => ({
  width: `${Math.round(USER_PHONE_WIDTH * phoneScale.value)}px`,
  height: `${Math.round(PHONE_HEIGHT * phoneScale.value)}px`
}))
const userPhoneFrameStyle = computed(() => ({
  width: `${USER_PHONE_WIDTH}px`,
  height: `${PHONE_HEIGHT}px`,
  transform: `scale(${phoneScale.value})`,
  transformOrigin: 'top left'
}))
const debugTraceShellStyle = computed(() => ({
  width: `${Math.round(DEBUG_TRACE_WIDTH * phoneScale.value)}px`,
  height: `${Math.round(PHONE_HEIGHT * phoneScale.value)}px`
}))
const debugTraceFrameStyle = computed(() => ({
  width: `${DEBUG_TRACE_WIDTH}px`,
  height: `${PHONE_HEIGHT}px`,
  transform: `scale(${phoneScale.value})`,
  transformOrigin: 'top left'
}))
const previewStageStyle = computed(() => ({
  '--fastaction-preview-left-width': `${previewLeftWidth.value || USER_PHONE_WIDTH + DEBUG_TRACE_WIDTH + PHONE_GAP}px`
}))
const runControlShellStyle = computed(() => ({
  height: `${Math.round(PHONE_HEIGHT * phoneScale.value)}px`
}))
const runControlBodyStyle = computed(() => ({
  height: `${Math.max(420, Math.round(PHONE_HEIGHT * phoneScale.value - 74))}px`
}))
const phoneTargetWidth = computed(() => {
  if (typeof window !== 'undefined' && window.matchMedia('(min-width: 900px)').matches) {
    return USER_PHONE_WIDTH + DEBUG_TRACE_WIDTH + PHONE_GAP
  }
  return Math.max(USER_PHONE_WIDTH, DEBUG_TRACE_WIDTH)
})

function defaultChatMessages() {
  return [
    {
      id: 'welcome',
      role: 'assistant',
      text: '您好，我是 FastAction 助手。请输入一句自然语言，我会根据已注册能力给出回复。'
    }
  ]
}

function resolveTestSessionId() {
  const generated = createTestSessionId()
  if (typeof window === 'undefined' || !window.localStorage) return generated
  const existing = window.localStorage.getItem(FASTACTION_TEST_SESSION_KEY)
  if (existing) return existing
  window.localStorage.setItem(FASTACTION_TEST_SESSION_KEY, generated)
  return generated
}

function resolvePreviewSplitRatio() {
  if (typeof window === 'undefined' || !window.localStorage) return 0.62
  const saved = Number(window.localStorage.getItem(FASTACTION_TEST_SPLIT_KEY))
  return Number.isFinite(saved) ? clamp(saved, 0.42, 0.78) : 0.62
}

function createTestSessionId() {
  const randomId = globalThis.crypto?.randomUUID?.() || `${Date.now()}_${Math.random().toString(16).slice(2)}`
  return `fastaction_test_${randomId}`
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

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

function localizedResultText(value) {
  if (!value) return ''
  if (typeof value === 'string') return value
  return value.zh || value['zh-CN'] || value.en || Object.values(value).find(Boolean) || ''
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

function parseJsonField(value, label) {
  try {
    return JSON.parse(value || '{}')
  } catch (error) {
    throw new Error(`${label} 不是合法 JSON：${error.message}`)
  }
}

function actionLabel(action) {
  return {
    invoke_api: '调用 API',
    answer: '直接回答',
    clarify: '需要补充信息',
    confirm: '需要确认',
    reject: '拒绝'
  }[action] || action || '未知'
}

function summarizePlan(result) {
  if (!result) return ''
  const reply = localizedResultText(result.reply)
  if (result.action === 'reject' && !result.api) {
    return reply && reply !== '当前没有可执行的已注册能力。'
      ? reply
      : '我暂时没有找到可以处理这个问题的已注册能力。可以换个问法，或先在 API 注册页补充对应能力。'
  }
  if (reply) return reply

  const apiName = result.api?.name?.zh || result.api?.id || '未命中 API'
  const action = actionLabel(result.action)
  const confidence = result.confidence != null ? `，置信度 ${Number(result.confidence).toFixed(2)}` : ''
  if (result.action === 'invoke_api') {
    return `已规划为${action}：${apiName}${confidence}。参数已解析，真实业务执行仍由 Host App 使用用户 token 完成。`
  }
  const message = localizedResultText(result.message)
  if (result.action === 'clarify') {
    return `当前需要补充信息：${message || apiName}${confidence}。`
  }
  if (result.action === 'confirm') {
    return confirmUserDescription(result)
  }
  if (message) return message
  return `规划结果：${action}，${apiName}${confidence}。`
}

function resultApiLabel(result) {
  if (!result?.api) return '-'
  return localizedResultText(result.api.name) || result.api.id || '-'
}

function resultConfidence(result) {
  if (result?.confidence == null) return '-'
  return Number(result.confidence).toFixed(2)
}

function resultCandidateCount(result) {
  return Array.isArray(result?.candidates) ? result.candidates.length : 0
}

function resultProviderId(result) {
  return result?.provider?.id || '-'
}

function resultProviderKind(result) {
  return result?.provider?.provider || '-'
}

function resultConfiguredModel(result) {
  return result?.provider?.model || '-'
}

function resultRuntimeModel(result) {
  return result?.provider?.runtime_model || result?.provider?.model || '-'
}

function isConfirmResult(result) {
  return result?.action === 'confirm'
}

function isClarifyResult(result) {
  return result?.action === 'clarify' && Boolean(result?.clarify)
}

function clarifyMissingDetails(result) {
  const details = Array.isArray(result?.clarify?.missing_param_details)
    ? result.clarify.missing_param_details
    : []
  const names = Array.isArray(result?.clarify?.missing_params) ? result.clarify.missing_params : []
  const normalized = details.map(item => normalizeMissingParamDetail(item)).filter(item => item.name)
  const known = new Set(normalized.map(item => item.name))
  for (const name of names) {
    if (!known.has(name)) normalized.push(normalizeMissingParamDetail({ name }))
  }
  return normalized
}

function normalizeMissingParamDetail(item = {}) {
  if (typeof item === 'string') return { name: item, label: item, type: '', source: [] }
  const name = String(item.name || '').trim()
  return {
    name,
    label: item.label || name,
    type: item.type || '',
    description: item.description || '',
    source: Array.isArray(item.source) ? item.source : [],
    option_set: item.option_set || '',
    resolve_entity: item.resolve_entity || '',
    ui: item.ui && typeof item.ui === 'object' ? item.ui : {},
    required: item.required !== false
  }
}

function missingParamLabel(item) {
  return localizedResultText(item.label) || item.name
}

function missingParamDescription(item) {
  return localizedResultText(item.description)
}

function missingParamMeta(item) {
  return [
    item.type,
    item.option_set ? `字典 ${item.option_set}` : '',
    item.resolve_entity ? `实体 ${item.resolve_entity}` : ''
  ].filter(Boolean).join(' · ') || 'required'
}

function missingParamHint(item) {
  const hint = localizedResultText(item.ui?.hint)
  if (hint) return hint
  if (item.option_set) return `从字典 ${item.option_set} 选择名称或 code。`
  if (item.resolve_entity) return `需要从 ${item.resolve_entity} 候选列表中校准真实 ID。`
  const contextSources = item.source.filter(source => source.startsWith('context.'))
  if (contextSources.length) return `可由上下文 ${contextSources.join(' / ')} 提供，或在 Params JSON 中填写。`
  if (item.source.includes('clarify')) return '需要用户补充该值。'
  return '在 Params JSON 中填写该字段后重试。'
}

function clarifyUserDescription(result) {
  const details = clarifyMissingDetails(result)
  const apiId = pendingApiLabel(result)
  return `已识别到 ${apiId}，但还缺 ${details.length || 1} 个必填参数。请补充这些信息后再次发送。`
}

function fillMissingParamsTemplate(result) {
  let params = {}
  try {
    params = parseJsonField(paramsText.value, '参数 JSON')
  } catch {
    params = {}
  }
  for (const detail of clarifyMissingDetails(result)) {
    if (detail.name && !(detail.name in params)) params[detail.name] = ''
  }
  paramsText.value = formatJson(params)
  toast.success('已生成 Params 模板', '补充字段值后重新发送即可')
}

function pendingApiLabel(result) {
  return result?.pending_instruction?.api_id || result?.api?.id || '-'
}

function pendingParams(result) {
  return result?.pending_instruction?.params || result?.params || {}
}

function pendingRiskLabel(result) {
  return result?.risk || result?.pending_instruction?.risk || result?.api?.policy?.risk_level || 'write'
}

function formatPendingValue(value) {
  if (value == null || value === '') return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function traceParamSummary(result) {
  const params = pendingParams(result)
  return Object.entries(params)
    .filter(([key]) => !['file'].includes(key))
    .map(([key, value]) => `${key}: ${formatPendingValue(value)}`)
}

function confirmUserTitle(result) {
  const apiName = resultApiLabel(result)
  return apiName && apiName !== '-' ? `确认${apiName}` : '操作待确认'
}

function confirmUserDescription(result) {
  const apiId = pendingApiLabel(result)
  const risk = pendingRiskLabel(result)
  const executorCount = activeHostExecutorDefinitions.value.length
  return `这一步会执行已注册能力 ${apiId}，风险级别为 ${risk}。当前已注册 ${executorCount} 个 Host Executor 定义；开源测试台不会直接调用你的业务系统，只会记录一次模拟 ExecutionResult。真实执行由 Host App 实现并回写结果。`
}

function confirmUserDetails(result) {
  const params = pendingParams(result)
  return Object.entries(params)
    .filter(([key]) => !['file'].includes(key))
    .slice(0, 3)
    .map(([key, value]) => ({ label: key, value: formatPendingValue(value) }))
}

function cancelPendingAction() {
  appendMessage('assistant', '已取消这个待确认操作，未执行任何业务 API。')
}

function acknowledgePendingAction(result) {
  appendMessage(
    'assistant',
    `测试台已收到确认：${pendingApiLabel(result)}。这里不会直接调用业务 API，真实执行应由 Host App 使用用户 token 执行 pending_instruction 后回写 Execution Result。`
  )
}

function formatFileSize(size) {
  const bytes = Number(size || 0)
  if (!bytes) return '0 KB'
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function appendMessage(role, text, result = null, attachments = []) {
  chatMessages.value.push({
    id: `${role}_${Date.now()}_${Math.random().toString(16).slice(2)}`,
    role,
    text,
    result,
    attachments
  })
}

function scrollElementToBottom(element) {
  if (!element) return
  element.scrollTop = element.scrollHeight
}

function scrollPreviewContainersToBottom() {
  nextTick(() => {
    scrollElementToBottom(userPreviewScrollRef.value)
    scrollElementToBottom(debugTraceScrollRef.value)
  })
}

function syncPreviewScroll(source) {
  if (previewScrollSyncing) return
  const sourceElement = source === 'user' ? userPreviewScrollRef.value : debugTraceScrollRef.value
  const targetElement = source === 'user' ? debugTraceScrollRef.value : userPreviewScrollRef.value
  if (!sourceElement || !targetElement) return

  const sourceScrollable = sourceElement.scrollHeight - sourceElement.clientHeight
  const targetScrollable = targetElement.scrollHeight - targetElement.clientHeight
  const ratio = sourceScrollable > 0 ? sourceElement.scrollTop / sourceScrollable : 1
  previewScrollSyncing = true
  targetElement.scrollTop = targetScrollable > 0 ? ratio * targetScrollable : 0
  window.requestAnimationFrame(() => {
    previewScrollSyncing = false
  })
}

function normalizePersistedMessage(row) {
  return {
    id: row.id || `${row.role || 'message'}_${Date.now()}_${Math.random().toString(16).slice(2)}`,
    role: row.role || 'assistant',
    text: row.content || '',
    result: row.result || null,
    attachments: Array.isArray(row.attachments) ? row.attachments.map(normalizePersistedAttachment) : []
  }
}

function normalizePersistedAttachment(item) {
  const kind = item.kind || attachmentFileKind(item) || 'file'
  return {
    id: item.id || item.name || `attachment_${Math.random().toString(16).slice(2)}`,
    name: item.name || item.file_name || 'attachment',
    type: item.type || item.mime_type || 'application/octet-stream',
    size: item.size || item.size_bytes || 0,
    kind,
    persisted: true
  }
}

async function loadPersistedTestMessages() {
  try {
    const rows = await getFastActionTestMessages({
      session_id: testSessionId.value,
      limit: 100
    })
    const restored = Array.isArray(rows) ? rows.map(normalizePersistedMessage).filter(item => item.text || item.attachments.length) : []
    if (!restored.length) return
    revokeAttachments(chatMessages.value.flatMap(message => message.attachments || []))
    chatMessages.value = [...defaultChatMessages(), ...restored]
    const lastResult = [...restored].reverse().find(item => item.result)?.result
    if (lastResult) testResult.value = lastResult
  } catch (error) {
    loadError.value = error.userMessage || error.message || 'FastAction 测试会话历史加载失败'
  }
}

async function clearChat() {
  revokeAttachments(chatMessages.value.flatMap(message => message.attachments || []))
  revokeAttachments(selectedAttachments.value)
  chatMessages.value = defaultChatMessages()
  selectedAttachments.value = []
  composerNotice.value = ''
  testResult.value = null
  try {
    await clearFastActionTestMessages(testSessionId.value)
  } catch (error) {
    toast.warning('测试会话已本地清空', error.userMessage || error.message || '服务端历史清理失败')
  }
}

function useQuickQuestion(text) {
  testInput.value = text
}

function chooseAttachment() {
  if (testSending.value) return
  fileInputRef.value?.click()
}

function attachmentFileKind(file) {
  const mimeType = String(file?.type || file?.mime_type || file?.content_type || '').toLowerCase()
  const name = String(file?.name || '').toLowerCase()
  if (mimeType.startsWith('image/') || /\.(avif|bmp|gif|jpe?g|png|webp|heic|heif|tiff?)$/i.test(name)) return 'image'
  if (mimeType === 'application/pdf' || /\.pdf$/i.test(name)) return 'pdf'
  if (mimeType.startsWith('video/') || /\.(mp4|mov|m4v|avi|mkv|webm|flv|wmv)$/i.test(name)) return 'video'
  if (mimeType.startsWith('audio/') || /\.(mp3|wav|m4a|aac|ogg|oga|flac|amr|webm)$/i.test(name)) return 'audio'
  if (/\.(dwg|dxf)$/i.test(name)) return 'dwg'
  return ''
}

function attachmentKindLabel(kind) {
  return ATTACHMENT_KIND_LABELS[kind] || '文件'
}

function handleAttachmentChange(event) {
  const picked = Array.from(event.target.files || [])
  event.target.value = ''
  if (!picked.length) return

  const remaining = Math.max(0, MAX_ATTACHMENTS - selectedAttachments.value.length)
  const accepted = []
  const rejected = []

  for (const file of picked) {
    const kind = attachmentFileKind(file)
    if (!kind) {
      rejected.push(`${file.name || '未知文件'} 格式不支持，请选择图片、PDF、视频、音频或 DWG/DXF 文件。`)
      continue
    }
    if (file.size > MAX_ATTACHMENT_SIZE) {
      rejected.push(`${file.name || '文件'} 超过 ${formatFileSize(MAX_ATTACHMENT_SIZE)}`)
      continue
    }
    if (accepted.length >= remaining) {
      rejected.push(`最多附加 ${MAX_ATTACHMENTS} 个文件`)
      continue
    }
    accepted.push(normalizeAttachment(file, accepted.length, kind))
  }

  selectedAttachments.value = [...selectedAttachments.value, ...accepted]
  composerNotice.value = rejected[0] || (accepted.length ? '文件已作为本次测试附件加入上下文。' : '')
}

function normalizeAttachment(file, index = 0, kind = attachmentFileKind(file)) {
  const previewUrl = kind === 'image' ? URL.createObjectURL(file) : ''
  return {
    id: `${file.name || 'file'}-${file.lastModified || Date.now()}-${Date.now()}-${index}`,
    name: file.name || `file-${index + 1}`,
    type: file.type || 'application/octet-stream',
    size: file.size || 0,
    kind: kind || 'file',
    previewUrl
  }
}

function removeAttachment(index) {
  const item = selectedAttachments.value[index]
  revokeAttachments(item ? [item] : [])
  selectedAttachments.value.splice(index, 1)
  if (!selectedAttachments.value.length && composerNotice.value.includes('文件已')) {
    composerNotice.value = ''
  }
}

function revokeAttachments(items = []) {
  items.forEach((item) => {
    if (item?.previewUrl) URL.revokeObjectURL(item.previewUrl)
  })
}

function buildAttachmentContext(attachments = []) {
  return attachments.map((item) => ({
    id: item.id,
    kind: item.kind,
    name: item.name,
    mime_type: item.type,
    size_bytes: item.size,
    local_preview: true,
    source: 'fastaction_test_bench'
  }))
}

function mergeInputModalities(value, modality) {
  const base = Array.isArray(value) ? value : ['text']
  return Array.from(new Set([...base, modality]))
}

function hasVoiceRecordingSupport() {
  return typeof window !== 'undefined'
    && typeof navigator !== 'undefined'
    && Boolean(navigator.mediaDevices?.getUserMedia)
    && 'MediaRecorder' in window
}

async function toggleVoiceRecording() {
  if (!voiceSupported.value || testSending.value || voiceBusy.value) return
  if (isRecording.value) {
    stopVoiceRecording()
    return
  }
  await startVoiceRecording()
}

async function startVoiceRecording() {
  try {
    composerNotice.value = ''
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new window.MediaRecorder(mediaStream)
    audioChunks = []
    mediaRecorder.ondataavailable = (event) => {
      if (event.data?.size) audioChunks.push(event.data)
    }
    mediaRecorder.onstop = handleVoiceRecordingStopped
    mediaRecorder.start()
    isRecording.value = true
    recordingTimer = window.setTimeout(stopVoiceRecording, 60000)
  } catch (error) {
    composerNotice.value = error.message || '无法启动录音，请检查麦克风权限。'
  }
}

function stopVoiceRecording() {
  if (recordingTimer) {
    window.clearTimeout(recordingTimer)
    recordingTimer = null
  }
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  } else {
    stopVoiceTracks()
    isRecording.value = false
  }
}

async function handleVoiceRecordingStopped() {
  const chunks = audioChunks.slice()
  const mimeType = mediaRecorder?.mimeType || 'audio/webm'
  audioChunks = []
  stopVoiceTracks()
  isRecording.value = false
  if (!chunks.length) return

  try {
    voiceBusy.value = true
    composerNotice.value = '正在识别语音...'
    const blob = new Blob(chunks, { type: mimeType })
    const file = new File([blob], `fastaction-test-${Date.now()}.webm`, { type: blob.type || 'audio/webm' })
    const result = await transcribeFastActionAudio(file)
    const text = String(result?.text || '').trim()
    if (!text) throw new Error('语音识别结果为空')
    testInput.value = testInput.value ? `${testInput.value} ${text}` : text
    composerNotice.value = '语音已转成文字，可以继续补充附件。'
  } catch (error) {
    composerNotice.value = error.userMessage || error.message || '语音识别失败，请改用文字输入。'
  } finally {
    voiceBusy.value = false
  }
}

function stopVoiceTracks() {
  mediaStream?.getTracks?.().forEach(track => track.stop())
  mediaStream = null
  mediaRecorder = null
}

function cleanupVoiceRecording() {
  if (recordingTimer) {
    window.clearTimeout(recordingTimer)
    recordingTimer = null
  }
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.onstop = null
    mediaRecorder.stop()
  }
  audioChunks = []
  isRecording.value = false
  stopVoiceTracks()
}

function makeProviderEditor(provider = null) {
  const source = provider || defaultProviderTemplate()
  return {
    originalId: source.id || '',
    id: source.id || '',
    type: source.type || 'llm',
    provider: source.provider || providerOptions.value[0] || 'openai_compatible',
    baseUrl: source.base_url || '',
    model: source.model || 'auto',
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

function defaultProviderTemplate() {
  return modelPoolProvider.value || providerPresets.value[0] || {
    id: '',
    type: 'llm',
    provider: providerOptions.value[0] || 'openai_compatible',
    base_url: '',
    model: '',
    capabilities: ['chat', 'json_schema'],
    routing: { tasks: ['planning'], priority: 10 },
    credentials: { mode: 'server_secret', secret_ref: '', api_key: null },
    default_headers: {},
    extra: {},
    is_active: true
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

function selectProvider(provider) {
  selectedProviderId.value = provider.id
  providerEditor.value = makeProviderEditor(provider)
  providerTestResult.value = null
}

function startCreateProvider() {
  selectedProviderId.value = ''
  providerEditor.value = makeProviderEditor({
    id: '',
    provider: 'openai_compatible',
    type: 'llm',
    base_url: '',
    model: '',
    capabilities: ['chat', 'json_schema'],
    routing: { tasks: ['planning'], priority: 10 },
    credentials: { mode: 'server_secret', secret_ref: '' },
    default_headers: {},
    extra: {},
    is_active: true
  })
  providerTestResult.value = null
}

function editModelPoolProvider() {
  selectProvider(modelPoolProvider.value || defaultProviderTemplate())
}

async function saveProvider() {
  try {
    providerSaving.value = true
    const payload = buildProviderPayload()
    const saved = await saveFastActionProviderConfig(payload, Boolean(providerEditor.value?.originalId))
    const normalized = saved?.id ? saved : payload
    const index = providerConfigs.value.findIndex(item => item.id === normalized.id)
    if (index >= 0) providerConfigs.value.splice(index, 1, normalized)
    else providerConfigs.value.unshift(normalized)
    selectProvider(normalized)
    toast.success('Provider 已保存', normalized.id)
  } catch (error) {
    toast.error('保存 Provider 失败', error.userMessage || error.message || 'Provider 配置保存失败')
  } finally {
    providerSaving.value = false
  }
}

async function deleteProvider() {
  if (!selectedProvider.value || !window.confirm(`确认删除 ${selectedProvider.value.id}？`)) return
  try {
    providerDeleting.value = true
    await deleteFastActionProviderConfig(selectedProvider.value.id)
    providerConfigs.value = providerConfigs.value.filter(item => item.id !== selectedProvider.value.id)
    selectedProviderId.value = ''
    providerEditor.value = null
    toast.success('Provider 已删除', '配置已移除')
  } catch (error) {
    toast.error('删除 Provider 失败', error.userMessage || error.message || 'Provider 删除失败')
  } finally {
    providerDeleting.value = false
  }
}

async function previewProvider() {
  const id = providerEditor.value?.id?.trim()
  if (!id) {
    toast.warning('先保存 Provider', 'Provider ID 不能为空')
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

function selectIdentity(identity) {
  selectedIdentityId.value = identity.id
  identityEditor.value = makeIdentityEditor(identity)
}

function startCreateIdentity() {
  selectedIdentityId.value = ''
  identityEditor.value = makeIdentityEditor()
}

async function saveIdentity() {
  try {
    identitySaving.value = true
    const payload = buildIdentityPayload()
    const saved = await saveFastActionIdentityDefinition(payload, Boolean(identityEditor.value?.originalId))
    const index = identityDefinitions.value.findIndex(item => item.id === saved.id)
    if (index >= 0) identityDefinitions.value.splice(index, 1, saved)
    else identityDefinitions.value.unshift(saved)
    selectIdentity(saved)
    toast.success('身份定义已保存', saved.id)
  } catch (error) {
    toast.error('保存身份失败', error.userMessage || error.message || '身份定义保存失败')
  } finally {
    identitySaving.value = false
  }
}

async function deleteIdentity() {
  if (!selectedIdentity.value || !window.confirm(`确认删除 ${selectedIdentity.value.id}？`)) return
  try {
    identityDeleting.value = true
    await deleteFastActionIdentityDefinition(selectedIdentity.value.id)
    identityDefinitions.value = identityDefinitions.value.filter(item => item.id !== selectedIdentity.value.id)
    selectedIdentityId.value = ''
    identityEditor.value = null
    toast.success('身份定义已删除', '配置已移除')
  } catch (error) {
    toast.error('删除身份失败', error.userMessage || error.message || '身份定义删除失败')
  } finally {
    identityDeleting.value = false
  }
}

async function sendTestMessage() {
  const attachmentsForSend = selectedAttachments.value.slice()
  const rawText = testInput.value.trim()
  const text = rawText || (attachmentsForSend.length ? '请分析我上传的附件' : '')
  if (!text && !attachmentsForSend.length) {
    toast.warning('请输入测试语句或上传附件', '例如：我有哪些待办任务')
    return
  }
  try {
    const parsedContext = parseJsonField(contextText.value, '上下文 JSON')
    const attachmentContext = buildAttachmentContext(attachmentsForSend)
    const baseContext = {
      ...parsedContext,
      test_session_id: testSessionId.value
    }
    const context = attachmentContext.length
      ? {
          ...baseContext,
          attachments: attachmentContext,
          input_modalities: mergeInputModalities(baseContext.input_modalities, 'image')
        }
      : baseContext
    const params = parseJsonField(paramsText.value, '参数 JSON')
    appendMessage('user', text, null, attachmentsForSend)
    testInput.value = ''
    selectedAttachments.value = []
    composerNotice.value = ''
    testSending.value = true
    const result = await planFastActionChat({
      text,
      context,
      params,
      host_app: context.host_app || 'example',
      locale: context.locale || 'zh-CN',
      planner_mode: plannerMode.value,
      provider_id: plannerMode.value === 'deterministic' ? null : (plannerProviderId.value || null),
      no_api_hit_strategy: noApiHitStrategy.value,
      identity_id: plannerIdentityId.value || null
    })
    testResult.value = result
    appendMessage('assistant', summarizePlan(result), result)
  } catch (error) {
    const message = error.userMessage || error.message || 'FastAction 测试失败'
    appendMessage('assistant', `测试失败：${message}`)
    toast.error('测试失败', message)
  } finally {
    testSending.value = false
  }
}

async function loadSettings() {
  try {
    loading.value = true
    loadError.value = ''
    const results = await Promise.allSettled([
      getFastActionHealth(),
      getFastActionProviderConfigs(),
      getFastActionProviderPresets(),
      getFastActionHostExecutors(),
      getFastActionIdentityDefinitions(),
      getFastActionKnowledgeDefinitions()
    ])
    health.value = pickResult(results[0], null)
    providerConfigs.value = ensureArray(pickResult(results[1], []))
    providerPresets.value = ensureArray(pickResult(results[2], []))
    hostExecutorDefinitions.value = ensureArray(pickResult(results[3], []))
    identityDefinitions.value = ensureArray(pickResult(results[4], []))
    knowledgeDefinitions.value = ensureArray(pickResult(results[5], []))
    modelPoolStatus.value = await loadModelPoolStatus(pickModelPoolProvider(providerConfigs.value))
    const rejected = results.find(item => item.status === 'rejected')
    if (rejected) {
      loadError.value = rejected.reason?.userMessage || rejected.reason?.message || 'FastAction 基础配置加载不完整'
    }
    if (providerConfigs.value[0]) selectProvider(providerConfigs.value[0])
    if (identityDefinitions.value[0]) selectIdentity(identityDefinitions.value[0])
    if (!plannerProviderId.value) {
      plannerProviderId.value = pickRecommendedProvider(providerConfigs.value)?.id || ''
    }
    if (plannerIdentityId.value && !identityDefinitions.value.some(item => item.id === plannerIdentityId.value)) {
      plannerIdentityId.value = ''
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

function providerCapabilities(provider) {
  return new Set((provider?.capabilities || []).map(item => String(item)))
}

function providerSupportsCapability(provider, capability) {
  return providerCapabilities(provider).has(capability)
}

function pickModelPoolProvider(providers) {
  return ensureArray(providers).find(provider => provider.is_active !== false && (
    providerSupportsCapability(provider, 'model_pool') ||
    providerSupportsCapability(provider, 'balanced_routing')
  )) || null
}

function pickRecommendedProvider(providers) {
  const active = ensureArray(providers).filter(provider => provider.is_active !== false)
  const preferredCapabilities = defaultFastActionTestScenario.preferredProviderCapabilities || []
  return active.find(provider => preferredCapabilities.every(capability => providerSupportsCapability(provider, capability))) ||
    pickModelPoolProvider(active) ||
    active.find(provider => providerSupportsCapability(provider, 'chat')) ||
    active[0] ||
    null
}

async function loadModelPoolStatus(provider) {
  if (!provider?.id) return null
  try {
    return await getFastActionProviderModelPoolStatus(provider.id)
  } catch {
    return null
  }
}

function formatNumber(value) {
  return new Intl.NumberFormat('zh-CN').format(Number(value || 0))
}

function modelStatus(model) {
  if (model.supports_chat === false) return '非聊天'
  if (model.is_exhausted) return '已耗尽'
  if (!model.is_enabled) return '停用'
  if (model.last_status === 'success') return '可用'
  return model.last_status || '待测'
}

function updatePhoneScale() {
  if (typeof window === 'undefined') return
  const containerWidth = phoneViewportRef.value?.clientWidth || previewStageRef.value?.clientWidth || window.innerWidth
  const widthForPhones = Math.max(1, containerWidth)
  const widthScale = widthForPhones / phoneTargetWidth.value
  const nextScale = Math.min(MAX_PHONE_SCALE, widthScale)
  phoneScale.value = Number(Math.max(MIN_PHONE_SCALE, nextScale).toFixed(3))
}

function canUseResizablePreview() {
  return typeof window !== 'undefined' && window.matchMedia('(min-width: 1536px)').matches
}

function updatePreviewLayout() {
  if (typeof window === 'undefined') return
  const stageWidth = previewStageRef.value?.clientWidth || window.innerWidth
  if (canUseResizablePreview()) {
    const maxPhysicalWidth = Math.round(phoneTargetWidth.value * MAX_PHONE_SCALE)
    const minPhysicalWidth = Math.round(phoneTargetWidth.value * MIN_PHONE_SCALE)
    const maxLeftWidth = Math.min(maxPhysicalWidth, Math.max(minPhysicalWidth, stageWidth - RUN_CONTROL_MIN_WIDTH - PREVIEW_RESIZE_HANDLE_WIDTH))
    const minLeftWidth = Math.min(maxLeftWidth, Math.max(minPhysicalWidth, PREVIEW_LEFT_MIN_WIDTH))
    const nextLeftWidth = clamp(
      Math.round((stageWidth - PREVIEW_RESIZE_HANDLE_WIDTH) * previewSplitRatio.value),
      minLeftWidth,
      maxLeftWidth
    )
    previewLeftWidth.value = nextLeftWidth
  } else {
    previewLeftWidth.value = null
  }
  updatePhoneScale()
}

function startPreviewResize(event) {
  if (!canUseResizablePreview()) return
  event.preventDefault()
  isPreviewResizing.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  window.addEventListener('pointermove', handlePreviewResize)
  window.addEventListener('pointerup', stopPreviewResize)
  handlePreviewResize(event)
}

function handlePreviewResize(event) {
  const rect = previewStageRef.value?.getBoundingClientRect()
  if (!rect) return
  const maxPhysicalWidth = Math.round(phoneTargetWidth.value * MAX_PHONE_SCALE)
  const minPhysicalWidth = Math.round(phoneTargetWidth.value * MIN_PHONE_SCALE)
  const maxLeftWidth = Math.min(maxPhysicalWidth, Math.max(minPhysicalWidth, rect.width - RUN_CONTROL_MIN_WIDTH - PREVIEW_RESIZE_HANDLE_WIDTH))
  const minLeftWidth = Math.min(maxLeftWidth, Math.max(minPhysicalWidth, PREVIEW_LEFT_MIN_WIDTH))
  const nextLeftWidth = clamp(Math.round(event.clientX - rect.left), minLeftWidth, maxLeftWidth)
  previewLeftWidth.value = nextLeftWidth
  previewSplitRatio.value = Number((nextLeftWidth / Math.max(1, rect.width - PREVIEW_RESIZE_HANDLE_WIDTH)).toFixed(4))
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.setItem(FASTACTION_TEST_SPLIT_KEY, String(previewSplitRatio.value))
  }
  updatePhoneScale()
}

function stopPreviewResize() {
  if (!isPreviewResizing.value) return
  isPreviewResizing.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  window.removeEventListener('pointermove', handlePreviewResize)
  window.removeEventListener('pointerup', stopPreviewResize)
}

function setupPhoneScaleObserver() {
  updatePreviewLayout()
  window.addEventListener('resize', updatePreviewLayout)
  if (typeof ResizeObserver !== 'undefined' && previewStageRef.value) {
    previewResizeObserver = new ResizeObserver(updatePreviewLayout)
    previewResizeObserver.observe(previewStageRef.value)
  }
}

watch(
  () => [chatMessages.value.length, testSending.value],
  () => scrollPreviewContainersToBottom(),
  { flush: 'post' }
)

onMounted(async () => {
  voiceSupported.value = hasVoiceRecordingSupport()
  await loadSettings()
  await loadPersistedTestMessages()
  await nextTick()
  setupPhoneScaleObserver()
  scrollPreviewContainersToBottom()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updatePreviewLayout)
  stopPreviewResize()
  previewResizeObserver?.disconnect()
  previewResizeObserver = null
  cleanupVoiceRecording()
  revokeAttachments(selectedAttachments.value)
  revokeAttachments(chatMessages.value.flatMap(message => message.attachments || []))
})
</script>

<template>
  <AdminLayout>
    <div class="space-y-3">
      <section class="rounded-xl border border-neutral-200 bg-white/90 px-4 py-3 shadow-sm">
        <div class="flex flex-col gap-2 xl:flex-row xl:items-center xl:justify-between">
          <div class="flex min-w-0 flex-wrap items-center gap-2">
            <h2 class="text-xl font-semibold text-neutral-950">测试台</h2>
            <span class="h-4 w-px bg-neutral-200"></span>
            <span class="text-[11px] font-semibold uppercase tracking-wider text-primary">FastAction Test Bench</span>
            <span class="h-4 w-px bg-neutral-200"></span>
            <span class="text-xs text-neutral-500">用户预览、调试预览和运行配置</span>
          </div>
          <div class="-mx-0.5 flex min-w-0 gap-1.5 overflow-x-auto px-0.5 pb-1 xl:flex-1 xl:justify-end xl:pb-0">
            <div class="min-w-[116px] flex-1 rounded-lg border border-neutral-200 bg-neutral-50 px-2.5 py-2">
              <p class="text-xs text-neutral-500">引擎</p>
              <p class="text-sm font-semibold" :class="healthState === 'healthy' ? 'text-success-700' : 'text-warning-700'">{{ healthState }}</p>
            </div>
            <div class="min-w-[116px] flex-1 rounded-lg border border-warning/20 bg-warning-50 px-2.5 py-2">
              <p class="text-xs text-warning-700">Provider</p>
              <p class="text-sm font-semibold text-warning-700">{{ providerConfigs.length }}</p>
            </div>
            <div class="min-w-[116px] flex-1 rounded-lg border border-primary/20 bg-primary/5 px-2.5 py-2">
              <p class="text-xs text-primary">身份</p>
              <p class="text-sm font-semibold text-primary">{{ identityDefinitions.length }}</p>
            </div>
            <div class="min-w-[116px] flex-1 rounded-lg border border-success/20 bg-success-50 px-2.5 py-2">
              <p class="text-xs text-success-700">知识库</p>
              <p class="text-sm font-semibold text-success-700">{{ knowledgeDefinitions.length }}</p>
            </div>
            <div class="min-w-[116px] flex-1 rounded-lg border border-info-200 bg-info-50 px-2.5 py-2">
              <p class="text-xs text-info-700">模型池可用</p>
              <p class="text-sm font-semibold text-info-700">{{ modelPoolUsableModels.length }}</p>
            </div>
          </div>
          <div class="flex shrink-0 gap-1.5">
            <router-link to="/fastaction" class="rounded-lg border border-neutral-200 px-2.5 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-50">
              返回 API 注册
            </router-link>
            <button class="rounded-lg border border-neutral-200 px-2.5 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-50" @click="loadSettings">
              刷新
            </button>
          </div>
        </div>
        <div v-if="loadError" class="mt-2 rounded-lg border border-warning/20 bg-warning-50 px-3 py-1.5 text-xs text-warning-800">
          {{ loadError }}
        </div>
      </section>

      <div v-if="loading" class="rounded-lg border border-neutral-200 bg-white p-8 text-center text-neutral-500 shadow-sm">
        <span class="mx-auto mb-2 block h-6 w-6 animate-spin rounded-full border-2 border-neutral-200 border-t-neutral-700"></span>
        <p class="text-sm">加载 FastAction 基础配置中...</p>
      </div>

      <template v-else>
        <section
          ref="previewStageRef"
          class="grid min-w-0 grid-cols-1 items-start gap-3 overflow-hidden 2xl:grid-cols-[minmax(0,var(--fastaction-preview-left-width))_14px_minmax(340px,1fr)]"
          :style="previewStageStyle"
        >
          <div ref="phoneViewportRef" class="grid min-w-0 grid-cols-1 items-start gap-3 min-[900px]:grid-cols-[min-content_min-content]">
          <div class="relative mx-auto shrink-0 min-[900px]:mx-0" :style="userPhoneShellStyle">
          <div class="absolute left-0 top-0 overflow-hidden rounded-[30px] border border-neutral-800 bg-neutral-950 p-1.5 shadow-sm" :style="userPhoneFrameStyle">
            <div class="flex h-[782px] overflow-hidden rounded-[25px] bg-white">
              <div class="flex min-h-0 flex-1 flex-col">
            <div class="flex items-center justify-between gap-3 border-b border-neutral-100 bg-white/80 px-4 py-3">
              <div class="min-w-0 flex-1">
                <h3 class="text-base font-semibold text-neutral-950">用户预览</h3>
                <p class="mt-0.5 break-words text-sm leading-5 text-neutral-500">{{ plannerIdentityId || '默认身份' }} · Pro Max 360×782</p>
              </div>
              <button class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-neutral-200 text-sm text-neutral-600 hover:bg-neutral-50" type="button" @click="clearChat">
                <span class="text-base leading-none">↻</span>
              </button>
            </div>

            <div ref="userPreviewScrollRef" class="min-h-0 flex-1 overflow-y-auto bg-neutral-50/80 px-4 py-4" @scroll="syncPreviewScroll('user')">
              <div class="space-y-3">
                <article
                  v-for="message in chatMessages"
                  :key="`preview_${message.id}`"
                  class="flex"
                  :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
                >
                  <div
                    class="min-w-0 max-w-[84%] rounded-2xl px-3.5 py-2.5 text-sm leading-6 shadow-sm"
                    :class="message.role === 'user' ? 'rounded-br-md bg-neutral-950 text-white' : 'rounded-bl-md bg-white text-neutral-800'"
                  >
                    <p v-if="!(message.role === 'assistant' && (isConfirmResult(message.result) || isClarifyResult(message.result)))" class="whitespace-pre-wrap break-words">{{ message.text }}</p>
                    <div
                      v-if="message.role === 'assistant' && isConfirmResult(message.result)"
                      class="mt-3 min-w-0 overflow-hidden rounded-2xl border border-warning/20 bg-warning-50 p-3 text-left text-neutral-800"
                    >
                      <div class="flex flex-wrap items-center gap-2">
                        <span class="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-warning-700">待确认</span>
                        <span class="min-w-0 break-words text-sm font-semibold text-neutral-900">{{ confirmUserTitle(message.result) }}</span>
                      </div>
                      <p class="mt-2 break-words text-sm leading-6 text-neutral-700">{{ confirmUserDescription(message.result) }}</p>
                      <div v-if="confirmUserDetails(message.result).length" class="mt-3 space-y-1.5 rounded-xl bg-white/70 p-2.5">
                        <div
                          v-for="item in confirmUserDetails(message.result)"
                          :key="item.label"
                          class="grid grid-cols-[3.5rem_minmax(0,1fr)] gap-2 text-xs leading-5"
                        >
                          <span class="text-neutral-500">{{ item.label }}</span>
                          <span class="min-w-0 break-all font-medium text-neutral-800">{{ item.value }}</span>
                        </div>
                      </div>
                      <div class="mt-3 grid grid-cols-2 gap-2">
                        <button
                          type="button"
                          class="rounded-full border border-neutral-200 bg-white px-2 py-1.5 text-xs font-medium text-neutral-700"
                          @click="cancelPendingAction"
                        >
                          取消
                        </button>
                        <button
                          type="button"
                          class="rounded-full bg-neutral-950 px-2 py-1.5 text-xs font-medium text-white"
                          @click="acknowledgePendingAction(message.result)"
                        >
                          确认执行
                        </button>
                      </div>
                    </div>
                    <div
                      v-if="message.role === 'assistant' && isClarifyResult(message.result)"
                      class="mt-3 min-w-0 overflow-hidden rounded-2xl border border-info-100 bg-info-50 p-3 text-left text-neutral-800"
                    >
                      <div class="flex flex-wrap items-center gap-2">
                        <span class="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-info-700">待补充</span>
                        <span class="min-w-0 break-words text-sm font-semibold text-neutral-900">缺少必要参数</span>
                      </div>
                      <p class="mt-2 break-words text-sm leading-6 text-neutral-700">{{ clarifyUserDescription(message.result) }}</p>
                      <div class="mt-3 space-y-2">
                        <div
                          v-for="item in clarifyMissingDetails(message.result)"
                          :key="item.name"
                          class="rounded-xl bg-white/80 p-2.5"
                        >
                          <div class="flex flex-wrap items-center gap-2">
                            <span class="font-semibold text-neutral-900">{{ missingParamLabel(item) }}</span>
                            <span class="font-mono text-xs text-neutral-500">{{ item.name }}</span>
                            <span class="rounded-full bg-neutral-100 px-2 py-0.5 text-[11px] text-neutral-600">{{ missingParamMeta(item) }}</span>
                          </div>
                          <p v-if="missingParamDescription(item)" class="mt-1 text-xs leading-5 text-neutral-600">{{ missingParamDescription(item) }}</p>
                          <p class="mt-1 text-xs leading-5 text-neutral-500">{{ missingParamHint(item) }}</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        class="mt-3 w-full rounded-full bg-neutral-950 px-3 py-1.5 text-xs font-medium text-white"
                        @click="fillMissingParamsTemplate(message.result)"
                      >
                        生成 Params 模板
                      </button>
                    </div>
                    <div v-if="message.attachments?.length" class="mt-3 grid grid-cols-2 gap-2">
                      <div
                        v-for="attachment in message.attachments"
                        :key="`preview_attachment_${message.id}_${attachment.id}`"
                        class="overflow-hidden rounded-xl border"
                        :class="message.role === 'user' ? 'border-white/20 bg-white/10' : 'border-neutral-100 bg-neutral-50'"
                      >
                        <img v-if="attachment.kind === 'image' && attachment.previewUrl" :src="attachment.previewUrl" :alt="attachment.name" class="h-20 w-full object-cover">
                        <div
                          v-else
                          class="flex h-20 w-full flex-col items-center justify-center gap-1"
                          :class="message.role === 'user' ? 'text-white/70' : 'text-neutral-400'"
                        >
                          <span class="text-[10px] font-semibold tracking-wide">{{ attachmentKindLabel(attachment.kind) }}</span>
                        </div>
                        <div
                          class="truncate px-2 py-1.5 text-[11px]"
                          :class="message.role === 'user' ? 'text-white/80' : 'text-neutral-500'"
                        >
                          {{ attachment.name }}
                        </div>
                      </div>
                    </div>
                  </div>
                </article>
                <article v-if="testSending" class="flex justify-start">
                  <div class="rounded-2xl rounded-bl-md bg-white px-4 py-3 text-sm text-neutral-500 shadow-sm">
                    <span class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-neutral-200 border-t-neutral-600 align-[-2px]"></span>思考中...
                  </div>
                </article>
              </div>
            </div>

            <div class="border-t border-neutral-100 bg-white px-3 py-3">
              <div class="mb-2.5 flex gap-1.5 overflow-x-auto pb-1">
                <button
                  v-for="question in quickQuestions"
                  :key="question"
                  class="shrink-0 rounded-full border border-neutral-200 bg-white px-2.5 py-1 text-xs text-neutral-600 hover:bg-neutral-50"
                  @click="useQuickQuestion(question)"
                >
                  {{ question }}
                </button>
              </div>
              <div v-if="selectedAttachments.length" class="mb-2.5 flex gap-1.5 overflow-x-auto pb-1">
                <div
                  v-for="(attachment, index) in selectedAttachments"
                  :key="attachment.id"
                  class="group relative h-12 w-12 shrink-0 overflow-hidden rounded-xl border border-neutral-200 bg-neutral-50"
                >
                  <img v-if="attachment.kind === 'image' && attachment.previewUrl" :src="attachment.previewUrl" :alt="attachment.name" class="h-full w-full object-cover">
                  <div v-else class="flex h-full w-full flex-col items-center justify-center gap-0.5 text-neutral-500">
                    <span class="max-w-[2.5rem] truncate text-[9px] font-medium">{{ attachmentKindLabel(attachment.kind) }}</span>
                  </div>
                  <button
                    type="button"
                    class="absolute right-0.5 top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-neutral-950/80 text-[8px] text-white opacity-90"
                    title="移除附件"
                    @click="removeAttachment(index)"
                  >
                    <span class="leading-none">×</span>
                  </button>
                </div>
              </div>
              <div v-if="composerNotice" class="mb-2 rounded-xl bg-neutral-100 px-3 py-2 text-xs text-neutral-600">
                {{ composerNotice }}
              </div>
              <input
                ref="fileInputRef"
                class="hidden"
                type="file"
                :accept="ATTACHMENT_ACCEPT"
                multiple
                @change="handleAttachmentChange"
              >
              <div class="flex items-center gap-1.5">
                <button
                  class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-neutral-200 bg-white text-sm text-neutral-700 shadow-sm hover:bg-neutral-50 disabled:opacity-50"
                  type="button"
                  title="上传附件"
                  :disabled="testSending"
                  @click="chooseAttachment"
                >
                  <span class="text-[10px] font-semibold leading-none">FILE</span>
                </button>
                <button
                  class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-neutral-200 bg-white text-sm text-neutral-700 shadow-sm hover:bg-neutral-50 disabled:opacity-50"
                  :class="isRecording ? 'border-danger-200 bg-danger-50 text-danger-700' : ''"
                  type="button"
                  :title="voiceSupported ? (isRecording ? '停止录音' : '语音输入') : '当前浏览器不支持录音'"
                  :disabled="testSending || voiceBusy || !voiceSupported"
                  @click="toggleVoiceRecording"
                >
                  <span v-if="voiceBusy" class="h-4 w-4 animate-spin rounded-full border-2 border-neutral-200 border-t-neutral-600"></span>
                  <span v-else-if="isRecording" class="h-3 w-3 rounded-sm bg-current"></span>
                  <span v-else class="text-[10px] font-semibold leading-none">MIC</span>
                </button>
                <input
                  v-model="testInput"
                  type="text"
                  class="h-9 min-w-0 flex-1 rounded-full border border-neutral-200 px-3 text-sm outline-none focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10"
                  placeholder="输入问题，也可以语音转文字或上传附件..."
                  @keydown.enter.exact.prevent="sendTestMessage"
                >
                <button
                  class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-neutral-950 text-sm text-white shadow-sm disabled:opacity-50"
                  type="button"
                  :disabled="testSending || (!testInput.trim() && !selectedAttachments.length)"
                  @click="sendTestMessage"
                >
                  <svg class="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M5 12h13"></path>
                    <path d="M13 6l6 6-6 6"></path>
                  </svg>
                </button>
              </div>
            </div>
            </div>
          </div>
          </div>
          </div>

          <div class="relative mx-auto shrink-0 min-[900px]:mx-0" :style="debugTraceShellStyle">
          <div class="absolute left-0 top-0 overflow-hidden rounded-[30px] border border-neutral-800 bg-neutral-950 p-1.5 shadow-sm" :style="debugTraceFrameStyle">
            <div class="flex h-[782px] overflow-hidden rounded-[25px] bg-white">
              <div class="flex min-h-0 flex-1 flex-col">
            <div class="flex items-start justify-between gap-3 border-b border-neutral-100 bg-white/80 px-5 py-4">
              <div class="min-w-0 flex-1">
                <h3 class="text-base font-semibold text-neutral-950">调试 Trace</h3>
                <p class="mt-0.5 break-words text-sm leading-5 text-neutral-500">{{ plannerMode }} · {{ testProviderLabel }} · Trace 520×782</p>
              </div>
              <span class="shrink-0 rounded-full bg-neutral-100 px-3 py-1 text-xs font-medium text-neutral-600">
                {{ testResult?.action || 'waiting' }}
              </span>
            </div>

            <div ref="debugTraceScrollRef" class="min-h-0 flex-1 overflow-y-auto bg-neutral-50/80 px-5 py-5" @scroll="syncPreviewScroll('debug')">
              <div class="space-y-4">
                <article
                  v-for="message in chatMessages"
                  :key="`debug_${message.id}`"
                  class="flex"
                  :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
                >
                  <div
                    class="min-w-0 max-w-[92%] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm"
                    :class="message.role === 'user' ? 'rounded-br-md bg-neutral-900 text-white' : 'rounded-bl-md bg-white text-neutral-800'"
                  >
                    <p class="whitespace-pre-wrap break-words">{{ message.text }}</p>
                    <div v-if="message.attachments?.length" class="mt-3 space-y-2">
                      <div
                        v-for="attachment in message.attachments"
                        :key="`debug_attachment_${message.id}_${attachment.id}`"
                        class="flex items-center gap-2 rounded-xl border px-2 py-2"
                        :class="message.role === 'user' ? 'border-white/20 bg-white/10 text-white/80' : 'border-neutral-100 bg-neutral-50 text-neutral-600'"
                      >
                        <img v-if="attachment.kind === 'image' && attachment.previewUrl" :src="attachment.previewUrl" :alt="attachment.name" class="h-10 w-10 shrink-0 rounded-lg object-cover">
                        <div v-else class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/50 text-neutral-400">
                          <span class="text-[10px] font-semibold">{{ attachmentKindLabel(attachment.kind) }}</span>
                        </div>
                        <div class="min-w-0 flex-1">
                          <p class="truncate font-mono text-xs">{{ attachment.name }}</p>
                          <p class="font-mono text-[11px] opacity-70">{{ attachment.type || 'application/octet-stream' }} · {{ formatFileSize(attachment.size) }}</p>
                        </div>
                      </div>
                    </div>
                    <details v-if="message.result" class="group mt-3 overflow-hidden rounded-xl border border-neutral-100 bg-neutral-50 text-sm text-neutral-700">
                      <summary class="flex cursor-pointer list-none items-start justify-between gap-3 px-3 py-2.5 marker:hidden">
                        <div class="flex min-w-0 flex-1 flex-wrap items-center gap-2">
                          <span class="shrink-0 rounded-full bg-white px-2 py-1 text-xs font-medium text-neutral-700 shadow-sm">
                            {{ actionLabel(message.result.action) }}
                          </span>
                          <span class="min-w-0 break-all font-mono text-xs text-neutral-900">
                            {{ resultApiLabel(message.result) }}
                          </span>
                          <span class="hidden min-w-0 break-all font-mono text-xs text-neutral-500 sm:inline">
                            {{ resultProviderId(message.result) }}
                          </span>
                          <span class="hidden min-w-0 break-all font-mono text-xs text-neutral-500 sm:inline">
                            {{ resultRuntimeModel(message.result) }}
                          </span>
                        </div>
                        <div class="flex shrink-0 items-center gap-2 text-xs text-neutral-500">
                          <span class="font-mono">{{ resultConfidence(message.result) }}</span>
                          <span class="inline-block transition-transform group-open:rotate-180">⌄</span>
                        </div>
                      </summary>
                      <div class="space-y-3 border-t border-neutral-100 px-3 pb-3 pt-3">
                        <div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
                          <p class="min-w-0"><span class="text-neutral-500">Action</span><br><span class="break-all font-mono text-neutral-900">{{ actionLabel(message.result.action) }}</span></p>
                          <p class="min-w-0"><span class="text-neutral-500">API</span><br><span class="break-all font-mono text-neutral-900">{{ resultApiLabel(message.result) }}</span></p>
                          <p class="min-w-0"><span class="text-neutral-500">置信度</span><br><span class="break-all font-mono text-neutral-900">{{ resultConfidence(message.result) }}</span></p>
                          <p class="min-w-0"><span class="text-neutral-500">候选</span><br><span class="break-all font-mono text-neutral-900">{{ resultCandidateCount(message.result) }}</span></p>
                          <p class="min-w-0"><span class="text-neutral-500">Provider</span><br><span class="break-all font-mono text-neutral-900">{{ resultProviderId(message.result) }}</span></p>
                          <p class="min-w-0"><span class="text-neutral-500">厂商</span><br><span class="break-all font-mono text-neutral-900">{{ resultProviderKind(message.result) }}</span></p>
                          <p><span class="text-neutral-500">配置模型</span><br><span class="break-all font-mono text-neutral-900">{{ resultConfiguredModel(message.result) }}</span></p>
                          <p><span class="text-neutral-500">运行版本</span><br><span class="break-all font-mono text-neutral-900">{{ resultRuntimeModel(message.result) }}</span></p>
                        </div>
                        <div v-if="isConfirmResult(message.result)" class="rounded-lg bg-white p-2">
                          <p class="mb-1 text-neutral-500">Pending Instruction</p>
                          <div class="space-y-1 font-mono text-xs leading-5 text-neutral-800">
                            <p class="break-all">api_id: {{ pendingApiLabel(message.result) }}</p>
                            <p class="break-all">risk: {{ pendingRiskLabel(message.result) }}</p>
                            <p
                              v-for="line in traceParamSummary(message.result)"
                              :key="line"
                              class="break-all"
                            >
                              {{ line }}
                            </p>
                          </div>
                        </div>
                        <div v-if="isClarifyResult(message.result)" class="rounded-lg bg-white p-2">
                          <p class="mb-1 text-neutral-500">Missing Parameters</p>
                          <div class="space-y-2 text-xs leading-5 text-neutral-800">
                            <div
                              v-for="item in clarifyMissingDetails(message.result)"
                              :key="`debug_missing_${item.name}`"
                              class="rounded-lg bg-neutral-50 p-2"
                            >
                              <p class="break-all font-mono text-neutral-900">{{ item.name }}</p>
                              <p class="break-all text-neutral-600">{{ missingParamMeta(item) }}</p>
                              <p class="break-all text-neutral-500">{{ missingParamHint(item) }}</p>
                            </div>
                          </div>
                        </div>
                        <p class="break-all font-mono text-xs text-neutral-500">run: {{ message.result.run_id || '-' }}</p>
                        <div>
                          <p class="mb-1 text-neutral-500">Params</p>
                          <pre class="max-h-32 overflow-auto rounded-lg bg-white p-2 font-mono text-xs leading-5 text-neutral-800">{{ JSON.stringify(message.result.params || {}, null, 2) }}</pre>
                        </div>
                        <details>
                          <summary class="cursor-pointer text-neutral-500">原始规划结果</summary>
                          <pre class="mt-2 max-h-52 overflow-auto rounded-lg bg-neutral-950 p-2 font-mono text-xs leading-5 text-neutral-100">{{ JSON.stringify(message.result, null, 2) }}</pre>
                        </details>
                      </div>
                    </details>
                  </div>
                </article>
                <article v-if="testSending" class="flex justify-start">
                  <div class="rounded-2xl rounded-bl-md bg-white px-4 py-3 text-sm text-neutral-500 shadow-sm">
                    <span class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-neutral-200 border-t-neutral-600 align-[-2px]"></span>规划中...
                  </div>
                </article>
              </div>
            </div>
            </div>
          </div>
          </div>
          </div>
          </div>

          <button
            type="button"
            class="group hidden h-full min-h-[420px] cursor-col-resize items-center justify-center rounded-xl outline-none 2xl:flex"
            title="拖动调整模拟器和运行控制宽度"
            aria-label="拖动调整模拟器和运行控制宽度"
            @pointerdown="startPreviewResize"
          >
            <span
              class="flex h-24 w-3 items-center justify-center rounded-full border border-neutral-200 bg-white shadow-sm transition group-hover:border-neutral-300 group-hover:bg-neutral-50 group-hover:shadow"
              :class="isPreviewResizing ? 'border-neutral-400 bg-neutral-100 shadow' : ''"
            >
              <span class="grid gap-1">
                <span class="h-1 w-1 rounded-full bg-neutral-400"></span>
                <span class="h-1 w-1 rounded-full bg-neutral-400"></span>
                <span class="h-1 w-1 rounded-full bg-neutral-400"></span>
              </span>
            </span>
          </button>

          <aside class="flex min-w-0 flex-col overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-sm" :style="runControlShellStyle">
            <div class="shrink-0 border-b border-neutral-100 px-5 py-4">
              <h3 class="text-base font-semibold text-neutral-950">运行控制</h3>
              <p class="mt-0.5 text-sm text-neutral-500">选择模型、身份和测试上下文。</p>
            </div>
            <div class="flex min-h-0 flex-col gap-4 overflow-y-auto p-5" :style="runControlBodyStyle">
              <div class="grid shrink-0 grid-cols-1 gap-3">
                <label class="block text-sm font-medium text-neutral-700">
                  Planner Mode
                  <select v-model="plannerMode" class="mt-1 w-full rounded-xl border border-neutral-200 px-3 py-2.5 text-sm outline-none focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10">
                    <option value="deterministic">deterministic</option>
                    <option value="hybrid">hybrid</option>
                    <option value="llm">llm</option>
                  </select>
                </label>
                <label class="block text-sm font-medium text-neutral-700">
                  未命中 API
                  <select v-model="noApiHitStrategy" :disabled="plannerMode === 'deterministic'" class="mt-1 w-full rounded-xl border border-neutral-200 px-3 py-2.5 text-sm outline-none focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10 disabled:bg-neutral-50">
                    <option value="hybrid">混合模式：AI 回复，失败走固定兜底</option>
                    <option value="llm_answer">大模型自然回复</option>
                    <option value="fixed">固定兜底</option>
                  </select>
                </label>
                <label class="block text-sm font-medium text-neutral-700">
                  Identity
                  <select v-model="plannerIdentityId" class="mt-1 w-full rounded-xl border border-neutral-200 px-3 py-2.5 text-sm outline-none focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10">
                    <option value="">不指定</option>
                    <option v-for="identity in identityDefinitions" :key="identity.id" :value="identity.id">{{ identity.id }}</option>
                  </select>
                </label>
                <label class="block text-sm font-medium text-neutral-700">
                  Provider
                  <select v-model="plannerProviderId" :disabled="plannerMode === 'deterministic'" class="mt-1 w-full rounded-xl border border-neutral-200 px-3 py-2.5 text-sm outline-none focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10 disabled:bg-neutral-50">
                    <option value="">不指定</option>
                    <option v-for="provider in activeProviderConfigs" :key="provider.id" :value="provider.id">{{ provider.id }}</option>
                  </select>
                </label>
              </div>
              <div v-if="testResult" class="grid shrink-0 grid-cols-2 gap-2">
                <div class="rounded-xl bg-neutral-50 px-3 py-2">
                  <p class="text-xs text-neutral-500">Action</p>
                  <p class="mt-1 truncate text-sm font-semibold text-neutral-900">{{ actionLabel(testResult.action) }}</p>
                </div>
                <div class="rounded-xl bg-neutral-50 px-3 py-2">
                  <p class="text-xs text-neutral-500">API</p>
                  <p class="mt-1 truncate font-mono text-sm font-semibold text-neutral-900">{{ testResult.api?.id || '-' }}</p>
                </div>
              </div>
              <label class="flex min-h-[220px] flex-1 flex-col text-sm font-medium text-neutral-700">
                Context JSON
                <textarea v-model="contextText" rows="7" class="mt-1 min-h-0 flex-1 resize-none rounded-xl border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10"></textarea>
              </label>
              <label class="shrink-0 text-sm font-medium text-neutral-700">
                Params JSON
                <textarea v-model="paramsText" rows="4" class="mt-1 w-full resize-none rounded-xl border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10"></textarea>
              </label>
              <pre v-if="testResult" class="max-h-56 shrink-0 overflow-auto rounded-xl bg-neutral-950 p-3 text-xs leading-5 text-neutral-100">{{ JSON.stringify(testResult, null, 2) }}</pre>
            </div>
          </aside>
        </section>

        <div class="flex items-center gap-3 pt-1">
          <button
            class="group flex shrink-0 items-center gap-2 rounded-full border border-neutral-200 bg-white px-3 py-1.5 text-sm font-semibold tracking-wide text-neutral-700 shadow-sm hover:border-neutral-300 hover:bg-neutral-50"
            type="button"
            @click="systemSettingsCollapsed = !systemSettingsCollapsed"
          >
            <span class="inline-block text-xs text-neutral-500 transition-transform group-hover:text-neutral-700" :class="systemSettingsCollapsed ? '-rotate-90' : 'rotate-0'">⌄</span>
            系统设置
          </button>
          <div class="h-px flex-1 bg-neutral-200"></div>
        </div>

        <section v-show="!systemSettingsCollapsed" class="grid grid-cols-1 gap-4 xl:grid-cols-2 2xl:grid-cols-4">
          <section class="min-h-0 overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-sm">
            <div class="flex items-center justify-between gap-3 border-b border-neutral-100 px-4 py-3">
              <div class="min-w-0">
                <h3 class="text-base font-semibold text-neutral-950">模型池服务</h3>
                <p class="mt-0.5 truncate text-sm text-neutral-500">{{ modelPoolServiceLabel }}</p>
              </div>
              <button class="shrink-0 rounded-xl bg-neutral-950 px-3 py-2 text-sm text-white hover:bg-neutral-800" @click="editModelPoolProvider">
                {{ modelPoolRegisteredProvider ? '编辑' : '注册' }}
              </button>
            </div>
            <div class="max-h-[620px] overflow-y-auto p-4">
              <div class="grid grid-cols-2 gap-2">
                <div class="rounded-lg bg-neutral-50 px-3 py-2">
                  <p class="text-[11px] text-neutral-500">注册状态</p>
                  <p class="mt-0.5 text-sm font-semibold" :class="modelPoolRegisteredProvider ? 'text-success-700' : 'text-warning-700'">{{ modelPoolRegisteredProvider ? '已注册' : '未注册' }}</p>
                </div>
                <div class="rounded-lg bg-neutral-50 px-3 py-2">
                  <p class="text-[11px] text-neutral-500">模型池</p>
                  <p class="mt-0.5 text-sm font-semibold text-neutral-900">{{ formatNumber(modelPoolModels.length) }}</p>
                </div>
                <div class="rounded-lg bg-neutral-50 px-3 py-2">
                  <p class="text-[11px] text-neutral-500">聊天可路由</p>
                  <p class="mt-0.5 text-sm font-semibold text-neutral-900">{{ formatNumber(modelPoolChatModels.length) }}</p>
                </div>
                <div class="rounded-lg bg-neutral-50 px-3 py-2">
                  <p class="text-[11px] text-neutral-500">可用未耗尽</p>
                  <p class="mt-0.5 text-sm font-semibold text-neutral-900">{{ formatNumber(modelPoolUsableModels.length) }}</p>
                </div>
              </div>
              <p v-if="modelPoolModels.length" class="mt-3 text-xs text-neutral-500">
                已加载全部 {{ formatNumber(modelPoolModels.length) }} 个模型，表格内滚动查看。
              </p>
              <div v-if="modelPoolModels.length" class="mt-2 max-h-[420px] overflow-auto rounded-xl border border-neutral-100">
                <table class="min-w-full text-left text-xs">
                  <thead class="sticky top-0 bg-white text-neutral-500">
                    <tr>
                      <th class="px-3 py-2">模型</th>
                      <th class="px-3 py-2">状态</th>
                      <th class="px-3 py-2">剩余额度</th>
                      <th class="px-3 py-2">成功</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-neutral-100">
                    <tr v-for="model in modelPoolModels" :key="model.model">
                      <td class="max-w-[180px] truncate px-3 py-2 font-mono text-neutral-900">{{ model.model }}</td>
                      <td class="px-3 py-2 text-neutral-600">{{ modelStatus(model) }}</td>
                      <td class="px-3 py-2 text-neutral-600">{{ formatNumber(model.remaining_tokens) }}</td>
                      <td class="px-3 py-2 text-neutral-600">{{ formatNumber(model.success_count) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div v-else class="mt-3 rounded-xl border border-dashed border-neutral-200 px-3 py-6 text-center text-sm text-neutral-500">
                暂无模型池数据。注册带 model_pool 能力的 Provider 后，这里会展示可观测状态。
              </div>
            </div>
          </section>

          <section class="min-h-0 overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-sm">
            <div class="flex items-center justify-between gap-3 border-b border-neutral-100 px-4 py-3">
              <div class="min-w-0">
                <h3 class="text-base font-semibold text-neutral-950">Host Executor</h3>
                <p class="mt-0.5 truncate text-sm text-neutral-500">注册执行契约，不保存宿主业务函数</p>
              </div>
              <span class="shrink-0 rounded-full bg-neutral-100 px-3 py-1 text-xs font-semibold text-neutral-700">{{ activeHostExecutorDefinitions.length }} 个</span>
            </div>
            <div class="max-h-[620px] overflow-y-auto p-4">
              <div v-if="activeHostExecutorDefinitions.length" class="space-y-2">
                <article
                  v-for="executor in activeHostExecutorDefinitions"
                  :key="executor.id"
                  class="rounded-xl border border-neutral-100 bg-neutral-50 px-3 py-2"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="truncate text-sm font-semibold text-neutral-950">{{ textValue(executor.name) || executor.id }}</p>
                      <p class="mt-0.5 break-all font-mono text-xs text-neutral-500">{{ executor.id }}</p>
                    </div>
                    <span class="shrink-0 rounded-full bg-white px-2 py-1 text-[11px] text-neutral-600">{{ executor.kind }}</span>
                  </div>
                  <p class="mt-2 break-words text-xs leading-5 text-neutral-600">{{ textValue(executor.description) || '宿主应用按同 ID 接入 runtime implementation。' }}</p>
                  <p class="mt-2 break-all font-mono text-[11px] text-neutral-500">runtime: {{ executor.runtime?.implementation || 'host_app' }}</p>
                </article>
              </div>
              <div v-else class="rounded-xl border border-dashed border-neutral-200 px-3 py-6 text-center text-sm text-neutral-500">
                暂无 Host Executor。写入类 API 可先注册执行契约，再由宿主应用接入同 ID 的运行实现。
              </div>
            </div>
          </section>

          <section class="min-h-0 overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-sm">
            <div class="flex items-center justify-between gap-3 border-b border-neutral-100 px-4 py-3">
              <div class="min-w-0">
                <h3 class="text-base font-semibold text-neutral-950">Provider 配置</h3>
                <p class="mt-0.5 text-sm text-neutral-500">{{ providerConfigs.length }} 个模型接入</p>
              </div>
              <div class="flex shrink-0 gap-2">
                <button class="rounded-xl border border-neutral-200 px-3 py-2 text-sm hover:bg-neutral-50" @click="startCreateProvider">新增</button>
                <button class="rounded-xl bg-neutral-950 px-3 py-2 text-sm text-white disabled:opacity-60" :disabled="providerSaving" @click="saveProvider">{{ providerSaving ? '保存中' : '保存' }}</button>
              </div>
            </div>
            <div class="max-h-[620px] overflow-y-auto p-4">
              <div class="-mx-1 flex gap-2 overflow-x-auto px-1 pb-2">
                <button
                  v-for="provider in providerConfigs"
                  :key="provider.id"
                  class="min-w-[168px] shrink-0 rounded-xl border px-3 py-2 text-left text-xs"
                  :class="selectedProviderId === provider.id ? 'border-primary bg-primary/5 text-primary' : 'border-neutral-100 hover:bg-neutral-50'"
                  @click="selectProvider(provider)"
                >
                  <p class="truncate font-semibold">{{ provider.id }}</p>
                  <p class="mt-1 truncate font-mono text-neutral-500">{{ provider.provider }} · {{ provider.model }}</p>
                </button>
              </div>

              <div v-if="providerEditor" class="mt-2 grid grid-cols-1 gap-3">
                <div class="flex flex-wrap gap-2">
                  <button class="rounded-xl border border-neutral-200 px-3 py-2 text-sm hover:bg-neutral-50 disabled:opacity-60" :disabled="providerTesting" @click="previewProvider">Payload 预览</button>
                  <button v-if="selectedProvider" class="rounded-xl border border-danger-200 px-3 py-2 text-sm text-danger-700 hover:bg-danger-50 disabled:opacity-60" :disabled="providerDeleting" @click="deleteProvider">删除</button>
                </div>
                <label class="text-sm font-medium text-neutral-700">
                  ID
                  <input v-model.trim="providerEditor.id" :disabled="Boolean(providerEditor.originalId)" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-primary disabled:bg-neutral-50">
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  Provider
                  <select v-model="providerEditor.provider" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary">
                    <option v-for="option in providerOptions" :key="option" :value="option">{{ option }}</option>
                  </select>
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  Base URL
                  <input v-model.trim="providerEditor.baseUrl" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-primary">
                </label>
                <div class="grid grid-cols-1 gap-3 2xl:grid-cols-2">
                  <label class="text-sm font-medium text-neutral-700">
                    Model
                    <input v-model.trim="providerEditor.model" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-primary">
                  </label>
                  <label class="text-sm font-medium text-neutral-700">
                    Secret Ref
                    <input v-model.trim="providerEditor.secretRef" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-primary">
                  </label>
                  <label class="text-sm font-medium text-neutral-700">
                    Priority
                    <input v-model.number="providerEditor.routingPriority" type="number" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary">
                  </label>
                  <label class="flex items-center gap-2 pt-7 text-sm font-medium text-neutral-700">
                    <input v-model="providerEditor.isActive" type="checkbox" class="rounded border-neutral-300 text-primary focus:ring-primary">
                    启用
                  </label>
                </div>
                <label class="text-sm font-medium text-neutral-700">
                  Capabilities
                  <textarea v-model="providerEditor.capabilitiesText" rows="4" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary"></textarea>
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  Routing Tasks
                  <textarea v-model="providerEditor.routingTasksText" rows="4" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary"></textarea>
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  Default Headers JSON
                  <textarea v-model="providerEditor.defaultHeadersText" rows="4" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary"></textarea>
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  Extra JSON
                  <textarea v-model="providerEditor.extraText" rows="4" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary"></textarea>
                </label>
              </div>
              <div v-else class="mt-3 rounded-xl border border-dashed border-neutral-200 px-3 py-6 text-center text-sm text-neutral-500">
                选择或新增 Provider
              </div>
              <pre v-if="providerTestResult" class="mt-3 max-h-56 overflow-auto rounded-lg bg-neutral-950 p-3 text-xs text-neutral-100">{{ JSON.stringify(providerTestResult, null, 2) }}</pre>
            </div>
          </section>

          <section class="min-h-0 overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-sm">
            <div class="flex items-center justify-between gap-3 border-b border-neutral-100 px-4 py-3">
              <div class="min-w-0">
                <h3 class="text-base font-semibold text-neutral-950">身份定义</h3>
                <p class="mt-0.5 text-sm text-neutral-500">{{ identityDefinitions.length }} 个执行身份</p>
              </div>
              <div class="flex shrink-0 gap-2">
                <button class="rounded-xl border border-neutral-200 px-3 py-2 text-sm hover:bg-neutral-50" @click="startCreateIdentity">新增</button>
                <button class="rounded-xl bg-neutral-950 px-3 py-2 text-sm text-white disabled:opacity-60" :disabled="identitySaving" @click="saveIdentity">{{ identitySaving ? '保存中' : '保存' }}</button>
              </div>
            </div>
            <div class="max-h-[620px] overflow-y-auto p-4">
              <div class="-mx-1 flex gap-2 overflow-x-auto px-1 pb-2">
                <button
                  v-for="identity in identityDefinitions"
                  :key="identity.id"
                  class="min-w-[168px] shrink-0 rounded-xl border px-3 py-2 text-left text-xs"
                  :class="selectedIdentityId === identity.id ? 'border-primary bg-primary/5 text-primary' : 'border-neutral-100 hover:bg-neutral-50'"
                  @click="selectIdentity(identity)"
                >
                  <p class="truncate font-semibold">{{ identity.id }}</p>
                  <p class="mt-1 truncate text-neutral-500">{{ textValue(identity.name) }} · {{ identity.actor_type }}</p>
                </button>
              </div>

              <div v-if="identityEditor" class="mt-2 grid grid-cols-1 gap-3">
                <div class="flex flex-wrap gap-2">
                  <button v-if="selectedIdentity" class="rounded-xl border border-danger-200 px-3 py-2 text-sm text-danger-700 hover:bg-danger-50 disabled:opacity-60" :disabled="identityDeleting" @click="deleteIdentity">删除</button>
                </div>
                <div class="grid grid-cols-1 gap-3 2xl:grid-cols-2">
                  <label class="text-sm font-medium text-neutral-700">
                    ID
                    <input v-model.trim="identityEditor.id" :disabled="Boolean(identityEditor.originalId)" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-primary disabled:bg-neutral-50">
                  </label>
                  <label class="text-sm font-medium text-neutral-700">
                    Actor Type
                    <input v-model.trim="identityEditor.actorType" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary">
                  </label>
                  <label class="text-sm font-medium text-neutral-700">
                    中文名称
                    <input v-model.trim="identityEditor.nameZh" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary">
                  </label>
                  <label class="text-sm font-medium text-neutral-700">
                    Host App
                    <input v-model.trim="identityEditor.hostApp" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-sm outline-none focus:border-primary">
                  </label>
                </div>
                <label class="text-sm font-medium text-neutral-700">
                  Role Aliases
                  <textarea v-model="identityEditor.roleAliasesText" rows="4" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary"></textarea>
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  Permissions
                  <textarea v-model="identityEditor.permissionsText" rows="4" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary"></textarea>
                </label>
                <div class="grid grid-cols-1 gap-3 2xl:grid-cols-2">
                  <label class="text-sm font-medium text-neutral-700">
                    Allow APIs
                    <textarea v-model="identityEditor.allowedApiIdsText" rows="4" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary"></textarea>
                  </label>
                  <label class="text-sm font-medium text-neutral-700">
                    Deny APIs
                    <textarea v-model="identityEditor.deniedApiIdsText" rows="4" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary"></textarea>
                  </label>
                </div>
                <label class="text-sm font-medium text-neutral-700">
                  系统提示词
                  <textarea v-model="identityEditor.systemPromptZh" rows="5" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-primary"></textarea>
                </label>
                <label class="flex items-center gap-2 text-sm font-medium text-neutral-700">
                  <input v-model="identityEditor.isActive" type="checkbox" class="rounded border-neutral-300 text-primary focus:ring-primary">
                  启用
                </label>
                <label class="text-sm font-medium text-neutral-700">
                  Metadata JSON
                  <textarea v-model="identityEditor.metadataText" rows="5" class="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 font-mono text-xs outline-none focus:border-primary"></textarea>
                </label>
              </div>
              <div v-else class="mt-3 rounded-xl border border-dashed border-neutral-200 px-3 py-6 text-center text-sm text-neutral-500">
                选择或新增身份
              </div>
            </div>
          </section>
        </section>
      </template>
    </div>
  </AdminLayout>
</template>
