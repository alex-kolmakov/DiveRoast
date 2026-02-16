import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import get_or_create_session, get_session
from src.api.models import ChatRequest

router = APIRouter()


@router.post("/api/chat")
async def chat(request: ChatRequest):
    """Send a message and receive a streaming SSE response."""
    session_id = request.session_id
    existing = get_session(session_id)

    if existing is not None:
        agent = existing
    else:
        session_id, agent = get_or_create_session(session_id)

    async def event_generator():
        try:
            async for chunk in agent.chat_stream(request.message):
                yield {"event": "message", "data": json.dumps({"content": chunk})}
            yield {"event": "done", "data": json.dumps({"status": "complete"})}
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(event_generator())
