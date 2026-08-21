# Sakhi — AI Travel Copilot for Solo Female Travellers in India

Sakhi is a trip-planning and safety-context copilot for solo female
travellers in India, and a hands-on learning project for production AI
agent engineering (MCP, tool calling, guardrails, evaluation, observability).

<img width="1536" height="1024" alt="sakhi architecture" src="https://github.com/user-attachments/assets/cdddaace-15e3-42a5-a782-7fd1ec31965c" />



## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

cp .env.example .env          # then fill in HF_TOKEN
# get a free token at https://huggingface.co/settings/tokens

docker-compose up -d           # Postgres + pgvector, for RAG
python -m app.rag.ingest       # embed and store the curated knowledge base

uvicorn app.main:app --reload
```

Try it:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I am travelling solo to Varkala, what should I know?"}'
```

`GET /health` for a liveness check.

## Frontend

```bash
cd frontend
npm install
npm run dev             
```



## Project layout

```
app/                  FastAPI backend, agent orchestrator, RAG, Memory
mcp_servers/           Travel MCP and Safety MCP servers (stdio)
frontend/              React (Vite) chat UI
tests/                 Offline unit tests
evals/                 Small eval dataset + manual runner
docs/                  Architecture, decisions, and learning notes
docker-compose.yml     Postgres + pgvector
```

## Status

Working: chat endpoint, manual tool-calling loop over Hugging Face,
Travel MCP, Safety MCP, RAG over a curated knowledge base (pgvector),
session-scoped Memory (preferences + saved places), guardrails, rate
limiting, structured logging, React chat UI.


