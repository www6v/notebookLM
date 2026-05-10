"""HTTP client helpers for the deep-searcher service.

Covers ``/load-files/``, ``/query/``, and ``/upload`` endpoints.
"""

import argparse
import json
import logging
from typing import Any, Dict, Optional, Union

import requests

from notebooklm_shared.config import settings

logger = logging.getLogger(__name__)


def call_load_files(
    base_url: str,
    paths: Union[str, list],
    collection_name: Optional[str] = None,
    collection_description: Optional[str] = None,
    batch_size: Optional[int] = None,
    timeout_sec: float = 3600.0,
) -> requests.Response:
    """
    POST to /load-files/ with the same body shape as main.load_files.

    Args:
        base_url: Server root, e.g. http://127.0.0.1:8000 (no trailing
            slash).
        paths: Single path or list of paths / directories.
        collection_name: Optional Milvus collection name.
        collection_description: Optional collection description.
        batch_size: Optional embedding batch size.
        timeout_sec: Request timeout (loading can be slow).

    Returns:
        The raw ``requests.Response`` for status and body inspection.
    """
    url = f"{base_url.rstrip('/')}/load-files/"
    payload: Dict[str, Any] = {"paths": paths}
    if collection_name is not None:
        payload["collection_name"] = collection_name
    if collection_description is not None:
        payload["collection_description"] = collection_description
    if batch_size is not None:
        payload["batch_size"] = batch_size
    return requests.post(url, json=payload, timeout=timeout_sec)


def deepsearch_query(query: str) -> dict | None:
    """Call /query/ endpoint with the given question."""
    root = settings.deep_searcher_base_url.rstrip("/")
    url = f"{root}/query/"
    params = {
        "original_query": query,
    }
    response = requests.get(url, params=params, timeout=120)
    if not response.ok:
        logger.error("deepsearch query failed: %s", response.text)
        return None
    logger.info("deepsearch query status_code=%s", response.status_code)
    logger.info("deepsearch query body=%s", response.text)

    return response.json()


def call_upload(oss_url: str, notebook_id: str) -> str | None:
    """POST /upload with url and notebookid; return local_path if present."""
    root = settings.deep_searcher_base_url.rstrip("/")
    endpoint = f"{root}/upload"
    payload = {
        "url": oss_url,
        "notebookid": notebook_id,
        "use_aliyun_oss_sdk": True,
    }
    response = requests.post(endpoint, json=payload, timeout=120)
    logger.info("deep upload status_code=%s", response.status_code)
    try:
        data = response.json()
    except ValueError:
        logger.warning(
            "deep upload response not JSON: %s",
            (response.text or "")[:500],
        )
        return None
    if not isinstance(data, dict):
        logger.warning("deep upload response not a dict: %s", type(data))
        return None
    raw = data.get("local_path")
    if raw is None:
        logger.warning("deep upload response missing local_path: %s", data)
        return None
    return str(raw)


def _cli_load_files() -> None:
    base_url = settings.deep_searcher_base_url
    paths = "/app/files-my/2303.06865v2.pdf"
    collection_name = "deepsearcher"
    resp = call_load_files(
        base_url=base_url,
        paths=paths,
        collection_name=collection_name,
        collection_description="collection desc",
        batch_size=8,
    )
    print(f"status_code: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except ValueError:
        print(resp.text)


def _cli_query() -> None:
    result = deepsearch_query("what is the main idea of FlexGen?")
    if result is None:
        print("query failed")
    else:
        print(result)


def _cli_upload() -> None:
    out = call_upload(
        oss_url="https://arxiv.org/pdf/2303.06865.pdf",
        notebook_id="test-notebook",
    )
    print(out)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deep searcher HTTP client demos.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="load-files",
        choices=("load-files", "query", "upload"),
        help="Which demo to run (default: load-files).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "load-files":
        _cli_load_files()
    elif args.command == "query":
        _cli_query()
    elif args.command == "upload":
        _cli_upload()


if __name__ == "__main__":
    main()
