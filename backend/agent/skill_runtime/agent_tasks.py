"""Single-shot agent tasks for bundled skills (replaces staged workflows)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shutil

INFOGRAPHIC_STAGES = ("analysis", "structured", "prompt", "image")

INFOGRAPHIC_STAGE_REL = {
    "analysis": "analysis.md",
    "structured": "structured-content.md",
    "prompt": "prompts/infographic.md",
}
SLIDE_DECK_STAGES = ("analysis", "outline", "prompt", "image")
PODCAST_STAGES = ("script", "audio")

ASPECT_RATIO_MAP = {
    "landscape": "16:9",
    "portrait": "9:16",
    "square": "1:1",
}

_PODCAST_FORMAT_INSTRUCTIONS: dict[str, str] = {
    "deep_dive": (
        "深入探究：两位主持人之间生动、有互动的对话，解读并串联来源中的主题，"
        "适当举例与追问。"
    ),
    "summary": (
        "摘要：用尽量少的对话轮次概括来源的核心观点，语气清晰、紧凑。"
    ),
    "commentary": (
        "评论：一位偏主持、一位偏点评，对来源给出建设性评价与可执行建议。"
    ),
    "debate": (
        "辩论：两位主持人立场有张力但尊重对方，围绕来源中的争议点展开论证。"
    ),
}


def _podcast_length_instruction(audio_length: str) -> str:
    if audio_length == "short":
        return (
            "短：约 15–25 轮对话（lines 条目），每段 paragraph 不宜过长。"
        )
    return (
        "默认：约 35–50 轮对话（lines 条目），保持节奏紧凑、好听懂。"
    )


@dataclass(frozen=True)
class PreparedSkillWorkspace:
    """Resolved paths after copying source into the workflow output dir."""

    workspace: Path
    source_path: Path
    source_copy: Path
    output_dir: Path


def backup_if_exists(path: Path) -> None:
    """Rename an existing file before overwriting it."""
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.stem}-backup-{stamp}{path.suffix}")
    shutil.move(str(path), str(backup))


def workspace_relative(workspace: Path, path: Path) -> str:
    """Return a path relative to workspace."""
    return str(path.resolve().relative_to(workspace.resolve()))


def prepare_skill_workspace(
    workspace: Path,
    source_path: str,
    output_dir: str,
) -> PreparedSkillWorkspace:
    """Copy source into output_dir and return resolved paths."""
    root = workspace.resolve()
    source = Path(source_path)
    if not source.is_absolute():
        source = (root / source).resolve()
    else:
        source = source.resolve()
    out_dir = Path(output_dir)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    else:
        out_dir = out_dir.resolve()
    if root not in out_dir.parents and out_dir != root:
        raise FileNotFoundError(f"Output path escapes workspace: {output_dir}")
    if root not in source.parents and source != root:
        raise FileNotFoundError(f"Source path escapes workspace: {source_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    source_copy = out_dir / f"source-{source.name}"
    backup_if_exists(source_copy)
    shutil.copy2(source, source_copy)
    return PreparedSkillWorkspace(
        workspace=root,
        source_path=source,
        source_copy=source_copy,
        output_dir=out_dir,
    )


def build_infographic_agent_task(
    prep: PreparedSkillWorkspace,
    *,
    through_stage: str,
    options: dict[str, str],
) -> tuple[str, list[str]]:
    """Return (task, attachments) for baoyu-infographic."""
    if through_stage not in INFOGRAPHIC_STAGES:
        raise ValueError(f"Unsupported through_stage: {through_stage}")
    ws = prep.workspace
    rel_source = workspace_relative(ws, prep.source_path)
    rel_copy = workspace_relative(ws, prep.source_copy)
    rel_out = workspace_relative(ws, prep.output_dir)
    rel_analysis = workspace_relative(ws, prep.output_dir / "analysis.md")
    rel_structured = workspace_relative(
        ws, prep.output_dir / "structured-content.md"
    )
    rel_prompt = workspace_relative(
        ws, prep.output_dir / "prompts" / "infographic.md"
    )
    rel_image = workspace_relative(ws, prep.output_dir / "infographic.png")
    aspect_key = options.get("aspect", "landscape")
    aspect_ratio = ASPECT_RATIO_MAP.get(aspect_key, aspect_key)

    stage_hints = {
        "analysis": (
            f"Step 1 only: read `references/analysis-framework.md`, analyze "
            f"`{rel_source}`, write `{rel_analysis}`. "
            "Stop after this file exists; do not continue to later steps."
        ),
        "structured": (
            f"Steps 1–2: ensure `{rel_analysis}` exists (create via Step 1 if "
            f"missing). Read `{rel_source}` and analysis. Read "
            f"`references/structured-content-template.md`. Write "
            f"`{rel_structured}`. Stop after structured content exists."
        ),
        "prompt": (
            f"Steps 1–5: produce `{rel_analysis}`, `{rel_structured}`, then "
            f"read `references/base-prompt.md` and layout/style references. "
            f"Write `{rel_prompt}`. Stop after the prompt file exists; do "
            f"not generate the final image yet."
        ),
        "image": (
            f"Run the full baoyu-infographic pipeline: Steps 1–6 through "
            f"final image. Use `{rel_source}`; output dir `{rel_out}`. "
            f"Artifacts: `{rel_analysis}`, `{rel_structured}`, `{rel_prompt}`, "
            f"then call `generate_image_from_promptfile` for `{rel_prompt}` "
            f"-> `{rel_image}` with aspect_ratio `{aspect_ratio}`."
        ),
    }
    task = (
        "Execute the baoyu-infographic skill in non-interactive automation "
        "mode.\n"
        f"{stage_hints[through_stage]}\n"
        "Use tools to write files and generate the image; do not stop at a "
        "plan only.\n"
        f"Parameters: {options!r}."
    )
    attachments = [rel_source, rel_copy]
    return task, attachments


def build_slide_deck_agent_task(
    prep: PreparedSkillWorkspace,
    *,
    through_stage: str,
    options: dict[str, str],
) -> tuple[str, list[str]]:
    """Return (task, attachments) for baoyu-slide-deck."""
    if through_stage not in SLIDE_DECK_STAGES:
        raise ValueError(f"Unsupported through_stage: {through_stage}")
    ws = prep.workspace
    rel_source = workspace_relative(ws, prep.source_path)
    rel_copy = workspace_relative(ws, prep.source_copy)
    rel_out = workspace_relative(ws, prep.output_dir)
    rel_analysis = workspace_relative(ws, prep.output_dir / "analysis.md")
    rel_outline = workspace_relative(ws, prep.output_dir / "outline.md")
    rel_prompts = workspace_relative(ws, prep.output_dir / "prompts")
    images_only = options.get("images-only", "").lower() in {
        "1",
        "true",
        "yes",
    }
    img_note = "\nTreat this run as `--images-only`." if images_only else ""

    stage_hints = {
        "analysis": (
            f"Step 1 only: read `references/analysis-framework.md`, analyze "
            f"`{rel_source}`, write `{rel_analysis}`. Stop after analysis."
        ),
        "outline": (
            f"Steps 1 and 3: `{rel_analysis}` then read "
            f"`references/outline-template.md`; write `{rel_outline}` with "
            f"parameters style/audience/lang/slides. Stop after outline."
        ),
        "prompt": (
            f"Steps 1,3,5: through `{rel_outline}`; read "
            f"`references/base-prompt.md` and `references/layouts.md`; write "
            f"all prompt markdown files under `{rel_prompts}/`. Stop before "
            f"generating images."
        ),
        "image": (
            f"Full pipeline through Step 7: analysis, outline, prompts under "
            f"`{rel_prompts}/`, then call `generate_image_from_promptfile` "
            f"for each slide prompt into `{rel_out}`."
            f"{img_note}"
        ),
    }
    task = (
        "Execute the baoyu-slide-deck skill in non-interactive automation "
        "mode.\n"
        f"{stage_hints[through_stage]}\n"
        "Skip review and confirmation steps; use tools to create files and "
        "images.\n"
        f"Parameters: {options!r}."
    )
    attachments: list[str] = [rel_source, rel_copy]
    if through_stage in {"outline", "prompt", "image"}:
        attachments.append(rel_analysis)
    if through_stage in {"prompt", "image"}:
        attachments.append(rel_outline)
    return task, attachments


def build_podcast_agent_task(
    prep: PreparedSkillWorkspace,
    *,
    through_stage: str,
    options: dict[str, str],
) -> tuple[str, list[str]]:
    """Return (task, attachments) for podcast-generation (script via LLM)."""
    if through_stage not in PODCAST_STAGES:
        raise ValueError(f"Unsupported through_stage: {through_stage}")
    ws = prep.workspace
    rel_source = workspace_relative(ws, prep.source_path)
    rel_copy = workspace_relative(ws, prep.source_copy)
    rel_out = workspace_relative(ws, prep.output_dir)
    rel_script = workspace_relative(ws, prep.output_dir / "script.json")

    format_key = options.get("audio_format", "deep_dive")
    format_hint = _PODCAST_FORMAT_INSTRUCTIONS.get(
        format_key,
        _PODCAST_FORMAT_INSTRUCTIONS["deep_dive"],
    )
    length_hint = _podcast_length_instruction(
        options.get("audio_length", "default")
    )
    lang = options.get("audio_language", "简体中文")
    focus_raw = (options.get("audio_focus_prompt") or "").strip()
    focus_block = (
        f"\nUser focus / emphasis:\n{focus_raw}\n" if focus_raw else ""
    )
    audio_note = ""
    if through_stage == "audio":
        audio_note = (
            "\nAfter `script.json` is valid, stop; the host will run TTS "
            "separately. Do not run shell audio commands."
        )

    task = (
        "Execute the podcast-generation skill: produce structured JSON "
        "script only (no TTS).\n"
        f"Source: `{rel_source}`; copy: `{rel_copy}`; output dir: "
        f"`{rel_out}`.\n"
        "Obey SKILL.md: JSON with title, locale (en or zh), lines of "
        "{speaker: male|female, paragraph: string}. Plain spoken text; "
        'male opens with a greeting containing "Hello Deer"; alternate '
        "hosts naturally.\n"
        "If the source is technical documentation or a tutorial, call "
        "`read_skill_reference` with skill_name `podcast-generation` and "
        "reference_path `templates/tech-explainer.md` before drafting "
        "lines.\n"
        f"Episode format:\n{format_hint}\n"
        f"Target length:\n{length_hint}\n"
        f"Dialogue language:\n{lang}\n"
        f"{focus_block}"
        f"Write raw JSON only to `{rel_script}` via `write_file` (no "
        f"markdown fences)."
        f"{audio_note}"
    )
    return task, [rel_source, rel_copy]


def infographic_artifact_followup_task(
    prep: PreparedSkillWorkspace,
    through_stage: str,
) -> str | None:
    """Force write_file when a non-image stage output is still missing."""
    rel_key = INFOGRAPHIC_STAGE_REL.get(through_stage)
    if rel_key is None:
        return None
    ws = prep.workspace
    rel_target = workspace_relative(ws, prep.output_dir / rel_key)
    return (
        "The required output file is still missing. You MUST call "
        f"`write_file` now with path exactly `{rel_target}` "
        "(workspace-relative path). Write the complete markdown for this "
        "workflow step. Do not finish until the file exists on disk."
    )


def infographic_followup_task(
    prep: PreparedSkillWorkspace,
    *,
    through_stage: str,
    options: dict[str, str],
) -> str | None:
    """Return a corrective task if the first run may have missed artifacts."""
    if through_stage != "image":
        return None
    ws = prep.workspace
    rel_prompt = workspace_relative(
        ws, prep.output_dir / "prompts" / "infographic.md"
    )
    rel_image = workspace_relative(ws, prep.output_dir / "infographic.png")
    aspect_key = options.get("aspect", "landscape")
    aspect_ratio = ASPECT_RATIO_MAP.get(aspect_key, aspect_key)
    return (
        "The final infographic image is still missing. Use "
        f"`{rel_prompt}` and call `generate_image_from_promptfile` to create "
        f"`{rel_image}` with aspect_ratio `{aspect_ratio}`. Reply only after "
        "the image file exists."
    )


def slide_deck_followup_task(prep: PreparedSkillWorkspace) -> str:
    """Nudge the model to run image generation for slide prompts."""
    ws = prep.workspace
    rel_prompts = workspace_relative(ws, prep.output_dir / "prompts")
    rel_out = workspace_relative(ws, prep.output_dir)
    return (
        "Slide images are still missing. Use prompt files in "
        f"`{rel_prompts}` and call `generate_image_from_promptfile` for "
        f"each slide; write images into `{rel_out}`."
    )


def podcast_script_followup_task(prep: PreparedSkillWorkspace) -> str:
    """Nudge the model to write script.json."""
    ws = prep.workspace
    rel_script = workspace_relative(ws, prep.output_dir / "script.json")
    return (
        f"The podcast script JSON is still missing. Create `{rel_script}` "
        "now with `write_file` using valid JSON per podcast-generation "
        "SKILL.md (title, locale, lines array with male/female speakers)."
    )


def backup_infographic_artifacts(output_dir: Path) -> None:
    """Back up files that a full infographic run may overwrite."""
    backup_if_exists(output_dir / "analysis.md")
    backup_if_exists(output_dir / "structured-content.md")
    prompt_file = output_dir / "prompts" / "infographic.md"
    backup_if_exists(prompt_file)
    backup_if_exists(output_dir / "infographic.png")


def backup_slide_deck_artifacts(output_dir: Path) -> None:
    """Back up slide-deck outputs before a new run."""
    backup_if_exists(output_dir / "analysis.md")
    backup_if_exists(output_dir / "outline.md")
    prompts_dir = output_dir / "prompts"
    if prompts_dir.exists():
        for prompt_file in sorted(prompts_dir.glob("*.md")):
            backup_if_exists(prompt_file)
    for image_file in sorted(output_dir.glob("*-slide-*.png")):
        backup_if_exists(image_file)


def backup_podcast_artifacts(output_dir: Path) -> None:
    """Back up podcast outputs before a new run."""
    backup_if_exists(output_dir / "script.json")
    backup_if_exists(output_dir / "podcast.wav")
    backup_if_exists(output_dir / "transcript.md")
