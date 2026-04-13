from openai import OpenAI

from .config import env, llm_api_key, llm_base_url


def client() -> OpenAI:
    key = llm_api_key()
    if not key:
        raise RuntimeError(
            "LLM_API_KEY is not set. Use a Google AI Studio key (https://aistudio.google.com/apikey) "
            "for hosted Gemma 4 — this is not an OpenAI company key."
        )
    return OpenAI(api_key=key, base_url=llm_base_url())


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
