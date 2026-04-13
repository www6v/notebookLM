"""Skill discovery and loading helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import shutil
from typing import Iterable


DIMENSION_REFERENCE_ALIASES = {
    "clean": "texture.md",
    "grid": "texture.md",
    "organic": "texture.md",
    "pixel": "texture.md",
    "paper": "texture.md",
    "professional": "mood.md",
    "warm": "mood.md",
    "cool": "mood.md",
    "vibrant": "mood.md",
    "dark": "mood.md",
    "neutral": "mood.md",
    "geometric": "typography.md",
    "humanist": "typography.md",
    "handwritten": "typography.md",
    "editorial": "typography.md",
    "technical": "typography.md",
    "minimal": "density.md",
    "balanced": "density.md",
    "dense": "density.md",
}


@dataclass(frozen=True)
class SkillInfo:
    """Metadata for a discovered skill."""

    name: str
    path: Path
    source: str
    description: str = ""
    available: bool = True
    missing_requirements: tuple[str, ...] = ()
    metadata: dict[str, str] | None = None


@dataclass(frozen=True)
class SkillReference:
    """One reference path mentioned by a skill document."""

    raw_path: str
    resolved_path: Path
    exists: bool
    uses_placeholders: bool


class SkillLoader:
    """Discover skills from workspace and user-level directories."""

    def __init__(
        self,
        workspace: Path,
        builtin_skill_dirs: Iterable[Path] | None = None,
    ) -> None:
        self.workspace = workspace.resolve()
        self.workspace_skill_dirs = [
            self.workspace / "agent" / "skills",
            self.workspace / "agent",
            self.workspace / "agent" / ".cursor" / "skills",
            self.workspace / ".cursor" / "skills",
        ]
        self.builtin_skill_dirs = [
            path.expanduser().resolve()
            for path in (
                builtin_skill_dirs
                or [
                    Path.home() / ".agents" / "skills",
                ]
            )
        ]

    def list_skills(self) -> list[SkillInfo]:
        """List all discovered skills with workspace priority."""
        skills: dict[str, SkillInfo] = {}

        for skill_dir in self.workspace_skill_dirs:
            for info in self._scan_dir(skill_dir, source="workspace"):
                skills[info.name] = info

        for skill_dir in self.builtin_skill_dirs:
            for info in self._scan_dir(skill_dir, source="builtin"):
                skills.setdefault(info.name, info)

        return sorted(skills.values(), key=lambda item: item.name)

    def load_skill(self, name: str) -> str:
        """Load a skill by directory name."""
        info = self.get_skill(name)
        if info is None:
            raise FileNotFoundError(f"Skill not found: {name}")
        return info.path.read_text(encoding="utf-8")

    def load_skills_for_context(self, skill_names: list[str]) -> str:
        """Load selected skills with frontmatter stripped."""
        parts = []
        for name in skill_names:
            content = self.load_skill(name)
            stripped = self._strip_frontmatter(content)
            parts.append(f"### Skill: {name}\n\n{stripped}")
        return "\n\n---\n\n".join(parts) if parts else ""

    def load_reference(
        self,
        skill_name: str,
        reference_path: str,
        variables: dict[str, str] | None = None,
    ) -> str:
        """Load one skill reference file by relative path."""
        skill = self.get_skill(skill_name)
        if skill is None:
            raise FileNotFoundError(f"Skill not found: {skill_name}")

        resolved = self.resolve_reference_path(
            skill=skill,
            reference_path=reference_path,
            variables=variables or {},
        )
        return resolved.read_text(encoding="utf-8")

    def get_skill(self, name: str) -> SkillInfo | None:
        """Return metadata for one skill."""
        for info in self.list_skills():
            if info.name == name:
                return info
        return None

    def list_skill_references(
        self,
        name: str,
        variables: dict[str, str] | None = None,
    ) -> list[SkillReference]:
        """List references declared or mentioned by a skill."""
        skill = self.get_skill(name)
        if skill is None:
            raise FileNotFoundError(f"Skill not found: {name}")

        content = self.load_skill(name)
        raw_paths = self._extract_reference_paths(content)
        references = []
        for raw_path in raw_paths:
            resolved = self.resolve_reference_path(
                skill=skill,
                reference_path=raw_path,
                variables=variables or {},
            )
            references.append(
                SkillReference(
                    raw_path=raw_path,
                    resolved_path=resolved,
                    exists=resolved.exists(),
                    uses_placeholders="<" in raw_path and ">" in raw_path,
                )
            )
        return references

    def build_skills_summary(self) -> str:
        """Build a short summary block like nanobot's prompt context."""
        skills = self.list_skills()
        if not skills:
            return ""

        lines = ["# Skills", ""]
        lines.append(
            "The following skills extend your capabilities. To use a skill, "
            "load its SKILL.md and follow the document as the task procedure."
        )
        lines.append("")

        for info in skills:
            lines.append(f"- `{info.name}`")
            lines.append(f"  path: `{info.path}`")
            lines.append(f"  source: `{info.source}`")
            lines.append(f"  available: `{str(info.available).lower()}`")
            if info.description:
                lines.append(f"  description: {info.description}")
            if info.missing_requirements:
                joined = ", ".join(info.missing_requirements)
                lines.append(f"  missing: {joined}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def build_skills_summary_for_names(self, names: Iterable[str]) -> str:
        """Build a skills summary for an ordered allowlist (session registry)."""
        by_name = {info.name: info for info in self.list_skills()}
        lines = ["# Skills", ""]
        lines.append(
            "Registered skills for this session (metadata only unless loaded "
            "elsewhere)."
        )
        lines.append("")
        for name in names:
            info = by_name.get(name)
            if info is None:
                lines.append(f"- `{name}`")
                lines.append("  status: `not discovered`")
                lines.append("")
                continue
            lines.append(f"- `{info.name}`")
            lines.append(f"  path: `{info.path}`")
            lines.append(f"  source: `{info.source}`")
            lines.append(f"  available: `{str(info.available).lower()}`")
            if info.description:
                lines.append(f"  description: {info.description}")
            if info.missing_requirements:
                joined = ", ".join(info.missing_requirements)
                lines.append(f"  missing: {joined}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def get_skill_metadata(self, name: str) -> dict[str, str] | None:
        """Return parsed frontmatter metadata for a skill."""
        info = self.get_skill(name)
        if info is None:
            return None
        return info.metadata or {}

    def get_always_skills(self) -> list[str]:
        """Return skills marked as always=true and currently available."""
        result = []
        for info in self.list_skills():
            metadata = info.metadata or {}
            if not info.available:
                continue
            if metadata.get("always", "").lower() == "true":
                result.append(info.name)
        return result

    def build_references_summary(
        self,
        name: str,
        variables: dict[str, str] | None = None,
    ) -> str:
        """Build a progressive-disclosure summary for one skill's references."""
        references = self.list_skill_references(name, variables=variables)
        if not references:
            return ""

        lines = [
            "## Skill References",
            "",
            "The following reference files are available for progressive disclosure.",
            "Do not inline them by default. Load a specific file only when its details",
            "are needed for the current step.",
            "",
        ]

        for reference in references:
            status = "exists" if reference.exists else "missing"
            placeholder = " templated" if reference.uses_placeholders else ""
            lines.append(f"- `{reference.raw_path}`")
            lines.append(f"  resolved: `{reference.resolved_path}`")
            lines.append(f"  status: `{status}`{placeholder}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def _scan_dir(self, base_dir: Path, source: str) -> list[SkillInfo]:
        """Read one skill root and return discovered skills."""
        if not base_dir.exists():
            return []

        skills = []
        for child in sorted(base_dir.iterdir(), key=lambda item: item.name):
            if not child.is_dir():
                continue
            skill_file = child / "SKILL.md"
            if not skill_file.exists():
                continue
            metadata = self._get_skill_metadata(skill_file)
            available, missing_requirements = self._check_requirements(metadata)
            description = self._get_skill_description(skill_file)
            skills.append(
                SkillInfo(
                    name=child.name,
                    path=skill_file,
                    source=source,
                    description=description,
                    available=available,
                    missing_requirements=tuple(missing_requirements),
                    metadata=metadata,
                )
            )
        return skills

    def _get_skill_description(self, skill_file: Path) -> str:
        """Extract a lightweight description from frontmatter or first heading."""
        content = skill_file.read_text(encoding="utf-8")
        frontmatter = self._get_skill_metadata(skill_file)
        if "description" in frontmatter:
            return frontmatter["description"]

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return ""

    def _parse_frontmatter(self, content: str) -> dict[str, str]:
        """Parse a simple YAML frontmatter block."""
        if not content.startswith("---\n"):
            return {}

        match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
        if not match:
            return {}

        data: dict[str, str] = {}
        for raw_line in match.group(1).splitlines():
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
        return data

    def _get_skill_metadata(self, skill_file: Path) -> dict[str, str]:
        """Read frontmatter metadata from a SKILL.md file."""
        content = skill_file.read_text(encoding="utf-8")
        return self._parse_frontmatter(content)

    def _strip_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from markdown content."""
        if not content.startswith("---\n"):
            return content.strip()

        match = re.match(r"^---\n.*?\n---\n?", content, re.DOTALL)
        if not match:
            return content.strip()
        return content[match.end():].strip()

    def _check_requirements(
        self,
        metadata: dict[str, str],
    ) -> tuple[bool, list[str]]:
        """Check simple frontmatter requirements similar to nanobot."""
        requires_bins = self._split_csv(metadata.get("requires_bins", ""))
        requires_env = self._split_csv(metadata.get("requires_env", ""))
        missing: list[str] = []

        for binary in requires_bins:
            binary_path = shutil.which(binary)
            if binary_path is None:
                missing.append(f"CLI: {binary}")

        for env_name in requires_env:
            if not os.environ.get(env_name):
                missing.append(f"ENV: {env_name}")

        return not missing, missing

    def resolve_reference_path(
        self,
        skill: SkillInfo,
        reference_path: str,
        variables: dict[str, str] | None = None,
    ) -> Path:
        """Resolve a skill-local reference path against the skill directory."""
        variables = variables or {}
        rendered = reference_path
        for key, value in variables.items():
            rendered = rendered.replace(f"<{key}>", value)

        skill_root = skill.path.parent.resolve()
        resolved = (skill_root / rendered).resolve()
        if skill_root not in resolved.parents and resolved != skill_root:
            raise FileNotFoundError(
                f"Reference path escapes skill root: {reference_path}"
            )
        if not resolved.exists():
            aliased = self._resolve_dimension_alias(skill_root, rendered)
            if aliased is not None:
                return aliased
        return resolved

    def _resolve_dimension_alias(
        self,
        skill_root: Path,
        rendered_reference_path: str,
    ) -> Path | None:
        """Map dimension option aliases to their canonical reference files."""
        relative_path = Path(rendered_reference_path)
        if relative_path.parent.as_posix() != "references/dimensions":
            return None
        if relative_path.suffix != ".md":
            return None

        target_name = DIMENSION_REFERENCE_ALIASES.get(relative_path.stem)
        if target_name is None:
            return None

        aliased_path = (skill_root / "references" / "dimensions" / target_name)
        if aliased_path.exists():
            return aliased_path.resolve()
        return None

    def _extract_reference_paths(self, content: str) -> list[str]:
        """Extract unique `references/...` paths from skill markdown."""
        pattern = re.compile(r"`(references/[^`]+)`|(references/[^\s)]+)")
        paths: list[str] = []
        seen: set[str] = set()

        for match in pattern.finditer(content):
            raw_path = match.group(1) or match.group(2)
            raw_path = raw_path.strip().rstrip(".,")
            if raw_path in seen:
                continue
            seen.add(raw_path)
            paths.append(raw_path)
        return paths

    def _split_csv(self, raw: str) -> list[str]:
        """Parse a comma-separated frontmatter value."""
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]
