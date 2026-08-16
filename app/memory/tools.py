"""Wraps session-scoped traveller memory as LocalTools for the agent's
tool-calling loop. session_id is injected by the orchestrator from the
trusted request context — see app/agent/tools.py::LocalToolRegistry.call
and docs/memory.md for why it's never an LLM-supplied argument.
"""
from __future__ import annotations

from app.agent.tools import LocalTool
from app.logging_config import get_logger
from app.memory import store as memory_store

logger = get_logger(__name__)


def _remember_preference(session_id: str | None, key: str, value: str) -> str:
    if not session_id:
        return "No session_id on this request — start a session to remember preferences."
    try:
        memory_store.save_preference(session_id, key, value)
    except Exception as exc:  # noqa: BLE001 - DB failure must degrade, not crash the request
        logger.error("memory_save_preference_failed", error=str(exc))
        return "Memory is temporarily unavailable."
    return f"Remembered: {key} = {value}"


def _remember_place(session_id: str | None, place: str, note: str = "") -> str:
    if not session_id:
        return "No session_id on this request — start a session to save places."
    try:
        memory_store.save_place(session_id, place, note)
    except Exception as exc:  # noqa: BLE001
        logger.error("memory_save_place_failed", error=str(exc))
        return "Memory is temporarily unavailable."
    return f"Saved place: {place}"


def _recall_traveller_context(session_id: str | None) -> str:
    if not session_id:
        return "No session_id on this request — nothing to recall."
    try:
        context = memory_store.get_context(session_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("memory_recall_failed", error=str(exc))
        return "Memory is temporarily unavailable."
    if not context["preferences"] and not context["saved_places"]:
        return "Nothing remembered yet for this traveller."
    lines = [f"- {k}: {v}" for k, v in context["preferences"].items()]
    lines += [
        f"- Saved place: {p['place']}" + (f" ({p['note']})" if p["note"] else "")
        for p in context["saved_places"]
    ]
    return "Remembered so far:\n" + "\n".join(lines)


def build_memory_tools() -> list[LocalTool]:
    return [
        LocalTool(
            name="remember_preference",
            description=(
                "Save a traveller preference for this session (e.g. dietary needs, travel style, budget). "
                "Use when the user states a preference worth remembering for the rest of the trip."
            ),
            input_schema={
                "type": "object",
                "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
                "required": ["key", "value"],
            },
            fn=_remember_preference,
            needs_session=True,
        ),
        LocalTool(
            name="remember_place",
            description="Save a place the traveller wants to remember for this trip (e.g. a hostel, restaurant, landmark).",
            input_schema={
                "type": "object",
                "properties": {"place": {"type": "string"}, "note": {"type": "string"}},
                "required": ["place"],
            },
            fn=_remember_place,
            needs_session=True,
        ),
        LocalTool(
            name="recall_traveller_context",
            description=(
                "Retrieve everything remembered so far for this traveller — preferences and saved places. "
                "Use at the start of planning to personalize the answer."
            ),
            input_schema={"type": "object", "properties": {}},
            fn=_recall_traveller_context,
            needs_session=True,
        ),
    ]
