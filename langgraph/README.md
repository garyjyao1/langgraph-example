# langgraph-example

[![Build](https://github.com/jecklgamis/langgraph-example/actions/workflows/build.yaml/badge.svg)](https://github.com/jecklgamis/langgraph-example/actions/workflows/build.yaml)

A LangGraph agent with local function tools, guardrails, memory, human-in-the-loop, and optional MCP server connections.

## Features

- Local tools: filesystem, network, web search, math, bash
- Optional MCP server connections (math, perf)
- Configurable LLM providers: Ollama (default), OpenAI, Google Gemini, Anthropic, Microsoft Azure, Meta, DeepSeek, Mistral, xAI, OpenRouter
- Conversation memory via LangGraph checkpointing (SQLite)
- Guardrails: input validation, LLM-as-judge, output PII redaction, bash command denylist
- Human-in-the-loop tool call confirmation
- Graceful error handling for LLM connection failures
- HTTP API via FastAPI with streaming support
- Playground UI at `/playground`
- React frontend under `frontend/`
- LangSmith tracing support

## Getting Started

```bash
uv sync
./run-cli-agent.sh
```

For a different LLM provider:

```bash
export GEMINI_API_KEY=your-api-key
./run-cli-agent.sh --provider gemini
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

| Variable             | Default              | Purpose                                           |
|----------------------|----------------------|---------------------------------------------------|
| `LLM_PROVIDER`       | `ollama`             | LLM backend (see providers below) |
| `LLM_MODEL`          | _(provider default)_ | Override model name (see defaults below)          |
| `OPENAI_API_KEY`          | —                    | Required for `openai`; default model: `gpt-4.1-nano` |
| `GEMINI_API_KEY`          | —                    | Required for `gemini`; default model: `gemini-2.5-flash` |
| `ANTHROPIC_API_KEY`       | —                    | Required for `anthropic`; default model: `claude-sonnet-4-6` |
| `AZURE_OPENAI_API_KEY`    | —                    | Required for `azure`; default model: `gpt-4o` |
| `AZURE_OPENAI_ENDPOINT`   | —                    | Required for `azure`; your Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_VERSION`| `2025-01-01-preview` | Azure OpenAI API version |
| `LLAMA_API_KEY`           | —                    | Required for `meta`; default model: `Llama-4-Scout-17B-16E-Instruct` |
| `DEEPSEEK_API_KEY`        | —                    | Required for `deepseek`; default model: `deepseek-chat` |
| `MISTRAL_API_KEY`         | —                    | Required for `mistral`; default model: `mistral-large-latest` |
| `XAI_API_KEY`             | —                    | Required for `xai`; default model: `grok-3-mini` |
| `OPENROUTER_API_KEY`      | —                    | Required for `openrouter`; default model: `openrouter/auto` |
| `GUARDRAILS_ENABLED` | `true`               | Enable input/output guardrails                    |
| `HUMAN_IN_LOOP`      | `false`              | Prompt user to confirm tool calls before exec     |
| `LANGCHAIN_API_KEY`  | —                    | Enables LangSmith tracing when set                |
