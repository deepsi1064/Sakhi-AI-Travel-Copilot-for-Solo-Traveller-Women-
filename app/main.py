from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.llm_client import HuggingFaceLLMClient, LLMError
from app.agent.mcp_client import McpClientManager
from app.agent.orchestrator import AgentOrchestrator
from app.agent.tools import LocalToolRegistry
from app.api.routes_chat import router as chat_router
from app.api.routes_plan import router as plan_router
from app.config import get_settings
from app.core.middleware import RequestIDMiddleware
from app.logging_config import configure_logging, get_logger
from app.memory.tools import build_memory_tools
from app.rag.tools import build_rag_tools

configure_logging()
logger = get_logger(__name__)


def _build_local_tools() -> LocalToolRegistry:
    registry = LocalToolRegistry()
    for tool in [*build_rag_tools(), *build_memory_tools()]:
        registry.register(tool)
    return registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    mcp_manager = McpClientManager()
    await mcp_manager.start()
    local_tools = _build_local_tools()

    try:
        llm_client: HuggingFaceLLMClient | None = HuggingFaceLLMClient()
    except LLMError as exc:
        logger.warning("llm_client_unavailable", error=str(exc))
        llm_client = None

    app.state.mcp_manager = mcp_manager
    app.state.orchestrator = AgentOrchestrator(llm_client, mcp_manager, local_tools) if llm_client else None

    yield

    await mcp_manager.stop()


app = FastAPI(title="Sakhi", version="0.1.0", lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "X-API-Key"],
)
app.include_router(chat_router)
app.include_router(plan_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
