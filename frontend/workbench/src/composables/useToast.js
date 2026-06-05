export function useToast() {
  return {
    success(message) {
      globalThis.console?.info?.(`[FastAction] ${message}`)
    },
    error(message) {
      globalThis.console?.error?.(`[FastAction] ${message}`)
    },
    warning(message) {
      globalThis.console?.warn?.(`[FastAction] ${message}`)
    },
    info(message) {
      globalThis.console?.info?.(`[FastAction] ${message}`)
    }
  }
}

