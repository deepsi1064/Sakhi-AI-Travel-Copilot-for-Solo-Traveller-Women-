"""Local (non-MCP) tools: capabilities that stay in-process because they
need direct access to the app's own state (e.g. a DB connection) rather
than an external boundary. See docs/rag.md for why RAG is a local tool
and not a third MCP server.

Local and MCP tools share one contract — {name, description, input_schema}
— so the orchestrator's tool-calling loop doesn't need to know which kind
it's calling.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class LocalTool:
    name: str
    description: str
    input_schema: dict[str, Any]
    fn: Callable[..., str]
    # True for tools that need the caller's session_id (e.g. memory).
    # session_id is injected by the orchestrator from the trusted request
    # context, never taken from the LLM-supplied arguments — see
    # docs/memory.md for why that boundary matters.
    needs_session: bool = False


class LocalToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, LocalTool] = {}

    def register(self, tool: LocalTool) -> None:
        self._tools[tool.name] = tool

    def has(self, name: str) -> bool:
        return name in self._tools

    def get_schema(self, name: str) -> dict[str, Any] | None:
        tool = self._tools.get(name)
        return tool.input_schema if tool else None

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": t.name, "server": "local", "description": t.description, "input_schema": t.input_schema}
            for t in self._tools.values()
        ]

    def call(self, name: str, arguments: dict[str, Any], session_id: str | None = None) -> str:
        tool = self._tools[name]
        call_args = dict(arguments)
        call_args.pop("session_id", None)  # never let the LLM supply/override this
        if tool.needs_session:
            return tool.fn(session_id=session_id, **call_args)
        return tool.fn(**call_args)
