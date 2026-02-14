"""Mind map generation service."""

import json
import logging

logger = logging.getLogger(__name__)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import chat_completion
from app.models.source import Source
from app.models.studio import MindMap


async def generate_mindmap_from_sources(
    db: AsyncSession,
    notebook_id: str,
    title: str = "Mind Map",
    source_ids: list[str] | None = None,
) -> MindMap:
    """Generate a mind map by asking the LLM to extract key concepts."""
    # Gather source content
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

    if not combined_content.strip():
        graph_data = {"nodes": [], "edges": []}
    else:
        messages = [
            {
                "role": "system",
                "content": """Analyze the provided content and generate a mind map structure as JSON.
Return ONLY valid JSON with this format:
{
  "nodes": [{"id": "1", "label": "Main Topic"}, ...],
  "edges": [{"source": "1", "target": "2"}, ...]
}
Create a central node for the main theme and branch out to sub-topics. Maximum 20 nodes.""",
            },
            {"role": "user", "content": combined_content},
        ]

        try:
            response = await chat_completion(messages, temperature=0.3)
            content = response.choices[0].message.content
            # Try to parse JSON from the response
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            graph_data = json.loads(content)
            logger.info("graph_data: %s", graph_data)
        except Exception:
            graph_data = {
                "nodes": [{"id": "1", "label": title}],
                "edges": [],
            }

    mind_map = MindMap(
        notebook_id=notebook_id,
        title=title,
        graph_data=graph_data,
    )
    db.add(mind_map)
    await db.flush()
    await db.refresh(mind_map)
    return mind_map
