"""Embedding service via DashScope MultiModalEmbedding (qwen3-vl-embedding).

Uses DashScope SDK directly so that the same model supports text now and
image/video later (multimodal). LiteLLM does not support dashscope for
embedding endpoints.
"""

import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

try:
    from dashscope.embeddings.multimodal_embedding import (
        AioMultiModalEmbedding,
        MultiModalEmbeddingItemText,
    )
    HAS_DASHSCOPE_EMBED = True
except ImportError:
    HAS_DASHSCOPE_EMBED = False
    AioMultiModalEmbedding = None
    MultiModalEmbeddingItemText = None


def _embedding_input_items(texts: list[str]) -> list:
    """Build MultiModalEmbedding input list for text-only (multimodal later)."""
    if not HAS_DASHSCOPE_EMBED or MultiModalEmbeddingItemText is None:
        return []
    return [MultiModalEmbeddingItemText(text=t, factor=1.0) for t in texts]


def _to_float_vector(raw: list | str) -> list[float]:
    """Normalize embedding to list of float for Milvus FLOAT_VECTOR."""
    if isinstance(raw, str):
        raw = json.loads(raw) if raw.strip().startswith("[") else []
    if not isinstance(raw, list):
        return []
    try:
        return [float(x) for x in raw]
    except (TypeError, ValueError):
        return []


def _parse_dashscope_embeddings(response) -> list[list[float]]:
    """Parse DashScope MultiModalEmbedding response to list of vectors."""
    out: list[list[float]] = []
    output = getattr(response, "output", None) or {}
    if isinstance(output, dict):
        data = output.get("embeddings", output.get("embedding", []))
    else:
        data = getattr(output, "embeddings", getattr(output, "embedding", []))
    if isinstance(data, str) and data.strip().startswith("["):
        data = [data]
    if not isinstance(data, list):
        data = [data] if data else []
    for item in data:
        if isinstance(item, dict):
            emb = item.get("embedding", [])
        elif isinstance(item, str) and item.strip().startswith("["):
            emb = item
        else:
            emb = getattr(item, "embedding", [])
        out.append(_to_float_vector(emb))
    return out


async def embed_text(text: str) -> list[float]:
    """Generate an embedding vector for a piece of text."""
    if not HAS_DASHSCOPE_EMBED:
        raise RuntimeError(
            "DashScope embedding requires: dashscope MultiModalEmbedding."
        )
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is required for embeddings.")
    items = _embedding_input_items([text])
    if not items:
        return []
    kwargs = {
        "model": settings.embedding_model,
        "input": items,
        "api_key": settings.dashscope_api_key,
    }
    if getattr(settings, "embedding_dimension", None):
        kwargs["dimension"] = settings.embedding_dimension
    if settings.dashscope_api_base:
        import dashscope
        dashscope.base_http_api_url = settings.dashscope_api_base.rstrip("/")
    response = await AioMultiModalEmbedding.call(**kwargs)
    if getattr(response, "status_code", 0) != 200:
        logger.error(
            "Embedding failed: status_code=%s, code=%s, message=%s",
            getattr(response, "status_code", None),
            getattr(response, "code", None),
            getattr(response, "message", None),
        )
        return []
    vectors = _parse_dashscope_embeddings(response)
    return vectors[0] if vectors else []


async def embed_chunks(
    chunks: list[str], batch_size: int = 6,
) -> list[list[float] | None]:
    """Generate embedding vectors for multiple text chunks.

    Uses DashScope MultiModalEmbedding (qwen3-vl-embedding). Batch size
    kept small to respect API limits. Same API will support image/video
    input later via MultiModalEmbeddingItemImage / ItemVideo.
    """
    if not HAS_DASHSCOPE_EMBED:
        raise RuntimeError(
            "DashScope embedding requires: dashscope MultiModalEmbedding."
        )
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is required for embeddings.")
    all_embeddings: list[list[float] | None] = []
    base_url = settings.dashscope_api_base.rstrip("/") if settings.dashscope_api_base else None

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        truncated = [t[:2000] for t in batch]
        try:
            items = _embedding_input_items(truncated)
            if not items:
                all_embeddings.extend([None] * len(batch))
                continue
            kwargs = {
                "model": settings.embedding_model,
                "input": items,
                "api_key": settings.dashscope_api_key,
            }
            if getattr(settings, "embedding_dimension", None):
                kwargs["dimension"] = settings.embedding_dimension
            if base_url:
                import dashscope
                dashscope.base_http_api_url = base_url
            response = await AioMultiModalEmbedding.call(**kwargs)
            if getattr(response, "status_code", 0) != 200:
                logger.error(
                    "Embedding batch %d failed: status_code=%s, code=%s",
                    i // batch_size,
                    getattr(response, "status_code", None),
                    getattr(response, "code", None),
                )
                all_embeddings.extend([None] * len(batch))
                continue
            batch_embs = _parse_dashscope_embeddings(response)
            all_embeddings.extend(batch_embs)
        except Exception as exc:
            logger.error(
                "Embedding batch %d failed: %s", i // batch_size, exc
            )
            all_embeddings.extend([None] * len(batch))

    return all_embeddings
