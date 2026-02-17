"""Slide deck generation service.

Generates PPT content from notebook sources via qwen3-max, renders each slide
to an image via qwen3-vl-max, then combines images into a single PDF for
frontend display.
"""

import asyncio
import base64
import json
import logging
import re
import uuid
from io import BytesIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import chat_completion
from app.api.sources import _extract_text
from app.config import settings
from app.models.source import Source
from app.models.studio import SlideDeck
from app.services.obs_storage import (
    download_file_from_obs,
    upload_file_to_obs,
)

logger = logging.getLogger(__name__)


def _decode_base64_image(data: str) -> bytes | None:
    """Decode base64 image string, fixing common padding/length issues from VL output.

    Base64 length must be a multiple of 4. Strip whitespace, then pad or truncate
    as needed so b64decode does not raise.
    """
    if not data:
        return None
    s = re.sub(r"\s+", "", data)
    if not s:
        return None
    n = len(s)
    remainder = n % 4
    if remainder == 1:
        s = s[: n - 1]
    elif remainder == 2:
        s = s + "=="
    elif remainder == 3:
        s = s + "="
    try:
        return base64.b64decode(s)
    except Exception:
        return None


async def _get_combined_content_from_sources(
    db: AsyncSession,
    notebook_id: str,
    source_ids: list[str] | None,
) -> str:
    """Fetch and combine document content from notebook sources (OBS + extract)."""
    stmt = select(Source).where(
        Source.notebook_id == notebook_id,
        Source.is_active.is_(True),
    )
    if source_ids:
        stmt = stmt.where(Source.id.in_(source_ids))

    result = await db.execute(stmt)
    sources = result.scalars().all()

    combined_parts = []
    for source in sources:
        try:
            raw_content = source.raw_content
            if raw_content is None and source.file_path:
                try:
                    file_bytes = download_file_from_obs(source.file_path)
                    raw_content = _extract_text(file_bytes, source.type)
                except RuntimeError as exc:
                    logger.warning(
                        "Failed to download source %s: %s",
                        source.title,
                        exc,
                    )
                    continue

            if raw_content:
                combined_parts.append(
                    f"[{source.title}]: {raw_content[:3000]}"
                )
            else:
                logger.warning(
                    "No content for source %s, skipping",
                    source.title,
                )
        except Exception as exc:
            logger.exception("Error getting content for %s", source.title)
            fallback = (source.raw_content or "")[:3000]
            if fallback:
                combined_parts.append(f"[{source.title}]: {fallback}")

    return "\n\n".join(combined_parts)


async def _render_slide_to_image(slide: dict) -> bytes | None:
    """Ask VL model to render one slide as image; return PNG bytes or None.

    If the API returns base64 image data, decode and return. Otherwise
    return None (caller may use a placeholder).
    """
    title = slide.get("title", "Slide")
    content = slide.get("content")
    if isinstance(content, list):
        content_text = "\n".join(str(c) for c in content)
    else:
        content_text = str(content or "")

    prompt = (
        f"Generate a single slide image for a presentation. "
        f"Title: {title}\nContent: {content_text}\n"
        "Use a clean, professional default style and layout. "
        "Output only the slide as an image (e.g. base64 PNG)."
    )
    messages = [
        {"role": "system", "content": "You are a slide designer. Output the slide as an image (base64-encoded PNG when possible)."},
        {"role": "user", "content": prompt},
    ]

    try:
        response = await chat_completion(
            messages,
            model=settings.slide_image_model,
            temperature=0.3,
            max_tokens=4096,
        )
        text = (response.choices[0].message.content or "").strip()

        # Try to extract base64 image from response
        match = re.search(
            r"data:image/[^;]+;base64,([A-Za-z0-9+/=\s]+)",
            text,
        )
        if match:
            decoded = _decode_base64_image(match.group(1))
            if decoded is not None:
                return decoded

        # Plain base64 block
        match = re.search(r"([A-Za-z0-9+/=]{100,})", text)
        if match:
            decoded = _decode_base64_image(match.group(1))
            if decoded is not None:
                return decoded

        return None
    except Exception as exc:
        logger.warning("VL render failed for slide %s: %s", title, exc)
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
    """Generate a slide deck: document content -> qwen3-max -> slides JSON
    -> qwen3-vl-max per slide image -> PDF -> OBS. Frontend shows the PDF.
    """
    combined_content = await _get_combined_content_from_sources(
        db, notebook_id, source_ids
    )

    focus_instruction = ""
    if focus_topic:
        focus_instruction = f"\nFocus specifically on: {focus_topic}"

    system_prompt = f"""Create a slide deck from the provided content. Return ONLY valid JSON.
Content must be coherent across slides. Total number of slides must be 15 or fewer.
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

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": combined_content or "No source content available.",
        },
    ]

    try:
        response = await chat_completion(
            messages,
            model=settings.slide_content_model,
            temperature=0.3,
            max_tokens=4096,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        slides_data = json.loads(content)
    except Exception as exc:
        logger.exception("Slide content generation failed: %s", exc)
        slides_data = {
            "slides": [
                {
                    "slide_number": 1,
                    "title": title,
                    "content": ["Content generation failed. Please try again."],
                    "speaker_notes": "",
                    "layout": "title",
                }
            ],
        }

    slides = slides_data.get("slides") or []
    logger.info("slides: %s", slides)

    image_bytes_list = []
    render_tasks = [_render_slide_to_image(slide) for slide in slides]
    render_results = await asyncio.gather(*render_tasks)
    for i, img_bytes in enumerate(render_results):
        if img_bytes is None:
            img_bytes = _placeholder_slide_image(
                i + 1,
                slides[i].get("title", "Slide"),
            )
        image_bytes_list.append(img_bytes)

    if not image_bytes_list:
        image_bytes_list.append(
            _placeholder_slide_image(1, title or "Slide Deck")
        )

    slide_titles = [s.get("title", "Slide") for s in slides]
    pdf_bytes = _images_to_pdf(image_bytes_list, slide_titles=slide_titles)

    unique_id = uuid.uuid4().hex[:12]
    pdf_filename = f"slides/deck_{unique_id}.pdf"
    object_key = upload_file_to_obs(
        file_content=pdf_bytes,
        filename=pdf_filename,
        content_type="application/pdf",
    )

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
