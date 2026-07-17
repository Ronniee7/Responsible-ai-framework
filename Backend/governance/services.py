from __future__ import annotations

import re
from typing import Any


class GovernanceService:
    """Provide lightweight governance checks for generated responses."""

    @staticmethod
    def evaluate_response(response_text: str) -> dict[str, Any]:
        """Evaluate a response for toxicity, policy risk, and review needs."""
        normalized = (response_text or "").strip().lower()

        toxicity_score = 0.0
        toxic_terms = ["idiot", "stupid", "fired", "hate", "worthless"]
        for term in toxic_terms:
            if term in normalized:
                toxicity_score += 0.35

        if re.search(r"\b(password|credential|secret|token)\b", normalized):
            toxicity_score += 0.1

        toxicity_score = min(toxicity_score, 1.0)

        policy_compliant = True
        risk_score = 0.0
        if re.search(r"\b(password|credential|secret|token)\b", normalized):
            policy_compliant = False
            risk_score = 0.8
        elif toxicity_score > 0.5:
            policy_compliant = False
            risk_score = max(risk_score, toxicity_score)

        requires_human_review = toxicity_score > 0.5 or not policy_compliant

        return {
            "toxicity_score": round(toxicity_score, 2),
            "policy_compliant": policy_compliant,
            "risk_score": round(risk_score, 2),
            "requires_human_review": requires_human_review,
            "summary": "Response passed governance checks." if policy_compliant and toxicity_score <= 0.5 else "Response requires review.",
        }
