"""Small OpenAI-compatible structured-output client with timeouts and bounded retries."""

import json
import os
import time
from pathlib import Path
from typing import TypeVar

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def _strict_schema(value):
    """Convert Pydantic defaults into the strict subset accepted by Responses API."""
    if isinstance(value, dict):
        normalized = {key: _strict_schema(item) for key, item in value.items()}
        if normalized.get("type") == "object" and "properties" in normalized:
            normalized["required"] = list(normalized["properties"])
            normalized["additionalProperties"] = False
        return normalized
    if isinstance(value, list):
        return [_strict_schema(item) for item in value]
    return value


class OpenAIClient:
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        timeout: float = 30,
        retries: int = 2,
        env_file: str | Path | None = None,
    ):
        self.model = model
        if not api_key and not os.getenv("OPENAI_API_KEY"):
            default_env = Path(__file__).parents[1] / ".env"
            load_dotenv(env_file or default_env, override=False)
        self.key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise RuntimeError("OPENAI_API_KEY is required for llm mode")
        self.timeout, self.retries = timeout, retries
        self.input_tokens = 0
        self.output_tokens = 0

    def structured(self, prompt: str, schema: type[T]) -> T:
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": "Follow the JSON schema exactly."},
                {"role": "user", "content": prompt},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema.__name__,
                    "strict": True,
                    "schema": _strict_schema(schema.model_json_schema()),
                }
            },
        }
        error = None
        for attempt in range(self.retries + 1):
            try:
                response = httpx.post(
                    "https://api.openai.com/v1/responses",
                    headers={"Authorization": f"Bearer {self.key}"},
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                usage = data.get("usage", {})
                self.input_tokens += int(usage.get("input_tokens", 0))
                self.output_tokens += int(usage.get("output_tokens", 0))
                text = next(
                    part["text"]
                    for item in data["output"]
                    for part in item["content"]
                    if part["type"] == "output_text"
                )
                return schema.model_validate(json.loads(text))
            except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError) as exc:
                error = exc
                if attempt < self.retries:
                    time.sleep(0.25 * (2**attempt))
        raise RuntimeError(
            f"LLM request failed after {self.retries + 1} attempts: {type(error).__name__}"
        ) from error
