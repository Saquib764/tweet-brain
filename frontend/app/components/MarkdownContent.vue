<script setup lang="ts">
import { marked } from 'marked'

const props = defineProps<{
  content: string
}>()

marked.setOptions({
  gfm: true,
  breaks: true,
})

const html = computed(() => marked.parse(props.content || '') as string)
</script>

<template>
  <div class="tf-markdown text-sm text-gray-200" v-html="html" />
</template>

<style scoped>
.tf-markdown :deep(h1) {
  margin-bottom: 0.75rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--ui-text-highlighted);
}

.tf-markdown :deep(h2) {
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--ui-text-highlighted);
}

.tf-markdown :deep(h2:first-child) {
  margin-top: 0;
}

.tf-markdown :deep(h3) {
  margin-top: 0.75rem;
  margin-bottom: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ui-text-toned);
}

.tf-markdown :deep(p) {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}

.tf-markdown :deep(ul),
.tf-markdown :deep(ol) {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  padding-left: 1.25rem;
}

.tf-markdown :deep(li) {
  margin-top: 0.25rem;
}

.tf-markdown :deep(strong) {
  color: var(--ui-text-highlighted);
  font-weight: 600;
}

.tf-markdown :deep(blockquote) {
  margin-top: 0.75rem;
  border-left: 2px solid rgba(236, 72, 153, 0.45);
  padding-left: 0.75rem;
  color: var(--ui-text-toned);
}

.tf-markdown :deep(pre) {
  margin-top: 0.5rem;
  overflow-x: auto;
  border-radius: 0.375rem;
  border: 1px solid var(--fs-border-subtle);
  background: var(--fs-bg-canvas);
  padding: 0.75rem;
}

.tf-markdown :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8125rem;
  color: var(--ui-text-highlighted);
}

.tf-markdown :deep(pre code) {
  white-space: pre-wrap;
}
</style>
