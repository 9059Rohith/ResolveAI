"""Intent-filtered retrieval with stable local embeddings and optional Chroma persistence."""

from collections.abc import Iterable

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import normalize

from src.schemas import Intent, RetrievalHit


def _hybrid_vectorizer() -> FeatureUnion:
    return FeatureUnion(
        [
            (
                "word",
                HashingVectorizer(
                    n_features=3072,
                    alternate_sign=False,
                    ngram_range=(1, 2),
                    norm="l2",
                ),
            ),
            (
                "character",
                HashingVectorizer(
                    analyzer="char_wb",
                    n_features=1024,
                    alternate_sign=False,
                    ngram_range=(3, 5),
                    norm="l2",
                ),
            ),
        ]
    )


def _embed(vectorizer: FeatureUnion, texts: list[str]):
    return normalize(vectorizer.transform(texts), norm="l2")


class MemoryRetriever:
    def __init__(self, rows: Iterable[dict]):
        self.rows = [r for r in rows if r.get("resolved_proxy", False)]
        self.vectorizer = _hybrid_vectorizer()
        self.matrix = _embed(self.vectorizer, [r["message"] for r in self.rows]) if self.rows else None

    def search(self, message: str, intent: Intent, top_k: int = 3) -> list[RetrievalHit]:
        if not self.rows:
            return []
        eligible = [i for i, row in enumerate(self.rows) if row.get("intent") == intent.value]
        if not eligible:
            eligible = list(range(len(self.rows)))
        query = _embed(self.vectorizer, [message])
        scores = np.asarray((self.matrix[eligible] @ query.T).toarray()).ravel()
        order = np.argsort(-scores)[:top_k]
        return [
            RetrievalHit(
                thread_id=str(self.rows[eligible[i]]["thread_id"]),
                customer_message=self.rows[eligible[i]]["message"],
                brand_reply=self.rows[eligible[i]]["reply"],
                similarity=max(-1.0, min(1.0, float(scores[i]))),
            )
            for i in order
        ]


class ChromaRetriever:
    """Persistent Chroma adapter. Uses the same local hashing vectors for zero-cost reproducibility."""

    def __init__(self, path="data/chroma"):
        import chromadb

        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            "spotify_resolved_hybrid_cosine_v2", configuration={"hnsw": {"space": "cosine"}}
        )
        self.vectorizer = _hybrid_vectorizer()

    def index(self, rows: list[dict]) -> int:
        rows = [r for r in rows if r.get("resolved_proxy")]
        if not rows:
            return 0
        embeddings = _embed(self.vectorizer, [r["message"] for r in rows]).toarray().tolist()
        for start in range(0, len(rows), 500):
            batch = rows[start : start + 500]
            self.collection.upsert(
                ids=[str(r["thread_id"]) for r in batch],
                embeddings=embeddings[start : start + 500],
                documents=[r["message"] for r in batch],
                metadatas=[{"reply": r["reply"], "intent": r["intent"]} for r in batch],
            )
        return len(rows)

    def search(self, message: str, intent: Intent, top_k: int = 3) -> list[RetrievalHit]:
        if self.collection.count() == 0:
            return []
        vector = _embed(self.vectorizer, [message]).toarray()[0].tolist()
        result = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k,
            where={"intent": intent.value},
            include=["documents", "metadatas", "distances"],
        )
        return [
            RetrievalHit(
                thread_id=id,
                customer_message=doc,
                brand_reply=meta["reply"],
                similarity=max(-1.0, min(1.0, 1 - float(distance))),
            )
            for id, doc, meta, distance in zip(
                result["ids"][0],
                result["documents"][0],
                result["metadatas"][0],
                result["distances"][0],
                strict=False,
            )
        ]
