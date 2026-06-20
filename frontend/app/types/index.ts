export interface GroupFetchConfig {
  posts_per_user: number
}

export interface GroupMember {
  account: string
}

export interface GroupStepItem {
  name: string
  content: string
}

export interface GroupSteps {
  items: GroupStepItem[]
  stem: string
  combine: string
  craft: string
}

export interface Group {
  id: string
  name: string
  category: string
  description: string
  members: GroupMember[]
  fetch: GroupFetchConfig
  steps: GroupSteps
}

export interface GroupInput {
  id?: string
  name: string
  category: string
  description: string
  members: GroupMember[]
  fetch: GroupFetchConfig
  steps: GroupSteps
}

export interface GroupCreateInput {
  name: string
  category: string
  description: string
}

export interface GroupMeta {
  last_fetched_at: string | null
  post_count: number
  last_run_at: string | null
  last_run_status: string | null
}

export interface GroupWithMeta {
  group: Group
  meta: GroupMeta
}

export interface Post {
  id: string
  author: string
  text: string
  created_at: string
  url: string
}

export function postUrl(post: Pick<Post, 'author' | 'id' | 'url'>) {
  if (post.url) return post.url
  const handle = post.author.replace(/^@/, '')
  return `https://x.com/${handle}/status/${post.id}`
}

export interface PostCache {
  group_id: string
  fetched_at: string
  posts: Post[]
}

export interface StemResult {
  post_id: string
  author: string
  analysis: string
}

export interface CombineResult {
  ideas: string[]
}

export interface CraftResult {
  tweet: string
}

export interface StepResult {
  name: string
  index: number
  output: string
}

export interface WorkflowStages {
  steps: StepResult[]
  stem: StemResult[]
  combine: CombineResult | null
  craft: CraftResult | null
}

export interface WorkflowRun {
  run_id: string
  group_id: string
  started_at: string
  completed_at: string | null
  status: 'running' | 'completed' | 'failed'
  stages: WorkflowStages
  error: string | null
}

export interface RunSummary {
  run_id: string
  group_id: string
  started_at: string
  completed_at: string | null
  status: 'running' | 'completed' | 'failed'
  idea_count: number
  crafted_tweet: string | null
}

export interface SecretFieldStatus {
  configured: boolean
  masked: string
}

export interface XApiSettingsPublic {
  bearer_token: SecretFieldStatus
}

export interface XaiSettingsPublic {
  api_key: SecretFieldStatus
  model: string
}

export interface AppSettingsPublic {
  x_api: XApiSettingsPublic
  xai: XaiSettingsPublic
  x_api_configured: boolean
  xai_configured: boolean
}

export interface XApiSettingsUpdate {
  bearer_token?: string
}

export interface XaiSettingsUpdate {
  api_key?: string
  model?: string
}

export interface AppSettingsUpdate {
  x_api?: XApiSettingsUpdate
  xai?: XaiSettingsUpdate
}

export type GroupSection = 'details' | 'members' | 'steps'

export const GROUP_SECTIONS: { label: string, value: GroupSection }[] = [
  { label: 'Details', value: 'details' },
  { label: 'Members', value: 'members' },
  { label: 'Steps', value: 'steps' },
]

export type SettingsSection = 'xdk' | 'grok'

export const SETTINGS_SECTIONS: { label: string, value: SettingsSection }[] = [
  { label: 'XDK', value: 'xdk' },
  { label: 'Grok', value: 'grok' },
]

export function groupToInput(group: Group): GroupInput {
  return {
    id: group.id,
    name: group.name,
    category: group.category,
    description: group.description,
    members: group.members.map(member => ({ ...member })),
    fetch: { ...group.fetch },
    steps: { ...group.steps },
  }
}

export function formatDate(value: string | null | undefined, fallback = '') {
  if (!value) return fallback
  return new Date(value).toLocaleString()
}
