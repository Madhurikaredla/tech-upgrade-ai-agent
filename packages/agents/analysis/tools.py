from typing import Any

import logfire
from pydantic_ai import RunContext


async def validate_data(ctx: RunContext[None], data: str) -> dict[str, Any]:
    """Validate input data structure and report any issues."""
    with logfire.span("tool.validate_data"):
        issues: list[str] = []

        if len(data) < 10:
            issues.append("Data too short for meaningful analysis")
        if len(data) > 50_000:
            issues.append("Data exceeds recommended size limit")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "length": len(data),
            "word_count": len(data.split()),
        }


async def extract_entities(ctx: RunContext[None], text: str) -> dict[str, list[str]]:
    """Extract named entities and high-signal keywords from text."""
    with logfire.span("tool.extract_entities"):
        words = text.split()
        entities = list({w.strip(".,;:!?") for w in words if len(w) > 3 and w[0].isupper()})[:20]
        keywords = [w.lower() for w in words if len(w) > 5][:10]
        return {"entities": entities, "keywords": keywords}


async def enrich_context(ctx: RunContext[None], payload_id: str) -> dict[str, Any]:
    """Fetch supplementary context for a payload."""
    with logfire.span("tool.enrich_context", payload_id=payload_id):
        return {
            "payload_id": payload_id,
            "enriched": True,
            "tags": [],
            "priority": "normal",
        }


async def calculate_risk_score(ctx: RunContext[None], factors: str) -> dict[str, Any]:
    """Calculate a composite risk score from a comma-separated factor list."""
    with logfire.span("tool.calculate_risk_score"):
        factor_list = [f.strip() for f in factors.split(",") if f.strip()]
        score = min(len(factor_list) * 25, 100)
        level = "low" if score < 25 else "medium" if score < 50 else "high" if score < 75 else "critical"
        return {"score": score, "level": level, "factors": factor_list}
