"""Call remote deep-searcher /upload API and print response."""

import logging

import requests

logger = logging.getLogger(__name__)


def call_upload(oss_url: str, notebook_id: str) -> str | None:
    """POST /upload with url and notebookid; return ``local_path`` if present."""
    endpoint = "http://124.221.28.203:8000/upload"
    payload = {
        "url": oss_url,
        "notebookid": notebook_id,
        "use_aliyun_oss_sdk": True
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


if __name__ == "__main__":
    out = call_upload(
        oss_url="https://arxiv.org/pdf/2303.06865.pdf",
        notebook_id="test-notebook",
    )
    print(out)
