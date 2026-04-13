#!/usr/bin/env python3
"""Skill runtime entrypoints for backend workflows."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
import sys

try:
    from agent.skill_runtime import (
        OpenAISkillExecutor,
        SkillAgentLoop,
        SkillLoader,
        SkillPromptBuilder,
        SkillRunResult,
        WorkflowStageResult,
        merge_skill_run_results,
    )
    from agent.skill_runtime.agent_tasks import (
        INFOGRAPHIC_STAGES,
        PODCAST_STAGES,
        SLIDE_DECK_STAGES,
        backup_infographic_artifacts,
        backup_podcast_artifacts,
        backup_slide_deck_artifacts,
        build_infographic_agent_task,
        build_podcast_agent_task,
        build_slide_deck_agent_task,
        infographic_artifact_followup_task,
        infographic_followup_task,
        podcast_script_followup_task,
        prepare_skill_workspace,
        slide_deck_followup_task,
    )
    from agent.skill_runtime.podcast_finalize import (
        finalize_podcast_script_json_file,
        run_podcast_audio_generation,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - script fallback
    if exc.name not in {
        "agent",
        "agent.skill_runtime",
        "agent.skill_runtime.agent_tasks",
        "agent.skill_runtime.podcast_finalize",
    }:
        raise
    from skill_runtime import (
        OpenAISkillExecutor,
        SkillAgentLoop,
        SkillLoader,
        SkillPromptBuilder,
        SkillRunResult,
        WorkflowStageResult,
        merge_skill_run_results,
    )
    from skill_runtime.agent_tasks import (
        INFOGRAPHIC_STAGES,
        PODCAST_STAGES,
        SLIDE_DECK_STAGES,
        backup_infographic_artifacts,
        backup_podcast_artifacts,
        backup_slide_deck_artifacts,
        build_infographic_agent_task,
        build_podcast_agent_task,
        build_slide_deck_agent_task,
        infographic_artifact_followup_task,
        infographic_followup_task,
        podcast_script_followup_task,
        prepare_skill_workspace,
        slide_deck_followup_task,
    )
    from skill_runtime.podcast_finalize import (
        finalize_podcast_script_json_file,
        run_podcast_audio_generation,
    )


@dataclass(frozen=True)
class SkillWorkflowRequest:
    """Programmatic request for running a bundled skill workflow (agent loop)."""

    skill_name: str
    source: str
    output_dir: str
    through_stage: str = "image"
    options: dict[str, str] = field(default_factory=dict)
    model: str | None = None
    temperature: float | None = None
    max_completion_tokens: int | None = None


def default_workspace() -> Path:
    """Return the backend root used by the skill runtime."""
    return Path(__file__).resolve().parent.parent


def _primary_output_path(
    skill_name: str,
    through_stage: str,
    output_dir: Path,
) -> Path:
    """Primary artifact path reported in WorkflowStageResult."""
    if skill_name == "baoyu-infographic":
        if through_stage == "analysis":
            return output_dir / "analysis.md"
        if through_stage == "structured":
            return output_dir / "structured-content.md"
        if through_stage == "prompt":
            return output_dir / "prompts" / "infographic.md"
        return output_dir / "infographic.png"
    if skill_name == "baoyu-slide-deck":
        if through_stage == "analysis":
            return output_dir / "analysis.md"
        if through_stage == "outline":
            return output_dir / "outline.md"
        if through_stage == "prompt":
            return output_dir / "prompts"
        return output_dir
    if skill_name == "podcast-generation":
        if through_stage == "script":
            return output_dir / "script.json"
        return output_dir / "podcast.wav"
    raise ValueError(f"Unsupported workflow skill: {skill_name}")


def _validate_infographic_artifacts(
    output_dir: Path,
    through_stage: str,
) -> None:
    if through_stage == "analysis":
        path = output_dir / "analysis.md"
    elif through_stage == "structured":
        path = output_dir / "structured-content.md"
    elif through_stage == "prompt":
        path = output_dir / "prompts" / "infographic.md"
    elif through_stage == "image":
        path = output_dir / "infographic.png"
    else:
        raise ValueError(f"Unsupported through_stage: {through_stage}")
    if not path.exists():
        raise FileNotFoundError(
            f"Infographic stage `{through_stage}` did not create: {path}"
        )


def _validate_slide_deck_artifacts(
    output_dir: Path,
    through_stage: str,
) -> None:
    if through_stage == "analysis":
        path = output_dir / "analysis.md"
        if not path.exists():
            raise FileNotFoundError(
                f"Slide deck stage `analysis` did not create: {path}"
            )
        return
    if through_stage == "outline":
        path = output_dir / "outline.md"
        if not path.exists():
            raise FileNotFoundError(
                f"Slide deck stage `outline` did not create: {path}"
            )
        return
    if through_stage == "prompt":
        prompt_files = list((output_dir / "prompts").glob("*.md"))
        if not prompt_files:
            raise FileNotFoundError(
                "Slide deck stage `prompt` did not create prompt files in "
                f"{output_dir / 'prompts'}"
            )
        return
    if through_stage == "image":
        image_files = list(output_dir.glob("*-slide-*.png"))
        if not image_files:
            raise FileNotFoundError(
                f"Slide deck stage `image` did not create slide images in "
                f"{output_dir}"
            )
        return
    raise ValueError(f"Unsupported through_stage: {through_stage}")


async def run_skill_workflow(
    request: SkillWorkflowRequest,
    workspace: Path | None = None,
) -> list:
    """Run a bundled skill workflow via SkillAgentLoop (single LLM session)."""
    if not request.model:
        raise ValueError("Workflow model is required.")
    resolved_workspace = (workspace or default_workspace()).expanduser().resolve()
    loader = SkillLoader(workspace=resolved_workspace)
    builder = SkillPromptBuilder(workspace=resolved_workspace)
    executor = OpenAISkillExecutor(
        workspace=resolved_workspace,
        loader=loader,
        prompt_builder=builder,
    )
    loop = SkillAgentLoop(resolved_workspace, executor)
    prep = prepare_skill_workspace(
        resolved_workspace,
        request.source,
        request.output_dir,
    )
    out_dir = prep.output_dir
    opt = dict(request.options or {})

    if request.skill_name == "baoyu-infographic":
        if request.through_stage not in INFOGRAPHIC_STAGES:
            raise ValueError(
                f"Unsupported through_stage for infographic: "
                f"{request.through_stage}"
            )
        backup_infographic_artifacts(out_dir)
        (out_dir / "prompts").mkdir(parents=True, exist_ok=True)
        task, attachments = build_infographic_agent_task(
            prep,
            through_stage=request.through_stage,
            options=opt,
        )
        result = await loop.run(
            skill_name="baoyu-infographic",
            task=task,
            options=opt,
            attachments=attachments,
            model=request.model,
            temperature=request.temperature,
            max_completion_tokens=request.max_completion_tokens,
        )
        artifact_fu = infographic_artifact_followup_task(
            prep, request.through_stage
        )
        if artifact_fu is not None:
            target = _primary_output_path(
                request.skill_name,
                request.through_stage,
                out_dir,
            )
            for _ in range(2):
                if target.exists():
                    break
                follow = await loop.run(
                    skill_name="baoyu-infographic",
                    task=artifact_fu,
                    options=opt,
                    attachments=attachments,
                    model=request.model,
                    temperature=request.temperature,
                    max_completion_tokens=request.max_completion_tokens,
                )
                result = merge_skill_run_results(result, follow)
        if request.through_stage == "image":
            transcript_joined = "\n".join(result.tool_transcript)
            if "generate_image_from_promptfile" not in transcript_joined:
                img_fu = infographic_followup_task(
                    prep,
                    through_stage=request.through_stage,
                    options=opt,
                )
                if img_fu:
                    rel_prompt = str(
                        (out_dir / "prompts" / "infographic.md").relative_to(
                            resolved_workspace
                        )
                    )
                    follow = await loop.run(
                        skill_name="baoyu-infographic",
                        task=img_fu,
                        options=opt,
                        attachments=[rel_prompt],
                        model=request.model,
                        temperature=request.temperature,
                        max_completion_tokens=request.max_completion_tokens,
                    )
                    result = merge_skill_run_results(result, follow)
        _validate_infographic_artifacts(out_dir, request.through_stage)
        primary = _primary_output_path(
            request.skill_name,
            request.through_stage,
            out_dir,
        )
        return [
            WorkflowStageResult(
                stage=request.through_stage,
                output_path=primary,
                llm_result=result,
            )
        ]

    if request.skill_name == "baoyu-slide-deck":
        if request.through_stage not in SLIDE_DECK_STAGES:
            raise ValueError(
                f"Unsupported through_stage for slide deck: "
                f"{request.through_stage}"
            )
        backup_slide_deck_artifacts(out_dir)
        (out_dir / "prompts").mkdir(parents=True, exist_ok=True)
        task, attachments = build_slide_deck_agent_task(
            prep,
            through_stage=request.through_stage,
            options=opt,
        )
        result = await loop.run(
            skill_name="baoyu-slide-deck",
            task=task,
            options=opt,
            attachments=attachments,
            model=request.model,
            temperature=request.temperature,
            max_completion_tokens=request.max_completion_tokens,
        )
        if request.through_stage == "image":
            transcript_joined = "\n".join(result.tool_transcript)
            if "generate_image_from_promptfile" not in transcript_joined:
                img_fu = slide_deck_followup_task(prep)
                rel_outline = str(
                    (out_dir / "outline.md").relative_to(resolved_workspace)
                )
                follow = await loop.run(
                    skill_name="baoyu-slide-deck",
                    task=img_fu,
                    options=opt,
                    attachments=[rel_outline],
                    model=request.model,
                    temperature=request.temperature,
                    max_completion_tokens=request.max_completion_tokens,
                )
                result = merge_skill_run_results(result, follow)
        _validate_slide_deck_artifacts(out_dir, request.through_stage)
        primary = _primary_output_path(
            request.skill_name,
            request.through_stage,
            out_dir,
        )
        return [
            WorkflowStageResult(
                stage=request.through_stage,
                output_path=primary,
                llm_result=result,
            )
        ]

    if request.skill_name == "podcast-generation":
        if request.through_stage not in PODCAST_STAGES:
            raise ValueError(
                f"Unsupported through_stage for podcast: {request.through_stage}"
            )
        backup_podcast_artifacts(out_dir)
        task, attachments = build_podcast_agent_task(
            prep,
            through_stage=request.through_stage,
            options=opt,
        )
        result = await loop.run(
            skill_name="podcast-generation",
            task=task,
            options=opt,
            attachments=attachments,
            model=request.model,
            temperature=request.temperature,
            max_completion_tokens=request.max_completion_tokens,
        )
        script_path = out_dir / "script.json"
        for _ in range(2):
            if script_path.exists():
                break
            fu = podcast_script_followup_task(prep)
            follow = await loop.run(
                skill_name="podcast-generation",
                task=fu,
                options=opt,
                attachments=[str(prep.source_copy.relative_to(resolved_workspace))],
                model=request.model,
                temperature=request.temperature,
                max_completion_tokens=request.max_completion_tokens,
            )
            result = merge_skill_run_results(result, follow)
        if not script_path.exists():
            raise FileNotFoundError(
                f"Podcast stage `script` did not create: {script_path}"
            )
        finalize_podcast_script_json_file(script_path)
        results: list = [
            WorkflowStageResult(
                stage="script",
                output_path=script_path,
                llm_result=result,
            )
        ]
        if request.through_stage == "audio":
            wav_path = out_dir / "podcast.wav"
            transcript_path = out_dir / "transcript.md"
            await run_podcast_audio_generation(
                resolved_workspace,
                script_path=script_path,
                wav_path=wav_path,
                transcript_path=transcript_path,
            )
            if not wav_path.exists():
                raise FileNotFoundError(
                    f"Podcast stage `audio` did not create: {wav_path}"
                )
            placeholder = SkillRunResult(
                model="podcast-generation/audio",
                system_prompt="",
                user_message="",
                content=(
                    "Audio synthesized via "
                    "agent/skills/podcast-generation/scripts/generate.py."
                ),
                finish_reason="stop",
                tool_transcript=(),
            )
            results.append(
                WorkflowStageResult(
                    stage="audio",
                    output_path=wav_path,
                    llm_result=placeholder,
                )
            )
        return results

    raise ValueError(f"Unsupported workflow skill: {request.skill_name}")


# def parse_key_value(text: str) -> tuple[str, str]:
#     """Parse one key=value item."""
#     if "=" not in text:
#         raise argparse.ArgumentTypeError(
#             f"Invalid option format `{text}`. Expected key=value."
#         )
#     key, value = text.split("=", 1)
#     key = key.strip()
#     value = value.strip()
#     if not key:
#         raise argparse.ArgumentTypeError(
#             f"Invalid option format `{text}`. Empty key is not allowed."
#         )
#     return key, value


# def build_parser() -> argparse.ArgumentParser:
#     """Create CLI parser."""
#     parser = argparse.ArgumentParser(
#         description="Build a skill-driven execution prompt from SKILL.md"
#     )
#     parser.add_argument(
#         "--workspace",
#         default=".",
#         help="Workspace root used for workspace skill discovery",
#     )

#     subparsers = parser.add_subparsers(dest="command", required=True)

#     subparsers.add_parser(
#         "list",
#         help="List discovered skills",
#     )

#     context_parser = subparsers.add_parser(
#         "context",
#         help="Build a nanobot-style skill system prompt",
#     )
#     context_parser.add_argument(
#         "--select",
#         action="append",
#         default=[],
#         help="Skill name to inline fully; can be repeated",
#     )

#     refs_parser = subparsers.add_parser(
#         "refs",
#         help="List progressive-disclosure references for one skill",
#     )
#     refs_parser.add_argument("skill_name", help="Skill directory name")
#     refs_parser.add_argument(
#         "--option",
#         action="append",
#         default=[],
#         type=parse_key_value,
#         help="Resolution variable in key=value form; can be repeated",
#     )

#     ref_parser = subparsers.add_parser(
#         "ref",
#         help="Read one specific reference file for a skill",
#     )
#     ref_parser.add_argument("skill_name", help="Skill directory name")
#     ref_parser.add_argument(
#         "reference_path",
#         help="Relative reference path, for example references/base-prompt.md",
#     )
#     ref_parser.add_argument(
#         "--option",
#         action="append",
#         default=[],
#         type=parse_key_value,
#         help="Resolution variable in key=value form; can be repeated",
#     )

#     prompt_parser = subparsers.add_parser(
#         "prompt",
#         help="Build a skill-driven prompt for one skill",
#     )
#     prompt_parser.add_argument("skill_name", help="Skill directory name")
#     prompt_parser.add_argument(
#         "--task",
#         help="Task description",
#     )
#     prompt_parser.add_argument(
#         "--task-file",
#         help="Read task description from a file",
#     )
#     prompt_parser.add_argument(
#         "--option",
#         action="append",
#         default=[],
#         type=parse_key_value,
#         help="Skill parameter in key=value form; can be repeated",
#     )
#     prompt_parser.add_argument(
#         "--attach",
#         action="append",
#         default=[],
#         help="Referenced file path; can be repeated",
#     )
#     prompt_parser.add_argument(
#         "--output",
#         help="Write prompt to a file instead of stdout",
#     )

#     run_parser = subparsers.add_parser(
#         "run",
#         help="Execute one skill task through an OpenAI-compatible API",
#     )
#     run_parser.add_argument("skill_name", help="Skill directory name")
#     run_parser.add_argument(
#         "--task",
#         help="Task description",
#     )
#     run_parser.add_argument(
#         "--task-file",
#         help="Read task description from a file",
#     )
#     run_parser.add_argument(
#         "--option",
#         action="append",
#         default=[],
#         type=parse_key_value,
#         help="Skill parameter in key=value form; can be repeated",
#     )
#     run_parser.add_argument(
#         "--attach",
#         action="append",
#         default=[],
#         help="Referenced file path; can be repeated",
#     )
#     run_parser.add_argument(
#         "--model",
#         required=True,
#         help="OpenAI-compatible model name",
#     )
#     run_parser.add_argument(
#         "--api-key",
#         help="API key; defaults to OPENAI_API_KEY",
#     )
#     run_parser.add_argument(
#         "--base-url",
#         help="Base URL; defaults to OPENAI_BASE_URL",
#     )
#     run_parser.add_argument(
#         "--temperature",
#         type=float,
#         help="Optional sampling temperature",
#     )
#     run_parser.add_argument(
#         "--max-completion-tokens",
#         type=int,
#         help="Optional max completion tokens",
#     )
#     run_parser.add_argument(
#         "--select",
#         action="append",
#         default=[],
#         help="Extra skill names to inline into the system prompt; can be repeated",
#     )
#     run_parser.add_argument(
#         "--print-prompts",
#         action="store_true",
#         help="Print system/user prompts before the model response",
#     )
#     run_parser.add_argument(
#         "--print-tools",
#         action="store_true",
#         help="Print executed tool transcript before the model response",
#     )
#     run_parser.add_argument(
#         "--image-provider",
#         help="Default provider for generate_image_from_promptfile tool",
#     )
#     run_parser.add_argument(
#         "--image-model",
#         help="Default image model for generate_image_from_promptfile tool",
#     )
#     run_parser.add_argument(
#         "--image-quality",
#         default="2k",
#         help="Default image quality for generate_image_from_promptfile tool",
#     )
#     run_parser.add_argument(
#         "--image-api-key",
#         help="Default image API key for generate_image_from_promptfile tool",
#     )

#     workflow_parser = subparsers.add_parser(
#         "workflow",
#         help="Run a staged skill workflow with multiple tool-driven stages",
#     )
#     workflow_parser.add_argument(
#         "skill_name",
#         choices=["baoyu-infographic"],
#         help="Workflow-enabled skill name",
#     )
#     workflow_parser.add_argument(
#         "--source",
#         required=True,
#         help="Source file path inside the workspace",
#     )
#     workflow_parser.add_argument(
#         "--output-dir",
#         required=True,
#         help="Output directory inside the workspace",
#     )
#     workflow_parser.add_argument(
#         "--through-stage",
#         default="image",
#         choices=["analysis", "structured", "prompt", "image"],
#         help="Final stage to execute",
#     )
#     workflow_parser.add_argument(
#         "--option",
#         action="append",
#         default=[],
#         type=parse_key_value,
#         help="Skill parameter in key=value form; can be repeated",
#     )
#     workflow_parser.add_argument(
#         "--model",
#         required=True,
#         help="OpenAI-compatible model name",
#     )
#     workflow_parser.add_argument(
#         "--api-key",
#         help="API key; defaults to OPENAI_API_KEY",
#     )
#     workflow_parser.add_argument(
#         "--base-url",
#         help="Base URL; defaults to OPENAI_BASE_URL",
#     )
#     workflow_parser.add_argument(
#         "--temperature",
#         type=float,
#         help="Optional sampling temperature",
#     )
#     workflow_parser.add_argument(
#         "--max-completion-tokens",
#         type=int,
#         help="Optional max completion tokens",
#     )
#     workflow_parser.add_argument(
#         "--image-provider",
#         help="Default provider for generate_image_from_promptfile tool",
#     )
#     workflow_parser.add_argument(
#         "--image-model",
#         help="Default image model for generate_image_from_promptfile tool",
#     )
#     workflow_parser.add_argument(
#         "--image-quality",
#         default="2k",
#         help="Default image quality for generate_image_from_promptfile tool",
#     )
#     workflow_parser.add_argument(
#         "--image-api-key",
#         help="Default image API key for generate_image_from_promptfile tool",
#     )
#     workflow_parser.add_argument(
#         "--print-tools",
#         action="store_true",
#         help="Print tool transcript for each completed stage",
#     )

#     return parser


# def resolve_task(args: argparse.Namespace) -> str:
#     """Resolve task text from cli args."""
#     if args.task and args.task_file:
#         raise ValueError("Use either --task or --task-file, not both.")
#     if args.task:
#         return args.task
#     if args.task_file:
#         return Path(args.task_file).expanduser().read_text(encoding="utf-8").strip()
#     raise ValueError("One of --task or --task-file is required.")


# def cmd_list(loader: SkillLoader) -> int:
#     """Print discovered skills."""
#     skills = loader.list_skills()
#     if not skills:
#         print("No skills found.")
#         return 0

#     for info in skills:
#         print(
#             f"{info.name}\t{info.source}\t"
#             f"{'available' if info.available else 'unavailable'}\t{info.path}"
#         )
#     return 0


# def cmd_prompt(loader: SkillLoader, builder: SkillPromptBuilder, args: argparse.Namespace) -> int:
#     """Generate one prompt."""
#     skill = loader.get_skill(args.skill_name)
#     if skill is None:
#         print(f"Skill not found: {args.skill_name}", file=sys.stderr)
#         return 1

#     task = resolve_task(args)
#     options = dict(args.option)
#     references_summary = loader.build_references_summary(
#         skill.name,
#         variables=options,
#     )
#     prompt = builder.build_prompt(
#         skill=skill,
#         skill_content=loader.load_skill(skill.name),
#         task=task,
#         options=options,
#         attachments=args.attach,
#         references_summary=references_summary,
#     )

#     if args.output:
#         output_path = Path(args.output).expanduser()
#         output_path.write_text(prompt, encoding="utf-8")
#         print(output_path)
#         return 0

#     print(prompt)
#     return 0


# def cmd_context(loader: SkillLoader, builder: SkillPromptBuilder, args: argparse.Namespace) -> int:
#     """Print a nanobot-style system prompt for skill use."""
#     prompt = builder.build_system_prompt(
#         loader=loader,
#         selected_skills=args.select,
#     )
#     print(prompt)
#     return 0


# def cmd_refs(loader: SkillLoader, args: argparse.Namespace) -> int:
#     """Print progressive-disclosure references for one skill."""
#     skill = loader.get_skill(args.skill_name)
#     if skill is None:
#         print(f"Skill not found: {args.skill_name}", file=sys.stderr)
#         return 1

#     variables = dict(args.option)
#     summary = loader.build_references_summary(skill.name, variables=variables)
#     print(summary.rstrip() if summary else "No references found.")
#     return 0


# def cmd_ref(loader: SkillLoader, args: argparse.Namespace) -> int:
#     """Read one explicit reference file for a skill."""
#     variables = dict(args.option)
#     try:
#         content = loader.load_reference(
#             skill_name=args.skill_name,
#             reference_path=args.reference_path,
#             variables=variables,
#         )
#     except FileNotFoundError as exc:
#         print(str(exc), file=sys.stderr)
#         return 1

#     print(content)
#     return 0


# async def cmd_run(
#     loader: SkillLoader,
#     builder: SkillPromptBuilder,
#     workspace: Path,
#     args: argparse.Namespace,
# ) -> int:
#     """Execute one skill task through the backend LLM runtime."""
#     task = resolve_task(args)
#     try:
#         executor = OpenAISkillExecutor(
#             workspace=workspace,
#             loader=loader,
#             prompt_builder=builder,
#             api_key=args.api_key,
#             base_url=args.base_url,
#             image_provider=args.image_provider,
#             image_model=args.image_model,
#             image_quality=args.image_quality,
#             image_api_key=args.image_api_key,
#         )

#         result = await executor.run(
#             skill_name=args.skill_name,
#             task=task,
#             options=dict(args.option),
#             attachments=args.attach,
#             model=args.model,
#             selected_skills=args.select or [args.skill_name],
#             temperature=args.temperature,
#             max_completion_tokens=args.max_completion_tokens,
#         )
#     except (FileNotFoundError, ValueError) as exc:
#         print(str(exc), file=sys.stderr)
#         return 1

#     if args.print_prompts:
#         print("# System Prompt")
#         print()
#         print(result.system_prompt.rstrip())
#         print()
#         print("# User Message")
#         print()
#         print(result.user_message.rstrip())
#         print()
#         print("# Model Response")
#         print()

#     if args.print_tools and result.tool_transcript:
#         print("# Tool Transcript")
#         print()
#         for item in result.tool_transcript:
#             print(item)
#             print()
#         print("# Model Response")
#         print()

#     print(result.content)
#     return 0


# async def cmd_workflow(
#     loader: SkillLoader,
#     builder: SkillPromptBuilder,
#     workspace: Path,
#     args: argparse.Namespace,
# ) -> int:
#     """Execute a staged workflow for supported skills."""
#     if args.skill_name != "baoyu-infographic":
#         print(f"Unsupported workflow skill: {args.skill_name}", file=sys.stderr)
#         return 1

#     options = dict(args.option)
#     try:
#         executor = OpenAISkillExecutor(
#             workspace=workspace,
#             loader=loader,
#             prompt_builder=builder,
#             api_key=args.api_key,
#             base_url=args.base_url,
#             image_provider=args.image_provider,
#             image_model=args.image_model,
#             image_quality=args.image_quality,
#             image_api_key=args.image_api_key,
#         )
#         results = await run_skill_workflow(
#             SkillWorkflowRequest(
#                 skill_name=args.skill_name,
#                 source=args.source,
#                 output_dir=args.output_dir,
#                 through_stage=args.through_stage,
#                 options=options,
#                 model=args.model,
#                 temperature=args.temperature,
#                 max_completion_tokens=args.max_completion_tokens,
#             ),
#             workspace=workspace,
#         )
#     except (FileNotFoundError, ValueError) as exc:
#         print(str(exc), file=sys.stderr)
#         return 1

#     for result in results:
#         print(f"[stage:{result.stage}] {result.output_path}")
#         if args.print_tools and result.llm_result.tool_transcript:
#             for item in result.llm_result.tool_transcript:
#                 print(item)
#         print(result.llm_result.content.strip())
#         print()

#     return 0


# async def dispatch_command(
#     parser: argparse.ArgumentParser,
#     args: argparse.Namespace,
#     workspace: Path,
#     loader: SkillLoader,
#     builder: SkillPromptBuilder,
# ) -> int:
#     """Dispatch one parsed command."""
#     if args.command == "list":
#         return cmd_list(loader)
#     if args.command == "context":
#         return cmd_context(loader, builder, args)
#     if args.command == "refs":
#         return cmd_refs(loader, args)
#     if args.command == "ref":
#         return cmd_ref(loader, args)
#     if args.command == "prompt":
#         return cmd_prompt(loader, builder, args)
#     if args.command == "run":
#         return await cmd_run(loader, builder, workspace, args)
#     if args.command == "workflow":
#         return await cmd_workflow(loader, builder, workspace, args)

#     parser.error(f"Unsupported command: {args.command}")
#     return 2


# def main() -> int:
#     """CLI entry point kept for manual debugging."""
#     parser = build_parser()
#     args = parser.parse_args()

#     workspace = Path(args.workspace).expanduser().resolve()
#     loader = SkillLoader(workspace=workspace)
#     builder = SkillPromptBuilder(workspace=workspace)
#     return asyncio.run(dispatch_command(parser, args, workspace, loader, builder))


# if __name__ == "__main__":
#     raise SystemExit(main())
