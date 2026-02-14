"""Slide deck generation service."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import chat_completion
from app.models.source import Source
from app.models.studio import SlideDeck


async def generate_slide_deck(
    db: AsyncSession,
    notebook_id: str,
    title: str = "Slide Deck",
    theme: str = "light",
    source_ids: list[str] | None = None,
    focus_topic: str | None = None,
) -> SlideDeck:
    """Generate a slide deck by asking the LLM to structure content into slides."""
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

    focus_instruction = ""
    if focus_topic:
        focus_instruction = f"\nFocus specifically on: {focus_topic}"

    messages = [
        {
            "role": "system",
            "content": f"""Create a slide deck from the provided content. Return ONLY valid JSON.
{focus_instruction}

Format:
{{
  "slides": [
    {{
      "slide_number": 1,
      "title": "Slide Title",
      "content": ["Bullet point 1", "Bullet point 2"],
      "speaker_notes": "Notes for the presenter",
      "layout": "title"
    }},
    ...
  ]
}}

Layout types: "title" (for title slide), "content" (for regular slides), "two_column", "image_text".
Create 8-12 slides. First slide should be a title slide, last slide a summary/conclusion.""",
        },
        {"role": "user", "content": combined_content or "No source content available."},
    ]

    try:
        response = await chat_completion(messages, temperature=0.3, max_tokens=4096)
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        slides_data = json.loads(content)
    except Exception:
        slides_data = {
            "slides": [
                {
                    "slide_number": 1,
                    "title": title,
                    "content": ["Content generation failed. Please try again."],
                    "speaker_notes": "",
                    "layout": "title",
                }
            ]
        }

    slide_deck = SlideDeck(
        notebook_id=notebook_id,
        title=title,
        theme=theme,
        slides_data=slides_data,
        status="ready",
    )
    db.add(slide_deck)
    await db.flush()
    await db.refresh(slide_deck)
    return slide_deck
