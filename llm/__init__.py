# llm/__init__.py
from .client import get_groq_client
from .embeddings import embed_texts, embed_query

__all__ = ["get_groq_client", "embed_texts", "embed_query"]