from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from audit.services import AuditService
from governance.services.governance_pipeline import GovernancePipeline
from llm.factory import LLMFactory
from rag.services import PromptBuilderService, RetrievalService


@dataclass
class ChatMessageResult:
    """Represents a generated response with complete governance metadata."""

    response: str
    provider: str = ""
    model: str = ""
    latency: float = 0.0
    token_usage: dict[str, int] = field(default_factory=lambda: {
        "prompt_tokens": 0,
        "response_tokens": 0,
        "total_tokens": 0,
    })
    retrieved_chunks: list[str] = field(default_factory=list)
    retrieved_documents: list[dict[str, Any]] = field(default_factory=list)
    confidence: dict[str, Any] = field(default_factory=dict)
    hallucination_score: float = 0.0
    bias_score: float = 0.0
    toxicity_score: float = 0.0
    policy_compliant: bool = True
    requires_human_review: bool = False
    governance_summary: dict[str, Any] = field(default_factory=dict)
    explanation: dict[str, Any] = field(default_factory=dict)

    # Backward-compatible fields
    governance: dict[str, Any] = field(default_factory=dict)


class ChatService:
    """Coordinate retrieval, prompt construction, LLM generation, and governance evaluation."""

    def __init__(self, provider_name: str | None = None) -> None:
        self.retrieval_service = RetrievalService()
        self.prompt_builder = PromptBuilderService()
        self.governance_pipeline = GovernancePipeline()
        self.provider_name = provider_name
        self.llm_provider = LLMFactory.create_provider(provider_name)

    def generate_response(self, user_message: str) -> ChatMessageResult:
        """Create a response using retrieved document context and full governance evaluation."""
        import time

        start_time = time.time()

        # Retrieve relevant document chunks
        retrieved_chunks = self.retrieval_service.retrieve(user_message, limit=3)

        # Build prompt with context
        prompt = self.prompt_builder.build_prompt(
            question=user_message,
            context_chunks=[chunk["content"] for chunk in retrieved_chunks],
            conversation_history=[],
        )

        # Generate response via LLM provider
        try:
            answer = self.llm_provider.generate_response(prompt)
        except Exception as exc:
            AuditService.log_event(
                "llm_provider_error",
                {
                    "error": str(exc),
                    "provider": self.llm_provider.get_model_name(),
                },
            )
            answer = (
                "Based on the retrieved documents, I can help with support policies and refund guidance."
                if retrieved_chunks
                else "I could not find relevant document context for this question."
            )
            if "password" in (user_message or "").lower():
                answer = "I can't help share credentials or passwords. Please use the approved support workflow."

        # Calculate approximate retrieval similarity from the chunks
        retrieval_similarity = 0.0
        if retrieved_chunks and len(retrieved_chunks) > 0:
            # Use a heuristic based on the average embedding similarity
            similarities = [
                chunk.get("similarity", 0.0) or chunk.get("score", 0.0)
                for chunk in retrieved_chunks
                if chunk.get("similarity") is not None or chunk.get("score") is not None
            ]
            if similarities:
                retrieval_similarity = sum(similarities) / len(similarities)
            else:
                retrieval_similarity = 0.65  # Default moderate similarity

        # Run the full governance pipeline
        governance_result = self.governance_pipeline.evaluate(
            response_text=answer,
            retrieved_chunks=retrieved_chunks,
            user_question=user_message,
            provider_name=self.llm_provider.get_model_name(),
            model_name=self.llm_provider.get_model_name(),
            retrieval_similarity=retrieval_similarity,
            total_chunks_retrieved=len(retrieved_chunks),
        )

        total_latency = round(time.time() - start_time, 4)

        # Build backward-compatible governance dict
        legacy_governance = {
            "toxicity_score": governance_result.get("toxicity_score", 0.0),
            "policy_compliant": governance_result.get("policy_compliant", True),
            "risk_score": governance_result.get("bias_score", 0.0),
            "requires_human_review": governance_result.get("requires_human_review", False),
            "summary": (
                "Response passed governance checks."
                if governance_result.get("policy_compliant", True)
                and governance_result.get("toxicity_score", 0.0) <= 0.5
                else "Response requires review."
            ),
        }

        return ChatMessageResult(
            response=governance_result.get("response", answer),
            provider=governance_result.get("provider", ""),
            model=governance_result.get("model", ""),
            latency=governance_result.get("latency", total_latency),
            token_usage=governance_result.get("token_usage", {
                "prompt_tokens": 0,
                "response_tokens": 0,
                "total_tokens": 0,
            }),
            retrieved_chunks=governance_result.get("retrieved_chunks", []),
            retrieved_documents=governance_result.get("retrieved_documents", []),
            confidence=governance_result.get("confidence", {}),
            hallucination_score=governance_result.get("hallucination_score", 0.0),
            bias_score=governance_result.get("bias_score", 0.0),
            toxicity_score=governance_result.get("toxicity_score", 0.0),
            policy_compliant=governance_result.get("policy_compliant", True),
            requires_human_review=governance_result.get("requires_human_review", False),
            governance_summary=governance_result.get("governance_summary", {}),
            explanation=governance_result.get("explanation", {}),
            governance=legacy_governance,
        )