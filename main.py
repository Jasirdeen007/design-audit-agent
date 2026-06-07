"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from api.routes import router, set_llm_client
from api.routes_l2 import router_l2, set_llm_client_l2
from core.llm_client import LLMClient
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Design Audit Agent starting up...")
    client = LLMClient()
    set_llm_client(client)
    set_llm_client_l2(client)
    logger.info("Startup complete", extra={"provider": client.provider, "model": client.model})
    yield
    logger.info("Design Audit Agent shutting down.")


app = FastAPI(
    title="Design Audit Agent",
    description="Level 1 single-screenshot audits and Level 2 before/after design diff analysis.",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1", tags=["Design Audit - Level 1"])
app.include_router(router_l2, prefix="/api/v1", tags=["Design Audit - Level 2"])


@app.get("/")
async def root() -> dict:
    return {
        "agent": "Design Audit Agent",
        "level": 1,
        "docs": "/docs",
        "ui": "/ui",
        "health": "/api/v1/health",
        "analyze": "POST /api/v1/analyze",
        "compare": "POST /api/v1/compare",
    }


@app.get("/ui", response_class=HTMLResponse)
async def upload_ui() -> HTMLResponse:
    from pathlib import Path

    html = (Path(__file__).parent / "templates" / "upload.html").read_text(encoding="utf-8")
    return HTMLResponse(html)
