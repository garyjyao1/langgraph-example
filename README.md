# pydantic-ai-example

[![Build](https://github.com/jecklgamis/langgraph-example/actions/workflows/build.yaml/badge.svg)](https://github.com/jecklgamis/langgraph-example/actions/workflows/build.yaml)

A PydanticAI agent with local function tools, guardrails, conversation memory, human-in-the-loop, and MCP server connections.

> **Migrated from LangGraph** — see [Framework Comparison](#framework-comparison-langgraph-vs-pydanticai) below.

## Features

- Local tools: filesystem, network, web search, math, bash
- MCP server connections (math, perf) via `pydantic_ai.mcp.MCPServerStreamableHTTP`
- Configurable LLM providers: **Ollama** (default, OpenAI-compatible) and **OpenAI**
- Conversation memory via SQLite (`memory.py`) — per-thread message history
- Guardrails: input validation, LLM-as-judge, output PII redaction, bash command denylist
- Human-in-the-loop tool call confirmation (tool-level wrapper)
- Graceful error handling for LLM connection failures
- HTTP API via FastAPI with streaming support
- Playground UI at `/playground`
- React frontend under `frontend/`
- Logfire tracing support

## Getting Started

```bash
uv sync
./run-cli-agent.sh
```

For OpenAI:

```bash
export OPENAI_API_KEY=your-api-key
./run-cli-agent.sh --provider openai
```

## HTTP API

```bash
./run-server-api.sh

# Single response
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what is 2 + 2?", "thread_id": "session-1"}'

# Streaming response
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "list files in /tmp", "thread_id": "session-1"}'
```

Use the same `thread_id` across requests to maintain conversation history.

## React Frontend

```bash
./frontend/run-frontend.sh   # http://localhost:5173
```

Requires `server_api.py` running on port 8000. Vite proxies `/chat` to the backend automatically.

## MCP Servers

```bash
./mcp_servers/example/run-mcp-server.sh
./run-cli-agent.sh
```

## Environment Variables

| Variable             | Default                         | Purpose                                                  |
|----------------------|---------------------------------|----------------------------------------------------------|
| `LLM_PROVIDER`       | `ollama`                        | LLM backend (`openai` or `ollama`)                       |
| `LLM_MODEL`          | _(provider default)_            | Override model name                                      |
| `OPENAI_API_KEY`     | —                               | Required for `openai`; default model: `gpt-4.1-nano`     |
| `OLLAMA_BASE_URL`    | `http://localhost:11434/v1`     | Ollama endpoint (default model: `llama3.2`)              |
| `GUARDRAILS_ENABLED` | `true`                          | Enable input/output guardrails                           |
| `HUMAN_IN_LOOP`      | `false`                         | Prompt user to confirm tool calls before exec            |
| `LOGFIRE_TOKEN`      | —                               | Enables Logfire tracing when set                         |

---

## Framework Comparison: LangGraph vs PydanticAI

### Architecture

| Aspect | LangGraph | PydanticAI |
|---|---|---|
| **Core abstraction** | `StateGraph` with nodes/edges | `Agent` object |
| **Tool registration** | `ToolNode` + `bind_tools()` on the LLM | Pass callables directly to `Agent(tools=[...])` |
| **Agent loop** | Explicit graph: `agent → tools → agent → …` | Built-in ReAct loop; no graph definition needed |
| **State model** | Typed dict (`MessagesState`, custom fields) | Message list passed as `message_history` arg |
| **Memory / persistence** | LangGraph checkpointer (SQLite, Redis, etc.) | Bring your own store; messages serialised to JSON via `ModelMessagesTypeAdapter` |
| **Streaming** | `astream_events(version="v2")` event bus | `async with agent.run_stream() as r: async for chunk in r.stream_text(delta=True)` |
| **Human-in-the-loop** | Native `interrupt_before` graph feature | Tool-level wrapper (confirmation before each call) |
| **MCP support** | `langchain_mcp_adapters` (converts MCP → LangChain tools) | Native `MCPServerStreamableHTTP` in `Agent` |
| **Type safety** | Message dicts, loose typing | Full Pydantic validation; structured `result_type` for tool outputs |
| **Multi-provider** | Dedicated `langchain-*` packages per provider | Single `openai`-package client; Ollama via custom `base_url` |

### Developer Experience

| Aspect | LangGraph | PydanticAI |
|---|---|---|
| **Dependency surface** | `langchain` + `langgraph` + `langchain-openai` + `langchain-mcp-adapters` + `mcp` + `langgraph-checkpoint-sqlite` (6+ packages) | `pydantic-ai[openai]` + `aiosqlite` (2 packages) |
| **Lines of code (runtime)** | `graph.py` 65 lines | `pydantic_agent.py` ~110 lines (includes HITL wrapper) |
| **Adding a new tool** | Define function, add to `get_local_tools()` | Same – no additional glue code needed |
| **Adding a provider** | New `langchain-<provider>` package + factory entry | Custom `AsyncOpenAI(base_url=...)` client; single package |
| **Debugging tool calls** | LangSmith trace viewer or `astream_events` parsing | `result.all_messages()` returns typed, inspectable list |
| **Observability** | LangSmith (proprietary) | Logfire (open, Pydantic-native) |

### Streaming Comparison

```
LangGraph:
  app.astream_events(inputs, config=config, version="v2")
  → filter on event["event"] == "on_chat_model_stream"
  → extract_text(event["data"]["chunk"].content)   # provider-specific normalisation

PydanticAI:
  async with agent.run_stream(user_input, message_history=history) as result:
      async for chunk in result.stream_text(delta=True):
          yield chunk   # always a plain str
```

PydanticAI's streaming API is significantly simpler and does not require provider-specific content normalisation.

### Memory / Persistence Comparison

```
LangGraph:
  AsyncSqliteSaver.from_conn_string("checkpoints.db")
  → full graph state (messages + custom fields) checkpointed automatically
  → requires langgraph-checkpoint-sqlite package

PydanticAI:
  result.all_messages() → list[ModelMessage]
  ModelMessagesTypeAdapter.dump_json(messages) → bytes   (save)
  ModelMessagesTypeAdapter.validate_json(data) → list    (load)
  → stored in SQLite via aiosqlite; ~50 lines total (memory.py)
```

LangGraph's checkpointer is more automatic but couples you to the LangGraph runtime. PydanticAI requires explicit save/load but uses a plain, portable JSON format.

### Human-in-the-Loop Comparison

```
LangGraph:
  workflow.compile(interrupt_before=["tools"])
  → graph pauses before the ToolNode
  → app.aget_state() / app.aupdate_state() / Command(resume=True)
  → rich: can inspect pending tool_calls, selectively approve

PydanticAI:
  tools = [_wrap_hitl(fn) for fn in tools]
  → each tool is wrapped; confirmation prompt fires before the function body
  → simpler code; less precise (can't preview args before the tool is scheduled)
```

LangGraph has a more powerful HITL primitive at the cost of graph state management. PydanticAI's wrapper approach is portable but limited to per-call approval.

### When to Choose Each

**Choose LangGraph if:**
- You need complex, branching agent workflows (parallel branches, conditional retries, multi-agent graphs)
- You need first-class human-in-the-loop with full state inspection/modification
- You are already invested in the LangSmith/LangChain ecosystem
- You need LangGraph Platform deployment

**Choose PydanticAI if:**
- You want a simple, Pythonic API with minimal dependencies
- Type safety and structured outputs are priorities
- You are building a straightforward ReAct agent
- You prefer native MCP support without adapters
- You want Pydantic-native tooling (Logfire, structured output validation)
