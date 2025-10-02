# Contributing Guidelines

Thank you for your interest in the **D&D 5e SRD — MongoDB Prototype**!

This repository demonstrates structured use of **MongoDB** with real data (D&D 5e SRD) and includes ingestion, schema validation, testing, and CI. Contributions are welcome if they align with the project goals and scope.

---

## Development Setup
1. Clone the repo and set up the environment:
   ~~~bash
   conda env create -f environment.yml
   conda activate srd-mongo
   cp .env.example .env   # adjust if needed
   ~~~

2. Start MongoDB locally (MongoDB 5/6.x).

3. Run the ingest + tests to confirm everything works:
   ~~~bash
   python scripts/ingest_srd.py
   pytest -q
   ~~~

---

## Code Style
- Python: follow **PEP8** (format with `black` or `ruff` if available).  
- JavaScript (MongoDB scripts): keep them minimal and idempotent.  
- Tests: add or update tests for any new helpers, schema changes, or ingest logic.  

---

## Pull Requests
- PRs should include:
  - A clear description of the change.  
  - Passing tests (`pytest`).  
  - No linter/formatter errors.  

All changes are checked by CI (GitHub Actions) before merging.

---

## Project Scope
The current focus is:
- ✅ SRD Class ingest & validation (levels 1–5)  
- ✅ Helpers for reading/querying  
- ⏳ Next: class progression demos & expansion to subclasses/spells  

Out of scope: closed-source or homebrew content (this repo sticks strictly to SRD).

---

Thanks for helping improve this project! 🎲
