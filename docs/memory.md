# Memory

**What:** session-scoped traveller state — preferences (e.g. dietary needs,
budget) and saved places. Distinct from RAG (static, shared, curated) and
MCP (live/external): Memory is per-traveller, mutable, and written by the
agent during the conversation, not pre-loaded.

**Why Sakhi needs it:** without it, every message starts from zero — the
agent can't personalize a plan around something the traveller already said
two turns ago ("I'm vegetarian", "I'm on a tight budget").

**How it works here:**
- Two small Postgres tables (`app/memory/store.py`): `traveller_preferences`
  (one JSONB row per session, merged on write) and `saved_places` (append-only).
  Schema is created on first connect — no separate migration step, unlike
  RAG's `ingest.py` (a deliberate simplification; would move to explicit
  migrations in a real deployment).
- Exposed as three **local tools** (`app/memory/tools.py`):
  `remember_preference`, `remember_place`, `recall_traveller_context`. Same
  `LocalToolRegistry` mechanism as RAG — the LLM decides when to use them.
- `session_id` comes from `ChatRequest.session_id` (`app/api/schemas.py`),
  validated (`guardrails.validate_session_id`) and passed through
  `orchestrator.handle_message` down to `LocalToolRegistry.call`, which
  injects it into the tool function directly.

**Why session_id is never an LLM tool argument (important):** memory tools
are marked `needs_session=True` and their JSON schemas don't declare a
`session_id` property. `LocalToolRegistry.call` strips any `session_id` key
an LLM tool-call might still include before invoking the function, then
injects the real one from the trusted request. If this weren't enforced,
a crafted tool call could read or write another session's memory — the LLM
output is not a trusted source for *whose* data to touch, only for *what*
to do with it.

**Why not an MCP server:** same reasoning as RAG (`docs/rag.md`) — no
external boundary — plus a security-shaped reason specific to Memory:
authenticating "which session does this MCP tool call belong to" over a
stdio/network transport is a harder problem than the in-process solution
above. Not worth solving until there's an actual reason to run Memory out
of process.

**Limitation:** no explicit user confirmation before something is
remembered — the agent decides. No expiry/deletion tool yet (data
minimization is enforced only by *what* gets written, not by cleanup). No
real user accounts — `session_id` is whatever the client sends, so it's
only as private as that identifier is kept.
