**Knowledge Graph Builder**
- Build domain knowledge graphs from Vietnamese academic documents using LLM-assisted extraction, schema normalization, and embeddings-based type standardization.
- Current stack combines Google Gemini models (text + embedding) and OpenAI-compatible APIs for entity and triple extraction.

---

**Overview**
- `KG_builder` ingests cleaned corpora, splits text into overlapping chunks, and calls `extract_triples` to retrieve `(subject, predicate, object)` relationships.
- Extracted predicates are cross-checked against your relation schema; unseen predicates trigger an on-the-fly definition request and embedding similarity matching to map them to canonical types.
- Utility scripts help expand entity schemas, define predicates, and convert PDF profiles into text with page-level provenance.

**Repository Layout**
- `src/KG_builder/builder.py` — orchestrates chunking, triple extraction, and schema alignment.
- `src/KG_builder/utils/clean_data.py` — text cleaning, sentence-aware chunking, CSV helpers.
- `src/KG_builder/utils/embedding_utils.py` — Gemini embedding wrapper and cosine similarity utilities.
- `src/KG_builder/extract/` — LLM prompts for triples, entities, and ontology definitions.
- `src/run.py` — minimal example showing how to instantiate `KG_builder` and run it on a corpus.
- `entities.csv` / `relationships.csv` — seed schemas (Type → Definition pairs).
- `data/` — sample raw documents; keep large inputs here.

**Prerequisites**
- Python ≥ 3.9 (project targets 3.9+).
- Access to Google Gemini (text + embedding) and an OpenAI-compatible endpoint.
- Environment variables (store them in `.env`):
  - `OPENAI` — API key used by `CostModel` when calling LLM endpoints.
  - `GOOGLE_API_KEY` — required by `google.genai.Client` for embeddings (configured by the Google SDK).
- Install dependencies:
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  pip install -e .
  ```
  For development extras (`pytest`, `ruff`, `mypy`):
  ```bash
  pip install -e ".[dev]"
  ```

**Using the Builder**
- Prepare your corpus:
  1. Place the raw document in `data/`.
  2. Clean it with `clean_vn_text` if you are skipping `run.py`.
- Run the sample script:
  ```bash
  python -m src.run
  ```
- Programmatic usage:
  ```python
  from KG_builder.builder import KG_builder

  args = {
      "enities_schema": "entities.csv",
      "relation_schema": "relationships.csv",
      "threshold": 0.6,
  }
  builder = KG_builder(**args)
  triples = builder.run(
      context=my_corpus,
      chunk_config={"max_chunk_chars": 1200, "min_chunk_chars": 400, "sentence_overlap": 1},
  )
  ```
- Each chunk is processed separately; duplicate triples are removed before the schema alignment step.
- Updated relations are written with `builder.write_schema("new_relationships.csv")` if you want to persist newly standardized predicates.

**LLM Prompts & Schema Expansion**
- `extract/extract_entities.py` — prompts a model to label entities, optionally creating new types.
- `extract/definition.py` — asks Gemini for concise ontology-style definitions for unseen entities and predicates.
- Generated schema expansions land in `new_entities.csv`, `new_relationship.csv`, and their JSON counterparts under project root.

**Converting PDFs**
- `convert_pdf_to_text/core.py` uses PyMuPDF to read PDFs, strip headers, and produce `[PAGE x]` tagged context blocks ready for chunking/extraction.
- Call `build_context_with_provenance` to obtain both the concatenated context string and per-page metadata.

**Testing & Tooling**
- Run unit tests (when available): `pytest`.
- Static checks: `ruff check .` and `mypy src`.
- When experimenting with chunk sizes or schemas, favor small trial documents to manage LLM cost.

**Notes & Limitations**
- Rate limits and cost depend on your LLM provider configuration; monitor usage when processing large corpora.
- Ensure your `.env` keys are set before running scripts to avoid authentication errors.
- Cleaning heuristics are tailored for Vietnamese academic/administrative documents; adjust `clean_vn_text` for other domains.
