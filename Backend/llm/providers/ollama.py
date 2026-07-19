from __future__ import annotations

import json
import os
from urllib import error, request

from llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Ollama HTTP provider."""

    def __init__(self, model_name: str | None = None) -> None:
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        # Check if you have a specific model running (like llama2, llama2.1, mistral, etc.)
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "OLLAMA_MODEL")

    def generate_response(self, prompt: str) -> str:
        try:
            payload = {
                "model": self.model_name, 
                "prompt": prompt, 
                "stream": False
            }
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
        
        # FIX 1: Safely serialize to valid double-quoted JSON strings
        json_data = json.dumps(payload).encode("utf-8")
        
        req = request.Request(
            url, 
            data=json_data, 
            headers={"Content-Type": "application/json"}, 
            method="POST"
        )
        
        try:
            with request.urlopen(req, timeout=30) as response:
                raw_response = response.read().decode("utf-8")
                
                # FIX 2: Correctly decode the string response into a dict object
                return json.loads(raw_response)
        except error.HTTPError as e:
            # Helpful catch-all to read out any internal messaging Ollama sends back
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"Ollama API returned HTTP {e.code}: {error_body or e.reason}") from e