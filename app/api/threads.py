from fastapi import APIRouter, Depends

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
