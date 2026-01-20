"""
API grounding tests (P4).

Goals:
- Cache-backed endpoints should always work (no DB required).
- Feature endpoints:
  - If Mongo env is not set -> expect 503 (service degrades gracefully)
  - If Mongo env is set -> expect 200 + correct shape
"""

import os

from fastapi.testclient import TestClient

from app.main import app


def _mongo_configured() -> bool:
    # Must match the env check used by app/routes.py
    return bool(os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL") or os.getenv("MONGO_URI"))


client = TestClient(app)


def test_meta_returns_expected_keys():
    r = client.get("/meta")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    # minimal expectations (stable across runs)
    assert {"edition", "classes", "levels_supported"} <= set(data.keys())


def test_classes_fighter_returns_payload():
    r = client.get("/classes/fighter")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert data.get("name") == "Fighter"


def test_features_by_slug_behaves_with_or_without_mongo():
    # Any slug works for the "Mongo not configured" branch;
    # for the configured branch, we just check it returns JSON without asserting a specific slug exists.
    r = client.get("/features/any-slug")

    if not _mongo_configured():
        assert r.status_code == 503
        assert "Mongo not configured" in r.json().get("detail", "")
    else:
        # If Mongo is configured but slug doesn't exist, 404 is valid; if it exists, 200 is valid.
        assert r.status_code in (200, 404)
