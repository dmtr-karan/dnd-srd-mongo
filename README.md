<p align="center">
  <img src="assets/crest.png" alt="Epic Crest Logo" width="360"/>
</p>

<h1 align="center">D&D 5e SRD — MongoDB</h1>

<p align="center">
  <em>Production-style MongoDB project modeling D&D 5e SRD class data (levels 1–5) — schema design, ETL ingestion, and JSON validation</em>
</p>

[![CI](https://github.com/dmtr-karan/dnd-srd-mongo/actions/workflows/ci.yml/badge.svg?branch=main&event=push&ts=20251002)](https://github.com/dmtr-karan/dnd-srd-mongo/actions/workflows/ci.yml)  
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)  
[![SRD: CC-BY-4.0](https://img.shields.io/badge/SRD-CC--BY--4.0-lightgrey.svg)](https://dnd.wizards.com/resources/systems-reference-document)  
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)  
[![MongoDB 5+](https://img.shields.io/badge/MongoDB-5%2B-brightgreen.svg)](https://www.mongodb.com/)

<sub>Keywords: D&D, 5e, SRD, MongoDB, TTRPG</sub>


## ✨ What this is
A **production-style project** that ingests **D&D 5e SRD class data (levels 1–5)**, validates it with **JSON Schema**, and stores it in **MongoDB** in two forms:
- **Embedded `classes`** collection with full `features_by_level`
- **Normalized `features`** collection with stable slugs + indexes

It also emits **deterministic cache JSONs** for fast demos and ships a tiny **read helper layer** + tests.

This repository is part of a larger learning/demo project exploring how to build a **character progression engine** and other D&D tools on top of MongoDB.

---

## 📦 Features
- Canonical SRD class JSONs (`data/srd/classes/`)
- JSON Schema validation (`schemas/srd-class-5e-2014.json`)
- Ingest script (`scripts/ingest_srd.py`) with idempotent upserts
- Canonical indexes (`scripts/indexes.mongo.js`)
- Strict validator (`scripts/feature_validator.mongo.js`)
- Cache emitter (`cache/classes.min.json`, `cache/meta.json`)
- Smoke + helper tests (`tests/`)

---

---

## 🗂️ Schema Design — Embedded vs Normalized

This project demonstrates two complementary MongoDB schema approaches for the same SRD class data:

- **Embedded** → all class features by level are stored inside each class document.  
- **Normalized** → features are stored in a separate collection with slugs and indexes, deduplicating shared rules.  

<p align="center">
  <img src="assets/schema.png" alt="Epic Schema Diagram" width="720"/>
</p>

> **Why both?**  
> Embedded schemas make common reads self-contained; normalized avoids duplication and enables cross-class analytics.

---

## 🚀 Quickstart

### 1. Environment (Conda recommended)
~~~bash
conda env create -f environment.yml
conda activate srd-mongo
~~~

### 1b. Environment variables
Copy the template to set your MongoDB URI locally:

**Linux/macOS/Git Bash**
~~~bash
cp .env.example .env
~~~

**Windows PowerShell**
~~~powershell
copy .env.example .env
~~~

### 2. Start MongoDB (Windows examples)
Service install:
~~~powershell
net start MongoDB
~~~

Portable run:
~~~powershell
mongod --dbpath "C:\path\to\your\data"
~~~

### 3. Apply indexes + validator
~~~powershell
mongosh "mongodb://localhost:27017/dnd_srd" scripts/indexes.mongo.js
mongosh "mongodb://localhost:27017/dnd_srd" scripts/feature_validator.mongo.js
~~~

### 4. Ingest SRD data
~~~powershell
python scripts/ingest_srd.py
~~~

### 5. Run tests
~~~powershell
pytest -q
~~~

---

### 🔎 Example Queries

Using the helper layer in Python:

~~~python
from scripts.read_helpers import list_classes, features_by_class_level, feature_by_slug

print(list_classes())                               # SRD classes
print(features_by_class_level("Fighter", 1))        # Fighter level-1 features
print(feature_by_slug("fighter-second-wind-l1"))    # Lookup by slug
~~~

Outputs (click to expand):

<details><summary>A) <code>list_classes()</code></summary>

~~~text
[{'srd_id': 'class:barbarian:srd-5-1', 'hit_die': 12, 'name': 'Barbarian'}, {'srd_id': 'class:bard:srd-5-1', 'hit_die': 8, 'name': 'Bard'}, {'srd_id': 'class:fighter:srd-5-1', 'hit_die': 10, 'name': 'Fighter'}, {'srd_id': 'class:wizard:srd-5-1', 'hit_die': 6, 'name': 'Wizard'}]
~~~

</details>

<details><summary>B) <code>features_by_class_level("Fighter", 1)</code></summary>

~~~text
[{'slug': 'fighter-fighting-style-l1', 'name': 'Fighting Style'}, {'slug': 'fighter-second-wind-l1', 'name': 'Second Wind'}]
~~~

</details>

<details><summary>C) <code>feature_by_slug("fighter-second-wind-l1")</code></summary>

~~~text
{'level': 1, 'class_srd_id': 'class:fighter:srd-5-1', 'slug': 'fighter-second-wind-l1', 'class_name': 'Fighter', 'description_md': 'You have a limited well of stamina that you can draw on to protect yourself.', 'edition': '5e-2014', 'license': 'CC-BY-4.0', 'meta': {'imported_at': '2025-10-02T09:51:08Z', 'import_version': 1}, 'name': 'Second Wind', 'source': 'SRD 5.1', 'srd_feature_id': 'fighter:second-wind'}
~~~

</details>


## 🧭 Status & Roadmap

**Current status (`v0.3.0`):**
- Local SRD sample data (classes + features) included.
- Example read queries in README; CI is green on `main`.

**Near-term (`0.3.x` by 2025-10-20):**
- **Ingest CLI** (`scripts/ingest_srd.py`): read local SRD JSON, validate with JSON Schema, write both:
  - **Embedded** (`classes_embedded`) for simple reads.
  - **Normalized** (`features`, `classes_refs`) for dedup & analytics.
- **DX:** `.env.example`, `Makefile` targets (`make ingest`, `make drop:test`, `make validate`).
- **CI:** schema validation job to fail on invalid data.
- **Licensing:** keep SRD content under CC-BY-4.0 with explicit attribution.

**Optional extensions (showcase later):**
- Read-only API (FastAPI) and/or small Streamlit viewer.
- Atlas how-to with secure connection notes.

---

## 📜 License
- MIT (code)
- SRD 5.1 content under Creative Commons **CC-BY-4.0**

## SRD Data & Attribution
Portions of this repository (`data/srd/classes/`) are based on the *Dungeons & Dragons® 5.1 System Reference Document (SRD)* by Wizards of the Coast, used under Creative Commons Attribution 4.0 International (CC-BY-4.0).

Source: [https://dnd.wizards.com/resources/systems-reference-document](https://dnd.wizards.com/resources/systems-reference-document)  
Attribution: *“Dungeons & Dragons® 5.1 System Reference Document (SRD) — Wizards of the Coast. Used under CC-BY-4.0.”*

All SRD content remains © Wizards of the Coast.
