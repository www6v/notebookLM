#!/usr/bin/env python3
"""Copy objects from Aliyun OSS to Tencent COS with path-prefix remap.

Each OSS key under ``oss_path_prefix`` is written to COS under
``cos_path_prefix`` (the segment after the OSS prefix is preserved).

Run from repo root with ``config.yaml`` / credentials configured::

    python scripts/migrate_oss_to_cos.py --dry-run
    python scripts/migrate_oss_to_cos.py

After verifying objects in COS, apply the printed SQL (or adjust
``original_url`` values that still point at OSS hosts).
"""

import argparse
import logging
import mimetypes
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "shared"))

from notebooklm_shared.config import settings  # noqa: E402

logger = logging.getLogger(__name__)


def _strip_slash(prefix: str) -> str:
    return prefix.strip().rstrip("/")


def _map_oss_key_to_cos(oss_key: str, oss_prefix: str, cos_prefix: str) -> str:
    op = _strip_slash(oss_prefix)
    cp = _strip_slash(cos_prefix)
    if not op:
        return f"{cp}/{oss_key}" if cp else oss_key
    root = f"{op}/"
    if oss_key.startswith(root):
        suffix = oss_key[len(root) :]
    elif oss_key == op:
        suffix = ""
    else:
        raise ValueError(f"Key not under OSS prefix {op!r}: {oss_key!r}")
    if cp:
        return f"{cp}/{suffix}" if suffix else cp
    return suffix


def _iter_oss_keys(bucket, prefix: str):
    import oss2

    for obj in oss2.ObjectIterator(bucket, prefix=prefix):
        yield obj.key


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy OSS objects into COS (prefix remap).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List keys and mappings without uploading.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Copy at most N objects (0 = no limit).",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )

    oss_prefix = _strip_slash(settings.oss_path_prefix)
    cos_prefix = _strip_slash(settings.cos_path_prefix)
    list_prefix = f"{oss_prefix}/" if oss_prefix else ""

    if not (
        settings.oss_access_key_id.strip()
        and settings.oss_access_key_secret.strip()
    ):
        logger.error("OSS credentials are not configured.")
        return 1
    if not (
        settings.cos_secret_id.strip()
        and settings.cos_secret_key.strip()
        and settings.cos_bucket_name.strip()
    ):
        logger.error("COS credentials / bucket are not configured.")
        return 1

    import oss2
    from qcloud_cos import CosConfig, CosS3Client

    auth = oss2.Auth(
        settings.oss_access_key_id,
        settings.oss_access_key_secret,
    )
    oss_bucket = oss2.Bucket(
        auth,
        settings.oss_endpoint,
        settings.oss_bucket_name,
    )

    region = settings.cos_region.strip() or "ap-shanghai"
    cos_conf = CosConfig(
        Region=region,
        SecretId=settings.cos_secret_id.strip(),
        SecretKey=settings.cos_secret_key.strip(),
        Scheme="https",
    )
    cos_client = CosS3Client(cos_conf)
    cos_bucket = settings.cos_bucket_name.strip()

    copied = 0
    for oss_key in _iter_oss_keys(oss_bucket, list_prefix):
        try:
            cos_key = _map_oss_key_to_cos(oss_key, oss_prefix, cos_prefix)
        except ValueError as exc:
            logger.warning("Skip %s: %s", oss_key, exc)
            continue
        if args.dry_run:
            logger.info("DRY-RUN %s -> %s", oss_key, cos_key)
        else:
            body = oss_bucket.get_object(oss_key).read()
            ctype, _ = mimetypes.guess_type(oss_key)
            kwargs = {
                "Bucket": cos_bucket,
                "Body": body,
                "Key": cos_key,
                "EnableMD5": False,
            }
            if ctype:
                kwargs["ContentType"] = ctype
            cos_client.put_object(**kwargs)
            logger.info("Copied %s -> %s (%s bytes)", oss_key, cos_key, len(body))
        copied += 1
        if args.limit and copied >= args.limit:
            break

    logger.info("Done. Objects processed: %s", copied)

    op_esc = oss_prefix.replace("'", "''")
    cp_esc = cos_prefix.replace("'", "''")
    print(
        "\n-- Suggested MySQL updates after verifying COS (adjust prefixes):\n"
        f"UPDATE sources SET file_path = REPLACE(file_path, '{op_esc}/', "
        f"'{cp_esc}/') WHERE file_path LIKE '{op_esc}/%';\n"
        f"UPDATE slide_decks SET file_path = REPLACE(file_path, '{op_esc}/', "
        f"'{cp_esc}/') WHERE file_path LIKE '{op_esc}/%';\n"
        f"UPDATE infographics SET file_path = REPLACE(file_path, '{op_esc}/', "
        f"'{cp_esc}/') WHERE file_path LIKE '{op_esc}/%';\n"
        f"UPDATE podcast_overviews SET file_path = REPLACE(file_path, "
        f"'{op_esc}/', '{cp_esc}/') WHERE file_path LIKE '{op_esc}/%';\n"
        "-- slide_decks.slides_data JSON may embed object_key strings; "
        "search for txt2imgcn and update if needed.\n"
        "-- original_url may still reference OSS host; update to COS "
        "public URL where appropriate.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
