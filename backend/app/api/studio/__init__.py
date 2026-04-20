"""Studio HTTP API package (mindmaps, slides, infographics, reports, podcasts)."""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["studio"])
