"""Generate model predictions before labels, without reading or modifying label fields."""

import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from eval.run_eval import load_cached_predictions, pipeline_prediction
from scripts.run_pipeline import make_pipeline
from src.classifier import LLMClassifier
from src.data import read_jsonl, write_jsonl
from src.draft import LLMDrafter
from src.llm_client import OpenAIClient
from src.pipeline import SupportPipeline
from src.settings import SETTINGS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", choices=["simple", "primary_llm"], default="primary_llm")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.workers <= 12:
        raise SystemExit("--workers must be between 1 and 12")

    rows = read_jsonl("eval/golden_set.jsonl")
    output = Path(f"eval/results/{args.system}_predictions.jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)
    existing = read_jsonl(output) if output.exists() else []
    completed = {row["example_id"]: row for row in existing}
    pending = [row for row in rows if row["example_id"] not in completed]
    if not pending and load_cached_predictions(output, rows):
        print(f"Already complete: {len(rows)} predictions in {output}")
        return

    base = make_pipeline("local")
    local = threading.local()

    def pipeline():
        if args.system == "simple":
            return base
        if not hasattr(local, "pipeline"):
            client = OpenAIClient(
                SETTINGS.llm.agent_model,
                timeout=SETTINGS.llm.timeout_seconds,
                retries=SETTINGS.llm.max_retries,
            )
            local.pipeline = SupportPipeline(
                LLMClassifier(client), base.retriever, LLMDrafter(client), "llm"
            )
        return local.pipeline

    def predict(row):
        prediction = pipeline_prediction(
            pipeline(), row, retrieval_only=args.system == "simple"
        )
        prediction["example_id"] = row["example_id"]
        return prediction

    order = {row["example_id"]: index for index, row in enumerate(rows)}

    def persist() -> None:
        write_jsonl(output, sorted(completed.values(), key=lambda row: order[row["example_id"]]))

    try:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(predict, row): row["example_id"] for row in pending}
            for count, future in enumerate(as_completed(futures), 1):
                prediction = future.result()
                completed[prediction["example_id"]] = prediction
                if count % 10 == 0 or count == len(pending):
                    persist()
                    print(f"Completed {len(completed)}/{len(rows)}")
    finally:
        persist()

    metadata = {
        "system": args.system,
        "model": SETTINGS.llm.agent_model if args.system == "primary_llm" else "local",
        "examples": len(completed),
        "labels_read": False,
        "total_input_tokens": sum(row.get("input_tokens", 0) for row in completed.values()),
        "total_output_tokens": sum(row.get("output_tokens", 0) for row in completed.values()),
        "total_estimated_cost_usd": round(
            sum(row.get("estimated_cost_usd", 0) for row in completed.values()), 6
        ),
    }
    output.with_suffix(".meta.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
