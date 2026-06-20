<script setup lang="ts">
useHead({
  meta: [
    { charset: 'utf-8' },
    { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    { name: 'theme-color', content: '#030712' },
    { name: 'color-scheme', content: 'dark' },
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' },
  ],
  htmlAttrs: {
    lang: 'en',
    class: 'scheme-dark',
  },
  bodyAttrs: {
    class: 'scheme-dark bg-gray-950 text-gray-200',
  },
})

useSeoMeta({
  title: 'Tweet Brain',
  description:
    'Track X account groups, collect recent posts, and run Grok LLM workflows to craft tweet ideas.',
})
</script>

<template>
  <UApp>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
