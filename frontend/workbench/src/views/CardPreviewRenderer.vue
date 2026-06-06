<script setup>
const props = defineProps({
  card: {
    type: Object,
    required: true
  },
  compact: {
    type: Boolean,
    default: false
  }
})

function sampleData() {
  return props.card.sampleResponse?.data || props.card.sampleResponse || {}
}

function sampleItems() {
  const data = sampleData()
  return data.items || data.todos || data.records || data.highlights || data.files || data.attachments || data.options || []
}

function sampleTitle() {
  const data = sampleData()
  return data.title || data.name || props.card.name
}

function sampleSubtitle() {
  const data = sampleData()
  return data.subtitle || data.summary || data.code || data.phase || props.card.nameZh
}

function sampleRows() {
  return sampleData().rows || []
}

function itemLabel(item, fallback) {
  return item?.title || item?.label || item?.name || item?.value || fallback
}

function itemMeta(item) {
  return [item?.meta, item?.owner_name, item?.status_name, item?.priority_name, item?.created_at, item?.mime_type]
    .filter(Boolean)
    .join(' · ')
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm" :class="compact ? 'p-3 shadow-none' : ''">
    <template v-if="card.visual === 'list'">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <p class="truncate font-semibold text-slate-950">{{ sampleTitle() }}</p>
          <p class="mt-1 truncate text-xs text-slate-500">{{ sampleSubtitle() }}</p>
        </div>
        <span class="shrink-0 rounded-full bg-blue-50 px-2 py-1 text-xs text-blue-700">{{ sampleItems().length }}</span>
      </div>
      <div class="mt-3 space-y-2">
        <div
          v-for="(item, index) in sampleItems().slice(0, compact ? 2 : 3)"
          :key="item.id || item.value || index"
          class="rounded-lg bg-slate-50 px-3 py-2"
        >
          <p class="truncate text-sm font-medium text-slate-900">{{ itemLabel(item, `Item ${index + 1}`) }}</p>
          <p class="mt-0.5 truncate text-xs text-slate-500">{{ itemMeta(item) || 'Ready' }}</p>
        </div>
      </div>
    </template>

    <template v-else-if="card.visual === 'detail'">
      <p class="truncate font-semibold text-slate-950">{{ sampleTitle() }}</p>
      <p class="mt-1 truncate text-xs text-slate-500">{{ sampleSubtitle() }}</p>
      <div class="mt-3 space-y-2">
        <div
          v-for="(row, index) in sampleRows().slice(0, compact ? 2 : 4)"
          :key="index"
          class="flex justify-between gap-4 rounded-lg bg-slate-50 px-3 py-2 text-sm"
        >
          <span class="truncate text-slate-500">{{ row.label }}</span>
          <span class="truncate font-medium text-slate-900">{{ row.value }}</span>
        </div>
      </div>
    </template>

    <template v-else-if="card.visual === 'metric'">
      <p class="text-sm text-slate-500">{{ sampleData().label }}</p>
      <p class="mt-2 font-semibold text-slate-950" :class="compact ? 'text-3xl' : 'text-4xl'">{{ sampleData().value }}</p>
      <p class="mt-2 text-xs font-medium text-amber-700">{{ sampleData().trend }}</p>
    </template>

    <template v-else-if="card.visual === 'result'">
      <span class="rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">{{ sampleData().status }}</span>
      <p class="mt-3 font-semibold text-slate-950">{{ sampleData().title }}</p>
      <p class="mt-2 text-sm leading-6 text-slate-500">{{ sampleData().message }}</p>
      <p class="mt-3 truncate font-mono text-xs text-slate-400">{{ sampleData().reference_id }}</p>
    </template>

    <template v-else-if="card.visual === 'confirm'">
      <span class="rounded-full bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">{{ sampleData().risk }}</span>
      <p class="mt-3 font-semibold text-slate-950">{{ sampleData().title }}</p>
      <p class="mt-2 text-sm leading-6 text-slate-600">{{ sampleData().action }}</p>
      <div class="mt-3 rounded-lg bg-slate-50 p-2 font-mono text-xs text-slate-600">{{ JSON.stringify(sampleData().params) }}</div>
      <div class="mt-3 flex gap-2">
        <button class="rounded-lg bg-slate-950 px-3 py-2 text-xs font-medium text-white">Confirm</button>
        <button class="rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-600">Cancel</button>
      </div>
    </template>

    <template v-else-if="card.visual === 'picker'">
      <p class="font-semibold text-slate-950">{{ sampleTitle() }}</p>
      <div class="mt-3 space-y-2">
        <button
          v-for="(item, index) in sampleItems().slice(0, compact ? 2 : 4)"
          :key="item.value || index"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-left hover:bg-slate-50"
        >
          <p class="truncate text-sm font-medium text-slate-900">{{ item.label }}</p>
          <p class="mt-0.5 truncate text-xs text-slate-500">{{ item.value }} · {{ item.meta }}</p>
        </button>
      </div>
    </template>

    <template v-else-if="card.visual === 'missing'">
      <span class="rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">Need input</span>
      <p class="mt-3 font-semibold text-slate-950">{{ card.sampleResponse.api.name }}</p>
      <div class="mt-3 space-y-2">
        <div
          v-for="item in card.sampleResponse.clarify.missing_param_details.slice(0, compact ? 1 : 3)"
          :key="item.name"
          class="rounded-lg bg-slate-50 px-3 py-2"
        >
          <div class="flex flex-wrap items-center gap-2">
            <p class="text-sm font-medium text-slate-900">{{ item.label.zh || item.label.en }}</p>
            <span class="font-mono text-xs text-slate-500">{{ item.name }}</span>
          </div>
          <p class="mt-1 truncate text-xs text-slate-500">{{ item.source }}</p>
        </div>
      </div>
    </template>

    <template v-else-if="card.visual === 'progress'">
      <p class="font-semibold text-slate-950">{{ sampleData().name }}</p>
      <p class="mt-1 text-xs text-slate-500">{{ sampleData().progress.phase }}</p>
      <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
        <div class="h-full rounded-full bg-teal-600" :style="{ width: `${sampleData().progress.percent}%` }"></div>
      </div>
      <p class="mt-2 text-sm font-semibold text-slate-900">{{ sampleData().progress.percent }}%</p>
      <ul v-if="!compact" class="mt-3 space-y-1 text-xs text-slate-500">
        <li v-for="item in sampleData().milestones" :key="item">{{ item }}</li>
      </ul>
    </template>

    <template v-else-if="card.visual === 'risk'">
      <span class="rounded-full bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">{{ sampleData().level }}</span>
      <p class="mt-3 font-semibold text-slate-950">{{ sampleData().title }}</p>
      <p class="mt-2 text-sm leading-6 text-slate-600">{{ sampleData().reason }}</p>
      <div class="mt-3 flex flex-wrap gap-2">
        <span v-for="item in sampleData().actions" :key="item" class="rounded-lg bg-slate-100 px-2 py-1 text-xs text-slate-600">{{ item }}</span>
      </div>
    </template>

    <template v-else-if="['attachment', 'feed', 'brief'].includes(card.visual)">
      <p class="font-semibold text-slate-950">{{ sampleTitle() }}</p>
      <p class="mt-1 truncate text-xs text-slate-500">{{ sampleSubtitle() }}</p>
      <div class="mt-3 grid gap-2">
        <div
          v-for="(item, index) in sampleItems().slice(0, compact ? 2 : 3)"
          :key="item.id || item.name || item.title || index"
          class="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2"
        >
          <p class="truncate text-sm font-medium text-slate-900">{{ itemLabel(item, `Entry ${index + 1}`) }}</p>
          <p class="mt-0.5 truncate text-xs text-slate-500">{{ itemMeta(item) || item }}</p>
        </div>
      </div>
    </template>

    <template v-else-if="card.visual === 'chat'">
      <div class="rounded-2xl bg-slate-950 px-4 py-3 text-white">
        <p class="text-sm leading-6">{{ card.sampleResponse.message.content }}</p>
      </div>
    </template>

    <template v-else-if="card.visual === 'chips'">
      <button class="rounded-full border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700">
        {{ card.sampleResponse.label }}
      </button>
      <p class="mt-3 text-xs leading-5 text-slate-500">{{ card.sampleResponse.prompt }}</p>
    </template>

    <template v-else-if="card.visual === 'notification'">
      <div class="flex gap-3">
        <span class="mt-1 h-2 w-2 rounded-full bg-blue-600"></span>
        <div class="min-w-0">
          <p class="truncate font-semibold text-slate-950">{{ card.sampleResponse.title }}</p>
          <p class="mt-1 text-sm leading-6 text-slate-600">{{ card.sampleResponse.body }}</p>
          <p class="mt-2 text-xs text-slate-400">{{ card.sampleResponse.created_at }}</p>
        </div>
      </div>
    </template>

    <template v-else>
      <p class="font-semibold text-slate-950">{{ sampleTitle() }}</p>
      <pre class="mt-3 max-h-52 overflow-auto rounded-lg bg-slate-950 p-3 text-xs leading-5 text-slate-100">{{ JSON.stringify(card.sampleResponse, null, 2) }}</pre>
    </template>
  </div>
</template>
