import pytest

pytest.importorskip("chromadb")

from src.retrieval import ChromaRetriever
from src.schemas import Intent


def test_chroma_uses_cosine_distance_for_similarity(tmp_path):
    retriever = ChromaRetriever(str(tmp_path))
    retriever.index(
        [
            {
                "thread_id": "exact",
                "message": "music pauses every second",
                "reply": "check device details",
                "intent": Intent.PLAYBACK.value,
                "resolved_proxy": True,
            },
            {
                "thread_id": "other",
                "message": "playlist album missing",
                "reply": "share the link",
                "intent": Intent.PLAYBACK.value,
                "resolved_proxy": True,
            },
        ]
    )
    hits = retriever.search("music pauses every second", Intent.PLAYBACK, 1)
    assert hits[0].thread_id == "exact"
    assert hits[0].similarity > 0.99
