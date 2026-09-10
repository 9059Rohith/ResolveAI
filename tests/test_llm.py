import json
from pathlib import Path

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


def test_client_loads_key_from_env_file(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=from-file\n", encoding="utf-8")

    client = OpenAIClient("test", env_file=env_file)

    assert client.key == "from-file"


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


def test_strict_schema_marks_every_property_required(monkeypatch):
    captured = {}

    def post(*args, **kwargs):
        captured.update(kwargs["json"])
        return FakeResponse(
            json.dumps(
                {
                    "intent": "other",
                    "confidence": 0.5,
                    "rationale": "unclear",
                    "risk_factors": [],
                }
            )
        )

    monkeypatch.setattr(httpx, "post", post)
    OpenAIClient("test", api_key="secret").structured("message", Classification)

    schema = captured["text"]["format"]["schema"]
    assert set(schema["required"]) == set(schema["properties"])


def test_drafter_rejects_invented_citation():
    class Client:
        def structured(self, prompt, schema):
            return Draft(text="reply", grounded=True, exemplar_ids=["invented"])

    hit = RetrievalHit(thread_id="real", customer_message="x", brand_reply="y", similarity=0.8)
    with pytest.raises(ValueError, match="not supplied"):
        LLMDrafter(Client())(
            "x", Classification(intent=Intent.APP, confidence=0.8, rationale="app"), [hit]
        )


def test_drafter_removes_historical_signature_and_dead_link_placeholder():
    class Client:
        def structured(self, prompt, schema):
            return Draft(text="Please restart the app. /MG [LINK]", grounded=True, exemplar_ids=["real"])

    hit = RetrievalHit(thread_id="real", customer_message="x", brand_reply="y", similarity=0.8)
    draft = LLMDrafter(Client())(
        "x", Classification(intent=Intent.APP, confidence=0.8, rationale="app"), [hit]
    )

    assert draft.text == "Please restart the app."


def test_drafter_prompt_forbids_sensitive_identifier_requests():
    class Client:
        def structured(self, prompt, schema):
            assert "Never request usernames, email addresses, passwords, or payment details" in prompt
            return Draft(text="Please share your device type.", grounded=True, exemplar_ids=["real"])

    hit = RetrievalHit(thread_id="real", customer_message="x", brand_reply="y", similarity=0.8)
    LLMDrafter(Client())(
        "x", Classification(intent=Intent.PLAYBACK, confidence=0.8, rationale="audio"), [hit]
    )
