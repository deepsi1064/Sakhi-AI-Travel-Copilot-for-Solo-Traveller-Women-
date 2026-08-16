from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.agent.guardrails import GuardrailViolation
from app.api.schemas import ChatRequest, ChatResponse, ToolCallView
from app.core.middleware import enforce_rate_limit, require_api_key

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)])
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    orchestrator = request.app.state.orchestrator
    if orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM not configured: set HF_TOKEN in .env and restart",
        )

    try:
        result = await orchestrator.handle_message(payload.message, payload.session_id)
    except GuardrailViolation as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ChatResponse(
        reply=result.reply,
        disclaimer=result.disclaimer,
        tool_calls=[
            ToolCallView(name=t.name, arguments=t.arguments, result=t.result, error=t.error) for t in result.tool_calls
        ],
        flagged_injection=result.flagged_injection,
    )
