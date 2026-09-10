"""Blind, resume-safe human rating tool for the judge-agreement sample."""

import argparse

from src.data import read_jsonl, write_jsonl

DIMENSIONS = (
    "groundedness",
    "tone",
    "safety",
    "actionability",
    "conciseness",
    "evidence_relevance",
)


def select_pair_ids(rows: list[dict], count_per_intent: int = 4) -> list[str]:
    intents = sorted({row["suggested_intent"] for row in rows})
    selected = []
    for intent in intents:
        candidates = [row for row in rows if row["suggested_intent"] == intent]
        candidates.sort(key=lambda row: ("edge_case" not in row.get("strata", []), row["example_id"]))
        selected.extend(row["example_id"] for row in candidates[:count_per_intent])
    return selected


def ask_score(dimension: str) -> int:
    while True:
        value = input(f"{dimension.replace('_', ' ').title()} (1-5): ").strip()
        if value.isdigit() and 1 <= int(value) <= 5:
            return int(value)
        print("Enter a whole number from 1 to 5.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count-per-intent", type=int, default=4)
    args = parser.parse_args()
    if args.count_per_intent < 4:
        raise SystemExit("Use at least 4 per intent so the paired sample exceeds 30.")

    golden_rows = read_jsonl("eval/golden_set.jsonl")
    golden = {row["example_id"]: row for row in golden_rows}
    predictions = {
        row["example_id"]: row
        for row in read_jsonl("eval/results/primary_llm_predictions.jsonl")
    }
    path = "eval/human_judge_scores.jsonl"
    existing_rows = read_jsonl(path)
    existing = {row["example_id"]: row for row in existing_rows}
    selected = select_pair_ids(golden_rows, args.count_per_intent)
    rater = input("Rater name or initials: ").strip()
    if not rater:
        raise SystemExit("A human rater identifier is required.")

    for index, example_id in enumerate(selected, 1):
        if example_id in existing:
            continue
        row, prediction = golden[example_id], predictions[example_id]
        reference = row.get("reference_reply") or row["historical_reply"]
        print(f"\n{index}/{len(selected)} · {example_id}")
        print(f"CUSTOMER: {row['message']}")
        print(f"REFERENCE: {reference}")
        print(f"DRAFT: {prediction['reply']}")
        print("EVIDENCE:")
        for hit in prediction.get("retrieved", []):
            print(f"- [{hit['thread_id']}] {hit['brand_reply']}")
        rating = {"example_id": example_id}
        for dimension in DIMENSIONS:
            rating[dimension] = ask_score(dimension)
        rating["rationale"] = input("Short rationale: ").strip()
        rating["rater"] = rater
        rating["reference_basis"] = (
            "human_reference" if row.get("reference_reply") else "historical_reply_proxy"
        )
        existing[example_id] = rating
        write_jsonl(path, [existing[key] for key in selected if key in existing])
    print(f"Completed {len(existing)}/{len(selected)} blind human ratings.")
    print("Run: uv run python -m eval.judge_human_agreement")


if __name__ == "__main__":
    main()
