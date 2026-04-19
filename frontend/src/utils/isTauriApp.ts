/**
 * True when the bundle runs inside a Tauri WebView (set by the Tauri/Vite pipeline).
 */
export function isTauriApp(): boolean {
  return Boolean(import.meta.env.TAURI_ENV_PLATFORM)
}
