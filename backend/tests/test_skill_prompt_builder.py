"""Tests for skill prompt builder and session registry summaries."""

from __future__ import annotations

from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from agent.skill_runtime.loader import SkillLoader
from agent.skill_runtime.prompt_builder import (
    DEFAULT_SKILL_NAMES,
    SkillPromptBuilder,
)


def test_build_skills_summary_for_names_lists_defaults() -> None:
    """Ordered allowlist should mention each requested skill."""
    loader = SkillLoader(workspace=BACKEND_ROOT)
    block = loader.build_skills_summary_for_names(
        [
            "baoyu-infographic",
            "baoyu-slide-deck",
            "podcast-generation",
        ]
    )
    assert "baoyu-infographic" in block
    assert "baoyu-slide-deck" in block
    assert "podcast-generation" in block


def test_build_system_prompt_default_registry_summary_only() -> None:
    """Primary skill full document; other bundle skills stay summary-only."""
    loader = SkillLoader(workspace=BACKEND_ROOT)
    builder = SkillPromptBuilder(BACKEND_ROOT)
    prompt = builder.build_system_prompt(
        loader,
        primary_skill_name="baoyu-infographic",
        full_skill_names=["baoyu-infographic"],
        default_registry_skills=DEFAULT_SKILL_NAMES,
    )
    assert "# Selected skills (full documents)" in prompt
    assert "### Skill: baoyu-infographic" in prompt
    assert "### Skill: baoyu-slide-deck" not in prompt
    assert "# Default registry (summary only)" in prompt


def test_build_system_prompt_two_full_skills() -> None:
    """Explicit full_skill_names inlines each listed skill once."""
    loader = SkillLoader(workspace=BACKEND_ROOT)
    builder = SkillPromptBuilder(BACKEND_ROOT)
    prompt = builder.build_system_prompt(
        loader,
        primary_skill_name="baoyu-infographic",
        full_skill_names=["baoyu-infographic", "baoyu-slide-deck"],
        default_registry_skills=DEFAULT_SKILL_NAMES,
    )
    assert prompt.count("### Skill: baoyu-infographic") == 1
    assert prompt.count("### Skill: baoyu-slide-deck") == 1
    assert "### Skill: podcast-generation" not in prompt
    assert "podcast-generation" in prompt
