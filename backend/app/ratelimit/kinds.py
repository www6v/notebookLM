"""Generation content kinds for rate limiting (aligned with Studio APIs)."""

from __future__ import annotations

from enum import Enum


class GenerationKind(str, Enum):
    """One value per Studio generation surface."""

    REPORT = "report"
    SLIDE_DECK = "slide_deck"
    PODCAST = "podcast"
    MINDMAP = "mindmap"
    INFOGRAPHIC = "infographic"
    DEEP_RESEARCH = "deep_research"
