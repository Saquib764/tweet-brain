<script setup lang="ts">
import {
  GROUP_SECTIONS,
  groupToInput,
  type Group,
  type GroupCreateInput,
  type GroupInput,
  type GroupMember,
  type GroupSection,
  type GroupSteps,
} from '~/types'
const route = useRoute()
const router = useRouter()
const api = useTweetBrainApi()
const toast = useToast()

const { data, pending, refresh } = await useGroupsList('groups-editor')

const groups = computed(() => data.value?.groups ?? [])
const isCreate = computed(() => route.query.create === '1')
const selectedId = computed(() => route.query.id as string | undefined)
const section = computed(() => route.query.section as GroupSection | undefined)

const selectedGroup = computed<Group | null>(() => {
  if (isCreate.value) return null
  return groups.value.find(item => item.group.id === selectedId.value)?.group ?? null
})

const expandedIds = ref<Set<string>>(new Set())
const saving = ref(false)
const saveError = ref<string | null>(null)

const createForm = reactive({ name: '', category: '', description: '' })

const detailsForm = reactive({
  name: '',
  category: '',
  description: '',
  postsPerUser: 5,
})

const members = ref<GroupMember[]>([])
const newMemberInput = ref('')

interface StepEditorItem {
  name: string
  content: string
}

const DEFAULT_STEP_NAMES = ['Stem', 'Combine', 'Craft'] as const
const NEW_STEP_CONTENT = `You are an expert assistant.

Your task:
Describe what this step should analyze or produce.

Guidelines:
- Be concise and specific
- Focus on actionable output

Return your response in the format required for the next pipeline stage.`
const stepItems = ref<StepEditorItem[]>([])
const selectedStepIndex = ref<number | null>(null)
const dragStepIndex = ref<number | null>(null)

function groupStepsToItems(steps: GroupSteps): StepEditorItem[] {
  if (steps.items?.length) {
    return steps.items.map(item => ({ name: item.name, content: item.content }))
  }
  return [
    { name: DEFAULT_STEP_NAMES[0], content: steps.stem },
    { name: DEFAULT_STEP_NAMES[1], content: steps.combine },
    { name: DEFAULT_STEP_NAMES[2], content: steps.craft },
  ]
}

function itemsToGroupSteps(items: StepEditorItem[]): GroupSteps {
  const normalized = items.map(item => ({
    name: item.name.trim() || 'Step',
    content: item.content,
  }))
  return {
    items: normalized,
    stem: normalized[0]?.content ?? '',
    combine: normalized[1]?.content ?? '',
    craft: normalized[2]?.content ?? '',
  }
}

function stepPreview(content: string): string {
  return content.split('\n').slice(0, 3).join('\n')
}

function selectStep(index: number) {
  selectedStepIndex.value = index
}

function addStep() {
  stepItems.value.push({
    name: `Step ${stepItems.value.length + 1}`,
    content: NEW_STEP_CONTENT,
  })
  selectedStepIndex.value = stepItems.value.length - 1
}

function onStepDragStart(index: number, event: DragEvent) {
  dragStepIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(index))
  }
}

function onStepDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
}

function onStepDrop(index: number) {
  if (dragStepIndex.value === null) return
  reorderSteps(dragStepIndex.value, index)
  dragStepIndex.value = null
}

function onStepDragEnd() {
  dragStepIndex.value = null
}

function reorderSteps(from: number, to: number) {
  if (from === to) return
  const items = [...stepItems.value]
  const [moved] = items.splice(from, 1)
  if (!moved) return
  items.splice(to, 0, moved)
  stepItems.value = items

  if (selectedStepIndex.value === from) {
    selectedStepIndex.value = to
  } else if (selectedStepIndex.value !== null) {
    const selected = selectedStepIndex.value
    if (from < selected && to >= selected) selectedStepIndex.value = selected - 1
    else if (from > selected && to <= selected) selectedStepIndex.value = selected + 1
  }
}

const selectedStep = computed(() =>
  selectedStepIndex.value === null ? null : stepItems.value[selectedStepIndex.value] ?? null,
)

watch(selectedId, (id) => {
  if (id) expandedIds.value.add(id)
}, { immediate: true })

watch(selectedGroup, (group) => {
  if (!group) return
  detailsForm.name = group.name
  detailsForm.category = group.category
  detailsForm.description = group.description
  detailsForm.postsPerUser = group.fetch.posts_per_user
  members.value = group.members.map(member => ({ ...member }))
  newMemberInput.value = ''
  stepItems.value = groupStepsToItems(group.steps)
  selectedStepIndex.value = null
}, { immediate: true })

watch(section, (value) => {
  if (value !== 'steps') selectedStepIndex.value = null
})

function navigate(query: Record<string, string>) {
  router.push({ path: '/groups', query })
}

function toggleExpanded(id: string) {
  const next = new Set(expandedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expandedIds.value = next
}

function selectSection(id: string, value: GroupSection) {
  navigate({ id, section: value })
}

function startCreate() {
  navigate({ create: '1' })
}

function isSectionActive(id: string, value: GroupSection) {
  return selectedId.value === id && section.value === value && !isCreate.value
}

async function withSaving(action: () => Promise<void>) {
  saving.value = true
  saveError.value = null
  try {
    await action()
  } catch (err) {
    saveError.value = err instanceof Error ? err.message : 'Request failed'
  } finally {
    saving.value = false
  }
}

async function runUpdate(payload: GroupInput) {
  if (!selectedId.value) return
  await withSaving(async () => {
    await api.updateGroup(selectedId.value!, payload)
    await refresh()
    toast.add({ title: 'Saved', color: 'success' })
  })
}

async function handleCreate() {
  const payload: GroupCreateInput = {
    name: createForm.name.trim(),
    category: createForm.category.trim(),
    description: createForm.description,
  }
  await withSaving(async () => {
    const created = await api.createGroup(payload)
    await refresh()
    expandedIds.value.add(created.group.id)
    toast.add({ title: 'Group created', color: 'success' })
    navigate({ id: created.group.id, section: 'details' })
  })
}

function handleDetailsSave() {
  if (!selectedGroup.value) return
  runUpdate({
    ...groupToInput(selectedGroup.value),
    name: detailsForm.name.trim(),
    category: detailsForm.category.trim(),
    description: detailsForm.description,
    fetch: { posts_per_user: detailsForm.postsPerUser },
  })
}

function memberHandle(account: string) {
  return account.trim().replace(/^@/, '')
}

function memberUrl(account: string) {
  return `https://x.com/${memberHandle(account)}`
}

function buildMembersList(): GroupMember[] {
  const cleaned = members.value
    .map(member => ({ account: memberHandle(member.account) }))
    .filter(member => member.account)

  const pending = memberHandle(newMemberInput.value)
  if (pending && !cleaned.some(member => member.account === pending)) {
    cleaned.unshift({ account: pending })
  }

  return cleaned
}

async function handleMembersSave() {
  if (!selectedGroup.value) return
  const cleaned = buildMembersList()
  members.value = cleaned.map(member => ({ ...member }))
  newMemberInput.value = ''
  await runUpdate({ ...groupToInput(selectedGroup.value), members: cleaned })
}

function handleStepsSave() {
  if (!selectedGroup.value) return
  runUpdate({ ...groupToInput(selectedGroup.value), steps: itemsToGroupSteps(stepItems.value) })
}

function commitNewMember() {
  const account = memberHandle(newMemberInput.value)
  if (!account) return
  if (members.value.some(member => memberHandle(member.account) === account)) {
    newMemberInput.value = ''
    return
  }
  members.value.unshift({ account })
  newMemberInput.value = ''
}

function removeMember(index: number) {
  members.value.splice(index, 1)
}

async function handleDelete() {
  if (!selectedId.value) return
  const deletedId = selectedId.value
  await withSaving(async () => {
    await api.deleteGroup(deletedId)
    await refresh()
    toast.add({ title: 'Group deleted', color: 'success' })
    const next = groups.value.find(item => item.group.id !== deletedId)
    if (next) navigate({ id: next.group.id, section: 'details' })
    else startCreate()
  })
}
</script>

<template>
  <div class="min-h-0 flex-1 overflow-hidden">
    <div class="flex h-full min-h-0">
      <aside class="w-64 shrink-0 overflow-y-auto border-r border-gray-800 bg-gray-900 p-4">
        <div class="mb-4 flex items-center justify-between gap-2">
          <h1 class="text-sm font-bold text-white">Groups</h1>
          <UButton v-if="groups.length > 0" size="xs" icon="i-lucide-plus" @click="startCreate">
            New
          </UButton>
        </div>

        <div v-if="pending" class="text-xs text-gray-500">Loading…</div>

        <div v-else-if="groups.length === 0" class="space-y-3">
          <p class="text-xs text-gray-500">No list found</p>
          <UButton size="sm" icon="i-lucide-plus" block @click="startCreate">
            Create
          </UButton>
        </div>

        <nav v-else class="space-y-1">
          <div v-for="item in groups" :key="item.group.id">
            <button
              type="button"
              class="flex w-full items-center gap-1 rounded-md px-2 py-2 text-left text-sm transition-colors"
              :class="selectedId === item.group.id && !isCreate
                ? 'font-medium text-primary-400'
                : 'text-gray-300 hover:bg-gray-800'"
              @click="toggleExpanded(item.group.id)"
            >
              <UIcon
                :name="expandedIds.has(item.group.id) ? 'i-lucide-chevron-down' : 'i-lucide-chevron-right'"
                class="h-4 w-4 shrink-0 text-gray-500"
              />
              <span class="truncate">{{ item.group.name }}</span>
            </button>

            <div v-if="expandedIds.has(item.group.id)" class="ml-5 space-y-0.5 border-l border-gray-800 pl-2">
              <button
                v-for="entry in GROUP_SECTIONS"
                :key="entry.value"
                type="button"
                class="block w-full rounded-md px-2 py-1.5 text-left text-xs transition-colors"
                :class="isSectionActive(item.group.id, entry.value)
                  ? 'bg-primary-500/15 font-medium text-primary-400'
                  : 'text-gray-500 hover:bg-gray-800 hover:text-gray-300'"
                @click="selectSection(item.group.id, entry.value)"
              >
                {{ entry.label }}
              </button>
            </div>
          </div>
        </nav>
      </aside>

      <div
        class="min-h-0 flex-1"
        :class="selectedGroup && section === 'steps' && !isCreate
          ? 'flex flex-col overflow-hidden'
          : 'overflow-y-auto p-4 sm:p-6'"
      >
        <div
          v-if="!(selectedGroup && section === 'steps' && !isCreate)"
          class="mx-auto max-w-3xl"
        >
          <UAlert
            v-if="saveError"
            color="error"
            variant="subtle"
            :title="saveError"
            class="mb-4"
          />

          <div v-if="saving" class="mb-4 text-sm text-gray-500">Saving…</div>

          <form v-if="isCreate" class="space-y-4" @submit.prevent="handleCreate">
            <h2 class="text-xs font-bold uppercase tracking-widest text-gray-400">New group</h2>

            <UFormField label="Name" required>
              <UInput v-model="createForm.name" placeholder="AI News" required />
            </UFormField>

            <UFormField label="Category" required>
              <UInput v-model="createForm.category" placeholder="tech" required />
            </UFormField>

            <UFormField label="Description">
              <UTextarea
                v-model="createForm.description"
                :rows="3"
                placeholder="What this group tracks and why"
              />
            </UFormField>

            <div class="flex justify-end">
              <UButton type="button" icon="i-lucide-plus" :loading="saving" @click="handleCreate">
                Create
              </UButton>
            </div>
          </form>

          <form
            v-else-if="selectedGroup && section === 'details'"
            class="space-y-4"
            @submit.prevent="handleDetailsSave"
          >
            <h2 class="text-xs font-bold uppercase tracking-widest text-gray-400">Details</h2>
            <p class="text-xs text-gray-500">ID: <code class="rounded bg-gray-950 px-1 py-0.5 text-xs text-primary-300 ring-1 ring-gray-800">{{ selectedGroup.id }}</code></p>

            <div class="grid gap-4 sm:grid-cols-2">
              <UFormField label="Name" required>
                <UInput v-model="detailsForm.name" required />
              </UFormField>
              <UFormField label="Category" required>
                <UInput v-model="detailsForm.category" required />
              </UFormField>
            </div>

            <UFormField label="Description">
              <UTextarea v-model="detailsForm.description" :rows="3" />
            </UFormField>

            <UFormField label="Posts per member">
              <UInput v-model.number="detailsForm.postsPerUser" type="number" min="1" max="100" />
            </UFormField>

            <div class="flex flex-wrap justify-between gap-3">
              <UButton type="button" color="error" variant="outline" icon="i-lucide-trash-2" @click="handleDelete">
                Delete group
              </UButton>
              <UButton type="button" icon="i-lucide-save" :loading="saving" @click="handleDetailsSave">
                Save
              </UButton>
            </div>
          </form>

          <form
            v-else-if="selectedGroup && section === 'members'"
            class="space-y-4"
            @submit.prevent="handleMembersSave"
          >
            <h2 class="text-xs font-bold uppercase tracking-widest text-gray-400">Members</h2>

            <div class="flex flex-wrap items-center gap-2">
              <span
                v-for="(member, index) in members"
                :key="`${memberHandle(member.account)}-${index}`"
                class="inline-flex items-center gap-1 rounded-full border border-gray-700 bg-gray-900 py-1 pl-2.5 pr-1 text-sm text-gray-200"
              >
                @{{ memberHandle(member.account) }}
                <a
                  :href="memberUrl(member.account)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex rounded p-1 text-gray-500 transition-colors hover:text-primary-400"
                  :aria-label="`Open @${memberHandle(member.account)} on X`"
                >
                  <UIcon name="i-lucide-external-link" class="size-3.5" />
                </a>
                <button
                  type="button"
                  class="inline-flex rounded p-1 text-gray-500 transition-colors hover:text-red-400"
                  :aria-label="`Remove @${memberHandle(member.account)}`"
                  @click="removeMember(index)"
                >
                  <UIcon name="i-lucide-trash-2" class="size-3.5" />
                </button>
              </span>

              <UInput
                v-model="newMemberInput"
                placeholder="@handle"
                size="sm"
                class="w-36"
                @keydown.enter.prevent="commitNewMember"
              />
            </div>

            <div class="flex justify-end">
              <UButton type="button" icon="i-lucide-save" :loading="saving" @click="handleMembersSave">
                Save
              </UButton>
            </div>
          </form>

          <div v-else-if="!pending && !isCreate" class="text-sm text-gray-500">
            Select Details, Members, or Steps from the sidebar.
          </div>
        </div>

        <form
          v-else-if="selectedGroup && section === 'steps'"
          class="flex min-h-0 flex-1 flex-col"
          @submit.prevent="handleStepsSave"
        >
          <div class="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-gray-800 px-4 py-4 sm:px-6">
            <div>
              <h2 class="text-xs font-bold uppercase tracking-widest text-gray-400">Steps</h2>
              <p class="mt-1 text-xs text-gray-500">Drag to reorder. Click a step to edit its prompt.</p>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <UButton type="button" size="sm" variant="outline" icon="i-lucide-plus" @click="addStep">
                Step
              </UButton>
              <UButton type="button" size="sm" :loading="saving" icon="i-lucide-save" @click="handleStepsSave">
                Save
              </UButton>
            </div>
          </div>

          <UAlert
            v-if="saveError"
            color="error"
            variant="subtle"
            :title="saveError"
            class="mx-4 mt-4 shrink-0 sm:mx-6"
          />

          <div v-if="saving" class="mx-4 mt-4 shrink-0 text-sm text-gray-500 sm:mx-6">Saving…</div>

          <div class="flex min-h-0 flex-1">
            <div class="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
              <div class="space-y-2">
                <div
                  v-for="(item, index) in stepItems"
                  :key="index"
                  class="flex gap-2 rounded-lg border border-gray-800 bg-gray-950 transition-colors"
                  :class="selectedStepIndex === index ? 'border-primary-500/40 ring-1 ring-primary-500/20' : ''"
                  @dragover="onStepDragOver"
                  @drop.prevent="onStepDrop(index)"
                >
                  <button
                    type="button"
                    class="flex shrink-0 cursor-grab items-center px-2 text-gray-500 hover:text-gray-300 active:cursor-grabbing"
                    draggable="true"
                    aria-label="Reorder step"
                    @dragstart="onStepDragStart(index, $event)"
                    @dragend="onStepDragEnd"
                    @click.stop
                  >
                    <UIcon name="i-lucide-grip-vertical" class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="min-w-0 flex-1 px-3 py-3 text-left"
                    @click="selectStep(index)"
                  >
                    <div class="text-sm font-medium text-white">{{ item.name || 'Untitled step' }}</div>
                    <p class="mt-1 whitespace-pre-wrap text-sm text-gray-500">
                      {{ stepPreview(item.content) || 'No prompt yet' }}
                    </p>
                  </button>
                </div>
              </div>
            </div>

            <aside
              v-if="selectedStep"
              class="flex w-[32rem] shrink-0 flex-col border-l border-gray-800 bg-gray-900/50"
            >
              <div class="flex items-center justify-between border-b border-gray-800 px-4 py-3">
                <h3 class="text-xs font-bold uppercase tracking-widest text-gray-400">Edit step</h3>
                <UButton
                  type="button"
                  color="neutral"
                  variant="ghost"
                  size="xs"
                  icon="i-lucide-x"
                  aria-label="Close editor"
                  @click="selectedStepIndex = null"
                />
              </div>
              <div class="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4">
                <UFormField label="Name">
                  <UInput v-model="selectedStep.name" placeholder="Step name" />
                </UFormField>
                <UFormField label="Prompt" class="flex min-h-0 flex-1 flex-col">
                  <UTextarea
                    v-model="selectedStep.content"
                    :rows="24"
                    class="min-h-[24rem] w-full"
                    placeholder="LLM prompt"
                  />
                </UFormField>
              </div>
            </aside>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
