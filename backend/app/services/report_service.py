"""Report generation service.

Generates reports (briefing doc, study guide, blog post, custom) from notebook
sources via LLM. The generated content is stored as Markdown text in the
Report model.
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from langfuse import observe, propagate_attributes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import chat_completion
from app.config import settings
from app.models.studio import Report
from app.schemas.studio import ReportStatus
from app.services.source_service import (
    build_combined_content_from_sources,
    fetch_sources,
)
from app.services.studio_status_service import (
    clear_generation_error,
    mark_generation_as_error,
)

logger = logging.getLogger(__name__)


def _sanitize_text_for_mysql_utf8mb3(text: str) -> str:
    """Remove 4-byte Unicode chars unsupported by utf8mb3 columns.

    Some MySQL deployments still use utf8/utf8mb3 at table/column level.
    In that case, characters above U+FFFF (for example many emoji) trigger
    DataError 1366 during INSERT/UPDATE.
    """
    return "".join(ch for ch in text if ord(ch) <= 0xFFFF)


def _render_report_system_prompt(
    report_format: str = "briefing_doc",
    report_language: str = "简体中文",
    custom_prompt: str | None = None,
) -> str:
    """Render report system prompt from Jinja2 template."""
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    env = Environment(
        autoescape=select_autoescape(default_for_string=False),
        loader=FileSystemLoader(template_dir),
    )
    template = env.get_template("report_system_prompt.txt")
    return template.render(
        report_format=report_format,
        report_language=report_language,
        custom_prompt=custom_prompt or "",
    )


@observe(name="run_report_generation_for_existing", as_type="generation")
async def run_report_generation_for_existing(
    db: AsyncSession,
    report_id: str,
    source_ids: list[str] | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
) -> Report:
    """Run report generation for an existing pending Report record.

    Fetches sources, builds combined content, generates a Markdown report via
    LLM, then updates the Report with content and status=ready. On error sets
    status=error.
    """
    with propagate_attributes(
        user_id=user_id or "",
        session_id=session_id or report_id,
        metadata={"llm": settings.litellm_model},
    ):
        result = await db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        if report is None:
            raise ValueError(f"Report not found: {report_id}")

        report.status = ReportStatus.PROCESSING.value
        clear_generation_error(report)
        await db.flush()

        try:
            sources = await fetch_sources(
                db, report.notebook_id, source_ids
            )
            logger.info(
                "Found %s sources for report %s", len(sources), report_id
            )

            combined_content = await build_combined_content_from_sources(
                sources
            )
            if not combined_content.strip():
                report.status = ReportStatus.ERROR.value
                await db.flush()
                raise ValueError(
                    "No usable content from selected sources for report."
                )

            system_prompt = _render_report_system_prompt(
                report_format=report.report_format or "briefing_doc",
                report_language=report.report_language or "简体中文",
                custom_prompt=report.report_custom_prompt,
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": combined_content},
            ]

            logger.info("Sending request to LLM for report generation")
            response = await chat_completion(
                messages,
                model=settings.litellm_model,
                temperature=0.3,
                max_tokens=8192,
                user_id=user_id,
                session_id=session_id or report_id,
            )
            content = response.choices[0].message.content
            sanitized_content = _sanitize_text_for_mysql_utf8mb3(
                content.strip() if content else ""
            )
            if content and len(sanitized_content) != len(content.strip()):
                logger.warning(
                    "Report %s content contains unsupported utf8mb3 chars; "
                    "they were removed before saving.",
                    report_id,
                )
            report.content = sanitized_content
            report.status = ReportStatus.READY.value
            clear_generation_error(report)
            await db.flush()
            logger.info(
                "Report %s generated successfully, content length: %s",
                report_id,
                len(report.content),
            )
            return report
        except Exception as exc:
            mark_generation_as_error(
                report,
                "report generation failed",
                str(exc),
            )
            await db.flush()
            logger.exception("Report generation failed for report %s", report_id)
            raise
