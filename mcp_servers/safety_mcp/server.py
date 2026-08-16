"""Safety MCP server: deterministic emergency information.

Kept as a separate MCP server from Travel because it carries a different
trust and change profile — this data must stay accurate and is never
LLM-generated, whereas travel content can be looser and more exploratory.
See docs/mcp.md.
"""
from __future__ import annotations

from mcp.server import MCPServer

from mcp_servers.safety_mcp.data import NATIONAL_EMERGENCY_NUMBERS

mcp = MCPServer("sakhi-safety")


@mcp.tool()
def get_emergency_info(state_or_city: str = "") -> str:
    """Get India emergency contact numbers: national emergency, police, women's helpline, ambulance, tourist helpline. These are fixed national numbers, not a location-specific lookup yet."""
    lines = [f"- {label.replace('_', ' ').title()}: {number}" for label, number in NATIONAL_EMERGENCY_NUMBERS.items()]
    location_note = f" (these are national numbers and apply regardless of {state_or_city})" if state_or_city else ""
    return f"India emergency numbers{location_note}:\n" + "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
