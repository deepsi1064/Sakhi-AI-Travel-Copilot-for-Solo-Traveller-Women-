# RAG

**What:** retrieval over a small curated knowledge base — cultural norms,
common scams, general solo-safety habits. Distinct from MCP (live/external
data) and the planned Memory (per-traveller state): RAG is Sakhi's own
trusted, static knowledge.

**Why Sakhi needs it:** broad "what should I know" questions aren't
destination lookups or emergency numbers — they need general guidance that
doesn't belong in either MCP server. Retrieval keeps that guidance grounded
in text we actually wrote, instead of the LLM inventing it.

**How it works here:**
- `app/rag/knowledge/*.md` — curated source docs, paragraph-chunked
  (`app/rag/ingest.py::chunk_markdown`).
- Embeddings via Hugging Face's free `feature-extraction` endpoint
  (`sentence-transformers/all-MiniLM-L6-v2`) — same provider as the chat
  model, no local ML dependency.
- Stored in Postgres/pgvector (`knowledge_chunks` table);
  `app/rag/store.py::search` runs a cosine-distance `ORDER BY ... LIMIT k`
  query. No ANN index — the corpus is a few dozen chunks, doesn't need one.
- Exposed to the agent as `retrieve_travel_knowledge`, a **local tool**
  (`app/agent/tools.py`), through the same JSON tool-call loop as MCP
  tools — the LLM decides whether to call it, same as any other tool. No
  separate "RAG orchestration" step.
- `DISTANCE_THRESHOLD` drops weak matches, so a query outside the knowledge
  base gets "nothing relevant" back instead of a stretched, low-quality
  chunk the LLM might present as an answer anyway.

**Why not an MCP server:** this needs a live DB connection scoped to the
agent process, not an external system boundary — nothing here benefits
from process isolation, so a third MCP server would be MCP for its own
sake. Compare Travel/Safety MCP in `docs/mcp.md`.

**Limitation:** the knowledge base is a handful of hand-written files, not
a real content pipeline. "Nothing relevant" is a distance-threshold
heuristic, not a calibrated confidence score. Ingestion
(`python -m app.rag.ingest`) is a full re-embed each run, not incremental.
