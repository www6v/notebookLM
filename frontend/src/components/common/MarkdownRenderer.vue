<template>
  <div
    class="markdown-renderer"
    v-html="renderedHtml"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import markdownItKatex from 'markdown-it-katex'
import 'katex/dist/katex.min.css'

defineOptions({
  name: 'MarkdownRenderer',
})

const props = withDefaults(
  defineProps<{
    content?: string | null
  }>(),
  {
    content: '',
  }
)

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

md.use(markdownItKatex)

const renderedHtml = computed(() => md.render(props.content || ''))
</script>
