"""Validated objects shared across the API, pipeline and evaluator."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Intent(StrEnum):
    PLAYBACK = "playback_or_audio"
    LOGIN = "account_access"
    BILLING = "billing_or_subscription"
    APP = "app_or_device_issue"
    CONTENT = "content_availability"
    PLAN = "plan_or_feature_question"
    SECURITY = "security_or_privacy"
    OTHER = "other"


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Intent
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1, max_length=300)


class RetrievalHit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thread_id: str
    customer_message: str
    brand_reply: str
    similarity: float = Field(ge=-1, le=1)


class Draft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=800)
    grounded: bool
    exemplar_ids: list[str] = Field(max_length=5)


class Routing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str
    reason: str = Field(min_length=1, max_length=500)
    risk_factors: list[str]

    @field_validator("action")
    @classmethod
    def valid_action(cls, value: str) -> str:
        if value not in {"auto_handle", "escalate"}:
            raise ValueError("action must be auto_handle or escalate")
        return value


class PipelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str
    classification: Classification
    retrieved: list[RetrievalHit]
    draft: Draft
    routing: Routing
    mode: str
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0
