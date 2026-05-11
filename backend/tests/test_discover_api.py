"""Discover and subscription API surface checks (no live DB required)."""


def test_openapi_includes_discover_routes() -> None:
    from app.main import app

    paths = app.openapi()["paths"]
    assert "/api/public/discover/notebooks" in paths
    assert "/api/public/discover/notebooks/{notebook_id}" in paths
    assert "/api/discover/notebooks/{notebook_id}/subscribe" in paths
    assert "/api/notebooks/published" in paths
    assert "/api/notebooks/subscriptions" in paths
