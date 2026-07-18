from __future__ import annotations

import re
from typing import Any

# Configurable policy rules
# Each rule has: id, pattern, description, severity, action
POLICY_RULES: list[dict[str, Any]] = [
    {
        "id": "POLICY-001",
        "name": "never_reveal_passwords",
        "description": "Never reveal passwords, credentials, secrets, or tokens.",
        "severity": "critical",
        "action": "block_and_alert",
        "patterns": [
            r"\b(?:password|passwd|pwd)\s+(?:is|:|=)\s+\S+",
            r"\b(?:here\s+(?:is|are|'s)\s+(?:your\s+)?(?:password|credential))\b",
            r"\b(?:login|log\s*in)\s+(?:credential|detail|info)\b",
            r"\b(?:api[_-]?key|secret[_-]?key|access[_-]?key)\s+(?:is|:|=)\s+\S+",
            r"\b(?:token|auth[_-]?token|bearer)\s+(?:is|:|=)\s+\S+",
        ],
    },
    {
        "id": "POLICY-002",
        "name": "never_expose_personal_information",
        "description": "Never expose personal information (PII) such as SSN, addresses, phone numbers, emails.",
        "severity": "critical",
        "action": "block_and_alert",
        "patterns": [
            r"\b\d{3}[-]\d{2}[-]\d{4}\b",  # SSN
            r"\b(?:ssn|social\s+security)\s+(?:number|#|no)\s+(?:is|:|=)\s+\S+",
            r"\b(?:email|e-mail)\s+(?:address|id)\s+(?:is|:|=)\s+\S+@\S+",
            r"\b(?:phone|mobile|cell|telephone)\s+(?:number|#|no)\s+(?:is|:|=)\s+\d+",
            r"\b(?:credit\s+card|cc)\s+(?:number|#|no)\s+(?:is|:|=)\s+\d{13,16}",
        ],
    },
    {
        "id": "POLICY-003",
        "name": "never_unsupported_legal_advice",
        "description": "Never provide unsupported legal advice or opinions that could be construed as legal counsel.",
        "severity": "high",
        "action": "flag_for_review",
        "patterns": [
            r"\byou\s+should\s+(?:sue|file|claim|settle|lawsuit)\b",
            r"\b(?:legal\s+advice|legal\s+counsel|legal\s+opinion)\b",
            r"\b(?:i\s+(?:am|'m)\s+(?:not\s+)?a\s+lawyer)\s+but\b",
            r"\b(?:this\s+is\s+(?:not\s+)?legal\s+advice)\b",
        ],
    },
    {
        "id": "POLICY-004",
        "name": "never_fabricate_company_policy",
        "description": "Never fabricate company policy statements that are not grounded in retrieved documents.",
        "severity": "high",
        "action": "flag_for_review",
        "patterns": [
            r"\b(?:our\s+policy|company\s+policy|corporate\s+policy)\s+(?:states|requires|mandates|prohibits)\b",
            r"\b(?:as\s+per\s+(?:our|company)\s+policy)\b",
            r"\b(?:policy\s+#\d+|policy\s+number)\b",
        ],
    },
    {
        "id": "POLICY-005",
        "name": "never_provide_medical_advice",
        "description": "Never provide medical advice, diagnoses, or treatment recommendations.",
        "severity": "high",
        "action": "flag_for_review",
        "patterns": [
            r"\byou\s+should\s+(?:take|use|try)\s+(?:\w+\s+)?(?:medication|medicine|drug|prescription)\b",
            r"\b(?:diagnos|diagnose|diagnosis|diagnosed)\s+(?:you|your)\b",
            r"\b(?:medical\s+(?:advice|opinion|treatment))\s+(?:is|:)\b",
            r"\b(?:i\s+(?:recommend|prescribe)\s+(?:you\s+)?(?:this\s+)?(?:medication|treatment))\b",
        ],
    },
    {
        "id": "POLICY-006",
        "name": "never_prompt_injection",
        "description": "Never respond to prompt injection or jailbreak attempts.",
        "severity": "critical",
        "action": "block_and_alert",
        "patterns": [
            r"\b(?:ignore|disregard)\s+(?:all\s+)?(?:previous|above)\s+(?:instructions|prompts|commands)\b",
            r"\b(?:ignore|disregard)\s+all\s+(?:previous\s+)?(?:instructions|prompts|commands)\b",
            r"\b(?:you\s+are\s+(?:now|free)\s+(?:to\s+)?(?:ignore|act))\b",
            r"\b(?:system\s+prompt|developer\s+mode|do\s+anything\s+now)\b",
            r"\b(?:pretend|act\s+as\s+if|roleplay)\s+(?:you\s+are|to\s+be)\b",
        ],
    },
]


class PolicyService:
    """Evaluate generated responses against configurable policy rules."""

    @staticmethod
    def evaluate(
        response_text: str,
        has_retrieved_context: bool = False,
    ) -> dict[str, Any]:
        """Check the response against all configured policy rules.

        Returns:
            policy_compliant: bool indicating overall compliance
            violations: list of policy violations with details
            recommended_action: suggested action based on violations
        """
        if not response_text:
            return {
                "policy_compliant": True,
                "violations": [],
                "recommended_action": "none",
            }

        response_lower = response_text.lower()
        violations: list[dict[str, Any]] = []
        highest_severity = "low"

        for rule in POLICY_RULES:
            for pattern in rule["patterns"]:
                if re.search(pattern, response_lower):
                    violation = {
                        "policy_id": rule["id"],
                        "policy_name": rule["name"],
                        "description": rule["description"],
                        "severity": rule["severity"],
                        "action": rule["action"],
                    }
                    violations.append(violation)

                    # Track highest severity
                    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
                    if severity_order.get(rule["severity"], 0) > severity_order.get(highest_severity, 0):
                        highest_severity = rule["severity"]

                    break  # One match per rule is sufficient

        policy_compliant = len(violations) == 0

        # Determine recommended action
        if not policy_compliant:
            if highest_severity in ("critical", "high"):
                recommended_action = "block_and_notify"
            elif any(v["action"] == "flag_for_review" for v in violations):
                recommended_action = "flag_for_review"
            else:
                recommended_action = "flag_for_review"
        else:
            recommended_action = "none"

        return {
            "policy_compliant": policy_compliant,
            "violations": violations,
            "recommended_action": recommended_action,
        }

    @staticmethod
    def get_all_rules() -> list[dict[str, Any]]:
        """Return all configured policy rules for diagnostic/display purposes."""
        return [
            {
                "id": rule["id"],
                "name": rule["name"],
                "description": rule["description"],
                "severity": rule["severity"],
                "action": rule["action"],
            }
            for rule in POLICY_RULES
        ]