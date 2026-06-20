<script setup lang="ts">
import type { RunSummary } from '~/types'
import { formatDate } from '~/types'

defineProps<{
  runs: RunSummary[]
  selectedRunId?: string | null
  loading?: boolean
  deleting?: boolean
  deletingRunId?: string | null
}>()

const emit = defineEmits<{
  select: [runId: string]
  delete: []
  deleteRun: [runId: string]
}>()

function statusColor(status: RunSummary['status']) {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'error'
  return 'warning'
}

function preview(run: RunSummary) {
  const text = run.crafted_tweet?.trim()
  if (!text) return 'No output yet'
  return text.replace(/\s+/g, ' ').slice(0, 120) + (text.length > 120 ? '…' : '')
}
</script>

<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between gap-2">
      <h3 class="text-xs font-bold uppercase tracking-widest text-gray-400">Run history</h3>
      <UButton
        v-if="runs.length > 0"
        size="xs"
        color="error"
        variant="ghost"
        icon="i-lucide-trash-2"
        :loading="deleting"
        :disabled="loading || deleting || !!deletingRunId"
        @click="emit('delete')"
      >
        Clear
      </UButton>
    </div>

    <div v-if="loading" class="text-xs text-gray-500">Loading runs…</div>

    <div v-else-if="runs.length === 0" class="text-xs text-gray-500">
      No runs yet. Click Play to start one.
    </div>

    <div v-else class="space-y-1.5">
      <div
        v-for="run in runs"
        :key="run.run_id"
        class="flex items-start gap-1 rounded-lg border transition-colors"
        :class="selectedRunId === run.run_id
          ? 'border-primary-500/40 bg-primary-500/10'
          : 'border-gray-800 bg-gray-900 hover:border-gray-700'"
      >
        <button
          type="button"
          class="flex min-w-0 flex-1 flex-col gap-1 px-3 py-2.5 text-left"
          @click="emit('select', run.run_id)"
        >
          <div class="flex flex-wrap items-center gap-2">
            <UBadge :color="statusColor(run.status)" variant="subtle" size="xs">
              {{ run.status }}
            </UBadge>
            <span class="text-xs text-gray-400">
              {{ formatDate(run.completed_at ?? run.started_at) }}
            </span>
          </div>
          <p class="line-clamp-2 text-xs text-gray-500">
            {{ preview(run) }}
          </p>
        </button>
        <UButton
          size="xs"
          color="error"
          variant="ghost"
          icon="i-lucide-trash-2"
          class="my-2 mr-1 shrink-0"
          :loading="deletingRunId === run.run_id"
          :disabled="loading || deleting || deletingRunId === run.run_id"
          @click.stop="emit('deleteRun', run.run_id)"
        />
      </div>
    </div>
  </div>
</template>
