from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.postgres import PostgresSaver

from app.api.pages import FRONTEND_DIR
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.graph.graph import build_graph

    settings = get_settings()
    with PostgresSaver.from_conn_string(settings.supabase_db_url) as checkpointer:
        checkpointer.setup()
        app.state.rag_app = build_graph(checkpointer=checkpointer)
        yield


app = FastAPI(title="Nexus AI API", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

from app.api import auth, chat, pages, threads  # noqa: E402

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(threads.router)
app.include_router(pages.router)
