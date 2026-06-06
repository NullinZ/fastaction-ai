<script setup>
import { computed, ref } from 'vue'
import AdminLayout from './AdminLayout.vue'
import CardPreviewRenderer from './CardPreviewRenderer.vue'
import { cardGalleryGroups, cardSnippet, flattenCards } from '../cardGalleryDefinitions'

const activeGroup = ref('all')
const keyword = ref('')
const copiedKey = ref('')

const allCards = flattenCards()

const filteredGroups = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return cardGalleryGroups
    .filter(group => activeGroup.value === 'all' || group.key === activeGroup.value)
    .map(group => ({
      ...group,
      cards: group.cards.filter(card => {
        if (!query) return true
        return [
          card.type,
          card.name,
          card.nameZh,
          card.purpose,
          card.purposeZh,
          card.status,
          card.visual,
          ...(card.style || []),
          ...(card.styleZh || [])
        ].join(' ').toLowerCase().includes(query)
      })
    }))
    .filter(group => group.cards.length)
})

const coreCount = computed(() => allCards.filter(card => card.status === 'core').length)
const exampleCount = computed(() => allCards.filter(card => card.status === 'example').length)
const hostCount = computed(() => allCards.filter(card => card.status === 'host').length)

const statusStyles = {
  core: 'border-teal-200 bg-teal-50 text-teal-800',
  example: 'border-blue-200 bg-blue-50 text-blue-800',
  host: 'border-amber-200 bg-amber-50 text-amber-800'
}

const statusLabels = {
  core: 'Core',
  example: 'Example',
  host: 'Host'
}

async function copySnippet(card, kind) {
  const text = cardSnippet(card, kind)
  const key = `${card.type}:${kind}`
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.setAttribute('readonly', 'true')
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }
  copiedKey.value = key
  window.setTimeout(() => {
    if (copiedKey.value === key) copiedKey.value = ''
  }, 1600)
}

function copiedLabel(card, kind, label) {
  return copiedKey.value === `${card.type}:${kind}` ? 'Copied' : label
}
</script>

<template>
  <AdminLayout>
    <div class="flex h-[calc(100vh-96px)] min-h-0 flex-col gap-4 overflow-hidden">
      <section class="shrink-0 rounded-2xl border border-slate-200 bg-white/95 px-5 py-4 shadow-sm">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-3">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700">FastAction Card Gallery</p>
              <span class="hidden h-4 w-px bg-slate-200 sm:block"></span>
              <p class="text-sm text-slate-500">Preview, copy, and bind card protocols</p>
            </div>
            <h1 class="mt-1 truncate text-2xl font-semibold text-slate-950">卡片库与字段绑定样例</h1>
          </div>

          <div class="grid w-full grid-cols-4 gap-2 xl:w-[560px]">
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
              <p class="text-xs text-slate-500">Total</p>
              <p class="mt-0.5 text-lg font-semibold text-slate-950">{{ allCards.length }}</p>
            </div>
            <div class="rounded-xl border border-teal-200 bg-teal-50 px-3 py-2">
              <p class="text-xs text-teal-700">Core</p>
              <p class="mt-0.5 text-lg font-semibold text-teal-800">{{ coreCount }}</p>
            </div>
            <div class="rounded-xl border border-blue-200 bg-blue-50 px-3 py-2">
              <p class="text-xs text-blue-700">Examples</p>
              <p class="mt-0.5 text-lg font-semibold text-blue-800">{{ exampleCount }}</p>
            </div>
            <div class="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2">
              <p class="text-xs text-amber-700">Host</p>
              <p class="mt-0.5 text-lg font-semibold text-amber-800">{{ hostCount }}</p>
            </div>
          </div>
        </div>

        <div class="mt-4 grid grid-cols-1 gap-2 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div class="flex min-w-0 gap-2 overflow-x-auto">
            <button
              class="shrink-0 rounded-xl border px-3 py-2 text-sm font-medium transition-colors"
              :class="activeGroup === 'all' ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'"
              @click="activeGroup = 'all'"
            >
              All cards
            </button>
            <button
              v-for="group in cardGalleryGroups"
              :key="group.key"
              class="shrink-0 rounded-xl border px-3 py-2 text-sm font-medium transition-colors"
              :class="activeGroup === group.key ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'"
              @click="activeGroup = group.key"
            >
              {{ group.nameZh }}
            </button>
          </div>
          <input
            v-model="keyword"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950 focus:ring-2 focus:ring-slate-950/10"
            placeholder="Search card_type, purpose, style"
          >
        </div>
      </section>

      <section class="min-h-0 flex-1 overflow-y-auto pr-1">
        <div class="space-y-5">
          <section
            v-for="group in filteredGroups"
            :key="group.key"
            class="space-y-3"
          >
            <div class="flex flex-wrap items-end justify-between gap-3">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <h2 class="text-lg font-semibold text-slate-950">{{ group.nameZh }}</h2>
                  <span class="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-xs text-slate-500">{{ group.scope }}</span>
                </div>
                <p class="mt-1 max-w-4xl text-sm leading-6 text-slate-500">{{ group.descriptionZh }}</p>
              </div>
              <p class="text-xs uppercase tracking-[0.14em] text-slate-400">{{ group.cards.length }} cards</p>
            </div>

            <div class="grid grid-cols-1 gap-4 2xl:grid-cols-2">
              <article
                v-for="card in group.cards"
                :key="card.type"
                class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
              >
                <div class="grid min-h-full grid-cols-1 xl:grid-cols-[minmax(0,1fr)_440px]">
                  <div class="min-w-0 p-4">
                    <div class="flex flex-wrap items-start justify-between gap-3">
                      <div class="min-w-0">
                        <div class="flex flex-wrap items-center gap-2">
                          <h3 class="truncate text-base font-semibold text-slate-950">{{ card.nameZh }}</h3>
                          <span class="rounded-full border px-2 py-0.5 text-[11px] font-semibold" :class="statusStyles[card.status]">
                            {{ statusLabels[card.status] }}
                          </span>
                        </div>
                        <p class="mt-1 font-mono text-xs text-teal-700">{{ card.type }}</p>
                      </div>
                      <p class="rounded-lg bg-slate-100 px-2 py-1 text-xs text-slate-500">{{ card.visual }}</p>
                    </div>

                    <p class="mt-3 text-sm leading-6 text-slate-600">{{ card.purposeZh }}</p>

                    <div class="mt-3 flex flex-wrap gap-1.5">
                      <span
                        v-for="item in card.styleZh"
                        :key="item"
                        class="rounded-lg bg-slate-100 px-2 py-1 text-xs text-slate-600"
                      >
                        {{ item }}
                      </span>
                    </div>

                    <div class="mt-4 grid grid-cols-3 gap-2">
                      <button
                        class="rounded-xl border border-slate-200 px-2 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        @click="copySnippet(card, 'definition')"
                      >
                        {{ copiedLabel(card, 'definition', 'Copy Definition') }}
                      </button>
                      <button
                        class="rounded-xl border border-slate-200 px-2 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        @click="copySnippet(card, 'render')"
                      >
                        {{ copiedLabel(card, 'render', 'Copy Render') }}
                      </button>
                      <button
                        class="rounded-xl border border-slate-200 px-2 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        @click="copySnippet(card, 'response')"
                      >
                        {{ copiedLabel(card, 'response', 'Copy Response') }}
                      </button>
                    </div>

                    <details class="mt-4 rounded-xl border border-slate-200 bg-slate-50">
                      <summary class="cursor-pointer px-3 py-2 text-sm font-medium text-slate-700">Field bindings</summary>
                      <pre class="max-h-44 overflow-auto border-t border-slate-200 p-3 text-xs leading-5 text-slate-700">{{ cardSnippet(card, 'render') }}</pre>
                    </details>
                  </div>

                  <div class="space-y-3 border-t border-slate-100 bg-slate-50 p-4 xl:border-l xl:border-t-0">
                    <div>
                      <div class="mb-2 flex items-center justify-between">
                        <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Card Image</p>
                        <span class="rounded-full bg-white px-2 py-0.5 text-[11px] text-slate-500">standalone</span>
                      </div>
                      <CardPreviewRenderer :card="card" />
                    </div>

                    <div>
                      <div class="mb-2 flex items-center justify-between">
                        <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Chat Window</p>
                        <span class="rounded-full bg-white px-2 py-0.5 text-[11px] text-slate-500">embedded</span>
                      </div>
                      <div class="overflow-hidden rounded-[1.35rem] border border-slate-300 bg-slate-100 shadow-sm">
                        <div class="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-2.5">
                          <div>
                            <p class="text-sm font-semibold text-slate-950">Assistant</p>
                            <p class="text-[11px] text-slate-400">FastAction preview</p>
                          </div>
                          <span class="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
                        </div>
                        <div class="space-y-3 p-3">
                          <div class="ml-auto max-w-[78%] rounded-2xl bg-slate-950 px-3 py-2 text-sm leading-5 text-white">
                            Show this result
                          </div>
                          <div class="max-w-[92%] rounded-2xl bg-white p-2.5 shadow-sm">
                            <p class="mb-2 text-xs leading-5 text-slate-500">Here is the structured result.</p>
                            <CardPreviewRenderer :card="card" compact />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </section>

          <section v-if="!filteredGroups.length" class="rounded-2xl border border-slate-200 bg-white p-12 text-center text-slate-500">
            No matching cards.
          </section>
        </div>
      </section>
    </div>
  </AdminLayout>
</template>
