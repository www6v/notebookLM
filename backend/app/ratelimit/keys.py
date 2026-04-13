"""Pure helpers: Redis cooldown key materialization."""

from __future__ import annotations

from app.ratelimit.kinds import GenerationKind


def build_cooldown_keys(
    user_id: str,
    kind: GenerationKind,
    notebook_id: str,
    source_ids: list[str] | None,
    artifact_id: str | None,
) -> list[str]:
    """Return Redis keys for this generation attempt (one or many).

    - Regenerate (artifact_id set): single artifact:* key.
    - Explicit sources: one key per unique source_id (sorted for stability).
    - No sources: single notebook:* key for the notebook scope.
    """
    base = f"genrl:cooldown:{user_id}:{kind.value}"
    if artifact_id:
        return [f"{base}:artifact:{artifact_id}"]
    if source_ids:
        unique = sorted({sid.strip() for sid in source_ids if sid and sid.strip()})
        if unique:
            return [f"{base}:source:{sid}" for sid in unique]
        return [f"{base}:notebook:{notebook_id}"]
    return [f"{base}:notebook:{notebook_id}"]
