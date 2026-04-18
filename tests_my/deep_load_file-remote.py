"""Call the running deep-searcher /load-files/ HTTP API."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
if _BACKEND.is_dir() and str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.config import settings  # noqa: E402


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
        base_url: Server root, e.g. http://127.0.0.1:8000 (no trailing slash).
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


def main() -> None:
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


if __name__ == "__main__":
    main()
