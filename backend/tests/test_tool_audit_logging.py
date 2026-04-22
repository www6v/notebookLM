"""Regression tests for skill-runtime tool audit logging."""

from __future__ import annotations

import logging
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from agent.skill_runtime.loader import SkillLoader
from agent.skill_runtime.tool_policy import tool_allowlist_for_skill
from agent.skill_runtime.tools import SkillToolRuntime


@pytest.mark.asyncio
async def test_denied_run_shell_logs_tool_audit_denied(caplog) -> None:
    """Blocked shell attempts must emit WARNING for alerting pipelines."""
    caplog.set_level(logging.WARNING)
    loader = SkillLoader(workspace=BACKEND_ROOT)
    allow = tool_allowlist_for_skill("baoyu-infographic")
    runtime = SkillToolRuntime(
        BACKEND_ROOT,
        loader,
        current_skill_name="baoyu-infographic",
        allowed_tool_names=allow,
    )
    await runtime.execute(
        "run_shell",
        {"command": "echo x", "working_directory": "."},
    )
    assert any(
        "TOOL_AUDIT_DENIED" in rec.message and "run_shell" in rec.message
        for rec in caplog.records
    )


@pytest.mark.asyncio
async def test_allowed_list_dir_logs_tool_audit_invoke(caplog) -> None:
    """Allowed tools should emit INFO invoke lines (no full tool bodies)."""
    caplog.set_level(logging.INFO)
    loader = SkillLoader(workspace=BACKEND_ROOT)
    allow = tool_allowlist_for_skill("baoyu-infographic")
    runtime = SkillToolRuntime(
        BACKEND_ROOT,
        loader,
        current_skill_name="baoyu-infographic",
        allowed_tool_names=allow,
    )
    await runtime.execute("list_dir", {"path": "."})
    assert any(
        "TOOL_AUDIT_INVOKE" in rec.message and "list_dir" in rec.message
        for rec in caplog.records
    )


@pytest.mark.asyncio
async def test_run_shell_when_allowed_logs_tool_audit_run_shell(caplog) -> None:
    """Real run_shell must emit WARNING with command length only (no body)."""
    caplog.set_level(logging.WARNING)
    loader = SkillLoader(workspace=BACKEND_ROOT)
    runtime = SkillToolRuntime(
        BACKEND_ROOT,
        loader,
        current_skill_name="unlisted-skill",
    )
    cmd = "echo ok"
    with patch(
        "agent.skill_runtime.tools.subprocess.run",
        return_value=MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        ),
    ) as mock_run:
        await runtime.execute(
            "run_shell",
            {"command": cmd, "working_directory": "."},
        )
    mock_run.assert_called_once()
    assert any(
        "TOOL_AUDIT_RUN_SHELL" in rec.message
        and f"command_char_len={len(cmd)}" in rec.message
        for rec in caplog.records
    )
    for rec in caplog.records:
        if "TOOL_AUDIT_RUN_SHELL" in rec.message:
            assert "echo" not in rec.message
