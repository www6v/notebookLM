import { isTauriApp } from '@/utils/isTauriApp'

export async function readDesktopBackendUrl(): Promise<string> {
  if (!isTauriApp()) {
    return ''
  }
  const { invoke } = await import('@tauri-apps/api/core')
  return invoke<string>('settings_get_backend_url')
}

export async function writeDesktopBackendUrl(url: string): Promise<void> {
  if (!isTauriApp()) {
    return
  }
  const { invoke } = await import('@tauri-apps/api/core')
  await invoke('settings_set_backend_url', { url })
}
