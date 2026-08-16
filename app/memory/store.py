"""Session-scoped traveller memory: preferences and saved places.

Plain internal module, not MCP — same reasoning as RAG (docs/rag.md), plus
a stronger one here: session_id must come from the trusted request context,
never from LLM-generated tool arguments. Keeping this in-process avoids
having to design a way to authenticate that boundary over MCP. See
docs/memory.md.
"""
from __future__ import annotations

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS traveller_preferences (
    session_id TEXT PRIMARY KEY,
    preferences JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS saved_places (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    place TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def _connect() -> psycopg.Connection:
    # Schema is created on every connect (idempotent, cheap at this scale)
    # rather than needing a separate migration step like RAG's ingest script.
    conn = psycopg.connect(get_settings().database_url, row_factory=dict_row, connect_timeout=5)
    with conn.cursor() as cur:
        cur.execute(SCHEMA)
    conn.commit()
    return conn


def save_preference(session_id: str, key: str, value: str) -> None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO traveller_preferences (session_id, preferences, updated_at)
            VALUES (%s, %s, now())
            ON CONFLICT (session_id) DO UPDATE
            SET preferences = traveller_preferences.preferences || %s, updated_at = now()
            """,
            (session_id, Jsonb({key: value}), Jsonb({key: value})),
        )
        conn.commit()


def save_place(session_id: str, place: str, note: str) -> None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO saved_places (session_id, place, note) VALUES (%s, %s, %s)",
            (session_id, place, note or None),
        )
        conn.commit()


def get_context(session_id: str) -> dict:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT preferences FROM traveller_preferences WHERE session_id = %s", (session_id,))
        pref_row = cur.fetchone()
        preferences = pref_row["preferences"] if pref_row else {}

        cur.execute(
            "SELECT place, note FROM saved_places WHERE session_id = %s ORDER BY created_at DESC LIMIT 20",
            (session_id,),
        )
        places = cur.fetchall()
    return {"preferences": preferences, "saved_places": places}
