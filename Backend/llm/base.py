from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract interface for all LLM providers."""

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generate a response for the supplied prompt."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return whether the provider is available."""

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the configured model name for the provider."""

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Return the number of tokens for the supplied text."""
