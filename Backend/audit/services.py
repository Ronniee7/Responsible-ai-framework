from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class AuditService:
    """Record lightweight audit events for the research platform."""

    @staticmethod
    def log_event(event_type: str, details: dict[str, Any]) -> dict[str, Any]:
        """Create a structured audit entry."""
        return {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details,
        }
