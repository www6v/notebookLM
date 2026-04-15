"""Deep Search module: iterative query decomposition, vector retrieval, and reasoning.

Uses Milvus for vector retrieval and MySQL for chunk content; Qwen embedding
and the project's LLM API as the reasoning engine.
"""

import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable

from langfuse import observe, propagate_attributes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_chunks
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


def _chunk_row_to_dict(cid: str, row) -> dict:
    """Map a SourceChunk ORM row to the chunk dict used in retrieval."""
    return {
        "chunk_id": cid,
        "content": row.content,
        "chunk_index": row.chunk_index,
        "source_id": str(row.source_id),
        "source_title": row.source_title,
        "metadata": row.metadata_ or {},
    }


async def _retrieve_new_chunks_for_subquestions_batched(
    db: AsyncSession,
    notebook_id: str,
    source_ids: list[str] | None,
    sub_questions: list[str],
    top_k: int,
    already_retrieved_chunk_ids: set[str],
) -> tuple[list[tuple[str, list[dict]]], dict[str, float]]:
    """Embed all sub-questions in batch, search Milvus in parallel, one DB round-trip.

    Mutates ``already_retrieved_chunk_ids`` for chunk_ids appended from this batch
    (same semantics as sequential per-sub-question retrieval).

    Returns:
        Ordered (sub_question, new_chunks) pairs, and timing fields in milliseconds
        (embed_ms, milvus_ms, db_ms).
    """
    timings: dict[str, float] = {
        "embed_ms": 0.0,
        "milvus_ms": 0.0,
        "db_ms": 0.0,
    }
    if not sub_questions:
        return [], timings

    texts = [sq[:2000] for sq in sub_questions]
    t_embed = time.perf_counter()
    try:
        vectors = await embed_chunks(texts)
    except Exception as exc:
        logger.warning("embed_chunks failed for retrieval: %s", exc)
        return [(sq, []) for sq in sub_questions], timings
    timings["embed_ms"] = (time.perf_counter() - t_embed) * 1000.0

    while len(vectors) < len(sub_questions):
        vectors.append(None)

    async def _search_one(
        vec: list[float] | None,
    ) -> list[tuple[str, float]]:
        if not vec:
            return []
        try:
            return await asyncio.to_thread(
                search_vectors,
                vec,
                top_k,
                notebook_id,
                source_ids,
            )
        except Exception as exc:
            logger.warning("Milvus search_vectors failed: %s", exc)
            return []

    t_milvus = time.perf_counter()
    hits_per_sq = await asyncio.gather(
        *(_search_one(v) for v in vectors[: len(sub_questions)])
    )
    timings["milvus_ms"] = (time.perf_counter() - t_milvus) * 1000.0

    all_ids: list[str] = []
    ordered_unique: set[str] = set()
    for hits in hits_per_sq:
        for cid, _ in hits:
            if cid not in ordered_unique:
                ordered_unique.add(cid)
                all_ids.append(cid)

    if not all_ids:
        return [(sq, []) for sq in sub_questions], timings

    t_db = time.perf_counter()
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
            SourceChunk.id.in_(all_ids),
            Source.notebook_id == notebook_id,
            Source.is_active.is_(True),
        )
    )
    if source_ids:
        stmt = stmt.where(Source.id.in_(source_ids))
    result = await db.execute(stmt)
    rows = {str(row.id): row for row in result.all()}
    timings["db_ms"] = (time.perf_counter() - t_db) * 1000.0

    per_sq: list[tuple[str, list[dict]]] = []
    for sq, hits in zip(sub_questions, hits_per_sq, strict=True):
        new_for_sq: list[dict] = []
        for cid, _ in hits:
            if cid in already_retrieved_chunk_ids:
                continue
            row = rows.get(cid)
            if row is None:
                continue
            new_for_sq.append(_chunk_row_to_dict(cid, row))
            already_retrieved_chunk_ids.add(cid)
        per_sq.append((sq, new_for_sq))

    return per_sq, timings


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
    seen: set[str] = set()
    pairs, _timings = await _retrieve_new_chunks_for_subquestions_batched(
        db,
        notebook_id,
        source_ids,
        [query],
        top_k,
        seen,
    )
    _sq, chunks = pairs[0]
    return chunks


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

    t_pipeline = time.perf_counter()
    t_decompose = time.perf_counter()
    sub_questions = await _decompose_query(
        query, user_id=user_id, session_id=session_id
    )
    decompose_ms = (time.perf_counter() - t_decompose) * 1000.0
    logger.info(
        "deep_search phase=decompose decompose_ms=%.1f notebook_id=%s "
        "session_id=%s sub_q_count=%d",
        decompose_ms,
        notebook_id,
        session_id or "",
        len(sub_questions),
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
        seen_chunk_ids = {c["chunk_id"] for c in all_retrieved}
        t_retrieve = time.perf_counter()
        pairs, batch_timings = await _retrieve_new_chunks_for_subquestions_batched(
            db,
            notebook_id,
            source_ids,
            sub_questions,
            top_k,
            seen_chunk_ids,
        )
        retrieve_total_ms = (time.perf_counter() - t_retrieve) * 1000.0

        for sq, new_chunks in pairs:
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

        logger.info(
            "deep_search phase=retrieve_batch notebook_id=%s session_id=%s "
            "iteration=%d retrieve_total_ms=%.1f embed_ms=%.1f milvus_ms=%.1f "
            "db_ms=%.1f sub_q_count=%d accumulated_chunks=%d",
            notebook_id,
            session_id or "",
            iteration + 1,
            retrieve_total_ms,
            batch_timings["embed_ms"],
            batch_timings["milvus_ms"],
            batch_timings["db_ms"],
            len(sub_questions),
            len(accumulated_context),
        )

        t_reflect = time.perf_counter()
        reflection = await _reflect(
            query,
            sub_questions,
            accumulated_context,
            iteration,
            user_id=user_id,
            session_id=session_id,
        )
        reflect_ms = (time.perf_counter() - t_reflect) * 1000.0
        logger.info(
            "deep_search phase=reflect reflect_ms=%.1f notebook_id=%s "
            "session_id=%s iteration=%d sufficient=%s accumulated_chunks=%d",
            reflect_ms,
            notebook_id,
            session_id or "",
            iteration + 1,
            reflection["sufficient"],
            len(accumulated_context),
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

    t_final = time.perf_counter()
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
    final_answer_ms = (time.perf_counter() - t_final) * 1000.0
    total_ms = (time.perf_counter() - t_pipeline) * 1000.0
    logger.info(
        "deep_search phase=final_answer final_answer_ms=%.1f notebook_id=%s "
        "session_id=%s accumulated_chunks=%d",
        final_answer_ms,
        notebook_id,
        session_id or "",
        len(accumulated_context),
    )
    logger.info(
        "deep_search phase=total total_ms=%.1f notebook_id=%s session_id=%s",
        total_ms,
        notebook_id,
        session_id or "",
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
                "If the retrieved passages already reasonably address the original "
                "question—including definition-style or overview questions—set "
                "sufficient to true. Do not set sufficient to false only because "
                "some sub-questions returned no chunks while others returned "
                "relevant material.\n\n"
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
