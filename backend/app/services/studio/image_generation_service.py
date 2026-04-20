"""Shared image generation helpers for studio workflows."""

from __future__ import annotations

import asyncio
import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

IMAGE_RATE_LIMIT_RETRIES = 3
IMAGE_RATE_LIMIT_BACKOFF = (15, 30, 60)
IMAGE_RETRYABLE_EXC = (httpx.ConnectError, httpx.TimeoutException)
DEFAULT_NEGATIVE_PROMPT = (
    "low resolution, low quality, deformed, oversaturated, "
    "blurry text, distorted text."
)
# DashScope qwen-image-max / qwen-image-plus 同步接口支持的 size（见阿里云百炼文档）。
# 误用 1280*1280 等未列出的分辨率会导致 HTTP 400。
ASPECT_RATIO_TO_SIZE = {
    "16:9": "1664*928",
    "9:16": "928*1664",
    "1:1": "1328*1328",
    "4:3": "1472*1104",
    "3:4": "1104*1472",
    "landscape": "1664*928",
    "portrait": "928*1664",
    "square": "1328*1328",
}


def aspect_ratio_to_size(aspect_ratio: str) -> str:
    """Map a workflow aspect ratio to the DashScope image size."""
    return ASPECT_RATIO_TO_SIZE.get((aspect_ratio or "").strip(), "1664*928")


def dashscope_image_model_id(configured: str) -> str:
    """Return the model id for raw DashScope HTTP API (no lite-style prefix)."""
    raw = (configured or "").strip()
    if raw.startswith("dashscope/"):
        return raw[len("dashscope/"):]
    return raw


async def generate_image_from_prompt(
    prompt: str,
    *,
    size: str = "1664*928",
    title: str = "image",
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    prompt_extend: bool = True,
) -> bytes | None:
    """Generate one image with the application's configured image backend."""
    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("Prompt is empty.")
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured.")

    model_id = dashscope_image_model_id(settings.litellm_image_model)
    if not model_id:
        raise RuntimeError("LITELLM_IMAGE_MODEL is not configured.")

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
                    "content": [{"text": prompt}],
                }
            ]
        },
        "parameters": {
            "negative_prompt": negative_prompt,
            "prompt_extend": prompt_extend,
            "watermark": False,
            "size": size,
        },
    }

    start = time.perf_counter()
    data = None
    last_exc = None

    for attempt in range(IMAGE_RATE_LIMIT_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
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
                            "Image generation rate-limited, retrying in %s seconds "
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
                        "DashScope image API HTTP %s (title=%s, model=%s, size=%s): %s",
                        response.status_code,
                        title,
                        model_id,
                        size,
                        preview,
                    )
                    raise RuntimeError(
                        f"DashScope image API HTTP {response.status_code}: {preview}"
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
                    "Image generation rate-limited, retrying in %s seconds "
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
                    "Image generation network error %s, retrying in %s seconds "
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
                "Image generation failed for %s: %s (elapsed %.2f seconds)",
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
                "Image API error: %s %s (elapsed %.2f seconds)",
                data.get("code"),
                data.get("message", ""),
                elapsed,
            )
            return None

        choices = (data.get("output") or {}).get("choices") or []
        if not choices:
            elapsed = time.perf_counter() - start
            logger.warning(
                "Image generation returned no choices (elapsed %.2f seconds)",
                elapsed,
            )
            return None

        content_list = (choices[0].get("message") or {}).get("content") or []
        if not content_list or "image" not in content_list[0]:
            elapsed = time.perf_counter() - start
            logger.warning(
                "Image generation returned no image content (elapsed %.2f seconds)",
                elapsed,
            )
            return None

        image_url = content_list[0]["image"]
        if not image_url:
            elapsed = time.perf_counter() - start
            logger.warning(
                "Image generation returned no image url (elapsed %.2f seconds)",
                elapsed,
            )
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            image_response = await client.get(image_url)
            image_response.raise_for_status()
            elapsed = time.perf_counter() - start
            logger.info(
                "Image generation completed in %.2f seconds (title: %s)",
                elapsed,
                title,
            )
            return image_response.content
    except Exception as exc:
        elapsed = time.perf_counter() - start
        logger.warning(
            "Image generation failed for %s: %s (elapsed %.2f seconds)",
            title,
            exc,
            elapsed,
        )
        return None
