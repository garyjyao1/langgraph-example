import asyncio
import logging
import os
import signal
import sys
from contextlib import AsyncExitStack
from typing import Optional

import typer
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command
from rich.console import Console

from functions.config import get_local_tools
from functions.guardrails import (
    GuardrailError,
    guardrails_enabled,
    is_safe,
    validate_input,
    validate_output,
)
from graph import build_graph
from mcp_servers import load_mcp_tools_from_servers
from tracing import setup_logging, setup_tracing
from utils import extract_text

logger = logging.getLogger(__name__)
console = Console()

_MAGENTA = "\033[35m"
_GREEN = "\033[32m"
_RESET = "\033[0m"


async def stream_tokens(app, inputs_or_command, config: dict) -> str:
    """Streams tokens from the model and returns the full response."""
    buffer = []
    print(_MAGENTA, end="", flush=True)
    async for event in app.astream_events(inputs_or_command, config=config, version="v2"):
        if event["event"] == "on_chat_model_stream":
            text = extract_text(event["data"]["chunk"].content)
            if text:
                print(text, end="", flush=True)
                buffer.append(text)
    print(_RESET)
    return validate_output("".join(buffer))


async def handle_interrupt(app, config: dict) -> None:
    """Handles human-in-the-loop interrupts: shows pending tool calls and asks for confirmation."""
    state = await app.aget_state(config)
    while state.next:
        last_msg = state.values["messages"][-1]
        console.print("\n[Pending tool calls]", style="yellow bold")
        for tc in last_msg.tool_calls:
            console.print(f"  {tc['name']}({tc['args']})", style="yellow")
        confirm = input("Allow? [y/N] ").strip().lower()
        if confirm == "y":
            await stream_tokens(app, Command(resume=True), config)
        else:
            tool_messages = [
                ToolMessage(content="Tool call rejected by user.", tool_call_id=tc["id"])
                for tc in last_msg.tool_calls
            ]
            await app.aupdate_state(config, {"messages": tool_messages}, as_node="tools")
            await stream_tokens(app, None, config)
        state = await app.aget_state(config)


async def run_repl(thread_id: str, human_in_loop: bool):
    setup_tracing()
    async with AsyncExitStack() as stack:
        checkpointer = await stack.enter_async_context(
            AsyncSqliteSaver.from_conn_string("checkpoints.db")
        )
        mcp_tools = await load_mcp_tools_from_servers(stack)
        interrupt_before = ["tools"] if human_in_loop else []
        app = build_graph(
            get_local_tools() + mcp_tools,
            checkpointer=checkpointer,
            interrupt_before=interrupt_before,
        )

        config = {"configurable": {"thread_id": thread_id}}
        inputs_base = {"user_id": os.getenv("USER", "user"), "session_metadata": {}}
        while True:
            try:
                user_input = input(f"{_GREEN}>{_RESET} ").strip()
            except EOFError:
                break
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye"):
                console.print("See ya!", style="bold")
                break
            if guardrails_enabled():
                try:
                    validate_input(user_input)
                except GuardrailError as e:
                    console.print(f"Blocked: {e}", style="red")
                    continue
                if not await is_safe(user_input):
                    console.print("Blocked: input flagged as unsafe.", style="red")
                    continue
            inputs = {**inputs_base, "messages": [HumanMessage(content=user_input)]}
            await stream_tokens(app, inputs, config)
            await handle_interrupt(app, config)


cli = typer.Typer()


@cli.command()
def chat(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider (ollama, openai, gemini, anthropic, groq, mistral, openrouter, cohere, together, fireworks, deepseek, xai)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override the default model for the selected provider"),
    thread_id: str = typer.Option("repl", "--thread-id", "-t", help="Conversation thread ID for memory persistence"),
    guardrails: bool = typer.Option(True, "--guardrails/--no-guardrails", help="Enable or disable input/output guardrails"),
    human_in_loop: bool = typer.Option(False, "--human-in-loop", "-H", help="Prompt for confirmation before each tool call"),
):
    if provider:
        os.environ["LLM_PROVIDER"] = provider
    if model:
        os.environ["LLM_MODEL"] = model
    if not guardrails:
        os.environ["GUARDRAILS_ENABLED"] = "false"
    if human_in_loop:
        os.environ["HUMAN_IN_LOOP"] = "true"

    def _sigint_handler(sig, frame):
        print("\nSee ya!")
        sys.exit(0)

    signal.signal(signal.SIGINT, _sigint_handler)
    setup_logging()
    console.print(f"Hello {os.getenv('USER', 'user')}! How can I assist you today?", style="bold")
    asyncio.run(run_repl(thread_id=thread_id, human_in_loop=human_in_loop))


if __name__ == "__main__":
    cli()
