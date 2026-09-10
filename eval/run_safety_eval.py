"""Run the versioned adversarial and safe-automation launch gate."""

import json
from pathlib import Path

from eval.safety_eval import evaluate_safety_cases
from scripts.run_pipeline import make_pipeline
from src.data import read_jsonl


def main() -> None:
    cases = read_jsonl("eval/safety_cases.jsonl")
    report = evaluate_safety_cases(make_pipeline("local"), cases)
    path = Path("eval/results/safety_metrics.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["failed"]:
        raise SystemExit(f"Safety launch gate failed {report['failed']} case(s).")


if __name__ == "__main__":
    main()
