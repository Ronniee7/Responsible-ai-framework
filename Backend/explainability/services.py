from __future__ import annotations

from typing import Any


class ExplainabilityService:
    """Create explanation payloads for generated responses."""

    @staticmethod
    def build_explanation(response: str, governance: dict[str, Any]) -> dict[str, Any]:
        """Create a structured explanation block for the response."""
        return {
            "summary": "Response was generated with human-safe fallback logic and governance checks.",
            "confidence": 0.87 if governance["policy_compliant"] else 0.42,
            "sources": ["internal-policy-manual", "customer-support-playbook"],
        }
