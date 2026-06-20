<script setup lang="ts">
import type { WorkflowRun } from '~/types'
import { formatDate } from '~/types'

defineProps<{
  run: WorkflowRun | null
  loading?: boolean
  error?: string | null
}>()
</script>

<template>
  <div class="space-y-4">
    <UAlert
      v-if="error"
      color="error"
      variant="subtle"
      :title="error"
    />

    <div v-if="loading" class="space-y-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-5">
      <div class="flex items-center gap-2 text-amber-300">
        <UIcon name="i-lucide-loader-circle" class="h-4 w-4 animate-spin" />
        <span class="text-sm font-medium">Running workflow steps…</span>
      </div>
      <p class="text-xs text-amber-200/70">Each step feeds its output to the next. This may take a minute.</p>
    </div>

    <template v-if="run && !loading">
      <div class="flex flex-wrap items-center gap-2 text-xs text-gray-500">
        <UBadge :color="run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'warning'">
          {{ run.status }}
        </UBadge>
        <span>Run {{ run.run_id }}</span>
        <span v-if="run.completed_at">· {{ formatDate(run.completed_at) }}</span>
      </div>

      <section v-if="run.stages.steps?.length" class="space-y-2">
        <h3 class="text-xs font-bold uppercase tracking-widest text-gray-400">Step outputs</h3>
        <div class="space-y-2">
          <div
            v-for="step in run.stages.steps"
            :key="step.index"
            class="rounded-lg border border-gray-800 bg-gray-950 p-4"
          >
            <p class="text-xs font-medium text-primary-400">{{ step.name }}</p>
            <MarkdownContent class="mt-2" :content="step.output" />
          </div>
        </div>
      </section>

      <section v-if="run.stages.stem.length" class="space-y-2">
        <h3 class="text-xs font-bold uppercase tracking-widest text-gray-400">Stem analyses</h3>
        <div class="space-y-2">
          <div
            v-for="item in run.stages.stem"
            :key="item.post_id"
            class="rounded-lg border border-gray-800 bg-gray-950 p-4"
          >
            <p class="text-xs font-medium text-primary-400">@{{ item.author }} · {{ item.post_id }}</p>
            <p class="mt-2 whitespace-pre-wrap text-sm text-gray-300">{{ item.analysis }}</p>
          </div>
        </div>
      </section>

      <section v-if="run.stages.combine?.ideas?.length" class="space-y-2">
        <h3 class="text-xs font-bold uppercase tracking-widest text-gray-400">Tweet ideas</h3>
        <ol class="space-y-2">
          <li
            v-for="(idea, index) in run.stages.combine.ideas"
            :key="index"
            class="rounded-lg border border-gray-800 bg-gray-950 px-4 py-3 text-sm text-gray-200"
          >
            <span class="mr-2 font-semibold text-primary-400">{{ index + 1 }}.</span>
            {{ idea }}
          </li>
        </ol>
      </section>

      <section v-if="run.stages.craft?.tweet" class="space-y-2">
        <h3 class="text-xs font-bold uppercase tracking-widest text-gray-400">Crafted tweet</h3>
        <div class="rounded-lg border border-primary-500/30 bg-primary-500/10 p-6">
          <p class="whitespace-pre-wrap text-sm text-white">{{ run.stages.craft.tweet }}</p>
          <p class="mt-2 text-xs text-primary-200/70">{{ run.stages.craft.tweet.length }} characters</p>
        </div>
      </section>

      <UAlert
        v-if="run.error"
        color="error"
        variant="subtle"
        :title="run.error"
      />
    </template>
  </div>
</template>
