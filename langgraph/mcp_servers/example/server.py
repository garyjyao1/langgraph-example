from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from tools.math_tools import math_tools
from tools.math_tools import mcp as math_mcp
from tools.perf_tools import mcp as perf_mcp
from tools.perf_tools import perf_tools

math_mcp_app = math_mcp.http_app(path="/")
perf_mcp_app = perf_mcp.http_app(path="/")


@asynccontextmanager
async def lifespan(app):
    async with math_mcp_app.lifespan(app):
        async with perf_mcp_app.lifespan(app):
            yield


app = FastAPI(
    title="MCP Server",
    description="MCP Server",
    version="1.0.0-rc.1",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app_name": "langgraph-example",
        "message": "It works on my machine!",
        "endpoints": {
            "docs": "/docs",
            "math_mcp": "/math_mcp",
            "perf_mcp": "/perf-mcp",
        },
    }


# FastAPI routes
for tool_fn in math_tools:
    app.get(f"/{tool_fn.__name__.lstrip('_')}", tags=["math"])(tool_fn)

for tool_fn in perf_tools:
    app.get(f"/{tool_fn.__name__.lstrip('_')}", tags=["perf"])(tool_fn)

app.mount("/math_mcp", math_mcp_app)
app.mount("/perf-mcp", perf_mcp_app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=58080)
