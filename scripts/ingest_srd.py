#!/usr/bin/env python3
"""
ingest_srd.py — SRD 5.1 (5e 2014) JSON → MongoDB

Purpose:
  Validate canonical class JSON files against the repo JSON Schema,
  upsert data into MongoDB (both embedded classes and normalized features),
  emit lightweight cache files, and print a brief ingest report.

Pipeline:
  1) Validate JSON files in data/srd/classes/ using schemas/srd-class-5e-2014.json
  2) Upsert into MongoDB:
       - classes   (embedded features_by_level)
       - features  (normalized per feature per level)
  3) Emit cache/:
       - classes.min.json  (compact summaries for UI/readme)
       - meta.json         (counts, timestamp, license)
  4) Print a brief ingest report

Environment:
  MONGODB_URI (default: mongodb://localhost:27017/dnd_srd)

Idempotence:
  Safe to re-run; unique indexes prevent duplicates and the script upserts records.

Usage (Windows example):
  # Start MongoDB (service)
  net start MongoDB
  # OR run portable mongod
  mongod --dbpath "C:\\path\\to\\your\\data"

  # Run ingest
  python scripts/ingest_srd.py
"""

import os
import json
import datetime as dt
from pathlib import Path
from typing import Dict, Any, List, Tuple

from pymongo import MongoClient, UpdateOne
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]  # repo root (assuming scripts/ingest_srd.py)
DATA_DIR = ROOT / "data" / "srd" / "classes"
CACHE_DIR = ROOT / "cache"

DEFAULT_URI = "mongodb://localhost:27017/dnd_srd"


SCHEMA_PATH = ROOT / "schemas" / "srd-class-5e-2014.json"
with open(SCHEMA_PATH, "r", encoding="utf-8") as _fh:
    SCHEMA: Dict[str, Any] = json.load(_fh)


def iso_now() -> str:
    """Return current UTC time as an RFC-3339/ISO-8601 string (Zulu, no micros)."""
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def slugify(text: str) -> str:
    """
    Tiny dependency-free slug generation for feature names.
    - Lowercase ASCII
    - Non [a-z0-9] -> hyphen
    - Collapse multiple hyphens; trim leading/trailing hyphens
    Examples:
      "Second Wind" -> "second-wind"
      "Rage (2/long rest)" -> "rage-2-long-rest"
    """
    import re
    t = text.lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    t = re.sub(r"-+", "-", t).strip("-")
    return t


def class_summary(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a compact public summary of a class document for cache/classes.min.json.
    Returns: {name, srd_id, hit_die, primary_abilities, levels_supported, feature_count, edition, license}
    """
    levels = [e.get("level") for e in doc.get("features_by_level", [])]
    feature_count = sum(len(e.get("features", [])) for e in doc.get("features_by_level", []))
    return {
        "name": doc["name"],
        "srd_id": doc["srd_id"],
        "hit_die": doc["hit_die"],
        "primary_abilities": doc["primary_abilities"],
        "levels_supported": sorted(levels),
        "feature_count": feature_count,
        "edition": doc.get("edition"),
        "license": doc.get("license")
    }


def load_class_files() -> List[Tuple[Path, Dict[str, Any]]]:
    """
    Load all canonical class JSON files from data/srd/classes/.
    Returns: list of (path, json_dict) in filename-sorted order.
    """
    files = sorted(Path(DATA_DIR).glob("*.json"))
    items = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        items.append((f, data))
    return items


def validate_classes(items: List[Tuple[Path, Dict[str, Any]]]) -> List[Tuple[Path, Dict[str, Any]]]:
    validator = Draft7Validator(SCHEMA)
    errors = []
    valid = []
    for path, data in items:
        errs = sorted(validator.iter_errors(data), key=lambda e: e.path)
        if errs:
            for e in errs:
                errors.append(f"{path.name}: {list(e.path)} -> {e.message}")
        else:
            valid.append((path, data))
    if errors:
        print("Validation errors:")
        for e in errors:
            print(" -", e)
        raise SystemExit(2)
    return valid


def connect_mongo() -> MongoClient:
    uri = os.getenv("MONGODB_URI", DEFAULT_URI)
    client = MongoClient(uri)
    return client


def upsert_classes_and_features(client: MongoClient, docs: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
        Upsert the canonical classes and normalized features into MongoDB.

        Behavior:
          - Resolve database safely for PyMongo 4.x:
              * Use client.get_default_database() if available from URI
              * Fallback to "dnd_srd"
          - Ensure canonical indexes:
              * classes.srd_id → unique
              * features (class_srd_id, level, slug) → unique
              * features (class_name, level) → helper for simple queries
          - Clean up legacy/demo remnants (old index names, malformed docs)
          - Upsert:
              * classes: replace by srd_id; attach meta (levels, feature_count, imported_at)
              * features: normalized per feature per level; stable slug = "{class}-{feature}-l{level}"
          - Return counts for brief report and cache metadata.

        Idempotence:
          Multiple runs converge to the same state due to unique indexes + upserts.
        """
    # DB select and collection handles follow…
    # Resolve DB (PyMongo 4.x safe — no truthiness checks)
    # PyMongo 4.x: prefer database from the URI; fall back to named DB if absent.
    db = client.get_default_database()
    if db is None:
        db = client["dnd_srd"]

    classes = db["classes"]
    features = db["features"]

    # --- one-time cleanup to avoid conflicts with older demos ---
    # Drop legacy unique index on (class_name, level, name) if it exists.
    # That index name came from your earlier demos (e.g., basic_ops).
    try:
        features.drop_index("uniq_class_level_name")
    except Exception:
        pass

    # Remove legacy demo docs that lack the canonical key we use now.
    features.delete_many({"class_srd_id": {"$exists": False}})
    # Why: remove any legacy/demo docs that lack our canonical foreign key
    #      (class_srd_id). Keeps the normalized collection coherent.
    # -------------------------------------------------------------

    # Guard: if a previous run created the srd_id index with different options/name,
    #        drop that exact key to avoid conflicts, then recreate with canonical options.
    for ix in classes.list_indexes():
        if list(ix["key"].items()) == [("srd_id", 1)]:
            classes.drop_index(ix["name"])
            break
    # ----------------------------------------------------------------------

    # Indexes (idempotent)
    classes.create_index("srd_id", unique=True)
    classes.create_index("name")

    # Guard: normalize any prior index definition on (class_srd_id, level, slug)
    #        to our canonical unique index (avoid duplicate definitions/name clashes).
    for ix in features.list_indexes():
        if list(ix["key"].items()) == [("class_srd_id", 1), ("level", 1), ("slug", 1)]:
            features.drop_index(ix["name"])
            break
    # ----------------------------------------------------------------------

    # Canonical uniqueness for features is (class_srd_id, level, slug)
    features.create_index(
        [("class_srd_id", 1), ("level", 1), ("slug", 1)],
        unique=True
    )
    features.create_index([("class_name", 1), ("level", 1)])

    # Upsert classes (replace on srd_id)
    class_ops = []
    now = iso_now()
    for c in docs:
        c = dict(c)  # shallow copy
        # Why: meta mirrors what the cache shows (levels + feature_count) and tracks ingest provenance.
        feature_count = sum(len(e.get("features", [])) for e in c.get("features_by_level", []))
        c["meta"] = {
            "levels_supported": [e["level"] for e in c["features_by_level"]],
            "feature_count": feature_count,
            "imported_at": now,
            "import_version": 1,
        }
        class_ops.append(UpdateOne({"srd_id": c["srd_id"]}, {"$set": c}, upsert=True))
    if class_ops:
        classes.bulk_write(class_ops)

    # Upsert features (normalized)
    feat_ops = []
    for c in docs:
        cls_name = c["name"]
        cls_id = c["srd_id"]
        edition = c["edition"]
        license_ = c["license"]
        for level_block in c.get("features_by_level", []):
            lvl = level_block["level"]
            for f in level_block["features"]:
                base_slug = slugify(f["name"])
                slug = f"{slugify(cls_name)}-{base_slug}-l{lvl}"
                # Deterministic slug = "<class>-<feature>-l<level>" for deduplication + indexing stability.
                feat_doc = {
                    "class_name": cls_name,
                    "class_srd_id": cls_id,
                    "edition": edition,
                    "level": lvl,
                    "name": f["name"],
                    "slug": slug,
                    "srd_feature_id": f.get("srd_feature_id"),
                    "description_md": f["description_md"],
                    "source": f["source"],
                    "license": license_,
                    "meta": {"imported_at": now, "import_version": 1},
                }
                feat_ops.append(
                    UpdateOne(
                        {"class_srd_id": cls_id, "level": lvl, "slug": slug},
                        {"$set": feat_doc},
                        upsert=True,
                    )
                )
    if feat_ops:
        features.bulk_write(feat_ops)
        # Bulk write: fewer round-trips + atomic batch of upserts for consistency.

    # Counts
    # Final counts reflect the idempotent end-state after upserts.
    class_count = db.classes.count_documents({})
    feature_count = db.features.count_documents({})
    return class_count, feature_count


def write_caches(docs: List[Dict[str, Any]], class_count: int, feature_count: int) -> None:
    """
    Write cache files for quick consumption:
      - cache/classes.min.json: array of class summaries (compact JSON)
      - cache/meta.json: ingest metadata (timestamp, license, counts, class names, levels_supported)
    Side effects: creates cache/ if missing.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    summaries = [class_summary(d) for d in docs]

    # classes.min.json (fully minified, no whitespace)
    with open(CACHE_DIR / "classes.min.json", "w", encoding="utf-8") as fh:
        json.dump(summaries, fh, separators=(",", ":"))

    meta = {
        "generated_at": iso_now(),
        "edition": "5e-2014",
        "license": "CC-BY-4.0",
        "source": "SRD 5.1",
        "class_documents": class_count,
        "feature_documents": feature_count,
        "classes": [s["name"] for s in summaries],
        "levels_supported": sorted(
            {lv for d in docs for lv in [e["level"] for e in d["features_by_level"]]}
        ),
        "license_notice": "D&D 5.1 SRD © Wizards of the Coast — CC-BY-4.0 (see LICENSE)",
        "attribution": (
            "Dungeons & Dragons® 5.1 System Reference Document (SRD) — Wizards of the Coast. "
            "Source: https://dnd.wizards.com/resources/systems-reference-document"
        ),
    }

    with open(CACHE_DIR / "meta.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)


def main() -> None:
    """
    Entrypoint: load → validate → upsert → cache → report.
    Fails fast on missing files or schema errors; exits with nonzero on validation failure.
    Printout shows per-file feature totals, DB totals, and cache paths.
    """
    print("SRD 5.1 ingest started.")
    items = load_class_files()
    if not items:
        print(f"No class JSON found in {DATA_DIR}")
        raise SystemExit(1)
    print(f"Found {len(items)} class files.")

    valid = validate_classes(items)
    print(f"Validated {len(valid)} class files.")

    docs = [data for _, data in valid]
    client = connect_mongo()
    class_count, feature_count = upsert_classes_and_features(client, docs)
    write_caches(docs, class_count, feature_count)

    # brief report
    file_counts = {Path(p).stem: sum(len(lvl["features"]) for lvl in d["features_by_level"]) for p, d in valid}
    print("\nIngest report")
    print("-------------")
    for stem, cnt in file_counts.items():
        print(f"{stem}: {cnt} features")
    print(f"\nMongoDB totals → classes: {class_count}, features: {feature_count}")
    print("Cache written → cache/classes.min.json, cache/meta.json")
    print("\nDone.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MongoDND — SRD ingest & validation")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Execute validation routine and exit."
    )
    args = parser.parse_args()

    if args.validate:
        # Execute validation workflow
        main()
    else:
        # Default execution path
        main()
