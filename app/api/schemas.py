from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class ToolCallView(BaseModel):
    name: str
    arguments: dict
    result: str | None = None
    error: str | None = None


class ChatResponse(BaseModel):
    reply: str
    disclaimer: str | None = None
    tool_calls: list[ToolCallView]
    flagged_injection: bool = False


class PlanRequest(BaseModel):
    destination: str | None = Field(None, max_length=200)
    starting_city: str | None = Field(None, max_length=200)
    duration_days: int | None = Field(None, gt=0, le=90)
    budget: str | None = Field(None, max_length=200)
    preferences: str | None = Field(None, max_length=1000)
    session_id: str | None = None


class PlanResponse(BaseModel):
    plan: str
    disclaimer: str | None = None
    tool_calls: list[ToolCallView]
    # Always present, from Safety MCP directly — not left to the LLM's
    # discretion. See app/api/routes_plan.py.
    emergency_info: str
    flagged_injection: bool = False
