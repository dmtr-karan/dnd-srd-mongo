# File: scripts/db.py
"""
Canonical MongoDB connection helpers.

Pattern:
- env var -> client -> ping
- Resolve DB safely for PyMongo 4.x:
    * prefer DB named in the URI (client.get_default_database())
    * fallback to "dnd_srd"
"""

from __future__ import annotations

import os
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database


DEFAULT_MONGODB_URI = "mongodb://localhost:27017/dnd_srd"
DEFAULT_DB_NAME = "dnd_srd"


def get_mongo_uri() -> str:
    """Return MongoDB URI from env (MONGODB_URI) with a safe localhost default."""
    return os.getenv("MONGODB_URI", DEFAULT_MONGODB_URI)


def get_client(uri: Optional[str] = None) -> MongoClient:
    """Create a MongoClient for the given URI (or env/default)."""
    return MongoClient(uri or get_mongo_uri())


def ping(client: MongoClient) -> None:
    """Raise on failure; no return value needed."""
    client.admin.command("ping")


def get_db(client: MongoClient, fallback_db: str = DEFAULT_DB_NAME) -> Database:
    """
    Return a Database handle.
    - Prefer the DB named in the URI (if provided)
    - Otherwise fallback to 'dnd_srd'
    """
    try:
        db = client.get_default_database()
    except Exception:
        db = None
    return db if db is not None else client[fallback_db]


def close_client(client: MongoClient) -> None:
    """Close the underlying connection pool."""
    client.close()
