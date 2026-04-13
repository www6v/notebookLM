"""Build skill-driven execution prompts."""

from __future__ import annotations

from pathlib import Path

from .loader import SkillLoader, SkillInfo

DEFAULT_SKILL_NAMES: tuple[str, ...] = (
    "baoyu-infographic",
    "baoyu-slide-deck",
    "podcast-generation",
)


class SkillPromptBuilder:
    """Create prompts that tell an agent to follow SKILL.md as procedure."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()

    def build_prompt(
        self,
        skill: SkillInfo,
        skill_content: str,
        task: str,
        options: dict[str, str] | None = None,
        attachments: list[str] | None = None,
        references_summary: str = "",
    ) -> str:
        """Return a full prompt for a selected skill and task."""
        stripped_content = self._strip_frontmatter(skill_content)
        task_message = self.build_task_message(
            skill=skill,
            task=task,
            options=options,
            attachments=attachments,
            references_summary=references_summary,
        )
        return (
            f"{task_message}\n"
            "## Skill Document\n"
            f"{stripped_content}\n"
        )

    def build_task_message(
        self,
        skill: SkillInfo,
        task: str,
        options: dict[str, str] | None = None,
        attachments: list[str] | None = None,
        references_summary: str = "",
    ) -> str:
        """Build the user-task message consumed by an LLM runtime."""
        option_lines = self._format_mapping(options or {})
        attachment_lines = self._format_list(attachments or [])

        lines = [
            "# Skill-Driven Task",
            "",
            "You must complete the task by following the selected SKILL.md "
            "document as the primary procedure.",
            "",
            "## Runtime Context",
            f"- Workspace: `{self.workspace}`",
            f"- Selected skill: `{skill.name}`",
            f"- Skill path: `{skill.path}`",
            f"- Skill source: `{skill.source}`",
        ]

        if skill.description:
            lines.append(f"- Skill description: {skill.description}")

        lines.extend(
            [
                "",
                "## Task",
                task,
                "",
                "## Parameters",
            ]
        )

        if option_lines:
            lines.extend(option_lines)
        else:
            lines.append("- None")

        lines.extend(
            [
                "",
                "## Referenced Files",
            ]
        )

        if attachment_lines:
            lines.extend(attachment_lines)
        else:
            lines.append("- None")

        lines.extend(
            [
                "",
                "## Execution Rules",
                "- Follow the selected skill document exactly where applicable.",
                "- If the task conflicts with the skill's supported options, "
                "normalize the parameters and state the normalization clearly.",
                "- Do not invent workflow steps that contradict the skill.",
                "- Use the workspace paths exactly as provided.",
                "- Treat skill references as progressive disclosure material: "
                "inspect the catalog first, then load only the specific "
                "reference files needed for the current step.",
                "",
            ]
        )

        if references_summary:
            lines.extend(
                [
                    references_summary.strip(),
                    "",
                ]
            )

        return "\n".join(lines)

    def build_system_prompt(
        self,
        loader: SkillLoader,
        *,
        primary_skill_name: str,
        full_skill_names: list[str] | None = None,
        default_registry_skills: tuple[str, ...] = DEFAULT_SKILL_NAMES,
    ) -> str:
        """Build a nanobot-style system prompt for skill discovery.

        Inlines full SKILL.md only for ``full_skill_names`` (defaults to the
        primary skill). Other ``default_registry_skills`` appear as summary
        rows so the model can load them via ``read_skill_reference``.
        """
        resolved_full = list(
            dict.fromkeys(
                full_skill_names
                if full_skill_names is not None
                else [primary_skill_name]
            )
        )
        summary_only = [
            name
            for name in default_registry_skills
            if name not in set(resolved_full)
        ]
        parts = [
            "# Skill Runtime",
            "",
            f"Workspace: `{self.workspace}`",
            "",
            "Use skills progressively:",
            "- Inspect the skills summary first.",
            "- Full SKILL.md is inlined only under `# Selected skills` below.",
            "- For other default-bundle skills, use `read_skill_reference` or "
            "read the skill path when you need their procedure.",
            "- Load references only when needed for the current step.",
            "- When execution is requested, use the available tools to "
            "actually perform the work.",
            "- Do not stop at a prose plan if tools can complete the next "
            "step.",
            "- If the workflow already has a prompt file and the task asks "
            "for a final image, call `generate_image_from_promptfile` instead "
            "of only describing that step.",
            "",
            f"- Default skill bundle: {', '.join(default_registry_skills)}.",
            f"- Active primary skill: `{primary_skill_name}`.",
            "",
        ]

        skills_summary = loader.build_skills_summary()
        if skills_summary:
            parts.append(skills_summary.strip())
            parts.append("")

        if summary_only:
            registry_block = loader.build_skills_summary_for_names(summary_only)
            if registry_block.strip():
                parts.append("# Default registry (summary only)")
                parts.append("")
                parts.append(registry_block.strip())
                parts.append("")

        always_skills = loader.get_always_skills()
        if always_skills:
            active_content = loader.load_skills_for_context(always_skills)
            if active_content:
                parts.append("# Active Skills")
                parts.append("")
                parts.append(active_content)
                parts.append("")

        selected_content = loader.load_skills_for_context(resolved_full)
        if selected_content:
            parts.append("# Selected skills (full documents)")
            parts.append("")
            parts.append(selected_content)
            parts.append("")

        return "\n".join(parts).rstrip() + "\n"

    def _strip_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter if present."""
        if not content.startswith("---\n"):
            return content.strip()

        end = content.find("\n---", 4)
        if end == -1:
            return content.strip()
        return content[end + 4:].strip()

    def _format_mapping(self, mapping: dict[str, str]) -> list[str]:
        """Render parameters as markdown bullets."""
        return [f"- `{key}`: `{value}`" for key, value in mapping.items()]

    def _format_list(self, items: list[str]) -> list[str]:
        """Render a list of file references."""
        return [f"- `{item}`" for item in items]
