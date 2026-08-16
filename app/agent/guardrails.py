"""Deterministic checks that run before and after the LLM.

These are heuristics, not guarantees. See docs/guardrails.md for what each
check does and does not catch.
"""
from __future__ import annotations

import re

from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError

MAX_MESSAGE_LENGTH_DEFAULT = 2000
MAX_SESSION_ID_LENGTH = 128

_INJECTION_PATTERNS = [
    re.compile(r"ignore (all|any|the) (previous|prior|above) instructions", re.IGNORECASE),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"disregard (your|the) (system|previous) prompt", re.IGNORECASE),
    re.compile(r"reveal (your|the) (system prompt|instructions)", re.IGNORECASE),
    re.compile(r"act as (?!a travel)", re.IGNORECASE),
]

_SAFETY_KEYWORDS = [
    "alone", "solo", "safe", "safety", "danger", "dangerous", "scared",
    "afraid", "night", "harass", "emergency", "police", "attack", "unsafe",
    "following", "follow me", "threat", "assault",
]

SAFETY_DISCLAIMER = (
    "Safety note: this is general guidance based on available information, "
    "not a verified safety guarantee. Conditions change — use your judgement, "
    "stay reachable, and contact local emergency services (112 in India) if "
    "you feel unsafe."
)


class GuardrailViolation(ValueError):
    pass


def validate_user_message(text: str, max_length: int = MAX_MESSAGE_LENGTH_DEFAULT) -> str:
    if not text or not text.strip():
        raise GuardrailViolation("message must not be empty")
    if len(text) > max_length:
        raise GuardrailViolation(f"message exceeds {max_length} characters")
    if "\x00" in text:
        raise GuardrailViolation("message contains invalid characters")
    return text.strip()


def validate_session_id(session_id: str | None) -> str | None:
    if session_id is None:
        return None
    session_id = session_id.strip()
    if not session_id or len(session_id) > MAX_SESSION_ID_LENGTH:
        raise GuardrailViolation(f"session_id must be 1-{MAX_SESSION_ID_LENGTH} characters")
    return session_id


def looks_like_prompt_injection(text: str) -> bool:
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)


def mentions_safety_topic(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in _SAFETY_KEYWORDS)


def validate_tool_arguments(schema: dict, arguments: dict) -> None:
    try:
        jsonschema_validate(instance=arguments, schema=schema)
    except ValidationError as exc:
        raise GuardrailViolation(f"invalid tool arguments: {exc.message}") from exc
