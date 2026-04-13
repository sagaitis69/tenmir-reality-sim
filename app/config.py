import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge" / "books"
DB_PATH = ROOT / "data" / "corpus.sqlite3"


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def ensure_data_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def llm_api_key() -> str:
    """Google AI Studio / Gemini API key for Gemma (not OpenAI the company)."""
    return env("LLM_API_KEY") or env("OPENAI_API_KEY")


def llm_base_url() -> str:
    """Google serves Gemma 4 behind an OpenAI-*compatible* HTTP path (`/v1/...`)."""
    u = env("LLM_BASE_URL") or env("OPENAI_BASE_URL")
    if u:
        return u.rstrip("/") + "/"
    return "https://generativelanguage.googleapis.com/v1beta/openai/"
