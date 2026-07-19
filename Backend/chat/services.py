from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from audit.services import AuditService
from governance.services.governance_pipeline import GovernancePipeline
from llm.factory import LLMFactory
from rag.services import PromptBuilderService, RetrievalService


@dataclass
class ChatMessageResult:
    """
    Represents the final chat response returned to the API layer,
    including governance metadata and backward-compatible fields.
    """

    response: str

    # Model information
    provider: str = ""
    model: str = ""
    latency: float = 0.0

    # Token usage
    token_usage: dict[str, int] = field(
        default_factory=lambda: {
            "prompt_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0,
        }
    )

    # Retrieval
    retrieved_chunks: list[dict[str, Any]] = field(default_factory=list)
    retrieved_documents: list[dict[str, Any]] = field(default_factory=list)

    # Governance
    confidence: dict[str, Any] = field(default_factory=dict)
    hallucination_score: float = 0.0
    bias_score: float = 0.0
    toxicity_score: float = 0.0
    policy_compliant: bool = True
    requires_human_review: bool = False

    governance_summary: dict[str, Any] = field(default_factory=dict)
    explanation: dict[str, Any] = field(default_factory=dict)

    # Backward compatibility
    governance: dict[str, Any] = field(default_factory=dict)


class ChatService:
    """
    Coordinates:

    • Retrieval
    • Prompt construction
    • LLM generation
    • Governance evaluation
    • Audit logging

    This service intentionally contains orchestration only.
    """

    def __init__(self, provider_name: str | None = None) -> None:
        self.provider_name = provider_name

        self.retrieval_service = RetrievalService()
        self.prompt_builder = PromptBuilderService()
        self.governance_pipeline = GovernancePipeline()

        self.llm_provider = LLMFactory.create_provider(provider_name)

    def generate_response(self, user_message: str) -> ChatMessageResult:
        """
        Generate a governance-aware response grounded in retrieved documents.
        """

        start_time = time.perf_counter()

        # ---------------------------------------------------------
        # Retrieve supporting document chunks
        # ---------------------------------------------------------

        retrieved_chunks = self.retrieval_service.retrieve(
            question=user_message,
            limit=3,
        )

        context_chunks = [
            chunk.get("content", "")
            for chunk in retrieved_chunks
            if chunk.get("content")
        ]

        # ---------------------------------------------------------
        # Build prompt
        # ---------------------------------------------------------

        prompt = self.prompt_builder.build_prompt(
            question=user_message,
            context_chunks=context_chunks,
            conversation_history=[],
        )

        # ---------------------------------------------------------
        # Generate response
        # ---------------------------------------------------------

        llm_failed = False

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
            # FORCE CRASH HERE SO THE PIPELINE DOESN'T MASK IT:
            raise exc

        # except Exception as exc:

        #     llm_failed = True

        #     AuditService.log_event(
        #         "llm_generation_failed",
        #         {
        #             "provider": self.provider_name or "default",
        #             "model": self.llm_provider.get_model_name(),
        #             "error": str(exc),
        #         },
        #     )

        #     if retrieved_chunks:
        #         answer = (
        #             "The language model is currently unavailable. "
        #             "Relevant document context was retrieved, but a grounded "
        #             "response could not be generated."
        #         )
        #     else:
        #         answer = (
        #             "The language model is currently unavailable and "
        #             "no supporting document context could be retrieved."
        #         )

        # ---------------------------------------------------------
        # Estimate retrieval similarity
        # ---------------------------------------------------------

        similarity_scores = []

        for chunk in retrieved_chunks:

            if chunk.get("similarity") is not None:
                similarity_scores.append(chunk["similarity"])

            elif chunk.get("score") is not None:
                similarity_scores.append(chunk["score"])

        retrieval_similarity = (
            sum(similarity_scores) / len(similarity_scores)
            if similarity_scores
            else 0.0
        )

        latency = round(time.perf_counter() - start_time, 4)

        # ---------------------------------------------------------
        # Audit successful request
        # ---------------------------------------------------------

        AuditService.log_event(
            "chat_request_processed",
            {
                "provider": self.provider_name or "default",
                "model": self.llm_provider.get_model_name(),
                "question": user_message,
                "retrieved_chunks": len(retrieved_chunks),
                "latency": latency,
                "llm_failed": llm_failed,
            },
        )

        governance_result = self.governance_pipeline.evaluate(
            response_text=answer,
            retrieved_chunks=retrieved_chunks,
            user_question=user_message,
            provider_name=self.provider_name or self.llm_provider.__class__.__name__.replace(
                "Provider", ""
            ),
            model_name=self.llm_provider.get_model_name(),
            retrieval_similarity=retrieval_similarity,
            total_chunks_retrieved=len(retrieved_chunks),
        )

        # ---------------------------------------------------------
        # Merge latency if pipeline didn't provide one
        # ---------------------------------------------------------

        governance_result.setdefault("latency", latency)

        # ---------------------------------------------------------
        # Estimate token usage when provider doesn't expose it
        # ---------------------------------------------------------

        if "token_usage" not in governance_result:

            prompt_tokens = self.llm_provider.count_tokens(prompt)
            response_tokens = self.llm_provider.count_tokens(answer)

            governance_result["token_usage"] = {
                "prompt_tokens": prompt_tokens,
                "response_tokens": response_tokens,
                "total_tokens": prompt_tokens + response_tokens,
            }

        # ---------------------------------------------------------
        # Ensure provider/model are populated
        # ---------------------------------------------------------

        governance_result.setdefault(
            "provider",
            self.provider_name
            or self.llm_provider.__class__.__name__.replace("Provider", ""),
        )

        governance_result.setdefault(
            "model",
            self.llm_provider.get_model_name(),
        )

        # ---------------------------------------------------------
        # Backward-compatible governance structure
        # ---------------------------------------------------------

        legacy_governance = {
            "toxicity_score": governance_result.get("toxicity_score", 0.0),
            "policy_compliant": governance_result.get(
                "policy_compliant",
                True,
            ),
            "risk_score": governance_result.get(
                "bias_score",
                0.0,
            ),
            "requires_human_review": governance_result.get(
                "requires_human_review",
                False,
            ),
            "summary": (
                "Response passed governance checks."
                if (
                    governance_result.get(
                        "policy_compliant",
                        True,
                    )
                    and governance_result.get(
                        "toxicity_score",
                        0.0,
                    )
                    <= 0.5
                )
                else "Response requires governance review."
            ),
        }

        # ---------------------------------------------------------
        # Final audit record
        # ---------------------------------------------------------

        AuditService.log_event(
            "governance_completed",
            {
                "provider": governance_result["provider"],
                "model": governance_result["model"],
                "confidence": governance_result.get("confidence"),
                "hallucination_score": governance_result.get(
                    "hallucination_score"
                ),
                "bias_score": governance_result.get(
                    "bias_score"
                ),
                "toxicity_score": governance_result.get(
                    "toxicity_score"
                ),
                "policy_compliant": governance_result.get(
                    "policy_compliant"
                ),
                "requires_human_review": governance_result.get(
                    "requires_human_review"
                ),
            },
        )

        # ---------------------------------------------------------
        # Build final API response
        # ---------------------------------------------------------

        return ChatMessageResult(
            response=governance_result.get(
                "response",
                answer,
            ),
            provider=governance_result["provider"],
            model=governance_result["model"],
            latency=governance_result["latency"],
            token_usage=governance_result["token_usage"],
            retrieved_chunks=governance_result.get(
                "retrieved_chunks",
                retrieved_chunks,
            ),
            retrieved_documents=governance_result.get(
                "retrieved_documents",
                [],
            ),
            confidence=governance_result.get(
                "confidence",
                {},
            ),
            hallucination_score=governance_result.get(
                "hallucination_score",
                0.0,
            ),
            bias_score=governance_result.get(
                "bias_score",
                0.0,
            ),
            toxicity_score=governance_result.get(
                "toxicity_score",
                0.0,
            ),
            policy_compliant=governance_result.get(
                "policy_compliant",
                True,
            ),
            requires_human_review=governance_result.get(
                "requires_human_review",
                False,
            ),
            governance_summary=governance_result.get(
                "governance_summary",
                {},
            ),
            explanation=governance_result.get(
                "explanation",
                {},
            ),
            governance=legacy_governance,
        )