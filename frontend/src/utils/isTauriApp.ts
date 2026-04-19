/**
 * True when the SPA runs inside a Tauri WebView.
 *
 * `import.meta.env.TAURI_ENV_*` is only defined if `@tauri-apps/vite-plugin` is
 * configured; `window.__TAURI_INTERNALS__` is always set by the WebView at
 * runtime, so we rely on it for `cargo tauri dev` without the plugin.
 */
export function isTauriApp(): boolean {
  if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
    return true
  }
  return Boolean(import.meta.env.TAURI_ENV_PLATFORM)
}
