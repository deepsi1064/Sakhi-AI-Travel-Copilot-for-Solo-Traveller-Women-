# Trip Planning

**What:** `POST /plan` — structured trip details in, a personalized
itinerary out. The product-facing shape of "decision assistant," not a new
subsystem: it's the existing agent loop plus one deterministic addition.

**Why:** the original `/chat` is free text — good for Q&A, weak for "here
are my constraints, give me a plan," and structurally unable to *guarantee*
deterministic safety data was used (tool choice is always the LLM's
discretion on `/chat`). `/plan` fixes both without duplicating any existing
capability.

## How preferences reach Memory

`ProfileView` (frontend) collects budget, travel style, quiet-vs-crowded,
transport, avoid-list, typical duration as a structured form. On save, each
filled field becomes its own short sentence (e.g. *"My preferred
transportation is Train."*) sent as a separate `POST /chat` call, in
sequence. Each maps to one `remember_preference` call — this is why fields
are sent one at a time rather than as one blob: the agent's tool-call budget
per request is small (`MAX_TOOL_ITERATIONS`), and one clean sentence per
call is far more reliable than hoping the model extracts six preferences
from one paragraph and calls the tool six times. No backend change needed —
this is the same Memory tool `/chat` already exposed.

## How trip constraints reach the agent

`PlanView` collects destination, starting city, duration, budget, and
trip-specific preferences, then calls `POST /plan`. The route
(`app/api/routes_plan.py`) turns those fields into one instruction via
`app/agent/plan_prompt.py::build_plan_prompt` — a **pure, deterministic
function**, not an LLM call — then hands that prompt to the exact same
`AgentOrchestrator.handle_message` used by `/chat`. Nothing about the agent
loop, guardrails, or tool-calling changed.

## When Travel MCP / RAG / Safety MCP / Memory are used

All at the LLM's discretion, same as `/chat` — the prompt instructs it to
check saved preferences (Memory), and the itinerary naturally invites
`get_destination_info`/`search_places` (Travel MCP) and
`retrieve_travel_knowledge` (RAG). One exception, deliberate:

**Emergency numbers are never left to that discretion.** `routes_plan.py`
calls `mcp_manager.call_tool("get_emergency_info", ...)` **directly**,
bypassing the LLM entirely, and the result is always present in the
response (`emergency_info` field) regardless of what the model did. This
exists because live testing (see `docs/decisions.md`) proved the model
sometimes skips calling a real tool even when it's available and answers
from training data instead — fine for casual chat, not acceptable for a
feature whose explicit job is grounded safety information.

## Why one small API change (`POST /plan`) was necessary

`/chat`'s contract (free text in, one reply out) cannot express "always
attach real emergency data regardless of what the model decides." That
requires code between the agent's answer and the HTTP response — which
means a route, which means either changing `/chat`'s behavior for everyone
(rejected: unrelated behavior change to an existing, working feature) or a
new endpoint scoped to the one feature that needs the guarantee. `/plan` is
~40 lines, reuses `AgentOrchestrator` and `McpClientManager` as-is, adds one
new Pydantic request/response pair, and one pure prompt-building function.
No new services, servers, or database tables.

`AgentOrchestrator.handle_message` also gained two optional parameters,
both defaulting to `/chat`'s existing behavior when omitted:
`max_iterations` (`/plan` allows one more tool-call round than casual chat —
planning plausibly needs Memory + Travel MCP + RAG in one turn), and
`max_tokens` (`/plan` requests 900 vs. the default 512 — live testing showed
a day-by-day itinerary plus a safety section gets cut off mid-sentence at
the chat-sized default).

## Why this stays simple

- No new database table for "trips" — a generated plan lives in the
  browser's React state for that session. A "Save this trip" button reuses
  `remember_place` (existing Memory tool) to persist a short note, nothing more.
- No planning-specific prompt templates beyond one plain function.
- No second LLM, no separate "planning agent," no new MCP server.
- The deterministic safety guarantee is the *only* new backend behavior;
  everything else is existing capability, differently framed.
