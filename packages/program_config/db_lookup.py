"""Direct DB lookups for small, stable reference data.

Queries the shared Postgres DB instead of round-tripping through the NestJS
backend. Results are cached in-process since program types and workflows never
change mid-session.
"""

from __future__ import annotations

import logfire
from sqlalchemy import text

from packages.db.database import engine

# In-process cache: sub_program_type key → (type_id, workflow_id)
_cache: dict[str, tuple[int | None, int | None]] = {}


async def get_type_and_workflow(sub_program_type: str | None) -> tuple[int | None, int | None]:
    """Return (type_id, workflow_id) for the given program sub-type.

    Looks up workflow_configuration by matching program_type_key ILIKE '%<key>%'
    and picks the row with the highest id (most recently created workflow).
    Falls back to (None, None) and logs a warning if nothing matches.
    """
    key = (sub_program_type or "CUSTOM").upper()

    if key in _cache:
        return _cache[key]

    # Derive the search pattern — HDBMSD covers both "HDB" and "MSD" sub-types
    pattern_map = {
        "HDB": "%HDBMSD%",
        "MSD": "%HDBMSD%",
        "TAT": "%TAT%",
        "ENT": "%ENTRAINMENT%",
        "CUSTOM": "CUSTOM",
    }
    pattern = pattern_map.get(key, f"%{key}%")

    try:
        with logfire.span("db.lookup_program_type", sub_type=key, pattern=pattern):
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT program_type_id, id "
                        "FROM workflow_configuration "
                        "WHERE program_type_key ILIKE :pattern "
                        "  AND deleted_at IS NULL "
                        "ORDER BY id DESC "
                        "LIMIT 1"
                    ),
                    {"pattern": pattern},
                )
                row = result.fetchone()

        if row:
            type_id, workflow_id = int(row[0]), int(row[1])
            logfire.info(
                "resolved program type from DB",
                sub_type=key,
                type_id=type_id,
                workflow_id=workflow_id,
            )
            _cache[key] = (type_id, workflow_id)
            return type_id, workflow_id

        logfire.warning("no workflow found for program type", sub_type=key, pattern=pattern)
        _cache[key] = (None, None)
        return None, None

    except Exception:
        logfire.exception("db.lookup_program_type failed", sub_type=key)
        return None, None
