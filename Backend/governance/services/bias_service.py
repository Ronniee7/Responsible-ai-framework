from __future__ import annotations

import re
from typing import Any

# Bias categories with patterns that may indicate biased language
BIAS_PATTERNS: dict[str, list[str]] = {
    "gender": [
        r"\b(?:women?\s+(?:are|always|never|can't|cannot)\b)",
        r"\b(?:men?\s+(?:are|always|never|can't|cannot)\b)",
        r"\b(?:the\s+(?:weaker|stronger|fairer|better|inferior)\s+sex)\b",
        r"\b(?:all\s+(?:women|men|girls|boys)\s+(?:are|should|must))\b",
        r"\b(?:typical\s+(?:female|male|woman|man|girl|boy))\b",
    ],
    "racial": [
        r"\b(?:all\s+\w+\s+(?:people|individuals|workers|employees)\s+(?:are|should))\b",
        r"\b(?:those\s+people)\b",
        r"\b(?:racial\s+(?:superiority|inferiority))\b",
    ],
    "age": [
        r"\b(?:all\s+(?:old|elderly|senior|young)\s+(?:people|workers|employees)\s+(?:are|can't|cannot))\b",
        r"\b(?:too\s+old\s+(?:to|for))\b",
        r"\b(?:too\s+young\s+(?:to|for))\b",
        r"\b(?:overqualified)\b",
    ],
    "socioeconomic": [
        r"\b(?:poor\s+people\s+(?:are|always|never))\b",
        r"\b(?:rich\s+people\s+(?:are|always|never))\b",
        r"\b(?:welfare\s+(?:queen|recipient))\b",
    ],
    "religious": [
        r"\b(?:all\s+\w+\s+(?:are|should|must)\s+(?:terrorists|extremists))\b",
        r"\b(?:religious\s+(?:superiority|inferiority))\b",
    ],
    "disability": [
        r"\b(?:the\s+\w+\s+(?:are|can't|cannot|shouldn't))\b",
        r"\b(?:special\s+(?:needs|ed)\s+(?:kids|children|students))\b",
    ],
}

RISK_THRESHOLDS = {
    "low": 0.0,
    "medium": 0.3,
    "high": 0.6,
    "critical": 0.8,
}


class BiasService:
    """Detect potentially biased language in generated responses."""

    @staticmethod
    def evaluate(response_text: str) -> dict[str, Any]:
        """Analyze the response text for biased language.

        Returns:
            bias_score: float between 0.0 (no bias) and 1.0 (high bias)
            bias_category: the dominant bias category detected, or None
            risk_level: one of "low", "medium", "high", "critical"
        """
        if not response_text:
            return {
                "bias_score": 0.0,
                "bias_category": None,
                "risk_level": "low",
            }

        response_lower = response_text.lower()
        bias_score = 0.0
        detected_categories: dict[str, float] = {}

        for category, patterns in BIAS_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, response_lower)
                if matches:
                    category_score = min(1.0, len(matches) * 0.35)
                    detected_categories[category] = max(
                        detected_categories.get(category, 0.0),
                        category_score,
                    )
                    bias_score = max(bias_score, category_score)

        # Check for demographic generalizations with pronoun associations
        generalization_patterns = [
            r"\b(?:they|them|those|these)\s+(?:are|always|never)\b",
            r"\b(?:such\s+people)\b",
            r"\b(?:not\s+like\s+us)\b",
        ]
        for pattern in generalization_patterns:
            if re.search(pattern, response_lower):
                bias_score = max(bias_score, 0.2)
                detected_categories["generalization"] = 0.2

        bias_score = round(min(1.0, bias_score), 4)

        # Determine dominant category
        bias_category = max(detected_categories, key=detected_categories.get) if detected_categories else None

        # Determine risk level
        risk_level = "low"
        for level, threshold in sorted(RISK_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if bias_score >= threshold:
                risk_level = level
                break

        return {
            "bias_score": bias_score,
            "bias_category": bias_category,
            "risk_level": risk_level,
        }