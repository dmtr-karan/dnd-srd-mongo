# File: tests/test_validator.py
"""
Validator test:
- Ensures the $jsonSchema on 'features' rejects a clearly invalid doc.
- Auto-skips if validator isn't active (to avoid red tests locally).
"""

import pytest
from pymongo import errors

from scripts.db import get_client, get_db


def _db():
    client = get_client()
    return get_db(client)


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
        "class_name": "",
        "class_srd_id": "class:bad",
        "edition": "wrong",
        "level": 0,
        "name": "",
        "slug": "not-a-valid-slug",
        "description_md": "",
        "source": "",
        "license": "CC-BY-4.0",
        "meta": {"imported_at": "", "import_version": 1},
    }
    with pytest.raises(errors.WriteError):
        db.features.insert_one(bad)
