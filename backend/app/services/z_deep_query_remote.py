"""Call local deep-searcher query API and print response."""

import logging

import requests

from app.config import settings

logger = logging.getLogger(__name__)


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


if __name__ == "__main__":
    result = deepsearch_query("what is the main idea of FlexGen?")
    if result is None:
        print("query failed")
    else:
        print(result)
