# File: scripts/read_helpers.py
"""
Tiny read layer for showcase & tests.
Env: MONGODB_URI (default: mongodb://localhost:27017/dnd_srd)
"""

import os
from typing import List, Dict, Any, Optional
from pymongo import MongoClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/dnd_srd")


def _db():
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    return db if db is not None else client["dnd_srd"]


def list_classes() -> List[Dict[str, Any]]:
    """Return basic info for all classes (name, srd_id, hit_die)."""
    db = _db()
    cur = db.classes.find({}, {"_id": 0, "name": 1, "srd_id": 1, "hit_die": 1}).sort("name", 1)
    return list(cur)


def features_by_class_level(class_name: str, level: int) -> List[Dict[str, Any]]:
    """Return normalized features for a given class & level (name, slug)."""
    db = _db()
    cur = db.features.find(
        {"class_name": class_name, "level": level},
        {"_id": 0, "name": 1, "slug": 1},
    ).sort("name", 1)
    return list(cur)


def feature_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Return one feature by slug (without _id), or None."""
    db = _db()
    doc = db.features.find_one({"slug": slug}, {"_id": 0})
    return doc
