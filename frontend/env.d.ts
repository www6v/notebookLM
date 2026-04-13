/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

declare module 'markdown-it-katex' {
  import type MarkdownIt from 'markdown-it'

  const markdownItKatex: MarkdownIt.PluginSimple
  export default markdownItKatex
}
