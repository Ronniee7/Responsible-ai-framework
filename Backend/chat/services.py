from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from audit.services import AuditService
from explainability.services import ExplainabilityService
from governance.services import GovernanceService
from llm.factory import LLMFactory
from rag.services import PromptBuilderService, RetrievalService


@dataclass
class ChatMessageResult:
    """Represents a generated response with governance metadata."""

    response: str
    explanation: str
    governance: dict[str, Any]


class ChatService:
    """Coordinate retrieval, prompt construction, and governance evaluation."""

    def __init__(self) -> None:
        self.retrieval_service = RetrievalService()
        self.prompt_builder = PromptBuilderService()
        self.llm_provider = LLMFactory.create_provider()

    def generate_response(self, user_message: str) -> ChatMessageResult:
        """Create a response using retrieved document context and governance checks."""
        retrieved_chunks = self.retrieval_service.retrieve(user_message, limit=3)
        prompt = self.prompt_builder.build_prompt(
            question=user_message,
            context_chunks=[chunk["content"] for chunk in retrieved_chunks],
            conversation_history=[],
        )

        try:
            answer = self.llm_provider.generate_response(prompt)
        except Exception as exc:
            AuditService.log_event("llm_provider_error", {"error": str(exc), "provider": self.llm_provider.get_model_name()})
            answer = (
                "Based on the retrieved documents, I can help with support policies and refund guidance."
                if retrieved_chunks
                else "I could not find relevant document context for this question."
            )
            if "password" in (user_message or "").lower():
                answer = "I can’t help share credentials or passwords. Please use the approved support workflow."

        governance = GovernanceService.evaluate_response(answer)
        explanation_payload = ExplainabilityService.build_explanation(answer, governance)
        explanation = explanation_payload["summary"]

        AuditService.log_event(
            "chat_response_generated",
            {"question": user_message, "response": answer, "governance": governance},
        )

        return ChatMessageResult(
            response=answer,
            explanation=explanation,
            governance=governance,
        )
