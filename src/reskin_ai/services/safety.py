from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SafetyCheckResult:
    blocked: bool
    rule_id: str | None = None
    reason: str | None = None


class SafetyEngine:
    """Simple keyword-based safety engine for MVP baseline."""

    banned_terms = {
        "self-harm": "RULE_SELF_HARM",
        "kill myself": "RULE_SELF_HARM",
        "hate symbol": "RULE_HATE",
        "racial slur": "RULE_HATE",
        "extreme violence": "RULE_VIOLENCE",
    }

    def evaluate(self, text: str) -> SafetyCheckResult:
        normalized = text.lower()
        for term, rule_id in self.banned_terms.items():
            if term in normalized:
                return SafetyCheckResult(
                    blocked=True,
                    rule_id=rule_id,
                    reason=f"Blocked unsafe content term: {term}",
                )
        return SafetyCheckResult(blocked=False)

