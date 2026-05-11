"""FastAPI application entry point."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.logging_setup import configure_logging

configure_logging()

from app.api import (
    auth,
    chat,
    deep_research,
    discover,
    notebooks,
    notes,
    oauth,
    ocr_layout,
    payment,
    public_config,
    public_discover,
    settings,
    share_read,
    sources,
    studio,
    task_events,
)
from app.api.studio import (
    infographics,
    mindmaps,
    podcasts,
    reports,
    slide_deck,
)
from notebooklm_shared.config import settings as config
from notebooklm_shared.database import init_db
from app.services.infra.runtime_dependency_service import collect_dependency_status


def _init_langfuse_env():
    """Set Langfuse env vars from config so @observe() and SDK use them."""
    if config.langfuse_public_key and config.langfuse_secret_key:
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", config.langfuse_public_key)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", config.langfuse_secret_key)
        os.environ.setdefault("LANGFUSE_HOST", config.langfuse_host)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: run startup/shutdown hooks."""
    _init_langfuse_env()
    await init_db()
    yield


app = FastAPI(
    title=config.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(public_config.router)
app.include_router(public_discover.router)
app.include_router(discover.router)
app.include_router(settings.router)
app.include_router(notebooks.router)
app.include_router(share_read.router)
app.include_router(ocr_layout.router)
app.include_router(sources.router)
app.include_router(chat.router)
app.include_router(notes.router)
app.include_router(mindmaps.router)
app.include_router(slide_deck.router)
app.include_router(infographics.router)
app.include_router(reports.router)
app.include_router(podcasts.router)
app.include_router(deep_research.router)
app.include_router(studio.router)
app.include_router(payment.router)
app.include_router(task_events.router)


@app.get("/api/health/live")
async def live_health_check():
    """Liveness probe for process-level health."""
    return {"status": "ok", "app": config.app_name}


@app.get("/api/health/ready")
async def readiness_health_check():
    """Readiness probe with dependency checks for traffic gating."""
    status_summary = await collect_dependency_status()
    if status_summary["ready"]:
        return {"status": "ready", "app": config.app_name, **status_summary}
    return JSONResponse(
        status_code=503,
        content={"status": "degraded", "app": config.app_name, **status_summary},
    )


@app.get("/api/health")
async def health_check():
    """Compatibility health endpoint with dependency summary."""
    status_summary = await collect_dependency_status()
    response_status = "ok" if status_summary["ready"] else "degraded"
    return {"status": response_status, "app": config.app_name, **status_summary}
