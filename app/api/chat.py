import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.api.deps import get_current_user, supabase_admin

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    thread_id: str | None = None


@router.post("/chat")
def chat(body: ChatRequest, request: Request, user_id: str = Depends(get_current_user)):
    thread_id = body.thread_id or f"{user_id}-{uuid.uuid4()}"
    is_new_thread = body.thread_id is None

    config = {"configurable": {"thread_id": thread_id}}
    result = request.app.state.rag_app.invoke({"question": body.question}, config=config)

    if is_new_thread:
        title = body.question[:80]
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

    return {
        "answer": result["generation"],
        "thread_id": thread_id,
    }
