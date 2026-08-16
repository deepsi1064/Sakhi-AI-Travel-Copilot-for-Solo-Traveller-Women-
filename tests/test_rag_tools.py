from app.rag.tools import _retrieve_travel_knowledge, build_rag_tools


def test_retrieve_returns_no_results_message(monkeypatch):
    monkeypatch.setattr("app.rag.tools.rag_store.search", lambda query, top_k=3: [])
    assert "No relevant information" in _retrieve_travel_knowledge("visa rules")


def test_retrieve_formats_results(monkeypatch):
    results = [{"source": "cultural_norms", "chunk_text": "Cover shoulders at temples.", "distance": 0.1}]
    monkeypatch.setattr("app.rag.tools.rag_store.search", lambda query, top_k=3: results)

    result = _retrieve_travel_knowledge("what to wear")

    assert "cultural_norms" in result
    assert "Cover shoulders at temples." in result


def test_retrieve_degrades_on_error(monkeypatch):
    def boom(query, top_k=3):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.rag.tools.rag_store.search", boom)
    assert _retrieve_travel_knowledge("anything") == "Knowledge base is temporarily unavailable."


def test_build_rag_tools_returns_one_tool():
    tools = build_rag_tools()
    assert [t.name for t in tools] == ["retrieve_travel_knowledge"]
    assert tools[0].needs_session is False
