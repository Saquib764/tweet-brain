<script setup lang="ts">
import type { Post } from '~/types'
import { formatDate, postUrl } from '~/types'
import { formatPostText } from '~/utils/formatPostText'

defineProps<{
  posts: Post[]
}>()
</script>

<template>
  <div v-if="posts.length === 0" class="rounded-lg border border-gray-800 bg-gray-900 p-5 text-sm text-gray-500">
    No posts cached yet. Fetch posts to get started.
  </div>

  <div v-else class="space-y-3">
    <article
      v-for="post in posts"
      :key="post.id"
      class="rounded-lg border border-gray-800 bg-gray-900 p-5"
    >
      <div class="flex items-center justify-between gap-2 text-xs text-gray-500">
        <div class="flex min-w-0 items-center gap-1.5">
          <span class="truncate font-medium text-primary-400">@{{ post.author }}</span>
          <a
            :href="postUrl(post)"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex shrink-0 rounded p-1 text-gray-500 transition-colors hover:text-primary-400"
            :aria-label="`Open post by @${post.author} on X`"
          >
            <UIcon name="i-lucide-external-link" class="size-3.5" />
          </a>
        </div>
        <span class="shrink-0">{{ formatDate(post.created_at) }}</span>
      </div>
      <p class="mt-2 whitespace-pre-wrap text-sm text-gray-200">
        <template v-for="(part, index) in formatPostText(post.text)" :key="`${post.id}-${index}`">
          <span v-if="part.type === 'text'">{{ part.text }}</span>
          <a
            v-else
            :href="part.href"
            target="_blank"
            rel="noopener noreferrer"
            class="text-primary-400 hover:underline"
          >@{{ part.handle }}</a>
        </template>
      </p>
    </article>
  </div>
</template>
