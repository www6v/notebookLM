"""Mind map generation service.

This service generates mind maps from selected documents. The original documents
are stored in OSS, while the mind map itself is stored in the database as
structured graph data.
"""

import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from langfuse import observe, propagate_attributes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import chat_completion
from app.config import settings
from app.models.studio import MindMap
from app.schemas.studio import MindMapStatus
from app.services.source_service import (
    build_combined_content_from_sources,
    fetch_sources,
)
from app.services.studio.studio_status_service import (
    clear_generation_error,
    mark_generation_as_error,
)

logger = logging.getLogger(__name__)


def _render_mindmap_system_prompt(
    max_nodes: int = 20,
    extra_instruction: str = "",
    output_language: str = "简体中文",
) -> str:
    """Render mind map system prompt from template with Jinja2 variables."""
    template_dir = Path(__file__).resolve().parents[2] / "templates"
    env = Environment(
        autoescape=select_autoescape(default_for_string=False),
        loader=FileSystemLoader(template_dir),
    )
    template = env.get_template("mindmap_system_prompt.txt")
    return template.render(
        max_nodes=max_nodes,
        extra_instruction=extra_instruction,
        output_language=output_language,
    )


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


@observe(name="mindmap_build_graph_data", as_type="generation")
async def _build_graph_data_from_content(
    combined_content: str,
    title: str,
    output_language: str = "简体中文",
    user_id: str | None = None,
    session_id: str | None = None,
) -> tuple[dict, str | None]:
    """Build mind map graph data (nodes/edges) from combined text via LLM.

    Returns (graph_data, suggested_filename). graph_data is empty if content
    is empty; on parse error returns a single-node fallback graph.
    """
    if not combined_content.strip():
        logger.warning("No content found in sources from OSS, creating empty mind map")
        return {"nodes": [], "edges": []}, None

    logger.info(
        "Combined content length from OSS documents: %s characters",
        len(combined_content),
    )
    logger.info("Combined content preview: %s", combined_content[:1000])

    system_prompt = _render_mindmap_system_prompt(
        max_nodes=20, output_language=output_language
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": combined_content},
    ]

    try:
        logger.info(
            "Sending request to LLM for mind map generation from OSS document content"
        )
        response = await chat_completion(
            messages,
            temperature=0.3,
            user_id=user_id,
            session_id=session_id,
        )
        content = response.choices[0].message.content
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        llm_result = json.loads(content)
        suggested_filename = llm_result.pop("suggested_filename", None)
        logger.info("Successfully parsed graph data from LLM response")
        logger.info("graph_data: %s", llm_result)
        return llm_result, suggested_filename
    except Exception as e:
        logger.error("Error processing LLM response: %s", str(e))
        return {
            "nodes": [{"id": "1", "label": title}],
            "edges": [],
        }, None

#  老接口
# async def generate_mindmap_from_sources(
#     db: AsyncSession,
#     notebook_id: str,
#     title: str = "Mind Map",
#     source_ids: list[str] | None = None,
# ) -> MindMap:
#     """Generate a mind map by asking the LLM to extract key concepts from selected sources.

#     Note: The original documents are stored in OSS,
#     while the mind map itself is stored in the database as structured graph data.
#     """
#     logger.info(
#         "Starting mind map generation for notebook_id: %s, title: %s, source_ids: %s",
#         notebook_id,
#         title,
#         source_ids,
#     )

#     sources = await fetch_sources(db, notebook_id, source_ids)
#     logger.info(
#         "Found %s sources from OSS for mind map generation",
#         len(sources),
#     )

#     combined_content = await build_combined_content_from_sources(sources)
#     if not combined_content.strip():
#         raise ValueError(
#             "No usable content from selected sources for mind map. "
#             "Ensure documents have content or retry after video understanding is available."
#         )
#     graph_data = await _build_graph_data_from_content(combined_content, title)

#     logger.info(
#         "Creating mind map with %s nodes and %s edges",
#         len(graph_data["nodes"]),
#         len(graph_data["edges"]),
#     )

#     mind_map = await _create_and_persist_mindmap(
#         db, notebook_id, title, graph_data
#     )
#     logger.info(
#         "Mind map created successfully with ID: %s and stored in database",
#         mind_map.id,
#     )
#     return mind_map


@observe(name="run_mindmap_generation_for_existing", as_type="generation")
async def run_mindmap_generation_for_existing(
    db: AsyncSession,
    mindmap_id: str,
    source_ids: list[str] | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
) -> MindMap:
    """Run mind map generation for an existing pending MindMap record.

    Fetches sources, builds content, generates graph data via LLM, then updates
    the MindMap with graph_data and status=ready. On error sets status=error.
    """
    with propagate_attributes(
        user_id=user_id or "",
        session_id=session_id or mindmap_id,
        metadata={"llm": settings.litellm_model},
    ):
        result = await db.execute(
            select(MindMap).where(MindMap.id == mindmap_id)
        )
        mind_map = result.scalar_one_or_none()
        if mind_map is None:
            raise ValueError(f"MindMap not found: {mindmap_id}")

        mind_map.status = MindMapStatus.PROCESSING.value
        clear_generation_error(mind_map)
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
            combined_content = await build_combined_content_from_sources(
                sources
            )
            if not combined_content.strip():
                mind_map.status = MindMapStatus.ERROR.value
                await db.flush()
                raise ValueError(
                    "No usable content from selected sources for mind map."
                )
            output_language = (
                getattr(mind_map, "output_language", None) or "简体中文"
            )
            graph_data, suggested_filename = (
                await _build_graph_data_from_content(
                    combined_content,
                    mind_map.title,
                    output_language=output_language,
                    user_id=user_id,
                    session_id=session_id or mindmap_id,
                )
            )
            mind_map.graph_data = graph_data
            if suggested_filename:
                mind_map.suggested_filename = suggested_filename
            mind_map.status = MindMapStatus.READY.value
            clear_generation_error(mind_map)
            await db.flush()
            logger.info(
                "Mind map %s updated with %s nodes, %s edges, suggested_filename=%s",
                mindmap_id,
                len(graph_data.get("nodes", [])),
                len(graph_data.get("edges", [])),
                suggested_filename,
            )
            return mind_map
        except Exception as exc:
            mark_generation_as_error(
                mind_map,
                "mind map generation failed",
                str(exc),
            )
            await db.flush()
            raise
