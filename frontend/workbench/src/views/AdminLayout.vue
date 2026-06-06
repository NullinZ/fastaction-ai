<template>
  <div class="min-h-screen bg-slate-50 text-slate-950">
    <header class="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div class="mx-auto flex max-w-[1600px] items-center justify-between px-5 py-3">
        <router-link to="/fastaction" class="text-sm font-semibold tracking-[0.18em] text-teal-700">
          FASTACTION
        </router-link>
        <nav class="flex items-center gap-2 text-sm">
          <router-link to="/fastaction" class="rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100">
            API Registry
          </router-link>
          <router-link to="/fastaction/test" class="rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100">
            Test Bench
          </router-link>
          <router-link to="/fastaction/cards" class="rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100">
            Card Gallery
          </router-link>
        </nav>
      </div>
    </header>
    <main class="mx-auto max-w-[1600px] px-5 py-5">
      <slot />
    </main>
  </div>
</template>
