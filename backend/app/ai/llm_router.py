"""LLM Router: unified interface via LiteLLM SDK (chat, vision) and embedding."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from langfuse import observe, propagate_attributes

from app.config import settings

try:
    from litellm import Router, acompletion
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False
    Router = None
    acompletion = None

logger = logging.getLogger(__name__)

_litellm_chat_router: Any = None
_router_misconfig_warned = False
_router_fallback_env_warned = False


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

def _dashscope_compatible_api_base(api_base: str) -> str:
    """DashScope OpenAI-compatible base URL for LiteLLM."""
    return api_base.replace("/api/", "/compatible-mode/").rstrip("/")


def _build_litellm_chat_router_config() -> tuple[
    list[dict[str, Any]],
    list[dict[str, list[str]]],
    dict[str, str],
]:
    """Build Router model_list, fallbacks, and alias (Qwen first, then backups).

    - Public virtual name: ``litellm_router_group_name`` (e.g. notebooklm-chat).
    - Alias maps it to ``{group}-qwen`` (two DashScope deployments, simple-shuffle).
    - On Qwen pool failure, Router ``fallbacks`` uses a ``"*"`` entry so backup
      models run whether the failing ``model_group`` is the public alias or the
      resolved Qwen pool name; backups are ``{group}-gemini`` then ``{group}-openai``
      when those deployments exist.
    """
    group = settings.litellm_router_group_name.strip()
    qwen_group = f"{group}-qwen"
    gemini_group = f"{group}-gemini"
    openai_group = f"{group}-openai"
    qwen_model = settings.litellm_router_qwen_model.strip()
    primary_key = settings.dashscope_api_key.strip()
    secondary_key = settings.dashscope_api_key_secondary.strip()
    secondary_base_raw = (
        settings.dashscope_api_base_secondary.strip()
        or settings.dashscope_api_base
    )
    model_list: list[dict[str, Any]] = []

    if primary_key and qwen_model and group:
        model_list.append(
            {
                "model_name": qwen_group,
                "litellm_params": {
                    "model": qwen_model,
                    "api_key": primary_key,
                    "api_base": _dashscope_compatible_api_base(
                        settings.dashscope_api_base
                    ),
                },
            }
        )
        key_b = secondary_key or primary_key
        base_b = (
            secondary_base_raw
            if secondary_key
            else settings.dashscope_api_base
        )
        model_list.append(
            {
                "model_name": qwen_group,
                "litellm_params": {
                    "model": qwen_model,
                    "api_key": key_b,
                    "api_base": _dashscope_compatible_api_base(base_b),
                },
            }
        )

    gemini_key = settings.gemini_api_key.strip()
    gemini_model = settings.litellm_router_gemini_model.strip()
    if gemini_key and gemini_model and group:
        model_list.append(
            {
                "model_name": gemini_group,
                "litellm_params": {
                    "model": gemini_model,
                    "api_key": gemini_key,
                },
            }
        )

    openai_key = settings.openai_api_key.strip()
    openai_model = settings.litellm_router_openai_model.strip()
    if openai_key and openai_model and group:
        model_list.append(
            {
                "model_name": openai_group,
                "litellm_params": {
                    "model": openai_model,
                    "api_key": openai_key,
                },
            }
        )

    fallback_targets: list[str] = []
    if gemini_key and gemini_model and group:
        fallback_targets.append(gemini_group)
    if openai_key and openai_model and group:
        fallback_targets.append(openai_group)

    # Use LiteLLM generic fallbacks key "*" so backup models run regardless of
    # whether the failing request used the public alias (group) or the
    # resolved pool name (qwen_group) as model_group during error handling.
    fallbacks: list[dict[str, list[str]]] = (
        [{"*": fallback_targets}] if fallback_targets else []
    )
    alias: dict[str, str] = {group: qwen_group} if group else {}

    return model_list, fallbacks, alias


def _get_litellm_chat_router() -> Any:
    """Lazy-init LiteLLM SDK Router (Qwen pool + fallbacks to Gemini/OpenAI)."""
    global _litellm_chat_router, _router_misconfig_warned
    global _router_fallback_env_warned
    if _litellm_chat_router is not None:
        return _litellm_chat_router
    if not HAS_LITELLM or Router is None:
        raise RuntimeError("LiteLLM Router is not available.")
    model_list, fallbacks, model_group_alias = _build_litellm_chat_router_config()
    if not model_list:
        raise RuntimeError(
            "LiteLLM chat router has no deployments. Set DASHSCOPE_API_KEY "
            "and optionally GEMINI_API_KEY / OPENAI_API_KEY."
        )
    if (
        not _router_misconfig_warned
        and settings.litellm_chat_router_enabled
        and settings.litellm_model.strip()
        and settings.litellm_model != settings.litellm_router_group_name
    ):
        _router_misconfig_warned = True
        logger.warning(
            "LITELLM_CHAT_ROUTER_ENABLED is on but LITELLM_MODEL (%s) != "
            "LITELLM_ROUTER_GROUP_NAME (%s). Default chat will skip the "
            "router unless the request passes the group name as model.",
            settings.litellm_model,
            settings.litellm_router_group_name,
        )
    _litellm_chat_router = Router(
        model_list=model_list,
        routing_strategy="simple-shuffle",
        fallbacks=fallbacks,
        model_group_alias=model_group_alias,
    )
    _g = settings.litellm_router_group_name.strip()
    fb_desc = "(none)"
    if fallbacks and fallbacks[0]:
        fb_map = fallbacks[0]
        if _g in fb_map:
            fb_desc = " -> ".join(fb_map[_g])
        elif "*" in fb_map:
            fb_desc = " -> ".join(fb_map["*"])
    logger.info(
        "LiteLLM SDK Router ready: public_group=%s deployments=%d "
        "qwen_pool=simple-shuffle fallbacks=%s",
        settings.litellm_router_group_name,
        len(model_list),
        fb_desc,
    )
    if (
        not fallbacks
        and not _router_fallback_env_warned
        and settings.litellm_chat_router_enabled
    ):
        _router_fallback_env_warned = True
        logger.warning(
            "LiteLLM router cross-provider fallbacks are off (Qwen pool only). "
            "Pass GEMINI_API_KEY or GOOGLE_API_KEY and/or OPENAI_API_KEY into "
            "the worker/container (with LITELLM_ROUTER_GEMINI_MODEL / "
            "LITELLM_ROUTER_OPENAI_MODEL) to enable backup routing after "
            "DashScope failures.",
        )
    return _litellm_chat_router


def _should_route_chat_via_litellm_router(model: str | None) -> bool:
    if not settings.litellm_chat_router_enabled:
        return False
    effective = (model or settings.litellm_model or "").strip()
    group = settings.litellm_router_group_name.strip()
    return bool(group) and effective == group


def _litellm_response_to_chat_response(response) -> _ChatResponse:
    """Convert LiteLLM ModelResponse to _ChatResponse."""
    choices = []
    for i, c in enumerate(getattr(response, "choices", []) or []):
        msg = getattr(c, "message", None)
        if msg is None:
            continue
        content = getattr(msg, "content", None) or ""
        role = getattr(msg, "role", "assistant")
        finish_reason = getattr(c, "finish_reason", "stop") or "stop"
        choices.append(
            _Choice(
                message=_Message(content=content, role=role),
                index=i,
                finish_reason=finish_reason,
            )
        )
    return _ChatResponse(choices=choices)


async def _chat_via_litellm_sdk_router(
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    stream: bool,
) -> _ChatResponse:
    """Chat via LiteLLM SDK Router (Qwen pool first, then configured fallbacks)."""
    router = _get_litellm_chat_router()
    response = await router.acompletion(
        model=settings.litellm_router_group_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream,
    )
    if stream:
        content_parts = []
        async for chunk in response:
            delta = getattr(chunk, "choices", [None])[0]
            if delta and getattr(delta, "delta", None):
                part = getattr(delta.delta, "content", None)
                if part:
                    content_parts.append(part)
        return _ChatResponse(
            choices=[
                _Choice(
                    message=_Message(
                        content="".join(content_parts),
                        role="assistant",
                    ),
                )
            ]
        )
    return _litellm_response_to_chat_response(response)


async def _chat_via_litellm_sdk(
    messages: list[dict],
    model: str,
    temperature: float,
    max_tokens: int,
    stream: bool,
) -> _ChatResponse:
    """Call LiteLLM SDK (acompletion)."""
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    if model.startswith("dashscope/") and settings.dashscope_api_key:
        kwargs["api_key"] = settings.dashscope_api_key
        base = settings.dashscope_api_base.replace("/api/", "/compatible-mode/")
        kwargs["api_base"] = base.rstrip("/")
    response = await acompletion(**kwargs)
    if stream:
        content_parts = []
        async for chunk in response:
            delta = getattr(chunk, "choices", [None])[0]
            if delta and getattr(delta, "delta", None):
                part = getattr(delta.delta, "content", None)
                if part:
                    content_parts.append(part)
        return _ChatResponse(
            choices=[
                _Choice(
                    message=_Message(content="".join(content_parts), role="assistant"),
                )
            ]
        )
    return _litellm_response_to_chat_response(response)


@observe(name="chat_completion", as_type="generation")
async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    stream: bool = False,
    user_id: str | None = None,
    session_id: str | None = None,
):
    """Send a chat completion request via LiteLLM SDK.

    使用 LITELLM_MODEL（如 dashscope/qwen3.5-plus），或启用
    LITELLM_CHAT_ROUTER_ENABLED 且 LITELLM_MODEL 等于
    LITELLM_ROUTER_GROUP_NAME 时走 SDK Router：两路 Qwen 池内
    simple-shuffle，失败后再依次尝试 Gemini、OpenAI（Router fallbacks）。
    返回对象保持 ``response.choices[0].message.content`` 接口不变。
    """
    if not HAS_LITELLM:
        raise RuntimeError(
            "LiteLLM is required. Install litellm and set LITELLM_MODEL."
        )
    if not settings.litellm_chat_router_enabled and not settings.litellm_model:
        raise RuntimeError(
            "LiteLLM is required. Install litellm and set LITELLM_MODEL."
        )
    if settings.litellm_chat_router_enabled and not (
        settings.litellm_model.strip() or model
    ):
        raise RuntimeError(
            "Set LITELLM_MODEL to the router group name "
            "(same as LITELLM_ROUTER_GROUP_NAME) when using the chat router."
        )
    resolved = model or settings.litellm_model
    trace_model = resolved
    if _should_route_chat_via_litellm_router(model):
        trace_model = settings.litellm_router_group_name
        with propagate_attributes(
            user_id=user_id or "",
            session_id=session_id or "",
            metadata={"llm": trace_model},
        ):
            result = await _chat_via_litellm_sdk_router(
                messages, temperature, max_tokens, stream
            )
        logger.debug("LLM response via LiteLLM SDK Router model=%s", trace_model)
        return result
    with propagate_attributes(
        user_id=user_id or "",
        session_id=session_id or "",
        metadata={"llm": resolved},
    ):
        result = await _chat_via_litellm_sdk(
            messages, resolved, temperature, max_tokens, stream
        )
    logger.debug("LLM response via LiteLLM SDK model=%s", resolved)
    return result


@observe(name="tool_chat_completion", as_type="generation")
async def tool_chat_completion(
    messages: list[dict],
    tools: list[dict],
    model: str | None = None,
    temperature: float | None = 0.7,
    max_tokens: int | None = 2048,
    user_id: str | None = None,
    session_id: str | None = None,
):
    """Send a tool-enabled chat completion request via LiteLLM SDK."""
    if not HAS_LITELLM:
        raise RuntimeError(
            "LiteLLM is required. Install litellm and set LITELLM_MODEL."
        )
    if not settings.litellm_chat_router_enabled and not settings.litellm_model:
        raise RuntimeError(
            "LiteLLM is required. Install litellm and set LITELLM_MODEL."
        )
    if settings.litellm_chat_router_enabled and not (
        settings.litellm_model.strip() or model
    ):
        raise RuntimeError(
            "Set LITELLM_MODEL to the router group name "
            "(same as LITELLM_ROUTER_GROUP_NAME) when using the chat router."
        )
    resolved = model or settings.litellm_model
    trace_model = resolved
    kwargs: dict[str, Any] = {
        "model": resolved,
        "messages": messages,
        "tools": tools,
        "stream": False,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    if _should_route_chat_via_litellm_router(model):
        trace_model = settings.litellm_router_group_name
        kwargs["model"] = settings.litellm_router_group_name
        with propagate_attributes(
            user_id=user_id or "",
            session_id=session_id or "",
            metadata={"llm": trace_model},
        ):
            router = _get_litellm_chat_router()
            response = await router.acompletion(**kwargs)
        logger.debug("Tool LLM via LiteLLM SDK Router model=%s", trace_model)
        return response

    if resolved.startswith("dashscope/") and settings.dashscope_api_key:
        kwargs["api_key"] = settings.dashscope_api_key
        base = settings.dashscope_api_base.replace("/api/", "/compatible-mode/")
        kwargs["api_base"] = base.rstrip("/")

    with propagate_attributes(
        user_id=user_id or "",
        session_id=session_id or "",
        metadata={"llm": resolved},
    ):
        response = await acompletion(**kwargs)
    logger.debug("Tool LLM response via LiteLLM SDK model=%s", resolved)
    return response


@observe(name="vision_chat_completion_with_url", as_type="generation")
async def vision_chat_completion_with_url(
    image_url: str,
    prompt: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    user_id: str | None = None,
    session_id: str | None = None,
) -> str:
    """Send image URL + text to vision model via LiteLLM, return assistant text.

    Uses OpenAI-format messages with image_url. Model defaults to
    LITELLM_VISION_MODEL (e.g. dashscope/qwen3-vl-plus).
    """
    if not HAS_LITELLM:
        raise RuntimeError("LiteLLM is required for vision completion.")
    model = model or settings.litellm_vision_model
    with propagate_attributes(
        user_id=user_id or "",
        session_id=session_id or "",
        metadata={"llm": model},
    ):
        logger.info(
            "vision_chat_completion_with_url: model=%s prompt_len=%d temperature=%s "
            "max_tokens=%d",
            model,
            len(prompt),
            temperature,
            max_tokens,
        )
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if model.startswith("dashscope/") and settings.dashscope_api_key:
            kwargs["api_key"] = settings.dashscope_api_key
            base = settings.dashscope_api_base.replace("/api/", "/compatible-mode/")
            kwargs["api_base"] = base.rstrip("/")
        response = await acompletion(**kwargs)
        parsed = _litellm_response_to_chat_response(response)
        out = (parsed.choices[0].message.content or "").strip()
    logger.info("Vision LLM response model=%s", model)
    return out


async def get_embedding(text: str, model: str | None = None) -> list[float]:
    """Get text embedding via DashScope MultiModalEmbedding (see app.ai.embeddings)."""
    from app.ai.embeddings import embed_text
    return await embed_text(text)
