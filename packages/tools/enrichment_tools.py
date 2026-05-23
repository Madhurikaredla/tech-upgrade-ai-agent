from typing import Any

import logfire
from pydantic_ai import RunContext

from packages.models.output import RiskLevel

_RISK_KEYWORDS: dict[str, list[str]] = {
    "critical": ["password", "secret", "token", "key", "credential", "private_key"],
    "high": ["admin", "root", "sudo", "delete", "drop", "truncate"],
    "medium": ["update", "modify", "change", "alter", "patch"],
}

_RISK_WEIGHTS = {"critical": 40, "high": 20, "medium": 5}


async def enrich_context(
    ctx: RunContext[None],
    payload_id: str,
    metadata: dict[str, str],
) -> dict[str, Any]:
    """Attach environmental context to a payload."""
    with logfire.span("tool.enrich_context", payload_id=payload_id):
        return {
            "payload_id": payload_id,
            "has_metadata": bool(metadata),
            "metadata_keys": list(metadata.keys()),
            "source": metadata.get("source", "unknown"),
            "environment": metadata.get("environment", "production"),
        }


async def calculate_risk_score(
    ctx: RunContext[None],
    text: str,
    entities: list[str],
) -> dict[str, Any]:
    """Score content risk based on keyword signals."""
    with logfire.span("tool.calculate_risk_score"):
        text_lower = text.lower()
        score = 0
        matched: list[str] = []

        for level, keywords in _RISK_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    matched.append(kw)
                    score += _RISK_WEIGHTS[level]

        if score >= 40:
            level = RiskLevel.CRITICAL
        elif score >= 20:
            level = RiskLevel.HIGH
        elif score >= 5:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return {"score": score, "level": level, "matched_keywords": matched}
