import json
import logging
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import get_current_user, supabase_admin
from app.cache import get_semantic_cache

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str
    thread_id: str | None = None


@router.post("/chat")
async def chat(body: ChatRequest, request: Request, user_id: str = Depends(get_current_user)):
    thread_id = body.thread_id or f"{user_id}-{uuid.uuid4()}"
    is_new_thread = body.thread_id is None

    # Check semantic cache
    cache = get_semantic_cache()
    cached_response = cache.lookup(body.question) if cache else None

    if cached_response:
        _save_thread(is_new_thread, user_id, thread_id, body.question)
        return {"answer": cached_response, "thread_id": thread_id, "cached": True}

    # Stream response via SSE
    async def event_stream():
        config = {"configurable": {"thread_id": thread_id}}
        full_answer = ""

        async for event in request.app.state.rag_app.astream_events(
            {"question": body.question}, config=config, version="v2"
        ):
            kind = event.get("event")
            if kind == "on_chat_model_stream":
                # Only stream tokens from the generation node
                tags = event.get("tags", [])
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    token = chunk.content
                    full_answer += token
                    yield f"data: {json.dumps({'token': token})}\n\n"

        # Store in cache
        if cache and full_answer:
            try:
                cache.store(body.question, full_answer)
            except Exception:
                logger.warning("Failed to store cache entry", exc_info=True)

        _save_thread(is_new_thread, user_id, thread_id, body.question)

        yield f"data: {json.dumps({'done': True, 'thread_id': thread_id, 'answer': full_answer})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _save_thread(is_new_thread: bool, user_id: str, thread_id: str, question: str):
    if is_new_thread:
        title = question[:80]
        try:
            supabase_admin.table("threads").insert(
                {
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "title": title,
                }
            ).execute()
        except Exception:
            pass
