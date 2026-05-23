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
