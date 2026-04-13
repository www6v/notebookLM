from __future__ import annotations

import argparse
import json
import logging
import os
import re
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from typing import Literal, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScriptLine:
    def __init__(
        self,
        speaker: Literal["male", "female"] = "male",
        paragraph: str = "",
    ):
        self.speaker = speaker
        self.paragraph = paragraph


class Script:
    def __init__(
        self,
        locale: Literal["en", "zh"] = "en",
        lines: list[ScriptLine] | None = None,
    ):
        self.locale = locale
        self.lines = lines or []

    @classmethod
    def from_dict(cls, data: dict) -> Script:
        loc = data.get("locale", "en")
        if loc not in ("en", "zh"):
            loc = "en"
        script = cls(locale=loc)
        for line in data.get("lines", []):
            script.lines.append(
                ScriptLine(
                    speaker=line.get("speaker", "male"),
                    paragraph=line.get("paragraph", ""),
                )
            )
        return script


# Qwen3-TTS ~512 tokens per request; stay conservative for mixed CJK/Latin.
_MAX_TTS_CHARS_ZH = 280
_MAX_TTS_CHARS_EN = 450


def _dashscope_api_key() -> str:
    key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY") or ""
    return key.strip()


def _dashscope_api_base() -> str:
    base = (
        os.getenv("DASHSCOPE_API_BASE")
        or os.getenv("QWEN_API_BASE")
        or "https://dashscope.aliyuncs.com/api/v1"
    )
    return base.rstrip("/")


def _tts_model() -> str:
    return os.getenv("QWEN_TTS_MODEL", "qwen3-tts-flash").strip()


def _voice_for_speaker(speaker: Literal["male", "female"]) -> str:
    if speaker == "male":
        return os.getenv("QWEN_TTS_VOICE_MALE", "Ethan").strip()
    return os.getenv("QWEN_TTS_VOICE_FEMALE", "Cherry").strip()


def _language_type_for_locale(locale: str) -> str:
    if locale == "zh":
        return "Chinese"
    if locale == "en":
        return "English"
    return "Auto"


def _split_paragraph(text: str, locale: str) -> list[str]:
    """Split long text for TTS limits, preferring sentence boundaries."""
    text = text.strip()
    if not text:
        return []
    max_len = _MAX_TTS_CHARS_ZH if locale == "zh" else _MAX_TTS_CHARS_EN
    if len(text) <= max_len:
        return [text]

    if locale == "zh":
        parts = re.split(r"(?<=[。！？；\n])", text)
    else:
        parts = re.split(r"(?<=[.!?\n])\s*", text)

    chunks: list[str] = []
    buf = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(buf) + len(p) <= max_len:
            buf = f"{buf}{p}" if buf else p
            continue
        if buf:
            chunks.append(buf)
        if len(p) <= max_len:
            buf = p
        else:
            for i in range(0, len(p), max_len):
                chunks.append(p[i : i + max_len])
            buf = ""
    if buf:
        chunks.append(buf)
    return [c for c in chunks if c.strip()]


def _merge_wav_bytes(parts: list[bytes]) -> bytes:
    """Concatenate WAV byte blobs (same sample format required)."""
    if not parts:
        raise ValueError("No WAV segments to merge")
    first_buf = BytesIO(parts[0])
    with wave.open(first_buf, "rb") as w0:
        nchannels = w0.getnchannels()
        sampwidth = w0.getsampwidth()
        framerate = w0.getframerate()
        if w0.getcomptype() != "NONE":
            raise ValueError("Compressed WAV is not supported")
    out_buf = BytesIO()
    with wave.open(out_buf, "wb") as out_w:
        out_w.setnchannels(nchannels)
        out_w.setsampwidth(sampwidth)
        out_w.setframerate(framerate)
        for raw in parts:
            with wave.open(BytesIO(raw), "rb") as w:
                if (
                    w.getnchannels() != nchannels
                    or w.getsampwidth() != sampwidth
                    or w.getframerate() != framerate
                ):
                    raise ValueError("WAV format mismatch between TTS segments")
                if w.getcomptype() != "NONE":
                    raise ValueError("Compressed WAV is not supported")
                out_w.writeframes(w.readframes(w.getnframes()))
    return out_buf.getvalue()


def _synthesize_segment(
    text: str,
    voice: str,
    language_type: str,
    api_key: str,
    api_base: str,
    model: str,
) -> Optional[bytes]:
    """One Qwen TTS call; returns WAV bytes from result URL."""
    url = f"{api_base}/services/aigc/multimodal-generation/generation"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "model": model,
        "input": {
            "text": text,
            "voice": voice,
            "language_type": language_type,
        },
    }
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=120)
        if resp.status_code != 200:
            logger.error(
                "TTS HTTP %s: %s",
                resp.status_code,
                resp.text[:500],
            )
            return None
        data = resp.json()
        if data.get("code"):
            logger.error(
                "TTS API error: %s — %s",
                data.get("code"),
                data.get("message"),
            )
            return None
        audio_info = (data.get("output") or {}).get("audio") or {}
        audio_url = audio_info.get("url")
        if not audio_url:
            logger.error("TTS response missing output.audio.url")
            return None
        wav_resp = requests.get(audio_url, timeout=120)
        if wav_resp.status_code != 200:
            logger.error(
                "TTS audio download failed: %s",
                wav_resp.status_code,
            )
            return None
        return wav_resp.content
    except Exception as exc:
        logger.error("TTS error: %s", exc)
        return None


def text_to_speech(
    text: str,
    voice: str,
    language_type: str,
) -> Optional[bytes]:
    """Convert text to speech (WAV) via DashScope Qwen3-TTS."""
    api_key = _dashscope_api_key()
    if not api_key:
        raise ValueError(
            "DASHSCOPE_API_KEY or QWEN_API_KEY must be set for Qwen TTS"
        )
    chunk_loc = (
        "zh"
        if language_type == "Chinese"
        else "en"
        if language_type == "English"
        else "zh"
    )
    segments = _split_paragraph(text, chunk_loc)
    if not segments:
        return None
    api_base = _dashscope_api_base()
    model = _tts_model()
    wav_parts: list[bytes] = []
    for seg in segments:
        part = _synthesize_segment(
            seg,
            voice,
            language_type,
            api_key,
            api_base,
            model,
        )
        if not part:
            return None
        wav_parts.append(part)
    if len(wav_parts) == 1:
        return wav_parts[0]
    return _merge_wav_bytes(wav_parts)


def _process_line(
    args: tuple[int, ScriptLine, int, str],
) -> tuple[int, Optional[bytes]]:
    """Process a single script line for TTS. Returns (index, wav bytes)."""
    i, line, total, locale = args
    language_type = _language_type_for_locale(locale)
    voice = _voice_for_speaker(line.speaker)
    logger.info(
        "Processing line %s/%s (%s, voice=%s)",
        i + 1,
        total,
        line.speaker,
        voice,
    )
    try:
        audio = text_to_speech(line.paragraph, voice, language_type)
    except ValueError:
        raise
    except Exception as exc:
        logger.error("Line %s TTS failed: %s", i + 1, exc)
        audio = None
    if not audio:
        logger.warning("Failed to generate audio for line %s", i + 1)
    return (i, audio)


def tts_node(script: Script, max_workers: int = 4) -> list[bytes]:
    """Convert script lines to WAV chunks using TTS with multi-threading."""
    logger.info("Converting script to audio using %s workers...", max_workers)
    total = len(script.lines)
    if total == 0:
        raise ValueError("Script contains no lines to process")
    if not _dashscope_api_key():
        raise ValueError(
            "Missing DASHSCOPE_API_KEY or QWEN_API_KEY for Qwen TTS"
        )
    locale = script.locale if script.locale in ("en", "zh") else "en"
    tasks = [(i, line, total, locale) for i, line in enumerate(script.lines)]
    results: dict[int, Optional[bytes]] = {}
    failed_indices: list[int] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process_line, t): t[0] for t in tasks}
        for future in as_completed(futures):
            idx, audio = future.result()
            results[idx] = audio
            if not audio:
                failed_indices.append(idx)
    if failed_indices:
        logger.warning(
            "Failed to generate audio for %s/%s lines: line numbers %s",
            len(failed_indices),
            total,
            sorted(i + 1 for i in failed_indices),
        )
    audio_chunks: list[bytes] = []
    for i in range(total):
        audio = results.get(i)
        if audio:
            audio_chunks.append(audio)
    logger.info(
        "Generated %s/%s audio chunks successfully",
        len(audio_chunks),
        total,
    )
    if not audio_chunks:
        raise ValueError(
            "TTS generation failed for all lines. Check API key and Qwen TTS "
            "quota; optional: QWEN_TTS_VOICE_MALE / QWEN_TTS_VOICE_FEMALE."
        )
    return audio_chunks


def mix_audio(audio_chunks: list[bytes]) -> bytes:
    """Combine WAV chunks into a single WAV file."""
    logger.info("Mixing audio chunks...")
    if not audio_chunks:
        raise ValueError("No audio chunks to mix - TTS may have failed")
    merged = _merge_wav_bytes(audio_chunks)
    if len(merged) == 0:
        raise ValueError("Mixed audio is empty - TTS may have failed")
    logger.info("Audio mixing complete: %s bytes", len(merged))
    return merged


def generate_markdown(script: Script, title: str = "Podcast Script") -> str:
    """Generate a markdown script from the podcast script."""
    lines = [f"# {title}", ""]
    for line in script.lines:
        speaker_name = (
            "**Host (Male)**" if line.speaker == "male" else "**Host (Female)**"
        )
        lines.append(f"{speaker_name}: {line.paragraph}")
        lines.append("")
    return "\n".join(lines)


def generate_podcast(
    script_file: str,
    output_file: str,
    transcript_file: Optional[str] = None,
) -> str:
    """Generate a podcast from a script JSON file."""
    with open(script_file, "r", encoding="utf-8") as f:
        script_json = json.load(f)
    if "lines" not in script_json:
        raise ValueError(
            "Invalid script format: missing 'lines' key. "
            f"Got keys: {list(script_json.keys())}"
        )
    script = Script.from_dict(script_json)
    logger.info("Loaded script with %s lines", len(script.lines))
    if transcript_file:
        title = script_json.get("title", "Podcast Script")
        markdown_content = generate_markdown(script, title)
        transcript_dir = os.path.dirname(transcript_file)
        if transcript_dir:
            os.makedirs(transcript_dir, exist_ok=True)
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logger.info("Generated transcript to %s", transcript_file)
    audio_chunks = tts_node(script)
    if not audio_chunks:
        raise RuntimeError("Failed to generate any audio")
    output_audio = mix_audio(audio_chunks)
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_file, "wb") as f:
        f.write(output_audio)
    result = f"Successfully generated podcast to {output_file}"
    if transcript_file:
        result += f" and transcript to {transcript_file}"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate podcast from script JSON file (Qwen TTS → WAV)",
    )
    parser.add_argument(
        "--script-file",
        required=True,
        help="Absolute path to script JSON file",
    )
    parser.add_argument(
        "--output-file",
        required=True,
        help="Output path for generated podcast WAV",
    )
    parser.add_argument(
        "--transcript-file",
        required=False,
        help="Output path for transcript markdown (optional)",
    )
    args = parser.parse_args()
    try:
        result = generate_podcast(
            args.script_file,
            args.output_file,
            args.transcript_file,
        )
        print(result)
    except Exception as e:
        import traceback

        print(f"Error generating podcast: {e}")
        traceback.print_exc()
