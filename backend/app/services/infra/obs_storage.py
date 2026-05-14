"""Object storage: Tencent COS only (Aliyun OSS fallback removed)."""

import logging
import uuid
from typing import Any, Optional

from notebooklm_shared.config import settings

logger = logging.getLogger(__name__)

_cos_client = None
_cos_available: Optional[bool] = None


def _normalize_prefix(prefix: str) -> str:
    return prefix.strip().rstrip("/")


def _cos_configured() -> bool:
    return bool(
        settings.config_cos_secret_id.strip()
        and settings.config_cos_secret_key.strip()
        and settings.config_cos_bucket_name.strip()
    )


def _primary_path_prefix() -> str:
    """Logical key prefix for new uploads (COS layout)."""
    return _normalize_prefix(settings.config_cos_path_prefix)


def _key_variants(object_key: str) -> list[str]:
    """Map between legacy path prefix and COS prefix when they differ."""
    raw = object_key.strip().lstrip("/")
    if not raw:
        return []
    legacy_p = _normalize_prefix(settings.oss_path_prefix)
    cos_p = _normalize_prefix(settings.config_cos_path_prefix)
    keys: list[str] = [raw]
    if legacy_p and cos_p and legacy_p != cos_p:
        if raw.startswith(f"{legacy_p}/") or raw == legacy_p:
            suffix = raw[len(legacy_p) :].lstrip("/")
            alt = f"{cos_p}/{suffix}" if suffix else cos_p
            if alt != raw:
                keys.append(alt)
        if raw.startswith(f"{cos_p}/") or raw == cos_p:
            suffix = raw[len(cos_p) :].lstrip("/")
            alt = f"{legacy_p}/{suffix}" if suffix else legacy_p
            if alt not in keys:
                keys.append(alt)
    out: list[str] = []
    for key in keys:
        if key and key not in out:
            out.append(key)
    return out


def _preferred_public_object_key(object_key: str) -> str:
    """Pick COS-side key for public URLs when prefixes differ."""
    stripped = object_key.strip().lstrip("/")
    variants = _key_variants(stripped)
    if not variants:
        return stripped
    cos_p = _normalize_prefix(settings.config_cos_path_prefix)
    if cos_p:
        for key in variants:
            if key.startswith(f"{cos_p}/") or key == cos_p:
                return key
    return variants[0]


def _cos_head_exists(object_key: str) -> bool:
    client = _get_cos_client()
    if client is None:
        return False
    try:
        client.head_object(
            Bucket=settings.config_cos_bucket_name.strip(),
            Key=object_key,
        )
        return True
    except Exception as exc:
        if _is_cos_not_found(exc):
            return False
        logger.warning("COS head_object failed for %s: %s", object_key, exc)
        return False


def _parsed_prefix_roots() -> list[str]:
    """Path roots for MinerU parsed assets (legacy prefix vs COS prefix)."""
    roots: list[str] = []
    for root in (
        _normalize_prefix(settings.oss_path_prefix),
        _normalize_prefix(settings.config_cos_path_prefix),
    ):
        if root and root not in roots:
            roots.append(root)
    return roots


def _get_cos_client():
    """Return CosS3Client or None if COS is not configured or unreachable."""
    global _cos_client, _cos_available
    if _cos_available is False:
        return None
    if _cos_client is not None:
        return _cos_client
    if not _cos_configured():
        _cos_available = False
        return None
    try:
        from qcloud_cos import CosConfig, CosS3Client

        region = settings.config_cos_region.strip() or "ap-shanghai"
        conf = CosConfig(
            Region=region,
            SecretId=settings.config_cos_secret_id.strip(),
            SecretKey=settings.config_cos_secret_key.strip(),
            Scheme="https",
        )
        client = CosS3Client(conf)
        client.head_bucket(Bucket=settings.config_cos_bucket_name.strip())
        _cos_client = client
        _cos_available = True
        logger.info("Tencent Cloud COS initialized successfully")
        return _cos_client
    except Exception as exc:
        _cos_available = False
        logger.warning("Tencent Cloud COS unavailable: %s", exc)
        return None


def _require_cos_client():
    client = _get_cos_client()
    if client is None:
        raise RuntimeError(
            "Tencent Cloud COS is not configured or unavailable. "
            "Configure the ``cos`` section in config.yaml "
            "(secret_id, secret_key, bucket_name, region)."
        )
    return client


def _is_cos_not_found(exc: BaseException) -> bool:
    try:
        from qcloud_cos.cos_exception import CosServiceError
    except ImportError:
        return False
    if not isinstance(exc, CosServiceError):
        return False
    code = (exc.get_error_code() or "").strip()
    status = exc.get_status_code()
    return status == 404 or code in ("NoSuchKey", "NoSuchResource", "NoSuchBucket")


def _cos_put_object(
    object_key: str,
    body: bytes,
    content_type: str,
    cache_control: str | None,
) -> None:
    client = _require_cos_client()
    kwargs: dict[str, Any] = {
        "Bucket": settings.config_cos_bucket_name.strip(),
        "Body": body,
        "Key": object_key,
        "EnableMD5": False,
    }
    if content_type:
        kwargs["ContentType"] = content_type
    if cache_control:
        kwargs["CacheControl"] = cache_control
    client.put_object(**kwargs)


def _cos_get_object(object_key: str) -> bytes:
    client = _require_cos_client()
    resp = client.get_object(
        Bucket=settings.config_cos_bucket_name.strip(),
        Key=object_key,
    )
    body = resp["Body"]
    if hasattr(body, "read"):
        return body.read()
    return bytes(body)


def _cos_delete_object(object_key: str) -> None:
    client = _require_cos_client()
    client.delete_object(
        Bucket=settings.config_cos_bucket_name.strip(),
        Key=object_key,
    )


def _cos_delete_prefix(prefix: str) -> int:
    client = _require_cos_client()
    bucket = settings.config_cos_bucket_name.strip()
    marker = ""
    deleted = 0
    while True:
        kwargs: dict[str, Any] = {
            "Bucket": bucket,
            "Prefix": prefix,
            "MaxKeys": 1000,
        }
        if marker:
            kwargs["Marker"] = marker
        resp = client.list_objects(**kwargs)
        contents = resp.get("Contents") or []
        for item in contents:
            client.delete_object(Bucket=bucket, Key=item["Key"])
            deleted += 1
        truncated = resp.get("IsTruncated")
        if truncated in (True, "true"):
            marker = resp.get("NextMarker") or (
                contents[-1]["Key"] if contents else ""
            )
            if not marker:
                break
        else:
            break
    return deleted


def _build_object_key(filename: str) -> str:
    """Build the full object key with prefix and unique suffix.

    Format: {path_prefix}/sources/{uuid}_{filename}
    """
    unique_id = uuid.uuid4().hex[:12]
    safe_name = filename.replace(" ", "_")
    prefix = _primary_path_prefix()
    base = f"sources/{unique_id}_{safe_name}"
    return f"{prefix}/{base}" if prefix else base


def upload_file_to_obs(
    file_content: bytes,
    filename: str,
    content_type: str = "application/octet-stream",
    cache_control: str | None = None,
) -> str:
    """Upload file bytes and return the object key (COS)."""
    object_key = _build_object_key(filename)
    _cos_put_object(
        object_key,
        file_content,
        content_type,
        cache_control,
    )
    logger.info("Uploaded file to COS: %s", object_key)
    return object_key


def get_file_url(object_key: str) -> str:
    """Build a public HTTPS URL for the object on COS."""
    if not _cos_configured():
        raise RuntimeError(
            "Tencent Cloud COS is not configured; cannot build object URL."
        )
    if not settings.config_cos_public_base_url.strip():
        raise RuntimeError(
            "COS public base URL is not configured (cos_public_base_url)."
        )
    base = settings.config_cos_public_base_url.rstrip("/")
    pub_key = _preferred_public_object_key(object_key)
    return f"{base}/{pub_key}"


def generate_presigned_url(
    object_key: str,
    expiration: int = 3600,
    response_content_disposition: str | None = None,
) -> str:
    """Presigned GET URL (COS)."""
    params: dict[str, str] | None = None
    if response_content_disposition:
        params = {
            "response-content-disposition": response_content_disposition,
        }
    stripped = object_key.strip().lstrip("/")
    variants = _key_variants(stripped) or [stripped]
    cos_client = _get_cos_client()
    if cos_client is None:
        raise RuntimeError(
            "Presigned URL generation failed: COS is not available."
        )
    for key in variants:
        if not _cos_head_exists(key):
            continue
        try:
            return cos_client.get_presigned_url(
                Method="GET",
                Bucket=settings.config_cos_bucket_name.strip(),
                Key=key,
                Expired=expiration,
                Params=params or {},
            )
        except Exception as exc:
            logger.error("Failed to generate COS presigned URL: %s", exc)
            raise RuntimeError(
                f"Presigned URL generation failed: {exc}"
            ) from exc
    raise RuntimeError(
        "Presigned URL generation failed: object not found in COS "
        "for any key variant, or COS is misconfigured."
    )


def download_file_from_obs(object_key: str) -> bytes:
    """Download bytes from COS (tries each key variant)."""
    stripped = object_key.strip().lstrip("/")
    variants = _key_variants(stripped) or [stripped]
    last_error: BaseException | None = None
    cos_client = _get_cos_client()
    if cos_client is None:
        raise RuntimeError(
            "No object storage backend is configured or available."
        )
    for key in variants:
        try:
            content = _cos_get_object(key)
            logger.info("Downloaded file from COS: %s", key)
            return content
        except Exception as exc:
            last_error = exc
            if _is_cos_not_found(exc):
                continue
            logger.error("Failed to download file from COS: %s", exc)
            raise RuntimeError(
                f"Object storage download failed: {exc}"
            ) from exc
    if last_error is not None:
        raise RuntimeError(
            f"Object storage download failed: {last_error}"
        ) from last_error
    raise RuntimeError(
        "No object storage backend is configured or available."
    )


def delete_file_from_obs(object_key: str) -> None:
    """Delete one object from COS (best-effort, all key variants)."""
    stripped = object_key.strip().lstrip("/")
    variants = _key_variants(stripped) or [stripped]
    if _get_cos_client() is None:
        return
    for key in variants:
        try:
            _cos_delete_object(key)
            logger.info("Deleted file from COS: %s", key)
        except Exception as exc:
            if _is_cos_not_found(exc):
                continue
            logger.warning("COS delete failed for %s: %s", key, exc)


def sources_parsed_prefix(source_id: str) -> str:
    """Object key prefix for MinerU output (markdown assets) for one source."""
    safe_id = source_id.replace("/", "").replace("\\", "")
    base = f"sources/parsed/{safe_id}/"
    prefix = _primary_path_prefix()
    return f"{prefix}/{base}" if prefix else base


def upload_bytes_at_key(
    object_key: str,
    file_content: bytes,
    content_type: str = "application/octet-stream",
    cache_control: str | None = None,
) -> str:
    """Upload bytes to a caller-chosen object key (COS)."""
    _cos_put_object(
        object_key,
        file_content,
        content_type,
        cache_control,
    )
    logger.info("Uploaded file to COS at key: %s", object_key)
    return object_key


def delete_objects_under_prefix(prefix: str) -> None:
    """Delete all objects whose key starts with ``prefix`` (COS)."""
    if _get_cos_client() is None:
        return
    try:
        cos_deleted = _cos_delete_prefix(prefix)
    except Exception as exc:
        logger.error("Failed to delete COS prefix %s: %s", prefix, exc)
        raise RuntimeError(
            f"Object storage batch delete failed: {exc}"
        ) from exc
    if cos_deleted:
        logger.info(
            "Deleted %s COS objects under prefix %s", cos_deleted, prefix
        )


def delete_parsed_assets_for_source(source_id: str) -> None:
    """Remove all MinerU-derived objects for ``source_id`` (all prefix roots)."""
    safe_id = source_id.replace("/", "").replace("\\", "")
    base = f"sources/parsed/{safe_id}/"
    roots = _parsed_prefix_roots()
    prefixes: list[str] = []
    if not roots:
        prefixes.append(base)
    else:
        for root in roots:
            prefix = f"{root}/{base}" if root else base
            if prefix not in prefixes:
                prefixes.append(prefix)
    for prefix in prefixes:
        delete_objects_under_prefix(prefix)
