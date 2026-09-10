"""Intent-filtered retrieval with stable local embeddings and optional Chroma persistence."""

import hashlib
import math
import re
from collections.abc import Iterable

from src.schemas import Intent, RetrievalHit

DIMENSIONS = 4096

def _index(feature: str, offset: int, dimensions: int) -> int:
    value = int.from_bytes(hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest(), "big")
    return offset + value % dimensions


def _unit(values: dict[int, float]) -> dict[int, float]:
    magnitude = math.sqrt(sum(value * value for value in values.values()))
    return {index: value / magnitude for index, value in values.items()} if magnitude else {}


def _features(text: str) -> dict[int, float]:
    """Stable normalized word/character hashing without scientific runtime dependencies."""

    words = re.findall(r"\w+", text.casefold(), flags=re.UNICODE)
    word_counts: dict[int, float] = {}
    for size in (1, 2):
        for start in range(len(words) - size + 1):
            feature = " ".join(words[start : start + size])
            index = _index(feature, 0, 3072)
            word_counts[index] = word_counts.get(index, 0.0) + 1.0
    char_counts: dict[int, float] = {}
    for word in words:
        padded = f" {word} "
        for size in (3, 4, 5):
            for start in range(len(padded) - size + 1):
                index = _index(padded[start : start + size], 3072, 1024)
                char_counts[index] = char_counts.get(index, 0.0) + 1.0
    scale = 1 / math.sqrt(2)
    return {
        **{index: value * scale for index, value in _unit(word_counts).items()},
        **{index: value * scale for index, value in _unit(char_counts).items()},
    }


def _similarity(left: dict[int, float], right: dict[int, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(index, 0.0) for index, value in left.items())


def _dense(vector: dict[int, float]) -> list[float]:
    result = [0.0] * DIMENSIONS
    for index, value in vector.items():
        result[index] = value
    return result


class MemoryRetriever:
    def __init__(self, rows: Iterable[dict]):
        self.rows = [r for r in rows if r.get("resolved_proxy", False)]
        self.vectors = [_features(row["message"]) for row in self.rows]

    def search(self, message: str, intent: Intent, top_k: int = 3) -> list[RetrievalHit]:
        if not self.rows:
            return []
        eligible = [i for i, row in enumerate(self.rows) if row.get("intent") == intent.value]
        if not eligible:
            eligible = list(range(len(self.rows)))
        query = _features(message)
        scores = [_similarity(self.vectors[index], query) for index in eligible]
        order = sorted(range(len(scores)), key=lambda index: (-scores[index], index))[:top_k]
        return [
            RetrievalHit(
                thread_id=str(self.rows[eligible[i]]["thread_id"]),
                customer_message=self.rows[eligible[i]]["message"],
                brand_reply=self.rows[eligible[i]]["reply"],
                similarity=max(-1.0, min(1.0, scores[i])),
            )
            for i in order
        ]


class ChromaRetriever:
    """Persistent Chroma adapter. Uses the same local hashing vectors for zero-cost reproducibility."""

    def __init__(self, path="data/chroma"):
        import chromadb

        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            "spotify_resolved_hybrid_cosine_v3", configuration={"hnsw": {"space": "cosine"}}
        )

    def index(self, rows: list[dict]) -> int:
        rows = [r for r in rows if r.get("resolved_proxy")]
        if not rows:
            return 0
        embeddings = [_dense(_features(row["message"])) for row in rows]
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
        vector = _dense(_features(message))
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
