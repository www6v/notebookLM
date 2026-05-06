"""Tests for slide deck revise request schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.studio import SlideDeckReviseRequest, SlideDeckSlideEdit


def test_revise_request_rejects_empty_edits():
    with pytest.raises(ValidationError):
        SlideDeckReviseRequest(edits=[])


def test_revise_request_dedupes_last_prompt_wins():
    body = SlideDeckReviseRequest(
        edits=[
            SlideDeckSlideEdit(slide_index=1, prompt="first"),
            SlideDeckSlideEdit(slide_index=1, prompt="second"),
        ]
    )
    assert len(body.edits) == 1
    assert body.edits[0].slide_index == 1
    assert body.edits[0].prompt == "second"


def test_revise_request_rejects_whitespace_only_prompt():
    with pytest.raises(ValidationError):
        SlideDeckReviseRequest(
            edits=[SlideDeckSlideEdit(slide_index=0, prompt="   ")]
        )
