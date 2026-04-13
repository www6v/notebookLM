"""Audio transcription via Qwen ASR.

DashScope short audio uses the compatible-mode HTTP endpoint directly.
Other providers can still use LiteLLM's OpenAI-compatible completion path.
Long audio keeps the DashScope filetrans fallback because LiteLLM does not
cover that async endpoint.
"""

import asyncio
import logging
from dataclasses import dataclass

import httpx
from langfuse import observe, propagate_attributes

try:
    from litellm import acompletion

    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False
    acompletion = None

from app.config import settings

logger = logging.getLogger(__name__)

_FILETRANS_PENDING_STATUSES = {"PENDING", "RUNNING"}
_FILETRANS_FAILED_STATUSES = {"FAILED", "UNKNOWN"}


@dataclass(frozen=True)
class _AsrModelConfig:
    """Normalized provider/model configuration for ASR calls."""

    litellm_model: str
    provider: str
    provider_model: str
    api_key: str | None
    compatible_api_base: str | None
    api_base: str | None


class QwenAsrError(RuntimeError):
    """Raised when DashScope ASR returns an application-level error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


def _compatible_base_url() -> str:
    base = settings.dashscope_api_base.rstrip("/")
    return base.replace("/api/", "/compatible-mode/")


def _async_base_url() -> str:
    return settings.dashscope_api_base.rstrip("/")


def _auth_headers(*, async_mode: bool = False) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }
    if async_mode:
        headers["X-DashScope-Async"] = "enable"
    return headers


def _asr_options() -> dict:
    options = {
        "enable_itn": settings.qwen_asr_enable_itn,
    }
    language = settings.qwen_asr_language.strip()
    if language:
        options["language"] = language
    return options


def _normalize_provider_model(model: str, default_model: str) -> str:
    model = model.strip()
    if not model:
        return default_model
    if model.startswith("dashscope/"):
        return model
    if "/" in model:
        return model
    return f"dashscope/{model}"


def _build_asr_model_config(
    model: str,
    *,
    default_model: str,
) -> _AsrModelConfig:
    litellm_model = _normalize_provider_model(model, default_model)
    provider, provider_model = litellm_model.split("/", 1)

    if provider == "dashscope":
        api_key = settings.dashscope_api_key or None
        compatible_api_base = _compatible_base_url()
        api_base = _async_base_url()
    else:
        api_key = None
        compatible_api_base = None
        api_base = None

    return _AsrModelConfig(
        litellm_model=litellm_model,
        provider=provider,
        provider_model=provider_model,
        api_key=api_key,
        compatible_api_base=compatible_api_base,
        api_base=api_base,
    )


def _sync_model_config() -> _AsrModelConfig:
    return _build_asr_model_config(
        settings.qwen_asr_model,
        default_model="dashscope/qwen3-asr-flash",
    )


def _filetrans_model_config() -> _AsrModelConfig:
    return _build_asr_model_config(
        settings.qwen_asr_filetrans_model,
        default_model="dashscope/qwen3-asr-flash-filetrans",
    )


def _require_dashscope_filetrans(config: _AsrModelConfig) -> None:
    if config.provider != "dashscope" or not config.api_key or not config.api_base:
        raise RuntimeError(
            "Qwen ASR filetrans currently requires a dashscope/* model and "
            "DASHSCOPE_API_KEY."
        )


def _parse_error_payload(
    response: httpx.Response,
) -> tuple[str, str | None]:
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return text or f"DashScope ASR HTTP {response.status_code}", None

    code = payload.get("code")
    for key in ("message", "detail"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip(), code

    output = payload.get("output")
    if isinstance(output, dict):
        code = output.get("code") or code
        message = output.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip(), code

    return f"DashScope ASR HTTP {response.status_code}", code


def _extract_text_from_message(content) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, dict):
                text = str(item.get("text", "")).strip()
            else:
                text = str(item).strip()
            if text:
                parts.append(text)
        return "\n".join(parts).strip()

    return str(content or "").strip()


def _extract_litellm_transcript(response) -> str:
    choices = getattr(response, "choices", []) or []
    if not choices:
        raise QwenAsrError("LiteLLM ASR returned no choices")

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None) if message else None
    transcript = _extract_text_from_message(content)
    if not transcript:
        raise QwenAsrError("LiteLLM ASR returned empty transcript")
    return transcript


def _extract_openai_payload_transcript(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise QwenAsrError("DashScope ASR returned no choices")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise QwenAsrError("DashScope ASR returned invalid choice payload")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise QwenAsrError("DashScope ASR returned no message payload")

    transcript = _extract_text_from_message(message.get("content"))
    if not transcript:
        raise QwenAsrError("DashScope ASR returned empty transcript")
    return transcript


def _extract_filetrans_transcript(payload: dict) -> str:
    transcripts = payload.get("transcripts") or []
    parts: list[str] = []
    for item in transcripts:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts).strip()


def _should_fallback_to_filetrans(exc: QwenAsrError) -> bool:
    message = str(exc).lower()
    if exc.status_code in {400, 413, 422}:
        return True
    if exc.code and any(
        token in exc.code.lower()
        for token in ("size", "length", "limit", "invalid_parameter")
    ):
        return True
    return any(
        token in message
        for token in (
            "10 mb",
            "10mb",
            "too large",
            "size limit",
            "length limit",
            "maximum size",
            "exceeds",
        )
    )


def _to_qwen_asr_error(exc: Exception) -> QwenAsrError:
    if isinstance(exc, QwenAsrError):
        return exc

    status_code = getattr(exc, "status_code", None)
    code = getattr(exc, "code", None)
    message = str(exc).strip() or "LiteLLM ASR request failed"
    return QwenAsrError(
        message,
        status_code=status_code if isinstance(status_code, int) else None,
        code=code if isinstance(code, str) else None,
    )


async def _fetch_remote_file_size_bytes(
    client: httpx.AsyncClient,
    audio_url: str,
) -> int | None:
    try:
        response = await client.head(
            audio_url,
            timeout=httpx.Timeout(settings.qwen_asr_timeout_seconds, connect=10.0),
        )
    except Exception:
        return None

    if response.status_code >= 400:
        return None

    content_length = response.headers.get("content-length", "").strip()
    if not content_length:
        return None

    try:
        return int(content_length)
    except ValueError:
        return None


async def _post_json(
    client: httpx.AsyncClient,
    url: str,
    payload: dict,
    *,
    headers: dict[str, str],
    timeout_seconds: float,
) -> dict:
    response = await client.post(
        url,
        headers=headers,
        json=payload,
        timeout=httpx.Timeout(timeout_seconds, connect=10.0),
    )
    if response.status_code >= 400:
        message, code = _parse_error_payload(response)
        raise QwenAsrError(
            message,
            status_code=response.status_code,
            code=code,
        )
    return response.json()


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    headers: dict[str, str] | None,
    timeout_seconds: float,
) -> dict:
    response = await client.get(
        url,
        headers=headers,
        timeout=httpx.Timeout(timeout_seconds, connect=10.0),
    )
    if response.status_code >= 400:
        message, code = _parse_error_payload(response)
        raise QwenAsrError(
            message,
            status_code=response.status_code,
            code=code,
        )
    return response.json()


async def _transcribe_short_audio(
    client: httpx.AsyncClient,
    audio_url: str,
) -> str:
    model_config = _sync_model_config()
    asr_options = _asr_options()
    payload = {
        "model": model_config.provider_model
        if model_config.provider == "dashscope"
        else model_config.litellm_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"data": audio_url},
                    }
                ],
            }
        ],
        "stream": False,
    }

    if model_config.provider == "dashscope":
        payload["asr_options"] = asr_options
        try:
            response_data = await _post_json(
                client,
                f"{model_config.compatible_api_base}/chat/completions",
                payload,
                headers=_auth_headers(),
                timeout_seconds=settings.qwen_asr_timeout_seconds,
            )
        except Exception as exc:
            raise _to_qwen_asr_error(exc) from exc

        transcript = _extract_openai_payload_transcript(response_data)
    else:
        if not HAS_LITELLM or acompletion is None:
            raise RuntimeError(
                "LiteLLM is required for non-DashScope short-audio ASR."
            )
        if model_config.api_key and model_config.compatible_api_base:
            payload["api_key"] = model_config.api_key
            payload["api_base"] = model_config.compatible_api_base
        payload["extra_body"] = {"asr_options": asr_options}
        try:
            response = await acompletion(**payload)
        except Exception as exc:
            raise _to_qwen_asr_error(exc) from exc

        transcript = _extract_litellm_transcript(response)
    return transcript


async def _submit_filetrans_task(
    client: httpx.AsyncClient,
    audio_url: str,
) -> str:
    model_config = _filetrans_model_config()
    _require_dashscope_filetrans(model_config)
    payload = {
        "model": model_config.provider_model,
        "input": {"file_url": audio_url},
        "parameters": _asr_options(),
    }
    data = await _post_json(
        client,
        f"{model_config.api_base}/services/audio/asr/transcription",
        payload,
        headers=_auth_headers(async_mode=True),
        timeout_seconds=settings.qwen_asr_timeout_seconds,
    )
    output = data.get("output") or {}
    task_id = str(output.get("task_id", "")).strip()
    if not task_id:
        raise QwenAsrError("DashScope ASR filetrans did not return a task_id")
    return task_id


async def _download_filetrans_result(
    client: httpx.AsyncClient,
    transcription_url: str,
) -> str:
    data = await _get_json(
        client,
        transcription_url,
        headers=None,
        timeout_seconds=settings.qwen_asr_timeout_seconds,
    )
    transcript = _extract_filetrans_transcript(data)
    if not transcript:
        raise QwenAsrError("DashScope ASR filetrans returned empty transcript")
    return transcript


async def _transcribe_long_audio(
    client: httpx.AsyncClient,
    audio_url: str,
) -> str:
    model_config = _filetrans_model_config()
    _require_dashscope_filetrans(model_config)
    task_id = await _submit_filetrans_task(client, audio_url)
    deadline = (
        asyncio.get_running_loop().time()
        + settings.qwen_asr_filetrans_timeout_seconds
    )
    task_url = f"{model_config.api_base}/tasks/{task_id}"

    while True:
        data = await _get_json(
            client,
            task_url,
            headers=_auth_headers(async_mode=True),
            timeout_seconds=settings.qwen_asr_timeout_seconds,
        )
        output = data.get("output") or {}
        task_status = str(output.get("task_status", "")).upper()

        if task_status == "SUCCEEDED":
            result = output.get("result") or {}
            transcription_url = str(
                result.get("transcription_url", "")
            ).strip()
            if not transcription_url:
                raise QwenAsrError(
                    "DashScope ASR filetrans completed without transcript URL"
                )
            return await _download_filetrans_result(client, transcription_url)

        if task_status in _FILETRANS_FAILED_STATUSES:
            message = str(
                output.get("message") or "DashScope ASR filetrans failed"
            ).strip()
            code = str(output.get("code", "")).strip() or None
            raise QwenAsrError(message, code=code)

        if task_status not in _FILETRANS_PENDING_STATUSES:
            raise QwenAsrError(
                f"DashScope ASR returned unexpected task status: {task_status}"
            )

        if asyncio.get_running_loop().time() >= deadline:
            raise TimeoutError("DashScope ASR filetrans polling timed out")

        await asyncio.sleep(settings.qwen_asr_poll_interval_seconds)


@observe(name="transcribe_audio", as_type="generation")
async def transcribe_audio(
    audio_url: str,
    *,
    user_id: str | None = None,
    session_id: str | None = None,
) -> str:
    """Transcribe an audio URL with Qwen ASR.

    Short DashScope audio is attempted through the compatible-mode endpoint
    first. Other providers use the OpenAI-compatible completion path.
    When the synchronous path rejects the input, the function falls back to
    the filetrans workflow for longer audio files.
    """
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is required for audio ASR.")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        with propagate_attributes(
            user_id=user_id or "",
            session_id=session_id or "",
            metadata={
                "llm": _sync_model_config().litellm_model,
                "filetrans_model": _filetrans_model_config().litellm_model,
            },
        ):
            max_sync_bytes = settings.qwen_asr_sync_max_file_mb * 1024 * 1024
            file_size_bytes = await _fetch_remote_file_size_bytes(
                client, audio_url
            )
            if (
                max_sync_bytes > 0
                and file_size_bytes is not None
                and file_size_bytes > max_sync_bytes
            ):
                logger.info(
                    "Using ASR filetrans for %s bytes audio", file_size_bytes
                )
                return await _transcribe_long_audio(client, audio_url)
            try:
                return await _transcribe_short_audio(client, audio_url)
            except Exception as exc:
                exc = _to_qwen_asr_error(exc)
                if not _should_fallback_to_filetrans(exc):
                    raise
                logger.info(
                    "Falling back to ASR filetrans after sync failure: %s",
                    exc,
                )
                return await _transcribe_long_audio(client, audio_url)
