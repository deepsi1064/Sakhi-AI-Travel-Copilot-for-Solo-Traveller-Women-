"""Deterministic, India-wide emergency contact data.

This is intentionally static and small: emergency numbers are exactly the
kind of fact the LLM must never be allowed to guess, so they're hard-coded
here rather than retrieved or inferred. See docs/guardrails.md.
"""

NATIONAL_EMERGENCY_NUMBERS = {
    "national_emergency": "112",
    "police": "100",
    "women_helpline": "1091",
    "ambulance": "108",
    "tourist_helpline": "1363",
}
