"""Fail-closed deterministic routing policy."""

import re

from src.schemas import Classification, Intent, Routing
from src.settings import SETTINGS

HIGH_RISK = {Intent(value) for value in SETTINGS.routing.always_escalate}


def route(classification: Classification, best_similarity: float, draft_text: str = "") -> Routing:
    risks = list(classification.risk_factors)
    if classification.intent in HIGH_RISK:
        risks.append("high_risk_intent")
    if classification.confidence < SETTINGS.routing.min_intent_confidence:
        risks.append("low_intent_confidence")
    if best_similarity < SETTINGS.retrieval.min_similarity:
        risks.append("weak_precedent")
    if re.search(
        r"\b(?:send|share|dm)\b.{0,40}\b(?:password|email|username|phone|account number)\b",
        draft_text,
        re.I,
    ):
        risks.append("sensitive_data_request")
    if risks:
        return Routing(
            action="escalate",
            risk_factors=risks,
            reason="Human review required: " + ", ".join(risks).replace("_", " ") + ".",
        )
    return Routing(
        action="auto_handle",
        risk_factors=[],
        reason="Low-risk intent with confident classification and a relevant resolved precedent.",
    )
