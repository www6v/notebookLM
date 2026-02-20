"""Slide deck generation service.

Generates PPT content from notebook sources via qwen3-max, renders each slide
to an image via Qwen-Image API, then combines images into a single PDF for
frontend display.
"""

import base64
import json
import logging
import time
import uuid
from io import BytesIO

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import chat_completion
# from app.api.sources import _extract_text
from app.services.source_service import extract_text

from app.commons.util import get_image_source_content
from app.config import settings
from app.models.source import Source
from app.models.studio import SlideDeck
from app.services.obs_storage import (
    download_file_from_obs,
    upload_file_to_obs,
)

logger = logging.getLogger(__name__)

# Ensure the logger has a handler for console output
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


async def _query_notebook_sources(
    db: AsyncSession,
    notebook_id: str,
    source_ids: list[str] | None,
) -> list[Source]:
    """Query active sources for a notebook, optionally filtered by source_ids."""
    stmt = select(Source).where(
        Source.notebook_id == notebook_id,
        Source.is_active.is_(True),
    )
    if source_ids:
        stmt = stmt.where(Source.id.in_(source_ids))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _fetch_raw_content_for_source(source: Source) -> str | None:
    """Get raw text for a single source: use cached raw_content or download and extract."""
    if source.raw_content:
        return source.raw_content
    if not source.file_path:
        return None
    if source.type == "image":
        try:
            return await get_image_source_content(source)
        except Exception as exc:
            logger.warning(
                "Failed to get image content for source %s: %s",
                source.title,
                exc,
            )
            return None
    try:
        file_bytes = download_file_from_obs(source.file_path)
        return extract_text(file_bytes, source.type)
    except RuntimeError as exc:
        logger.warning(
            "Failed to download source %s: %s",
            source.title,
            exc,
        )
        return None


def _format_source_part(title: str, content: str, max_length: int = 3000) -> str:
    """Format one source as a combined-content part: '[title]: content[:max_length]'."""
    return f"[{title}]: {content[:max_length]}"


async def _get_combined_content_from_sources(
    db: AsyncSession,
    notebook_id: str,
    source_ids: list[str] | None,
) -> str:
    """Fetch and combine document content from notebook sources (OBS + extract)."""
    sources = await _query_notebook_sources(db, notebook_id, source_ids)
    combined_parts = []

    for source in sources:
        try:
            raw_content = await _fetch_raw_content_for_source(source)
            if raw_content:
                combined_parts.append(
                    _format_source_part(source.title, raw_content)
                )
            else:
                logger.warning(
                    "No content for source %s, skipping",
                    source.title,
                )
        except Exception:
            logger.exception("Error getting content for %s", source.title)
            fallback = (source.raw_content or "")[:3000]
            if fallback:
                combined_parts.append(
                    _format_source_part(source.title, fallback)
                )

    return "\n\n".join(combined_parts)


async def _render_slide_to_image(slide: dict) -> bytes | None:
    """Call Qwen-Image API to generate one slide as image; return PNG bytes or None.

    Uses synchronous multimodal-generation API: prompt -> image URL -> download.
    Caller may use a placeholder when None is returned.
    """
    title = slide.get("title", "Slide")
    content = slide.get("content")
    if isinstance(content, list):
        content_text = "\n".join(str(c) for c in content)
    else:
        content_text = str(content or "")

    prompt = (
        f"Generate a single slide image for a presentation. "
        f"Title: {title}. Content: {content_text}. "
        "Use a clean, professional style and layout, suitable for a slide."
    )
    if len(prompt) > 800:
        prompt = prompt[:797] + "..."

    api_key = settings.qwen_image_api_key or settings.llm_api_key
    url = (
        f"{settings.qwen_image_api_base.rstrip('/')}"
        "/services/aigc/multimodal-generation/generation"
    )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.slide_image_model,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ]
        },
        "parameters": {
            "negative_prompt": (
                "low resolution, low quality, deformed, oversaturated, "
                "blurry text, distorted text."
            ),
            "prompt_extend": True,
            "watermark": False,
            "size": "1664*928",
        },
    }

    try:
        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if data.get("code"):
            elapsed = time.perf_counter() - start
            logger.warning(
                "Qwen-Image API error: %s %s (图像生成耗时: %.2f 秒)",
                data.get("code"),
                data.get("message", ""),
                elapsed,
            )
            return None

        choices = (data.get("output") or {}).get("choices") or []
        if not choices:
            elapsed = time.perf_counter() - start
            logger.warning("Qwen-Image 无 choices (图像生成耗时: %.2f 秒)", elapsed)
            return None
        content_list = (
            choices[0].get("message") or {}
        ).get("content") or []
        if not content_list or "image" not in content_list[0]:
            elapsed = time.perf_counter() - start
            logger.warning("Qwen-Image 无 image 内容 (图像生成耗时: %.2f 秒)", elapsed)
            return None
        image_url = content_list[0]["image"]
        if not image_url:
            elapsed = time.perf_counter() - start
            logger.warning("Qwen-Image 无 image_url (图像生成耗时: %.2f 秒)", elapsed)
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            img_resp = await client.get(image_url)
            img_resp.raise_for_status()
            elapsed = time.perf_counter() - start
            logger.info("图像生成耗时: %.2f 秒 (slide: %s)", elapsed, title)
            return img_resp.content
    except Exception as exc:
        elapsed = time.perf_counter() - start
        logger.warning(
            "Qwen-Image render failed for slide %s: %s (图像生成耗时: %.2f 秒)",
            title,
            exc,
            elapsed,
        )
        return None


def _placeholder_slide_image(slide_number: int, title: str) -> bytes:
    """Create a minimal placeholder PNG for a slide (e.g. when VL returns no image)."""
    minimal_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    try:
        from PIL import Image, ImageDraw, ImageFont

        width, height = 960, 540
        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        font = None
        for path in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSText.ttf",
        ):
            try:
                font = ImageFont.truetype(path, 36)
                break
            except OSError:
                continue
        if font is None:
            font = ImageFont.load_default()
        text = f"Slide {slide_number}: {title[:50]}"
        draw.text((40, height // 2 - 20), text, fill=(0, 0, 0), font=font)

        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        return minimal_png
    except Exception as exc:
        logger.warning("Placeholder image failed: %s", exc)
        return minimal_png


def _build_slide_deck_messages(
    combined_content: str,
    title: str,
    focus_topic: str | None,
) -> list[dict]:
    """Build system prompt and user message for slide deck LLM generation."""
    focus_instruction = ""
    if focus_topic:
        focus_instruction = f"\nFocus specifically on: {focus_topic}"

    system_prompt = f"""Create a slide deck from the provided content. Return ONLY valid JSON.
Content must be coherent across slides. Total number of slides must be 3 or fewer.
Use a default professional style and layout (title slide first, summary last).
{focus_instruction}

Format:
{{
  "slides": [
    {{
      "slide_number": 1,
      "title": "Slide Title",
      "content": ["Bullet point 1", "Bullet point 2"],
      "speaker_notes": "Notes for the presenter",
      "layout": "title"
    }},
    ...
  ]
}}

Layout types: "title", "content", "two_column", "image_text".
"""

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": combined_content or "No source content available.",
        },
    ]


async def _generate_slides_data(
    messages: list[dict],
    fallback_title: str,
) -> dict:
    """Call LLM to generate slides JSON; return slides_data dict with fallback on error."""
    try:
        response = await chat_completion(
            messages,
            model=settings.default_llm_model,
            temperature=0.3,
            max_tokens=4096,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(content)
    except Exception as exc:
        logger.exception("Slide content generation failed: %s", exc)
        return {
            "slides": [
                {
                    "slide_number": 1,
                    "title": fallback_title,
                    "content": ["Content generation failed. Please try again."],
                    "speaker_notes": "",
                    "layout": "title",
                }
            ],
        }


async def _render_slides_to_images(
    slides: list[dict],
    fallback_title: str,
) -> list[bytes]:
    """Render each slide to image bytes; use placeholder when API fails. Never empty."""
    image_bytes_list = []
    for i, slide in enumerate(slides):
        img_bytes = await _render_slide_to_image(slide)
        if img_bytes is None:
            img_bytes = _placeholder_slide_image(
                i + 1,
                slide.get("title", "Slide"),
            )
        image_bytes_list.append(img_bytes)

    if not image_bytes_list:
        image_bytes_list.append(
            _placeholder_slide_image(1, fallback_title or "Slide Deck")
        )
    return image_bytes_list


def _upload_slide_deck_pdf(pdf_bytes: bytes) -> str:
    """Upload PDF bytes to OBS and return object key."""
    unique_id = uuid.uuid4().hex[:12]
    pdf_filename = f"slides/deck_{unique_id}.pdf"
    return upload_file_to_obs(
        file_content=pdf_bytes,
        filename=pdf_filename,
        content_type="application/pdf",
    )


def _images_to_pdf(
    image_bytes_list: list[bytes],
    slide_titles: list[str] | None = None,
) -> bytes:
    """Combine a list of image bytes (PNG/JPEG) into a single PDF (one image per page).

    If any byte blob is not a valid image, a placeholder image is used for that
    slide to avoid UnidentifiedImageError.
    """
    from PIL import Image

    if not image_bytes_list:
        raise ValueError("No images to convert to PDF")

    titles = slide_titles if slide_titles else ["Slide"] * len(image_bytes_list)
    images = []
    for i, b in enumerate(image_bytes_list):
        try:
            img = Image.open(BytesIO(b)).convert("RGB")
            images.append(img)
        except Exception as exc:
            logger.warning(
                "Invalid image at slide %s, using placeholder: %s",
                i + 1,
                exc,
            )
            placeholder_bytes = _placeholder_slide_image(
                i + 1,
                titles[i] if i < len(titles) else "Slide",
            )
            images.append(Image.open(BytesIO(placeholder_bytes)).convert("RGB"))

    buf = BytesIO()
    images[0].save(buf, format="PDF", save_all=True, append_images=images[1:])
    return buf.getvalue()


async def generate_slide_deck(
    db: AsyncSession,
    notebook_id: str,
    title: str = "Slide Deck",
    theme: str = "light",
    source_ids: list[str] | None = None,
    focus_topic: str | None = None,
) -> SlideDeck:
    """Generate a slide deck: document content -> LLM -> slides JSON
    -> per-slide image -> PDF -> OBS. Frontend shows the PDF.
    """
    combined_content = await _get_combined_content_from_sources(
        db, notebook_id, source_ids
    )
    messages = _build_slide_deck_messages(combined_content, title, focus_topic)
    slides_data = await _generate_slides_data(messages, title)

    slides = slides_data.get("slides") or []
    logger.info("slides: %s", slides)

    image_bytes_list = await _render_slides_to_images(slides, title)
    slide_titles = [s.get("title", "Slide") for s in slides]
    pdf_bytes = _images_to_pdf(image_bytes_list, slide_titles=slide_titles)
    object_key = _upload_slide_deck_pdf(pdf_bytes)

    slide_deck = SlideDeck(
        notebook_id=notebook_id,
        title=title,
        theme=theme,
        slides_data=slides_data,
        status="ready",
        file_path=object_key,
    )
    db.add(slide_deck)
    await db.flush()
    await db.refresh(slide_deck)
    return slide_deck
