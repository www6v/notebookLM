"""LLM Router: unified interface calling the custom LLM API via httpx."""

import asyncio
import base64
import logging
from dataclasses import dataclass, field

import httpx

from app.config import settings

# Qwen3-VL vision uses dashscope MultiModalConversation (sync API)
try:
    import dashscope
    from dashscope import MultiModalConversation
    HAS_DASHSCOPE = True
except ImportError:
    HAS_DASHSCOPE = False

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response wrapper classes — keep the same interface as before:
#   response.choices[0].message.content
# ---------------------------------------------------------------------------

@dataclass
class _Message:
    content: str
    role: str = "assistant"


@dataclass
class _Choice:
    message: _Message
    index: int = 0
    finish_reason: str = "stop"


@dataclass
class _ChatResponse:
    choices: list[_Choice] = field(default_factory=list)


def _parse_response(data: dict) -> _ChatResponse:
    """Parse the JSON response into a _ChatResponse wrapper."""
    choices = []
    for item in data.get("choices", []):
        msg = item.get("message", {})
        choices.append(
            _Choice(
                message=_Message(
                    content=msg.get("content", ""),
                    role=msg.get("role", "assistant"),
                ),
                index=item.get("index", 0),
                finish_reason=item.get("finish_reason", "stop"),
            )
        )
    return _ChatResponse(choices=choices)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    stream: bool = False,
):
    """Send a chat completion request to the custom LLM API.

    The response object exposes ``response.choices[0].message.content``
    so callers don't need to change.
    """
    model = model or settings.default_llm_model
    url = f"{settings.llm_api_base}/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
        "enable_thinking": False,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    logger.debug("LLM response status=%s model=%s", resp.status_code, model)
    return _parse_response(data)


def _call_qwen3_vl_sync(
    model: str,
    data_url: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    # mock image_url
    data_url = "/Users/t-wangwei07/Downloads/myspace/www6vVisionHugo/content/docs/视觉理解/Connector/Connector/images/hr3jtz6a.bmp"

    """Synchronous call to dashscope MultiModalConversation (qwen3-vl)."""
    dashscope.api_key = settings.qwen_image_api_key
    dashscope.base_http_api_url = (
        settings.qwen_image_api_base.rstrip("/")
    )
    response = MultiModalConversation.call(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    # {"image": data_url},
                    {'image': f'file://{data_url}'},                    
                    {"text": prompt},
                ],
            },
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if not response or not response.output or not response.output.choices:
        msg = getattr(response, "message", None) or "empty response"
        raise RuntimeError(f"Qwen3-VL call failed: {msg}")
    content = response.output.choices[0].message.content
    if isinstance(content, list) and content and "text" in content[0]:
        return (content[0]["text"] or "").strip()
    if isinstance(content, str):
        return content.strip()
    return ""


async def vision_chat_completion_with_url(
    image_url: str,
    prompt: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str:
    """Send image URL + text to vision model (e.g. qwen3-vl), return assistant text.

    Messages format follows qwen3-vl-demo: content is a list of
    [{"image": "<url>"}, {"text": "<prompt>"}]. Used for image-to-text
    (e.g. mind map generation) when the image is available via URL (e.g. OBS presigned).
    """
    model = model or settings.vision_llm_model
    logger.info(
        "vision_chat_completion_with_url: model=%s prompt_len=%d temperature=%s "
        "max_tokens=%d",
        model,
        len(prompt),
        temperature,
        max_tokens,
    )

    if HAS_DASHSCOPE:
        result = await asyncio.to_thread(
            _call_qwen3_vl_sync,
            model,
            image_url,
            prompt,
            temperature,
            max_tokens,
        )
        logger.info("Vision LLM response model=%s", model)
        return result

    # # Fallback: OpenAI-compatible HTTP API
    # api_url = f"{settings.qwen_vision_api_base}/chat/completions"
    # messages = [
    #     {
    #         "role": "user",
    #         "content": [
    #             {"image": image_url},  # 图片URL
    #             {"text": prompt}                
    #         ],
    #     },
    # ]
    # headers = {
    #     "Authorization": f"Bearer {settings.qwen_image_api_key}",
    #     "Content-Type": "application/json",
    # }
    # payload = {
    #     "model": model,
    #     "messages": messages,
    #     "temperature": temperature,
    #     "max_tokens": max_tokens,
    #     "stream": False,
    #     "enable_thinking": False,
    # }
    # async with httpx.AsyncClient(timeout=120.0) as client:
    #     resp = await client.post(api_url, headers=headers, json=payload)
    #     if not resp.is_success:
    #         logger.error(
    #             "Vision API error status=%s body=%s",
    #             resp.status_code,
    #             resp.text[:500] if resp.text else "",
    #         )
    #     resp.raise_for_status()
    #     data = resp.json()
    # logger.info(
    #     "Vision LLM response status=%s model=%s", resp.status_code, model
    # )
    # parsed = _parse_response(data)
    # return (parsed.choices[0].message.content or "").strip()


# async def vision_chat_completion(
#     image_bytes: bytes,
#     image_media_type: str,
#     prompt: str,
#     model: str | None = None,
#     temperature: float = 0.3,
#     max_tokens: int = 2048,
# ) -> str:
#     """Send image + text to vision model (e.g. qwen3-vl), return assistant text.

#     Uses dashscope MultiModalConversation (same as qwen3-vl-demo). Used for
#     image-to-text so the result can be fed into downstream tasks
#     (e.g. mind map generation).
#     """
#     model = model or settings.vision_llm_model
#     logger.info(
#         "vision_chat_completion: model=%s image_size=%d image_media_type=%s "
#         "prompt_len=%d temperature=%s max_tokens=%d",
#         model,
#         len(image_bytes),
#         image_media_type,
#         len(prompt),
#         temperature,
#         max_tokens,
#     )

#     if HAS_DASHSCOPE:
#         b64 = base64.b64encode(image_bytes).decode("utf-8")
#         data_url = f"data:{image_media_type};base64,{b64}"
#         result = await asyncio.to_thread(
#             _call_qwen3_vl_sync,
#             model,
#             data_url,
#             prompt,
#             temperature,
#             max_tokens,
#         )
#         logger.info("Vision LLM response model=%s", model)
#         return result

#     # Fallback: OpenAI-compatible HTTP API (e.g. compatible-mode)
#     url = f"{settings.qwen_vision_api_base}/chat/completions"
#     b64 = base64.b64encode(image_bytes).decode("utf-8")
#     data_url = f"data:{image_media_type};base64,{b64}"
#     messages = [
#         {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": prompt},
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": data_url},
#                 },
#             ],
#         },
#     ]
#     headers = {
#         "Authorization": f"Bearer {settings.qwen_image_api_key}",
#         "Content-Type": "application/json",
#     }
#     payload = {
#         "model": model,
#         "messages": messages,
#         "temperature": temperature,
#         "max_tokens": max_tokens,
#         "stream": False,
#         "enable_thinking": False,
#     }
#     async with httpx.AsyncClient(timeout=120.0) as client:
#         resp = await client.post(url, headers=headers, json=payload)
#         if not resp.is_success:
#             logger.error(
#                 "Vision API error status=%s body=%s",
#                 resp.status_code,
#                 resp.text[:500] if resp.text else "",
#             )
#         resp.raise_for_status()
#         data = resp.json()
#     logger.info("Vision LLM response status=%s model=%s", resp.status_code, model)
#     parsed = _parse_response(data)
#     return (parsed.choices[0].message.content or "").strip()


async def get_embedding(text: str, model: str | None = None) -> list[float]:
    """Get text embedding using the configured embedding model."""
    model = model or settings.embedding_model
    url = f"{settings.llm_api_base}/embeddings"

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "input": [text],
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    return data["data"][0]["embedding"]
