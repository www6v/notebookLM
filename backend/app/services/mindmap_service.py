"""Mind map generation service.

This service generates mind maps from selected documents. The original documents
are stored in OBS (Object Storage Service), while the mind map itself is stored
in the database as structured graph data.
"""

import json
import logging

logger = logging.getLogger(__name__)

# Ensure the logger has a handler for console output
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import chat_completion, vision_chat_completion_with_url
from app.models.source import Source
from app.models.studio import MindMap
from app.services.obs_storage import download_file_from_obs, generate_presigned_url
from app.api.sources import _extract_text


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

    logger.info(f"Starting mind map generation for notebook_id: {notebook_id}, title: {title}, source_ids: {source_ids}")

    # Gather source content - these sources correspond to documents originally stored in OBS
    stmt = select(Source).where(
        Source.notebook_id == notebook_id,
        Source.is_active.is_(True),
    )
    if source_ids:
        stmt = stmt.where(Source.id.in_(source_ids))

    result = await db.execute(stmt)
    sources = result.scalars().all()

    logger.info(f"result:{result}")
    logger.info(f"sources:{sources}")

    logger.info(f"Found {len(sources)} sources from OBS for mind map generation")

    # Get content from each source using the same logic as get_source_content
    combined_content_parts = []
    for source in sources:
        try:
            raw_content = source.raw_content

            if raw_content is None and source.file_path:
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
                    else:
                        file_bytes = download_file_from_obs(source.file_path)
                        raw_content = _extract_text(file_bytes, source.type)
                except RuntimeError as e:
                    logger.error(
                        "Failed to download content from OBS for source "
                        "'%s': %s",
                        source.title,
                        str(e),
                    )
                    continue

            if raw_content:
                content_length = len(raw_content)
                logger.info(f"Source '{source.title}' content length: {content_length} characters")
                # Log first 500 characters of each source for debugging (truncated if necessary)
                content_preview = raw_content[:500]
                logger.info(f"Source '{source.title}' content preview: {content_preview}")

                # Add to combined content, limiting to first 3000 chars per source as before
                combined_content_parts.append(f"[{source.title}]: {raw_content[:3000]}")
            else:
                logger.warning(f"No content available for source '{source.title}', skipping")
        except Exception as e:
            logger.error(f"Unexpected error getting content for source '{source.title}': {str(e)}")
            # Fallback to raw_content if available, otherwise skip
            fallback_content = (source.raw_content or '')[:3000]
            if fallback_content:
                logger.info(f"Using fallback content for source '{source.title}'")
                combined_content_parts.append(f"[{source.title}]: {fallback_content}")
            continue

    combined_content = "\n\n".join(combined_content_parts)
    graph_data = await _build_graph_data_from_content(combined_content, title)

    logger.info(
        "Creating mind map with %s nodes and %s edges",
        len(graph_data["nodes"]),
        len(graph_data["edges"]),
    )

    mind_map = MindMap(
        notebook_id=notebook_id,
        title=title,
        graph_data=graph_data,
    )
    db.add(mind_map)
    await db.flush()
    await db.refresh(mind_map)

    logger.info(f"Mind map created successfully with ID: {mind_map.id} and stored in database")

    return mind_map
