import json
from pathlib import Path

from src.data import read_jsonl
from src.evaluation import judge_human_agreement

DIMENSIONS = [
    "groundedness",
    "tone",
    "safety",
    "actionability",
    "conciseness",
    "evidence_relevance",
]

if __name__ == "__main__":
    human = read_jsonl("eval/human_judge_scores.jsonl")
    judge = read_jsonl("eval/llm_judge_scores.jsonl")
    result = judge_human_agreement(human, judge, DIMENSIONS)
    Path("eval/results/judge_human_agreement.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
