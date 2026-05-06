import type { AxiosHeaders } from 'axios'
import client from './client'
import shareClient from './shareClient'

export interface SlideOcrRegion {
  x: number
  y: number
  w: number
  h: number
  text: string
}

export interface SlideImageLayoutOcrResponse {
  width: number
  height: number
  regions: SlideOcrRegion[]
}

const OCR_TIMEOUT_MS = 120000

const multipartOcrConfig = {
  timeout: OCR_TIMEOUT_MS,
  transformRequest: [
    (data: unknown, headers: unknown) => {
      const h = headers as AxiosHeaders
      h.delete('Content-Type')
      return data
    },
  ],
}

function blobToFilename(blob: Blob): string {
  if (blob.type === 'image/jpeg') {
    return 'slide.jpg'
  }
  if (blob.type === 'image/webp') {
    return 'slide.webp'
  }
  return 'slide.png'
}

/**
 * POST slide image for layout OCR (auth or share).
 */
export async function postSlideImageLayoutOcr(
  blob: Blob,
  shareToken?: string | null,
): Promise<SlideImageLayoutOcrResponse> {
  const form = new FormData()
  form.append('file', blob, blobToFilename(blob))
  if (shareToken) {
    const path = `/share/${encodeURIComponent(shareToken)}/ocr/slide-image-layout`
    const res = await shareClient.post<SlideImageLayoutOcrResponse>(
      path,
      form,
      multipartOcrConfig,
    )
    return res.data
  }
  const res = await client.post<SlideImageLayoutOcrResponse>(
    '/ocr/slide-image-layout',
    form,
    multipartOcrConfig,
  )
  return res.data
}
