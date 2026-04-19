# langgraph-example

[![Build](https://github.com/garyjyao1/langgraph-example/actions/workflows/build.yaml/badge.svg)](https://github.com/garyjyao1/langgraph-example/actions/workflows/build.yaml)

A side-by-side comparison of two Python AI agent frameworks — **LangGraph** and **PydanticAI** — implemented against the same feature set so you can make an informed choice for your own agent.

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

## Quickstart

Each implementation is self-contained with its own `pyproject.toml`. Run `uv sync` inside the relevant directory.

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

## Repository Structure

```
langgraph-example/
├── langgraph/          # LangGraph + LangChain implementation
│   ├── graph.py        # StateGraph definition (the core agent loop)
│   ├── agent.py        # CLI REPL
│   ├── server_api.py   # FastAPI HTTP API
│   ├── llm_factory.py  # LLM provider factory
│   ├── functions/      # Local tools (filesystem, web, math, bash)
│   ├── mcp_servers/    # Optional MCP server connections
│   └── pyproject.toml
├── pydantic-ai/        # PydanticAI implementation
│   ├── pydantic_agent.py  # Agent + MCP + HITL setup
│   ├── memory.py          # SQLite message history
│   ├── agent.py           # CLI REPL
│   ├── server_api.py      # FastAPI HTTP API
│   ├── llm_factory.py     # LLM provider factory
│   ├── functions/         # Local tools (filesystem, web, math, bash)
│   ├── mcp_servers/       # Optional MCP server connections
│   └── pyproject.toml
├── COMPARISON.md       # Detailed framework comparison
└── README.md           # This file
```

## Comparing the Implementations

To see the structural differences directly:

```bash
# File-level diff between the two implementations
diff -rq --exclude='uv.lock' --exclude='*.pyc' langgraph/ pydantic-ai/

# Diff a specific file (e.g. the agent entrypoint)
diff langgraph/agent.py pydantic-ai/agent.py
```

Or open the two folders side-by-side in any IDE (VS Code: right-click folder → "Open in Integrated Terminal", then use the diff view).
