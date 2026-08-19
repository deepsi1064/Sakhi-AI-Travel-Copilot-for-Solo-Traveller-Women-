# Agent Architecture

## Why a manual loop instead of a framework

No LangChain/LangGraph. The orchestrator (`app/agent/orchestrator.py`) is a
plain Python loop — bounded, inspectable, and small enough to read in one
sitting. Given the explicit learning goal ("understand what's actually
happening"), a framework would hide the exact mechanism we're trying to
learn: how tool calls get proposed, validated, and executed.

## The loop

```
messages = [system_prompt(tools), user_message]

repeat up to MAX_TOOL_ITERATIONS times:
    reply = llm.chat(messages)
    if reply parses as {"tool_call": {...}}:
        validate arguments against the tool's JSON schema
        result = mcp_client.call_tool(name, arguments)
        append reply and result to messages
        continue
    else:
        return reply as the final answer

# budget exhausted: force a plain-text answer, no more tool calls allowed
```

## Why JSON-in-text instead of native function calling

Anthropic and OpenAI expose a dedicated tool-use API: the model's structured
tool call comes back as a typed field, not as text you have to parse.
Hugging Face's free-tier inference doesn't offer that for most open models,
so the contract is taught entirely through the system prompt
(`app/agent/prompts.py`): *"respond with ONLY this JSON object, or plain
text for your final answer."*

Consequences of that choice, and how each is handled:

- **The model might not comply.** `_parse_tool_call` only accepts text that
  starts with `{` and parses as the exact expected shape; anything else
  falls through to "treat as final answer." A malformed tool-call attempt
  just becomes a slightly odd final answer instead of crashing the request.
- **The model might hallucinate a tool name or bad arguments.** Both are
  caught deterministically — unknown tool name, or `jsonschema` validation
  failure — before anything is executed. The error is fed back to the model
  as a tool result, not raised to the user.
- **The model might loop forever.** `MAX_TOOL_ITERATIONS` (default 3) caps
  it; the last turn explicitly instructs the model to stop calling tools.

See [learning-notes/001-tool-calling-without-native-function-calling.md](learning-notes/001-tool-calling-without-native-function-calling.md)
for the condensed version of this tradeoff.

## Where guardrails sit in the loop

- Before the loop: message validation (length, emptiness) and
  prompt-injection pattern matching on the *user's* input.
- Inside the loop: JSON-schema validation on every tool call's arguments,
  before execution.
- After the loop: the safety disclaimer is appended by code, never
  requested from or phrased by the model.

Full guardrail inventory and limitations: [guardrails.md](guardrails.md).
