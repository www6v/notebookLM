"""Mind map generation service.

This service generates mind maps from selected documents. The original documents
are stored in OBS (Object Storage Service), while the mind map itself is stored
in the database as structured graph data.
"""

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import chat_completion
from app.models.studio import MindMap
from app.schemas.studio import MindMapStatus
from app.services.source_service import (
    build_combined_content_from_sources,
    fetch_sources,
)

logger = logging.getLogger(__name__)


async def _create_and_persist_mindmap(
    db: AsyncSession,
    notebook_id: str,
    title: str,
    graph_data: dict,
) -> MindMap:
    """Create a MindMap entity, persist it, and return the refreshed instance."""
    mind_map = MindMap(
        notebook_id=notebook_id,
        title=title,
        graph_data=graph_data,
    )
    db.add(mind_map)
    await db.flush()
    await db.refresh(mind_map)
    return mind_map


async def _build_graph_data_from_content(
    combined_content: str,
    title: str,
) -> dict:
    """Build mind map graph data (nodes/edges) from combined text via LLM.

    Returns empty graph if content is empty; otherwise calls LLM and parses JSON.
    On LLM/parse error, returns a single-node graph with the given title.
    """
    if not combined_content.strip():
        logger.warning("No content found in sources from OBS, creating empty mind map")
        return {"nodes": [], "edges": []}

    logger.info(
        "Combined content length from OBS documents: %s characters",
        len(combined_content),
    )
    logger.info("Combined content preview: %s", combined_content[:1000])

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
        logger.info(
            "Sending request to LLM for mind map generation from OBS document content"
        )
        response = await chat_completion(messages, temperature=0.3)
        content = response.choices[0].message.content
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        graph_data = json.loads(content)
        logger.info("Successfully parsed graph data from LLM response")
        logger.info("graph_data: %s", graph_data)
        return graph_data
    except Exception as e:
        logger.error("Error processing LLM response: %s", str(e))
        return {
            "nodes": [{"id": "1", "label": title}],
            "edges": [],
        }


async def generate_mindmap_from_sources(
    db: AsyncSession,
    notebook_id: str,
    title: str = "Mind Map",
    source_ids: list[str] | None = None,
) -> MindMap:
    """Generate a mind map by asking the LLM to extract key concepts from selected sources.

    Note: The original documents are stored in OBS (Object Storage Service),
    while the mind map itself is stored in the database as structured graph data.
    """
    logger.info(
        "Starting mind map generation for notebook_id: %s, title: %s, source_ids: %s",
        notebook_id,
        title,
        source_ids,
    )

    sources = await fetch_sources(db, notebook_id, source_ids)
    logger.info(
        "Found %s sources from OBS for mind map generation",
        len(sources),
    )

    combined_content = await build_combined_content_from_sources(sources)
    if not combined_content.strip():
        raise ValueError(
            "No usable content from selected sources for mind map. "
            "Ensure documents have content or retry after video understanding is available."
        )
    graph_data = await _build_graph_data_from_content(combined_content, title)

    logger.info(
        "Creating mind map with %s nodes and %s edges",
        len(graph_data["nodes"]),
        len(graph_data["edges"]),
    )

    mind_map = await _create_and_persist_mindmap(
        db, notebook_id, title, graph_data
    )
    logger.info(
        "Mind map created successfully with ID: %s and stored in database",
        mind_map.id,
    )
    return mind_map


async def run_mindmap_generation_for_existing(
    db: AsyncSession,
    mindmap_id: str,
    source_ids: list[str] | None = None,
) -> MindMap:
    """Run mind map generation for an existing pending MindMap record.

    Fetches sources, builds content, generates graph data via LLM, then updates
    the MindMap with graph_data and status=ready. On error sets status=error.
    """
    result = await db.execute(select(MindMap).where(MindMap.id == mindmap_id))
    mind_map = result.scalar_one_or_none()
    if mind_map is None:
        raise ValueError(f"MindMap not found: {mindmap_id}")

    mind_map.status = MindMapStatus.PROCESSING.value
    await db.flush()

    try:
        sources = await fetch_sources(
            db, mind_map.notebook_id, source_ids
        )
        logger.info(
            "Found %s sources for mind map %s",
            len(sources),
            mindmap_id,
        )
        combined_content = await build_combined_content_from_sources(sources)
        if not combined_content.strip():
            mind_map.status = MindMapStatus.ERROR.value
            await db.flush()
            raise ValueError(
                "No usable content from selected sources for mind map."
            )
        graph_data = await _build_graph_data_from_content(
            combined_content, mind_map.title
        )
        mind_map.graph_data = graph_data
        mind_map.status = MindMapStatus.READY.value
        await db.flush()
        logger.info(
            "Mind map %s updated with %s nodes, %s edges",
            mindmap_id,
            len(graph_data.get("nodes", [])),
            len(graph_data.get("edges", [])),
        )
        return mind_map
    except Exception:
        mind_map.status = MindMapStatus.ERROR.value
        await db.flush()
        raise
