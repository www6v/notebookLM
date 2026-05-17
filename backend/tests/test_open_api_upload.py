"""Tests for OpenAPI file upload (create_media / confirm_source_upload)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.open_api.errors import OpenApiBizError, PARAM_ERROR
from app.open_api.source_upload import (
    build_cos_credential,
    parse_upload_file,
    verify_cos_object_uploaded,
)


def test_parse_upload_file_pdf():
    parsed = parse_upload_file(
        "report.pdf",
        1024,
        "application/pdf",
        "pdf",
    )
    assert parsed.file_name == "report.pdf"
    assert parsed.source_type == "pdf"
    assert parsed.file_ext == "pdf"


def test_parse_upload_file_rejects_unknown_ext():
    with pytest.raises(OpenApiBizError) as exc:
        parse_upload_file("x.xyz", 100, "application/octet-stream", "xyz")
    assert exc.value.code == PARAM_ERROR


@patch("app.open_api.source_upload.generate_presigned_put_url")
@patch("app.open_api.source_upload.cos_bucket_region")
def test_build_cos_credential_includes_presigned(mock_region, mock_presign):
    mock_region.return_value = ("my-bucket", "ap-shanghai")
    mock_presign.return_value = "https://my-bucket.cos.ap-shanghai.myqcloud.com/k?sign=1"
    cred = build_cos_credential("prefix/sources/ab_report.pdf", "application/pdf")
    assert cred["cos_key"] == "prefix/sources/ab_report.pdf"
    assert cred["presigned_put_url"].startswith("https://")
    assert cred["bucket_name"] == "my-bucket"
    assert cred["region"] == "ap-shanghai"
    assert cred["secret_id"] == ""


@patch("app.open_api.source_upload.cos_object_exists", return_value=False)
def test_verify_cos_object_missing(_mock_exists):
    with pytest.raises(OpenApiBizError) as exc:
        verify_cos_object_uploaded("missing/key.pdf")
    assert "COS" in exc.value.msg


@patch("app.open_api.source_upload.cos_object_exists", return_value=True)
def test_verify_cos_object_ok(_mock_exists):
    verify_cos_object_uploaded("ok/key.pdf")


@pytest.mark.asyncio
async def test_check_title_repeated():
    from app.open_api.source_upload import check_title_repeated

    db = AsyncMock()
    count_mock = MagicMock()
    count_mock.scalar_one.side_effect = [1, 0]
    db.execute = AsyncMock(return_value=count_mock)

    results = await check_title_repeated(
        db,
        "nb-1",
        ["dup.pdf", "new.pdf"],
    )
    assert results[0]["is_repeated"] is True
    assert results[1]["is_repeated"] is False
