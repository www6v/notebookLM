import * as pdfjsLib from 'pdfjs-dist'
import PdfJsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?worker'

// Use bundled worker instance to avoid runtime fetching `*.mjs` from static host.
// This prevents container/static-server MIME or content-encoding mismatches.
pdfjsLib.GlobalWorkerOptions.workerPort = new PdfJsWorker()

/**
 * Open a PDF document from bytes (browser-side).
 */
export async function openPdfFromBuffer(
  data: ArrayBuffer
): Promise<pdfjsLib.PDFDocumentProxy> {
  const loadingTask = pdfjsLib.getDocument({
    data,
    useSystemFonts: true,
  })
  return loadingTask.promise
}

/**
 * Rasterize one PDF page to a PNG data URL for preview thumbnails or main view.
 */
export async function renderPdfPageToPngDataUrl(
  pdf: pdfjsLib.PDFDocumentProxy,
  pageNumber: number,
  scale: number
): Promise<string> {
  const page = await pdf.getPage(pageNumber)
  const viewport = page.getViewport({ scale })
  const canvas = document.createElement('canvas')
  const context = canvas.getContext('2d')
  if (!context) {
    throw new Error('Canvas 2D context unavailable')
  }
  canvas.height = viewport.height
  canvas.width = viewport.width
  const renderTask = page.render({
    canvasContext: context,
    viewport,
  })
  await renderTask.promise
  return canvas.toDataURL('image/png')
}
