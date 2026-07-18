from __future__ import annotations

import re
from typing import Any


class HallucinationService:
    """Detect hallucination by comparing the generated response with retrieved document chunks."""

    @staticmethod
    def evaluate(
        response_text: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Compare the response against retrieved chunks to estimate hallucination risk.

        Returns:
            hallucination_score: float between 0.0 (no hallucination) and 1.0 (hallucinated)
            grounded: bool indicating whether the response is sufficiently grounded
            supporting_chunks: list of chunk contents that support the response
            confidence: float confidence in the hallucination assessment
        """
        if not response_text or not retrieved_chunks:
            return {
                "hallucination_score": 1.0,
                "grounded": False,
                "supporting_chunks": [],
                "confidence": 0.0,
            }

        response_lower = response_text.lower()
        response_sentences = [
            s.strip()
            for s in re.split(r"[.!?]+", response_text)
            if len(s.strip()) > 10
        ]

        supporting_chunks: list[str] = []
        total_overlap = 0.0
        chunk_count = len(retrieved_chunks)

        for chunk in retrieved_chunks:
            content = chunk.get("content", "")
            if not content:
                continue
            content_lower = content.lower()

            # Token overlap between response and chunk
            response_tokens = set(response_lower.split())
            chunk_tokens = set(content_lower.split())
            if not response_tokens or not chunk_tokens:
                continue

            overlap = len(response_tokens & chunk_tokens) / len(response_tokens)

            # Check how many sentences have supporting evidence
            supported_sentences = 0
            for sentence in response_sentences:
                sentence_words = set(sentence.lower().split())
                if len(sentence_words) < 3:
                    supported_sentences += 1
                    continue
                sentence_overlap = len(sentence_words & chunk_tokens) / len(sentence_words)
                if sentence_overlap > 0.15:
                    supported_sentences += 1

            sentence_support_ratio = (
                supported_sentences / len(response_sentences) if response_sentences else 0.0
            )

            combined_score = (overlap * 0.6) + (sentence_support_ratio * 0.4)
            total_overlap = max(total_overlap, combined_score)

            if combined_score > 0.2:
                supporting_chunks.append(content)

        if len(response_sentences) == 0:
            hallucination_score = 0.5
        else:
            hallucination_score = round(1.0 - total_overlap, 4)
            hallucination_score = max(0.0, min(1.0, hallucination_score))

        grounded = hallucination_score < 0.4
        confidence = round(min(1.0, chunk_count / 3.0), 4)

        return {
            "hallucination_score": hallucination_score,
            "grounded": grounded,
            "supporting_chunks": supporting_chunks,
            "confidence": confidence,
        }