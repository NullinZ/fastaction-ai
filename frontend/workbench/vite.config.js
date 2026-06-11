import { fileURLToPath, URL } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5177,
    proxy: {
      '^/fastaction/(health|chat|api-definitions|card-definitions|card-bindings|host-executors|provider-presets|provider-configs|audio|identity-definitions|knowledge-definitions|option-sets|runs|test-messages|execution-results)': {
        target: process.env.FASTACTION_API_BASE_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
