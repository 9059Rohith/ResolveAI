"""Single validated configuration source."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class RetrievalSettings(BaseModel):
    top_k: int = Field(ge=1, le=10)
    min_similarity: float = Field(ge=0, le=1)


class RoutingSettings(BaseModel):
    min_intent_confidence: float = Field(ge=0, le=1)
    always_escalate: list[str]


class LLMSettings(BaseModel):
    provider: str
    agent_model: str
    judge_model: str
    timeout_seconds: float = Field(gt=0)
    max_retries: int = Field(ge=0, le=5)
    max_input_characters: int = Field(ge=1, le=10000)
    input_price_per_million: float = Field(ge=0)
    output_price_per_million: float = Field(ge=0)


class APISettings(BaseModel):
    max_body_bytes: int = Field(ge=1024)
    requests_per_minute: int = Field(ge=1)


class Settings(BaseModel):
    brand: str
    seed: int
    retrieval: RetrievalSettings
    routing: RoutingSettings
    llm: LLMSettings
    api: APISettings


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = Settings.model_validate(
    yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
)
