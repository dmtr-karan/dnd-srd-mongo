"""
Smoke tests for the D&D 5e SRD MongoDB Prototype.

Goal:
- Prove that ingest ran and produced a minimal, consistent DB state.
- Verify canonical indexes exist.
- Keep assertions loose (not tied to exact counts), so the test remains stable as data grows.

How to run locally:
    # (venv) with dev deps installed
    pytest -q

Environment:
- Uses MONGODB_URI if set; defaults to local "mongodb://localhost:27017/dnd_srd".
"""

import os
from pymongo import MongoClient


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/dnd_srd")


def _get_db():
    """Return a Database handle, preferring the DB named in the URI; fallback to 'dnd_srd'."""
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    return db if db is not None else client["dnd_srd"]


def test_ingest_produced_documents_and_is_reasonable():
    """
    Basic health check:
    - We expect at least the baseline 4 classes (Barbarian, Bard, Fighter, Wizard).
    - We expect at least 1 feature in the normalized collection.
    (Exact totals may change as data grows; keep assertions minimal.)
    """
    db = _get_db()
    class_count = db.classes.count_documents({})
    feature_count = db.features.count_documents({})

    assert class_count >= 4, f"Expected ≥4 classes, found {class_count}"
    assert feature_count >= 1, f"Expected ≥1 feature, found {feature_count}"


def test_canonical_indexes_exist():
    """
    Indexes are part of the contract:
    - classes.srd_id must be unique
    - features (class_srd_id, level, slug) must be unique
    """
    db = _get_db()

    class_indexes = list(db.classes.list_indexes())
    feature_indexes = list(db.features.list_indexes())

    has_classes_srd_id = any(ix["key"] == {"srd_id": 1} and ix.get("unique", False) for ix in class_indexes)
    has_features_compound = any(
        ix["key"] == {"class_srd_id": 1, "level": 1, "slug": 1} and ix.get("unique", False)
        for ix in feature_indexes
    )

    assert has_classes_srd_id, "Missing unique index on classes.srd_id"
    assert has_features_compound, "Missing unique index on features(class_srd_id, level, slug)"


def test_sample_query_returns_results():
    """
    A tiny functional query: fetch Fighter level-1 features.
    If class names change later, update the query target here.
    """
    db = _get_db()
    cursor = db.features.find({"class_name": "Fighter", "level": 1}, {"_id": 0, "name": 1, "slug": 1})
    docs = list(cursor)

    assert len(docs) >= 1, "Expected at least one Fighter level-1 feature"
    # Optional shape check (keys exist)
    for d in docs:
        assert "name" in d and "slug" in d, f"Unexpected feature shape: {d}"