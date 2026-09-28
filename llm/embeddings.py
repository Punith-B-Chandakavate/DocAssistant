# llm/embeddings.py — LOCAL embeddings, no API key needed
from functools import lru_cache
from typing import Iterable
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"  # 80MB, fast, good quality


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    texts = list(texts)
    if not texts:
        return []
    vecs = _model().encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    return vecs.tolist()


def embed_query(text: str) -> list[float]:
    vec = _model().encode([text], normalize_embeddings=True)
    return vec[0].tolist()