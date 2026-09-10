from api.main import app as api_app
from app import app
from src.audit import JsonlAuditLog


def test_vercel_entrypoint_exports_the_same_asgi_application():
    assert app is api_app


def test_vercel_audit_uses_writable_temporary_storage(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("AUDIT_LOG_PATH", raising=False)
    assert JsonlAuditLog().path.as_posix() == "/tmp/resolve-audit.jsonl"
