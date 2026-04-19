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
1. Attempts to connect to each MCP server listed in `mcp_servers/config.py` (skips unreachable ones)
2. Loads local function tools from `functions/config.py`
3. Builds a LangGraph `StateGraph` with an agent node and a `ToolNode`
4. Loops on `input()` and streams responses via `app.astream`

### HTTP API (`server_api.py`)

A FastAPI app that wraps the same agent logic:
- `POST /chat` — returns the final agent reply as JSON
- `POST /chat/stream` — streams each agent step as plain text

The agent and MCP sessions are initialized once at startup via FastAPI lifespan and reused across requests.

### LLM Factory (`llm_factory.py`)

Maps the `LLM_PROVIDER` env var to the correct LangChain chat model. Supported providers: `ollama` (default, OpenAI-compat), `openai`, `gemini`, `anthropic`, `azure` (Azure OpenAI), `meta` (Llama API, OpenAI-compat), `deepseek` (OpenAI-compat), `mistral`, `xai` (OpenAI-compat), `openrouter`. Each provider has sensible defaults for `temperature` and `max_tokens`. The model name can be overridden via `LLM_MODEL`.

Default models per provider are defined in `_DEFAULT_MODELS`. Override with `LLM_MODEL` at runtime:
```bash
LLM_MODEL=llama3.1 ./run-cli-agent.sh
LLM_PROVIDER=openai LLM_MODEL=gpt-4o python agent.py
```

### Local Tools (`functions/`)

- `functions/machine.py` — filesystem and network tools (`list_files`, `read_file`, `run_df`, `run_du`, `run_hostname`, `run_ifconfig`, `run_netstat`, `get_current_user`)
- `functions/web.py` — `search` via DuckDuckGo
- `functions/math.py` — `calculate_math_expression` using safe AST evaluation (no `eval`)
- `functions/bash.py` — `run_bash` executes shell commands with a 30s timeout and a dangerous command denylist
- `functions/config.py` — `get_local_tools()` returns the full list

**Pattern for adding a local tool:** define a function in the appropriate module, add it to `get_local_tools()` in `functions/config.py`.

### Guardrails (`functions/guardrails.py`)

Applied on every input and output in both the REPL and the HTTP API:

- `validate_input` — blocks prompt injection, adult content, and violence/weapons patterns; enforces max input length
- `is_safe` — LLM-as-judge: a second LLM call classifies the input before the agent processes it; the LLM is instantiated once at module load (`_llm`) and reused across calls
- `validate_output` — redacts PII (SSN, email, phone number, credit card) from agent responses
- `run_bash` denylist — blocks dangerous shell commands (`rm -rf /`, fork bomb, `shutdown`, etc.)

### Memory (`MemorySaver`)

The agent uses LangGraph's `MemorySaver` checkpointer to persist conversation history across turns. Each conversation is identified by a `thread_id`:
- REPL: fixed `thread_id = "repl"` per session
- HTTP API: caller-supplied `thread_id` in the request body (defaults to `"default"`)

### MCP Server (`mcp_servers/example/`)

A FastAPI app that mounts two independent FastMCP sub-apps:

- `/math_mcp` — served by `tools/math_tools.py`
- `/perf-mcp` — served by `tools/perf_tools.py`

Both MCP servers also expose their tools as plain FastAPI REST routes (auto-registered via a loop over the `math_tools` / `perf_tools` lists). The server runs on port `58080`.

**Pattern for adding an MCP tool:** define a private function `_fn(...)`, register it with `mcp.tool()(_fn)`, and append it to the module's `*_tools` list.

### Environment Variables

| Variable             | Default                  | Purpose                                       |
|----------------------|--------------------------|-----------------------------------------------|
| `LLM_PROVIDER`       | `ollama`                 | LLM backend for the agent                     |
| `LLM_MODEL`          | _(provider default)_     | Override the model name for the selected provider |
| `OPENAI_API_KEY`          | —                        | Required when using `openai`                      |
| `GEMINI_API_KEY`          | —                        | Required when using `gemini`                      |
| `ANTHROPIC_API_KEY`       | —                        | Required when using `anthropic`                   |
| `AZURE_OPENAI_API_KEY`    | —                        | Required when using `azure`                       |
| `AZURE_OPENAI_ENDPOINT`   | —                        | Required when using `azure`                       |
| `AZURE_OPENAI_API_VERSION`| `2025-01-01-preview`     | Azure OpenAI API version                          |
| `LLAMA_API_KEY`           | —                        | Required when using `meta`                        |
| `DEEPSEEK_API_KEY`        | —                        | Required when using `deepseek`                    |
| `MISTRAL_API_KEY`         | —                        | Required when using `mistral`                     |
| `XAI_API_KEY`             | —                        | Required when using `xai`                         |
| `OPENROUTER_API_KEY`      | —                        | Required when using `openrouter`                  |
| `GUARDRAILS_ENABLED` | `true`                   | Enable input/output guardrails                |
| `HUMAN_IN_LOOP`      | `false`                  | Prompt user to confirm tool calls before exec |
| `LANGCHAIN_API_KEY`  | —                        | Enables LangSmith tracing when set            |
