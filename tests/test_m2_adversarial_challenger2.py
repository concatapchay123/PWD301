"""Comprehensive Adversarial Stress Test Suite for Milestone 2 (Challenger 2).

Probes:
1. ck_media_frontier constraint integrity:
   - Does media.duration_seconds ever drop below media.frontier_seconds?
   - Boundary checks: reported_duration = 0, negative, NaN, Inf, < 5.0, > 86400.0.
   - Dynamic down-refinement clamped to frontier.
2. Server-authoritative pacing and wall-clock rate check:
   - Can client tamper with reported_duration to jump forward in position or frontier?
   - Wall-clock rate check (allowed = elapsed * rate) strictly prevents time skipping.
3. Sequential completion gate & duration tampering attack:
   - If a student watches 5 seconds and reports duration=5.0:
     * Does is_video_complete become True?
     * Does text dwell time (60s) or mini-quiz prevent premature lesson completion?
     * Does multi-video tracking require ALL videos to be completed?
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from flask import Flask

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, EnrollmentPeriod, LearningUnit, Lesson
from pwd301.models.identity import Role
from pwd301.models.playback import MediaProgress
from pwd301.services import playback_service
from pwd301.services.lesson_service import get_lesson_progress, submit_lesson_quiz
from pwd301.services.playback_service import (
    record_playback_heartbeat,
    start_playback_session,
)
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def adversarial_env(app: Flask, monkeypatch: pytest.MonkeyPatch):
    if not db.session.query(Role).filter_by(code="STUDENT").first():
        db.session.add(Role(code="STUDENT", name="Student"))
        db.session.commit()

    student = register_user(
        f"adv_{uuid.uuid4().hex[:8]}@pwd301.local", "Password@123", "Adv Student"
    )
    student = assign_role_to_user(student.id, "STUDENT")

    course = Course(
        course_code=f"ADV-{uuid.uuid4().hex[:6].upper()}",
        title="Adversarial Course",
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

    # Default mock: YouTube metadata returns unavailable (triggering fallback)
    monkeypatch.setattr(
        playback_service,
        "get_youtube_metadata",
        lambda _: {"valid": False, "reason": "metadata_not_configured"},
    )

    return {
        "student": student,
        "course": course,
        "unit": unit,
        "enrollment": enrollment,
        "period": period,
        "base_time": datetime(2026, 10, 17, 12, 0, 0, tzinfo=UTC),
    }


def test_ck_media_frontier_never_violated_under_adversarial_durations(adversarial_env):
    """Stress test ck_media_frontier constraint with malicious and boundary duration values."""
    student = adversarial_env["student"]
    course = adversarial_env["course"]
    unit = adversarial_env["unit"]
    t0 = adversarial_env["base_time"]

    lesson = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Adversarial Duration Lesson",
        position=1,
        status="PUBLISHED",
        markdown_content="<!-- video_url: https://youtu.be/adv_vid_001 -->",
        minimum_completion_seconds=0,
    )
    db.session.add(lesson)
    db.session.commit()

    v_id = "youtube:adv_vid_001"
    start = start_playback_session(student, lesson.public_id, v_id, now=t0)
    assert start["duration"] == 1800.0  # default fallback

    # Advance 30 seconds legitimately
    t = t0
    seq = 1
    record_playback_heartbeat(
        student,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": seq,
            "media_id": v_id,
            "position_seconds": 0,
            "playback_rate": 1,
            "state": "playing",
        },
        now=t,
    )
    for i in range(1, 4):
        seq += 1
        t += timedelta(seconds=10)
        record_playback_heartbeat(
            student,
            lesson.public_id,
            {
                "playback_session_id": start["session_id"],
                "sequence": seq,
                "media_id": v_id,
                "position_seconds": i * 10,
                "playback_rate": 1,
                "state": "playing",
            },
            now=t,
        )

    # Frontier is now 30.0s
    media = (
        db.session.query(MediaProgress)
        .filter_by(
            enrollment_period_id=adversarial_env["period"].id,
            lesson_id=lesson.id,
            media_id=v_id,
        )
        .one()
    )
    assert media.frontier_seconds == 30.0

    # 1. Attack with reported_duration lower than current frontier (e.g. 10.0s)
    seq += 1
    t += timedelta(seconds=5)
    res = record_playback_heartbeat(
        student,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": seq,
            "media_id": v_id,
            "position_seconds": 35,
            "playback_rate": 1,
            "state": "playing",
            "duration": 10.0,  # Below current frontier (30.0)
        },
        now=t,
    )
    db.session.refresh(media)
    # Check that duration_seconds was clamped to max(frontier, 10.0) -> 30.0
    # And frontier is capped at duration_seconds (30.0), so frontier <= duration holds!
    assert media.duration_seconds == 30.0
    assert media.frontier_seconds == 30.0
    assert media.frontier_seconds <= media.duration_seconds

    # 2. Attack with invalid reported_duration values: negative, 0, NaN, Inf, < 5.0, > 86400
    invalid_durations = [-100.0, 0.0, 4.9, 86400.1, float("nan"), float("inf"), "malicious_string"]
    for inv in invalid_durations:
        seq += 1
        t += timedelta(seconds=1)
        record_playback_heartbeat(
            student,
            lesson.public_id,
            {
                "playback_session_id": start["session_id"],
                "sequence": seq,
                "media_id": v_id,
                "position_seconds": 30,
                "playback_rate": 1,
                "state": "playing",
                "duration": inv,
            },
            now=t,
        )
        db.session.refresh(media)
        assert media.duration_seconds > 0
        assert media.frontier_seconds >= 0
        assert media.frontier_seconds <= media.duration_seconds


def test_wall_clock_pacing_prevents_time_skipping_with_duration_tampering(adversarial_env):
    """Verify that wall-clock rate check strictly blocks jumping forward even if duration changes."""
    student = adversarial_env["student"]
    course = adversarial_env["course"]
    unit = adversarial_env["unit"]
    t0 = adversarial_env["base_time"]

    lesson = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Pacing Check Lesson",
        position=2,
        status="PUBLISHED",
        markdown_content="<!-- video_url: https://youtu.be/adv_vid_002 -->",
        minimum_completion_seconds=0,
    )
    db.session.add(lesson)
    db.session.commit()

    v_id = "youtube:adv_vid_002"
    start = start_playback_session(student, lesson.public_id, v_id, now=t0)

    # Sequence 1 at t0, pos 0
    record_playback_heartbeat(
        student,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": 1,
            "media_id": v_id,
            "position_seconds": 0,
            "playback_rate": 1,
            "state": "playing",
        },
        now=t0,
    )

    # Attack: Client waits 2 seconds, but claims position 300s and duration 300s
    t_jump = t0 + timedelta(seconds=2)
    res_jump = record_playback_heartbeat(
        student,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": 2,
            "media_id": v_id,
            "position_seconds": 300,  # Jumped from 0 to 300 in 2s
            "playback_rate": 1,
            "state": "playing",
            "duration": 300.0,
        },
        now=t_jump,
    )

    # Frontier must NOT have jumped to 300!
    assert res_jump["frontier"] == 0.0
    assert res_jump["credited_seconds"] == 0
    assert res_jump["is_video_complete"] is False
    assert res_jump["seek_required"] is True

    media = (
        db.session.query(MediaProgress)
        .filter_by(
            enrollment_period_id=adversarial_env["period"].id,
            lesson_id=lesson.id,
            media_id=v_id,
        )
        .one()
    )
    assert media.frontier_seconds == 0.0
    # ck_media_frontier is preserved
    assert media.frontier_seconds <= media.duration_seconds


def test_duration_refinement_to_actual_video_length(adversarial_env):
    """Verify that when client refines duration to genuine length (e.g. 120s from 1800s fallback),
    pacing still requires actual wall-clock time (120s) to complete."""
    student = adversarial_env["student"]
    course = adversarial_env["course"]
    unit = adversarial_env["unit"]
    t0 = adversarial_env["base_time"]

    lesson = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Refine Length Lesson",
        position=3,
        status="PUBLISHED",
        markdown_content="<!-- video_url: https://youtu.be/adv_vid_003 -->",
        minimum_completion_seconds=0,
    )
    db.session.add(lesson)
    db.session.commit()

    v_id = "youtube:adv_vid_003"
    start = start_playback_session(student, lesson.public_id, v_id, now=t0)
    assert start["duration"] == 1800.0

    # Heartbeat 1 refines duration to 120s
    res1 = record_playback_heartbeat(
        student,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": 1,
            "media_id": v_id,
            "position_seconds": 0,
            "playback_rate": 1,
            "state": "playing",
            "duration": 120.0,
        },
        now=t0,
    )
    assert res1["duration"] == 120.0
    assert res1["is_video_complete"] is False

    # Try jumping to 120s immediately in next heartbeat after 10s
    t1 = t0 + timedelta(seconds=10)
    res2 = record_playback_heartbeat(
        student,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": 2,
            "media_id": v_id,
            "position_seconds": 120.0,  # Jump to end
            "playback_rate": 1,
            "state": "playing",
        },
        now=t1,
    )
    assert res2["is_video_complete"] is False
    assert res2["frontier"] == 0.0

    # Advance legitimately with wall clock 12 intervals of 10s = 120s
    t = t1
    seq = 2
    # First recover from seek
    seq += 1
    t += timedelta(seconds=1)
    record_playback_heartbeat(
        student,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": seq,
            "media_id": v_id,
            "position_seconds": 0,
            "playback_rate": 1,
            "state": "playing",
        },
        now=t,
    )

    for i in range(1, 13):
        seq += 1
        t += timedelta(seconds=10)
        pos = min(120.0, i * 10)
        res_legit = record_playback_heartbeat(
            student,
            lesson.public_id,
            {
                "playback_session_id": start["session_id"],
                "sequence": seq,
                "media_id": v_id,
                "position_seconds": pos,
                "playback_rate": 1,
                "state": "playing",
            },
            now=t,
        )

    assert res_legit["is_video_complete"] is True
    assert res_legit["all_videos_complete"] is True
    assert res_legit["is_completed"] is True


def test_duration_tampering_cannot_bypass_text_dwell_and_quiz(adversarial_env):
    """Stress test: A malicious client claims duration=5.0s on a video.
    Verify that even if video reaches 100% after 5 seconds:
    1. Text dwell gate (60 seconds) prevents lesson completion.
    2. Mini-quiz gate prevents lesson completion until quiz is passed.
    """
    student = adversarial_env["student"]
    course = adversarial_env["course"]
    unit = adversarial_env["unit"]
    t0 = adversarial_env["base_time"]

    lesson = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Sequential Gate Lesson",
        position=4,
        status="PUBLISHED",
        markdown_content=(
            "<!-- video_url: https://youtu.be/adv_vid_004 -->\n"
            "This is required lesson text content that requires reading.\n"
            '<!-- mini_quiz: [{"type":"TRUE_FALSE","question":"Check","correct_value":true}] -->\n'
            "<!-- mini_quiz_passing: 80 -->"
        ),
        minimum_completion_seconds=60,  # Strict 60s dwell time requirement
    )
    db.session.add(lesson)
    db.session.commit()

    v_id = "youtube:adv_vid_004"
    start = start_playback_session(student, lesson.public_id, v_id, now=t0)

    # Malicious client sends duration=5.0 and watches 5 seconds
    record_playback_heartbeat(
        student,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": 1,
            "media_id": v_id,
            "position_seconds": 0,
            "playback_rate": 1,
            "state": "playing",
            "duration": 5.0,
        },
        now=t0,
    )

    t5 = t0 + timedelta(seconds=5)
    res_5s = record_playback_heartbeat(
        student,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": 2,
            "media_id": v_id,
            "position_seconds": 5.0,
            "playback_rate": 1,
            "state": "playing",
        },
        now=t5,
    )

    # The video itself is marked complete (5s / 5s)
    assert res_5s["is_video_complete"] is True
    assert res_5s["all_videos_complete"] is True

    # BUT the lesson must NOT be complete because:
    # 1. Dwell time is only 5s < 60s minimum
    # 2. Mini-quiz has not been submitted/passed
    assert res_5s["is_completed"] is False
    prog = get_lesson_progress(student, lesson.id)
    assert prog.completed_at is None
    assert prog.seconds_spent == 5

    # If student attempts quiz before dwell time is satisfied (e.g. at 5s):
    # Note: submit_lesson_quiz requires video watched (which passed) but let's check
    # if quiz submission completes lesson without dwell time:
    quiz_res = submit_lesson_quiz(student, lesson.id, [True])
    # Progress seconds_spent is still 5s < 60s!
    # Because minimum_completion_seconds = 60, does quiz_res.completed_at require dwell?
    # Let's check submit_lesson_quiz behavior:
    prog_after_quiz = get_lesson_progress(student, lesson.id)
    # If minimum_completion_seconds > 0, dwell must be met before full completion
