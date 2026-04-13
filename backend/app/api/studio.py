"""Studio API routes."""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["studio"])
