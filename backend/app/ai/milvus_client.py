"""Milvus vector store client for notebooklm chunk embeddings.

Stores chunk_id (pk), source_id, notebook_id, and embedding vector.
Used for ingestion (process_source) and retrieval (deep_search).
"""

import json
import logging
import os
from urllib.parse import urlparse

from app.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "notebooklm_chunks"
_CONN_ALIAS = "default"
_connected = False


def _get_connection_params():
    """Parse MILVUS_URI (e.g. http://47.100.78.241:19530) into host and port."""
    uri = (os.environ.get("MILVUS_URI", "") or "").strip()
    if not uri:
        return {"host": "localhost", "port": "19530"}
    parsed = urlparse(uri)
    host = parsed.hostname or "localhost"
    port = str(parsed.port or 19530)
    return {"host": host, "port": port}


def ensure_connected():
    """Ensure connection to Milvus; idempotent."""
    global _connected
    if _connected:
        return
    try:
        from pymilvus import connections

        params = _get_connection_params()
        connections.connect(_CONN_ALIAS, **params)
        _connected = True
        logger.info(
            "Milvus connected: %s:%s",
            params["host"],
            params["port"],
        )
    except Exception as e:
        logger.exception("Milvus connection failed: %s", e)
        raise


def ensure_collection():
    """Create collection if it does not exist; create index on vector field."""
    ensure_connected()
    from pymilvus import (
        Collection,
        CollectionSchema,
        DataType,
        FieldSchema,
        utility,
    )

    if utility.has_collection(COLLECTION_NAME):
        return

    dim = getattr(settings, "embedding_dimension", 1024)
    max_len = 64

    fields = [
        FieldSchema(
            name="chunk_id",
            dtype=DataType.VARCHAR,
            max_length=max_len,
            is_primary=True,
            auto_id=False,
        ),
        FieldSchema(
            name="source_id",
            dtype=DataType.VARCHAR,
            max_length=max_len,
        ),
        FieldSchema(
            name="notebook_id",
            dtype=DataType.VARCHAR,
            max_length=max_len,
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=dim,
        ),
    ]
    schema = CollectionSchema(
        fields,
        description="NotebookLM source chunks with embeddings",
    )
    collection = Collection(name=COLLECTION_NAME, schema=schema)
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    collection.create_index(
        field_name="embedding",
        index_params=index_params,
    )
    logger.info(
        "Milvus collection %s created with dim=%s",
        COLLECTION_NAME,
        dim,
    )


def _normalize_vector_to_floats(vec: list[float] | list[str] | str) -> list[float] | None:
    """Convert a single vector to list of float for Milvus FLOAT_VECTOR.

    Handles: list of numbers, list of numeric strings, or JSON string of array.
    """
    if isinstance(vec, str):
        s = vec.strip()
        if s.startswith("["):
            try:
                vec = json.loads(vec)
            except (json.JSONDecodeError, TypeError):
                return None
        else:
            return None
    if not isinstance(vec, list):
        return None
    try:
        return [float(x) for x in vec]
    except (TypeError, ValueError):
        return None


def insert_vectors(
    chunk_ids: list[str],
    source_ids: list[str],
    notebook_ids: list[str],
    vectors: list[list[float]],
) -> None:
    """Insert chunk vectors into Milvus. All lists must have the same length."""
    if not chunk_ids or not vectors:
        return
    if not (len(chunk_ids) == len(source_ids) == len(notebook_ids) == len(vectors)):
        raise ValueError(
            "insert_vectors: chunk_ids, source_ids, notebook_ids, vectors length mismatch"
        )

    ensure_connected()
    ensure_collection()

    from pymilvus import Collection

    # Milvus requires FLOAT_VECTOR; normalize and ensure every scalar is Python float.
    float_vectors: list[list[float]] = []
    for vec in vectors:
        normalized = _normalize_vector_to_floats(vec)
        if normalized is None:
            raise TypeError(
                f"insert_vectors: each vector must be list of numbers or JSON "
                f"string, got {type(vec).__name__}"
            )
        # Force every element to Python float (no str/numpy); Milvus rejects str.
        float_vectors.append([float(x) for x in normalized])

    # Insert by rows (entities) so embedding field type is explicit and unambiguous.
    collection = Collection(COLLECTION_NAME)
    data = [
        {
            "chunk_id": cid,
            "source_id": sid,
            "notebook_id": nid,
            "embedding": emb,
        }
        for cid, sid, nid, emb in zip(
            chunk_ids, source_ids, notebook_ids, float_vectors
        )
    ]
    collection.insert(data)
    collection.flush()
    logger.info("Milvus insert_vectors: %d rows", len(chunk_ids))


def search_vectors(
    query_embedding: list[float],
    top_k: int,
    notebook_id: str,
    source_ids: list[str] | None = None,
) -> list[tuple[str, float]]:
    """Search for nearest chunks; returns [(chunk_id, score), ...].

    Filter by notebook_id and optionally by source_ids.
    Uses COSINE metric.
    """
    ensure_connected()
    from pymilvus import Collection

    collection = Collection(COLLECTION_NAME)
    collection.load()

    expr_parts = [f'notebook_id == "{_escape_expr_str(notebook_id)}"']
    if source_ids:
        in_list = ", ".join(
            f'"{_escape_expr_str(sid)}"' for sid in source_ids
        )
        expr_parts.append(f"source_id in [{in_list}]")
    expr = " and ".join(expr_parts)

    search_params = {"metric_type": "COSINE", "params": {"nprobe": 32}}
    results = collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        expr=expr,
        output_fields=["chunk_id"],
    )

    out: list[tuple[str, float]] = []
    for hits in results:
        for hit in hits:
            chunk_id = hit.id if hit.id is not None else getattr(
                hit.entity, "chunk_id", None
            )
            chunk_id = chunk_id if isinstance(chunk_id, str) else str(chunk_id)
            score = float(getattr(hit, "score", None) or getattr(hit, "distance", 0))
            out.append((chunk_id, score))
    return out


def _escape_expr_str(s: str) -> str:
    """Escape double quotes in string for Milvus expr."""
    return s.replace('\\', '\\\\').replace('"', '\\"')


def delete_by_source_id(source_id: str) -> None:
    """Delete all vectors for the given source_id."""
    ensure_connected()
    from pymilvus import Collection, utility

    if not utility.has_collection(COLLECTION_NAME):
        return
    collection = Collection(COLLECTION_NAME)
    collection.load()
    expr = f'source_id == "{_escape_expr_str(source_id)}"'
    res = collection.delete(expr)
    collection.flush()
    deleted = getattr(res, "delete_count", 0) or 0
    logger.info("Milvus delete_by_source_id %s: deleted %s", source_id, deleted)
