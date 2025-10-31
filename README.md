**Knowledge Graph Builder**
- Build domain knowledge graphs from Vietnamese academic documents using LLM-assisted extraction, schema normalization, and embeddings-based type standardization.
- Current stack combines Google Gemini models (text + embedding) and OpenAI-compatible APIs for entity and triple extraction.

---

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

**Using the Builder**
- Prepare your corpus:
  1. Place the raw document in `data/`.
  2. Clean it with `clean_vn_text` if you are skipping `run.py`.
- Run the sample script:
  ```bash
  python -m src.run
  ```
**Notes & Limitations**
- Rate limits and cost depend on your LLM provider configuration; monitor usage when processing large corpora.
- Ensure your `.env` keys are set before running scripts to avoid authentication errors.
- Cleaning heuristics are tailored for Vietnamese academic/administrative documents; adjust `clean_vn_text` for other domains.
