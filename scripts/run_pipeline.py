import argparse
import json
import os

from src.audit import JsonlAuditLog
from src.classifier import LLMClassifier, LocalClassifier
from src.data import read_jsonl
from src.draft import LLMDrafter
from src.llm_client import OpenAIClient
from src.pipeline import SupportPipeline
from src.retrieval import ChromaRetriever, MemoryRetriever
from src.settings import SETTINGS


def make_pipeline(mode: str, audit: bool = False) -> SupportPipeline:
    try:
        retriever = ChromaRetriever()
        if retriever.collection.count() == 0:
            raise RuntimeError("empty")
    except Exception:
        path = "data/processed/retrieval_corpus.jsonl"
        retriever = MemoryRetriever(read_jsonl(path) if os.path.exists(path) else [])
    if mode == "llm":
        client = OpenAIClient(
            SETTINGS.llm.agent_model,
            timeout=SETTINGS.llm.timeout_seconds,
            retries=SETTINGS.llm.max_retries,
        )
        return SupportPipeline(
            LLMClassifier(client),
            retriever,
            LLMDrafter(client),
            "llm",
            JsonlAuditLog() if audit else None,
        )
    return SupportPipeline(
        LocalClassifier(), retriever, mode="local", audit_log=JsonlAuditLog() if audit else None
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("message")
    parser.add_argument("--mode", choices=["local", "llm"], default="local")
    args = parser.parse_args()
    print(json.dumps(make_pipeline(args.mode, audit=True).run(args.message).model_dump(), indent=2))


if __name__ == "__main__":
    main()
