<script setup lang="ts">
import type { GroupSteps, GroupWithMeta, PostCache, RunSummary, StepResult } from '~/types'

const route = useRoute()
const router = useRouter()
const api = useTweetBrainApi()

const { data, pending, refresh } = await useGroupsList('dashboard')

const groups = computed(() => data.value?.groups ?? [])

const selectedGroupId = ref<string | null>(null)

const selectedGroup = computed<GroupWithMeta | null>(() => {
  if (!selectedGroupId.value) return null
  return groups.value.find(item => item.group.id === selectedGroupId.value) ?? null
})

type RunState = 'idle' | 'fetching' | 'running' | 'done' | 'error'
type SelectedView = 'posts' | number

const runState = ref<RunState>('idle')
const posts = ref<PostCache | null>(null)
const stepResults = ref<StepResult[]>([])
const selectedView = ref<SelectedView>('posts')
const runError = ref<string | null>(null)
const runningStepIndex = ref<number | null>(null)
const currentRunId = ref<string | null>(null)
const runHistory = ref<RunSummary[]>([])
const historyPending = ref(false)
const historyDeleting = ref(false)
const deletingRunId = ref<string | null>(null)

function groupSteps(steps: GroupSteps) {
  if (steps.items?.length) {
    return steps.items
  }
  return [
    { name: 'Stem', content: steps.stem },
    { name: 'Combine', content: steps.combine },
    { name: 'Craft', content: steps.craft },
  ]
}

const stepItems = computed(() => {
  if (!selectedGroup.value) return []
  return groupSteps(selectedGroup.value.group.steps)
})

function resetRunState() {
  runState.value = 'idle'
  posts.value = null
  stepResults.value = []
  selectedView.value = 'posts'
  runError.value = null
  runningStepIndex.value = null
  currentRunId.value = null
}

async function loadRunHistory(groupId: string) {
  historyPending.value = true
  try {
    const result = await api.listRuns(groupId)
    runHistory.value = result.runs
  } catch {
    runHistory.value = []
  } finally {
    historyPending.value = false
  }
}

async function handleDeleteHistory() {
  if (!selectedGroup.value || runHistory.value.length === 0) return
  if (!confirm('Delete all run history for this group? This cannot be undone.')) return

  const groupId = selectedGroup.value.group.id
  historyDeleting.value = true
  runError.value = null

  try {
    await api.deleteRunHistory(groupId)
    runHistory.value = []
    resetRunState()
    await refresh()
  } catch (err) {
    runError.value = err instanceof Error ? err.message : 'Failed to delete run history'
  } finally {
    historyDeleting.value = false
  }
}

async function handleDeleteRun(runId: string) {
  if (!selectedGroup.value) return
  if (!confirm('Delete this run? This cannot be undone.')) return

  const groupId = selectedGroup.value.group.id
  deletingRunId.value = runId
  runError.value = null

  try {
    await api.deleteRun(runId)
    runHistory.value = runHistory.value.filter(run => run.run_id !== runId)
    if (currentRunId.value === runId) {
      resetRunState()
    }
    await refresh()
  } catch (err) {
    runError.value = err instanceof Error ? err.message : 'Failed to delete run'
  } finally {
    deletingRunId.value = null
  }
}

async function loadHistoricalRun(runId: string) {
  if (!selectedGroup.value) return

  const groupId = selectedGroup.value.group.id
  runError.value = null

  try {
    const run = await api.getRun(runId)
    currentRunId.value = run.run_id
    stepResults.value = run.stages.steps ?? []
    runState.value = 'done'

    try {
      posts.value = await api.getPosts(groupId)
    } catch {
      posts.value = null
    }

    if (stepResults.value.length > 0) {
      selectedView.value = stepResults.value.length - 1
    } else {
      selectedView.value = 'posts'
    }
  } catch (err) {
    runError.value = err instanceof Error ? err.message : 'Failed to load run'
  }
}

function selectGroup(id: string) {
  if (selectedGroupId.value === id) return
  selectedGroupId.value = id
  resetRunState()
  router.replace({ query: { ...route.query, group: id } })
}

function stepStatus(index: number): 'idle' | 'running' | 'done' {
  if (runningStepIndex.value === index) return 'running'
  if (stepResults.value.some(result => result.index === index)) return 'done'
  return 'idle'
}

function selectView(view: SelectedView) {
  selectedView.value = view
}

async function handlePlay() {
  if (!selectedGroup.value || stepItems.value.length === 0) return

  const groupId = selectedGroup.value.group.id
  runError.value = null
  stepResults.value = []
  currentRunId.value = null
  selectedView.value = 'posts'
  runState.value = 'fetching'

  try {
    posts.value = await api.fetchPosts(groupId, { days: 3 })
    runState.value = 'running'

    const run = await api.startRun(groupId)
    currentRunId.value = run.run_id

    for (let index = 0; index < stepItems.value.length; index++) {
      runningStepIndex.value = index
      const updated = await api.executeStep(groupId, run.run_id, index)
      const result = updated.stages?.steps?.find(step => step.index === index)
      if (result) {
        stepResults.value = [...stepResults.value.filter(s => s.index !== index), result]
      }
      selectedView.value = index
    }

    runState.value = 'done'
    await Promise.all([refresh(), loadRunHistory(groupId)])
  } catch (err) {
    runState.value = 'error'
    runError.value = err instanceof Error ? err.message : 'Run failed'
  } finally {
    runningStepIndex.value = null
  }
}

watch(
  () => route.query.group,
  (groupId) => {
    if (typeof groupId === 'string' && groupId) {
      selectedGroupId.value = groupId
    }
  },
  { immediate: true },
)

watch(groups, (items) => {
  if (!selectedGroupId.value && items.length > 0 && route.query.group) {
    const id = route.query.group as string
    if (items.some(item => item.group.id === id)) {
      selectedGroupId.value = id
    }
  }
})

watch(
  selectedGroupId,
  (groupId) => {
    if (groupId) {
      loadRunHistory(groupId)
    } else {
      runHistory.value = []
    }
  },
  { immediate: true },
)
</script>

<template>
  <div class="min-h-0 flex-1 overflow-hidden">
    <div class="flex h-full min-h-0">
      <aside class="w-64 shrink-0 overflow-y-auto border-r border-gray-800 bg-gray-900 p-4">
        <div class="mb-4 flex items-center justify-between gap-2">
          <h1 class="text-sm font-bold text-white">Dashboard</h1>
          <NuxtLink to="/groups?create=1">
            <UButton size="xs" icon="i-lucide-plus">
              New
            </UButton>
          </NuxtLink>
        </div>

        <div v-if="pending" class="text-xs text-gray-500">Loading groups…</div>

        <div v-else-if="groups.length === 0" class="space-y-3">
          <p class="text-xs text-gray-500">No groups yet.</p>
          <NuxtLink to="/groups?create=1">
            <UButton size="sm" icon="i-lucide-plus" block>
              Create group
            </UButton>
          </NuxtLink>
        </div>

        <nav v-else class="space-y-1">
          <button
            v-for="item in groups"
            :key="item.group.id"
            type="button"
            class="flex w-full flex-col rounded-md px-3 py-2 text-left transition-colors"
            :class="selectedGroupId === item.group.id
              ? 'bg-primary-500/15 text-primary-400'
              : 'text-gray-300 hover:bg-gray-800'"
            @click="selectGroup(item.group.id)"
          >
            <span class="truncate text-sm font-medium">{{ item.group.name }}</span>
            <span class="mt-1 flex flex-wrap gap-1.5 text-xs text-gray-500">
              <UBadge color="neutral" variant="subtle" size="xs">{{ item.group.category }}</UBadge>
              <span>{{ item.group.members.length }} members</span>
            </span>
          </button>
        </nav>
      </aside>

      <main class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden border-r border-gray-800 bg-gray-950">
        <div v-if="!selectedGroup" class="flex flex-1 items-center justify-center p-6 text-sm text-gray-500">
          Select a group to view its workflow steps.
        </div>

        <template v-else>
          <div class="shrink-0 border-b border-gray-800 px-4 py-4 sm:px-6">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 class="text-lg font-bold text-white">{{ selectedGroup.group.name }}</h2>
                <p v-if="selectedGroup.group.description" class="mt-1 text-sm text-gray-500">
                  {{ selectedGroup.group.description }}
                </p>
              </div>
              <UButton
                icon="i-lucide-play"
                :loading="runState === 'fetching' || runState === 'running'"
                :disabled="stepItems.length === 0"
                @click="handlePlay"
              >
                Play
              </UButton>
            </div>
          </div>

          <UAlert
            v-if="runError"
            color="error"
            variant="subtle"
            :title="runError"
            class="mx-4 mt-4 shrink-0 sm:mx-6"
          />

          <div class="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
            <div v-if="stepItems.length === 0" class="text-sm text-gray-500">
              No steps configured.
              <NuxtLink
                :to="`/groups?id=${selectedGroup.group.id}&section=steps`"
                class="text-primary-400 hover:underline"
              >
                Add steps
              </NuxtLink>
            </div>

            <div v-else class="space-y-6">
              <div class="space-y-2">
                <button
                  v-for="(step, index) in stepItems"
                  :key="index"
                  type="button"
                  class="flex w-full items-start gap-3 rounded-lg border px-4 py-3 text-left transition-colors"
                  :class="[
                    selectedView === index
                      ? 'border-primary-500/40 bg-primary-500/10'
                      : 'border-gray-800 bg-gray-900 hover:border-gray-700',
                    stepStatus(index) === 'done' ? 'cursor-pointer' : 'cursor-default',
                  ]"
                  :disabled="stepStatus(index) !== 'done'"
                  @click="stepStatus(index) === 'done' && selectView(index)"
                >
                  <div class="mt-0.5 shrink-0">
                    <UIcon
                      v-if="stepStatus(index) === 'running'"
                      name="i-lucide-loader-circle"
                      class="h-4 w-4 animate-spin text-amber-400"
                    />
                    <UIcon
                      v-else-if="stepStatus(index) === 'done'"
                      name="i-lucide-check-circle"
                      class="h-4 w-4 text-green-400"
                    />
                    <UIcon
                      v-else
                      name="i-lucide-circle"
                      class="h-4 w-4 text-gray-600"
                    />
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-sm font-medium text-white">{{ step.name }}</p>
                    <p class="mt-1 line-clamp-2 text-xs text-gray-500">
                      {{ step.content.split('\n').slice(0, 2).join(' ') }}
                    </p>
                  </div>
                </button>
              </div>

              <RunHistoryList
                :runs="runHistory"
                :selected-run-id="currentRunId"
                :loading="historyPending"
                :deleting="historyDeleting"
                :deleting-run-id="deletingRunId"
                @select="loadHistoricalRun"
                @delete="handleDeleteHistory"
                @delete-run="handleDeleteRun"
              />
            </div>
          </div>
        </template>
      </main>

      <aside class="flex w-[32rem] shrink-0 flex-col overflow-hidden bg-gray-900">
        <div class="shrink-0 border-b border-gray-800 px-4 py-4">
          <div class="flex items-center gap-2">
            <h2 class="text-xs font-bold uppercase tracking-widest text-gray-400">Output</h2>
            <UButton
              v-if="posts"
              size="xs"
              :variant="selectedView === 'posts' ? 'soft' : 'ghost'"
              color="neutral"
              @click="selectView('posts')"
            >
              Posts
            </UButton>
          </div>
        </div>

        <div class="min-h-0 flex-1 overflow-y-auto p-4">
          <div
            v-if="!selectedGroup"
            class="text-sm text-gray-500"
          >
            Output will appear here.
          </div>

          <div
            v-else-if="runState === 'fetching'"
            class="flex items-center gap-2 text-sm text-amber-300"
          >
            <UIcon name="i-lucide-loader-circle" class="h-4 w-4 animate-spin" />
            Fetching posts from the last 3 days…
          </div>

          <div
            v-else-if="runState === 'idle' && !posts"
            class="text-sm text-gray-500"
          >
            Click Play to fetch posts and run the workflow.
          </div>

          <template v-else-if="selectedView === 'posts'">
            <PostFeed :posts="posts?.posts ?? []" />
          </template>

          <template v-else-if="typeof selectedView === 'number'">
            <div
              v-if="stepResults.find(result => result.index === selectedView)"
              class="rounded-lg border border-gray-800 bg-gray-950 p-4"
            >
              <p class="text-xs font-bold uppercase tracking-widest text-primary-400">
                {{ stepItems[selectedView]?.name }}
              </p>
              <MarkdownContent
                class="mt-3"
                :content="stepResults.find(result => result.index === selectedView)?.output ?? ''"
              />
            </div>
            <div v-else class="text-sm text-gray-500">
              Step output not available yet.
            </div>
          </template>
        </div>
      </aside>
    </div>
  </div>
</template>
