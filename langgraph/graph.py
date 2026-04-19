"""
LangGraph agent graph.

Exports `graph` for LangGraph Platform (no checkpointer — the platform provides one).
Use `build_graph` to construct a compiled graph with a custom checkpointer and options.
"""

import logging
from typing import Optional

import httpx
from langchain_core.messages import AIMessage
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from functions.config import get_local_tools
from llm_factory import create_llm

logger = logging.getLogger(__name__)


class AgentState(MessagesState):
    user_id: str
    session_metadata: Optional[dict]


def build_graph(tools: list, *, checkpointer=None, interrupt_before: list = None):
    llm = create_llm().bind_tools(tools)

    async def call_model(state: AgentState):
        try:
            return {"messages": [await llm.ainvoke(state["messages"])]}
        except Exception as e:
            if isinstance(e, httpx.ConnectError) or "connection" in str(e).lower():
                logger.error("Could not connect to LLM: %s", e)
                return {
                    "messages": [
                        AIMessage(content="I am unable to connect to a language model.")
                    ]
                }
            logger.error("Model invocation failed: %s", e)
            return {
                "messages": [
                    AIMessage(content=f"I'm sorry, I encountered an error: {e}")
                ]
            }

    def should_continue(state: AgentState):
        return "tools" if state["messages"][-1].tool_calls else END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before or [],
    )


# For LangGraph Platform — the platform injects its own checkpointer.
# MCP tools are omitted here since they require a separately running MCP server.
graph = build_graph(get_local_tools())
