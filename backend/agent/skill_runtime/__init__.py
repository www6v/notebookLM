"""Minimal skill-doc-driven runtime inspired by nanobot."""

from .agent_loop import SkillAgentLoop, WorkflowStageResult
from .executor import (
    OpenAISkillExecutor,
    SkillRunResult,
    merge_skill_run_results,
)
from .loader import SkillInfo, SkillLoader, SkillReference
from .prompt_builder import DEFAULT_SKILL_NAMES, SkillPromptBuilder

__all__ = [
    "DEFAULT_SKILL_NAMES",
    "OpenAISkillExecutor",
    "SkillAgentLoop",
    "SkillInfo",
    "SkillLoader",
    "SkillPromptBuilder",
    "SkillReference",
    "SkillRunResult",
    "WorkflowStageResult",
    "merge_skill_run_results",
]
