from app.agent.tools import LocalTool, LocalToolRegistry


def test_register_list_and_call():
    registry = LocalToolRegistry()
    registry.register(
        LocalTool(
            name="echo",
            description="echoes input",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            fn=lambda text: f"echo:{text}",
        )
    )

    assert registry.has("echo")
    assert not registry.has("missing")

    tools = registry.list_tools()
    assert tools == [
        {
            "name": "echo",
            "server": "local",
            "description": "echoes input",
            "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        }
    ]

    assert registry.call("echo", {"text": "hi"}) == "echo:hi"


def test_get_schema_returns_none_for_unknown_tool():
    registry = LocalToolRegistry()
    assert registry.get_schema("nope") is None


def test_registry_injects_session_id_for_session_scoped_tools():
    registry = LocalToolRegistry()
    calls = []
    registry.register(
        LocalTool(
            name="save",
            description="saves",
            input_schema={"type": "object", "properties": {"value": {"type": "string"}}},
            fn=lambda session_id, value: calls.append((session_id, value)) or "ok",
            needs_session=True,
        )
    )

    result = registry.call("save", {"value": "x"}, session_id="abc")

    assert result == "ok"
    assert calls == [("abc", "x")]


def test_registry_strips_llm_supplied_session_id():
    registry = LocalToolRegistry()
    seen = {}
    registry.register(
        LocalTool(
            name="save",
            description="saves",
            input_schema={"type": "object", "properties": {}},
            fn=lambda session_id, **kw: seen.update(session_id=session_id, extra=kw) or "ok",
            needs_session=True,
        )
    )

    registry.call("save", {"session_id": "attacker-supplied", "other": "y"}, session_id="trusted")

    assert seen["session_id"] == "trusted"
    assert seen["extra"] == {"other": "y"}


def test_non_session_tool_does_not_receive_session_id():
    registry = LocalToolRegistry()
    registry.register(
        LocalTool(
            name="echo",
            description="echoes",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
            fn=lambda text: f"echo:{text}",
        )
    )

    assert registry.call("echo", {"text": "hi"}, session_id="abc") == "echo:hi"
