import asyncio
import logging
import os
import signal
import sys
from typing import Optional

import typer
from rich.console import Console

from functions.guardrails import (
    GuardrailError,
    guardrails_enabled,
    is_safe,
    validate_input,
    validate_output,
)
from memory import load_history, save_history
from pydantic_agent import create_agent_with_mcp
from tracing import setup_logging, setup_tracing

logger = logging.getLogger(__name__)
console = Console()

_MAGENTA = "\033[35m"
_GREEN = "\033[32m"
_RESET = "\033[0m"

_DB_PATH = "checkpoints.db"


async def stream_response(agent, user_input: str, history: list) -> tuple[str, list]:
    """Streams agent output token-by-token and returns (full_text, updated_history)."""
    buffer: list[str] = []
    print(_MAGENTA, end="", flush=True)
    async with agent.run_stream(user_input, message_history=history) as result:
        async for chunk in result.stream_text(delta=True):
            chunk = str(chunk)
            print(chunk, end="", flush=True)
            buffer.append(chunk)
        new_history = result.all_messages()
    print(_RESET)
    return validate_output("".join(buffer)), new_history


async def run_repl(thread_id: str, human_in_loop: bool):
    setup_tracing()
    agent = await create_agent_with_mcp(human_in_loop=human_in_loop)

    async with agent.run_mcp_servers():
        config_base = {"user_id": os.getenv("USER", "user"), "session_metadata": {}}
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

            history = await load_history(_DB_PATH, thread_id)
            try:
                response, new_history = await stream_response(agent, user_input, history)
                await save_history(_DB_PATH, thread_id, new_history)
            except Exception as e:
                if "connection" in str(e).lower():
                    logger.error("Could not connect to LLM: %s", e)
                    console.print("I am unable to connect to a language model.", style="red")
                else:
                    logger.error("Model invocation failed: %s", e)
                    console.print(f"I'm sorry, I encountered an error: {e}", style="red")


cli = typer.Typer()


@cli.command()
def chat(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider (openai, ollama)"),
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
