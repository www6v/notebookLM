"""Infographic generation service."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import chat_completion
from app.models.source import Source
from app.models.studio import Infographic


TEMPLATE_PROMPTS = {
    "timeline": "Extract key events/milestones and arrange them chronologically.",
    "comparison": "Identify 2-3 items/concepts to compare side-by-side with pros/cons.",
    "process": "Break down the content into sequential steps or phases.",
    "statistics": "Extract key numbers, percentages, and data points.",
    "hierarchy": "Organize the content into a hierarchical structure (categories and sub-items).",
}


async def generate_infographic(
    db: AsyncSession,
    notebook_id: str,
    title: str = "Infographic",
    template_type: str = "timeline",
    source_ids: list[str] | None = None,
    focus_topic: str | None = None,
    output_language: str = "简体中文",
) -> Infographic:
    """Generate infographic data by asking the LLM to extract structured data."""
    stmt = select(Source).where(
        Source.notebook_id == notebook_id,
        Source.is_active.is_(True),
    )
    if source_ids:
        stmt = stmt.where(Source.id.in_(source_ids))

    result = await db.execute(stmt)
    sources = result.scalars().all()

    combined_content = "\n\n".join(
        f"[{s.title}]: {(s.raw_content or '')[:3000]}" for s in sources
    )

    template_instruction = TEMPLATE_PROMPTS.get(template_type, TEMPLATE_PROMPTS["timeline"])
    focus_instruction = f"\nFocus on: {focus_topic}" if focus_topic else ""

    messages = [
        {
            "role": "system",
            "content": f"""Extract structured data from the content for a {template_type} infographic.
{template_instruction}{focus_instruction}
Write all titles, headings, labels, and descriptions in this language: {output_language}.

Return ONLY valid JSON:
{{
  "title": "Infographic Title",
  "subtitle": "Brief description",
  "sections": [
    {{
      "heading": "Section heading",
      "items": [
        {{"label": "Item label", "value": "Item value/description", "icon": "optional_icon_name"}}
      ]
    }}
  ],
  "color_scheme": "blue"
}}

Create 3-6 sections with 2-4 items each.""",
        },
        {"role": "user", "content": combined_content or "No source content available."},
    ]

    try:
        response = await chat_completion(messages, temperature=0.3, max_tokens=4096)
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        layout_data = json.loads(content)
    except Exception:
        layout_data = {
            "title": title,
            "subtitle": "Data extraction failed",
            "sections": [],
            "color_scheme": "blue",
        }

    infographic = Infographic(
        notebook_id=notebook_id,
        title=title,
        template_type=template_type,
        layout_data=layout_data,
        status="ready",
        output_language=output_language,
    )
    db.add(infographic)
    await db.flush()
    await db.refresh(infographic)
    return infographic
