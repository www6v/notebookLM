/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly TAURI_ENV_PLATFORM?: string
  readonly TAURI_ENV_ARCH?: string
}

interface Window {
  /** Present when the page runs inside a Tauri WebView (dev and release). */
  __TAURI_INTERNALS__?: unknown
}

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
