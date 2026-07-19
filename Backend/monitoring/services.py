from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from audit.services import AuditService
from governance.models import Review
from rag.models import Document, DocumentChunk


class DashboardService:
    """Aggregate metrics for the monitoring dashboard."""

    @staticmethod
    def get_summary() -> dict[str, Any]:
        """Return a high-level summary of system metrics."""
        documents = Document.objects.all()
        total_documents = documents.count()
        total_chunks = DocumentChunk.objects.count()
        total_embeddings = DocumentChunk.objects.exclude(embedding__exact=[]).exclude(embedding__isnull=True).count()

        # Gather audit events for analytics
        audit_events = AuditService.get_all_events()

        # Count conversations (chat responses)
        conversations = sum(1 for e in audit_events if e.get("event_type") == "governance_pipeline_completed")

        # Track provider usage
        provider_usage: dict[str, int] = {}
        for event in audit_events:
            details = event.get("details", {})
            provider = details.get("provider", "unknown")
            if provider:
                provider_usage[provider] = provider_usage.get(provider, 0) + 1

        # Calculate average metrics from governance events
        governance_events = [e for e in audit_events if e.get("event_type") == "governance_pipeline_completed"]

        avg_latency = 0.0
        avg_confidence = 0.0
        hallucination_count = 0
        policy_violation_count = 0
        human_review_count = 0
        total_gov = len(governance_events)

        for event in governance_events:
            details = event.get("details", {})
            avg_latency += details.get("latency", 0.0)
            avg_confidence += details.get("confidence_percentage", 0.0) or 0.0
            if details.get("hallucination_score", 0) and details["hallucination_score"] > 0.5:
                hallucination_count += 1
            if details.get("policy_compliant") is False:
                policy_violation_count += 1
            if details.get("requires_human_review"):
                human_review_count += 1

        if total_gov > 0:
            avg_latency /= total_gov
            avg_confidence /= total_gov

        governance_pass_rate = 0.0
        if total_gov > 0:
            passed = total_gov - policy_violation_count
            governance_pass_rate = round((passed / total_gov) * 100.0, 1)

        # Get review queue size
        review_queue_size = Review.objects.filter(status="pending").count()

        return {
            "documents": {
                "total": total_documents,
                "total_chunks": total_chunks,
                "total_embeddings": total_embeddings,
            },
            "conversations": {
                "total": conversations,
                "average_latency": round(avg_latency, 4),
                "average_confidence": round(avg_confidence, 2),
            },
            "governance": {
                "hallucination_count": hallucination_count,
                "policy_violations": policy_violation_count,
                "human_reviews": human_review_count,
                "pass_rate": governance_pass_rate,
                "review_queue_size": review_queue_size,
            },
            "providers": provider_usage,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def get_analytics() -> dict[str, Any]:
        """Return detailed analytics data for charts."""
        audit_events = AuditService.get_all_events()
        governance_events = [e for e in audit_events if e.get("event_type") == "governance_pipeline_completed"]

        # Conversation volume over time (by hour)
        volume_by_hour: dict[str, int] = {}
        for event in governance_events:
            ts = event.get("timestamp", "")
            hour_key = ts[:13] if len(ts) >= 13 else "unknown"
            volume_by_hour[hour_key] = volume_by_hour.get(hour_key, 0) + 1

        # Provider usage breakdown
        provider_usage: dict[str, int] = {}
        for event in governance_events:
            provider = event.get("details", {}).get("provider", "unknown")
            provider_usage[provider] = provider_usage.get(provider, 0) + 1

        # Confidence distribution
        confidence_buckets = {
            "very_low": 0,
            "low": 0,
            "medium": 0,
            "high": 0,
            "very_high": 0,
        }
        for event in governance_events:
            conf = event.get("details", {}).get("confidence_percentage", 0) or 0
            if conf >= 90:
                confidence_buckets["very_high"] += 1
            elif conf >= 70:
                confidence_buckets["high"] += 1
            elif conf >= 50:
                confidence_buckets["medium"] += 1
            elif conf >= 30:
                confidence_buckets["low"] += 1
            else:
                confidence_buckets["very_low"] += 1

        # Governance outcomes
        governance_outcomes = {
            "passed": 0,
            "policy_violations": 0,
            "toxicity_flagged": 0,
            "bias_flagged": 0,
            "hallucination_flagged": 0,
        }
        for event in governance_events:
            details = event.get("details", {})
            if details.get("policy_compliant") is False:
                governance_outcomes["policy_violations"] += 1
            else:
                governance_outcomes["passed"] += 1
            if (details.get("toxicity_score") or 0) > 0.5:
                governance_outcomes["toxicity_flagged"] += 1
            if (details.get("hallucination_score") or 0) > 0.5:
                governance_outcomes["hallucination_flagged"] += 1

        # Latency trend (last 20 events)
        latency_trend = []
        for event in governance_events[-20:]:
            latency_trend.append({
                "timestamp": event.get("timestamp", ""),
                "latency": event.get("details", {}).get("latency", 0.0),
            })

        # Policy violations breakdown
        policy_violations = []
        for event in governance_events:
            details = event.get("details", {})
            if details.get("policy_compliant") is False:
                policy_violations.append({
                    "timestamp": event.get("timestamp", ""),
                    "question": (details.get("question") or "")[:100],
                    "provider": details.get("provider", "unknown"),
                })

        return {
            "conversation_volume": [
                {"hour": k, "count": v}
                for k, v in sorted(volume_by_hour.items())
            ],
            "provider_usage": [
                {"provider": k, "count": v}
                for k, v in sorted(provider_usage.items(), key=lambda x: x[1], reverse=True)
            ],
            "confidence_distribution": confidence_buckets,
            "governance_outcomes": governance_outcomes,
            "latency_trend": latency_trend,
            "policy_violations": policy_violations[:50],
            "total_events": len(governance_events),
        }