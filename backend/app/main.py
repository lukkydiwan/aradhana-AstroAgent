"""FastAPI entry point — exposes the AstroAgent over HTTP with SSE streaming."""

import json
import os
import uuid
from typing import AsyncIterator, Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.graph import graph
from app.agent.state import BirthDetails

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Aradhana AstroAgent", version="1.0.0")

origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response models ──────────────────────────────────────────────────

class BirthDetailsPayload(BaseModel):
    date: str
    time: str
    place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    birth_details: Optional[BirthDetailsPayload] = None


class SessionResponse(BaseModel):
    session_id: str


# ── In-memory session store for birth details ─────────────────────────────────
# (LangGraph's MemorySaver persists messages; we keep birth details separately
#  because they live outside the message list)

_sessions: dict[str, dict] = {}


def _get_or_create_session(session_id: Optional[str]) -> str:
    sid = session_id or str(uuid.uuid4())
    if sid not in _sessions:
        _sessions[sid] = {"birth_details": None}
    return sid


# ── SSE helpers ────────────────────────────────────────────────────────────────

def _sse(event_type: str, data: dict) -> str:
    payload = json.dumps({"type": event_type, **data})
    return f"data: {payload}\n\n"


async def _stream_agent(session_id: str, message: str, birth_details: Optional[dict]) -> AsyncIterator[str]:
    config = {"configurable": {"thread_id": session_id}}

    # Fetch existing state to preserve message history
    state_snapshot = graph.get_state(config)
    existing_state = state_snapshot.values if state_snapshot else {}

    # Merge birth details (new payload wins over stored)
    stored_birth = _sessions.get(session_id, {}).get("birth_details")
    effective_birth = birth_details or stored_birth
    if birth_details:
        _sessions.setdefault(session_id, {})["birth_details"] = birth_details

    input_state = {
        "messages": [{"role": "user", "content": message}],
        "birth_details": effective_birth,
        "chart_data": existing_state.get("chart_data"),
        "session_id": session_id,
        "step_count": 0,
    }

    token_count = 0

    try:
        async for event in graph.astream_events(input_state, config=config, version="v2"):
            kind = event["event"]
            name = event.get("name", "")

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = getattr(chunk, "content", None)
                if content:
                    if isinstance(content, str):
                        yield _sse("token", {"content": content})
                        token_count += 1
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                yield _sse("token", {"content": block["text"]})
                                token_count += 1

            elif kind == "on_tool_start":
                yield _sse("tool_start", {
                    "tool": name,
                    "input": event["data"].get("input", {}),
                })

            elif kind == "on_tool_end":
                output = event["data"].get("output", {})
                if hasattr(output, "content"):
                    try:
                        output = json.loads(output.content)
                    except Exception:
                        output = str(output.content)
                yield _sse("tool_end", {"tool": name, "output": output})

    except Exception as exc:
        yield _sse("error", {"message": str(exc)})
        return

    # Fallback: if astream_events produced no tokens (e.g. Mistral buffered the
    # whole response), read the final message directly from the checkpoint.
    if token_count == 0:
        try:
            snap = graph.get_state({"configurable": {"thread_id": session_id}})
            if snap:
                msgs = snap.values.get("messages", [])
                for m in reversed(msgs):
                    content = getattr(m, "content", None)
                    if content and isinstance(content, str) and getattr(m, "type", "") == "ai":
                        yield _sse("token", {"content": content})
                        break
        except Exception:
            pass

    yield _sse("done", {})


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/sessions", response_model=SessionResponse)
def create_session():
    sid = str(uuid.uuid4())
    _sessions[sid] = {"birth_details": None}
    return {"session_id": sid}


@app.post("/sessions/{session_id}/birth-details")
def update_birth_details(session_id: str, payload: BirthDetailsPayload):
    _sessions.setdefault(session_id, {})["birth_details"] = payload.model_dump(exclude_none=True)
    return {"status": "updated"}


@app.get("/sessions/{session_id}/messages")
def get_messages(session_id: str):
    config = {"configurable": {"thread_id": session_id}}
    state_snapshot = graph.get_state(config)
    if not state_snapshot:
        return {"messages": []}
    messages = state_snapshot.values.get("messages", [])
    result = []
    for m in messages:
        role = getattr(m, "type", "unknown")
        # LangChain message types: "human" → "user", "ai" → "assistant"
        if role == "human":
            role = "user"
        elif role == "ai":
            role = "assistant"
        elif role == "tool":
            role = "tool"
        content = m.content if isinstance(m.content, str) else json.dumps(m.content)
        result.append({"role": role, "content": content})
    return {"messages": result}


@app.post("/chat")
async def chat(req: ChatRequest):
    session_id = _get_or_create_session(req.session_id)
    birth_details = req.birth_details.model_dump(exclude_none=True) if req.birth_details else None

    return StreamingResponse(
        _stream_agent(session_id, req.message, birth_details),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Session-Id": session_id,
        },
    )
