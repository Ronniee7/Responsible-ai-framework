from __future__ import annotations

from typing import Any


class ExplanationService:
    """Generate human-readable explanations of the governance evaluation process."""

    @staticmethod
    def build_explanation(
        response_text: str,
        hallucination_result: dict[str, Any],
        bias_result: dict[str, Any],
        toxicity_result: dict[str, Any],
        policy_result: dict[str, Any],
        confidence_result: dict[str, Any],
        retrieved_chunks: list[dict[str, Any]],
        provider_name: str,
        model_name: str,
    ) -> dict[str, Any]:
        """Generate a comprehensive explanation payload for the response.

        Returns:
            reasoning_summary: concise summary of how the response was generated
            retrieved_sources: list of sources used from retrieval
            confidence_explanation: explanation of the confidence score
            governance_summary: summary of all governance checks
            human_readable_explanation: plain text explanation for end users
        """
        # Reasoning summary
        num_sources = len(retrieved_chunks)
        supporting_count = len(hallucination_result.get("supporting_chunks", []))
        reasoning_summary = (
            f"The response was generated using {model_name} via {provider_name}, "
            f"grounded in {num_sources} retrieved document chunk(s). "
            f"{supporting_count} chunk(s) provide direct support for the response content."
        )

        # Retrieved sources
        retrieved_sources = []
        for i, chunk in enumerate(retrieved_chunks):
            content = chunk.get("content", "")
            retrieved_sources.append({
                "index": i + 1,
                "content_preview": content[:200] + ("..." if len(content) > 200 else ""),
                "length": len(content),
            })

        # Confidence explanation
        confidence_percentage = confidence_result.get("confidence_percentage", 0.0)
        confidence_level = confidence_result.get("confidence_level", "unknown")
        hallucination_score = hallucination_result.get("hallucination_score", 1.0)
        bias_score = bias_result.get("bias_score", 0.0)
        toxicity_score = toxicity_result.get("toxicity", 0.0)

        confidence_factors = []
        if hallucination_score < 0.3:
            confidence_factors.append("low hallucination risk")
        elif hallucination_score > 0.7:
            confidence_factors.append("high hallucination risk")

        if supporting_count > 0:
            confidence_factors.append(f"{supporting_count} supporting document chunk(s)")

        if bias_score > 0.5:
            confidence_factors.append("potential bias detected")
        if toxicity_score > 0.5:
            confidence_factors.append("toxicity detected")

        confidence_explanation = (
            f"Confidence is {confidence_level} ({confidence_percentage}%). "
            + (f"Factors: {', '.join(confidence_factors)}." if confidence_factors else "No significant risk factors detected.")
        )

        # Governance summary
        policy_compliant = policy_result.get("policy_compliant", True)
        violations = policy_result.get("violations", [])
        bias_category = bias_result.get("bias_category")
        bias_risk = bias_result.get("risk_level", "low")
        requires_review = (
            not policy_compliant
            or bias_risk in ("high", "critical")
            or toxicity_result.get("toxicity", 0.0) > 0.5
        )

        governance_items = []
        governance_items.append({
            "check": "Hallucination Detection",
            "status": "PASS" if hallucination_result.get("grounded", False) else "WARNING",
            "score": hallucination_score,
            "details": f"Score: {hallucination_score}, Grounded: {hallucination_result.get('grounded', False)}",
        })
        governance_items.append({
            "check": "Bias Detection",
            "status": "PASS" if bias_risk == "low" else ("WARNING" if bias_risk == "medium" else "FAIL"),
            "score": bias_score,
            "details": f"Score: {bias_score}, Category: {bias_category or 'none'}, Risk: {bias_risk}",
        })
        governance_items.append({
            "check": "Toxicity Detection",
            "status": "PASS" if toxicity_score <= 0.3 else ("WARNING" if toxicity_score <= 0.6 else "FAIL"),
            "score": toxicity_score,
            "details": f"Toxicity: {toxicity_score}, Harassment: {toxicity_result.get('harassment', 0.0)}, Hate: {toxicity_result.get('hate', 0.0)}",
        })
        governance_items.append({
            "check": "Policy Validation",
            "status": "PASS" if policy_compliant else "FAIL",
            "score": 0.0 if policy_compliant else 1.0,
            "details": f"Compliant: {policy_compliant}, Violations: {len(violations)}, Action: {policy_result.get('recommended_action', 'none')}",
        })
        governance_items.append({
            "check": "Confidence Estimation",
            "status": "PASS" if confidence_level in ("high", "very_high") else ("WARNING" if confidence_level == "medium" else "FAIL"),
            "score": confidence_percentage / 100.0,
            "details": f"Confidence: {confidence_percentage}% ({confidence_level})",
        })

        governance_summary = {
            "overall_status": "PASS" if (policy_compliant and not requires_review) else "FAIL",
            "requires_human_review": requires_review,
            "items": governance_items,
        }

        # Human-readable explanation
        if requires_review:
            review_reasons = []
            if not policy_compliant:
                violation_names = [v["policy_name"] for v in violations[:3]]
                review_reasons.append(f"policy violations ({', '.join(violation_names)})")
            if bias_risk in ("high", "critical"):
                review_reasons.append(f"bias risk ({bias_risk})")
            if toxicity_score > 0.5:
                review_reasons.append(f"toxicity detected ({toxicity_score})")
            human_readable_extra = f" This response requires human review due to: {'; '.join(review_reasons)}." if review_reasons else ""
        else:
            human_readable_extra = " All governance checks passed."

        human_readable_explanation = (
            f"The response was generated using {model_name} via {provider_name} "
            f"with {confidence_level.lower()} confidence ({confidence_percentage}%)."
            f"{human_readable_extra}"
        )

        # Include violation details in the payload
        violation_details = [
            {
                "policy_id": v["policy_id"],
                "policy_name": v["policy_name"],
                "severity": v["severity"],
                "description": v["description"],
            }
            for v in violations
        ]

        return {
            "reasoning_summary": reasoning_summary,
            "retrieved_sources": retrieved_sources,
            "confidence_explanation": confidence_explanation,
            "governance_summary": governance_summary,
            "human_readable_explanation": human_readable_explanation,
            "violation_details": violation_details,
        }