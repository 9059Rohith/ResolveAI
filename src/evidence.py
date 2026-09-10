"""Versioned, public evidence summary for reviewers and release checks."""

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def load_evidence() -> dict:
    path = Path(__file__).parents[1] / "data" / "processed" / "evidence_summary.json"
    return json.loads(path.read_text(encoding="utf-8"))
