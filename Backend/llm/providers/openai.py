from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI-backed chat provider."""

    def __init__(self, model_name: str | None = None) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-4.1")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def generate_response(self, prompt: str) -> str:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        try:
            response = self.client.responses.create(model=self.model_name, input=prompt)
            return getattr(response, "output_text", "") or ""
        except Exception as exc:  # pragma: no cover - defensive path
            raise RuntimeError(f"OpenAI provider failed: {exc}") from exc

    def health_check(self) -> bool:
        return bool(self.client)

    def get_model_name(self) -> str:
        return self.model_name

    def count_tokens(self, text: str) -> int:
        return max(1, len(text.split()))
