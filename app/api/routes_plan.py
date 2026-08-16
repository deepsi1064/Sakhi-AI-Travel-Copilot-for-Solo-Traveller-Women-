"""POST /plan: structured trip planning, built entirely on existing
capabilities. Reuses AgentOrchestrator (Travel MCP, RAG, Memory, LLM) for
the personalized itinerary, and calls Safety MCP's get_emergency_info
directly — bypassing the LLM's tool-choice discretion — so emergency
numbers are always present and never depend on whether the model decided
to look them up. See docs/planning.md and docs/decisions.md.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.agent.guardrails import GuardrailViolation
from app.agent.plan_prompt import build_plan_prompt
from app.api.schemas import PlanRequest, PlanResponse, ToolCallView
from app.core.middleware import enforce_rate_limit, require_api_key

router = APIRouter()

# A plan may need several tool calls in one turn (recall preferences, look up
# a destination, retrieve RAG guidance) — one more than the default /chat
# budget. Scoped to this route only; /chat's behavior is unchanged.
PLAN_MAX_ITERATIONS = 4
# A day-by-day itinerary + safety section runs longer than a typical chat
# reply — the default 512 was observed live cutting a plan off mid-sentence.
PLAN_MAX_TOKENS = 900


@router.post("/plan", response_model=PlanResponse, dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)])
async def plan_trip(payload: PlanRequest, request: Request) -> PlanResponse:
    orchestrator = request.app.state.orchestrator
    mcp_manager = request.app.state.mcp_manager
    if orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM not configured: set HF_TOKEN in .env and restart",
        )

    prompt = build_plan_prompt(payload)
    try:
        result = await orchestrator.handle_message(
            prompt, payload.session_id, max_iterations=PLAN_MAX_ITERATIONS, max_tokens=PLAN_MAX_TOKENS
        )
    except GuardrailViolation as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        emergency_info = await mcp_manager.call_tool("get_emergency_info", {"state_or_city": payload.destination or ""})
    except Exception:  # noqa: BLE001 - deterministic info must degrade, not break the plan
        emergency_info = "Emergency info temporarily unavailable."

    return PlanResponse(
        plan=result.reply,
        disclaimer=result.disclaimer,
        tool_calls=[
            ToolCallView(name=t.name, arguments=t.arguments, result=t.result, error=t.error) for t in result.tool_calls
        ],
        emergency_info=emergency_info,
        flagged_injection=result.flagged_injection,
    )
