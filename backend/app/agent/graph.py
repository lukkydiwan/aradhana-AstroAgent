python -c "
content = '''\"\"\"
LangGraph agent graph skeleton -- single agent node, no tools yet.
\"\"\"
import os
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import AstroState
from app.agent.prompts import SYSTEM_PROMPT

_llm = ChatMistralAI(
    model=\"mistral-small-latest\",
    temperature=0.7,
    streaming=True,
    api_key=os.environ.get(\"MISTRAL_API_KEY\"),
)


async def agent_node(state: AstroState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state[\"messages\"]
    response = None
    async for chunk in _llm.astream(messages):
        if response is None:
            response = chunk
        else:
            response = response + chunk
    if response is None:
        from langchain_core.messages import AIMessage
        response = AIMessage(content=\"I could not generate a response.\")
    return {\"messages\": [response], \"step_count\": state.get(\"step_count\", 0) + 1}


def build_graph(checkpointer=None):
    builder = StateGraph(AstroState)
    builder.add_node(\"agent\", agent_node)
    builder.add_edge(START, \"agent\")
    builder.add_edge(\"agent\", END)
    return builder.compile(checkpointer=checkpointer or MemorySaver())


graph = build_graph()
'''
open('backend/app/agent/graph.py', 'w', encoding='utf-8').write(content)
"