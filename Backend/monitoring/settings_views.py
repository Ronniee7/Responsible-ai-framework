from __future__ import annotations

import json
import os
from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

SETTINGS_FILE = os.path.join(os.getcwd(), "governance_settings.json")

DEFAULT_SETTINGS: dict[str, Any] = {
    "provider": "openai",
    "model": {
        "openai": "gpt-4.1",
        "gemini": "gemini-2.5-flash",
        "ollama": "llama3",
    },
    "temperature": 0.7,
    "max_tokens": 1024,
    "governance_thresholds": {
        "hallucination_threshold": 0.4,
        "bias_threshold": 0.5,
        "toxicity_threshold": 0.5,
        "confidence_threshold": 50.0,
    },
}


def _load_settings() -> dict[str, Any]:
    """Load settings from the JSON file, falling back to defaults."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as handle:
                stored = json.load(handle)
                # Merge with defaults to ensure all keys exist
                merged = dict(DEFAULT_SETTINGS)
                merged.update(stored)
                return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_SETTINGS)


def _save_settings(settings: dict[str, Any]) -> None:
    """Persist settings to the JSON file."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)


class SettingsView(APIView):
    """Get or update application settings."""

    @extend_schema(
        responses={200: dict},
        description="Return current application settings.",
    )
    def get(self, request, *args, **kwargs):
        settings = _load_settings()
        return Response(settings, status=status.HTTP_200_OK)

    @extend_schema(
        request=dict,
        responses={200: dict},
        description="Update application settings.",
    )
    def post(self, request, *args, **kwargs):
        current = _load_settings()
        updates = request.data

        # Merge updates into current settings
        for key, value in updates.items():
            if key in current and isinstance(current[key], dict) and isinstance(value, dict):
                current[key].update(value)
            else:
                current[key] = value

        _save_settings(current)
        return Response(current, status=status.HTTP_200_OK)