from app.rag.ingest import chunk_markdown


def test_chunk_markdown_splits_on_blank_lines():
    text = "Para one.\n\nPara two.\n\n\nPara three."
    assert chunk_markdown(text) == ["Para one.", "Para two.", "Para three."]


def test_chunk_markdown_strips_whitespace_and_drops_empty():
    text = "  First.  \n\n\n\n  Second.  \n\n"
    assert chunk_markdown(text) == ["First.", "Second."]


def test_knowledge_files_are_non_empty():
    from app.rag.ingest import KNOWLEDGE_DIR

    files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    assert files, "expected curated knowledge files to exist"
    for path in files:
        assert chunk_markdown(path.read_text(encoding="utf-8")), f"{path.name} produced no chunks"
