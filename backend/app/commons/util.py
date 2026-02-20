"""Common utilities shared across the application."""

import logging

from app.ai.llm_router import vision_chat_completion_with_url
from app.models.source import Source
from app.services.obs_storage import generate_presigned_url

logger = logging.getLogger(__name__)

# Max characters per source to include in combined content for LLM.
MAX_CONTENT_PER_SOURCE = 3000


async def get_image_source_content(
    source: Source,
    max_content: int = MAX_CONTENT_PER_SOURCE,
) -> str:
    """Get text content for an image source via vision API.

    Returns description text (truncated to max_content), or
    a fallback message if vision API fails.
    """
    prompt = (
        "请详细描述这张图片的内容，包括主要物体、文字、"
        "布局和关键信息，请输出纯文本。"
    )
    try:
        image_url = generate_presigned_url(
            source.file_path, expiration=3600
        )
        logger.info("image_url: %s", image_url)
        raw_content = await vision_chat_completion_with_url(
            image_url,
            prompt,
            temperature=0.3,
            max_tokens=2048,
        )
        if not raw_content:
            raw_content = "[Image description unavailable]"
    except Exception as vision_err:
        logger.warning(
            "Vision API failed for image '%s': %s",
            source.title,
            vision_err,
        )
        raw_content = "[Image description unavailable]"
    return raw_content[:max_content]
