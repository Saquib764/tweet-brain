<script setup lang="ts">
import type { GroupWithMeta } from '~/types'
import { formatDate } from '~/types'

defineProps<{
  item: GroupWithMeta
}>()
</script>

<template>
  <NuxtLink :to="`/?group=${item.group.id}`" class="block">
    <UCard class="transition-colors hover:border-primary-500/40">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <p class="truncate text-base font-bold text-white sm:text-lg">{{ item.group.name }}</p>
          <p v-if="item.group.description" class="mt-1 text-sm text-gray-500 line-clamp-2">
            {{ item.group.description }}
          </p>
        </div>
        <UBadge color="neutral" variant="subtle">
          {{ item.group.category }}
        </UBadge>
      </div>

      <div class="mt-4 flex flex-wrap gap-2 text-xs text-gray-400">
        <span class="inline-flex rounded-full border border-primary-500/20 bg-primary-500/10 px-2.5 py-0.5 text-xs font-medium text-primary-400">{{ item.group.members.length }} members</span>
        <span v-if="item.meta.post_count" class="inline-flex rounded-full border border-primary-500/20 bg-primary-500/10 px-2.5 py-0.5 text-xs font-medium text-primary-400">{{ item.meta.post_count }} posts cached</span>
      </div>

      <div class="mt-3 grid gap-1 text-xs text-gray-500">
        <p>Last fetch: {{ formatDate(item.meta.last_fetched_at, 'Never') }}</p>
        <p v-if="item.meta.last_run_at">
          Last run: {{ formatDate(item.meta.last_run_at) }}
          <span v-if="item.meta.last_run_status" class="text-gray-400">({{ item.meta.last_run_status }})</span>
        </p>
      </div>
    </UCard>
  </NuxtLink>
</template>
