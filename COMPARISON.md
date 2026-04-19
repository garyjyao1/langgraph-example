# Framework Comparison: LangGraph vs PydanticAI

This document compares the two agent implementations in this repository side-by-side.
Both implement the same feature set: local tools, guardrails, conversation memory,
human-in-the-loop, MCP server connections, and a FastAPI HTTP API.

---

## Architecture

| Aspect | LangGraph | PydanticAI |
|---|---|---|
| **Core abstraction** | `StateGraph` with typed nodes and edges | `Agent` object with built-in ReAct loop |
| **Tool registration** | `ToolNode` + `bind_tools()` on the LLM | Pass callables directly to `Agent(tools=[...])` |
| **Agent loop** | Explicit graph: `agent → tools → agent → …` | Built-in loop; no graph definition needed |
| **State model** | Typed dict (`MessagesState`, custom fields) | Message list passed as `message_history` arg |
| **Memory / persistence** | LangGraph checkpointer (SQLite, Redis, …) | Bring your own store; JSON via `ModelMessagesTypeAdapter` |
| **Streaming** | `astream_events(version="v2")` event bus | `async with agent.run_stream() as r: async for chunk in r.stream_text(delta=True)` |
| **Human-in-the-loop** | Native `interrupt_before` graph feature | Tool-level wrapper (confirmation before each call) |
| **MCP support** | `langchain_mcp_adapters` (converts MCP → LangChain tools) | Native `MCPServerStreamableHTTP` inside `Agent` |
| **Type safety** | Message dicts, loose typing | Full Pydantic validation; structured `result_type` for tool outputs |
| **Multi-provider** | Dedicated `langchain-*` packages per provider | Single `openai` client; Ollama via custom `base_url` |

---

## Developer Experience

| Aspect | LangGraph | PydanticAI |
|---|---|---|
| **Dependency surface** | `langchain` + `langgraph` + `langchain-openai` + `langchain-mcp-adapters` + `mcp` + `langgraph-checkpoint-sqlite` (6+ packages) | `pydantic-ai[openai]` + `aiosqlite` (2 packages) |
| **Lines of code (runtime)** | `graph.py` — 65 lines | `pydantic_agent.py` — ~110 lines (includes HITL wrapper) |
| **Adding a new tool** | Define function, add to `get_local_tools()` | Same — no additional glue code |
| **Adding a provider** | New `langchain-<provider>` package + factory entry | Custom `AsyncOpenAI(base_url=...)` client; single package |
| **Debugging tool calls** | LangSmith trace viewer or `astream_events` parsing | `result.all_messages()` returns typed, inspectable list |
| **Observability** | LangSmith (proprietary) | Logfire (open, Pydantic-native) |

---

## Key File Differences

| Concept | LangGraph | PydanticAI |
|---|---|---|
| Agent / graph definition | `graph.py` | `pydantic_agent.py` |
| Memory | _(built into LangGraph checkpointer)_ | `memory.py` |
| LangGraph config | `langgraph.json` | _(not needed)_ |

---

## Streaming

**LangGraph:**
```python
async for event in app.astream_events(inputs, config=config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        yield extract_text(event["data"]["chunk"].content)  # provider-specific
```

**PydanticAI:**
```python
async with agent.run_stream(user_input, message_history=history) as result:
    async for chunk in result.stream_text(delta=True):
        yield chunk  # always a plain str
```

PydanticAI's streaming API is simpler and does not require provider-specific content normalisation.

---

## Memory / Persistence

**LangGraph:**
```python
AsyncSqliteSaver.from_conn_string("checkpoints.db")
# → full graph state (messages + custom fields) checkpointed automatically
# → requires langgraph-checkpoint-sqlite package
```

**PydanticAI:**
```python
# Save
ModelMessagesTypeAdapter.dump_json(result.all_messages())  # → bytes

# Load
messages = ModelMessagesTypeAdapter.validate_json(data)    # → list[ModelMessage]

# ~50 lines total in memory.py; stored via aiosqlite
```

LangGraph's checkpointer is more automatic but couples you to the LangGraph runtime.
PydanticAI requires explicit save/load but uses a plain, portable JSON format.

---

## Human-in-the-Loop

**LangGraph:**
```python
workflow.compile(interrupt_before=["tools"])
# → graph pauses before the ToolNode
# → app.aget_state() / app.aupdate_state() / Command(resume=True)
# → can inspect pending tool_calls and selectively approve
```

**PydanticAI:**
```python
tools = [_wrap_hitl(fn) for fn in tools]
# → each tool wrapped; confirmation prompt fires before the function body
# → simpler code; args visible at confirmation time
```

LangGraph has a more powerful HITL primitive (full state inspection/modification) at the
cost of graph state management. PydanticAI's wrapper is portable and easier to understand.

---

## When to Choose Each

### Choose LangGraph if:
- You need complex, branching agent workflows (parallel branches, conditional retries, multi-agent graphs)
- You need first-class human-in-the-loop with full state inspection and modification
- You are already invested in the LangSmith / LangChain ecosystem
- You need LangGraph Platform for deployment

### Choose PydanticAI if:
- You want a simple, Pythonic API with minimal dependencies
- Type safety and structured outputs are a priority
- You are building a straightforward ReAct agent
- You prefer native MCP support without adapters
- You want Pydantic-native tooling (Logfire, structured output validation)
