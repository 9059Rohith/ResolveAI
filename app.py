"""Vercel ASGI entry point; local and container runs continue to use api.main."""

from api.main import app

__all__ = ["app"]
