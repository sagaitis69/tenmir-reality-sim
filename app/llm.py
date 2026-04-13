from openai import OpenAI

from .config import env


def client() -> OpenAI:
    key = env("OPENAI_API_KEY")
    base = env("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    base = base.rstrip("/") + "/"
    return OpenAI(api_key=key, base_url=base)


def run_gemma(system: str, user: str, max_tokens: int = 2048) -> str:
    model = env("LLM_MODEL", "gemma-4-31b-it")
    c = client()
    resp = c.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.55,
        max_tokens=max_tokens,
    )
    choice = resp.choices[0].message
    return (choice.content or "").strip()
