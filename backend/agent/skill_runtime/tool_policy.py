"""Per-skill tool allowlists for the skill agent runtime."""

from __future__ import annotations

# All tools currently exposed by SkillToolRuntime.get_tool_specs().
_ALL_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "list_dir",
        "read_file",
        "write_file",
        "run_shell",
        "read_skill_reference",
        "generate_image_from_promptfile",
    }
)

# Studio workflows: no arbitrary shell (prompt-injection surface).
_STUDIO_NO_SHELL: frozenset[str] = _ALL_TOOL_NAMES - frozenset({"run_shell"})

# skill_name -> allowed OpenAI function tool names
SKILL_TOOL_ALLOWLIST: dict[str, frozenset[str]] = {
    "baoyu-infographic": _STUDIO_NO_SHELL,
    "baoyu-slide-deck": _STUDIO_NO_SHELL,
    "podcast-generation": _STUDIO_NO_SHELL,
}


def tool_allowlist_for_skill(skill_name: str | None) -> frozenset[str] | None:
    """Return allowed tools for ``skill_name``, or None for full tool set.

    Unknown skills get ``None`` so CLI / future skills keep prior behavior
    (including ``run_shell``) unless explicitly listed above.
    """
    if not skill_name:
        return None
    return SKILL_TOOL_ALLOWLIST.get(skill_name)
