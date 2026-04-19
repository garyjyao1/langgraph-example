# langgraph-example

[![Build](https://github.com/garyjyao1/langgraph-example/actions/workflows/build.yaml/badge.svg)](https://github.com/garyjyao1/langgraph-example/actions/workflows/build.yaml)

A monorepo demonstrating a production-quality agentic application implemented against the same feature set in two Python AI frameworks — **LangGraph** and **PydanticAI** — so you can make an informed choice.

## Implementations

| | [langgraph/](langgraph/) | [pydantic-ai/](pydantic-ai/) |
|---|---|---|
| **Framework** | LangGraph + LangChain | PydanticAI |
| **Agent model** | `StateGraph` (nodes/edges) | `Agent` (built-in ReAct loop) |
| **Memory** | LangGraph SQLite checkpointer | Custom SQLite via `memory.py` |
| **MCP support** | `langchain-mcp-adapters` | Native `MCPServerStreamableHTTP` |
| **Providers** | LangChain multi-provider ecosystem | Ollama + OpenAI (OpenAI-compatible) |
| **Tracing** | LangSmith | Logfire |

See [COMPARISON.md](COMPARISON.md) for a detailed side-by-side breakdown.

## Repository Structure

```
langgraph-example/
├── pyproject.toml          # uv workspace root
├── shared/                 # shared Python package (uv workspace member)
│   ├── pyproject.toml
│   └── functions/          # tool implementations (bash, web, math, config)
│       ├── bash.py
│       ├── config.py
│       ├── math.py
│       └── web.py
├── langgraph/              # LangGraph implementation (uv workspace member)
│   ├── graph.py            # StateGraph definition
│   ├── agent.py            # CLI REPL
│   ├── server_api.py       # FastAPI HTTP API
│   ├── llm_factory.py      # LLM provider factory
│   ├── functions/
│   │   └── guardrails.py   # LangChain-backed guardrails
│   ├── mcp_servers/
│   │   └── __init__.py     # langchain-mcp-adapters connection logic
│   └── pyproject.toml
├── pydantic-ai/            # PydanticAI implementation (uv workspace member)
│   ├── pydantic_agent.py   # Agent + MCP + HITL setup
│   ├── memory.py           # SQLite message history
│   ├── agent.py            # CLI REPL
│   ├── server_api.py       # FastAPI HTTP API
│   ├── llm_factory.py      # LLM provider factory
│   ├── functions/
│   │   └── guardrails.py   # PydanticAI-backed guardrails
│   ├── mcp_servers/
│   │   └── __init__.py     # native MCPServerStreamableHTTP connection logic
│   └── pyproject.toml
├── mcp_servers/            # shared standalone MCP server
│   └── example/
│       ├── server.py
│       └── tools/
├── deployment/             # shared Helm charts
├── frontend/               # shared React frontend
├── static/                 # shared static assets (playground UI)
├── templates/              # shared HTML templates
├── COMPARISON.md           # detailed framework comparison
└── README.md               # this file
```

## Quickstart

Each implementation is a uv workspace member. Install from the repo root or from within each impl directory.

### LangGraph

```bash
cd langgraph/
uv sync
./run-cli-agent.sh
```

### PydanticAI

```bash
cd pydantic-ai/
uv sync
./run-cli-agent.sh
```

### Shared MCP Server (optional)

```bash
cd mcp_servers/example/
uv run server.py
# or: ./run-mcp-server.sh
```

## How shared code works

`shared/` is a uv workspace package that exposes a `functions` [namespace package](https://peps.python.org/pep-0420/). Each implementation also has its own `functions/` directory containing `guardrails.py` (the only tool that differs between frameworks). Python 3.3+ namespace packages transparently merge both `functions/` directories at import time — no special import paths needed.

```
import path for 'functions.bash'     → shared/functions/bash.py
import path for 'functions.guardrails' → langgraph/functions/guardrails.py  (or pydantic-ai/)
```

## Comparing the implementations

```bash
# File-level delta between the two implementations
diff -rq --exclude='uv.lock' --exclude='*.pyc' langgraph/ pydantic-ai/
```
