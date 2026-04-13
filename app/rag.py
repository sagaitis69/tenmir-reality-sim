import re
import sqlite3
from pathlib import Path

from .config import DB_PATH, KNOWLEDGE_DIR, ensure_data_dir


def _connect() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
            path,
            body,
            tokenize = 'porter unicode61'
        );
        """
    )
    conn.commit()
    conn.close()


def clear_path(path: str) -> None:
    conn = _connect()
    conn.execute("DELETE FROM chunks WHERE path = ?", (path,))
    conn.commit()
    conn.close()


def ingest_text_file(file_path: Path) -> int:
    """Chunk plain text / markdown into FTS. Returns number of chunks."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    return ingest_text(str(file_path), text)


def ingest_text(path_label: str, text: str) -> int:
    if not text.strip():
        return 0
    clear_path(path_label)
    chunk_size = 1600
    step = 1300
    chunks: list[tuple[str, str]] = []
    for i in range(0, len(text), step):
        piece = text[i : i + chunk_size].strip()
        if len(piece) < 80:
            continue
        chunks.append((path_label, piece))
    conn = _connect()
    conn.executemany("INSERT INTO chunks (path, body) VALUES (?, ?)", chunks)
    conn.commit()
    conn.close()
    return len(chunks)


def ingest_pdf_file(file_path: Path) -> int:
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    parts: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t.strip():
            parts.append(t)
    full = "\n\n".join(parts)
    return ingest_text(str(file_path), full)


def scan_knowledge_dir() -> dict[str, int]:
    """Load all .txt / .md / .pdf under knowledge/books."""
    counts: dict[str, int] = {}
    if not KNOWLEDGE_DIR.is_dir():
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        return counts
    for p in sorted(KNOWLEDGE_DIR.iterdir()):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        key = p.name
        try:
            if suf in (".txt", ".md"):
                counts[key] = ingest_text_file(p)
            elif suf == ".pdf":
                counts[key] = ingest_pdf_file(p)
        except Exception:
            counts[key] = -1
    return counts


def fts_query_from_question(question: str) -> str:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", question.lower())
    words = list(dict.fromkeys(words))[:14]
    if not words:
        return "the"
    return " OR ".join(words)


def retrieve(question: str, limit: int = 14) -> list[str]:
    conn = _connect()
    q = fts_query_from_question(question)
    try:
        rows = conn.execute(
            """
            SELECT path, body
            FROM chunks
            WHERE chunks MATCH ?
            ORDER BY bm25(chunks)
            LIMIT ?
            """,
            (q, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = conn.execute(
            "SELECT path, body FROM chunks LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    out: list[str] = []
    for r in rows:
        body = r["body"] if isinstance(r, sqlite3.Row) else r[1]
        path = r["path"] if isinstance(r, sqlite3.Row) else r[0]
        out.append(f"[{path}]\n{body}")
    return out


def chunk_count() -> int:
    conn = _connect()
    try:
        n = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
    except sqlite3.OperationalError:
        n = 0
    conn.close()
    return int(n)
