"""Layout OCR for slide preview images: paragraph-level regions and text."""

from __future__ import annotations

import io
import logging
from collections import defaultdict
from typing import Any

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

_MAX_OCR_DIMENSION = 2000
_MIN_REGION_AREA = 120
_MIN_REGION_SIDE = 8


class SlideLayoutOcrError(Exception):
    """Raised when OCR cannot complete."""


def _maybe_resize_for_ocr(image: Image.Image) -> tuple[Image.Image, float]:
    w, h = image.size
    longest = max(w, h)
    if longest <= _MAX_OCR_DIMENSION:
        return image, 1.0
    factor = _MAX_OCR_DIMENSION / longest
    new_w = max(1, int(round(w * factor)))
    new_h = max(1, int(round(h * factor)))
    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return resized, 1.0 / factor


def _regions_from_data(
    data: dict[str, Any],
    scale_back: float,
) -> list[dict[str, Any]]:
    n = len(data.get('text', []))
    groups: dict[tuple[int, int], list[tuple[int, int, int, int, str]]] = (
        defaultdict(list)
    )
    for i in range(n):
        raw_conf = data['conf'][i]
        try:
            conf = int(raw_conf)
        except (TypeError, ValueError):
            continue
        if conf < 0:
            continue
        text = (data['text'][i] or '').strip()
        if not text:
            continue
        try:
            b_num = int(data['block_num'][i])
            p_num = int(data['par_num'][i])
        except (TypeError, ValueError, KeyError):
            continue
        key = (b_num, p_num)
        left = int(data['left'][i])
        top = int(data['top'][i])
        width = int(data['width'][i])
        height = int(data['height'][i])
        right = left + max(width, 1)
        bottom = top + max(height, 1)
        groups[key].append((left, top, right, bottom, text))

    regions: list[dict[str, Any]] = []
    for parts in groups.values():
        min_l = min(p[0] for p in parts)
        min_t = min(p[1] for p in parts)
        max_r = max(p[2] for p in parts)
        max_b = max(p[3] for p in parts)
        texts = [p[4] for p in parts]
        merged = ' '.join(texts).strip()
        if not merged:
            continue
        x = int(round(min_l * scale_back))
        y = int(round(min_t * scale_back))
        rw = int(round((max_r - min_l) * scale_back))
        rh = int(round((max_b - min_t) * scale_back))
        if rw < _MIN_REGION_SIDE or rh < _MIN_REGION_SIDE:
            continue
        if rw * rh < _MIN_REGION_AREA:
            continue
        regions.append(
            {
                'x': x,
                'y': y,
                'w': rw,
                'h': rh,
                'text': merged,
            }
        )
    return regions


def run_slide_layout_ocr(image_bytes: bytes) -> dict[str, Any]:
    """Run OCR; return width, height, regions in original pixel space."""
    import pytesseract

    try:
        image = Image.open(io.BytesIO(image_bytes))
    except UnidentifiedImageError as exc:
        raise SlideLayoutOcrError('Unrecognized image format') from exc

    rgb = image.convert('RGB')
    orig_w, orig_h = rgb.size
    work, scale_back = _maybe_resize_for_ocr(rgb)

    try:
        data = pytesseract.image_to_data(
            work,
            lang='chi_sim+eng',
            output_type=pytesseract.Output.DICT,
        )
    except pytesseract.TesseractNotFoundError as exc:
        logger.exception('Tesseract binary not found')
        raise SlideLayoutOcrError(
            'Tesseract OCR is not installed on the server'
        ) from exc
    except Exception as exc:
        logger.exception('OCR failed')
        raise SlideLayoutOcrError('OCR processing failed') from exc

    regions = _regions_from_data(data, scale_back)
    return {
        'width': orig_w,
        'height': orig_h,
        'regions': regions,
    }
