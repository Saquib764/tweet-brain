import type {
  AppSettingsPublic,
  AppSettingsUpdate,
  GroupCreateInput,
  GroupInput,
  GroupWithMeta,
  PostCache,
  RunSummary,
  WorkflowRun,
} from '~/types'

function getApiBase(): string {
  const config = useRuntimeConfig()
  return config.public.apiBase as string
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const base = getApiBase()
  const response = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      if (body?.detail) {
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export function useTweetBrainApi() {
  const prefix = '/api/v1'

  return {
    listGroups: () =>
      apiFetch<{ groups: GroupWithMeta[] }>(`${prefix}/groups`),

    getGroup: (id: string) =>
      apiFetch<GroupWithMeta>(`${prefix}/groups/${id}`),

    createGroup: (payload: GroupCreateInput) =>
      apiFetch<GroupWithMeta>(`${prefix}/groups`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    updateGroup: (id: string, payload: GroupInput) =>
      apiFetch<GroupWithMeta>(`${prefix}/groups/${id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      }),

    deleteGroup: (id: string) =>
      apiFetch<void>(`${prefix}/groups/${id}`, { method: 'DELETE' }),

    getPosts: (groupId: string) =>
      apiFetch<PostCache>(`${prefix}/groups/${groupId}/posts`),

    fetchPosts: (groupId: string, options?: { days?: number }) => {
      const days = options?.days ?? 3
      return apiFetch<PostCache>(
        `${prefix}/groups/${groupId}/fetch?days=${days}`,
        { method: 'POST' },
      )
    },

    startRun: (groupId: string) =>
      apiFetch<WorkflowRun>(`${prefix}/groups/${groupId}/runs`, { method: 'POST' }),

    executeStep: (groupId: string, runId: string, stepIndex: number) =>
      apiFetch<WorkflowRun>(
        `${prefix}/groups/${groupId}/runs/${runId}/steps/${stepIndex}`,
        { method: 'POST' },
      ),

    runWorkflow: (groupId: string) =>
      apiFetch<WorkflowRun>(`${prefix}/groups/${groupId}/run`, { method: 'POST' }),

    listRuns: (groupId?: string) => {
      const query = groupId ? `?group_id=${encodeURIComponent(groupId)}` : ''
      return apiFetch<{ runs: RunSummary[] }>(`${prefix}/runs${query}`)
    },

    getRun: (runId: string) =>
      apiFetch<WorkflowRun>(`${prefix}/runs/${runId}`),

    deleteRunHistory: (groupId: string) =>
      apiFetch<void>(`${prefix}/groups/${groupId}/runs`, { method: 'DELETE' }),

    deleteRun: (runId: string) =>
      apiFetch<void>(`${prefix}/runs/${runId}`, { method: 'DELETE' }),

    getSettings: () =>
      apiFetch<AppSettingsPublic>(`${prefix}/settings`),

    updateSettings: (payload: AppSettingsUpdate) =>
      apiFetch<AppSettingsPublic>(`${prefix}/settings`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      }),
  }
}

export async function useGroupsList(key = 'groups') {
  const api = useTweetBrainApi()
  return useAsyncData(key, async () => {
    try {
      return await api.listGroups()
    } catch {
      return { groups: [] }
    }
  })
}
