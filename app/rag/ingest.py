"""One-off ingestion: chunk docs in app/rag/knowledge/ and embed+store them
into Postgres/pgvector.

Usage: python -m app.rag.ingest
Requires the postgres service from docker-compose.yml running, and HF_TOKEN
set (embeddings use the same Hugging Face client as the chat model).
"""
from __future__ import annotations

from pathlib import Path

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector

from app.config import get_settings
from app.rag.embeddings import EMBEDDING_DIM, embed_text

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector({EMBEDDING_DIM}) NOT NULL
);
"""


def chunk_markdown(text: str) -> list[str]:
    """Paragraph-level chunks — matches the size of our curated docs.
    Not sentence- or token-aware; fine while chunks are single ideas."""
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def main() -> None:
    conn = psycopg.connect(get_settings().database_url, connect_timeout=5)
    with conn.cursor() as cur:
        cur.execute(SCHEMA)  # must create the `vector` extension before register_vector can look up its OID
    conn.commit()
    register_vector(conn)
    with conn, conn.cursor() as cur:
        cur.execute("DELETE FROM knowledge_chunks")  # full re-ingest each run, not incremental
        for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
            chunks = chunk_markdown(path.read_text(encoding="utf-8"))
            for chunk in chunks:
                embedding = Vector(embed_text(chunk))
                cur.execute(
                    "INSERT INTO knowledge_chunks (source, chunk_text, embedding) VALUES (%s, %s, %s)",
                    (path.stem, chunk, embedding),
                )
            print(f"ingested {len(chunks)} chunks from {path.name}")
    conn.close()


if __name__ == "__main__":
    main()
