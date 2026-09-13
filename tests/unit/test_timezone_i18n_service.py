"""Unit tests for i18n service and timezone conversion helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pwd301.services.assessment_service import _parse_iso_datetime
from pwd301.services.i18n_service import (
    format_tz_datetime,
    get_current_locale,
    parse_tz_offset,
    t,
)

if TYPE_CHECKING:
    from flask import Flask


def test_i18n_translation_basic() -> None:
    """Test standard dictionary lookup for Vietnamese and English."""
    assert t("common.save", lang="vi") == "Lưu thay đổi"
    assert t("common.save", lang="en") == "Save changes"
    assert t("nav.assessments", lang="vi") == "Bài kiểm tra"
    assert t("nav.assessments", lang="en") == "Assessments"
    assert t("assessment.waiting_room", lang="vi") == "Phòng chờ thi trực tuyến"
    assert t("assessment.waiting_room", lang="en") == "Online Exam Waiting Room"


def test_i18n_fallback_on_missing_key() -> None:
    """Test that missing keys safely return the key itself."""
    missing = "some.nonexistent.key"
    assert t(missing, lang="vi") == missing
    assert t(missing, lang="en") == missing


def test_i18n_parameter_formatting() -> None:
    """Test string interpolation with named arguments."""
    msg_vi = t("assessment.opens_in", lang="vi", minutes=15)
    assert "15" in msg_vi
    msg_en = t("assessment.opens_in", lang="en", minutes=15)
    assert "15" in msg_en


def test_i18n_locale_resolution_in_request_context(app: Flask) -> None:
    """Test get_current_locale using session and request headers."""
    with app.test_request_context("/"):
        assert get_current_locale() in ("vi", "en")


def test_parse_tz_offset() -> None:
    """Test parsing timezone offset strings like +01:00, GMT+7, UTC-5."""
    assert parse_tz_offset("+01:00") == 3600
    assert parse_tz_offset("GMT+1") == 3600
    assert parse_tz_offset("UTC+07:00") == 25200
    assert parse_tz_offset("GMT-05:00") == -18000
    assert parse_tz_offset("+00:00") == 0
    assert parse_tz_offset("UTC") == 0


def test_parse_iso_datetime_with_timezone_offset() -> None:
    """Test that naive datetime combined with timezone offset converts to correct UTC."""
    # Instructor in GMT+1 sets 12:00 -> should be 11:00 UTC
    dt_gmt1 = _parse_iso_datetime("2026-09-15T12:00", "open_at", tz_offset_str="+01:00")
    assert dt_gmt1 is not None
    assert dt_gmt1 == datetime(2026, 9, 15, 11, 0, 0, tzinfo=UTC)

    # Student/Instructor in GMT+7 sets 18:00 -> should be 11:00 UTC
    dt_gmt7 = _parse_iso_datetime("2026-09-15T18:00", "open_at", tz_offset_str="+07:00")
    assert dt_gmt7 is not None
    assert dt_gmt7 == datetime(2026, 9, 15, 11, 0, 0, tzinfo=UTC)

    # Identical absolute moment!
    assert dt_gmt1 == dt_gmt7


def test_format_tz_datetime() -> None:
    """Test formatting UTC datetime into local timezone with GMT label."""
    utc_dt = datetime(2026, 9, 15, 11, 0, 0, tzinfo=UTC)

    # Convert to GMT+1
    formatted_gmt1 = format_tz_datetime(utc_dt, tz_offset_str="+01:00")
    assert "12:00" in formatted_gmt1
    assert "GMT+1" in formatted_gmt1 or "+01:00" in formatted_gmt1

    # Convert to GMT+7
    formatted_gmt7 = format_tz_datetime(utc_dt, tz_offset_str="+07:00")
    assert "18:00" in formatted_gmt7
    assert "GMT+7" in formatted_gmt7 or "+07:00" in formatted_gmt7
