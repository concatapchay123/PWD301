"""Adversarial stress test suite for Milestone 2: Backend Resilient Playback Fallback.

Empirical Challenger verification for:
1. Boundary conditions for client_duration (0, negative, > 86400, NaN, Inf, non-numeric strings, boundary values 4.9, 5.0, 86400.0, 86400.1).
2. Google Data API metadata failure states (valid=False, embeddable missing/False, zero duration, negative duration, NaN/Inf, quota/network error).
3. Absolute guarantee that LessonValidationError("Trusted YouTube duration is unavailable. Please retry later.") is NEVER raised for YouTube lessons.
4. 3-Tier fallback hierarchy priority preservation.
5. Heartbeat dynamic duration refinement and clamping against frontier_seconds preserving ck_media_frontier DB constraint.
6. HTTP route payload boundary handling (/playback/start, /playback-sessions, and /progress).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.extensions import db
from backend.models.course import Course, Enrollment, EnrollmentPeriod, LearningUnit, Lesson
from backend.models.identity import Role
from backend.models.playback import MediaProgress
from backend.services import playback_service
from backend.services.playback_service import (
    DEFAULT_YOUTUBE_FALLBACK_DURATION,
    record_playback_heartbeat,
    start_playback_session,
)
from backend.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def challenger_setup(app, monkeypatch):
    if not db.session.query(Role).filter_by(code="STUDENT").first():
        db.session.add(Role(code="STUDENT", name="Student"))
        db.session.commit()

    student = register_user(
        f"chal_{datetime.now().timestamp()}@example.com",
        "Password@123",
        "Challenger Student",
    )
    student = assign_role_to_user(student.id, "STUDENT")
    course = Course(
        course_code=f"CHAL-{int(datetime.now().timestamp())}",
        title="Challenger Course",
        owner_instructor_id=student.id,
        status="PUBLISHED",
    )
    db.session.add(course)
    db.session.flush()

    unit = LearningUnit(course_id=course.id, title="Unit 1", position=1)
    db.session.add(unit)
    db.session.flush()

    lesson = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Challenger Lesson",
        position=1,
        status="PUBLISHED",
        markdown_content="<!-- video_url: https://youtu.be/abcdefghijk -->",
        minimum_completion_seconds=0,
    )
    db.session.add(lesson)
    db.session.flush()

    enrollment = Enrollment(student_user_id=student.id, course_id=course.id, status="ACTIVE")
    db.session.add(enrollment)
    db.session.flush()

    period = EnrollmentPeriod(enrollment_id=enrollment.id, period_no=1, status="ACTIVE")
    db.session.add(period)
    db.session.flush()

    enrollment.current_period_id = period.id
    db.session.commit()

    return student, lesson, datetime(2026, 10, 17, 12, 0, 0, tzinfo=UTC)


def _send_hb(actor, lesson, start, seq, now, pos, state="playing", **kwargs):
    return record_playback_heartbeat(
        actor,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": seq,
            "media_id": start.get("media_id", "youtube:abcdefghijk"),
            "position_seconds": pos,
            "playback_rate": 1,
            "state": state,
            **kwargs,
        },
        now=now,
    )


# ==============================================================================
# Challenge 1: Boundary values for client_duration on session start
# ==============================================================================


@pytest.mark.parametrize(
    "bad_duration",
    [
        0,
        0.0,
        -1,
        -100.5,
        10000000,
        86400.1,
        4.99,
        "invalid",
        "NaN",
        "Infinity",
        float("nan"),
        float("inf"),
        float("-inf"),
        None,
        [],
        {},
    ],
)
def test_adversarial_client_duration_boundary_start_falls_back(
    challenger_setup, monkeypatch, bad_duration
):
    """Stress test: Unusable/adversarial client_duration must never corrupt duration or crash."""
    actor, lesson, t = challenger_setup
    monkeypatch.setattr(
        playback_service,
        "get_youtube_metadata",
        lambda _: {"valid": False, "reason": "metadata_not_configured"},
    )

    # Lesson has no estimated duration, so fallback must be DEFAULT_YOUTUBE_FALLBACK_DURATION (1800.0)
    start = start_playback_session(
        actor, lesson.public_id, "youtube:abcdefghijk", client_duration=bad_duration, now=t
    )
    assert start["session_id"] is not None
    assert start["duration"] == DEFAULT_YOUTUBE_FALLBACK_DURATION
    assert start["frontier"] == 0.0

    media = (
        db.session.query(MediaProgress)
        .filter_by(media_id="youtube:abcdefghijk", lesson_id=lesson.id)
        .first()
    )
    assert media is not None
    assert media.duration_seconds == DEFAULT_YOUTUBE_FALLBACK_DURATION
    assert media.frontier_seconds == 0.0


@pytest.mark.parametrize(
    "valid_boundary_duration, expected",
    [
        (5.0, 5.0),
        (5.01, 5.01),
        ("5.0", 5.0),
        (86400.0, 86400.0),
        (86399.9, 86399.9),
        ("3600", 3600.0),
    ],
)
def test_adversarial_client_duration_valid_boundaries_accepted(
    challenger_setup, monkeypatch, valid_boundary_duration, expected
):
    """Valid boundary durations [5.0, 86400.0] are accepted float conversions."""
    actor, lesson, t = challenger_setup
    monkeypatch.setattr(
        playback_service,
        "get_youtube_metadata",
        lambda _: {"valid": False, "reason": "metadata_not_configured"},
    )

    start = start_playback_session(
        actor,
        lesson.public_id,
        "youtube:abcdefghijk",
        client_duration=valid_boundary_duration,
        now=t,
    )
    assert start["duration"] == expected


# ==============================================================================
# Challenge 2: Google Data API failure states & metadata edge cases
# ==============================================================================


@pytest.mark.parametrize(
    "metadata_return",
    [
        {"valid": False},
        {"valid": False, "reason": "metadata_not_configured"},
        {"valid": False, "reason": "quotaExceeded"},
        {"valid": False, "reason": "metadata_network_error"},
        {"valid": True, "embeddable": False, "duration_seconds": 300},
        {"valid": True, "embeddable": None, "duration_seconds": 300},
        {"valid": True, "embeddable": True, "duration_seconds": 0},
        {"valid": True, "embeddable": True, "duration_seconds": -50},
        {"valid": True, "embeddable": True, "duration_seconds": float("nan")},
        {"valid": True, "embeddable": True, "duration_seconds": float("inf")},
        {"valid": True, "embeddable": True, "duration_seconds": "not-a-number"},
        {},
    ],
)
def test_adversarial_google_data_api_edge_cases_never_throw(
    challenger_setup, monkeypatch, metadata_return
):
    """Stress test: Any corrupt/failed Data API response triggers resilient fallback, never throws."""
    actor, lesson, t = challenger_setup
    monkeypatch.setattr(playback_service, "get_youtube_metadata", lambda _: metadata_return)

    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    assert start["session_id"] is not None
    assert start["duration"] == DEFAULT_YOUTUBE_FALLBACK_DURATION


# ==============================================================================
# Challenge 3: 3-Tier Fallback Priority Verification
# ==============================================================================


def test_adversarial_fallback_tier_priority(challenger_setup, monkeypatch):
    """Stress test: Verify exact fallback precedence order:
    1. Valid Data API metadata
    2. Client reported duration
    3. Lesson estimated duration
    4. Default 1800.0s
    """
    actor, lesson, t = challenger_setup

    # Tier 0: Valid Data API wins over everything
    monkeypatch.setattr(
        playback_service,
        "get_youtube_metadata",
        lambda _: {"valid": True, "embeddable": True, "duration_seconds": 250.0},
    )
    lesson.estimated_duration_minutes = 20
    db.session.commit()

    start0 = start_playback_session(
        actor, lesson.public_id, "youtube:abcdefghijk", client_duration=500.0, now=t
    )
    assert start0["duration"] == 250.0

    # Clean up MediaProgress for subsequent tests
    db.session.query(MediaProgress).delete()
    db.session.commit()

    # Tier 1: Client duration wins over lesson duration when Data API is unavailable
    monkeypatch.setattr(
        playback_service,
        "get_youtube_metadata",
        lambda _: {"valid": False, "reason": "timeout"},
    )
    start1 = start_playback_session(
        actor, lesson.public_id, "youtube:abcdefghijk", client_duration=600.0, now=t
    )
    assert start1["duration"] == 600.0

    db.session.query(MediaProgress).delete()
    db.session.commit()

    # Tier 2: Lesson estimated duration wins when client duration is bad/missing
    start2 = start_playback_session(
        actor, lesson.public_id, "youtube:abcdefghijk", client_duration=-10, now=t
    )
    assert start2["duration"] == 1200.0  # 20 min * 60 = 1200.0s

    db.session.query(MediaProgress).delete()
    lesson.estimated_duration_minutes = None
    lesson.duration_seconds = 750
    db.session.commit()

    # Tier 2b: Lesson duration_seconds wins when estimated minutes is None
    start2b = start_playback_session(
        actor, lesson.public_id, "youtube:abcdefghijk", client_duration=None, now=t
    )
    assert start2b["duration"] == 750.0

    db.session.query(MediaProgress).delete()
    lesson.duration_seconds = None
    db.session.commit()

    # Tier 3: Default 1800.0s when all else fails
    start3 = start_playback_session(
        actor, lesson.public_id, "youtube:abcdefghijk", client_duration=None, now=t
    )
    assert start3["duration"] == 1800.0


# ==============================================================================
# Challenge 4: Heartbeat Dynamic Duration Refinement & Frontier Clamping
# ==============================================================================


@pytest.mark.parametrize(
    "corrupt_reported",
    [
        0,
        -5,
        10000000,
        "corrupt",
        "NaN",
        float("nan"),
        float("inf"),
        4.5,
        86401.0,
    ],
)
def test_adversarial_heartbeat_corrupt_duration_ignored(
    challenger_setup, monkeypatch, corrupt_reported
):
    """Corrupt reported durations in heartbeat must be completely ignored."""
    actor, lesson, t = challenger_setup
    monkeypatch.setattr(
        playback_service,
        "get_youtube_metadata",
        lambda _: {"valid": False, "reason": "metadata_not_configured"},
    )

    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    assert start["duration"] == 1800.0

    _send_hb(actor, lesson, start, 1, t, 0)
    hb2 = _send_hb(
        actor,
        lesson,
        start,
        2,
        t + timedelta(seconds=10),
        10,
        client_duration=corrupt_reported,
    )
    assert hb2["duration"] == 1800.0
    media = (
        db.session.query(MediaProgress)
        .filter_by(media_id="youtube:abcdefghijk", lesson_id=lesson.id)
        .first()
    )
    assert media.duration_seconds == 1800.0


def test_adversarial_heartbeat_duration_clamped_to_frontier_strictly(challenger_setup, monkeypatch):
    """Stress test: If student watched up to frontier=50s and client reports duration=20s,
    duration must be clamped to at least frontier (50s) to never violate ck_media_frontier.
    """
    actor, lesson, t = challenger_setup
    monkeypatch.setattr(
        playback_service,
        "get_youtube_metadata",
        lambda _: {"valid": False, "reason": "metadata_not_configured"},
    )

    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    _send_hb(actor, lesson, start, 1, t, 0)

    # Accumulate frontier to 40 seconds
    for idx in range(1, 5):
        _send_hb(actor, lesson, start, idx + 1, t + timedelta(seconds=10 * idx), idx * 10)

    media = (
        db.session.query(MediaProgress)
        .filter_by(media_id="youtube:abcdefghijk", lesson_id=lesson.id)
        .first()
    )
    assert media.frontier_seconds == 40.0

    # Client now reports duration of 20 seconds (less than frontier 40s)
    hb = _send_hb(
        actor,
        lesson,
        start,
        6,
        t + timedelta(seconds=50),
        40,
        state="paused",
        client_duration=20.0,
    )
    db.session.refresh(media)

    # Duration must clamp to 40.0, NOT 20.0
    assert media.duration_seconds == 40.0
    assert media.frontier_seconds == 40.0
    assert media.frontier_seconds <= media.duration_seconds
    assert hb["duration"] == 40.0

    # If client later reports duration = 120s, duration expands to 120s
    hb_expand = _send_hb(
        actor,
        lesson,
        start,
        7,
        t + timedelta(seconds=55),
        40,
        state="paused",
        duration=120.0,  # testing "duration" payload key alias
    )
    db.session.refresh(media)
    assert media.duration_seconds == 120.0
    assert hb_expand["duration"] == 120.0


# ==============================================================================
# Challenge 5: Route HTTP Endpoints Stress Testing
# ==============================================================================


def test_adversarial_web_routes_boundary_payloads(challenger_setup, client, monkeypatch):
    """Stress test: Web HTTP routes handle invalid and boundary client_duration smoothly."""
    from tests.conftest import login_web_user

    actor, lesson, t = challenger_setup
    lesson_id = str(lesson.public_id)
    login_web_user(client, actor)

    monkeypatch.setattr(
        playback_service,
        "get_youtube_metadata",
        lambda _: {"valid": False, "reason": "metadata_not_configured"},
    )

    # 1. Start with negative duration
    res_neg = client.post(
        f"/student/lessons/{lesson_id}/playback/start",
        json={"media_id": "youtube:abcdefghijk", "client_duration": -100},
    )
    assert res_neg.status_code == 200
    assert res_neg.get_json()["data"]["duration"] == DEFAULT_YOUTUBE_FALLBACK_DURATION

    # 2. Start with string invalid
    res_str = client.post(
        f"/student/lessons/{lesson_id}/playback-sessions",
        json={"media_id": "youtube:abcdefghijk", "client_duration": "malformed_string"},
    )
    assert res_str.status_code == 200
    assert res_str.get_json()["data"]["duration"] == DEFAULT_YOUTUBE_FALLBACK_DURATION

    # 3. Start with valid client duration
    res_valid = client.post(
        f"/student/lessons/{lesson_id}/playback/start",
        json={"media_id": "youtube:abcdefghijk", "client_duration": 450.0},
    )
    assert res_valid.status_code == 200
    assert res_valid.get_json()["data"]["duration"] == 450.0

    session_id = res_valid.get_json()["data"]["session_id"]

    # 4. Heartbeat progress with corrupt duration
    hb_res = client.post(
        f"/student/lessons/{lesson_id}/progress",
        json={
            "playback_session_id": session_id,
            "sequence": 1,
            "media_id": "youtube:abcdefghijk",
            "position_seconds": 0,
            "playback_rate": 1,
            "state": "playing",
            "client_duration": "malformed",
        },
    )
    assert hb_res.status_code == 200
    assert hb_res.get_json()["data"]["duration"] == 450.0
