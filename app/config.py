import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge" / "books"
DB_PATH = ROOT / "data" / "corpus.sqlite3"


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def ensure_data_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
