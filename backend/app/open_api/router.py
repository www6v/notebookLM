"""Aggregate OpenAPI routers."""

from fastapi import APIRouter

from app.open_api.keys import router as keys_router
from app.open_api.routes import router as open_routes_router

router = APIRouter()
router.include_router(keys_router)
router.include_router(open_routes_router)
