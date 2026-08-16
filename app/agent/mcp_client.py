"""MCP client: launches each MCP server as a subprocess over stdio and
exposes tool discovery + invocation to the agent orchestrator.

Why stdio and not HTTP? These servers run on the same machine as the agent
for now, so stdio keeps the setup dependency-free (no extra port, no auth
layer) while still going through the real MCP protocol — tool discovery,
JSON-RPC framing, structured results. See docs/mcp.md.
"""
from __future__ import annotations

import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any

import structlog
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class McpServerSpec:
    name: str
    command: str
    args: list[str]


# Use sys.executable, not the bare "python" command: the MCP server runs as
# a subprocess, and it must be the same interpreter (with the same installed
# packages) as the agent process, not whatever "python" resolves to on PATH.
DEFAULT_SERVERS = [
    McpServerSpec(name="travel", command=sys.executable, args=["-m", "mcp_servers.travel_mcp.server"]),
    McpServerSpec(name="safety", command=sys.executable, args=["-m", "mcp_servers.safety_mcp.server"]),
]


class McpClientManager:
    """Owns one ClientSession per MCP server for the app's lifetime."""

    def __init__(self, servers: list[McpServerSpec] | None = None) -> None:
        self._servers = servers or DEFAULT_SERVERS
        self._stack = AsyncExitStack()
        self._sessions: dict[str, ClientSession] = {}
        self._tools: dict[str, dict[str, Any]] = {}

    async def start(self) -> None:
        for spec in self._servers:
            params = StdioServerParameters(command=spec.command, args=spec.args)
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self._sessions[spec.name] = session

            tool_list = await session.list_tools()
            for tool in tool_list.tools:
                self._tools[tool.name] = {
                    "server": spec.name,
                    "description": tool.description or "",
                    "input_schema": tool.input_schema or {},
                }
            logger.info("mcp_server_started", server=spec.name, tools=[t.name for t in tool_list.tools])

    async def stop(self) -> None:
        await self._stack.aclose()

    def list_tools(self) -> list[dict[str, Any]]:
        return [{"name": name, **meta} for name, meta in self._tools.items()]

    def get_tool_schema(self, name: str) -> dict[str, Any] | None:
        tool = self._tools.get(name)
        return tool["input_schema"] if tool else None

    def get_tool_server(self, name: str) -> str | None:
        tool = self._tools.get(name)
        return tool["server"] if tool else None

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"unknown tool: {name}")
        session = self._sessions[tool["server"]]
        result = await session.call_tool(name, arguments)
        parts = [block.text for block in result.content if hasattr(block, "text")]
        return "\n".join(parts)
