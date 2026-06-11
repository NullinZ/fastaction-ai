function localizedValue(value) {
  if (!value) return ''
  if (typeof value === 'string') return value
  return value.zh || value['zh-CN'] || value.en || Object.values(value).find(Boolean) || ''
}

function hostExecution(apiDefinition) {
  const execution = apiDefinition?.execution && typeof apiDefinition.execution === 'object'
    ? apiDefinition.execution
    : {}
  const metadata = apiDefinition?.metadata || {}
  const legacy = metadata.host_execution && typeof metadata.host_execution === 'object'
    ? metadata.host_execution
    : {}
  return {
    ...legacy,
    ...execution,
    endpoints: {
      ...(legacy.endpoints || {}),
      ...(execution.endpoints || {})
    }
  }
}

function executorIdFromApi(apiDefinition) {
  const metadata = apiDefinition?.metadata || {}
  return apiDefinition?.execution?.executor_id
    || metadata.host_execution?.id
    || ''
}

function isExecutorActive(definition) {
  return definition && definition.is_active !== false && definition.status !== 'disabled'
}

function executorMatchesApi(definition, apiDefinition) {
  if (!isExecutorActive(definition) || !apiDefinition) return false
  const configuredExecutorId = executorIdFromApi(apiDefinition)
  if (configuredExecutorId && configuredExecutorId === definition.id) return true

  const matcher = definition.matcher || {}
  const apiIds = Array.isArray(matcher.api_ids) ? matcher.api_ids : []
  if (apiIds.includes(apiDefinition.id)) return true

  const operationTypes = Array.isArray(matcher.operation_types) ? matcher.operation_types : []
  const methods = Array.isArray(matcher.methods) ? matcher.methods.map(item => String(item).toUpperCase()) : []
  if (operationTypes.length && !operationTypes.includes(apiDefinition.operation_type)) return false
  if (methods.length && !methods.includes(String(apiDefinition.request?.method || '').toUpperCase())) return false
  return Boolean(operationTypes.length || methods.length)
}

function apiExecutionLabel(apiDefinition, executorDefinition, fallback) {
  return localizedValue(executorDefinition?.name)
    || localizedValue(hostExecution(apiDefinition).label)
    || localizedValue(apiDefinition?.name)
    || fallback
}

const hostExecutorImplementationRegistry = new Map()

export function registerFastActionHostExecutorImplementation(implementation) {
  if (!implementation?.id || typeof implementation.execute !== 'function') {
    throw new Error('Host executor implementation must include id and execute().')
  }
  hostExecutorImplementationRegistry.set(implementation.id, implementation)
  return implementation
}

export function getFastActionHostExecutorImplementationIds() {
  return Array.from(hostExecutorImplementationRegistry.keys())
}

export function getFastActionHostExecutors(definitions = []) {
  const registeredDefinitions = Array.isArray(definitions) ? definitions.filter(isExecutorActive) : []
  return registeredDefinitions.map((definition) => {
    const implementation = hostExecutorImplementationRegistry.get(definition.id)
    if (!implementation) {
      return {
        id: definition.id,
        kind: definition.kind,
        definition,
        missingImplementation: true,
        label: () => localizedValue(definition.name) || definition.id,
        description: () => localizedValue(definition.description) || 'This executor is registered, but the standalone workbench has no host implementation for it.',
        supports: () => false
      }
    }
    return {
      ...implementation,
      definition,
      missingImplementation: false,
      label(apiDefinition) {
        return typeof implementation.label === 'function'
          ? implementation.label(apiDefinition, definition)
          : apiExecutionLabel(apiDefinition, definition, definition.id)
      },
      description(apiDefinition) {
        return typeof implementation.description === 'function'
          ? implementation.description(apiDefinition, definition)
          : localizedValue(definition.description)
      },
      supports(apiDefinition) {
        return typeof implementation.supports === 'function'
          ? implementation.supports(apiDefinition, definition)
          : executorMatchesApi(definition, apiDefinition)
      }
    }
  })
}
