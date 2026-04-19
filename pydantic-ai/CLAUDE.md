# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the agent (interactive REPL)
./run-cli-agent.sh
LLM_PROVIDER=openai ./run-cli-agent.sh

# Run the agent as an HTTP API
./run-server-api.sh

# Run the MCP server (from mcp_servers/example/)
./mcp_servers/example/run-mcp-server.sh

# Run tests
uv run pytest -s
uv run pytest -s -k <test_name>
```

## Architecture

The project has three entry points: an interactive REPL (`agent.py`), an HTTP API (`server_api.py`), and an optional MCP server (`mcp_servers/example/`).

### Agent (`agent.py`)

An async interactive REPL that:
1. Probes each configured MCP server (skips unreachable ones)
2. Builds a PydanticAI `Agent` via `pydantic_agent.create_agent_with_mcp()`
3. Enters `agent.run_mcp_servers()` context to maintain MCP connections
4. Loops on `input()`, loads thread history from SQLite, streams tokens via `agent.run_stream()`
5. Saves updated history back to SQLite after each turn

### HTTP API (`server_api.py`)

A FastAPI app that wraps the same agent logic:
- `POST /chat` — returns the final agent reply as JSON
- `POST /chat/stream` — streams each token as plain text

The agent and MCP connections are initialised once at startup via FastAPI lifespan and reused across requests.

### LLM Factory (`llm_factory.py`)

Maps the `LLM_PROVIDER` env var to a PydanticAI `OpenAIModel`. Supported providers:
- `ollama` (default) — local Ollama via OpenAI-compatible endpoint
- `openai` — standard OpenAI API

Override the model name with `LLM_MODEL`.

### PydanticAI Agent (`pydantic_agent.py`)

Core agent module. Replaces the former `graph.py` (LangGraph `StateGraph`):
- `build_agent(tools, mcp_urls, human_in_loop)` — creates a `pydantic_ai.Agent` with tools and `MCPServerStreamableHTTP` MCP servers
- `create_agent_with_mcp(human_in_loop)` — probes MCP servers then calls `build_agent`
- Human-in-the-loop: tools are wrapped with `_wrap_hitl()` when `HUMAN_IN_LOOP=true`

### Memory (`memory.py`)

Replaces LangGraph's SQLite checkpointer. Stores per-thread `ModelMessage` lists:
- `load_history(db_path, thread_id)` → `list[ModelMessage]`
- `save_history(db_path, thread_id, messages)` → persists to SQLite via aiosqlite

Messages are serialised with `ModelMessagesTypeAdapter` (JSON).

### Local Tools (`functions/`)

- `functions/machine.py` — filesystem and network tools
- `functions/web.py` — `search` via DuckDuckGo
- `functions/math.py` — `calculate_math_expression` using safe AST evaluation
- `functions/bash.py` — `run_bash` executes shell commands with a 30s timeout and denylist
- `functions/config.py` — `get_local_tools()` returns the full list

**Pattern for adding a local tool:** define a function in the appropriate module, add it to `get_local_tools()` in `functions/config.py`.

### Guardrails (`functions/guardrails.py`)

Applied on every input and output in both the REPL and the HTTP API:

- `validate_input` — blocks prompt injection, adult content, and violence/weapons patterns; enforces max input length
- `is_safe` — LLM-as-judge using a dedicated PydanticAI `Agent`; classifies input as safe/unsafe
- `validate_output` — redacts PII (SSN, email, phone number, credit card) from agent responses
- `run_bash` denylist — blocks dangerous shell commands

### MCP Server (`mcp_servers/example/`)

A FastAPI app that mounts two independent FastMCP sub-apps:

- `/math_mcp` — served by `tools/math_tools.py`
- `/perf-mcp` — served by `tools/perf_tools.py`

The MCP URLs are configured in `mcp_servers/config.py`. Reachability is checked at startup.

### Environment Variables

| Variable             | Default                         | Purpose                                       |
|----------------------|---------------------------------|-----------------------------------------------|
| `LLM_PROVIDER`       | `ollama`                        | LLM backend for the agent (`openai`, `ollama`)|
| `LLM_MODEL`          | _(provider default)_            | Override the model name for the selected provider |
| `OPENAI_API_KEY`     | —                               | Required when using `openai`                  |
| `OLLAMA_BASE_URL`    | `http://localhost:11434/v1`     | Ollama base URL (OpenAI-compatible)           |
| `GUARDRAILS_ENABLED` | `true`                          | Enable input/output guardrails                |
| `HUMAN_IN_LOOP`      | `false`                         | Prompt user to confirm tool calls before exec |
| `LOGFIRE_TOKEN`      | —                               | Enables Logfire tracing when set              |
