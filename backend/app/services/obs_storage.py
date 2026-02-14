"""OBS (Object Storage Service) client for file uploads.

Uses boto3 with S3-compatible API to interact with OBS.
"""

import uuid
import logging
from io import BytesIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy-initialized client
_s3_client = None


def _get_s3_client():
    """Get or create a boto3 S3 client for OBS."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.obs_endpoint,
            aws_access_key_id=settings.obs_access_key,
            aws_secret_access_key=settings.obs_secret_key,
            config=Config(
                s3={"addressing_style": "path"},
                signature_version="s3v4",
            ),
        )
    return _s3_client


def _build_object_key(filename: str) -> str:
    """Build the full object key with prefix and unique suffix.

    Format: {path_prefix}/sources/{uuid}_{filename}
    """
    unique_id = uuid.uuid4().hex[:12]
    safe_name = filename.replace(" ", "_")
    return f"{settings.obs_path_prefix}/sources/{unique_id}_{safe_name}"


def upload_file_to_obs(
    file_content: bytes,
    filename: str,
    content_type: str = "application/octet-stream",
) -> str:
    """Upload file bytes to OBS and return the object key.

    Args:
        file_content: Raw file content in bytes.
        filename: Original filename (used to derive the object key).
        content_type: MIME type of the file.

    Returns:
        The full object key stored in OBS.

    Raises:
        RuntimeError: If the upload fails.
    """
    client = _get_s3_client()
    object_key = _build_object_key(filename)

    try:
        client.upload_fileobj(
            Fileobj=BytesIO(file_content),
            Bucket=settings.obs_bucket_name,
            Key=object_key,
            ExtraArgs={"ContentType": content_type},
        )
        logger.info("Uploaded file to OBS: %s", object_key)
        return object_key
    except ClientError as exc:
        logger.error("Failed to upload file to OBS: %s", exc)
        raise RuntimeError(f"OBS upload failed: {exc}") from exc


def get_file_url(object_key: str) -> str:
    """Build the public URL for an object in OBS.

    Args:
        object_key: The object key in OBS.

    Returns:
        The full URL to access the object.
    """
    return (
        f"{settings.obs_endpoint}/"
        f"{settings.obs_bucket_name}/{object_key}"
    )


def generate_presigned_url(
    object_key: str, expiration: int = 3600
) -> str:
    """Generate a presigned URL for temporary access.

    Args:
        object_key: The object key in OBS.
        expiration: URL validity in seconds (default 1 hour).

    Returns:
        A presigned URL string.
    """
    client = _get_s3_client()
    try:
        url = client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.obs_bucket_name,
                "Key": object_key,
            },
            ExpiresIn=expiration,
        )
        return url
    except ClientError as exc:
        logger.error("Failed to generate presigned URL: %s", exc)
        raise RuntimeError(
            f"Presigned URL generation failed: {exc}"
        ) from exc


def download_file_from_obs(object_key: str) -> bytes:
    """Download a file from OBS and return its content as bytes.

    Args:
        object_key: The object key to download.

    Returns:
        The file content as bytes.

    Raises:
        RuntimeError: If the download fails.
    """
    client = _get_s3_client()
    try:
        buffer = BytesIO()
        client.download_fileobj(
            Bucket=settings.obs_bucket_name,
            Key=object_key,
            Fileobj=buffer,
        )
        buffer.seek(0)
        return buffer.read()
    except ClientError as exc:
        logger.error("Failed to download file from OBS: %s", exc)
        raise RuntimeError(
            f"OBS download failed: {exc}"
        ) from exc


def delete_file_from_obs(object_key: str) -> None:
    """Delete a file from OBS.

    Args:
        object_key: The object key to delete.
    """
    client = _get_s3_client()
    try:
        client.delete_object(
            Bucket=settings.obs_bucket_name,
            Key=object_key,
        )
        logger.info("Deleted file from OBS: %s", object_key)
    except ClientError as exc:
        logger.error("Failed to delete file from OBS: %s", exc)
        raise RuntimeError(
            f"OBS delete failed: {exc}"
        ) from exc
