-- Agent session and message history tables for the Program Configuration Agent.
-- Run this once against your PostgreSQL database before starting the agent service.

CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id          VARCHAR(64)  PRIMARY KEY,
    user_id             VARCHAR(64)  NOT NULL DEFAULT '',
    stage               VARCHAR(32)  NOT NULL DEFAULT 'COLLECTING',
    partial_dto         TEXT         NOT NULL DEFAULT '{}',
    program_id          INTEGER,
    template_questions  TEXT         NOT NULL DEFAULT '[]',
    display_messages    TEXT         NOT NULL DEFAULT '[]',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- One row per session — stores the full serialised pydantic-ai message list.
CREATE TABLE IF NOT EXISTS agent_message_history (
    session_id  VARCHAR(64)  PRIMARY KEY REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    messages    TEXT         NOT NULL DEFAULT '[]',
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id
    ON agent_sessions (user_id);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_updated_at
    ON agent_sessions (updated_at DESC);

-- Migration: add display_messages to existing installations
ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS display_messages TEXT NOT NULL DEFAULT '[]';

-- Migration: add state_json — full SessionState snapshot, source of truth for all fields.
-- The individual columns (stage, program_id, user_id) are kept for indexing/listing only.
ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS state_json TEXT NOT NULL DEFAULT '{}';
