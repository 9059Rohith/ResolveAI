import os

from fastapi.testclient import TestClient

os.environ["APP_API_TOKEN"] = "test-token"
from api.main import app  # noqa: E402

client = TestClient(app)


def test_health_is_public():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_analysis_requires_auth_when_configured():
    assert client.post("/v1/analyze", json={"message": "songs pause"}).status_code == 401


def test_analysis_validates_input_and_returns_audit_fields():
    headers = {"Authorization": "Bearer test-token"}
    assert client.post("/v1/analyze", headers=headers, json={"message": ""}).status_code == 422
    response = client.post("/v1/analyze", headers=headers, json={"message": "songs keep pausing"})
    assert response.status_code == 200
    body = response.json()
    assert {"classification", "retrieved", "draft", "routing", "latency_ms"} <= body.keys()


def test_unknown_mode_is_rejected():
    response = client.post(
        "/v1/analyze",
        headers={"Authorization": "Bearer test-token"},
        json={"message": "hello", "mode": "magic"},
    )
    assert response.status_code == 422
