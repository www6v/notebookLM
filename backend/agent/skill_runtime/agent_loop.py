"""Skill agent loop: single entry over OpenAISkillExecutor tool rounds."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .executor import OpenAISkillExecutor, SkillRunResult


@dataclass(frozen=True)
class WorkflowStageResult:
    """Result metadata for one agent workflow (compat with prior staged API)."""

    stage: str
    output_path: Path
    llm_result: SkillRunResult


class SkillAgentLoop:
    """Agent loop backed by chat completions + local tools (no memory/subagent)."""

    def __init__(
        self,
        workspace: Path,
        executor: OpenAISkillExecutor,
    ) -> None:
        self.workspace = workspace.resolve()
        self._executor = executor

    async def run(
        self,
        *,
        skill_name: str,
        task: str,
        model: str,
        options: dict[str, str] | None = None,
        attachments: list[str] | None = None,
        selected_skills: list[str] | None = None,
        temperature: float | None = None,
        max_completion_tokens: int | None = None,
    ) -> SkillRunResult:
        """Run one skill task with default bundled skill registry in system prompt."""
        return await self._executor.run(
            skill_name=skill_name,
            task=task,
            options=options,
            attachments=attachments,
            model=model,
            selected_skills=selected_skills,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
        )
