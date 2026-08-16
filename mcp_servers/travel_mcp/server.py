"""Travel MCP server: destination knowledge and (real) place lookup.

Why an MCP server and not a plain function import in the agent process? The
agent shouldn't have to trust or directly embed a growing set of travel
data sources — it talks to this server over the MCP protocol the same way
it would talk to a third-party MCP server. That boundary is what lets us
swap in a real API (OpenStreetMap Nominatim) for `search_places` without
touching the agent at all. See docs/mcp.md.
"""
from __future__ import annotations

import httpx
from mcp.server import MCPServer

from mcp_servers.travel_mcp.data import DESTINATIONS, normalize_key

mcp = MCPServer("sakhi-travel")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "sakhi-travel-agent/0.1 (educational project)"


@mcp.tool()
def get_destination_info(destination: str) -> str:
    """Get curated overview, best time to visit, and traveller notes for a supported Indian destination."""
    entry = DESTINATIONS.get(normalize_key(destination))
    if entry is None:
        supported = ", ".join(sorted(DESTINATIONS))
        return f"No curated data for '{destination}'. Currently supported: {supported}."

    notes = "\n".join(f"- {note}" for note in entry["traveller_notes"])
    return (
        f"{destination.title()}, {entry['state']}\n"
        f"Overview: {entry['overview']}\n"
        f"Best time to visit: {entry['best_time']}\n"
        f"Getting around: {entry['getting_around']}\n"
        f"Traveller notes (community-sourced, not verified):\n{notes}"
    )


@mcp.tool()
def search_places(query: str, near: str = "") -> str:
    """Look up real places (landmarks, stations, stays) by name using OpenStreetMap. `near` narrows the search, e.g. a city name."""
    search_text = f"{query}, {near}" if near else query
    try:
        response = httpx.get(
            NOMINATIM_URL,
            params={"q": search_text, "format": "json", "limit": 5, "countrycodes": "in"},
            headers={"User-Agent": USER_AGENT},
            timeout=10.0,
        )
        response.raise_for_status()
        results = response.json()
    except httpx.HTTPError as exc:
        return f"Place lookup failed: {exc}"

    if not results:
        return f"No results found for '{search_text}'."

    lines = [f"- {r['display_name']} (lat={r['lat']}, lon={r['lon']})" for r in results]
    return "Results (source: OpenStreetMap):\n" + "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
