"""Wraps RAG retrieval as a LocalTool for the agent's tool-calling loop."""
from __future__ import annotations

from app.agent.tools import LocalTool
from app.logging_config import get_logger
from app.rag import store as rag_store

logger = get_logger(__name__)


def _retrieve_travel_knowledge(query: str) -> str:
    try:
        results = rag_store.search(query)
    except Exception as exc:  # noqa: BLE001 - DB/embedding failure must degrade, not crash the request
        logger.error("rag_search_failed", error=str(exc))
        return "Knowledge base is temporarily unavailable."
    if not results:
        return "No relevant information found in the knowledge base for this query."
    entries = "\n\n".join(f"[{r['source']}] {r['chunk_text']}" for r in results)
    return f"Retrieved knowledge (curated, not live data):\n{entries}"


def build_rag_tools() -> list[LocalTool]:
    return [
        LocalTool(
            name="retrieve_travel_knowledge",
            description=(
                "Retrieve curated general guidance for solo female travellers in India — cultural norms, "
                "common tourist scams, general safety habits. Use for broad 'what should I know/be aware of' "
                "questions that aren't about a specific destination or a live lookup."
            ),
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            fn=_retrieve_travel_knowledge,
        )
    ]
