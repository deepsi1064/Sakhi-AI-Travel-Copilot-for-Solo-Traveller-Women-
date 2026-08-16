from app.memory.tools import (
    _recall_traveller_context,
    _remember_place,
    _remember_preference,
    build_memory_tools,
)


def test_remember_preference_without_session_id():
    assert "session_id" in _remember_preference(None, "diet", "vegetarian").lower()


def test_remember_place_without_session_id():
    assert "session_id" in _remember_place(None, "Cafe X").lower()


def test_recall_without_session_id():
    assert "nothing to recall" in _recall_traveller_context(None).lower()


def test_remember_preference_degrades_on_db_error(monkeypatch):
    def boom(session_id, key, value):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.memory.tools.memory_store.save_preference", boom)
    assert _remember_preference("s1", "diet", "vegetarian") == "Memory is temporarily unavailable."


def test_remember_place_degrades_on_db_error(monkeypatch):
    def boom(session_id, place, note):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.memory.tools.memory_store.save_place", boom)
    assert _remember_place("s1", "Cafe X") == "Memory is temporarily unavailable."


def test_recall_degrades_on_db_error(monkeypatch):
    def boom(session_id):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.memory.tools.memory_store.get_context", boom)
    assert _recall_traveller_context("s1") == "Memory is temporarily unavailable."


def test_recall_formats_preferences_and_places(monkeypatch):
    monkeypatch.setattr(
        "app.memory.tools.memory_store.get_context",
        lambda session_id: {
            "preferences": {"diet": "vegetarian"},
            "saved_places": [{"place": "Cafe X", "note": "good coffee"}],
        },
    )
    result = _recall_traveller_context("s1")
    assert "diet: vegetarian" in result
    assert "Cafe X" in result
    assert "good coffee" in result


def test_build_memory_tools_returns_three_session_scoped_tools():
    tools = build_memory_tools()
    assert {t.name for t in tools} == {"remember_preference", "remember_place", "recall_traveller_context"}
    assert all(t.needs_session for t in tools)
