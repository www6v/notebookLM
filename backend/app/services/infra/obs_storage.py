"""Object storage: Tencent COS primary, Alibaba OSS fallback."""

import logging
import uuid
from typing import Any, Optional

from notebooklm_shared.config import settings

logger = logging.getLogger(__name__)

_oss_bucket = None
_oss_available: Optional[bool] = None

_cos_client = None
_cos_available: Optional[bool] = None


def _normalize_prefix(prefix: str) -> str:
    return prefix.strip().rstrip("/")


def _cos_configured() -> bool:
    return bool(
        settings.cos_secret_id.strip()
        and settings.cos_secret_key.strip()
        and settings.cos_bucket_name.strip()
    )


def _primary_path_prefix() -> str:
    """Logical key prefix for new uploads (COS layout when COS is configured)."""
    if _cos_configured():
        return _normalize_prefix(settings.cos_path_prefix)
    return _normalize_prefix(settings.oss_path_prefix)


def _key_variants(object_key: str) -> list[str]:
    """Try legacy OSS prefix and COS prefix during migration."""
    raw = object_key.strip().lstrip("/")
    if not raw:
        return []
    oss_p = _normalize_prefix(settings.oss_path_prefix)
    cos_p = _normalize_prefix(settings.cos_path_prefix)
    keys: list[str] = [raw]
    if oss_p and cos_p and oss_p != cos_p:
        if raw.startswith(f"{oss_p}/") or raw == oss_p:
            suffix = raw[len(oss_p) :].lstrip("/")
            alt = f"{cos_p}/{suffix}" if suffix else cos_p
            if alt != raw:
                keys.append(alt)
        if raw.startswith(f"{cos_p}/") or raw == cos_p:
            suffix = raw[len(cos_p) :].lstrip("/")
            alt = f"{oss_p}/{suffix}" if suffix else oss_p
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
    cos_p = _normalize_prefix(settings.cos_path_prefix)
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
            Bucket=settings.cos_bucket_name.strip(),
            Key=object_key,
        )
        return True
    except Exception as exc:
        if _is_cos_not_found(exc):
            return False
        logger.warning("COS head_object failed for %s: %s", object_key, exc)
        return False


def _oss_head_exists(object_key: str) -> bool:
    bucket = _get_oss_bucket()
    if bucket is None:
        return False
    try:
        bucket.head_object(object_key)
        return True
    except Exception as exc:
        if _is_oss_not_found(exc):
            return False
        logger.warning("OSS head_object failed for %s: %s", object_key, exc)
        return False


def _parsed_prefix_roots() -> list[str]:
    """Distinct path roots used for MinerU parsed assets (OSS vs COS prefix)."""
    roots: list[str] = []
    for root in (
        _normalize_prefix(settings.oss_path_prefix),
        _normalize_prefix(settings.cos_path_prefix),
    ):
        if root and root not in roots:
            roots.append(root)
    return roots


def _get_oss_bucket():
    """Get or create an oss2 Bucket instance, or None if unavailable."""
    global _oss_bucket, _oss_available
    if _oss_available is False:
        return None
    if _oss_bucket is not None:
        return _oss_bucket
    if not (
        settings.oss_access_key_id.strip()
        and settings.oss_access_key_secret.strip()
    ):
        _oss_available = False
        return None
    try:
        import oss2

        auth = oss2.Auth(
            settings.oss_access_key_id,
            settings.oss_access_key_secret,
        )
        _oss_bucket = oss2.Bucket(
            auth,
            settings.oss_endpoint,
            settings.oss_bucket_name,
        )
        _oss_bucket.get_bucket_info()
        _oss_available = True
        logger.info("Alibaba Cloud OSS initialized successfully")
        return _oss_bucket
    except Exception as exc:
        _oss_available = False
        logger.warning("Alibaba Cloud OSS unavailable: %s", exc)
        return None


def _require_oss_bucket():
    """Return a working OSS bucket or raise."""
    bucket = _get_oss_bucket()
    if bucket is None:
        raise RuntimeError(
            "Alibaba Cloud OSS is not configured or unavailable. "
            "Set OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, "
            "OSS_ENDPOINT, and OSS_BUCKET_NAME."
        )
    return bucket


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

        region = settings.cos_region.strip() or "ap-shanghai"
        conf = CosConfig(
            Region=region,
            SecretId=settings.cos_secret_id.strip(),
            SecretKey=settings.cos_secret_key.strip(),
            Scheme="https",
        )
        client = CosS3Client(conf)
        client.head_bucket(Bucket=settings.cos_bucket_name.strip())
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
            "Set COS_SECRET_ID, COS_SECRET_KEY, COS_BUCKET_NAME, and COS_REGION."
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


def _is_oss_not_found(exc: BaseException) -> bool:
    try:
        import oss2.exceptions

        return isinstance(exc, oss2.exceptions.NoSuchKey)
    except ImportError:
        return False


def _cos_put_object(
    object_key: str,
    body: bytes,
    content_type: str,
    cache_control: str | None,
) -> None:
    client = _require_cos_client()
    kwargs: dict[str, Any] = {
        "Bucket": settings.cos_bucket_name.strip(),
        "Body": body,
        "Key": object_key,
        "EnableMD5": False,
    }
    if content_type:
        kwargs["ContentType"] = content_type
    if cache_control:
        kwargs["CacheControl"] = cache_control
    client.put_object(**kwargs)


def _oss_put_object(
    object_key: str,
    body: bytes,
    content_type: str,
    cache_control: str | None,
) -> None:
    bucket = _require_oss_bucket()
    headers = {"Content-Type": content_type}
    if cache_control:
        headers["Cache-Control"] = cache_control
    bucket.put_object(object_key, body, headers=headers)


def _cos_get_object(object_key: str) -> bytes:
    client = _require_cos_client()
    resp = client.get_object(
        Bucket=settings.cos_bucket_name.strip(),
        Key=object_key,
    )
    body = resp["Body"]
    if hasattr(body, "read"):
        return body.read()
    return bytes(body)


def _oss_get_object(object_key: str) -> bytes:
    bucket = _require_oss_bucket()
    result = bucket.get_object(object_key)
    return result.read()


def _cos_delete_object(object_key: str) -> None:
    client = _require_cos_client()
    client.delete_object(
        Bucket=settings.cos_bucket_name.strip(),
        Key=object_key,
    )


def _oss_delete_object(object_key: str) -> None:
    bucket = _require_oss_bucket()
    bucket.delete_object(object_key)


def _cos_delete_prefix(prefix: str) -> int:
    client = _require_cos_client()
    bucket = settings.cos_bucket_name.strip()
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


def _oss_delete_prefix(prefix: str) -> int:
    bucket = _require_oss_bucket()
    import oss2

    deleted = 0
    for obj in oss2.ObjectIterator(bucket, prefix=prefix):
        bucket.delete_object(obj.key)
        deleted += 1
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
    """Upload file bytes and return the object key (COS first, OSS fallback)."""
    object_key = _build_object_key(filename)
    if _get_cos_client() is not None:
        try:
            _cos_put_object(
                object_key,
                file_content,
                content_type,
                cache_control,
            )
            logger.info("Uploaded file to COS: %s", object_key)
            return object_key
        except Exception as exc:
            logger.warning(
                "COS upload failed, falling back to OSS: %s", exc
            )
    try:
        _oss_put_object(
            object_key,
            file_content,
            content_type,
            cache_control,
        )
        logger.info("Uploaded file to OSS: %s", object_key)
        return object_key
    except Exception as exc:
        logger.error("Object storage upload failed: %s", exc)
        raise RuntimeError(
            f"Object storage upload failed: {exc}"
        ) from exc


def get_file_url(object_key: str) -> str:
    """Build a public HTTPS URL for the object (COS when configured)."""
    if _cos_configured() and settings.cos_public_base_url.strip():
        base = settings.cos_public_base_url.rstrip("/")
        pub_key = _preferred_public_object_key(object_key)
        return f"{base}/{pub_key}"
    key = object_key.strip().lstrip("/")
    endpoint = settings.oss_endpoint.rstrip("/")
    bucket = settings.oss_bucket_name
    return f"{endpoint}/{bucket}/{key}"


def generate_presigned_url(
    object_key: str,
    expiration: int = 3600,
    response_content_disposition: str | None = None,
) -> str:
    """Presigned GET URL (COS first, OSS fallback; probes object location)."""
    params: dict[str, str] | None = None
    if response_content_disposition:
        params = {
            "response-content-disposition": response_content_disposition,
        }
    stripped = object_key.strip().lstrip("/")
    variants = _key_variants(stripped) or [stripped]
    cos_client = _get_cos_client()
    if cos_client is not None:
        for key in variants:
            if not _cos_head_exists(key):
                continue
            try:
                return cos_client.get_presigned_url(
                    Method="GET",
                    Bucket=settings.cos_bucket_name.strip(),
                    Key=key,
                    Expired=expiration,
                    Params=params or {},
                )
            except Exception as exc:
                logger.error("Failed to generate COS presigned URL: %s", exc)
                raise RuntimeError(
                    f"Presigned URL generation failed: {exc}"
                ) from exc
    oss_bucket = _get_oss_bucket()
    if oss_bucket is not None:
        for key in variants:
            if not _oss_head_exists(key):
                continue
            try:
                return oss_bucket.sign_url(
                    "GET",
                    key,
                    expiration,
                    params=params,
                )
            except Exception as exc:
                logger.error("Failed to generate OSS presigned URL: %s", exc)
                raise RuntimeError(
                    f"Presigned URL generation failed: {exc}"
                ) from exc
    raise RuntimeError(
        "Presigned URL generation failed: object not found in COS or OSS, "
        "or no object storage backend is configured."
    )


def download_file_from_obs(object_key: str) -> bytes:
    """Download bytes (COS first for each key variant, then OSS)."""
    stripped = object_key.strip().lstrip("/")
    variants = _key_variants(stripped) or [stripped]
    last_error: BaseException | None = None
    if _get_cos_client() is not None:
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
    if _get_oss_bucket() is not None:
        for key in variants:
            try:
                content = _oss_get_object(key)
                logger.info("Downloaded file from OSS: %s", key)
                return content
            except Exception as exc:
                last_error = exc
                if _is_oss_not_found(exc):
                    continue
                logger.error("Failed to download file from OSS: %s", exc)
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
    """Delete one object from COS and/or OSS (best-effort, all key variants)."""
    stripped = object_key.strip().lstrip("/")
    variants = _key_variants(stripped) or [stripped]
    if _get_cos_client() is not None:
        for key in variants:
            try:
                _cos_delete_object(key)
                logger.info("Deleted file from COS: %s", key)
            except Exception as exc:
                if _is_cos_not_found(exc):
                    continue
                logger.warning("COS delete failed for %s: %s", key, exc)
    if _get_oss_bucket() is not None:
        for key in variants:
            try:
                _oss_delete_object(key)
                logger.info("Deleted file from OSS: %s", key)
            except Exception as exc:
                if _is_oss_not_found(exc):
                    continue
                logger.warning("OSS delete failed for %s: %s", key, exc)


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
    """Upload bytes to a caller-chosen object key (COS first, OSS fallback)."""
    if _get_cos_client() is not None:
        try:
            _cos_put_object(
                object_key,
                file_content,
                content_type,
                cache_control,
            )
            logger.info("Uploaded file to COS at key: %s", object_key)
            return object_key
        except Exception as exc:
            logger.warning(
                "COS upload failed, falling back to OSS: %s", exc
            )
    try:
        _oss_put_object(
            object_key,
            file_content,
            content_type,
            cache_control,
        )
        logger.info("Uploaded file to OSS at key: %s", object_key)
        return object_key
    except Exception as exc:
        logger.error("Object storage upload failed: %s", exc)
        raise RuntimeError(
            f"Object storage upload failed: {exc}"
        ) from exc


def delete_objects_under_prefix(prefix: str) -> None:
    """Delete all objects whose key starts with ``prefix`` (COS and OSS)."""
    cos_deleted = 0
    oss_deleted = 0
    cos_err: BaseException | None = None
    oss_err: BaseException | None = None
    if _get_cos_client() is not None:
        try:
            cos_deleted = _cos_delete_prefix(prefix)
        except Exception as exc:
            cos_err = exc
            logger.error("Failed to delete COS prefix %s: %s", prefix, exc)
    if _get_oss_bucket() is not None:
        try:
            oss_deleted = _oss_delete_prefix(prefix)
        except Exception as exc:
            oss_err = exc
            logger.error("Failed to delete OSS prefix %s: %s", prefix, exc)
    if cos_deleted:
        logger.info(
            "Deleted %s COS objects under prefix %s", cos_deleted, prefix
        )
    if oss_deleted:
        logger.info(
            "Deleted %s OSS objects under prefix %s", oss_deleted, prefix
        )
    if cos_err and oss_err:
        raise RuntimeError(
            f"Object storage batch delete failed: {cos_err}"
        ) from cos_err


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
