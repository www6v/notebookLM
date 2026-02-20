"""Mind map generation service.

This service generates mind maps from selected documents. The original documents
are stored in OBS (Object Storage Service), while the mind map itself is stored
in the database as structured graph data.
"""

import json
import logging

logger = logging.getLogger(__name__)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import chat_completion, vision_chat_completion_with_url
from app.models.source import Source
from app.models.studio import MindMap
from app.services.obs_storage import download_file_from_obs, generate_presigned_url
# from app.api.sources import _extract_text
from app.services.source_service import extract_text

# Max characters per source to include in combined content for LLM.
_MAX_CONTENT_PER_SOURCE = 3000


async def _fetch_sources_for_mindmap(
    db: AsyncSession,
    notebook_id: str,
    source_ids: list[str] | None = None,
) -> list[Source]:
    """Load active sources for a notebook, optionally filtered by source_ids."""
    stmt = select(Source).where(
        Source.notebook_id == notebook_id,
        Source.is_active.is_(True),
    )
    if source_ids:
        stmt = stmt.where(Source.id.in_(source_ids))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_single_source_content(source: Source) -> str | None:
    """Get text content for one source from raw_content, OBS file, or vision API.

    Returns content string (suitable for mind map), or None if unavailable.
    """
    raw_content = source.raw_content
    if raw_content is not None:
        return raw_content[:_MAX_CONTENT_PER_SOURCE] if raw_content else None

    if not source.file_path:
        return None

    try:
        if source.type == "image":
            prompt = (
                "请详细描述这张图片的内容，包括主要物体、文字、"
                "布局和关键信息，输出纯文本便于后续生成思维导图。"
            )
            try:
                image_url = generate_presigned_url(
                    source.file_path, expiration=3600
                )
                logger.info("image_url: %s", image_url)
                raw_content = await vision_chat_completion_with_url(
                    image_url,
                    prompt,
                    temperature=0.3,
                    max_tokens=2048,
                )
                if not raw_content:
                    raw_content = "[Image description unavailable]"
            except Exception as vision_err:
                logger.warning(
                    "Vision API failed for image '%s': %s",
                    source.title,
                    vision_err,
                )
                raw_content = "[Image description unavailable]"
            return raw_content[:_MAX_CONTENT_PER_SOURCE]

        file_bytes = download_file_from_obs(source.file_path)
        raw_content = extract_text(file_bytes, source.type)
        return raw_content[:_MAX_CONTENT_PER_SOURCE] if raw_content else None
    except RuntimeError as e:
        logger.error(
            "Failed to download content from OBS for source '%s': %s",
            source.title,
            str(e),
        )
        return None
    except Exception as e:
        logger.error(
            "Unexpected error getting content for source '%s': %s",
            source.title,
            str(e),
        )
        fallback = (source.raw_content or "")[:_MAX_CONTENT_PER_SOURCE]
        if fallback:
            logger.info("Using fallback content for source '%s'", source.title)
        return fallback if fallback else None


async def _build_combined_content_from_sources(
    sources: list[Source],
) -> str:
    """Build a single combined text from multiple sources for mind map LLM."""
    parts = []
    for source in sources:
        content = await _get_single_source_content(source)
        if not content:
            logger.warning(
                "No content available for source '%s', skipping",
                source.title,
            )
            continue
        logger.info(
            "Source '%s' content length: %s characters",
            source.title,
            len(content),
        )
        logger.info(
            "Source '%s' content preview: %s",
            source.title,
            content[:500],
        )
        parts.append(f"[{source.title}]: {content}")
    return "\n\n".join(parts)


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

    sources = await _fetch_sources_for_mindmap(db, notebook_id, source_ids)
    logger.info(
        "Found %s sources from OBS for mind map generation",
        len(sources),
    )

    combined_content = await _build_combined_content_from_sources(sources)
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
