"""Audit repository evidence without turning machine suggestions into human labels."""

import argparse
import json
from pathlib import Path

from src.data import read_jsonl

ROOT = Path(__file__).parents[1]


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def audit_repository() -> dict:
    required_files = [
        "README.md",
        "REPORT.md",
        "DECISIONS.md",
        "CITATIONS.md",
        "ASSIGNMENT_CHECKLIST.md",
        "eval/golden_set.jsonl",
        "eval/judge_rubric.md",
        "eval/labeling_notes.md",
        "eval/safety_cases.jsonl",
        "eval/results/safety_metrics.json",
        "Dockerfile",
        "vercel.json",
        ".github/workflows/ci.yml",
    ]
    golden = read_jsonl(ROOT / "eval/golden_set.jsonl")
    corpus = read_jsonl(ROOT / "data/processed/retrieval_corpus.jsonl")
    sampling = _json("data/processed/sampling_stats.json")
    threads = _json("data/processed/thread_stats.json")
    safety = _json("eval/results/safety_metrics.json")
    evidence = _json("data/processed/evidence_summary.json")
    report = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    decisions = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    env_template = (ROOT / ".env.example").read_text(encoding="utf-8")

    human_verified = sum(row.get("label_status") == "human_verified" for row in golden)
    scores_path = ROOT / "eval/human_judge_scores.jsonl"
    paired_ratings = len(read_jsonl(scores_path)) if scores_path.exists() else 0
    checks = {
        "required_files_present": all((ROOT / path).exists() for path in required_files),
        "candidate_count_matches": len(golden) == sampling["candidate_threads"] == 200,
        "retrieval_count_matches": len(corpus) == sampling["retrieval_threads"] == 5000,
        "component_disjoint": sampling["component_disjoint"] is True,
        "balanced_intent_suggestions": set(sampling["intent_suggestions"].values()) == {25},
        "safety_gate_passes": safety["passed"] == safety["total"] == 16,
        "public_evidence_matches_artifacts": evidence["dataset"]["raw_tweets"]
        == threads["raw_tweets"]
        and evidence["dataset"]["spotify_threads"] == threads["threads"]
        and evidence["dataset"]["retrieval_threads"] == sampling["retrieval_threads"]
        and evidence["evaluation"]["candidate_examples"] == len(golden)
        and evidence["evaluation"]["human_verified_examples"] == human_verified
        and evidence["evaluation"]["safety_gate"]
        == {"passed": safety["passed"], "total": safety["total"]},
        "decision_log_has_15_items": decisions.count("- **") == 15,
        "report_has_problem_framing": "## 1. Problem framing" in report,
        "report_has_baselines": "## 3. Results versus baselines" in report
        and "trivial" in report.lower(),
        "report_has_five_failure_modes": all(f"\n{index}. **" in report for index in range(1, 6)),
        "report_has_misleading_number_section": "misleading about my headline number" in report.lower(),
        "report_has_one_week_plan": "one more week" in report.lower(),
        "readme_has_fast_path": "## Fifteen-minute reproduction" in readme,
        "readme_has_live_deployment": "https://resolve-ai-wheat.vercel.app" in readme,
        "readme_has_poster": "docs/assets/resolve-poster.png" in readme
        and (ROOT / "docs/assets/resolve-poster.png").exists(),
        "environment_template_is_sanitized": "OPENAI_API_KEY=your_openai_api_key_here"
        in env_template,
    }
    pending = []
    if human_verified < 200:
        pending.append("200 hand-labelled examples")
    if paired_ratings < 30:
        pending.append("at least 30 paired human/judge ratings")
    if not (ROOT / "eval/results/metrics.json").exists():
        pending.append("live primary-system evaluation")
    return {
        "software_ready": all(checks.values()),
        "verified_checks": sum(checks.values()),
        "total_checks": len(checks),
        "checks": checks,
        "candidate_examples": len(golden),
        "human_verified_examples": human_verified,
        "paired_human_ratings": paired_ratings,
        "safety_gate": f"{safety['passed']}/{safety['total']}",
        "component_disjoint": sampling["component_disjoint"],
        "human_evidence_ready": not pending,
        "pending_human_evidence": pending,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    result = audit_repository()
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"Software checks: {result['verified_checks']}/{result['total_checks']}")
    print(f"Safety gate: {result['safety_gate']}")
    print(f"Human labels: {result['human_verified_examples']}/{result['candidate_examples']}")
    print("Software ready: yes" if result["software_ready"] else "Software ready: no")
    if result["pending_human_evidence"]:
        print("Pending human evidence:")
        for item in result["pending_human_evidence"]:
            print(f"- {item}")


if __name__ == "__main__":
    main()
