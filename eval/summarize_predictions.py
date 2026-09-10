"""Report label-free operational diagnostics; these are not quality metrics."""

import json
from collections import Counter
from pathlib import Path

from src.data import read_jsonl
from src.evaluation import latency_metrics


def summarize(rows: list[dict]) -> dict:
    count = len(rows)
    if not count:
        raise ValueError("Prediction file is empty")
    confidences = [row["intent_confidence"] for row in rows if "intent_confidence" in row]
    return {
        "examples": count,
        "intent_distribution": dict(sorted(Counter(row["intent"] for row in rows).items())),
        "auto_handle_rate": sum(not row["should_escalate"] for row in rows) / count,
        "grounded_rate": sum(bool(row.get("exemplar_ids")) for row in rows) / count,
        "retrieval_coverage_at_0_24": sum(row.get("top_similarity", 0) >= 0.24 for row in rows)
        / count,
        "mean_top_similarity": sum(row.get("top_similarity", 0) for row in rows) / count,
        "mean_intent_confidence": sum(confidences) / len(confidences) if confidences else None,
        **latency_metrics([row.get("latency_ms", 0) for row in rows]),
        "total_estimated_cost_usd": round(
            sum(row.get("estimated_cost_usd", 0) for row in rows), 6
        ),
    }


def main() -> None:
    systems = ("simple", "primary_llm")
    predictions = {
        system: read_jsonl(f"eval/results/{system}_predictions.jsonl") for system in systems
    }
    by_system = {system: summarize(rows) for system, rows in predictions.items()}
    simple = {row["example_id"]: row for row in predictions["simple"]}
    primary = {row["example_id"]: row for row in predictions["primary_llm"]}
    shared = sorted(set(simple) & set(primary))
    report = {
        "status": "label_free_diagnostics_not_quality_evaluation",
        "systems": by_system,
        "cross_system": {
            "shared_examples": len(shared),
            "intent_agreement": sum(simple[key]["intent"] == primary[key]["intent"] for key in shared)
            / len(shared),
            "route_agreement": sum(
                simple[key]["should_escalate"] == primary[key]["should_escalate"] for key in shared
            )
            / len(shared),
        },
    }
    path = Path("eval/results/prediction_diagnostics.json")
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
