"""LLM Router: unified interface calling the custom LLM API via httpx."""

import logging
from dataclasses import dataclass, field

import httpx

from app.config import settings

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
