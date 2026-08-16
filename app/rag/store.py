"""pgvector-backed retrieval over Sakhi's curated knowledge base.

Plain internal module, not an MCP server — see docs/rag.md for why.
Blocking (sync) DB and embedding calls, matching the rest of the agent's
call style (app/agent/llm_client.py is sync too); fine at this request
volume, would need an async driver under real concurrent load.
"""
from __future__ import annotations

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from app.config import get_settings
from app.rag.embeddings import embed_text

# Cosine distance cutoff (0 = identical, 2 = opposite). Chunks past this are
# dropped rather than returned as a weak, possibly-misleading match. A
# heuristic, not a calibrated confidence score — see docs/rag.md.
DISTANCE_THRESHOLD = 0.6


def _connect() -> psycopg.Connection:
    # Fail fast if Postgres is unreachable rather than hanging the request —
    # libpq has no connect timeout by default.
    conn = psycopg.connect(get_settings().database_url, row_factory=dict_row, connect_timeout=5)
    register_vector(conn)
    return conn


def search(query: str, top_k: int = 3) -> list[dict]:
    # Wrapped in pgvector's Vector type: register_vector only auto-adapts
    # Vector/numpy.ndarray, not a bare Python list (silently becomes a
    # plain array otherwise, and `<=>` has no vector/array overload).
    query_embedding = Vector(embed_text(query))
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT source, chunk_text, embedding <=> %s AS distance
            FROM knowledge_chunks
            ORDER BY distance
            LIMIT %s
            """,
            (query_embedding, top_k),
        )
        rows = cur.fetchall()
    return [row for row in rows if row["distance"] <= DISTANCE_THRESHOLD]
