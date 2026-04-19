import logging
import os
from contextlib import AsyncExitStack, asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pydantic import BaseModel

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

_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent
    setup_tracing()
    async with AsyncExitStack() as stack:
        checkpointer = await stack.enter_async_context(
            AsyncSqliteSaver.from_conn_string("checkpoints.db")
        )
        mcp_tools = await load_mcp_tools_from_servers(stack)
        human_in_loop = os.environ.get("HUMAN_IN_LOOP", "false").lower() != "false"
        interrupt_before = ["tools"] if human_in_loop else []
        _agent = build_graph(
            get_local_tools() + mcp_tools,
            checkpointer=checkpointer,
            interrupt_before=interrupt_before,
        )
        yield


app = FastAPI(title="langgraph-example", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    user_id: str = "anonymous"
    session_metadata: dict = {}


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    user_id: str


async def check_guardrails(message: str) -> None:
    if not guardrails_enabled():
        return
    try:
        validate_input(message)
    except GuardrailError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not await is_safe(message):
        raise HTTPException(status_code=400, detail="Input flagged as unsafe.")


@app.get("/")
async def root():
    return {"message": "It works on my machine!", "name": "langgraph-example"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Returns the final agent reply."""
    await check_guardrails(request.message)
    inputs = {
        "messages": [HumanMessage(content=request.message)],
        "user_id": request.user_id,
        "session_metadata": request.session_metadata,
    }
    config = {"configurable": {"thread_id": request.thread_id}}
    result = await _agent.ainvoke(inputs, config=config)
    response = extract_text(result["messages"][-1].content)
    return ChatResponse(
        response=validate_output(response) if guardrails_enabled() else response,
        thread_id=request.thread_id,
        user_id=request.user_id,
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streams tokens as they are generated."""
    await check_guardrails(request.message)

    async def generate():
        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": request.user_id,
            "session_metadata": request.session_metadata,
        }
        config = {"configurable": {"thread_id": request.thread_id}}
        try:
            async for event in _agent.astream_events(inputs, config=config, version="v2"):
                if event["event"] == "on_chat_model_stream":
                    content = extract_text(event["data"]["chunk"].content)
                    if content:
                        yield validate_output(content) if guardrails_enabled() else content
        except Exception as e:
            logger.error("Stream error: %s", e)
            yield f"\n[Error: {e}]"

    return StreamingResponse(generate(), media_type="text/plain")


@app.get("/playground")
async def playground(request: Request):
    """Simple chat playground UI."""
    return templates.TemplateResponse(request, "playground.html")


if __name__ == "__main__":
    setup_logging()
    uvicorn.run(app, host="0.0.0.0", port=8000)
