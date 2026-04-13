"""Object storage client for Alibaba Cloud OSS."""

import logging
import uuid
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_oss_bucket = None
_oss_available: Optional[bool] = None


def _get_oss_bucket():
    """Get or create an oss2 Bucket instance, or None if unavailable."""
    global _oss_bucket, _oss_available
    if _oss_available is False:
        return None
    if _oss_bucket is not None:
        return _oss_bucket
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


def _build_object_key(filename: str) -> str:
    """Build the full object key with prefix and unique suffix.

    Format: {path_prefix}/sources/{uuid}_{filename}
    """
    unique_id = uuid.uuid4().hex[:12]
    safe_name = filename.replace(" ", "_")
    prefix = settings.oss_path_prefix.strip().rstrip("/")
    base = f"sources/{unique_id}_{safe_name}"
    return f"{prefix}/{base}" if prefix else base


def upload_file_to_obs(
    file_content: bytes,
    filename: str,
    content_type: str = "application/octet-stream",
    cache_control: str | None = None,
) -> str:
    """Upload file bytes to OSS and return the object key.

    Args:
        file_content: Raw file content in bytes.
        filename: Original filename (used to derive the object key).
        content_type: MIME type of the file.

    Returns:
        The full object key stored in object storage.

    Raises:
        RuntimeError: If the upload fails or OSS is unavailable.
    """
    object_key = _build_object_key(filename)
    bucket = _require_oss_bucket()
    try:
        headers = {"Content-Type": content_type}
        if cache_control:
            headers["Cache-Control"] = cache_control
        bucket.put_object(object_key, file_content, headers=headers)
        logger.info("Uploaded file to OSS: %s", object_key)
        return object_key
    except Exception as exc:
        logger.error("Failed to upload file to OSS: %s", exc)
        raise RuntimeError(f"Object storage upload failed: {exc}") from exc


def get_file_url(object_key: str) -> str:
    """Build the public URL for an object on OSS.

    Args:
        object_key: The object key in storage.

    Returns:
        The full URL to access the object.
    """
    endpoint = settings.oss_endpoint.rstrip("/")
    bucket = settings.oss_bucket_name
    return f"{endpoint}/{bucket}/{object_key}"


def generate_presigned_url(
    object_key: str,
    expiration: int = 3600,
    response_content_disposition: str | None = None,
) -> str:
    """Generate a presigned URL for temporary access.

    Args:
        object_key: The object key in storage.
        expiration: URL validity in seconds (default 1 hour).
        response_content_disposition: Optional Content-Disposition override.

    Returns:
        A presigned URL string.

    Raises:
        RuntimeError: If URL generation fails or OSS is unavailable.
    """
    bucket = _require_oss_bucket()
    try:
        params = None
        if response_content_disposition:
            params = {
                "response-content-disposition": (
                    response_content_disposition
                )
            }
        return bucket.sign_url(
            "GET",
            object_key,
            expiration,
            params=params,
        )
    except Exception as exc:
        logger.error("Failed to generate presigned URL: %s", exc)
        raise RuntimeError(
            f"Presigned URL generation failed: {exc}"
        ) from exc


def download_file_from_obs(object_key: str) -> bytes:
    """Download a file from OSS and return its content as bytes.

    Args:
        object_key: The object key to download.

    Returns:
        The file content as bytes.

    Raises:
        RuntimeError: If the download fails or OSS is unavailable.
    """
    bucket = _require_oss_bucket()
    try:
        result = bucket.get_object(object_key)
        content = result.read()
        logger.info("Downloaded file from OSS: %s", object_key)
        return content
    except Exception as exc:
        logger.error("Failed to download file from OSS: %s", exc)
        raise RuntimeError(
            f"Object storage download failed: {exc}"
        ) from exc


def delete_file_from_obs(object_key: str) -> None:
    """Delete a file from OSS.

    Args:
        object_key: The object key to delete.

    Raises:
        RuntimeError: If deletion fails or OSS is unavailable.
    """
    bucket = _require_oss_bucket()
    try:
        bucket.delete_object(object_key)
        logger.info("Deleted file from OSS: %s", object_key)
    except Exception as exc:
        logger.error("Failed to delete file from OSS: %s", exc)
        raise RuntimeError(
            f"Object storage delete failed: {exc}"
        ) from exc
