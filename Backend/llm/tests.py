import os
from unittest.mock import patch

from django.test import SimpleTestCase

from llm.base import LLMProvider
from llm.factory import LLMFactory
from llm.providers.gemini import GeminiProvider
from llm.providers.ollama import OllamaProvider
from llm.providers.openai import OpenAIProvider


class MockProvider(LLMProvider):
    def generate_response(self, prompt: str) -> str:
        return "mock-response"

    def health_check(self) -> bool:
        return True

    def get_model_name(self) -> str:
        return "mock-model"

    def count_tokens(self, text: str) -> int:
        return len(text.split())


class LLMFactoryTests(SimpleTestCase):
    def test_factory_selects_gemini_provider_from_environment(self) -> None:
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini"}, clear=False):
            provider = LLMFactory.create_provider()

        self.assertIsInstance(provider, GeminiProvider)

    def test_factory_selects_openai_provider_from_environment(self) -> None:
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai"}, clear=False):
            provider = LLMFactory.create_provider()

        self.assertIsInstance(provider, OpenAIProvider)

    def test_factory_selects_ollama_provider_from_environment(self) -> None:
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=False):
            provider = LLMFactory.create_provider()

        self.assertIsInstance(provider, OllamaProvider)

    def test_factory_raises_for_unknown_provider(self) -> None:
        with patch.dict(os.environ, {"LLM_PROVIDER": "unknown"}, clear=False):
            with self.assertRaises(ValueError):
                LLMFactory.create_provider()

    def test_factory_can_register_and_use_mock_provider(self) -> None:
        LLMFactory.register_provider("mock", MockProvider)
        with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}, clear=False):
            provider = LLMFactory.create_provider()

        self.assertIsInstance(provider, MockProvider)
        self.assertTrue(provider.health_check())
        self.assertEqual(provider.get_model_name(), "mock-model")
        self.assertEqual(provider.count_tokens("one two three"), 3)
        self.assertEqual(provider.generate_response("prompt"), "mock-response")
