"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, mindmaps, notebooks, notes, settings, slide_deck, sources, studio
from app.config import settings as config
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: run startup/shutdown hooks."""
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
app.include_router(settings.router)
app.include_router(notebooks.router)
app.include_router(sources.router)
app.include_router(chat.router)
app.include_router(notes.router)
app.include_router(mindmaps.router)
app.include_router(slide_deck.router)
app.include_router(studio.router)


@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "app": config.app_name}
