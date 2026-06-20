<script setup lang="ts">
import {
  SETTINGS_SECTIONS,
  type AppSettingsUpdate,
  type SettingsSection,
} from '~/types'

const route = useRoute()
const router = useRouter()
const api = useTweetBrainApi()
const toast = useToast()

const section = computed<SettingsSection>(() => {
  return route.query.section === 'grok' ? 'grok' : 'xdk'
})

function selectSection(value: SettingsSection) {
  router.push({ path: '/settings', query: { section: value } })
}

const { data, pending, refresh } = await useAsyncData('settings', async () => {
  try {
    return await api.getSettings()
  } catch {
    return null
  }
})

const saving = ref(false)
const saveError = ref<string | null>(null)

const xBearerToken = ref('')
const xaiApiKey = ref('')
const xaiModel = ref('grok-4.3')

watch(data, (settings) => {
  if (settings?.xai.model) {
    xaiModel.value = settings.xai.model
  }
}, { immediate: true })

function placeholder(field: { configured: boolean, masked: string } | undefined) {
  return field?.configured ? field.masked : ''
}

async function handleSave() {
  const payload: AppSettingsUpdate = {}
  const xApi: NonNullable<AppSettingsUpdate['x_api']> = {}
  if (xBearerToken.value) xApi.bearer_token = xBearerToken.value
  if (Object.keys(xApi).length) payload.x_api = xApi

  const xai: NonNullable<AppSettingsUpdate['xai']> = {}
  if (xaiApiKey.value) xai.api_key = xaiApiKey.value
  if (xaiModel.value) xai.model = xaiModel.value
  if (Object.keys(xai).length) payload.xai = xai

  if (!payload.x_api && !payload.xai) {
    saveError.value = 'Enter at least one value to save.'
    return
  }

  saving.value = true
  saveError.value = null
  try {
    await api.updateSettings(payload)
    xBearerToken.value = ''
    xaiApiKey.value = ''
    await refresh()
    toast.add({ title: 'Settings saved', color: 'success' })
  } catch (err) {
    saveError.value = err instanceof Error ? err.message : 'Failed to save settings'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="min-h-0 flex-1 overflow-hidden">
    <div class="flex h-full min-h-0">
      <aside class="w-64 shrink-0 overflow-y-auto border-r border-gray-800 bg-gray-900 p-4">
        <h1 class="mb-4 text-sm font-bold text-white">Settings</h1>

        <nav class="space-y-0.5">
          <button
            v-for="entry in SETTINGS_SECTIONS"
            :key="entry.value"
            type="button"
            class="block w-full rounded-md px-2 py-1.5 text-left text-xs transition-colors"
            :class="section === entry.value
              ? 'bg-primary-500/15 font-medium text-primary-400'
              : 'text-gray-500 hover:bg-gray-800 hover:text-gray-300'"
            @click="selectSection(entry.value)"
          >
            {{ entry.label }}
          </button>
        </nav>
      </aside>

      <div class="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
        <div class="mx-auto max-w-3xl">
          <div v-if="pending" class="text-sm text-gray-500">Loading settings…</div>

          <form v-else class="space-y-6" @submit.prevent="handleSave">
            <section v-if="section === 'xdk'" class="space-y-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <h2 class="text-xs font-bold uppercase tracking-widest text-gray-400">X API (XDK)</h2>
                  <p class="mt-1 text-xs text-gray-500">App-only bearer token from the X Developer Portal.</p>
                </div>
                <UBadge :color="data?.x_api_configured ? 'success' : 'warning'">
                  {{ data?.x_api_configured ? 'Configured' : 'Not configured' }}
                </UBadge>
              </div>

              <UFormField label="Bearer Token">
                <UInput
                  v-model="xBearerToken"
                  type="password"
                  :placeholder="placeholder(data?.x_api.bearer_token)"
                  autocomplete="off"
                />
              </UFormField>
            </section>

            <section v-else class="space-y-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <h2 class="text-xs font-bold uppercase tracking-widest text-gray-400">xAI Grok</h2>
                  <p class="mt-1 text-xs text-gray-500">Used for the stem → combine → craft workflow.</p>
                </div>
                <UBadge :color="data?.xai_configured ? 'success' : 'warning'">
                  {{ data?.xai_configured ? 'Configured' : 'Not configured' }}
                </UBadge>
              </div>

              <UFormField label="API Key">
                <UInput
                  v-model="xaiApiKey"
                  type="password"
                  :placeholder="placeholder(data?.xai.api_key)"
                  autocomplete="off"
                />
              </UFormField>

              <UFormField label="Model">
                <UInput v-model="xaiModel" placeholder="grok-4.3" />
              </UFormField>
            </section>

            <UAlert
              v-if="saveError"
              color="error"
              variant="subtle"
              :title="saveError"
              class="mb-2"
            />

            <div class="flex justify-end">
              <UButton type="submit" :loading="saving" icon="i-lucide-save">
                Save settings
              </UButton>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
