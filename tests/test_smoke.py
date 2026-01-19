"""
Smoke tests for the D&D 5e SRD MongoDB Prototype.
"""

from scripts.db import get_client, get_db


def _get_db():
    client = get_client()
    return get_db(client)


def test_ingest_produced_documents_and_is_reasonable():
    db = _get_db()
    assert db.classes.count_documents({}) >= 4
    assert db.features.count_documents({}) >= 1


def test_canonical_indexes_exist():
    db = _get_db()

    class_indexes = list(db.classes.list_indexes())
    feature_indexes = list(db.features.list_indexes())

    has_classes_srd_id = any(ix["key"] == {"srd_id": 1} and ix.get("unique", False) for ix in class_indexes)
    has_features_compound = any(
        ix["key"] == {"class_srd_id": 1, "level": 1, "slug": 1} and ix.get("unique", False)
        for ix in feature_indexes
    )

    assert has_classes_srd_id
    assert has_features_compound


def test_sample_query_returns_results():
    db = _get_db()
    docs = list(db.features.find({"class_name": "Fighter", "level": 1}, {"_id": 0, "name": 1, "slug": 1}))
    assert len(docs) >= 1
