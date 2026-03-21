from fastapi import Header, HTTPException
from supabase import create_client

from app.config import get_settings

settings = get_settings()

supabase_client = create_client(settings.supabase_url, settings.supabase_anon_key)
supabase_admin = create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_current_user(authorization: str = Header(...)) -> str:
    """Validate the Supabase JWT and return the user_id."""
    token = authorization.replace("Bearer ", "")
    try:
        response = supabase_client.auth.get_user(token)
        return response.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
