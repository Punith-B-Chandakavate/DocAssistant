# llm/client.py — Groq for chat generation
from functools import lru_cache
from groq import Groq
from config import GROQ_API_KEY


@lru_cache(maxsize=1)
def get_groq_client() -> Groq:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in .env")
    return Groq(api_key=GROQ_API_KEY)