"""LLM execution helpers for the skill runtime."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from json_repair import loads as json_repair_loads

from app.ai.llm_router import tool_chat_completion

from .loader import SkillLoader
from .prompt_builder import SkillPromptBuilder
from .tool_policy import tool_allowlist_for_skill
from .tools import SkillToolRuntime


def _strip_optional_json_fence(text: str) -> str:
    """Remove a leading/trailing markdown code fence if present."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


@dataclass(frozen=True)
class SkillRunResult:
    """Result from one skill-driven LLM execution."""

    model: str
    system_prompt: str
    user_message: str
    content: str
    finish_reason: str | None
    tool_transcript: tuple[str, ...] = ()


def merge_skill_run_results(
    primary: SkillRunResult,
    follow_up: SkillRunResult,
) -> SkillRunResult:
    """Chain tool transcripts; take final content from the follow-up run."""
    return SkillRunResult(
        model=follow_up.model,
        system_prompt=follow_up.system_prompt,
        user_message=follow_up.user_message,
        content=follow_up.content,
        finish_reason=follow_up.finish_reason,
        tool_transcript=primary.tool_transcript + follow_up.tool_transcript,
    )


class OpenAISkillExecutor:
    """Execute a skill-driven task through the backend LiteLLM runtime."""

    def __init__(
        self,
        workspace: Path,
        loader: SkillLoader,
        prompt_builder: SkillPromptBuilder,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 120.0,
        max_tool_rounds: int = 12,
        image_provider: str | None = None,
        image_model: str | None = None,
        image_quality: str = "2k",
        image_api_key: str | None = None,
    ) -> None:
        self.workspace = workspace.resolve()
        self.loader = loader
        self.prompt_builder = prompt_builder
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_tool_rounds = max_tool_rounds
        self.image_provider = image_provider
        self.image_model = image_model
        self.image_quality = image_quality
        self.image_api_key = image_api_key

    async def run(
        self,
        *,
        skill_name: str,
        task: str,
        options: dict[str, str] | None = None,
        attachments: list[str] | None = None,
        model: str,
        selected_skills: list[str] | None = None,
        temperature: float | None = None,
        max_completion_tokens: int | None = None,
    ) -> SkillRunResult:
        """Run one skill task using chat completions."""
        skill = self.loader.get_skill(skill_name)
        if skill is None:
            raise FileNotFoundError(f"Skill not found: {skill_name}")

        full_skill_names = list(
            dict.fromkeys([skill_name, *(selected_skills or [])])
        )
        references_summary = self.loader.build_references_summary(
            skill_name,
            variables=options or {},
        )
        system_prompt = self.prompt_builder.build_system_prompt(
            self.loader,
            primary_skill_name=skill_name,
            full_skill_names=full_skill_names,
        )
        user_message = self.prompt_builder.build_task_message(
            skill=skill,
            task=task,
            options=options,
            attachments=attachments,
            references_summary=references_summary,
        )

        tool_runtime = SkillToolRuntime(
            self.workspace,
            self.loader,
            current_skill_name=skill_name,
            current_variables=options or {},
            allowed_tool_names=tool_allowlist_for_skill(skill_name),
            image_provider=self.image_provider,
            image_model=self.image_model,
            image_quality=self.image_quality,
            image_api_key=self.image_api_key,
        )
        tool_specs = tool_runtime.get_tool_specs()
        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        tool_transcript: list[str] = []
        finish_reason: str | None = None
        content = ""

        for _ in range(self.max_tool_rounds):
            response = await tool_chat_completion(
                messages=messages,
                tools=tool_specs,
                model=model,
                temperature=temperature,
                max_tokens=max_completion_tokens,
            )
            choice = response.choices[0]
            message = choice.message
            finish_reason = choice.finish_reason
            content = self._coerce_message_content(getattr(message, "content", ""))
            tool_calls = message.tool_calls or []

            assistant_message = {
                "role": "assistant",
                "content": content,
            }
            if tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in tool_calls
                ]
            messages.append(assistant_message)

            if not tool_calls:
                break

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                raw_arguments = tool_call.function.arguments or "{}"
                arguments = self._parse_tool_arguments(raw_arguments)
                result = await tool_runtime.execute(tool_name, arguments)
                tool_transcript.append(
                    f"{tool_name}({raw_arguments}) -> {result[:1000]}"
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
        else:
            content = (
                "Stopped after reaching the maximum number of tool rounds "
                f"({self.max_tool_rounds})."
            )

        return SkillRunResult(
            model=model,
            system_prompt=system_prompt,
            user_message=user_message,
            content=content,
            finish_reason=finish_reason,
            tool_transcript=tuple(tool_transcript),
        )

    def _coerce_message_content(self, content) -> str:
        """Normalize LiteLLM/OpenAI message content to plain text."""
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        parts.append(str(text))
                else:
                    parts.append(str(item))
            return "\n".join(part for part in parts if part)
        return str(content)

    def _parse_tool_arguments(self, raw_arguments: str) -> dict:
        """Parse tool-call arguments; tolerate LLM JSON defects.

        Models often emit invalid JSON in tool arguments: unescaped
        newlines inside strings, truncated output when max_tokens cuts
        mid-string, or stray markdown fences. Strict ``json.loads`` and
        ``raw_decode`` cannot fix unterminated strings; ``json_repair``
        recovers common cases.
        """
        raw = (raw_arguments or "").strip()
        if not raw:
            return {}
        raw = _strip_optional_json_fence(raw)
        parsed: object
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            try:
                parsed = json_repair_loads(raw)
            except Exception as exc:
                snippet = raw[:240] + ("..." if len(raw) > 240 else "")
                raise ValueError(
                    "Invalid tool arguments JSON (repair failed): "
                    f"{exc}; snippet={snippet!r}"
                ) from exc
        if isinstance(parsed, dict):
            return parsed
        raise ValueError(
            "Tool arguments must decode to a JSON object; "
            f"got {type(parsed).__name__}"
        )
