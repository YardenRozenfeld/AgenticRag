from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import supabase_client

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
def signup(body: AuthRequest):
    try:
        response = supabase_client.auth.sign_up(
            {"email": body.email, "password": body.password}
        )
        return {
            "user_id": response.user.id,
            "access_token": response.session.access_token if response.session else None,
            "message": "Signup successful. Check email for confirmation if enabled.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(body: AuthRequest):
    try:
        response = supabase_client.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
        return {
            "user_id": response.user.id,
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
