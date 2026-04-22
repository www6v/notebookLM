"""Local tool runtime for skill-driven execution."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from app.services.studio.image_generation_service import (
    aspect_ratio_to_size,
    generate_image_from_prompt,
)

from .loader import SkillLoader


class SkillToolRuntime:
    """Execute local tools for a skill-driven agent loop."""

    def __init__(
        self,
        workspace: Path,
        loader: SkillLoader,
        *,
        current_skill_name: str | None = None,
        current_variables: dict[str, str] | None = None,
        allowed_tool_names: frozenset[str] | None = None,
        image_provider: str | None = None,
        image_model: str | None = None,
        image_quality: str = "2k",
        image_api_key: str | None = None,
    ) -> None:
        self.workspace = workspace.resolve()
        self.loader = loader
        self.current_skill_name = current_skill_name
        self.current_variables = current_variables or {}
        self.allowed_tool_names = allowed_tool_names
        self.image_provider = image_provider
        self.image_model = image_model
        self.image_quality = image_quality
        self.image_api_key = image_api_key
        self.extra_allowed_roots = [
            (Path.home() / ".agents" / "skills").resolve(),
            (Path.home() / ".baoyu-skills").resolve(),
        ]

    def get_tool_specs(self) -> list[dict]:
        """Return OpenAI-compatible tool definitions."""
        specs: list[dict] = [
            {
                "type": "function",
                "function": {
                    "name": "list_dir",
                    "description": "List files and directories inside a workspace path.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative or absolute path inside the workspace.",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a UTF-8 text file from the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative or absolute file path inside the workspace.",
                            }
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write a UTF-8 text file in the workspace, creating parents if needed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative or absolute file path inside the workspace.",
                            },
                            "content": {
                                "type": "string",
                                "description": "Full file contents to write.",
                            },
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_shell",
                    "description": "Run a shell command in the workspace for external commands like cp, mv, or Python scripts.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute.",
                            },
                            "working_directory": {
                                "type": "string",
                                "description": "Optional relative or absolute path inside the workspace.",
                            },
                            "timeout_ms": {
                                "type": "integer",
                                "description": "Optional timeout in milliseconds. Default 30000.",
                            },
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_skill_reference",
                    "description": "Read one progressive-disclosure reference file for a selected skill.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "skill_name": {
                                "type": "string",
                                "description": "Skill directory name, for example baoyu-infographic.",
                            },
                            "reference_path": {
                                "type": "string",
                                "description": "Reference path, for example references/base-prompt.md.",
                            },
                            "variables": {
                                "type": "object",
                                "description": "Optional placeholder substitutions like layout/style.",
                                "additionalProperties": {"type": "string"},
                            },
                        },
                        "required": ["skill_name", "reference_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_image_from_promptfile",
                    "description": "Generate an image from a prompt markdown file using the backend image service.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt_path": {
                                "type": "string",
                                "description": "Workspace path to the prompt markdown file.",
                            },
                            "output_path": {
                                "type": "string",
                                "description": "Workspace path for the output image.",
                            },
                            "aspect_ratio": {
                                "type": "string",
                                "description": "Aspect ratio like 16:9, 9:16, or 1:1.",
                            },
                            "provider": {
                                "type": "string",
                                "description": "Optional provider override. If omitted, runtime defaults may be used.",
                            },
                            "model": {
                                "type": "string",
                                "description": "Optional image model override. If omitted, runtime defaults may be used.",
                            },
                            "quality": {
                                "type": "string",
                                "description": "Optional quality preset, normal or 2k. If omitted, runtime defaults may be used.",
                            },
                        },
                        "required": ["prompt_path", "output_path"],
                    },
                },
            },
        ]
        if self.allowed_tool_names is not None:
            return [
                spec
                for spec in specs
                if spec.get("function", {}).get("name") in self.allowed_tool_names
            ]
        return specs

    def _tool_allowed(self, tool_name: str) -> bool:
        """Return whether ``tool_name`` may run for this runtime."""
        if self.allowed_tool_names is None:
            return True
        return tool_name in self.allowed_tool_names

    async def execute(self, tool_name: str, arguments: dict) -> str:
        """Run one tool call and return a text result."""
        if not self._tool_allowed(tool_name):
            return json.dumps(
                {
                    "error": "tool_not_allowed_for_skill",
                    "tool": tool_name,
                    "skill": self.current_skill_name,
                    "message": (
                        "This tool is disabled for the current skill. "
                        "Use read_file, write_file, list_dir, "
                        "read_skill_reference, or generate_image_from_promptfile."
                    ),
                },
                ensure_ascii=False,
            )
        if tool_name == "list_dir":
            return self.list_dir(arguments.get("path", "."))
        if tool_name == "read_file":
            return self.read_file(arguments["path"])
        if tool_name == "write_file":
            return self.write_file(arguments["path"], arguments["content"])
        if tool_name == "run_shell":
            return self.run_shell(
                command=arguments["command"],
                working_directory=arguments.get("working_directory", "."),
                timeout_ms=arguments.get("timeout_ms", 30000),
            )
        if tool_name == "read_skill_reference":
            return self.read_skill_reference(
                skill_name=arguments["skill_name"],
                reference_path=arguments["reference_path"],
                variables=arguments.get("variables") or {},
            )
        if tool_name == "generate_image_from_promptfile":
            return await self.generate_image_from_promptfile(
                prompt_path=arguments["prompt_path"],
                output_path=arguments["output_path"],
                aspect_ratio=arguments.get("aspect_ratio", "16:9"),
                provider=arguments.get("provider") or self.image_provider,
                model=arguments.get("model") or self.image_model,
                quality=arguments.get("quality") or self.image_quality,
            )
        raise ValueError(f"Unsupported tool: {tool_name}")

    def list_dir(self, path: str = ".") -> str:
        """List a workspace directory."""
        target = self._resolve_workspace_path(path)
        if not target.exists():
            return f"Directory not found: {target}"
        if not target.is_dir():
            return f"Path is not a directory: {target}"

        entries = []
        for child in sorted(target.iterdir(), key=lambda item: item.name):
            suffix = "/" if child.is_dir() else ""
            entries.append(f"{child.name}{suffix}")
        return "\n".join(entries) if entries else "(empty)"

    def read_file(self, path: str) -> str:
        """Read a workspace file."""
        target = self._resolve_workspace_path(path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {target}")
        return target.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> str:
        """Write a workspace file."""
        target = self._resolve_workspace_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {target}"

    def run_shell(
        self,
        *,
        command: str,
        working_directory: str = ".",
        timeout_ms: int = 30000,
    ) -> str:
        """Run a shell command inside the workspace."""
        cwd = self._resolve_workspace_path(working_directory)
        if not cwd.exists() or not cwd.is_dir():
            raise FileNotFoundError(f"Working directory not found: {cwd}")

        completed = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=max(timeout_ms, 1) / 1000,
        )
        payload = {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def read_skill_reference(
        self,
        *,
        skill_name: str,
        reference_path: str,
        variables: dict[str, str],
    ) -> str:
        """Read one skill reference through the loader."""
        return self.loader.load_reference(
            skill_name=skill_name,
            reference_path=reference_path,
            variables=variables,
        )

    async def generate_image_from_promptfile(
        self,
        *,
        prompt_path: str,
        output_path: str,
        aspect_ratio: str = "16:9",
        provider: str | None = None,
        model: str | None = None,
        quality: str = "2k",
    ) -> str:
        """Generate an image from a prompt file through the backend service."""
        prompt_file = self._resolve_workspace_path(prompt_path)
        output_file = self._resolve_workspace_path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_text = prompt_file.read_text(encoding="utf-8").strip()
        image_bytes = await generate_image_from_prompt(
            prompt_text,
            size=aspect_ratio_to_size(aspect_ratio),
            title=output_file.stem,
        )
        if image_bytes is None:
            payload = {
                "returncode": 1,
                "stdout": "",
                "stderr": "Image generation returned no bytes.",
                "output_path": str(output_file),
                "provider": provider,
                "model": model,
                "quality": quality,
            }
            return json.dumps(payload, ensure_ascii=False, indent=2)

        output_file.write_bytes(image_bytes)
        payload = {
            "returncode": 0,
            "stdout": "Image generated via backend service.",
            "stderr": "",
            "output_path": str(output_file),
            "provider": provider,
            "model": model,
            "quality": quality,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _skill_reference_relative_path(self, path: str) -> str | None:
        """Return skill-relative references/... path if `path` targets the active skill."""
        if not self.current_skill_name:
            return None
        skill = self.loader.get_skill(self.current_skill_name)
        if skill is None:
            return None

        skill_root = skill.path.parent.resolve()
        normalized = path.replace("\\", "/").strip()
        if normalized.startswith("references/"):
            return normalized

        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = (self.workspace / candidate).resolve()
        else:
            candidate = candidate.resolve()

        try:
            relative = candidate.relative_to(skill_root)
        except ValueError:
            return None

        rel_posix = relative.as_posix()
        if rel_posix.startswith("references/"):
            return rel_posix
        return None

    def _resolve_workspace_path(self, path: str) -> Path:
        """Resolve a path inside the workspace or approved config roots."""
        ref_relative = self._skill_reference_relative_path(path)
        if ref_relative is not None and self.current_skill_name:
            skill = self.loader.get_skill(self.current_skill_name)
            if skill is not None:
                return self.loader.resolve_reference_path(
                    skill=skill,
                    reference_path=ref_relative,
                    variables=self.current_variables,
                )

        target = Path(path)
        if not target.is_absolute():
            target = (self.workspace / target).resolve()
        else:
            target = target.resolve()

        allowed_roots = [self.workspace, *self.extra_allowed_roots]
        if not any(
            root in target.parents or target == root
            for root in allowed_roots
        ):
            raise FileNotFoundError(f"Path escapes workspace: {path}")
        return target
