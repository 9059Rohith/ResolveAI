"""Score saved replies with a separately prompted judge; outputs are never human labels."""

import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from src.data import read_jsonl, write_jsonl
from src.llm_client import OpenAIClient
from src.settings import SETTINGS

DIMENSIONS = (
    "groundedness",
    "tone",
    "safety",
    "actionability",
    "conciseness",
    "evidence_relevance",
)


class JudgeScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    example_id: str
    groundedness: int = Field(ge=1, le=5)
    tone: int = Field(ge=1, le=5)
    safety: int = Field(ge=1, le=5)
    actionability: int = Field(ge=1, le=5)
    conciseness: int = Field(ge=1, le=5)
    evidence_relevance: int = Field(ge=1, le=5)
    rationale: str = Field(max_length=600)


def select_reference(row: dict) -> tuple[str, str]:
    if row.get("reference_reply"):
        return row["reference_reply"], "human_reference"
    return row["historical_reply"], "historical_reply_proxy"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", default="primary_llm")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.workers <= 12:
        raise SystemExit("--workers must be between 1 and 12")
    golden = {r["example_id"]: r for r in read_jsonl("eval/golden_set.jsonl")}
    predictions = read_jsonl(f"eval/results/{args.system}_predictions.jsonl")
    rubric = Path("eval/judge_rubric.md").read_text(encoding="utf-8")
    output = Path("eval/llm_judge_scores.jsonl")
    existing = read_jsonl(output) if output.exists() else []
    desired_basis = {
        example_id: select_reference(row)[1] for example_id, row in golden.items()
    }
    completed = {
        row["example_id"]: row
        for row in existing
        if row.get("reference_basis") == desired_basis.get(row["example_id"])
    }
    pending = [row for row in predictions if row["example_id"] not in completed]
    local = threading.local()

    def client():
        if not hasattr(local, "client"):
            local.client = OpenAIClient(
                SETTINGS.llm.judge_model,
                timeout=SETTINGS.llm.timeout_seconds,
                retries=SETTINGS.llm.max_retries,
            )
        return local.client

    def score(prediction):
        row = golden[prediction["example_id"]]
        reference, basis = select_reference(row)
        prompt = (
            f"Apply this rubric independently. Return the example_id exactly.\n{rubric}\n"
            f"Example ID: {row['example_id']}\nCustomer: {row['message']}\nReference direction: {reference}\n"
            f"Draft: {prediction['reply']}\nRetrieved evidence: {prediction.get('retrieved', [])}"
        )
        judge = client()
        before_in, before_out = judge.input_tokens, judge.output_tokens
        result = judge.structured(prompt, JudgeScore)
        if result.example_id != row["example_id"]:
            raise ValueError("Judge returned the wrong example_id")
        return {
            **result.model_dump(),
            "reference_basis": basis,
            "input_tokens": judge.input_tokens - before_in,
            "output_tokens": judge.output_tokens - before_out,
        }

    order = {row["example_id"]: index for index, row in enumerate(predictions)}

    def persist() -> None:
        write_jsonl(output, sorted(completed.values(), key=lambda row: order[row["example_id"]]))

    try:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(score, row): row["example_id"] for row in pending}
            for count, future in enumerate(as_completed(futures), 1):
                result = future.result()
                completed[result["example_id"]] = result
                if count % 10 == 0 or count == len(pending):
                    persist()
                    print(f"Completed {len(completed)}/{len(predictions)}")
    finally:
        persist()

    scores = list(completed.values())
    Path("eval/results/judge_usage.json").write_text(
        json.dumps(
            {
                "model": SETTINGS.llm.judge_model,
                "examples": len(scores),
                "reference_basis": dict(
                    sorted(
                        {
                            basis: sum(row["reference_basis"] == basis for row in scores)
                            for basis in {row["reference_basis"] for row in scores}
                        }.items()
                    )
                ),
                "input_tokens": sum(row.get("input_tokens", 0) for row in scores),
                "output_tokens": sum(row.get("output_tokens", 0) for row in scores),
                "mean_scores": {
                    dimension: round(
                        sum(row[dimension] for row in scores) / len(scores), 3
                    )
                    for dimension in DIMENSIONS
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
