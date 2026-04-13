from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import rag
from .config import KNOWLEDGE_DIR, ROOT, env
from .llm import run_gemma

load_dotenv(ROOT / ".env")

app = FastAPI(title="TENMIR foresight console", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = ROOT / "static"
if static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=static_dir), name="assets")


class QueryBody(BaseModel):
    question: str = Field(..., min_length=4, max_length=8000)


SYSTEM_PROMPT = """You are a foresight and social-dynamics analyst (inspired by multi-agent world models, but you are a single model).
You MUST ground claims in the RETRIEVED_EXCERPTS when they are relevant; label clear speculation as speculation.
Use sections: Summary, Mechanisms (psychology / institutions), Stakeholder dynamics, Risks, What would change the outcome, Limitations.
Keep a serious, precise tone. Do not claim to predict the future with certainty."""


@app.on_event("startup")
def _startup() -> None:
    rag.init_db()
    rag.scan_knowledge_dir()


@app.get("/")
def landing() -> FileResponse:
    return FileResponse(static_dir / "dashboard.html")


@app.get("/console")
def console() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/graph.html")
def graph() -> FileResponse:
    return FileResponse(static_dir / "graph.html")


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "chunks": rag.chunk_count(),
        "model": env("LLM_MODEL", "gemma-4-31b-it"),
        "has_api_key": bool(env("OPENAI_API_KEY")),
    }


@app.post("/api/ingest/scan")
def ingest_scan() -> dict:
    counts = rag.scan_knowledge_dir()
    return {"chunks_total": rag.chunk_count(), "files": counts}


@app.post("/api/ingest/upload")
async def ingest_upload(file: UploadFile = File(...)) -> dict:
    raw = await file.read()
    if len(raw) > 25_000_000:
        raise HTTPException(413, "File too large (max ~25 MB)")
    name = Path(file.filename or "upload.txt").name
    safe = "".join(c for c in name if c.isalnum() or c in "._- ")[:120]
    dest = KNOWLEDGE_DIR / safe
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    suf = dest.suffix.lower()
    try:
        if suf == ".pdf":
            n = rag.ingest_pdf_file(dest)
        else:
            text = raw.decode("utf-8", errors="replace")
            n = rag.ingest_text(str(dest), text)
    except Exception as exc:
        raise HTTPException(400, f"Ingest failed: {exc}") from exc
    return {"path": str(dest), "chunks": n, "chunks_total": rag.chunk_count()}


@app.post("/api/query")
def query(body: QueryBody) -> dict:
    excerpts = rag.retrieve(body.question, limit=16)
    if not excerpts:
        ctx = "(No retrieved passages — corpus empty or not indexed. Add .txt / .md / .pdf under knowledge/books and call POST /api/ingest/scan .)"
    else:
        ctx = "\n\n---\n\n".join(excerpts)
    user = f"""RETRIEVED_EXCERPTS (from your psychology / books corpus):\n{ctx}\n\n---\n\nSCENARIO / QUESTION:\n{body.question}\n"""
    try:
        answer = run_gemma(SYSTEM_PROMPT, user)
    except Exception as exc:
        raise HTTPException(502, f"LLM error: {exc}") from exc
    return {"answer": answer, "chunks_used": len(excerpts)}
