"""Score saved replies with a separately prompted judge; outputs are never human labels."""

import argparse
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from src.data import read_jsonl, write_jsonl
from src.llm_client import OpenAIClient
from src.settings import SETTINGS


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", default="primary_llm")
    args = parser.parse_args()
    golden = {r["example_id"]: r for r in read_jsonl("eval/golden_set.jsonl")}
    predictions = read_jsonl(f"eval/results/{args.system}_predictions.jsonl")
    client = OpenAIClient(
        SETTINGS.llm.judge_model,
        timeout=SETTINGS.llm.timeout_seconds,
        retries=SETTINGS.llm.max_retries,
    )
    scores = []
    rubric = Path("eval/judge_rubric.md").read_text(encoding="utf-8")
    for prediction in predictions:
        row = golden[prediction["example_id"]]
        prompt = (
            f"Apply this rubric independently. Return the example_id exactly.\n{rubric}\n"
            f"Example ID: {row['example_id']}\nCustomer: {row['message']}\nReference direction: {row['reference_reply']}\n"
            f"Draft: {prediction['reply']}\nRetrieved evidence: {prediction.get('retrieved', [])}"
        )
        scores.append(client.structured(prompt, JudgeScore).model_dump())
    write_jsonl("eval/llm_judge_scores.jsonl", scores)
    Path("eval/results/judge_usage.json").write_text(
        json.dumps(
            {"input_tokens": client.input_tokens, "output_tokens": client.output_tokens}, indent=2
        )
    )


if __name__ == "__main__":
    main()
