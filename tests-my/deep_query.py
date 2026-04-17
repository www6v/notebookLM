"""Call local deep-searcher query API and print response."""

import requests


def query_imo() -> None:
    """Call /query/ endpoint with a fixed question and print response."""
    url = "http://0.0.0.0:8000/query/"
    params = {
        "original_query": "what is IMO?",
    }

    response = requests.get(url, params=params, timeout=120)
    print(f"status_code: {response.status_code}")
    try:
        print(response.json())
    except ValueError:
        print(response.text)


if __name__ == "__main__":
    query_imo()
