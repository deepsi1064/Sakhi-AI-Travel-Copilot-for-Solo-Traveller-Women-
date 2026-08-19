# Decisions

Log of the non-obvious architectural choices, in the order they came up.
Newest at the bottom.

## Hugging Face instead of Claude/OpenAI for the LLM

**Why:** explicit cost constraint — this project needs to run at zero
ongoing cost. HF's free inference tier covers it; Anthropic/OpenAI don't
have a comparable free tier for sustained use.

**Tradeoff accepted:** no native tool-calling API, so the agent implements
its own JSON-based tool-call contract and parser (see
[agent-architecture.md](agent-architecture.md)). Also: free-tier open models
are less reliable at instruction-following than Claude/GPT, so the
orchestrator has to tolerate malformed tool-call attempts gracefully rather
than assume compliance.

**Revisit if:** budget becomes available and reliability of tool-call
formatting becomes the limiting factor on quality.

## Manual tool-calling loop instead of LangChain/LangGraph

**Why:** the project's explicit purpose is learning what agent orchestration
actually does. A framework's tool-calling abstraction would hide exactly the
mechanism this project exists to teach. The loop is ~100 lines and fits in
one file (`app/agent/orchestrator.py`).

**Revisit if:** orchestration complexity grows past what a hand-rolled loop
handles cleanly (e.g. parallel tool calls, sub-agents, complex branching) —
at that point a framework's value proposition changes from "hides
mechanism" to "handles genuine complexity," and it's worth re-evaluating.

## MCP over stdio, two servers (Travel, Safety), not more

**Why:** stdio needs no network setup, no auth layer, and no extra
infrastructure — appropriate while everything runs on one machine. Two
servers because Travel and Safety are genuinely different trust domains
(exploratory vs. must-never-be-invented). RAG and Memory turned out not to
need a third or fourth server at all — see below.
Full reasoning: [mcp.md](mcp.md).

## Static curated data for `get_destination_info`, real API for `search_places`

**Why:** there's no free, reliable API for the specific thing
`get_destination_info` returns (solo-traveller-relevant context, "traveller
notes") — that's inherently curated/editorial content, not something a geo
API provides. `search_places`, by contrast, is exactly what a geocoding API
is for, so it calls OpenStreetMap's Nominatim (free, no key, per their usage
policy) instead of also being mocked.

**Limitation flagged in the code and to the user:** the curated dataset is
five example destinations, explicitly labeled as unverified/community-sourced
in the tool's own output — not a claim of completeness or accuracy.

## Emergency numbers hard-coded, not looked up

**Why:** this is the clearest instance of the project's stated safety
philosophy — prefer deterministic logic over LLM inference wherever
possible, especially for facts where being wrong is dangerous. India's
national emergency numbers (112, 100, 1091, 108, 1363) don't vary by
location, so a static dict is both correct and simpler than a lookup.

**Revisit if:** state-specific helplines are added — at that point this
needs a real data source, not a hand-maintained dict.

## In-memory rate limiting and single shared API key

**Why:** appropriate for a single-instance local deployment, which is all
that exists right now. Called out explicitly as a placeholder in
[guardrails.md](guardrails.md) rather than presented as a finished feature.

**Revisit if:** the app runs as more than one process/instance (rate limiter
breaks — needs Redis), or real user accounts are introduced (shared key
stops making sense — needs per-user auth).

## Privacy stance

The only thing logged from user input is an 80-character preview, and only
when a message is flagged as a possible prompt injection — logging exists
to help debug the guardrail, not to build a record of user messages. Memory
(`app/memory/`) now persists data, deliberately narrow: preferences and
saved places the agent chose to remember, keyed by `session_id`, nothing
else — not a conversation log. See [memory.md](memory.md) for what's stored
and its limitations (no expiry/deletion tool yet, no confirmation step
before writing).

## Flat repo layout (`app/`, `mcp_servers/` at root, not nested under `backend/`)

**Why:** avoids import-path friction between the FastAPI app and the MCP
servers it subprocess-launches (`python -m mcp_servers.travel_mcp.server`
needs to resolve cleanly from the repo root either way). No `backend/`
nesting since there's no other backend-adjacent service yet to distinguish
it from.

## RAG as a local tool, not a third MCP server

**Why:** `retrieve_travel_knowledge` needs a live Postgres connection
scoped to the agent process — there's no external system boundary to put
behind MCP, so a third server would only exist to inflate the MCP count.
Full reasoning: [rag.md](rag.md).

**Consequence:** the orchestrator now has two tool sources (MCP + local).
Rather than special-case RAG, added a small `LocalToolRegistry`
(`app/agent/tools.py`, ~35 lines) that MCP and local tools both satisfy the
same `{name, description, input_schema}` contract against. Justified now
because Memory (next capability) will also need this, not hypothetically.

## Embeddings via Hugging Face feature-extraction, not local sentence-transformers

**Why:** avoids adding `torch`/`sentence-transformers` as dependencies for
a project already using HF for chat completions — same provider, same
free-tier tradeoff (network call per embed, subject to availability), one
fewer thing to install.

**Revisit if:** embedding latency/availability becomes a bottleneck —
local embedding is the obvious swap, isolated to `app/rag/embeddings.py`.

## Redis removed from docker-compose

**Why:** nothing used it. It was provisioned speculatively in phase 1;
removed on audit rather than left as unused infrastructure. Rate limiting
stays in-memory, which is correct for a single-instance deployment (see
above). Add it back only when something concrete needs it (e.g. rate
limiting across multiple instances).

## Memory as a local tool, with session_id injected not LLM-supplied

**Why:** same "no external boundary" reasoning as RAG, plus a security
reason specific to Memory: whose data a tool call touches must come from
the trusted request, not from the LLM's own JSON output. `LocalTool` grew
a `needs_session` flag; `LocalToolRegistry.call` strips any `session_id`
the LLM might include in tool arguments and injects the real one itself.
Full reasoning: [memory.md](memory.md).

**Consequence:** `AgentOrchestrator.handle_message` now takes a
`session_id` parameter, threaded from `ChatRequest.session_id` through
`routes_chat.py`. Reused the existing `LocalToolRegistry` from RAG rather
than building a separate mechanism — this is the payoff of that earlier
decision.

## RAG and Memory tool-wiring moved out of main.py

**Why:** `main.py` was accumulating both domains' tool-building logic
directly in the FastAPI lifespan function. Moved to
`app/rag/tools.py::build_rag_tools()` and
`app/memory/tools.py::build_memory_tools()`; `main.py` just aggregates them
into one registry. Small, mechanical refactor — justified once there were
two domains showing the same pattern, not preemptively.

## Model sometimes fabricates a tool result instead of calling the real tool

**Found:** live-testing the Safety view, the model's reply began with
`"Tool result for retrieve_travel_knowledge: ..."` — imitating the
orchestrator's own internal `f"Tool result for {name}: ..."` framing —
while `tool_calls` showed only `get_emergency_info` was actually invoked
that turn. The model generated a second, fake "tool result" instead of a
real call.

**Why it matters:** confirms tool invocation is never a hard guarantee, only
a likelihood — directly informed the `/plan` endpoint's design (see
[planning.md](planning.md)): safety-critical deterministic data can't
depend on the LLM choosing to fetch it.

**Not fixed:** would require changing how tool results are framed in the
message history (e.g. a distinct role instead of reusing "user"), which
touches the core loop broadly. Left as a documented limitation.

## POST /plan: one new endpoint, not a change to /chat

**Why:** `/plan`'s job includes a hard requirement — emergency info must
always be present, never dependent on the LLM's tool choice (see the
fabrication case above). `/chat`'s free-text contract has no way to express
that guarantee. Rather than bolt a special case onto `/chat` for messages
that "look like" planning requests (fragile, and would change existing
`/chat` behavior for everyone), added one small, separate route that:
reuses `AgentOrchestrator` and `McpClientManager` entirely as-is, adds one
direct (non-LLM-mediated) call to Safety MCP's `get_emergency_info`, and
one pure prompt-building function (`app/agent/plan_prompt.py`). `/chat`'s
contract and behavior are unchanged. Full reasoning: [planning.md](planning.md).

**Consequence:** `AgentOrchestrator.handle_message` gained an optional
`max_iterations` parameter (default unchanged, only `/plan` overrides it) —
planning plausibly needs one more tool-call round (Memory + Travel MCP +
RAG) than casual chat in a single turn.
