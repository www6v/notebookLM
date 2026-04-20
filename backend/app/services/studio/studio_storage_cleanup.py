"""Remove studio outputs from object storage when records are deleted."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from app.services.infra.obs_storage import delete_file_from_obs

logger = logging.getLogger(__name__)


def delete_studio_objects_best_effort(keys: Iterable[str | None]) -> None:
    """Delete object keys; log and continue on failure (mirrors source delete)."""
    seen: set[str] = set()
    for raw in keys:
        if not raw or not isinstance(raw, str):
            continue
        key = raw.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        try:
            delete_file_from_obs(key)
        except RuntimeError:
            logger.warning(
                "Failed to delete object storage file %s, proceeding with DB "
                "deletion",
                key,
            )


def slide_deck_storage_keys(
    slides_data: dict | None,
    file_path: str | None,
) -> list[str]:
    """Collect OSS object keys for one slide deck (merged PDF + per-slide assets)."""
    keys: list[str] = []
    if file_path:
        keys.append(file_path)
    if not isinstance(slides_data, dict):
        return keys
    artifacts = slides_data.get("artifacts")
    if not isinstance(artifacts, dict):
        return keys
    images = artifacts.get("images")
    if not isinstance(images, list):
        return keys
    for item in images:
        if not isinstance(item, dict):
            continue
        variants = item.get("variants")
        if not isinstance(variants, dict):
            continue
        for variant in variants.values():
            if not isinstance(variant, dict):
                continue
            object_key = variant.get("object_key")
            if isinstance(object_key, str) and object_key.strip():
                keys.append(object_key.strip())
    return keys
