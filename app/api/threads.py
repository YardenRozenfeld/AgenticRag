from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_current_user, supabase_admin

router = APIRouter(tags=["threads"])


@router.get("/threads")
def list_threads(user_id: str = Depends(get_current_user)):
    response = (
        supabase_admin.table("threads")
        .select("thread_id, title, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"threads": response.data}


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    # Verify thread belongs to user (thread_id is prefixed with user_id)
    if not thread_id.startswith(user_id):
        raise HTTPException(status_code=403, detail="Access denied")

    checkpointer = request.app.state.checkpointer
    config = {"configurable": {"thread_id": thread_id}}

    try:
        checkpoint_tuple = await checkpointer.aget_tuple(config)
    except Exception:
        return {"messages": []}

    if not checkpoint_tuple or not checkpoint_tuple.checkpoint:
        return {"messages": []}

    state = checkpoint_tuple.checkpoint
    channel_values = state.get("channel_values", {})
    raw_messages = channel_values.get("messages", [])

    messages = []
    for msg in raw_messages:
        if hasattr(msg, "type") and hasattr(msg, "content"):
            role = "user" if msg.type == "human" else "bot"
            messages.append({"role": role, "content": msg.content})

    return {"messages": messages}
