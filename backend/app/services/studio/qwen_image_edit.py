"""DashScope qwen-image-edit: instruction-based image edits for slide revisions."""

from __future__ import annotations

import asyncio
import base64
import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

IMAGE_RATE_LIMIT_RETRIES = 3
IMAGE_RATE_LIMIT_BACKOFF = (15, 30, 60)
IMAGE_RETRYABLE_EXC = (httpx.ConnectError, httpx.TimeoutException)


def _png_data_uri(png_bytes: bytes) -> str:
    """Build a data URI for DashScope multimodal image input."""
    b64 = base64.standard_b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


async def edit_image_with_instruction(
    image_png: bytes,
    instruction: str,
    *,
    title: str = "slide-edit",
) -> bytes | None:
    """Edit one PNG using configured qwen-image-edit model (DashScope HTTP)."""
    text = (instruction or "").strip()
    if not text:
        raise ValueError("Instruction is empty.")
    if not image_png:
        raise ValueError("Image bytes are empty.")
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured.")

    model_id = (settings.dashscope_slide_image_edit_model or "").strip()
    if not model_id:
        raise RuntimeError("DASHSCOPE_SLIDE_IMAGE_EDIT_MODEL is not configured.")

    url = (
        f"{settings.dashscope_api_base.rstrip('/')}"
        "/services/aigc/multimodal-generation/generation"
    )
    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_id,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"image": _png_data_uri(image_png)},
                        {"text": text},
                    ],
                }
            ]
        },
        "parameters": {
            "watermark": False,
        },
    }

    start = time.perf_counter()
    data = None
    last_exc = None

    for attempt in range(IMAGE_RATE_LIMIT_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 429:
                    last_exc = httpx.HTTPStatusError(
                        "429 Too Many Requests",
                        request=response.request,
                        response=response,
                    )
                    if attempt < IMAGE_RATE_LIMIT_RETRIES - 1:
                        wait = IMAGE_RATE_LIMIT_BACKOFF[attempt]
                        logger.info(
                            "Image edit rate-limited, retrying in %s seconds "
                            "(title: %s, attempt: %s)",
                            wait,
                            title,
                            attempt + 1,
                        )
                        await asyncio.sleep(wait)
                        continue
                    raise last_exc
                if not response.is_success:
                    body = (response.text or "").strip()
                    preview = body[:2000] if body else "(empty response body)"
                    logger.error(
                        "DashScope image edit HTTP %s (title=%s, model=%s): %s",
                        response.status_code,
                        title,
                        model_id,
                        preview,
                    )
                    raise RuntimeError(
                        f"DashScope image edit HTTP {response.status_code}: "
                        f"{preview}"
                    )
                data = response.json()
            break
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            if (
                exc.response.status_code == 429
                and attempt < IMAGE_RATE_LIMIT_RETRIES - 1
            ):
                wait = IMAGE_RATE_LIMIT_BACKOFF[attempt]
                logger.info(
                    "Image edit rate-limited, retrying in %s seconds "
                    "(title: %s, attempt: %s)",
                    wait,
                    title,
                    attempt + 1,
                )
                await asyncio.sleep(wait)
                continue
            raise
        except IMAGE_RETRYABLE_EXC as exc:
            last_exc = exc
            if attempt < IMAGE_RATE_LIMIT_RETRIES - 1:
                wait = IMAGE_RATE_LIMIT_BACKOFF[attempt]
                logger.warning(
                    "Image edit network error %s, retrying in %s seconds "
                    "(title: %s, attempt: %s)",
                    type(exc).__name__,
                    wait,
                    title,
                    attempt + 1,
                )
                await asyncio.sleep(wait)
                continue
            elapsed = time.perf_counter() - start
            logger.warning(
                "Image edit failed for %s: %s (elapsed %.2f seconds)",
                title,
                exc,
                elapsed,
            )
            return None

    if data is None:
        if last_exc is not None:
            raise last_exc
        return None

    try:
        if data.get("code"):
            elapsed = time.perf_counter() - start
            logger.warning(
                "Image edit API error: %s %s (elapsed %.2f seconds)",
                data.get("code"),
                data.get("message", ""),
                elapsed,
            )
            return None

        choices = (data.get("output") or {}).get("choices") or []
        if not choices:
            elapsed = time.perf_counter() - start
            logger.warning(
                "Image edit returned no choices (elapsed %.2f seconds)",
                elapsed,
            )
            return None

        content_list = (choices[0].get("message") or {}).get("content") or []
        if not content_list or "image" not in content_list[0]:
            elapsed = time.perf_counter() - start
            logger.warning(
                "Image edit returned no image content (elapsed %.2f seconds)",
                elapsed,
            )
            return None

        image_url = content_list[0]["image"]
        if not image_url:
            elapsed = time.perf_counter() - start
            logger.warning(
                "Image edit returned no image url (elapsed %.2f seconds)",
                elapsed,
            )
            return None

        async with httpx.AsyncClient(timeout=60.0) as client:
            image_response = await client.get(image_url)
            image_response.raise_for_status()
            elapsed = time.perf_counter() - start
            logger.info(
                "Image edit completed in %.2f seconds (title: %s)",
                elapsed,
                title,
            )
            return image_response.content
    except Exception as exc:
        elapsed = time.perf_counter() - start
        logger.warning(
            "Image edit failed for %s: %s (elapsed %.2f seconds)",
            title,
            exc,
            elapsed,
        )
        return None
