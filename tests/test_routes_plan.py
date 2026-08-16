from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.agent.guardrails import GuardrailViolation
from app.agent.orchestrator import AgentResult, ToolInvocation
from app.api.routes_plan import PLAN_MAX_ITERATIONS, PLAN_MAX_TOKENS
from app.api.routes_plan import router as plan_router


class FakeOrchestrator:
    def __init__(self, result):
        self.result = result
        self.received = None

    async def handle_message(self, message, session_id, max_iterations=None, max_tokens=None):
        self.received = (message, session_id, max_iterations, max_tokens)
        return self.result


class FakeMcpManager:
    def __init__(self, emergency_text="India emergency numbers:\n- Police: 100"):
        self.emergency_text = emergency_text
        self.called_with = None

    async def call_tool(self, name, arguments):
        self.called_with = (name, arguments)
        return self.emergency_text


class BoomMcpManager:
    async def call_tool(self, name, arguments):
        raise RuntimeError("mcp unreachable")


class ViolatingOrchestrator:
    async def handle_message(self, message, session_id, max_iterations=None, max_tokens=None):
        raise GuardrailViolation("session_id must be 1-128 characters")


def _client(orchestrator, mcp_manager):
    app = FastAPI()
    app.include_router(plan_router)
    app.state.orchestrator = orchestrator
    app.state.mcp_manager = mcp_manager
    return TestClient(app)


def test_plan_returns_itinerary_and_deterministic_emergency_info():
    fake_result = AgentResult(
        reply="Day 1: arrive, settle in.",
        tool_calls=[ToolInvocation(name="get_destination_info", arguments={"destination": "Goa"}, result="...")],
        disclaimer="Safety note: ...",
    )
    orchestrator = FakeOrchestrator(fake_result)
    mcp_manager = FakeMcpManager()
    client = _client(orchestrator, mcp_manager)

    response = client.post(
        "/plan",
        json={"destination": "Goa", "starting_city": "Mumbai", "duration_days": 3, "budget": "15000", "session_id": "s1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "Day 1: arrive, settle in."
    assert body["disclaimer"] == "Safety note: ..."
    assert body["emergency_info"] == "India emergency numbers:\n- Police: 100"
    assert mcp_manager.called_with == ("get_emergency_info", {"state_or_city": "Goa"})
    assert orchestrator.received[2] == PLAN_MAX_ITERATIONS
    assert orchestrator.received[3] == PLAN_MAX_TOKENS


def test_plan_returns_503_when_llm_not_configured():
    client = _client(None, FakeMcpManager())
    response = client.post("/plan", json={})
    assert response.status_code == 503


def test_plan_degrades_when_emergency_lookup_fails():
    fake_result = AgentResult(reply="plan text", tool_calls=[])
    client = _client(FakeOrchestrator(fake_result), BoomMcpManager())

    response = client.post("/plan", json={"destination": "Goa"})

    assert response.status_code == 200
    assert response.json()["emergency_info"] == "Emergency info temporarily unavailable."


def test_plan_returns_400_on_guardrail_violation():
    client = _client(ViolatingOrchestrator(), FakeMcpManager())
    response = client.post("/plan", json={"session_id": "x" * 200})
    assert response.status_code == 400


def test_plan_rejects_out_of_range_duration():
    client = _client(FakeOrchestrator(AgentResult(reply="x")), FakeMcpManager())
    response = client.post("/plan", json={"duration_days": 0})
    assert response.status_code == 422
