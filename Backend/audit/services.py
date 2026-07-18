from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any


class AuditService:
    """Record audit events with persistence for the governance pipeline."""

    _audit_log: list[dict[str, Any]] = []

    @classmethod
    def log_event(cls, event_type: str, details: dict[str, Any]) -> dict[str, Any]:
        """Create a structured audit entry and persist it."""
        entry = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details,
        }
        cls._audit_log.append(entry)

        # Also try to persist to a file for durability
        cls._persist_event(entry)

        return entry

    @classmethod
    def get_all_events(cls) -> list[dict[str, Any]]:
        """Return all recorded audit events."""
        return list(cls._audit_log)

    @classmethod
    def clear_events(cls) -> None:
        """Clear the in-memory audit log (useful for testing)."""
        cls._audit_log.clear()

    @classmethod
    def _persist_event(cls, entry: dict[str, Any]) -> None:
        """Attempt to persist audit events to disk."""
        try:
            log_dir = os.path.join(os.getcwd(), "audit_logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(
                log_dir,
                f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl",
            )
            with open(log_file, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")
        except Exception:
            pass  # Silent fallback - in-memory storage still works