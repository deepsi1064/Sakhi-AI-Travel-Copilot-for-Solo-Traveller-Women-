# Frontend

**What:** a small React (Vite, plain JS, no TypeScript/Redux/router) app in
`frontend/`. Five views over two backend endpoints (`POST /chat`,
`POST /plan`) — see [planning.md](planning.md) for why `/plan` exists.

**Why:** the backend was only reachable via curl or as one plain chat
screen. This gives it a product shape (landing page, focused sections)
without adding backend surface beyond the one endpoint `/plan` needed.

## Structure

```
src/
  api.js            fetch wrappers for POST /chat and POST /plan
  session.js        session_id in localStorage           (unchanged)
  useChatThread.js  shared send/loading/error state, used by 3 views
  suggestions.js    destination/topic chip data, hand-kept in sync with backend content
  components/
    Message.jsx         one chat bubble (unchanged)
    SuggestionChips.jsx  clickable chip row
    NavBar.jsx           top nav / mobile bottom tab bar
  views/
    HomeView.jsx     landing page — branding + "Plan my trip" CTA + free-text ask
    PlanView.jsx      structured trip planner → POST /plan
    ProfileView.jsx   structured preference form → Memory, via /chat
    SafetyView.jsx   Safety MCP / RAG, as a focused Q&A
    ChatView.jsx     general-purpose chat (the original single screen)
```

`App.jsx` holds an `activeView` string and a `visitedViews` set. A view
mounts once, the first time its tab is opened, then stays mounted
(`display: none` when inactive) — so each view's own `useState` (chat
history, fetched summary, generated plans) survives switching tabs, without
a shared store or router.

## Every view maps to an existing backend capability

| View | Calls | Backend capability exercised |
|---|---|---|
| Home | — (routes to Plan or Chat) | none directly |
| Plan | `POST /plan` with structured fields | Orchestrator (Travel MCP, RAG, Memory) + deterministic Safety MCP call — see `planning.md` |
| Profile | `POST /chat`, one message per filled field, then a recall prompt | Memory's `remember_preference` / `recall_traveller_context` |
| Safety | `POST /chat` with a fixed safety prompt, then free text | Safety MCP's `get_emergency_info`, RAG's safety content |
| Chat | `POST /chat`, free text | Travel MCP, Safety MCP, RAG, Memory — LLM's choice |

**Why Profile sends one message per field, not one blob:** the agent's
tool-call budget per request is small; one clean sentence per field maps
reliably to one `remember_preference` call, instead of hoping the model
extracts and saves several preferences from one paragraph within budget.

**Why Plan is a dedicated endpoint but Profile/Safety are still just
`/chat`:** only Plan has a hard requirement (emergency info must always be
present) that free-text `/chat` structurally cannot guarantee — see
`planning.md`. Profile and Safety don't need that guarantee, so they stay
on the endpoint that already existed rather than getting one each.

**Known consequence, still true here:** tool use is the LLM's decision
except where explicitly bypassed (Plan's emergency info). If the model
skips a tool on `/chat`-backed views, the view still shows *a* reasonable
answer, just not provably grounded that turn — see `docs/decisions.md` for
a live-observed case.

## Session handling (unchanged)

`src/session.js` generates one `crypto.randomUUID()` per browser, kept in
`localStorage`. Every view uses the *same* `session_id` — a preference
saved via Profile is visible to Plan's "check my saved preferences" step
and vice versa, because they're the same Memory session server-side.

## Error handling (unchanged)

`src/api.js` distinguishes network failure from a non-2xx response (reads
FastAPI's `{"detail": "..."}` and shows that exact message). `planTrip`
mirrors `sendChatMessage`'s handling exactly, so Plan's errors behave the
same as every other view's.

## What's NOT built

No streaming. No chat/plan history persistence across browsers/devices
(only `session_id` round-trips; a generated plan is React state until
explicitly saved as a Memory note via "Save this trip"). No auth UI. No
plan editing — regenerate instead.
