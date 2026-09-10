"""FastAPI service and static reviewer workbench."""

import os
import secrets
import time
from collections import defaultdict, deque

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from scripts.run_pipeline import make_pipeline
from src.evidence import load_evidence
from src.settings import SETTINGS

load_dotenv()
app = FastAPI(title="Spotify Support Agent", version="1.0.0", docs_url="/docs")
local_pipeline = make_pipeline("local", audit=True)
calls: dict[str, deque] = defaultdict(deque)


class AnalyzeRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    mode: str = Field(default="local", pattern="^(local|llm)$")


def auth(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("APP_API_TOKEN")
    if expected and (
        not authorization or not secrets.compare_digest(authorization, f"Bearer {expected}")
    ):
        raise HTTPException(401, "Missing or invalid bearer token")


@app.middleware("http")
async def limits(request: Request, call_next):
    length = int(request.headers.get("content-length") or 0)
    if length > SETTINGS.api.max_body_bytes:
        raise HTTPException(413, "Request body too large")
    address = request.client.host if request.client else "unknown"
    now = time.monotonic()
    queue = calls[address]
    while queue and queue[0] < now - 60:
        queue.popleft()
    if len(queue) >= SETTINGS.api.requests_per_minute:
        raise HTTPException(429, "Rate limit exceeded")
    queue.append(now)
    return await call_next(request)


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/readyz")
def ready():
    return {"status": "ready", "local_mode": True, "llm_mode": bool(os.getenv("OPENAI_API_KEY"))}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/v1/evidence")
def evidence():
    return load_evidence()


@app.post("/v1/analyze", dependencies=[Depends(auth)])
def analyze(body: AnalyzeRequest):
    if body.mode == "llm":
        try:
            return make_pipeline("llm", audit=True).run(body.message)
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(503, f"LLM mode unavailable: {type(exc).__name__}") from exc
    return local_pipeline.run(body.message)


@app.get("/")
def index():
    return FileResponse("web/index.html")


@app.get("/evidence")
def evidence_page():
    return FileResponse("web/evidence.html")


app.mount("/assets", StaticFiles(directory="web"), name="assets")
