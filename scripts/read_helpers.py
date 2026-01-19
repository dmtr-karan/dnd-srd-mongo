# File: scripts/read_helpers.py
"""
Tiny read layer for showcase & tests.
Env: MONGODB_URI (default: mongodb://localhost:27017/dnd_srd)
"""

from typing import List, Dict, Any, Optional

# Canonical DB helpers (support both: imported as package or executed as script)
try:
    from scripts.db import get_client, get_db
except ImportError:  # running as: python scripts/read_helpers.py
    from db import get_client, get_db


def _db():
    client = get_client()
    return get_db(client)


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
