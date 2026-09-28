import hashlib
from pathlib import Path
from typing import Any
import chromadb
from chromadb.config import Settings

from config import CHROMA_PATH
from llm.embeddings import embed_texts, embed_query


class VectorStore:
    def __init__(self, collection_name: str = "documents"):
        self.client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ---------- INGEST ----------
    def add_chunks(
        self,
        source: str,
        chunks: list[dict],
        file_hash: str,
    ) -> int:
        """
        chunks: [{"text": ..., "page": int, "chunk_index": int}, ...]
        Adds them with embeddings and metadata. Skips if source+hash already present.
        """
        if not chunks:
            return 0

        # Skip re-ingest if identical file already ingested
        existing = self.collection.get(
            where={"file_hash": file_hash}, limit=1
        )
        if existing["ids"]:
            return 0

        # Remove any prior version of this source (different hash)
        try:
            self.collection.delete(where={"source": source})
        except Exception:
            pass

        ids, documents, metadatas = [], [], []
        for c in chunks:
            uid = hashlib.sha1(
                f"{source}::{file_hash}::p{c['page']}::c{c['chunk_index']}".encode()
            ).hexdigest()
            ids.append(uid)
            documents.append(c["text"])
            metadatas.append(
                {
                    "source": source,
                    "page": c["page"],
                    "chunk_index": c["chunk_index"],
                    "file_hash": file_hash,
                }
            )

        embeddings = embed_texts(documents)
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return len(ids)

    # ---------- QUERY ----------
    def search(self, query: str, k: int = 5) -> dict[str, Any]:
        q_emb = embed_query(query)
        results = self.collection.query(
            query_embeddings=[q_emb],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
        }

    def count(self) -> int:
        return self.collection.count()

    def list_sources(self) -> list[str]:
        try:
            got = self.collection.get(include=["metadatas"])
            sources = {m["source"] for m in got["metadatas"] if m}
            return sorted(sources)
        except Exception:
            return []

    def reset(self):
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"},
        )