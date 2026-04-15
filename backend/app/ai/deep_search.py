"""Deep Search module: iterative query decomposition, vector retrieval, and reasoning.

Uses Milvus for vector retrieval and MySQL for chunk content; Qwen embedding
and the project's LLM API as the reasoning engine.
"""

import json
import logging
from collections.abc import Awaitable, Callable

from langfuse import observe, propagate_attributes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_text
from app.ai.llm_router import chat_completion, iter_chat_completion_text
from app.ai.milvus_client import search_vectors
from app.config import settings
from app.models.source import Source, SourceChunk

logger = logging.getLogger(__name__)

_deepsearcher_available = False
try:
    from deepsearcher.configuration import Configuration, init_config
    from deepsearcher.online_query import query as ds_query
    from deepsearcher.offline_loading import load_from_local_files
    _deepsearcher_available = True
except ImportError:
    logger.info(
        "deepsearcher not installed; falling back to built-in deep search"
    )


@observe(name="deep_search", as_type="generation")
async def deep_search(
    db: AsyncSession,
    notebook_id: str,
    query: str,
    source_ids: list[str] | None = None,
    max_iterations: int | None = None,
    top_k: int | None = None,
    conversation_style: str | None = None,
    custom_prompt: str | None = None,
    answer_length: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    on_search_step: Callable[[dict], Awaitable[None]] | None = None,
    on_final_chunk: Callable[[str], Awaitable[None]] | None = None,
) -> dict:
    """Run deep search over notebook sources.

    Returns:
        {
            "content": str,          # final answer
            "citations": dict,       # citation map
            "search_steps": list,    # intermediate steps for UI
        }
    """
    max_iter = max_iterations or settings.deep_search_max_iterations
    top_k = top_k or settings.deep_search_top_k

    if not await _has_chunks_for_notebook(db, notebook_id, source_ids):
        return {
            "content": "I don't have enough information from your sources to "
                       "answer this question. Try adding more sources or "
                       "rephrasing your question.",
            "citations": {},
            "search_steps": [],
        }

    with propagate_attributes(
        user_id=user_id or "",
        session_id=session_id or "",
        metadata={"llm": settings.litellm_model},
    ):
        return await _iterative_deep_search(
            db,
            notebook_id,
            source_ids,
            query,
            max_iter,
            top_k,
            conversation_style=conversation_style,
            custom_prompt=custom_prompt,
            answer_length=answer_length,
            user_id=user_id,
            session_id=session_id,
            on_search_step=on_search_step,
            on_final_chunk=on_final_chunk,
        )


async def _has_chunks_for_notebook(
    db: AsyncSession,
    notebook_id: str,
    source_ids: list[str] | None = None,
) -> bool:
    """Return True if there is at least one chunk for the notebook (and optional source filter)."""
    stmt = (
        select(SourceChunk.id)
        .join(Source, SourceChunk.source_id == Source.id)
        .where(
            Source.notebook_id == notebook_id,
            Source.is_active.is_(True),
        )
    )
    if source_ids:
        stmt = stmt.where(Source.id.in_(source_ids))
    stmt = stmt.limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _retrieve_chunks_from_milvus(
    db: AsyncSession,
    notebook_id: str,
    source_ids: list[str] | None,
    query: str,
    top_k: int,
) -> list[dict]:
    """Retrieve top-k chunks by vector search in Milvus, then load content from MySQL.

    Returns list of chunk dicts: chunk_id, content, chunk_index, source_id,
    source_title, metadata (no embedding).
    """
    try:
        query_emb = await embed_text(query[:2000])
    except Exception as exc:
        logger.warning("embed_text failed for retrieval: %s", exc)
        return []
    if not query_emb:
        return []

    try:
        hits = search_vectors(
            query_embedding=query_emb,
            top_k=top_k,
            notebook_id=notebook_id,
            source_ids=source_ids,
        )
    except Exception as exc:
        logger.warning("Milvus search_vectors failed: %s", exc)
        return []

    if not hits:
        return []

    chunk_ids = [cid for cid, _ in hits]
    stmt = (
        select(
            SourceChunk.id,
            SourceChunk.content,
            SourceChunk.chunk_index,
            SourceChunk.source_id,
            SourceChunk.metadata_,
            Source.title.label("source_title"),
        )
        .join(Source, SourceChunk.source_id == Source.id)
        .where(
            SourceChunk.id.in_(chunk_ids),
            Source.notebook_id == notebook_id,
            Source.is_active.is_(True),
        )
    )
    if source_ids:
        stmt = stmt.where(Source.id.in_(source_ids))
    result = await db.execute(stmt)
    rows = {str(row.id): row for row in result.all()}

    ordered = []
    for cid in chunk_ids:
        row = rows.get(cid)
        if row is None:
            continue
        ordered.append({
            "chunk_id": cid,
            "content": row.content,
            "chunk_index": row.chunk_index,
            "source_id": str(row.source_id),
            "source_title": row.source_title,
            "metadata": row.metadata_ or {},
        })
    return ordered


async def _iterative_deep_search(
    db: AsyncSession,
    notebook_id: str,
    source_ids: list[str] | None,
    query: str,
    max_iterations: int,
    top_k: int,
    conversation_style: str | None = None,
    custom_prompt: str | None = None,
    answer_length: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    on_search_step: Callable[[dict], Awaitable[None]] | None = None,
    on_final_chunk: Callable[[str], Awaitable[None]] | None = None,
) -> dict:
    """Built-in iterative deep search pipeline.

    1. Decompose the query into sub-questions
    2. For each sub-question, retrieve relevant chunks via Milvus vector search
    3. Reason over retrieved context
    4. Reflect: if answer is insufficient, generate new sub-questions
    5. Produce final answer with citations
    """
    search_steps: list[dict] = []
    all_retrieved: list[dict] = []
    accumulated_context: list[dict] = []

    sub_questions = await _decompose_query(
        query, user_id=user_id, session_id=session_id
    )
    step_decompose_initial = {
        "step": "decompose",
        "message": f"Decomposed into {len(sub_questions)} sub-questions",
        "sub_questions": sub_questions,
    }
    search_steps.append(step_decompose_initial)
    if on_search_step is not None:
        await on_search_step(step_decompose_initial)

    for iteration in range(max_iterations):
        for sq in sub_questions:
            retrieved = await _retrieve_chunks_from_milvus(
                db, notebook_id, source_ids, sq, top_k
            )
            new_chunks = [
                r for r in retrieved
                if r["chunk_id"] not in {c["chunk_id"] for c in all_retrieved}
            ]
            all_retrieved.extend(new_chunks)
            accumulated_context.extend(new_chunks)

            step_retrieve = {
                "step": "retrieve",
                "iteration": iteration + 1,
                "sub_question": sq,
                "chunks_found": len(new_chunks),
            }
            search_steps.append(step_retrieve)
            if on_search_step is not None:
                await on_search_step(step_retrieve)

        reflection = await _reflect(
            query,
            sub_questions,
            accumulated_context,
            iteration,
            user_id=user_id,
            session_id=session_id,
        )
        step_reflect = {
            "step": "reflect",
            "iteration": iteration + 1,
            "sufficient": reflection["sufficient"],
        }
        search_steps.append(step_reflect)
        if on_search_step is not None:
            await on_search_step(step_reflect)

        if reflection["sufficient"] or iteration >= max_iterations - 1:
            break

        sub_questions = reflection.get("new_sub_questions", [])
        if not sub_questions:
            break

        step_decompose_follow = {
            "step": "decompose",
            "iteration": iteration + 2,
            "message": f"Generated {len(sub_questions)} follow-up questions",
            "sub_questions": sub_questions,
        }
        search_steps.append(step_decompose_follow)
        if on_search_step is not None:
            await on_search_step(step_decompose_follow)

    answer, citations = await _generate_final_answer(
        query,
        accumulated_context,
        conversation_style=conversation_style,
        custom_prompt=custom_prompt,
        answer_length=answer_length,
        user_id=user_id,
        session_id=session_id,
        on_final_chunk=on_final_chunk,
    )

    return {
        "content": answer,
        "citations": citations,
        "search_steps": search_steps,
    }


async def _decompose_query(
    query: str,
    user_id: str | None = None,
    session_id: str | None = None,
) -> list[str]:
    """Use LLM to decompose user query into 2-4 sub-questions."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a research assistant. Decompose the user's question "
                "into 2-4 focused sub-questions that together would fully "
                "answer the original question. Return a JSON array of strings. "
                "Only return the JSON array, nothing else."
            ),
        },
        {"role": "user", "content": query},
    ]

    response = await chat_completion(
        messages,
        temperature=0.3,
        max_tokens=512,
        user_id=user_id,
        session_id=session_id,
    )
    text = response.choices[0].message.content.strip()

    try:
        text = text.strip("`").removeprefix("json").strip()
        sub_qs = json.loads(text)
        if isinstance(sub_qs, list) and sub_qs:
            return [str(q) for q in sub_qs[:4]]
    except (json.JSONDecodeError, TypeError):
        pass

    return [query]


async def _reflect(
    original_query: str,
    sub_questions: list[str],
    context: list[dict],
    iteration: int,
    user_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Reflect on whether retrieved context sufficiently answers the query."""
    context_summary = "\n".join(
        f"- [{c['source_title']}] {c['content'][:200]}"
        for c in context[:15]
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a research quality checker. Given the original question, "
                "sub-questions asked, and context retrieved so far, determine:\n"
                "1. Is the context sufficient to answer the original question? "
                "(sufficient: true/false)\n"
                "2. If not sufficient, what new sub-questions should be asked?\n\n"
                "Return JSON: {\"sufficient\": bool, \"new_sub_questions\": [str]}\n"
                "Only return JSON, nothing else."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Original question: {original_query}\n\n"
                f"Sub-questions asked: {json.dumps(sub_questions)}\n\n"
                f"Context retrieved:\n{context_summary}\n\n"
                f"Iteration: {iteration + 1}"
            ),
        },
    ]

    response = await chat_completion(
        messages,
        temperature=0.2,
        max_tokens=512,
        user_id=user_id,
        session_id=session_id,
    )
    text = response.choices[0].message.content.strip()

    try:
        text = text.strip("`").removeprefix("json").strip()
        result = json.loads(text)
        return {
            "sufficient": bool(result.get("sufficient", True)),
            "new_sub_questions": result.get("new_sub_questions", []),
        }
    except (json.JSONDecodeError, TypeError):
        return {"sufficient": True, "new_sub_questions": []}


def _build_style_instruction(
    conversation_style: str | None = None,
    custom_prompt: str | None = None,
    answer_length: str | None = None,
) -> str:
    """Build additional system instructions based on conversation settings."""
    parts: list[str] = []

    if conversation_style == "learning_guide":
        parts.append(
            "You are acting as a learning guide. Explain concepts clearly and "
            "pedagogically. Use step-by-step explanations, examples, and analogies "
            "to help the user understand new concepts and skills effectively."
        )
    elif conversation_style == "custom" and custom_prompt:
        parts.append(f"Additional instructions from the user: {custom_prompt}")

    if answer_length == "long":
        parts.append(
            "Provide a comprehensive, detailed, and thorough answer. "
            "Cover all relevant aspects in depth."
        )
    elif answer_length == "short":
        parts.append(
            "Keep your answer concise and brief. Focus on the most "
            "important points only."
        )

    return "\n\n".join(parts)


async def _generate_final_answer(
    query: str,
    context: list[dict],
    conversation_style: str | None = None,
    custom_prompt: str | None = None,
    answer_length: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    on_final_chunk: Callable[[str], Awaitable[None]] | None = None,
) -> tuple[str, dict]:
    """Generate the final answer with precise citations."""
    context_parts = []
    for i, chunk in enumerate(context, 1):
        meta = chunk.get("metadata", {})
        page_info = ""
        if meta.get("page_number"):
            page_info = f", Page {meta['page_number']}"
        context_parts.append(
            f"[{i}] (Source: {chunk['source_title']}{page_info})\n"
            f"{chunk['content']}"
        )

    context_text = "\n\n".join(context_parts)

    style_instruction = _build_style_instruction(
        conversation_style, custom_prompt, answer_length
    )

    system_content = (
        "You are an AI research assistant. Answer the user's question "
        "based ONLY on the provided source materials. Always cite your "
        "sources using bracket notation like [1], [2], etc. Be thorough "
        "and detailed.\n\n"
        "If the sources don't contain enough information, say so honestly.\n\n"
    )

    if style_instruction:
        system_content += f"{style_instruction}\n\n"

    system_content += f"Source Materials:\n{context_text}"

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": query},
    ]

    if on_final_chunk is None:
        response = await chat_completion(
            messages,
            temperature=0.3,
            max_tokens=4096,
            user_id=user_id,
            session_id=session_id,
        )
        answer = response.choices[0].message.content or ""
    else:
        parts: list[str] = []
        async for delta in iter_chat_completion_text(
            messages,
            temperature=0.3,
            max_tokens=4096,
            user_id=user_id,
            session_id=session_id,
        ):
            if delta:
                parts.append(delta)
                await on_final_chunk(delta)
        answer = "".join(parts)

    citations = {}
    for i, chunk in enumerate(context, 1):
        meta = chunk.get("metadata", {})
        citations[str(i)] = {
            "source_id": chunk["source_id"],
            "source_title": chunk["source_title"],
            "chunk_id": chunk["chunk_id"],
            "chunk_index": chunk["chunk_index"],
            "page_number": meta.get("page_number"),
            "paragraph_index": meta.get("paragraph_index"),
            "content": chunk["content"][:300],
            "highlight_text": None,
        }

    return answer, citations
