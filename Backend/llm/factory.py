from __future__ import annotations

import os
from typing import Type

from llm.base import LLMProvider
from llm.providers.gemini import GeminiProvider
from llm.providers.ollama import OllamaProvider
from llm.providers.openai import OpenAIProvider


class LLMFactory:
    """Create and manage provider instances via configuration."""

    _registry: dict[str, Type[LLMProvider]] = {}

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[LLMProvider]) -> None:
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def create_provider(cls, provider_name: str | None = None) -> LLMProvider:
        cls._register_defaults()
        resolved_name = (provider_name or os.getenv("LLM_PROVIDER", "openai")).strip().lower()
        if not resolved_name:
            resolved_name = "openai"

        if resolved_name not in cls._registry:
            raise ValueError(f"Unsupported LLM provider: {resolved_name}")

        return cls._registry[resolved_name]()

    @classmethod
    def _register_defaults(cls) -> None:
        cls.register_provider("gemini", GeminiProvider)
        cls.register_provider("openai", OpenAIProvider)
        cls.register_provider("ollama", OllamaProvider)
