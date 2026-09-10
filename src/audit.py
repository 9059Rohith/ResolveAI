"""Privacy-minimizing append-only decision audit log."""

import hashlib
import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path

from src.schemas import PipelineResult


class JsonlAuditLog:
    """Record decision metadata without persisting customer or reply text."""

    def __init__(self, path: str | Path | None = None):
        default = "/tmp/resolve-audit.jsonl" if os.getenv("VERCEL") else "data/runtime/audit.jsonl"
        self.path = Path(path or os.getenv("AUDIT_LOG_PATH", default))
        self._lock = threading.Lock()

    def write(self, result: PipelineResult) -> None:
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": result.request_id,
            "message_sha256": hashlib.sha256(result.message.encode("utf-8")).hexdigest(),
            "mode": result.mode,
            "intent": result.classification.intent.value,
            "intent_confidence": result.classification.confidence,
            "action": result.routing.action,
            "risk_factors": result.routing.risk_factors,
            "grounded": result.draft.grounded,
            "exemplar_ids": result.draft.exemplar_ids,
            "top_similarity": result.retrieved[0].similarity if result.retrieved else 0.0,
            "latency_ms": result.latency_ms,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "estimated_cost_usd": result.estimated_cost_usd,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
