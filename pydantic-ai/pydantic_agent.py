"""PydanticAI agent factory.

Replaces ``graph.py`` (LangGraph ``StateGraph``/``ToolNode``) with a
PydanticAI ``Agent`` that supports local function tools, MCP servers, and an
optional human-in-the-loop confirmation wrapper.
"""

import asyncio
import functools
import inspect
import logging
import os

import httpx
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from rich.console import Console

from functions.config import get_local_tools
from llm_factory import create_model
from mcp_servers.config import mcp_servers as _mcp_server_configs

logger = logging.getLogger(__name__)
console = Console()

_SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "Use the available tools whenever they help answer the user's request. "
    "Be concise and accurate."
)


# ---------------------------------------------------------------------------
# Human-in-the-loop tool wrapper
# ---------------------------------------------------------------------------

def _wrap_hitl(fn):
    """Returns a version of *fn* that asks for console confirmation first."""

    @functools.wraps(fn)
    async def async_wrapper(*args, **kwargs):
        _print_pending(fn.__name__, args, kwargs)
        if _confirm():
            if inspect.iscoroutinefunction(fn):
                return await fn(*args, **kwargs)
            return fn(*args, **kwargs)
        return "Tool call rejected by user."

    @functools.wraps(fn)
    def sync_wrapper(*args, **kwargs):
        _print_pending(fn.__name__, args, kwargs)
        if _confirm():
            return fn(*args, **kwargs)
        return "Tool call rejected by user."

    return async_wrapper if inspect.iscoroutinefunction(fn) else sync_wrapper


def _print_pending(name: str, args, kwargs) -> None:
    parts = [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
    console.print(f"\n[Pending tool call] {name}({', '.join(parts)})", style="yellow bold")


def _confirm() -> bool:
    return input("Allow? [y/N] ").strip().lower() == "y"


# ---------------------------------------------------------------------------
# MCP server helpers
# ---------------------------------------------------------------------------

async def _reachable_mcp_urls() -> list[str]:
    """Probes each configured MCP server and returns the reachable URLs."""
    reachable: list[str] = []
    async with httpx.AsyncClient() as client:
        for cfg in _mcp_server_configs:
            url = cfg["url"]
            try:
                await client.get(url, timeout=2.0)
                reachable.append(url)
                console.print(f"Connected to MCP server: {url}", style="green")
            except Exception:
                logger.warning("MCP server not reachable, skipping: %s", url)
    return reachable


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def build_agent(
    tools: list | None = None,
    mcp_urls: list[str] | None = None,
    human_in_loop: bool = False,
) -> Agent:
    """Builds and returns a PydanticAI ``Agent``.

    Args:
        tools: Local callable tools to register (defaults to ``get_local_tools()``).
        mcp_urls: Reachable MCP server URLs (``MCPServerStreamableHTTP`` objects
            are created for each URL).
        human_in_loop: When ``True`` every tool is wrapped with a confirmation prompt.
    """
    if tools is None:
        tools = get_local_tools()

    if human_in_loop:
        tools = [_wrap_hitl(t) for t in tools]

    mcp_servers = [MCPServerStreamableHTTP(url) for url in (mcp_urls or [])]

    return Agent(
        model=create_model(),
        tools=tools,
        mcp_servers=mcp_servers,
        system_prompt=_SYSTEM_PROMPT,
    )


async def create_agent_with_mcp(human_in_loop: bool = False) -> Agent:
    """Probes MCP servers, then returns a fully configured ``Agent``."""
    mcp_urls = await _reachable_mcp_urls()
    return build_agent(mcp_urls=mcp_urls, human_in_loop=human_in_loop)
