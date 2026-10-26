"""Empirical Challenge Test Suite for Milestone 3 (Challenger 2).

Adversarial empirical stress-testing for Milestone 3 (R3 Backend HLS DRM & Multi-Video Tracking):
- Challenge 1: Multi-video lesson with 3 videos. Watch 2 of 3 to 100%, 3rd video at 0%.
  Verify `all_videos_complete` is False, `lesson_progress.max_view_fraction` is strictly <= 0.99,
  and quiz submission raises `LessonStateViolationError`.
  Then watch 3rd video to 100% and verify `all_videos_complete` is True, `max_view_fraction` is 1.0,
  and quiz is unlocked and completes successfully.
- Challenge 2: Single video threshold. 90% and 95% do NOT complete video or lesson.
  99.4s (boundary outside 0.5s tolerance) does not complete.
  99.6% (within 0.5s tolerance) completes video and lesson.
- Challenge 3: DRM key token validity. Token generated with default expiration (12 hours / 43,200s)
  is valid at 43,199s and expired at 43,201s.
"""

from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pytest
from flask import Flask

from backend.extensions import db
from backend.models.course import Course, Enrollment, EnrollmentPeriod, LearningUnit, Lesson
from backend.models.identity import Role
from backend.services.exceptions import LessonStateViolationError
from backend.services.lesson_service import get_lesson_progress, submit_lesson_quiz
from backend.services.playback_service import (
    record_playback_heartbeat,
    start_playback_session,
)
from backend.services.user_service import assign_role_to_user, register_user
from backend.services.video_drm_service import (
    DEFAULT_DRM_KEY_TOKEN_EXPIRATION_SECONDS,
    generate_key_token,
    verify_key_token,
)


@pytest.fixture
def m3_playback_env(app: Flask, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Provision a clean student enrollment and base course for empirical testing."""
    from backend.services import playback_service

    if not db.session.query(Role).filter_by(code="STUDENT").first():
        db.session.add(Role(code="STUDENT", name="Student"))
        db.session.commit()

    student_email = f"challenger2_{uuid.uuid4().hex[:8]}@backend.local"
    student = register_user(student_email, "Password@123", "Challenger 2 Student")
    student = assign_role_to_user(student.id, "STUDENT")

    course = Course(
        course_code=f"C2M3-{uuid.uuid4().hex[:6].upper()}",
        title="Milestone 3 Challenge Course",
        owner_instructor_id=student.id,
        status="PUBLISHED",
    )
    db.session.add(course)
    db.session.flush()

    unit = LearningUnit(course_id=course.id, title="Challenge Unit", position=1)
    db.session.add(unit)
    db.session.flush()

    enrollment = Enrollment(student_user_id=student.id, course_id=course.id, status="ACTIVE")
    db.session.add(enrollment)
    db.session.flush()

    period = EnrollmentPeriod(enrollment_id=enrollment.id, period_no=1, status="ACTIVE")
    db.session.add(period)
    db.session.flush()

    enrollment.current_period_id = period.id
    db.session.commit()

    # Mock YouTube metadata to return 100s duration for test YouTube IDs
    monkeypatch.setattr(
        playback_service,
        "get_youtube_metadata",
        lambda _: {"valid": True, "duration_seconds": 100, "embeddable": True},
    )

    return {
        "student": student,
        "course": course,
        "unit": unit,
        "enrollment": enrollment,
        "period": period,
        "base_time": datetime(2026, 10, 17, 12, 0, 0, tzinfo=UTC),
    }


def _send_heartbeat(
    actor: Any,
    lesson: Lesson,
    start: dict[str, Any],
    sequence: int,
    now: datetime,
    position: float,
    state: str = "playing",
    **kwargs: Any,
) -> dict[str, Any]:
    """Helper to dispatch a verified playback heartbeat."""
    return record_playback_heartbeat(
        actor,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": sequence,
            "media_id": start.get("media_id"),
            "position_seconds": position,
            "playback_rate": 1,
            "state": state,
            **kwargs,
        },
        now=now,
    )


# ==============================================================================
# Challenge 1: Multi-video lesson with 3 videos stress test
# ==============================================================================
def test_challenge_1_multi_video_lesson_3_videos(m3_playback_env: dict[str, Any]) -> None:
    """Challenge 1: Multi-video lesson with 3 videos.

    1. Watch 2 of 3 videos to 100%, 3rd video at 0%:
       - Verify all_videos_complete is False.
       - Verify lesson_progress.max_view_fraction is strictly <= 0.99.
       - Verify quiz submission raises LessonStateViolationError.
    2. Watch 3rd video to 100%:
       - Verify all_videos_complete is True.
       - Verify lesson_progress.max_view_fraction becomes 1.0.
       - Verify quiz is unlocked and submission completes the lesson.
    """
    student = m3_playback_env["student"]
    course = m3_playback_env["course"]
    unit = m3_playback_env["unit"]
    t0 = m3_playback_env["base_time"]

    # Create a published lesson with 3 videos and a mini-quiz
    v1_id = "youtube:vid11111111"
    v2_id = "youtube:vid22222222"
    v3_id = "youtube:vid33333333"

    lesson = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Multi-Video Challenge Lesson",
        position=1,
        status="PUBLISHED",
        markdown_content=(
            '<!-- video_urls: ["https://youtu.be/vid11111111", '
            '"https://youtu.be/vid22222222", '
            '"https://youtu.be/vid33333333"] -->\n'
            '<!-- mini_quiz: [{"type":"TRUE_FALSE","question":"M3 Multi-Video Check","correct_value":true}] -->\n'
            "<!-- mini_quiz_passing: 80 -->"
        ),
        minimum_completion_seconds=0,
    )
    db.session.add(lesson)
    db.session.commit()

    # --------------------------------------------------------------------------
    # Step 1: Watch Video 1 to 100% (100 seconds)
    # --------------------------------------------------------------------------
    t = t0
    start1 = start_playback_session(student, lesson.public_id, v1_id, now=t)
    _send_heartbeat(student, lesson, start1, 1, t, 0)

    res1 = {}
    for idx in range(1, 11):
        t += timedelta(seconds=10)
        res1 = _send_heartbeat(student, lesson, start1, idx + 1, t, idx * 10)

    # Video 1 is 100% complete, but Videos 2 and 3 are not started
    assert res1["is_video_complete"] is True
    assert res1["all_videos_complete"] is False
    assert res1["is_completed"] is False

    prog1 = get_lesson_progress(student, lesson.id)
    assert prog1.completed_at is None
    # 1 of 3 videos watched -> average 1/3 ~ 0.33 <= 0.99
    assert float(prog1.max_view_fraction) <= 0.99
    assert abs(float(prog1.max_view_fraction) - (1.0 / 3.0)) < 0.05

    # --------------------------------------------------------------------------
    # Step 2: Watch Video 2 to 100% (100 seconds), Video 3 stays at 0%
    # --------------------------------------------------------------------------
    t += timedelta(seconds=50)
    start2 = start_playback_session(student, lesson.public_id, v2_id, now=t)
    _send_heartbeat(student, lesson, start2, 1, t, 0)

    res2 = {}
    for idx in range(1, 11):
        t += timedelta(seconds=10)
        res2 = _send_heartbeat(student, lesson, start2, idx + 1, t, idx * 10)

    # Video 2 is 100% complete, Video 1 is 100% complete, but Video 3 is at 0%
    assert res2["is_video_complete"] is True
    assert res2["all_videos_complete"] is False, "all_videos_complete MUST be False when video 3 is at 0%"
    assert res2["is_completed"] is False

    # Check lesson progress in database
    prog2 = get_lesson_progress(student, lesson.id)
    assert prog2.completed_at is None, "Lesson must not be completed when video 3 is incomplete"
    # 2 of 3 videos watched -> average 2/3 ~ 0.6667, strictly <= 0.99
    assert float(prog2.max_view_fraction) <= 0.99, (
        f"max_view_fraction must be <= 0.99, got {prog2.max_view_fraction}"
    )
    assert abs(float(prog2.max_view_fraction) - (2.0 / 3.0)) < 0.05

    # Verify quiz submission is strictly blocked with LessonStateViolationError
    with pytest.raises(LessonStateViolationError, match="Watch the lesson video"):
        submit_lesson_quiz(student, lesson.id, [True])

    # --------------------------------------------------------------------------
    # Step 2b (Adversarial stress): Start Video 3, send heartbeat at 0s, verify still blocked
    # --------------------------------------------------------------------------
    t += timedelta(seconds=50)
    start3 = start_playback_session(student, lesson.public_id, v3_id, now=t)
    res3_start = _send_heartbeat(student, lesson, start3, 1, t, 0)
    assert res3_start["is_video_complete"] is False
    assert res3_start["all_videos_complete"] is False
    prog3_start = get_lesson_progress(student, lesson.id)
    assert float(prog3_start.max_view_fraction) <= 0.99

    with pytest.raises(LessonStateViolationError, match="Watch the lesson video"):
        submit_lesson_quiz(student, lesson.id, [True])

    # --------------------------------------------------------------------------
    # Step 2c (Adversarial stress): Advance Video 3 to 90% (90s)
    # Total progress = (100 + 100 + 90)/300 = 96.67%. Still NOT complete!
    # --------------------------------------------------------------------------
    for idx in range(1, 10):
        t += timedelta(seconds=10)
        res3_90 = _send_heartbeat(student, lesson, start3, idx + 1, t, idx * 10)

    assert res3_90["is_video_complete"] is False
    assert res3_90["all_videos_complete"] is False
    prog3_90 = get_lesson_progress(student, lesson.id)
    assert float(prog3_90.max_view_fraction) <= 0.99

    with pytest.raises(LessonStateViolationError, match="Watch the lesson video"):
        submit_lesson_quiz(student, lesson.id, [True])

    # --------------------------------------------------------------------------
    # Step 3: Advance Video 3 to 100% (100 seconds)
    # --------------------------------------------------------------------------
    t += timedelta(seconds=10)
    res3_100 = _send_heartbeat(student, lesson, start3, 11, t, 100)

    assert res3_100["is_video_complete"] is True
    assert res3_100["all_videos_complete"] is True, "all_videos_complete MUST be True when all 3 videos hit 100%"

    prog3_final = get_lesson_progress(student, lesson.id)
    assert float(prog3_final.max_view_fraction) >= 1.0, (
        f"max_view_fraction must be 1.0, got {prog3_final.max_view_fraction}"
    )

    # Mini quiz is now UNLOCKED and successfully completes the lesson!
    quiz_res = submit_lesson_quiz(student, lesson.id, [True])
    assert quiz_res.completed_at is not None


# ==============================================================================
# Challenge 2: Single video threshold precision & tolerance stress test
# ==============================================================================
def test_challenge_2_single_video_threshold_and_tolerance(m3_playback_env: dict[str, Any]) -> None:
    """Challenge 2: Single video threshold precision & 0.5s tolerance.

    Single video with duration 100s:
    - 90s (90%) -> is_video_complete is False, is_completed is False, max_view_fraction <= 0.99.
    - 95s (95%) -> is_video_complete is False, is_completed is False, max_view_fraction <= 0.99.
    - 99.4s (boundary outside 0.5s tolerance: 99.4 < 99.5) -> is_video_complete is False.
    - 99.6s (within 0.5s tolerance: 99.6 >= 99.5) -> is_video_complete is True, is_completed is True.
    """
    student = m3_playback_env["student"]
    course = m3_playback_env["course"]
    unit = m3_playback_env["unit"]
    t0 = m3_playback_env["base_time"]

    v_id = "youtube:singlevid01"
    lesson = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Single Video Precision Lesson",
        position=2,
        status="PUBLISHED",
        markdown_content="<!-- video_url: https://youtu.be/singlevid01 -->",
        minimum_completion_seconds=0,
    )
    db.session.add(lesson)
    db.session.commit()

    t = t0
    start = start_playback_session(student, lesson.public_id, v_id, now=t)
    _send_heartbeat(student, lesson, start, 1, t, 0)

    # 1. Advance to 90 seconds (90%)
    for idx in range(1, 10):
        t += timedelta(seconds=10)
        res_90 = _send_heartbeat(student, lesson, start, idx + 1, t, idx * 10)

    assert res_90["is_video_complete"] is False, "90% must NOT complete video"
    assert res_90["all_videos_complete"] is False, "90% must NOT complete all videos"
    assert res_90["is_completed"] is False, "90% must NOT complete lesson"
    prog_90 = get_lesson_progress(student, lesson.id)
    assert prog_90.completed_at is None
    assert float(prog_90.max_view_fraction) <= 0.99
    assert abs(float(prog_90.max_view_fraction) - 0.90) < 0.02

    # 2. Advance to 95 seconds (95%)
    t += timedelta(seconds=5)
    res_95 = _send_heartbeat(student, lesson, start, 11, t, 95)

    assert res_95["is_video_complete"] is False, "95% must NOT complete video"
    assert res_95["all_videos_complete"] is False, "95% must NOT complete all videos"
    assert res_95["is_completed"] is False, "95% must NOT complete lesson"
    prog_95 = get_lesson_progress(student, lesson.id)
    assert prog_95.completed_at is None
    assert float(prog_95.max_view_fraction) <= 0.99
    assert abs(float(prog_95.max_view_fraction) - 0.95) < 0.02

    # 3. Adversarial boundary: Advance to 99.4 seconds (duration - 0.6s)
    # 0.5s tolerance threshold is duration - 0.5s = 99.5s.
    # 99.4s is strictly below the tolerance boundary, so must NOT complete!
    t += timedelta(seconds=4.4)
    res_99_4 = _send_heartbeat(student, lesson, start, 12, t, 99.4)

    assert res_99_4["is_video_complete"] is False, "99.4s (< 99.5s) must NOT complete video"
    assert res_99_4["all_videos_complete"] is False
    assert res_99_4["is_completed"] is False
    prog_99_4 = get_lesson_progress(student, lesson.id)
    assert prog_99_4.completed_at is None
    assert float(prog_99_4.max_view_fraction) <= 0.99

    # 4. Advance to 99.6 seconds (duration - 0.4s >= duration - 0.5s)
    # Within 0.5s tolerance, this MUST trigger completion!
    t += timedelta(seconds=0.2)
    res_99_6 = _send_heartbeat(student, lesson, start, 13, t, 99.6)

    assert res_99_6["is_video_complete"] is True, "99.6s (>= 99.5s) MUST complete video"
    assert res_99_6["all_videos_complete"] is True, "99.6s MUST complete all videos"
    assert res_99_6["is_completed"] is True, "99.6s MUST complete lesson"
    prog_99_6 = get_lesson_progress(student, lesson.id)
    assert prog_99_6.completed_at is not None, "Lesson must have completed_at timestamp set"
    assert float(prog_99_6.max_view_fraction) >= 1.0


# ==============================================================================
# Challenge 3: DRM key token default validity & exact expiration stress test
# ==============================================================================
def test_challenge_3_drm_key_token_expiration_stress() -> None:
    """Challenge 3: DRM key token validity with default expiration.

    1. Verify DEFAULT_DRM_KEY_TOKEN_EXPIRATION_SECONDS is 43_200 (12 hours).
    2. Generate token with default expiration.
    3. Verify validity at t + 43,199s returns (True, "OK").
    4. Verify validity at t + 43,200s returns (True, "OK").
    5. Verify validity at t + 43,201s returns (False, "Token expired").
    6. Security edge-cases: tampered signature, mismatched student/course/lesson.
    """
    assert DEFAULT_DRM_KEY_TOKEN_EXPIRATION_SECONDS == 43_200, (
        f"Default token expiration must be 43,200s (12 hours), got {DEFAULT_DRM_KEY_TOKEN_EXPIRATION_SECONDS}"
    )

    secret = "empirical-challenge-drm-secret-2026"
    student_id = 9991
    course_id = 5552
    lesson_id = 7773
    t_start = 1700000000.0

    # Generate token using DEFAULT expiration (no expires_in argument)
    with patch("time.time", return_value=t_start):
        token = generate_key_token(student_id, course_id, lesson_id, secret)

    # 1. At t + 43,199s (1 second before 12 hours) -> Valid
    with patch("time.time", return_value=t_start + 43_199):
        valid_43199, reason_43199 = verify_key_token(token, student_id, course_id, lesson_id, secret)
        assert valid_43199 is True, f"Token must be valid at t + 43,199s, but got: {reason_43199}"
        assert reason_43199 == "OK"

    # 2. At t + 43,200s (exact boundary) -> Valid
    with patch("time.time", return_value=t_start + 43_200):
        valid_43200, reason_43200 = verify_key_token(token, student_id, course_id, lesson_id, secret)
        assert valid_43200 is True, f"Token must be valid at t + 43,200s, but got: {reason_43200}"
        assert reason_43200 == "OK"

    # 3. At t + 43,201s (1 second after 12 hours) -> Expired
    with patch("time.time", return_value=t_start + 43_201):
        valid_43201, reason_43201 = verify_key_token(token, student_id, course_id, lesson_id, secret)
        assert valid_43201 is False, "Token must be expired at t + 43,201s"
        assert "expired" in reason_43201.lower(), f"Expected 'Token expired', got '{reason_43201}'"

    # 4. Security edge cases at valid time (t + 100s)
    with patch("time.time", return_value=t_start + 100):
        # Mismatched student ID
        v_user, r_user = verify_key_token(token, 99999, course_id, lesson_id, secret)
        assert v_user is False
        assert "user mismatch" in r_user.lower()

        # Mismatched course ID
        v_course, r_course = verify_key_token(token, student_id, 99999, lesson_id, secret)
        assert v_course is False
        assert "course mismatch" in r_course.lower()

        # Mismatched lesson ID
        v_lesson, r_lesson = verify_key_token(token, student_id, course_id, 99999, secret)
        assert v_lesson is False
        assert "lesson mismatch" in r_lesson.lower()

        # Tampered signature
        tampered_token = token[:-5] + "AAAAA"
        v_tamp, r_tamp = verify_key_token(tampered_token, student_id, course_id, lesson_id, secret)
        assert v_tamp is False
        assert any(w in r_tamp.lower() for w in ("tampered", "signature", "invalid", "decode"))


# ==============================================================================
# Standalone execution entrypoint
# ==============================================================================
def run_all_challenges_standalone() -> int:
    """Run all 3 challenges standalone with detailed terminal reporting."""
    print("=" * 80)
    print("RUNNING STANDALONE EMPIRICAL CHALLENGES (CHALLENGER 2 - MILESTONE 3)")
    print("=" * 80)

    # 1. Challenge 3: Token Expiration (pure unit test, no app context needed)
    print("\n[CHALLENGE 3] Testing DRM Key Token Validity & Expiration Stress...")
    try:
        test_challenge_3_drm_key_token_expiration_stress()
        print("  -> PASS: Token is valid at 43,199s and expired at 43,201s.")
    except Exception as e:
        print(f"  -> FAIL: {e}")
        return 1

    # 2. Challenges 1 & 2 require Flask app and DB fixture
    from _pytest.monkeypatch import MonkeyPatch

    from backend import create_app

    test_app = create_app("testing", config_override={"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    mp = MonkeyPatch()

    with test_app.app_context():
        db.create_all()
        try:
            # Build fixture environment
            from backend.services import playback_service

            if not db.session.query(Role).filter_by(code="STUDENT").first():
                db.session.add(Role(code="STUDENT", name="Student"))
                db.session.commit()

            student = register_user("c2_standalone@backend.local", "Password@123", "Standalone Student")
            student = assign_role_to_user(student.id, "STUDENT")

            course = Course(
                course_code="C2-STANDALONE",
                title="Standalone Challenge Course",
                owner_instructor_id=student.id,
                status="PUBLISHED",
            )
            db.session.add(course)
            db.session.flush()

            unit = LearningUnit(course_id=course.id, title="Unit", position=1)
            db.session.add(unit)
            db.session.flush()

            enrollment = Enrollment(student_user_id=student.id, course_id=course.id, status="ACTIVE")
            db.session.add(enrollment)
            db.session.flush()

            period = EnrollmentPeriod(enrollment_id=enrollment.id, period_no=1, status="ACTIVE")
            db.session.add(period)
            db.session.flush()
            enrollment.current_period_id = period.id
            db.session.commit()

            mp.setattr(
                playback_service,
                "get_youtube_metadata",
                lambda _: {"valid": True, "duration_seconds": 100, "embeddable": True},
            )

            env = {
                "student": student,
                "course": course,
                "unit": unit,
                "enrollment": enrollment,
                "period": period,
                "base_time": datetime(2026, 10, 17, 12, 0, 0, tzinfo=UTC),
            }

            print("\n[CHALLENGE 1] Testing Multi-Video Lesson (3 videos) Stress...")
            test_challenge_1_multi_video_lesson_3_videos(env)
            print("  -> PASS: 2 of 3 videos watched keeps quiz locked and max_view_fraction <= 0.99.")
            print("  -> PASS: 3rd video watched to 100% unlocks quiz and completes lesson.")

            print("\n[CHALLENGE 2] Testing Single Video Threshold & 0.5s Tolerance Stress...")
            test_challenge_2_single_video_threshold_and_tolerance(env)
            print("  -> PASS: 90% and 95% do NOT complete video.")
            print("  -> PASS: 99.4s (< 99.5s) does NOT complete video.")
            print("  -> PASS: 99.6s (>= 99.5s) COMPLETES video and lesson.")

            print("\n" + "=" * 80)
            print("ALL 3 EMPIRICAL CHALLENGES PASSED EMPIRICALLY WITH ZERO ERRORS!")
            print("=" * 80)
            return 0
        finally:
            mp.undo()
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    sys.exit(run_all_challenges_standalone())
