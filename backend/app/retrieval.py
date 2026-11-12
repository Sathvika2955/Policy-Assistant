"""Embeddings + ChromaDB: store policy chunks and search them by meaning."""
from functools import lru_cache
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL
from app.ingestion import chunk_file


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    # Loaded once, reused everywhere (loading takes a few seconds).
    return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def _collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def _embed(texts: list[str]) -> list[list[float]]:
    return _model().encode(texts, normalize_embeddings=True).tolist()


def ingest_file(path: Path) -> int:
    """Add (or replace) one document. Returns number of chunks stored."""
    delete_document(path.name)  # re-uploading the same file replaces the old version
    chunks = chunk_file(path)
    if not chunks:
        return 0
    _collection().add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=_embed([c["text"] for c in chunks]),
        metadatas=[{"source": c["source"], "page": c["page"]} for c in chunks],
    )
    return len(chunks)


def delete_document(filename: str) -> None:
    _collection().delete(where={"source": filename})


def list_documents() -> list[str]:
    metas = _collection().get(include=["metadatas"])["metadatas"]
    return sorted({m["source"] for m in metas})


def search(query: str, k: int = 3) -> list[dict]:
    """Return the top-k most relevant chunks for a question."""
    res = _collection().query(query_embeddings=_embed([query]), n_results=k)
    hits = []
    for text, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        hits.append(
            {
                "text": text,
                "source": meta["source"],
                "page": meta["page"],
                "score": round(1 - dist, 3),  # cosine similarity: higher = closer
            }
        )
    return hits
