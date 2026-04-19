import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

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

_agent = None
_mcp_ctx = None

_DB_PATH = "checkpoints.db"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent, _mcp_ctx
    setup_tracing()
    human_in_loop = os.environ.get("HUMAN_IN_LOOP", "false").lower() != "false"
    _agent = await create_agent_with_mcp(human_in_loop=human_in_loop)
    async with _agent.run_mcp_servers():
        yield


app = FastAPI(title="pydantic-ai-example", lifespan=lifespan)
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
    return {"message": "It works on my machine!", "name": "pydantic-ai-example"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Returns the final agent reply."""
    await check_guardrails(request.message)
    history = await load_history(_DB_PATH, request.thread_id)
    result = await _agent.run(request.message, message_history=history)
    await save_history(_DB_PATH, request.thread_id, result.all_messages())
    response = result.output
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
        history = await load_history(_DB_PATH, request.thread_id)
        try:
            async with _agent.run_stream(request.message, message_history=history) as result:
                async for chunk in result.stream_text(delta=True):
                    chunk = str(chunk)
                    yield validate_output(chunk) if guardrails_enabled() else chunk
                await save_history(_DB_PATH, request.thread_id, result.all_messages())
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
