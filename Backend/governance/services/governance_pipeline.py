from __future__ import annotations

import time
from typing import Any

from audit.services import AuditService
from governance.services.bias_service import BiasService
from governance.services.confidence_service import ConfidenceService
from governance.services.explanation_service import ExplanationService
from governance.services.hallucination_service import HallucinationService
from governance.services.policy_service import PolicyService
from governance.services.toxicity_service import ToxicityService


class GovernancePipeline:
    """Orchestrate the complete governance evaluation pipeline.

    Every generated response passes through:
    1. Hallucination Detection
    2. Bias Detection
    3. Toxicity Detection
    4. Policy Validation
    5. Confidence Estimation
    6. Explainability Generation
    7. Audit Logging
    """

    def __init__(self) -> None:
        self.hallucination_service = HallucinationService()
        self.bias_service = BiasService()
        self.toxicity_service = ToxicityService()
        self.policy_service = PolicyService()
        self.confidence_service = ConfidenceService()
        self.explanation_service = ExplanationService()

    def evaluate(
        self,
        response_text: str,
        retrieved_chunks: list[dict[str, Any]],
        user_question: str,
        provider_name: str,
        model_name: str,
        retrieval_similarity: float = 0.0,
        total_chunks_retrieved: int = 0,
    ) -> dict[str, Any]:
        """Run the full governance pipeline on a generated response.

        Args:
            response_text: The LLM-generated response text
            retrieved_chunks: List of retrieved document chunks with content
            user_question: The original user question
            provider_name: Name of the LLM provider
            model_name: Name of the model used
            retrieval_similarity: Average similarity score from retrieval
            total_chunks_retrieved: Total number of chunks retrieved

        Returns:
            Complete governance result with all evaluations
        """
        start_time = time.time()

        # Step 1: Hallucination Detection
        hallucination_result = self.hallucination_service.evaluate(
            response_text=response_text,
            retrieved_chunks=retrieved_chunks,
        )

        # Step 2: Bias Detection
        bias_result = self.bias_service.evaluate(response_text=response_text)

        # Step 3: Toxicity Detection
        toxicity_result = self.toxicity_service.evaluate(response_text=response_text)

        # Step 4: Policy Validation
        has_retrieved_context = len(retrieved_chunks) > 0
        policy_result = self.policy_service.evaluate(
            response_text=response_text,
            has_retrieved_context=has_retrieved_context,
        )

        # Step 5: Confidence Estimation
        hallucination_score = hallucination_result.get("hallucination_score", 1.0)
        supporting_chunks = hallucination_result.get("supporting_chunks", [])
        confidence_result = self.confidence_service.evaluate(
            retrieval_similarity=retrieval_similarity,
            supporting_chunk_count=len(supporting_chunks),
            hallucination_score=hallucination_score,
            total_chunks_retrieved=total_chunks_retrieved,
        )

        # Step 6: Explainability Generation
        explanation_result = self.explanation_service.build_explanation(
            response_text=response_text,
            hallucination_result=hallucination_result,
            bias_result=bias_result,
            toxicity_result=toxicity_result,
            policy_result=policy_result,
            confidence_result=confidence_result,
            retrieved_chunks=retrieved_chunks,
            provider_name=provider_name,
            model_name=model_name,
        )

        # Compute latency
        latency = round(time.time() - start_time, 4)

        # Assess if human review is needed
        requires_human_review = (
            not policy_result.get("policy_compliant", True)
            or bias_result.get("risk_level") in ("high", "critical")
            or toxicity_result.get("toxicity", 0.0) > 0.5
            or hallucination_score > 0.7
        )

        # Compile governance summary
        governance_summary = explanation_result.get("governance_summary", {})
        governance_summary["requires_human_review"] = requires_human_review

        # Count token usage (approximate)
        token_usage = {
            "prompt_tokens": len(user_question.split()),
            "response_tokens": len(response_text.split()),
            "total_tokens": len(user_question.split()) + len(response_text.split()),
        }

        # Step 7: Audit Logging
        AuditService.log_event(
            "governance_pipeline_completed",
            {
                "question": user_question,
                "retrieved_chunks_count": len(retrieved_chunks),
                "provider": provider_name,
                "model": model_name,
                "response_preview": response_text[:200],
                "hallucination_score": hallucination_score,
                "bias_score": bias_result.get("bias_score"),
                "toxicity_score": toxicity_result.get("toxicity"),
                "policy_compliant": policy_result.get("policy_compliant"),
                "confidence_percentage": confidence_result.get("confidence_percentage"),
                "requires_human_review": requires_human_review,
                "latency": latency,
                "token_usage": token_usage,
            },
        )

        return {
            "response": response_text,
            "provider": provider_name,
            "model": model_name,
            "latency": latency,
            "token_usage": token_usage,
            "retrieved_chunks": [chunk.get("content", "") for chunk in retrieved_chunks],
            "retrieved_documents": [
                {
                    "index": i + 1,
                    "content_preview": chunk.get("content", "")[:200],
                }
                for i, chunk in enumerate(retrieved_chunks)
            ],
            "hallucination": hallucination_result,
            "bias": bias_result,
            "toxicity": toxicity_result,
            "policy": policy_result,
            "confidence": confidence_result,
            "explanation": explanation_result,
            "governance_summary": governance_summary,
            "requires_human_review": requires_human_review,
            "hallucination_score": hallucination_score,
            "bias_score": bias_result.get("bias_score", 0.0),
            "toxicity_score": toxicity_result.get("toxicity", 0.0),
            "policy_compliant": policy_result.get("policy_compliant", True),
        }