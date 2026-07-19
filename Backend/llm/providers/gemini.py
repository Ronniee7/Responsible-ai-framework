from __future__ import annotations

import os
from llm.base import LLMProvider

try:
    from google import genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None


class GeminiProvider(LLMProvider):
    """Google Gemini-backed chat provider."""
    
    def __init__(self, model_name: str | None = None) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        self.model_name = "gemini-2.0-flash"
        
        self.client = None

        # 1. Fail early if the SDK package is missing entirely
        if genai is None:
            raise ImportError(
                "The 'google-genai' package is not installed. "
                "Run `pip install google-genai` to use the Gemini provider."
            )

        # 2. Fail early if the API Key wasn't loaded from the environment
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is missing or empty. "
                "Please verify your .env file or environment configuration."
            )

        # 3. Initialize client without masking underlying client configuration exceptions
        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize Gemini Client: {exc}") from exc

    def generate_response(self, prompt: str) -> str:
        if not self.client:
            raise RuntimeError("Gemini client is uninitialized.")
        try:
            response = self.client.models.generate_content(
                model=self.model_name, 
                contents=prompt
            )
            return getattr(response, "text", "") or ""
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Gemini provider failed during generation: {exc}") from exc

    def health_check(self) -> bool:
        return self.client is not None

    def get_model_name(self) -> str:
        return self.model_name

    def count_tokens(self, text: str) -> int:
        # Note: If precise tracking matters, the SDK supports:
        # self.client.models.count_tokens(model=self.model_name, contents=text)
        return max(1, len(text.split()))