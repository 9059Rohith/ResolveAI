"""Composable classify → retrieve → draft → route pipeline."""

import time
import uuid

from src.classifier import contains_prompt_injection
from src.draft import local_draft
from src.router import route
from src.schemas import PipelineResult
from src.settings import SETTINGS


class SupportPipeline:
    def __init__(self, classifier, retriever, draft_fn=local_draft, mode="local", audit_log=None):
        self.classifier, self.retriever, self.draft_fn, self.mode = (
            classifier,
            retriever,
            draft_fn,
            mode,
        )
        self.audit_log = audit_log

    def run(self, message: str) -> PipelineResult:
        started = time.perf_counter()
        client = getattr(self.classifier, "client", None)
        before_in = getattr(client, "input_tokens", 0)
        before_out = getattr(client, "output_tokens", 0)
        classification = self.classifier.classify(message)
        hits = (
            []
            if contains_prompt_injection(message)
            else self.retriever.search(message, classification.intent, SETTINGS.retrieval.top_k)
        )
        draft = self.draft_fn(message, classification, hits)
        best = hits[0].similarity if hits else 0
        routing = route(classification, best if draft.grounded else 0, draft.text)
        input_tokens = getattr(client, "input_tokens", 0) - before_in
        output_tokens = getattr(client, "output_tokens", 0) - before_out
        result = PipelineResult(
            request_id=str(uuid.uuid4()),
            message=message,
            classification=classification,
            retrieved=hits,
            draft=draft,
            routing=routing,
            mode=self.mode,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=round(
                input_tokens * SETTINGS.llm.input_price_per_million / 1_000_000
                + output_tokens * SETTINGS.llm.output_price_per_million / 1_000_000,
                6,
            ),
        )
        if self.audit_log:
            self.audit_log.write(result)
        return result
