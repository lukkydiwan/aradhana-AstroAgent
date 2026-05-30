"""
LangGraph agent graph for the AstroAgent.

Graph topology:
  START → agent → tools (conditional) → agent → … → END

The agent node (Mistral) reasons with bound tools. If it emits tool calls,
the ToolNode executes them and the output loops back to the agent. When
the model produces a final response (no tool calls), the graph exits.

A step-budget guard prevents infinite loops.
"""

import os
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import AstroState
from app.agent.prompts import SYSTEM_PROMPT
from app.tools.geocode import geocode_place
from app.tools.birth_chart import compute_birth_chart
from app.tools.transits import get_daily_transits
from app.tools.knowledge import knowledge_lookup

MAX_STEPS = 10

TOOLS = [geocode_place, compute_birth_chart, get_daily_transits, knowledge_lookup]

_llm = ChatMistralAI(
    model="mistral-small-latest",
    temperature=0.7,
    streaming=True,
    api_key=os.environ.get("MISTRAL_API_KEY"),
)
_llm_with_tools = _llm.bind_tools(TOOLS)


async def agent_node(state: AstroState) -> dict:
    import json
    step = state.get("step_count", 0)
    if step >= MAX_STEPS:
        from langchain_core.messages import AIMessage
        return {
            "messages": [AIMessage(content=(
                "I've reached my reasoning limit for this response. "
                "Please try rephrasing your question."
            ))],
            "step_count": step + 1,
        }

    birth = state.get("birth_details") or {}
    context_lines = []
    if birth:
        context_lines.append(
            f"User birth details on file: {birth.get('date', '?')} "
            f"{birth.get('time', '?')} at {birth.get('place', '?')} "
            f"(lat={birth.get('latitude', '?')}, lon={birth.get('longitude', '?')}, "
            f"tz={birth.get('timezone', '?')})."
        )
    if state.get("chart_data"):
        context_lines.append("Natal chart has already been computed this session.")

    system_content = SYSTEM_PROMPT
    if context_lines:
        system_content += "\n\n═══ SESSION CONTEXT ═══\n" + "\n".join(context_lines)

    messages = [SystemMessage(content=system_content)] + state["messages"]

    # Use astream (not ainvoke) so every token fires on_chat_model_stream
    # callbacks reliably — ainvoke can silently buffer with some Mistral versions.
    response = None
    async for chunk in _llm_with_tools.astream(messages):
        if response is None:
            response = chunk
        else:
            try:
                response = response + chunk
            except Exception:
                pass  # accumulation failed; keep last complete chunk
    if response is None:
        from langchain_core.messages import AIMessage
        response = AIMessage(content="I had trouble generating a response. Please try again.")

    updates: dict = {
        "messages": [response],
        "step_count": step + 1,
    }

    # Cache chart data if a compute_birth_chart tool result is in the message history
    for tool_msg in state["messages"]:
        if hasattr(tool_msg, "name") and tool_msg.name == "compute_birth_chart":
            try:
                chart = json.loads(tool_msg.content) if isinstance(tool_msg.content, str) else tool_msg.content
                if isinstance(chart, dict) and "planets" in chart:
                    updates["chart_data"] = chart
            except Exception:
                pass

    return updates


def _step_guard(state: AstroState):
    """Route to tools if there are tool calls, else END (same as tools_condition but respects budget)."""
    if state.get("step_count", 0) >= MAX_STEPS:
        return END
    return tools_condition(state)


def build_graph(checkpointer=None):
    builder = StateGraph(AstroState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", _step_guard, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")

    return builder.compile(checkpointer=checkpointer or MemorySaver())


# Module-level graph with in-memory checkpointing (one instance per process)
graph = build_graph()
