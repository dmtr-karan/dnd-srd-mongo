import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO_ROOT / "cache"


def _read_json(path: Path):
    assert path.exists(), f"Missing required cache file: {path.as_posix()}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_cache_meta_is_srd_2014_cc_by_4():
    """
    Guardrail: prevent non-SRD cache from shipping.
    We expect SRD 5.1 (CC-BY-4.0) and edition marker 5e-2014 per project convention.
    """
    meta = _read_json(CACHE_DIR / "meta.json")

    assert meta.get("edition") == "5e-2014"
    assert meta.get("license") == "CC-BY-4.0"

    # Keep these as "contains" checks so wording can evolve slightly without breaking CI.
    license_notice = (meta.get("license_notice") or "").lower()
    assert "cc-by-4.0" in license_notice or "cc by 4.0" in license_notice

    source = (meta.get("source") or "").lower()
    assert "srd" in source


def test_cache_classes_min_is_restricted_to_shipped_set():
    """
    Guardrail: cache/classes.min.json should only list classes we actually ship in this repo.
    """
    data = _read_json(CACHE_DIR / "classes.min.json")

    # classes.min.json may be:
    # - a list of {"name": "..."} dicts
    # - a dict holding a list under "classes"/"items"
    if isinstance(data, dict):
        items = data.get("classes") or data.get("items") or []
    else:
        items = data

    assert isinstance(items, list), "classes.min.json must contain a list (or a dict holding one)"

    # Normalize to a list of class names
    names = []
    for item in items:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict) and "name" in item and isinstance(item["name"], str):
            names.append(item["name"])
        else:
            raise AssertionError(f"Unexpected class entry shape in classes.min.json: {item!r}")

    shipped = {"Barbarian", "Bard", "Fighter", "Wizard"}
    assert set(names) == shipped, f"Expected shipped class set {sorted(shipped)}, got {sorted(set(names))}"
