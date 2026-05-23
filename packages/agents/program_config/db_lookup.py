"""Direct DB lookups for small, stable reference data.

Queries the shared Postgres DB instead of round-tripping through NestJS.
Results are cached in-process since program types / workflows never change mid-session.
"""

from __future__ import annotations

from typing import Any

import logfire
from sqlalchemy import text

from packages.db.database import engine

_cache: dict[str, tuple[int | None, int | None]] = {}

# ---------------------------------------------------------------------------
# program_type_v1 lookup
# ---------------------------------------------------------------------------

_type_config_cache: dict[str, dict[str, Any] | None] = {}

_ADMIN_TYPE_TO_DB_KEY: dict[str, str] = {
    "HDB": "PT_HDBMSD",
    "TAT": "PT_TAT",
    "ENT": "PT_ENTRAINMENT",
    "CUSTOM": "CUSTOM",
}

_NORMALIZE_MAP: dict[str, str] = {
    "HDB": "HDB", "PST_HDB": "HDB", "HDBMSD": "HDB", "PT_HDBMSD": "HDB",
    "TAT": "TAT", "PST_TAT": "TAT", "PT_TAT": "TAT",
    "ENT": "ENT", "PST_ENTRAINMENT": "ENT", "ENTRAINMENT": "ENT", "PT_ENTRAINMENT": "ENT",
    "CUSTOM": "CUSTOM",
}


def normalize_admin_type(raw: str | None) -> str:
    """Map any agent-extracted sub_program_type variant to the canonical admin key.

    Returns one of: HDB / TAT / ENT / CUSTOM.
    """
    if not raw:
        return "CUSTOM"
    return _NORMALIZE_MAP.get(raw.upper(), "CUSTOM")


async def get_program_type_config(admin_type: str) -> dict[str, Any] | None:
    """Fetch the program_type_v1 row for the given admin type key.

    admin_type should be one of: HDB, TAT, ENT, CUSTOM (call normalize_admin_type first).
    Returns the full row as a plain dict, or None if not found / on DB error.
    Results are cached for the lifetime of the process.
    """
    key = normalize_admin_type(admin_type)

    if key in _type_config_cache:
        return _type_config_cache[key]

    db_key = _ADMIN_TYPE_TO_DB_KEY.get(key, "CUSTOM")

    try:
        with logfire.span("db.get_program_type_config", admin_type=key, db_key=db_key):
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT id, key, name, description, "
                        "mode_of_operation, online_type, "
                        "has_multiple_sessions, is_grouped_program, "
                        "requires_residence, involves_travel, "
                        "has_checkin_checkout, requires_payment, "
                        "requires_approval, waitlist_applicable, "
                        "limited_seats, no_of_session, sub_program_type, "
                        "email_sender_name, venue, max_capacity "
                        "FROM program_type_v1 "
                        "WHERE key = :db_key "
                        "LIMIT 1"
                    ),
                    {"db_key": db_key},
                )
                row = result.fetchone()

        if row:
            config: dict[str, Any] = dict(row._mapping)
            logfire.info(
                "program_type_config.loaded",
                admin_type=key,
                db_key=db_key,
                type_id=config.get("id"),
            )
            _type_config_cache[key] = config
            return config

        logfire.warning("program_type_config.not_found", admin_type=key, db_key=db_key)
        _type_config_cache[key] = None
        return None

    except Exception:
        logfire.exception("db.get_program_type_config failed", admin_type=key)
        return None


async def get_type_and_workflow(sub_program_type: str | None) -> tuple[int | None, int | None]:
    """Return (type_id, workflow_id) for the given program sub-type.

    Looks up workflow_configuration by program_type_key ILIKE, picks newest row.
    Falls back to (None, None) and logs a warning if nothing matches.
    """
    key = (sub_program_type or "CUSTOM").upper()

    if key in _cache:
        return _cache[key]

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
