from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

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
