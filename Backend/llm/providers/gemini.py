from __future__ import annotations

import os

from llm.base import LLMProvider

try:
    from google import genai  # type: ignore
except ImportError:  # pragma: no cover - optional dependency path
    genai = None


class GeminiProvider(LLMProvider):
    """Google Gemini-backed chat provider."""

    def __init__(self, model_name: str | None = None) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.client = None
        if self.api_key and genai is not None:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None

    def generate_response(self, prompt: str) -> str:
        if not self.client:
            raise RuntimeError("GEMINI_API_KEY is not configured or the Gemini SDK is unavailable.")
        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            return getattr(response, "text", "") or ""
        except Exception as exc:  # pragma: no cover - defensive path
            raise RuntimeError(f"Gemini provider failed: {exc}") from exc

    def health_check(self) -> bool:
        return bool(self.client)

    def get_model_name(self) -> str:
        return self.model_name

    def count_tokens(self, text: str) -> int:
        return max(1, len(text.split()))
