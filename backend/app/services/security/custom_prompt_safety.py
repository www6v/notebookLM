"""Shared validation for user-supplied custom prompt fields."""

from __future__ import annotations

import re
import unicodedata

MAX_CUSTOM_PROMPT_CHARS = 1000
MAX_CUSTOM_PROMPT_LINES = 120

_LINE_BREAK_RE = re.compile(r"\r\n?")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_MULTI_BLANK_RE = re.compile(r"\n{3,}")

_PROMPT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?is)\b(ignore|disregard|bypass|override)\b.{0,40}"
        r"\b(previous|above|system|developer|instruction|rules?)\b"
    ),
    re.compile(
        r"(?is)\b(system prompt|developer message|hidden prompt|"
        r"jailbreak|prompt injection)\b"
    ),
    re.compile(
        r"(?is)\b(run|execute|call|invoke)\b.{0,30}"
        r"\b(shell|command|bash|sh|powershell|terminal|tool|function)\b"
    ),
    re.compile(
        r"(?is)\b(curl|wget|netcat|nc|scp|ssh)\b"
    ),
    re.compile(
        r"(?is)\b(read|open|print|list|dump|exfiltrate)\b.{0,30}"
        r"\b(\.env|secret|token|api[_ -]?key|credential|password)\b"
    ),
    re.compile(
        r"(?s)(忽略|无视).{0,20}(之前|以上|系统|开发者|规则|指令)"
    ),
    re.compile(
        r"(?s)(执行|运行|调用).{0,20}(命令|shell|终端|工具)"
    ),
    re.compile(
        r"(?s)(读取|导出|泄露).{0,20}(密钥|凭证|token|secret|"
        r"密码|\\.env)"
    ),
)


def validate_custom_prompt_text(
    value: str | None,
    *,
    field_name: str,
    max_chars: int = MAX_CUSTOM_PROMPT_CHARS,
) -> str | None:
    """Validate and normalize custom prompt text from user input."""
    if value is None:
        return None
    normalized = _normalize_custom_prompt(value)
    if not normalized:
        return None
    if len(normalized) > max_chars:
        raise ValueError(
            f"{field_name} exceeds {max_chars} characters."
        )
    line_count = len(normalized.splitlines())
    if line_count > MAX_CUSTOM_PROMPT_LINES:
        raise ValueError(
            f"{field_name} exceeds {MAX_CUSTOM_PROMPT_LINES} lines."
        )
    if _looks_like_prompt_injection(normalized):
        raise ValueError(
            f"{field_name} contains unsafe instructions. "
            "Only provide visual/content preferences."
        )
    return normalized


def _normalize_custom_prompt(value: str) -> str:
    """Normalize line breaks and remove hidden control characters."""
    normalized = unicodedata.normalize("NFKC", value)
    normalized = "".join(
        ch for ch in normalized if unicodedata.category(ch) != "Cf"
    )
    normalized = _LINE_BREAK_RE.sub("\n", normalized)
    normalized = _CONTROL_CHAR_RE.sub("", normalized)
    normalized = normalized.strip()
    normalized = _MULTI_BLANK_RE.sub("\n\n", normalized)
    return normalized


def _looks_like_prompt_injection(text: str) -> bool:
    """Return true when text matches known prompt-injection patterns."""
    return any(pattern.search(text) for pattern in _PROMPT_INJECTION_PATTERNS)
