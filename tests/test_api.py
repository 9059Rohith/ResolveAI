import os

from fastapi.testclient import TestClient

os.environ["APP_API_TOKEN"] = "test-token"
from api.main import app  # noqa: E402

client = TestClient(app)


def test_health_is_public():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_browser_favicon_probe_does_not_create_a_console_error():
    assert client.get("/favicon.ico").status_code == 204


def test_public_evidence_page_and_machine_readable_proof():
    page = client.get("/evidence")
    assert page.status_code == 200
    assert "Evaluation evidence" in page.text

    response = client.get("/v1/evidence")
    assert response.status_code == 200
    body = response.json()
    assert body["dataset"]["raw_tweets"] == 2_811_774
    assert body["dataset"]["spotify_threads"] == 28_221
    assert body["evaluation"]["safety_gate"] == {"passed": 16, "total": 16}
    assert body["evaluation"]["candidate_examples"] == 200
    assert body["evaluation"]["human_verified_examples"] == 0
    assert body["evaluation"]["primary_predictions"] == 200
    assert body["evaluation"]["provisional_judge_scores"] == 200
    assert body["evaluation"]["headline_metrics_status"] == "pending_human_labels"
    assert body["leakage_control"]["component_disjoint"] is True


def test_analysis_requires_auth_when_configured():
    assert client.post("/v1/analyze", json={"message": "songs pause"}).status_code == 401


def test_analysis_validates_input_and_returns_audit_fields():
    headers = {"Authorization": "Bearer test-token"}
    assert client.post("/v1/analyze", headers=headers, json={"message": ""}).status_code == 422
    response = client.post("/v1/analyze", headers=headers, json={"message": "songs keep pausing"})
    assert response.status_code == 200
    body = response.json()
    assert {"request_id", "classification", "retrieved", "draft", "routing", "latency_ms"} <= body.keys()


def test_unknown_mode_is_rejected():
    response = client.post(
        "/v1/analyze",
        headers={"Authorization": "Bearer test-token"},
        json={"message": "hello", "mode": "magic"},
    )
    assert response.status_code == 422
