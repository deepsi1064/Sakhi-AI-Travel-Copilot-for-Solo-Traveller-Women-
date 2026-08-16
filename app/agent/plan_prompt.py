"""Deterministic prompt construction for POST /plan.

Turns structured form fields into one well-formed instruction for the same
agent loop /chat already uses — no separate "planning agent", just a
better-shaped prompt. Pure function, no I/O, easy to test. See docs/planning.md.
"""
from __future__ import annotations

from app.api.schemas import PlanRequest


def build_plan_prompt(payload: PlanRequest) -> str:
    lines = ["Plan a trip for a solo female traveller in India with these details:"]
    lines.append(
        f"- Destination: {payload.destination}"
        if payload.destination
        else "- Destination: open to a suggestion from supported destinations"
    )
    if payload.starting_city:
        lines.append(f"- Starting city: {payload.starting_city}")
    if payload.duration_days:
        lines.append(f"- Duration: {payload.duration_days} day(s)")
    if payload.budget:
        lines.append(f"- Approximate budget: {payload.budget}")
    if payload.preferences:
        lines.append(f"- Trip-specific preferences/constraints: {payload.preferences}")

    lines.append("")
    lines.append(
        "First check my saved traveller preferences if relevant to this trip. "
        "Then give a practical, day-by-day itinerary. Briefly explain why it fits my "
        "constraints and preferences — don't just describe the destination generically. "
        "Include specific, grounded safety considerations (e.g. late-night arrival, "
        "transport, isolated areas, relevant cultural considerations) without making "
        "unsupported claims like a place being 'safe' or 'unsafe' overall. "
        "Do not look up emergency numbers yourself — those are provided separately."
    )
    return "\n".join(lines)
