import logging
from contextlib import AsyncExitStack

import httpx
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from rich.console import Console

from mcp_servers.config import mcp_servers

logger = logging.getLogger(__name__)
console = Console()


async def load_mcp_tools_from_servers(stack: AsyncExitStack) -> list:
    tools = []
    async with httpx.AsyncClient() as client:
        for mcp in mcp_servers:
            url = mcp["url"]
            try:
                await client.get(url, timeout=2)
            except Exception:
                logger.warning("MCP server not reachable, skipping: %s", url)
                continue
            try:
                read, write, _ = await stack.enter_async_context(
                    streamable_http_client(url)
                )
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                tools.extend(await load_mcp_tools(session))
                logger.info("Connected to MCP: %s", url)
                console.print(f"Connected to MCP server: {url}", style="green")
            except Exception as e:
                logger.warning("Could not connect to %s: %s", url, e)
    return tools
