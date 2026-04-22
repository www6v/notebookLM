"""Structured audit logging for skill-runtime tool calls.

Ops can ship ``skill_runtime.tool_audit`` to a log pipeline and alert on
``TOOL_AUDIT_DENIED`` or ``TOOL_AUDIT_RUN_SHELL`` without ingesting full
arguments (secrets).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("skill_runtime.tool_audit")


def audit_tool_denied(skill_name: str | None, tool_name: str) -> None:
    """Log a tool the model requested but policy blocked for this skill."""
    logger.warning(
        "TOOL_AUDIT_DENIED skill=%r tool=%r",
        skill_name,
        tool_name,
    )


def audit_tool_invoked(
    skill_name: str | None,
    tool_name: str,
    arguments: dict[str, Any],
) -> None:
    """Log one allowed tool invocation with argument metadata only (no bodies)."""
    extra = _safe_argument_summary(tool_name, arguments)
    logger.info(
        "TOOL_AUDIT_INVOKE skill=%r tool=%r %s",
        skill_name,
        tool_name,
        extra,
    )


def audit_tool_result(
    skill_name: str | None,
    tool_name: str,
    *,
    response_chars: int,
) -> None:
    """Log tool response size for volume / cost monitoring."""
    logger.info(
        "TOOL_AUDIT_RESULT skill=%r tool=%r response_chars=%s",
        skill_name,
        tool_name,
        response_chars,
    )


def audit_run_shell(
    skill_name: str | None,
    *,
    working_directory: str,
    command_char_len: int,
) -> None:
    """High-visibility log for any real shell execution (alert hook)."""
    logger.warning(
        "TOOL_AUDIT_RUN_SHELL skill=%r cwd=%r command_char_len=%s",
        skill_name,
        working_directory,
        command_char_len,
    )


def _truncate(value: str, max_len: int = 240) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


def _safe_argument_summary(tool_name: str, arguments: dict[str, Any]) -> str:
    """Build a short, log-safe summary; never log write_file content."""
    if tool_name == "list_dir":
        return f"path={_truncate(str(arguments.get('path', '.')))!r}"
    if tool_name == "read_file":
        return f"path={_truncate(str(arguments.get('path', '')))!r}"
    if tool_name == "write_file":
        path = str(arguments.get("path", ""))
        content = arguments.get("content", "")
        content_len = len(content) if isinstance(content, str) else 0
        return (
            f"path={_truncate(path)!r} content_chars={content_len}"
        )
    if tool_name == "read_skill_reference":
        return (
            f"ref_skill={arguments.get('skill_name')!r} "
            f"ref_path={_truncate(str(arguments.get('reference_path', '')))!r}"
        )
    if tool_name == "generate_image_from_promptfile":
        return (
            f"prompt_path={_truncate(str(arguments.get('prompt_path', '')))!r} "
            f"output_path={_truncate(str(arguments.get('output_path', '')))!r} "
            f"aspect_ratio={arguments.get('aspect_ratio')!r}"
        )
    if tool_name == "run_shell":
        cmd = str(arguments.get("command", ""))
        return (
            f"working_directory={_truncate(str(arguments.get('working_directory', '.')))!r} "
            f"command_char_len={len(cmd)}"
        )
    return "args_redacted"
