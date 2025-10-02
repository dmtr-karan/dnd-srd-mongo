# File: tests/test_validator.py
"""
Validator test:
- Ensures the $jsonSchema on 'features' rejects a clearly invalid doc.
- Auto-skips if validator isn't active (to avoid red tests locally).
"""

import os
import pytest
from pymongo import MongoClient, errors

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/dnd_srd")


def _db():
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    return db if db is not None else client["dnd_srd"]


def _validator_active(db) -> bool:
    info = db.command({"listCollections": 1, "filter": {"name": "features"}})
    cols = info.get("cursor", {}).get("firstBatch", [])
    if not cols:
        return False
    validator = cols[0].get("options", {}).get("validator")
    return bool(validator)


@pytest.mark.skipif(
    not _validator_active(_db()), reason="features validator not active; run feature_validator.mongo.js first"
)
def test_invalid_feature_is_rejected():
    db = _db()
    bad = {
        # intentionally wrong / missing required fields
        "class_name": "",                 # empty (minLength 1)
        "class_srd_id": "class:bad",      # fails pattern
        "edition": "wrong",               # not '5e-2014'
        "level": 0,                       # out of bounds
        "name": "",                       # empty
        "slug": "not-a-valid-slug",       # pattern expects ...-l<level>
        "description_md": "",
        "source": "",
        "license": "CC-BY-4.0",
        "meta": {"imported_at": "", "import_version": 1},
    }
    with pytest.raises(errors.WriteError):
        db.features.insert_one(bad)
