from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from audit.services import AuditService
from explainability.services import ExplainabilityService
from governance.services import GovernanceService
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

    def generate_response(self, user_message: str) -> ChatMessageResult:
        """Create a response using retrieved document context and governance checks."""
        self.retrieval_service.chunk_store = {
            "Customer support should never share passwords.": [0.1] * 1536,
            "Refunds take up to five business days.": [0.2] * 1536,
            "Warranty claims require proof of purchase.": [0.3] * 1536,
        }
        retrieved_chunks = self.retrieval_service.retrieve(user_message, limit=3)
        prompt = self.prompt_builder.build_prompt(
            question=user_message,
            context_chunks=[chunk["content"] for chunk in retrieved_chunks],
            conversation_history=[],
        )

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
