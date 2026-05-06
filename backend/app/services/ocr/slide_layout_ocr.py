"""Layout OCR for slide preview images using RapidOCR (PP-OCR, ONNX)."""

from __future__ import annotations

import io
import logging
import threading
from typing import Any

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, UnidentifiedImageError

logger = logging.getLogger(__name__)

# Slides are often exported below ideal size for CJK; upscaling helps detection/Rec.
_MIN_LONGEST_EDGE_FOR_OCR = 1680
_MAX_LONGEST_EDGE_FOR_OCR = 2800
_MIN_REGION_AREA = 120
_MIN_REGION_SIDE = 8
_MIN_LINE_SCORE = 0.22

_engine_lock = threading.Lock()
_engine: Any | None = None


class SlideLayoutOcrError(Exception):
    """Raised when OCR cannot complete."""


def _get_rapid_ocr_engine() -> Any:
    """Lazy singleton; thread-safe init."""
    global _engine
    if _engine is not None:
        return _engine
    with _engine_lock:
        if _engine is not None:
            return _engine
        try:
            from rapidocr import RapidOCR
        except ImportError as exc:
            raise SlideLayoutOcrError(
                'RapidOCR is not installed. Install: pip install rapidocr onnxruntime'
            ) from exc
        try:
            _engine = RapidOCR()
        except Exception as exc:
            logger.exception('RapidOCR init failed')
            raise SlideLayoutOcrError(
                'Failed to initialize RapidOCR. Install onnxruntime (CPU): '
                'pip install onnxruntime'
            ) from exc
        return _engine


def _enhance_slide_for_ocr(rgb: Image.Image) -> Image.Image:
    """Mild contrast/sharpen for antialiased slide text."""
    work = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=3))
    work = ImageEnhance.Contrast(work).enhance(1.18)
    work = ImageEnhance.Sharpness(work).enhance(1.1)
    return work


def _resize_to_ocr_window(rgb: Image.Image) -> tuple[Image.Image, float]:
    """
    Scale image so longest edge is in [MIN, MAX].

    Returns (work_image, scale_from_work_pixels_to_original_pixels).
    """
    ow, oh = rgb.size
    if ow < 1 or oh < 1:
        return rgb, 1.0
    w, h = ow, oh
    img = rgb
    longest = max(w, h)
    if longest < _MIN_LONGEST_EDGE_FOR_OCR:
        scale_up = _MIN_LONGEST_EDGE_FOR_OCR / longest
        w = max(1, int(round(ow * scale_up)))
        h = max(1, int(round(oh * scale_up)))
        img = img.resize((w, h), Image.Resampling.LANCZOS)
        longest = max(w, h)
    if longest > _MAX_LONGEST_EDGE_FOR_OCR:
        scale_dn = _MAX_LONGEST_EDGE_FOR_OCR / longest
        w = max(1, int(round(w * scale_dn)))
        h = max(1, int(round(h * scale_dn)))
        img = img.resize((w, h), Image.Resampling.LANCZOS)
    scale_back = ow / img.size[0]
    return img, scale_back


def _regions_from_rapid_output(
    result: Any,
    scale_back: float,
) -> list[dict[str, Any]]:
    """Map RapidOCROutput line boxes to axis-aligned regions in original pixels."""
    boxes = getattr(result, 'boxes', None)
    txts = getattr(result, 'txts', None) or ()
    scores = getattr(result, 'scores', None) or ()

    if boxes is None:
        return []

    arr = np.asarray(boxes, dtype=np.float64)
    if arr.size == 0:
        return []
    if arr.ndim == 2 and arr.shape == (4, 2):
        arr = arr[np.newaxis, ...]
    if arr.ndim != 3 or arr.shape[-2:] != (4, 2):
        logger.warning('Unexpected RapidOCR boxes shape: %s', arr.shape)
        return []

    raw: list[tuple[int, int, int, int, str, float]] = []
    n = len(arr)
    for i in range(n):
        box = arr[i]
        if box.shape != (4, 2):
            continue
        text = (txts[i] if i < len(txts) else '').strip()
        if not text:
            continue
        score = float(scores[i]) if i < len(scores) else 1.0
        if score < _MIN_LINE_SCORE:
            continue
        xs = box[:, 0]
        ys = box[:, 1]
        min_x = float(np.min(xs))
        min_y = float(np.min(ys))
        max_x = float(np.max(xs))
        max_y = float(np.max(ys))
        x = int(round(min_x * scale_back))
        y = int(round(min_y * scale_back))
        rw = max(1, int(round((max_x - min_x) * scale_back)))
        rh = max(1, int(round((max_y - min_y) * scale_back)))
        if rw < _MIN_REGION_SIDE or rh < _MIN_REGION_SIDE:
            continue
        if rw * rh < _MIN_REGION_AREA:
            continue
        raw.append((x, y, rw, rh, text, score))

    raw.sort(key=lambda row: (row[1], row[0]))
    return [
        {'x': x, 'y': y, 'w': rw, 'h': rh, 'text': text}
        for x, y, rw, rh, text, _score in raw
    ]


def run_slide_layout_ocr(image_bytes: bytes) -> dict[str, Any]:
    """Run OCR; return width, height, regions in original pixel space."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except UnidentifiedImageError as exc:
        raise SlideLayoutOcrError('Unrecognized image format') from exc

    rgb = image.convert('RGB')
    orig_w, orig_h = rgb.size
    sized, scale_back = _resize_to_ocr_window(rgb)
    work = _enhance_slide_for_ocr(sized)
    img_np = np.array(work, dtype=np.uint8)

    engine = _get_rapid_ocr_engine()
    try:
        result = engine(img_np, use_det=True, use_cls=True, use_rec=True)
    except Exception as exc:
        logger.exception('RapidOCR inference failed')
        raise SlideLayoutOcrError('OCR processing failed') from exc

    if result is None:
        return {'width': orig_w, 'height': orig_h, 'regions': []}

    regions = _regions_from_rapid_output(result, scale_back)
    return {
        'width': orig_w,
        'height': orig_h,
        'regions': regions,
    }
