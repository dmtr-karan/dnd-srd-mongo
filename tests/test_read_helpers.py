# File: tests/test_read_helpers.py
"""
Tests for the tiny read layer.
Run: pytest -q
"""

import os
import pytest
from pymongo import MongoClient

from scripts.read_helpers import list_classes, features_by_class_level, feature_by_slug

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/dnd_srd")


def _db():
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    return db if db is not None else client["dnd_srd"]


def test_list_classes_returns_expected_shape():
    rows = list_classes()
    assert isinstance(rows, list) and len(rows) >= 4
    assert {"name", "srd_id", "hit_die"} <= set(rows[0].keys())


def test_features_by_class_level_baseline():
    rows = features_by_class_level("Fighter", 1)
    assert isinstance(rows, list) and len(rows) >= 1
    assert {"name", "slug"} <= set(rows[0].keys())


def test_feature_by_slug_roundtrip():
    db = _db()
    any_feat = db.features.find_one({}, {"_id": 0, "slug": 1})
    assert any_feat and "slug" in any_feat
    got = feature_by_slug(any_feat["slug"])
    assert got and got["slug"] == any_feat["slug"]
