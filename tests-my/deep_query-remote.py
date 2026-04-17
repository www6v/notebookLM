"""Call local deep-searcher query API and print response."""

import requests


def query_imo() -> None:
    """Call /query/ endpoint with a fixed question and print response."""
    url = "http://124.221.28.203:8000/query/"
    params = {
        # "original_query": "what is IMO?",
        "original_query": "what is the main idea of FlexGen?",                
    }

    response = requests.get(url, params=params, timeout=120)
    print(f"status_code: {response.status_code}")
    try:
        print(response.json())
    except ValueError:
        print(response.text)


if __name__ == "__main__":
    query_imo()
