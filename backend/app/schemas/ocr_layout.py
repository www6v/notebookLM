"""Schemas for slide image layout OCR API."""

from pydantic import BaseModel, Field


class SlideOcrRegion(BaseModel):
    """A text region in image pixel coordinates."""

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(ge=0)
    h: int = Field(ge=0)
    text: str


class SlideImageLayoutOcrResponse(BaseModel):
    """OCR layout for one slide image."""

    width: int = Field(ge=1)
    height: int = Field(ge=1)
    regions: list[SlideOcrRegion]
