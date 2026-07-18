from __future__ import annotations

from typing import Any


class ConfidenceService:
    """Estimate confidence in the generated response using retrieval and hallucination signals."""

    @staticmethod
    def evaluate(
        retrieval_similarity: float = 0.0,
        supporting_chunk_count: int = 0,
        hallucination_score: float = 1.0,
        total_chunks_retrieved: int = 0,
    ) -> dict[str, Any]:
        """Calculate a confidence score for the generated response.

        Args:
            retrieval_similarity: average cosine similarity from retrieval (0.0 to 1.0)
            supporting_chunk_count: number of chunks that support the response
            hallucination_score: hallucination score (0.0 = grounded, 1.0 = hallucinated)
            total_chunks_retrieved: total number of chunks retrieved

        Returns:
            confidence_percentage: float between 0.0 and 100.0
            confidence_level: one of "very_low", "low", "medium", "high", "very_high"
        """
        # Normalize inputs
        retrieval_similarity = max(0.0, min(1.0, retrieval_similarity))
        hallucination_score = max(0.0, min(1.0, hallucination_score))
        supporting_chunk_count = max(0, supporting_chunk_count)
        total_chunks_retrieved = max(0, total_chunks_retrieved)

        # Factor 1: Retrieval quality (weight: 0.35)
        retrieval_factor = retrieval_similarity * 0.35

        # Factor 2: Supporting chunk ratio (weight: 0.25)
        if total_chunks_retrieved > 0:
            chunk_ratio = min(1.0, supporting_chunk_count / total_chunks_retrieved)
        else:
            chunk_ratio = 0.0
        chunk_factor = chunk_ratio * 0.25

        # Factor 3: Hallucination inverse (weight: 0.40)
        hallucination_factor = (1.0 - hallucination_score) * 0.40

        # Combined confidence score (0.0 to 1.0)
        confidence = retrieval_factor + chunk_factor + hallucination_factor
        confidence = max(0.0, min(1.0, confidence))

        # Convert to percentage
        confidence_percentage = round(confidence * 100.0, 2)

        # Determine confidence level
        if confidence_percentage >= 90.0:
            confidence_level = "very_high"
        elif confidence_percentage >= 70.0:
            confidence_level = "high"
        elif confidence_percentage >= 50.0:
            confidence_level = "medium"
        elif confidence_percentage >= 30.0:
            confidence_level = "low"
        else:
            confidence_level = "very_low"

        return {
            "confidence_percentage": confidence_percentage,
            "confidence_level": confidence_level,
        }