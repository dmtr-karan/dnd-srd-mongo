import json
from pathlib import Path

from jsonschema import Draft7Validator


def _load_schema():
    root = Path(__file__).resolve().parents[1]
    schema_path = root / "schemas" / "srd-spell-5e-2014.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def test_spell_schema_accepts_minimal_spell_no_materials():
    schema = _load_schema()
    validator = Draft7Validator(schema)

    spell = {
        "name": "Magic Missile",
        "srd_id": "spell:magic-missile",
        "edition": "5e-2014",
        "license": "CC-BY-4.0",
        "source": {"title": "SRD 5.1", "url": None, "publisher": "Wizards of the Coast"},
        "level": 1,
        "school": "Evocation",
        "casting_time": "1 action",
        "range": "120 feet",
        "duration": "Instantaneous",
        "ritual": False,
        "concentration": False,
        "components": {"verbal": True, "somatic": True, "material": False},
        "materials": None,
        "description_md": "Placeholder SRD-safe text."
    }

    errors = sorted(validator.iter_errors(spell), key=lambda e: e.path)
    assert errors == []


def test_spell_schema_requires_materials_when_material_component_true():
    schema = _load_schema()
    validator = Draft7Validator(schema)

    spell = {
        "name": "Identify",
        "srd_id": "spell:identify",
        "edition": "5e-2014",
        "license": "CC-BY-4.0",
        "source": {"title": "SRD 5.1", "url": None, "publisher": "Wizards of the Coast"},
        "level": 1,
        "school": "Divination",
        "casting_time": "1 minute",
        "range": "Touch",
        "duration": "Instantaneous",
        "ritual": True,
        "concentration": False,
        "components": {"verbal": True, "somatic": True, "material": True},
        "materials": "a pearl worth at least 100 gp and an owl feather",
        "description_md": "Placeholder SRD-safe text."
    }

    errors = sorted(validator.iter_errors(spell), key=lambda e: e.path)
    assert errors == []
