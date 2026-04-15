/**
 * UUID for optimistic client-side message ids.
 *
 * crypto.randomUUID() is only available in secure contexts (HTTPS or
 * localhost). Plain http:// production sites throw; use fallbacks.
 */
export const createClientUuid = (): string => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = new Uint8Array(16)
    crypto.getRandomValues(bytes)
    bytes[6] = (bytes[6] & 0x0f) | 0x40
    bytes[8] = (bytes[8] & 0x3f) | 0x80
    const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-`
      + `${hex.slice(16, 20)}-${hex.slice(20)}`
  }
  return `local-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`
}
