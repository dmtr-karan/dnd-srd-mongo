"""
Atlas integration smoke test.

Runs only when Atlas secrets are present.
Behavior:
- If ATLAS_MONGODB_URI is missing/empty -> SKIP (graceful)
- Else: connect -> ping -> disconnect
"""

import os

import pytest
from pymongo import MongoClient


ATLAS_URI_ENV = "ATLAS_MONGODB_URI"


def test_atlas_connect_ping_disconnect():
    uri = os.getenv(ATLAS_URI_ENV)
    if not uri:
        pytest.skip(f"{ATLAS_URI_ENV} not set; skipping Atlas integration smoke test.")

    client = MongoClient(uri)
    try:
        client.admin.command("ping")
    finally:
        client.close()
