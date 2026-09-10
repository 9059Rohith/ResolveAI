import json

import httpx
import pytest

from src.draft import LLMDrafter
from src.llm_client import OpenAIClient
from src.schemas import Classification, Draft, Intent, RetrievalHit


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "output": [{"content": [{"type": "output_text", "text": self.text}]}],
            "usage": {"input_tokens": 10, "output_tokens": 4},
        }


def test_structured_client_retries_malformed_json(monkeypatch):
    responses = iter(
        [
            FakeResponse("not json"),
            FakeResponse(
                json.dumps({"intent": "other", "confidence": 0.5, "rationale": "unclear"})
            ),
        ]
    )
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: next(responses))
    client = OpenAIClient("test", api_key="secret", retries=1)
    result = client.structured("message", Classification)
    assert result.intent == Intent.OTHER
    assert client.input_tokens == 20


def test_drafter_rejects_invented_citation():
    class Client:
        def structured(self, prompt, schema):
            return Draft(text="reply", grounded=True, exemplar_ids=["invented"])

    hit = RetrievalHit(thread_id="real", customer_message="x", brand_reply="y", similarity=0.8)
    with pytest.raises(ValueError, match="not supplied"):
        LLMDrafter(Client())(
            "x", Classification(intent=Intent.APP, confidence=0.8, rationale="app"), [hit]
        )
