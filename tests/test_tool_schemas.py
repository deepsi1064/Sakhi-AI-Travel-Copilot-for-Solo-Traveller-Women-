from app.agent.orchestrator import _parse_tool_call
from mcp_servers.travel_mcp.data import DESTINATIONS


def test_parse_tool_call_valid_json():
    raw = '{"tool_call": {"name": "get_destination_info", "arguments": {"destination": "Varkala"}}}'
    assert _parse_tool_call(raw) == ("get_destination_info", {"destination": "Varkala"})


def test_parse_tool_call_returns_none_for_plain_text():
    assert _parse_tool_call("Varkala is a great choice for solo travellers.") is None


def test_parse_tool_call_returns_none_for_malformed_json():
    assert _parse_tool_call('{"tool_call": {"name": ') is None


def test_parse_tool_call_returns_none_when_arguments_not_object():
    raw = '{"tool_call": {"name": "get_destination_info", "arguments": "Varkala"}}'
    assert _parse_tool_call(raw) is None


def test_parse_tool_call_takes_first_of_multiple_concatenated_calls():
    # Real failure observed live: the model emitted two tool_call objects
    # back to back in one reply. json.loads would reject this outright.
    raw = (
        '{"tool_call": {"name": "remember_preference", "arguments": {"key": "diet", "value": "vegetarian"}}}\n'
        '{"tool_call": {"name": "remember_preference", "arguments": {"key": "budget", "value": "tight"}}}'
    )
    assert _parse_tool_call(raw) == ("remember_preference", {"key": "diet", "value": "vegetarian"})


def test_all_destinations_have_traveller_notes():
    for name, entry in DESTINATIONS.items():
        assert entry["traveller_notes"], f"{name} has no traveller notes"
