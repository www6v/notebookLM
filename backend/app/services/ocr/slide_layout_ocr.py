"""Layout OCR for slide preview images: paragraph-level regions and text."""

from __future__ import annotations

import io
import logging
from collections import defaultdict
from typing import Any

from PIL import Image, ImageEnhance, ImageFilter, UnidentifiedImageError

logger = logging.getLogger(__name__)

# Slides are often exported below ideal size for CJK; upscaling improves glyphs.
_MIN_LONGEST_EDGE_FOR_OCR = 1680
# Cap decode cost while keeping enough detail for mixed CN/EN slides.
_MAX_LONGEST_EDGE_FOR_OCR = 2800
_MIN_REGION_AREA = 120
_MIN_REGION_SIDE = 8

# LSTM + auto page layout; 11 (sparse) often mis-merges multi-column slides.
_TESSERACT_CONFIG = '--oem 1 --psm 3'
_TESSERACT_LANG = 'chi_sim+eng'


class SlideLayoutOcrError(Exception):
    """Raised when OCR cannot complete."""


def _contains_cjk(text: str) -> bool:
    return any('\u4e00' <= ch <= '\u9fff' for ch in text)


def _merge_word_strings(parts: list[str]) -> str:
    """Join OCR words: tight CJK runs; spaces between Latin tokens and script edges."""
    cleaned = [p.strip() for p in parts if p.strip()]
    if not cleaned:
        return ''
    if not any(_contains_cjk(p) for p in cleaned):
        return ' '.join(cleaned)
    merged: list[str] = [cleaned[0]]
    for piece in cleaned[1:]:
        prev = merged[-1]
        prev_cjk = _contains_cjk(prev)
        piece_cjk = _contains_cjk(piece)
        gap = ''
        if prev_cjk and piece_cjk:
            gap = ''
        elif prev_cjk ^ piece_cjk:
            gap = ' '
        elif prev[-1:].isalnum() and piece[:1].isalnum():
            gap = ' '
        merged.append(gap)
        merged.append(piece)
    return ''.join(merged)


def _enhance_slide_for_ocr(rgb: Image.Image) -> Image.Image:
    """Mild contrast/sharpen to help antialiased slide text (esp. CJK on gradients)."""
    work = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=3))
    work = ImageEnhance.Contrast(work).enhance(1.22)
    work = ImageEnhance.Sharpness(work).enhance(1.12)
    return work


def _resize_to_ocr_window(rgb: Image.Image) -> tuple[Image.Image, float]:
    """
    Scale image so longest edge is in [MIN, MAX] for Tesseract.

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
        merged = _merge_word_strings(texts).strip()
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
    sized, scale_back = _resize_to_ocr_window(rgb)
    work = _enhance_slide_for_ocr(sized)

    try:
        data = pytesseract.image_to_data(
            work,
            lang=_TESSERACT_LANG,
            config=_TESSERACT_CONFIG,
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
