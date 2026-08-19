# Guardrails

None of these make the system "safe" in an absolute sense — they narrow
specific, known failure modes. Each entry below says what it catches and
what it doesn't.

| Guardrail | Where | Protects against | Limitation |
|---|---|---|---|
| Message length/emptiness check | `guardrails.validate_user_message` | Empty requests, oversized payloads wasting LLM budget | Not a content filter — long-but-valid abuse still gets through |
| Prompt-injection pattern match | `guardrails.looks_like_prompt_injection` | Common phrasings ("ignore previous instructions", "you are now...") | Regex/keyword heuristic — trivially bypassed by rephrasing, translation, or encoding. It *flags and logs*, it does not block the request. |
| Tool-argument schema validation | `guardrails.validate_tool_arguments` via `jsonschema` | Malformed or type-mismatched tool arguments (from a non-compliant or hallucinating model) reaching a tool | Only checks shape/type, not semantic correctness (e.g. a syntactically valid but nonsense destination string still passes) |
| Tool-call iteration cap | `orchestrator.AgentOrchestrator` (`MAX_TOOL_ITERATIONS`) | Runaway tool-calling loops burning LLM calls/cost on one request | Fixed per-request cap, not a cost budget across requests |
| Deterministic safety disclaimer | `orchestrator.handle_message` | The LLM asserting or implying an absolute safety claim without a matching, code-attached caveat | The disclaimer is always the same fixed text — it doesn't verify the LLM's answer *content* was appropriately hedged, only that the caveat is present |
| No LLM-authored emergency data | `mcp_servers/safety_mcp/data.py` | The model inventing emergency phone numbers | Only covers the specific facts hard-coded here (national numbers); anything the model says beyond that dict is still ungrounded |
| Rate limiting | `core/middleware.enforce_rate_limit` | A single client hammering the (paid-adjacent, quota-limited) LLM API | In-memory, single-process — resets on restart, doesn't hold across multiple app instances |
| API key check | `core/middleware.require_api_key` | Anonymous access once a real key is configured | One shared key, not per-user identity or scoped permissions |
| Graceful LLM/tool failure handling | `orchestrator.handle_message`, `mcp_client.call_tool`, `app/rag/tools.py`, `app/memory/tools.py` | A downstream failure (HF API down, MCP tool crash, Postgres unreachable) turning into a 500 | Degrades to an apologetic text reply — doesn't retry indefinitely, doesn't distinguish "try again" from "this will keep failing" for the user |
| RAG distance threshold | `app/rag/store.py::DISTANCE_THRESHOLD` | The agent presenting a weakly-related knowledge chunk as if it answered the question | A fixed heuristic cutoff, not a calibrated confidence score — could still pass a mediocre match or drop a good one worded unusually |
| DB connect timeout | `app/rag/store.py::_connect`, `app/memory/store.py::_connect` (`connect_timeout=5`) | A request hanging indefinitely if Postgres is unreachable — libpq has no timeout by default | Only covers the connection phase; a slow query after connecting isn't bounded |
| session_id validation | `guardrails.validate_session_id` | Empty/oversized session identifiers reaching memory tools | Only checks shape (length, non-empty) — not ownership; anyone who has a session_id can read/write that session's memory |
| session_id injection, not LLM-supplied | `agent/tools.py::LocalToolRegistry.call` | A crafted tool call reading/writing another session's memory by passing a `session_id` argument | Memory is only as private as the session_id itself — there's no user auth binding a session_id to a person yet |
| Deterministic emergency info on `/plan` | `app/api/routes_plan.py` | The model skipping `get_emergency_info` and a plan shipping without real emergency numbers — observed live, see `docs/decisions.md` | Only covers `/plan`; `/chat` still relies on the LLM choosing to call the tool |

## What's explicitly out of scope right now

- **Output content moderation** (hate speech, harassment detection on LLM
  output) — not implemented. Would sit as a post-processing check on
  `AgentResult.reply` before returning it.
- **PII detection/redaction in logs** — logs currently include a truncated
  message preview (`message_preview=clean_message[:80]`) only when
  injection is flagged. No structured PII scrubbing yet; see
  [decisions.md](decisions.md) for the privacy stance.
- **Semantic hallucination detection** — nothing currently checks whether a
  final answer's claims are actually grounded in tool output vs. invented.
  This is what the eval dataset's `hallucination` category is for
  (manual review, not automated) — see [evaluation.md](evaluation.md).
- **RAG content injection** — the knowledge base is hand-authored by us, not
  fetched from the open web, so it isn't currently a prompt-injection vector
  the way retrieved external content would be. This stops being true if the
  corpus is ever populated from untrusted external sources — at that point
  retrieved chunks need the same untrusted-input treatment as tool output.
