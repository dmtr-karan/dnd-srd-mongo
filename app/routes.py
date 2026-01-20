from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

# Reuse existing Mongo-backed read helpers
# NOTE: scripts/ is a plain folder in this repo, so importing may require PYTHONPATH to include repo root.
# If this import fails in your environment, we will switch to a tiny local wrapper module under app/.
from scripts.read_helpers import feature_by_slug, features_by_class_level  # type: ignore

router = APIRouter()

# Repo root = parent of /app
REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO_ROOT / "cache"
CLASSES_DIR = REPO_ROOT / "data" / "srd" / "classes"


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {path.as_posix()}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in {path.name}: {e.msg}") from e


def _slugify_class_name(name: str) -> str:
    # Keep it deterministic + simple: "Fighter" -> "fighter", "Arcane Trickster" -> "arcane-trickster"
    return "-".join(name.strip().lower().split())


def _mongo_configured() -> bool:
    """
    Feature endpoints rely on Mongo.
    Consider Mongo "configured" if a URI is present via env.
    """
    # Align with common naming (you may already use one of these in your repo/secrets)
    return bool(os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL") or os.getenv("MONGO_URI"))


@router.get("/meta")
def get_meta() -> Any:
    return _read_json(CACHE_DIR / "meta.json")


@router.get("/classes")
def list_classes() -> Any:
    return _read_json(CACHE_DIR / "classes.min.json")


@router.get("/classes/{name}")
def get_class(name: str) -> Any:
    slug = _slugify_class_name(name)
    return _read_json(CLASSES_DIR / f"{slug}.json")


@router.get("/classes/{name}/features")
def get_class_features(
    name: str,
    level: int = Query(..., ge=1, le=20, description="Character level to retrieve features for"),
) -> Any:
    """
    Mongo-backed: returns features for a class at a given level.
    """
    if not _mongo_configured():
        raise HTTPException(status_code=503, detail="Mongo not configured; feature endpoints unavailable.")

    class_name = name.strip().title()
    try:
        return features_by_class_level(class_name=class_name, level=level)
    except KeyError as e:
        # read_helpers may raise KeyError when something isn't found
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read features: {e}") from e


@router.get("/features/{slug}")
def get_feature(slug: str) -> Any:
    """
    Mongo-backed: returns a single feature by slug.
    """
    if not _mongo_configured():
        raise HTTPException(status_code=503, detail="Mongo not configured; feature endpoints unavailable.")

    try:
        result = feature_by_slug(slug=slug)
        if not result:
            raise HTTPException(status_code=404, detail="Feature not found")
        return result
    except HTTPException:
        raise
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read feature: {e}") from e
