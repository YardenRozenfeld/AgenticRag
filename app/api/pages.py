from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["pages"])

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@router.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@router.get("/app")
def serve_chat():
    return FileResponse(FRONTEND_DIR / "chat.html")
