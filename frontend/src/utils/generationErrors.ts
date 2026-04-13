/** Shown when generation is blocked by server rate / concurrency rules. */
export const GENERATION_RATE_LIMIT_SNACKBAR_MESSAGE = '触发限流，请稍后重试'

/**
 * True when the API responded with HTTP 429 (Studio / Deep Research limits).
 */
export const isAxiosGenerationRateLimited = (err: unknown): boolean => {
  if (!err || typeof err !== 'object' || !('response' in err)) {
    return false
  }
  const status = (err as { response?: { status?: number } }).response?.status
  return status === 429
}

/**
 * Matches backend `GenerationRateLimited` user messages (policy.py).
 */
export const isStudioErrorMessageRateLimited = (
  message: string | null | undefined,
): boolean => {
  const m = message?.trim()
  if (!m) {
    return false
  }
  return (
    m.includes('同时进行的生成任务已达上限')
    || m.includes('同一来源同类生成过于频繁')
    || m.includes('免费用户每日最多生成')
    || m.includes('免费用户每日最多发起')
  )
}
