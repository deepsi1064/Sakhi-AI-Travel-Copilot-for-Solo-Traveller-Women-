"""Manual evaluation runner for the small eval dataset in eval_dataset.json.

This does not do automated pass/fail grading — most of these cases need a
human (or a documented LLM-judge, added later) to read the transcript and
decide whether the answer is acceptable. See docs/evaluation.md.

Usage:
    python evals/run_eval.py
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.agent.llm_client import HuggingFaceLLMClient
from app.agent.mcp_client import McpClientManager
from app.agent.orchestrator import AgentOrchestrator

DATASET_PATH = Path(__file__).parent / "eval_dataset.json"
RESULTS_PATH = Path(__file__).parent / "eval_results.json"


async def main() -> None:
    cases = json.loads(DATASET_PATH.read_text())
    mcp_manager = McpClientManager()
    await mcp_manager.start()
    llm_client = HuggingFaceLLMClient()
    orchestrator = AgentOrchestrator(llm_client, mcp_manager)

    results = []
    for case in cases:
        print(f"[{case['id']}] {case['input']}")
        result = await orchestrator.handle_message(case["input"], case.get("session_id"))
        results.append(
            {
                "id": case["id"],
                "category": case["category"],
                "input": case["input"],
                "expectation": case["expectation"],
                "reply": result.reply,
                "tool_calls": [{"name": t.name, "arguments": t.arguments, "error": t.error} for t in result.tool_calls],
                "flagged_injection": result.flagged_injection,
                "disclaimer_attached": result.disclaimer is not None,
            }
        )
        print(f"  -> {result.reply[:120]}")

    await mcp_manager.stop()
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {len(results)} results to {RESULTS_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
