# MCP (Model Context Protocol)

## What we built

Two MCP servers, each a standalone process speaking MCP over stdio, launched
and supervised by the FastAPI app's lifespan:

- **Travel MCP** (`mcp_servers/travel_mcp/server.py`) — `get_destination_info`
  (curated static data) and `search_places` (real OpenStreetMap Nominatim
  lookup, free, no API key).
- **Safety MCP** (`mcp_servers/safety_mcp/server.py`) — `get_emergency_info`,
  a deterministic lookup over a hard-coded dict of India emergency numbers.

Both use the official Python SDK's `MCPServer` (`mcp.server.MCPServer` —
the high-level server class; this SDK went through a naming change from the
earlier `FastMCP`, worth knowing if you see `FastMCP` in older tutorials),
which handles JSON-RPC framing, tool registration (via the `@mcp.tool()`
decorator and function type hints → input schema), and the stdio transport
loop.

The agent process holds one `mcp.ClientSession` per server
(`app/agent/mcp_client.py`), created with `mcp.client.stdio.stdio_client`,
which spawns the server as a subprocess and connects its stdin/stdout as the
transport. At startup, `list_tools()` discovers each tool's name,
description, and JSON Schema — that's what gets rendered into the system
prompt and used to validate arguments later.

## Client/server relationship

```
Agent process (FastAPI + orchestrator)
  │
  ├── ClientSession ──stdio──> Travel MCP server subprocess
  └── ClientSession ──stdio──> Safety MCP server subprocess
```

Each session is a separate subprocess and a separate protocol connection.
The agent doesn't import travel or safety code — it only knows tool names,
schemas, and how to call them. If either server crashed and was rewritten in
a different language tomorrow, nothing in `app/` would need to change.

## Tools, resources, prompts

Only **tools** are used so far (both servers expose functions the model can
invoke). MCP also defines **resources** (addressable, read-only content the
client can fetch without a tool call — e.g. a static "India safety basics"
document) and **prompts** (server-defined prompt templates). Neither is used
yet because nothing in the current scope needs them: there's no read-only
content large enough to warrant a resource instead of a tool call, and no
reusable prompt template shared across clients. Worth revisiting once
Memory MCP exists (traveller profile as a resource is a natural fit).

## Why MCP here and not a normal REST endpoint

The honest answer: at this scale, a REST endpoint would work almost as
well. MCP earns its place for three reasons specific to this project:

1. **Uniform tool contract.** The orchestrator's loop doesn't special-case
   "travel" vs "safety" tools — it discovers a flat list of
   `{name, description, input_schema}` from whichever servers are
   registered. Adding a third MCP server means no changes to
   `orchestrator.py` at all.
2. **Process isolation on a meaningful boundary.** Safety data (must never
   be LLM-invented) and travel data (looser, more exploratory) are different
   trust domains. Separate processes make that boundary structural, not just
   a code convention.
3. **The explicit learning goal.** This project exists partly to learn MCP
   properly — tool discovery, schema-driven validation, the stdio transport
   — which a bespoke REST client would teach differently (and the point was
   to learn *this* protocol).

What would tip it back to a plain REST/internal call: if a "tool" needs to
share a request-scoped resource with the agent process (e.g. a DB
transaction) — MCP's process boundary makes that awkward. That's part of why
Memory MCP (which will touch Postgres) needs more thought before it's built.

## Security implications

- **stdio, not network** — the current servers are subprocesses of the
  agent, not network services. No auth is needed today because there's no
  network boundary to cross. This stops being true the moment either server
  moves to a different host or is shared across multiple agent instances —
  at that point it needs real transport-level auth (MCP supports this over
  HTTP+SSE transports), not just "trust the subprocess."
- **Tool arguments are untrusted input from the model**, which is itself
  responding to untrusted input from the user. Every tool call's arguments
  are validated against the tool's declared JSON schema
  (`app/agent/guardrails.py::validate_tool_arguments`) before execution —
  this is the actual authorization boundary today, not the transport.
- **`search_places` makes an outbound HTTP call** built from a
  model-influenced query string. It's a read-only GET against a public
  geocoding API with no credentials attached, so the blast radius of a
  malicious query is low (worst case: a weird search string sent to
  Nominatim). A tool that could write data or spend money would need
  stricter argument constraints than a JSON-schema type check.
- **No tool-level authorization yet** — any discovered tool is callable by
  any request. Fine with two low-risk servers; would need a policy layer
  (which caller can invoke which tool) before adding anything that mutates
  state or costs money.
