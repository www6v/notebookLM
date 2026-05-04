
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
import markdownItMultimdTable from 'markdown-it-multimd-table'
import 'katex/dist/katex.min.css'

defineOptions({
  name: 'MarkdownRenderer',
})

const props = withDefaults(
  defineProps<{
    content?: string | null
    /** When true, raw HTML in markdown is passed through (e.g. PDF tables). */
    allowHtml?: boolean
  }>(),
  {
    content: '',
    allowHtml: false,
  },
)

const mdSafe = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

mdSafe.use(markdownItKatex)
mdSafe.use(markdownItMultimdTable)

const mdUnsafe = new MarkdownIt({
  html: true,
  linkify: true,
  breaks: true,
})

mdUnsafe.use(markdownItKatex)
mdUnsafe.use(markdownItMultimdTable)

const renderedHtml = computed(() => {
  const engine = props.allowHtml ? mdUnsafe : mdSafe
  return engine.render(props.content || '')
})
</script>

<style scoped>
.markdown-renderer :deep(h1),
.markdown-renderer :deep(h2),
.markdown-renderer :deep(h3) {
  margin: 0.75em 0 0.4em;
  font-weight: 600;
  line-height: 1.3;
  color: #202124;
}

.markdown-renderer :deep(p) {
  margin: 0.5em 0;
  line-height: 1.65;
  color: #202124;
}

.markdown-renderer :deep(ul),
.markdown-renderer :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.4em;
}

.markdown-renderer :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: 13px;
  display: block;
  overflow-x: auto;
}

.markdown-renderer :deep(th),
.markdown-renderer :deep(td) {
  border: 1px solid #dadce0;
  padding: 8px 10px;
  text-align: left;
}

.markdown-renderer :deep(th) {
  background: #f1f3f4;
  font-weight: 600;
}

.markdown-renderer :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

.markdown-renderer :deep(pre) {
  overflow-x: auto;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e8eaed;
  font-size: 12px;
}

.markdown-renderer :deep(.citation-highlight) {
  background: #fff3cd;
  border-radius: 3px;
  padding: 2px 0;
  border-bottom: 2px solid #ffc107;
}
</style>
