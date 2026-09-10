"""Run all systems on one frozen human-labelled set; never overwrites labels."""

import argparse
import json
import time
from pathlib import Path

from scripts.run_pipeline import make_pipeline
from src.data import read_jsonl, write_jsonl
from src.evaluation import (
    bootstrap_proportion_interval,
    calibration_metrics,
    classification_metrics,
    latency_metrics,
    require_complete_labels,
    routing_metrics,
    selective_risk_curve,
)


def trivial(row):
    return {
        "intent": "other",
        "should_escalate": True,
        "reply": "Thanks for reaching out. A support specialist will review this.",
    }


def pipeline_prediction(pipeline, row, retrieval_only=False):
    out = pipeline.run(row["message"])
    reply = out.retrieved[0].brand_reply if retrieval_only and out.retrieved else out.draft.text
    return {
        "intent": out.classification.intent.value,
        "intent_confidence": out.classification.confidence,
        "should_escalate": out.routing.action == "escalate",
        "reply": reply,
        "latency_ms": out.latency_ms,
        "exemplar_ids": out.draft.exemplar_ids,
        "retrieved": [hit.model_dump() for hit in out.retrieved],
        "top_similarity": out.retrieved[0].similarity if out.retrieved else 0,
        "input_tokens": out.input_tokens,
        "output_tokens": out.output_tokens,
        "estimated_cost_usd": out.estimated_cost_usd,
    }


def load_cached_predictions(path: str | Path, rows: list[dict]) -> list[dict] | None:
    path = Path(path)
    if not path.exists():
        return None
    predictions = read_jsonl(path)
    by_id = {row.get("example_id"): row for row in predictions}
    expected = [row["example_id"] for row in rows]
    if len(by_id) != len(predictions) or set(by_id) != set(expected):
        return None
    return [by_id[example_id] for example_id in expected]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reuse-predictions",
        action="store_true",
        help="Reuse complete prediction files created by eval.generate_predictions",
    )
    args = parser.parse_args()
    rows = read_jsonl("eval/golden_set.jsonl")
    try:
        require_complete_labels(rows)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    systems = {"trivial": trivial}
    for mode in ("local", "llm"):
        try:
            pipeline = make_pipeline(mode)
            name = "simple" if mode == "local" else "primary_llm"
            systems[name] = lambda row, p=pipeline, simple=mode == "local": pipeline_prediction(
                p, row, simple
            )
        except RuntimeError as exc:
            print(f"Skipping {mode}: {exc}")
    report = {}
    Path("eval/results").mkdir(parents=True, exist_ok=True)
    for name, fn in systems.items():
        path = f"eval/results/{name}_predictions.jsonl"
        predictions = load_cached_predictions(path, rows) if args.reuse_predictions else None
        if predictions is None:
            predictions = []
            for row in rows:
                started = time.perf_counter()
                prediction = fn(row)
                prediction.setdefault("latency_ms", (time.perf_counter() - started) * 1000)
                prediction["example_id"] = row["example_id"]
                predictions.append(prediction)
            write_jsonl(path, predictions)
        else:
            print(f"Reusing {len(predictions)} cached predictions for {name}")
        report[name] = {
            **classification_metrics(
                [r["intent"] for r in rows], [p["intent"] for p in predictions]
            ),
            **routing_metrics(
                [r["should_escalate"] for r in rows], [p["should_escalate"] for p in predictions]
            ),
            **latency_metrics([p["latency_ms"] for p in predictions]),
            "retrieval_coverage_at_threshold": sum(
                p.get("top_similarity", 0) >= 0.24 for p in predictions
            )
            / len(predictions),
            "mean_top_similarity": sum(p.get("top_similarity", 0) for p in predictions)
            / len(predictions),
            "mean_cost_usd": sum(p.get("estimated_cost_usd", 0) for p in predictions)
            / len(predictions),
        }
        intent_correct = [
            row["intent"] == prediction["intent"]
            for row, prediction in zip(rows, predictions, strict=True)
        ]
        escalation_cases = [
            prediction["should_escalate"]
            for row, prediction in zip(rows, predictions, strict=True)
            if row["should_escalate"]
        ]
        report[name]["intent_accuracy_95_ci"] = bootstrap_proportion_interval(intent_correct)
        if escalation_cases:
            report[name]["escalation_recall_95_ci"] = bootstrap_proportion_interval(
                escalation_cases
            )
        if all("intent_confidence" in prediction for prediction in predictions):
            report[name].update(
                calibration_metrics(
                    [row["intent"] for row in rows],
                    [prediction["intent"] for prediction in predictions],
                    [prediction["intent_confidence"] for prediction in predictions],
                )
            )
            report[name]["intent_risk_coverage_curve"] = selective_risk_curve(
                [row["intent"] for row in rows],
                [prediction["intent"] for prediction in predictions],
                [prediction["intent_confidence"] for prediction in predictions],
            )
    Path("eval/results/metrics.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
