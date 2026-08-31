"""FastAPI entrypoint: admin API, demo sites, and the built React dashboard."""

from __future__ import annotations

import logging
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.config import settings
from src.bootstrap import init_db
from src.demo_builder import OUTPUT_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("visionkled")

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info(
        "Vision Kled listening on %s:%s (LLM provider=%s)",
        settings.api_host,
        settings.api_port,
        settings.llm_provider,
    )
    yield


def create_app() -> FastAPI:
    """Create the Vision Kled HTTP application."""
    init_db()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    app = FastAPI(
        title="Vision Kled",
        description="Vision Kled by Moetez Khaled",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.mount("/demos", StaticFiles(directory=OUTPUT_DIR, html=True), name="demos")

    if FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="admin")

    return app


app = create_app()
