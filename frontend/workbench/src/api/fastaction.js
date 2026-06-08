const API_BASE = import.meta.env.VITE_FASTACTION_API_BASE || ''

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}/fastaction${path}`, {
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers || {})
    },
    ...options
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `FastAction request failed: ${response.status}`)
  }
  if (response.status === 204) return null
  return response.json()
}

function jsonRequest(path, method, body) {
  return request(path, { method, body: JSON.stringify(body ?? {}) })
}

function queryString(params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, value)
  })
  const value = search.toString()
  return value ? `?${value}` : ''
}

export const getFastActionHealth = () => request('/health')
export const getFastActionApiDefinitions = () => request('/api-definitions')
export const saveFastActionApiDefinition = (payload) => jsonRequest('/api-definitions', 'POST', payload)
export const deleteFastActionApiDefinition = (id) => request(`/api-definitions/${encodeURIComponent(id)}`, { method: 'DELETE' })
export const getFastActionCardDefinitions = () => request('/card-definitions')
export const getFastActionHostExecutors = () => request('/host-executors')
export const saveFastActionHostExecutor = (payload) => jsonRequest('/host-executors', 'POST', payload)
export const deleteFastActionHostExecutor = (id) => request(`/host-executors/${encodeURIComponent(id)}`, { method: 'DELETE' })
export const getFastActionProviderConfigs = () => request('/provider-configs')
export const getFastActionProviderPresets = () => request('/provider-presets')
export const saveFastActionProviderConfig = (payload) => jsonRequest('/provider-configs', 'POST', payload)
export const deleteFastActionProviderConfig = (id) => request(`/provider-configs/${encodeURIComponent(id)}`, { method: 'DELETE' })
export const testFastActionProviderConfig = (id, payload) => jsonRequest(`/provider-configs/${encodeURIComponent(id)}/test`, 'POST', payload)
export const getFastActionProviderModelPoolStatus = (id) => request(`/provider-configs/${encodeURIComponent(id)}/model-pool`)
export const getFastActionIdentityDefinitions = () => request('/identity-definitions')
export const saveFastActionIdentityDefinition = (payload) => jsonRequest('/identity-definitions', 'POST', payload)
export const deleteFastActionIdentityDefinition = (id) => request(`/identity-definitions/${encodeURIComponent(id)}`, { method: 'DELETE' })
export const getFastActionKnowledgeDefinitions = () => request('/knowledge-definitions')
export const getFastActionOptionSets = () => request('/option-sets')
export const saveFastActionOptionSet = (payload, isUpdate = false) => {
  const id = String(payload?.id || '').trim()
  return jsonRequest(isUpdate ? `/option-sets/${encodeURIComponent(id)}` : '/option-sets', isUpdate ? 'PUT' : 'POST', payload)
}
export const deleteFastActionOptionSet = (id) => request(`/option-sets/${encodeURIComponent(id)}`, { method: 'DELETE' })
export const getFastActionRuns = () => request('/runs')
export const planFastActionChat = (payload) => jsonRequest('/chat', 'POST', payload)
export const getFastActionTestMessages = (params = {}) => {
  const normalized = typeof params === 'string' ? { session_id: params } : params
  return request(`/test-messages${queryString(normalized)}`)
}
export const clearFastActionTestMessages = (sessionId) => request(`/test-messages?session_id=${encodeURIComponent(sessionId)}`, { method: 'DELETE' })
export const transcribeFastActionAudio = (formData) => request('/audio/transcriptions', { method: 'POST', body: formData })
