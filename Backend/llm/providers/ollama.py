from __future__ import annotations

import os
from urllib import error, request

from llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Ollama HTTP provider."""

    def __init__(self, model_name: str | None = None) -> None:
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3")

    def generate_response(self, prompt: str) -> str:
        try:
            payload = {"model": self.model_name, "prompt": prompt, "stream": False}
            data = self._post_json("/api/generate", payload)
            return data.get("response", "")
        except Exception as exc:  # pragma: no cover - defensive path
            raise RuntimeError(f"Ollama provider failed: {exc}") from exc

    def health_check(self) -> bool:
        try:
            self._post_json("/api/tags", {})
            return True
        except Exception:
            return False

    def get_model_name(self) -> str:
        return self.model_name

    def count_tokens(self, text: str) -> int:
        return max(1, len(text.split()))

    def _post_json(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.host.rstrip('/')}{endpoint}"
        body = str(payload).encode("utf-8")
        req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=10) as response:
            return {"response": response.read().decode("utf-8")}
