"""OCR endpoints for slide preview images."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.ocr_layout import SlideImageLayoutOcrResponse, SlideOcrRegion
from app.services.ocr.slide_layout_ocr import SlideLayoutOcrError, run_slide_layout_ocr

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/ocr', tags=['ocr'])

_MAX_UPLOAD_BYTES = 12 * 1024 * 1024

_ALLOWED_TYPES = frozenset(
    {
        'image/png',
        'image/jpeg',
        'image/webp',
    }
)


async def read_upload_image_bytes(upload: UploadFile) -> bytes:
    """Validate upload and return raw bytes. Raises HTTPException."""
    if upload.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Only PNG, JPEG, and WebP images are supported',
        )
    data = await upload.read()
    if len(data) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail='Image too large',
        )
    if len(data) < 32:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Image payload is empty',
        )
    return data


async def build_slide_layout_ocr_response(
    upload: UploadFile,
) -> SlideImageLayoutOcrResponse:
    """Shared handler for authenticated and share OCR routes."""
    payload = await read_upload_image_bytes(upload)
    try:
        raw = run_slide_layout_ocr(payload)
    except SlideLayoutOcrError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    regions = [SlideOcrRegion.model_validate(r) for r in raw['regions']]
    return SlideImageLayoutOcrResponse(
        width=raw['width'],
        height=raw['height'],
        regions=regions,
    )


@router.post(
    '/slide-image-layout',
    response_model=SlideImageLayoutOcrResponse,
)
async def ocr_slide_image_layout(
    file: UploadFile = File(...),
    _user: User = Depends(get_current_user),
):
    """Run OCR on a slide raster; return paragraph-level regions."""
    return await build_slide_layout_ocr_response(file)
