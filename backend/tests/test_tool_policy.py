"""Tests for per-skill tool allowlists."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from agent.skill_runtime.loader import SkillLoader
from agent.skill_runtime.tool_policy import tool_allowlist_for_skill
from agent.skill_runtime.tools import SkillToolRuntime


def test_studio_skills_disallow_run_shell_in_policy() -> None:
    """Bundled studio skills must not include run_shell."""
    for name in (
        "baoyu-infographic",
        "baoyu-slide-deck",
        "podcast-generation",
    ):
        allow = tool_allowlist_for_skill(name)
        assert allow is not None
        assert "run_shell" not in allow
        assert "read_file" in allow
        assert "write_file" in allow


def test_unknown_skill_uses_full_tool_set() -> None:
    """Unlisted skills keep all tools (backward compatible)."""
    assert tool_allowlist_for_skill("some-future-skill") is None


def test_get_tool_specs_filters_run_shell_for_infographic() -> None:
    """OpenAI tool list must omit run_shell when allowlisted."""
    loader = SkillLoader(workspace=BACKEND_ROOT)
    allow = tool_allowlist_for_skill("baoyu-infographic")
    runtime = SkillToolRuntime(
        BACKEND_ROOT,
        loader,
        current_skill_name="baoyu-infographic",
        allowed_tool_names=allow,
    )
    names = {s["function"]["name"] for s in runtime.get_tool_specs()}
    assert "run_shell" not in names
    assert names == allow


@pytest.mark.asyncio
async def test_execute_run_shell_rejected_under_allowlist() -> None:
    """Defense in depth: block run_shell even if the model requests it."""
    loader = SkillLoader(workspace=BACKEND_ROOT)
    allow = tool_allowlist_for_skill("baoyu-infographic")
    runtime = SkillToolRuntime(
        BACKEND_ROOT,
        loader,
        current_skill_name="baoyu-infographic",
        allowed_tool_names=allow,
    )
    out = await runtime.execute(
        "run_shell",
        {"command": "echo pwned", "working_directory": "."},
    )
    payload = json.loads(out)
    assert payload.get("error") == "tool_not_allowed_for_skill"
    assert payload.get("tool") == "run_shell"


def test_full_runtime_includes_run_shell_when_no_allowlist() -> None:
    """Default runtime still advertises run_shell for unlisted skills."""
    loader = SkillLoader(workspace=BACKEND_ROOT)
    runtime = SkillToolRuntime(BACKEND_ROOT, loader)
    names = {s["function"]["name"] for s in runtime.get_tool_specs()}
    assert "run_shell" in names
