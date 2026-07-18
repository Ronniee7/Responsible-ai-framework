from __future__ import annotations

from typing import Any

from governance.services.governance_pipeline import GovernancePipeline

# Backward-compatible wrapper that delegates to the new pipeline
_pipeline_instance: GovernancePipeline | None = None


def _get_pipeline() -> GovernancePipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = GovernancePipeline()
    return _pipeline_instance


class GovernanceService:
    """Provide governance checks for generated responses.

    This class is maintained for backward compatibility.
    New code should use GovernancePipeline directly.
    """

    @staticmethod
    def evaluate_response(response_text: str) -> dict[str, Any]:
        """Evaluate a response for toxicity, policy risk, and review needs.

        Legacy method - delegates to the new pipeline with minimal context.
        """
        pipeline = _get_pipeline()
        result = pipeline.evaluate(
            response_text=response_text,
            retrieved_chunks=[],
            user_question="",
            provider_name="unknown",
            model_name="unknown",
        )
        return {
            "toxicity_score": result.get("toxicity_score", 0.0),
            "policy_compliant": result.get("policy_compliant", True),
            "risk_score": result.get("bias_score", 0.0),
            "requires_human_review": result.get("requires_human_review", False),
            "summary": (
                "Response passed governance checks."
                if result.get("policy_compliant", True) and result.get("toxicity_score", 0.0) <= 0.5
                else "Response requires review."
            ),
        }