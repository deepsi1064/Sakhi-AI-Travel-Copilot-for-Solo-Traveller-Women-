"""Prompt construction for the manual tool-calling loop.

Hugging Face's free-tier chat models don't expose native function-calling
the way Anthropic/OpenAI do, so we teach the model a tool-call contract
through the system prompt and parse its output ourselves. See
docs/learning-notes/001-tool-calling-without-native-function-calling.md
"""
from __future__ import annotations

import json

SYSTEM_PROMPT_TEMPLATE = """You are Sakhi, a travel copilot for solo female travellers in India.

You help with trip planning, destinations, transport, and safety-conscious context.
You do not invent safety facts. When you are not sure, say so plainly.
You never claim a place or route is "safe" or "dangerous" in absolute terms —
you can only report what tools return, plus clearly-labelled general guidance.

You have access to these tools:
{tool_descriptions}

To call a tool, respond with ONLY this JSON object and nothing else:
{{"tool_call": {{"name": "<tool_name>", "arguments": {{...}}}}}}

To give the traveller your final answer, respond with plain text (no JSON).
Only call a tool when it will materially improve your answer. Never call the
same tool with the same arguments more than once.
"""


def render_tool_descriptions(tools: list[dict]) -> str:
    lines = []
    for tool in tools:
        schema = json.dumps(tool["input_schema"])
        lines.append(f"- {tool['name']} ({tool['server']}): {tool['description']}\n  arguments schema: {schema}")
    return "\n".join(lines) if lines else "(no tools available)"


def build_system_prompt(tools: list[dict]) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(tool_descriptions=render_tool_descriptions(tools))
