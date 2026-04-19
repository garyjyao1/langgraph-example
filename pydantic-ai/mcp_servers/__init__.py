"""MCP server connectivity helpers.

Returns reachable ``MCPServerStreamableHTTP`` URLs; the actual
``MCPServerStreamableHTTP`` objects are created inside ``pydantic_agent.py``
so the agent's lifetime owns the connection context.
"""

import logging

import httpx
from rich.console import Console

_MCP_SERVERS = [
    {"url": "http://localhost:58080/math_mcp/"},
    {"url": "http://localhost:58080/perf-mcp/"},
]

logger = logging.getLogger(__name__)
console = Console()


async def get_reachable_mcp_urls() -> list[str]:
    """Returns a list of MCP server URLs that are currently reachable."""
    reachable: list[str] = []
    async with httpx.AsyncClient() as client:
        for mcp in _MCP_SERVERS:
            url = mcp["url"]
            try:
                await client.get(url, timeout=2.0)
                reachable.append(url)
                logger.info("Connected to MCP: %s", url)
                console.print(f"Connected to MCP server: {url}", style="green")
            except Exception:
                logger.warning("MCP server not reachable, skipping: %s", url)
    return reachable
