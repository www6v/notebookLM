import { shareReadApi } from '@/api/shareRead'
import { studioApi } from '@/api/studio'
import { sanitizeFileName, triggerBlobDownload } from '@/utils/exportZip'

export type SlidePdfMode = { shareToken?: string | null }

const OBJECT_URL_REVOKE_DELAY_MS = 120000

function normalizePdfFilename(filename?: string | null): string {
  let normalized = sanitizeFileName(filename || 'slides', 'slides')
  const lower = normalized.toLowerCase()

  if (lower.endsWith('.pptx')) {
    normalized = normalized.slice(0, -5)
  }

  if (!normalized.toLowerCase().endsWith('.pdf')) {
    normalized = `${normalized}.pdf`
  }

  return normalized
}

function triggerUrlDownload(url: string, filename: string) {
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.rel = 'noopener noreferrer'
  anchor.click()
}

function scheduleObjectUrlRevoke(objectUrl: string) {
  window.setTimeout(() => {
    URL.revokeObjectURL(objectUrl)
  }, OBJECT_URL_REVOKE_DELAY_MS)
}

function openObjectUrlInTab(objectUrl: string, popup: Window | null) {
  if (popup && !popup.closed) {
    popup.location.href = objectUrl
    scheduleObjectUrlRevoke(objectUrl)
    return
  }

  const opened = window.open(objectUrl, '_blank', 'noopener,noreferrer')
  if (!opened) {
    URL.revokeObjectURL(objectUrl)
    throw new Error('Unable to open PDF preview')
  }

  scheduleObjectUrlRevoke(objectUrl)
}

async function getDirectPdfUrl(
  slideId: string,
  filename: string,
  download: boolean,
  mode?: SlidePdfMode,
): Promise<string> {
  const tok = mode?.shareToken
  const response = tok
    ? await shareReadApi.getSlidePdfUrl(tok, slideId, {
      download,
      filename,
    })
    : await studioApi.getSlidePdfUrl(slideId, {
      download,
      filename,
    })
  if (!response.url) {
    throw new Error('Missing PDF URL')
  }
  return response.url
}

export async function downloadSlidePdfWithFallback(
  slideId: string,
  filename?: string | null,
  mode?: SlidePdfMode,
) {
  const normalizedFilename = normalizePdfFilename(filename)

  try {
    const directUrl = await getDirectPdfUrl(
      slideId,
      normalizedFilename,
      true,
      mode,
    )
    triggerUrlDownload(directUrl, normalizedFilename)
    return
  } catch {
    const tok = mode?.shareToken
    const buffer = tok
      ? await shareReadApi.getSlidePdfArrayBuffer(tok, slideId)
      : await studioApi.getSlidePdfArrayBuffer(slideId)
    triggerBlobDownload(
      new Blob([buffer], { type: 'application/pdf' }),
      normalizedFilename
    )
  }
}

export async function openSlidePdfWithFallback(
  slideId: string,
  filename?: string | null,
  mode?: SlidePdfMode,
) {
  const normalizedFilename = normalizePdfFilename(filename)
  const popup = window.open('', '_blank', 'noopener,noreferrer')

  try {
    const directUrl = await getDirectPdfUrl(
      slideId,
      normalizedFilename,
      false,
      mode,
    )
    if (popup && !popup.closed) {
      popup.location.href = directUrl
      return
    }

    const opened = window.open(directUrl, '_blank', 'noopener,noreferrer')
    if (!opened) {
      throw new Error('Unable to open PDF preview')
    }
    return
  } catch {
    const tok = mode?.shareToken
    const buffer = tok
      ? await shareReadApi.getSlidePdfArrayBuffer(tok, slideId)
      : await studioApi.getSlidePdfArrayBuffer(slideId)
    const objectUrl = URL.createObjectURL(
      new Blob([buffer], { type: 'application/pdf' })
    )
    openObjectUrlInTab(objectUrl, popup)
  }
}
