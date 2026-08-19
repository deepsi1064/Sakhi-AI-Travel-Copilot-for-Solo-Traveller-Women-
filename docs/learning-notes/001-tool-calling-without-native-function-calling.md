# Learning note: tool calling without native function-calling support

**Concept:** getting an LLM to invoke external tools (functions/APIs) as
part of generating a response, and getting structured results back into its
context.

**Why it exists:** LLMs can't execute code or hit APIs themselves — tool
calling is the pattern that lets the model *request* an action (by name and
arguments) which the surrounding program actually performs, then hands the
result back so the model can use it in its answer.

**How it works here:** Anthropic/OpenAI expose tool calling as a first-class
API feature — you pass tool schemas, the model returns a typed "tool use"
block instead of text. Hugging Face's free inference tier for most open
models doesn't have that. So the contract is taught entirely through the
system prompt: *"to call a tool, respond with ONLY `{"tool_call": {...}}`;
otherwise respond in plain text."* The orchestrator (`app/agent/orchestrator.py`)
then:

1. Sends the prompt + conversation so far.
2. Tries to parse the reply as that exact JSON shape.
3. If it parses: validates arguments against the tool's JSON schema, calls
   the tool via MCP, appends the result as a new message, and loops.
4. If it doesn't parse: treats the reply as the final answer.

**Why we chose this design:** it's the only free option, and it happens to
be more educational — nothing about tool calling is hidden behind an SDK.
The cost is reliability: a smaller/free model is more likely to disobey the
format than a model with a dedicated tool-use training objective.

**Production concern:** every step that trusts the model's output is a
place things can go wrong, and each needs an explicit fallback:
malformed JSON → treated as plain text, not an error; unknown tool name →
returned as an "error" tool result, not raised; invalid arguments → caught
by JSON-schema validation before execution, not passed through. A framework
with native function-calling support removes the *parsing* failure mode
(the API guarantees valid structure) but not the *argument correctness* or
*infinite-loop* failure modes — those guardrails would still be needed even
with Claude or GPT.
