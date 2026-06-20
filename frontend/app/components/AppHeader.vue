<script setup lang="ts">
const route = useRoute()

const navItems = [
  { label: 'Dashboard', to: '/', icon: 'i-lucide-layout-dashboard' },
  { label: 'Groups', to: '/groups', icon: 'i-lucide-users' },
]

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path === path || route.path.startsWith(`${path}/`)
}
</script>

<template>
  <header class="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-gray-800 bg-gray-900 px-4 sm:px-6">
    <div class="flex min-w-0 items-center gap-6">
      <NuxtLink to="/" class="flex shrink-0 items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-500/15 text-primary-400">
          <UIcon name="i-lucide-brain" class="h-5 w-5" />
        </div>
        <div class="hidden sm:block">
          <p class="text-sm font-bold text-white">Tweet Brain</p>
          <p class="text-xs text-gray-500">X groups → ideas → tweets</p>
        </div>
      </NuxtLink>

      <nav class="flex items-center gap-1">
        <NuxtLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors"
          :class="isActive(item.to)
            ? 'bg-primary-500/15 font-medium text-primary-400'
            : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'"
        >
          <UIcon :name="item.icon" class="h-4 w-4" />
          {{ item.label }}
        </NuxtLink>
      </nav>
    </div>

    <NuxtLink to="/settings">
      <UButton
        color="neutral"
        variant="ghost"
        icon="i-lucide-settings"
        size="sm"
        :class="route.path === '/settings' ? 'text-primary-400' : ''"
      >
        <span class="hidden sm:inline">Settings</span>
      </UButton>
    </NuxtLink>
  </header>
</template>
