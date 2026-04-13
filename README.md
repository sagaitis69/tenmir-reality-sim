# TENMIR foresight console (Gemma 4 + book RAG)

**Repository:** [github.com/sagaitis69/tenmir-reality-sim](https://github.com/sagaitis69/tenmir-reality-sim)

**Product shape:** web only (browser UI + FastAPI backend). There is no native mobile app in this repo—use a responsive browser on phones if you want small screens.

A **small, self-contained** slice of the [MiroFish](https://dev.to/arshtechpro/mirofish-the-open-source-ai-engine-that-builds-digital-worlds-to-predict-the-future-ki8) idea: ingest long-form texts (psychology and other books), retrieve relevant passages for a scenario, and call **Gemma 4** on **Google’s developer API** to produce a structured brief.

### Which API is this?

- **Provider:** [Google AI Studio / Gemini API](https://ai.google.dev/) — you create a key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). That is **not** an OpenAI company account.
- **Model:** Gemma 4 (set `LLM_MODEL` to the id Google lists for your project, e.g. `gemma-4-31b-it`).
- **Wire format:** Google exposes a **`/v1beta/openai/...`** base URL that speaks the same **HTTP + JSON** shape many tools call “OpenAI-compatible.” The Python package `openai` in `requirements.txt` is only an **HTTP client** for that shape; inference is still **Gemma on Google** (or your own vLLM/Ollama if you point `LLM_BASE_URL` there).

This is **not** a full clone of MiroFish (no OASIS swarm, no Zep, no GraphRAG). It is a practical starting point you can extend.

## What you get

- **UI**: Your existing network header (`static/graph.html`) plus a console (`static/index.html`).
- **Backend**: FastAPI + SQLite **FTS5** full-text index over `knowledge/books/*.txt|*.md|*.pdf`.
- **LLM**: Defaults to **Gemma 4** on Google’s API (`LLM_BASE_URL` + `LLM_API_KEY`); optional self-hosted Gemma with the same request JSON shape.

## Setup (Windows / macOS / Linux)

```bash
cd reality-sim
py -3 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

On some Windows setups use `py -3` instead of `python` if `python` is not on your PATH.

Edit `.env`: set **`LLM_API_KEY`** from [Google AI Studio](https://aistudio.google.com/apikey) and confirm **`LLM_MODEL`** matches a Gemma 4 id your key can call (see Google’s docs; example `gemma-4-31b-it`).

Drop books into `knowledge/books/` (UTF-8 `.txt` / `.md` or `.pdf`), then:

```bash
uvicorn app.main:app --reload --port 8787
```

Open **http://127.0.0.1:8787/** for the **working console** (ingest + query). Optional marketing shell: **http://127.0.0.1:8787/dashboard** — use **Re-index books folder** on the console after adding files.

### Local Gemma 4 (optional)

Point **`LLM_BASE_URL`** at **vLLM** or **Ollama** if you serve Gemma 4 locally, and set **`LLM_MODEL`** to the served model name.

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Corpus chunk count; `has_llm_key` if `LLM_API_KEY` is set |
| POST | `/api/ingest/scan` | Re-read everything under `knowledge/books/` |
| POST | `/api/ingest/upload` | multipart upload into that folder + index |
| POST | `/api/query` | JSON `{ "question": "..." }` → Gemma 4 answer |

## Honest limits

Simulations are **not** forecasts of real outcomes. Respect copyrights for books you ingest; use licensed copies or public-domain sources where applicable.
