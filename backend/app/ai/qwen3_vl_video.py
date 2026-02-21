"""Video understanding via DashScope qwen3-vl (MultiModalConversation)."""

import asyncio
import logging
import os

import dashscope

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_VIDEO_PROMPT = (
    "请详细描述这段视频的内容，包括主要场景、人物、事件和关键信息，请输出纯文本。"
)
DEFAULT_FPS = 2
MODEL = settings.vision_llm_model


def _call_video_understanding_sync(
    video_url: str,
    prompt: str = DEFAULT_VIDEO_PROMPT,
    fps: int = DEFAULT_FPS,
) -> str:
    """Synchronous call to DashScope MultiModalConversation for video.

    Args:
        video_url: Accessible URL of the video (e.g. presigned OBS URL).
        prompt: Text prompt for the model.
        fps: Frames per second for sampling (default 2).

    Returns:
        Text description from the model.

    Raises:
        ValueError: When API key is missing or response has no text.
        RuntimeError: When API call fails.
    """
    dashscope.api_key = settings.qwen_image_api_key
    dashscope.base_http_api_url = (
        settings.qwen_image_api_base.rstrip("/")
    )
    
    # for local test
    local_path = "/Users/t-wangwei07/Downloads/workspacePy/mycode/notebookLM-video/dog-cat.mp4"
    video_path = f"file://{local_path}"

    messages = [
        {
            "role": "user",
            "content": [
                # {"video": video_url, "fps": fps},
                {'video': video_path, 'fps': 2, 'max_frames': 2000},                
                {"text": prompt},
            ],
        }
    ]
    response = dashscope.MultiModalConversation.call(
        model=MODEL,
        messages=messages,
    )
    if not response or not response.output:
        raise RuntimeError("DashScope video API returned no output")
    choices = getattr(response.output, "choices", None) or []
    if not choices:
        raise RuntimeError("DashScope video API returned no choices")
    message = choices[0].message
    content = getattr(message, "content", None) or []
    if not content:
        raise RuntimeError("DashScope video API returned empty content")
    first = content[0]
    if isinstance(first, dict) and "text" in first:
        return first["text"].strip()
    if isinstance(first, str):
        return first.strip()
    raise RuntimeError("DashScope video API content format unexpected")


async def understand_video(
    video_url: str,
    prompt: str = DEFAULT_VIDEO_PROMPT,
    fps: int = DEFAULT_FPS,
) -> str:
    """Get text description of a video via qwen3-vl (async wrapper).

    Uses asyncio.to_thread to avoid blocking the event loop.
    """
    return await asyncio.to_thread(
        _call_video_understanding_sync,
        video_url,
        prompt,
        fps,
    )
