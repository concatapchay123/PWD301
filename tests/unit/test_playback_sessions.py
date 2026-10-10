"""Disposable SQLite regressions; SQL Server locking requires a separate live gate."""

from datetime import UTC, datetime, timedelta

import pytest

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, EnrollmentPeriod, LearningUnit, Lesson
from pwd301.models.identity import Role
from pwd301.services.exceptions import LessonValidationError
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def playback_setup(app, monkeypatch):
    from pwd301.services import playback_service

    if not db.session.query(Role).filter_by(code="STUDENT").first():
        db.session.add(Role(code="STUDENT", name="Student"))
        db.session.commit()

    student = register_user("playback@example.com", "Password@123", "Playback Student")
    student = assign_role_to_user(student.id, "STUDENT")
    course = Course(
        course_code="PLAY-1", title="Playback", owner_instructor_id=student.id, status="PUBLISHED"
    )
    db.session.add(course)
    db.session.flush()
    unit = LearningUnit(course_id=course.id, title="Video unit", position=1)
    db.session.add(unit)
    db.session.flush()
    lesson = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Video",
        position=1,
        status="PUBLISHED",
        markdown_content="<!-- video_url: https://youtu.be/abcdefghijk -->",
        minimum_completion_seconds=30,
    )
    db.session.add(lesson)
    enrollment = Enrollment(student_user_id=student.id, course_id=course.id, status="ACTIVE")
    db.session.add(enrollment)
    db.session.flush()
    period = EnrollmentPeriod(enrollment_id=enrollment.id, period_no=1, status="ACTIVE")
    db.session.add(period)
    db.session.flush()
    enrollment.current_period_id = period.id
    db.session.commit()
    monkeypatch.setattr(
        playback_service,
        "get_youtube_metadata",
        lambda _: {"valid": True, "duration_seconds": 100, "embeddable": True},
    )
    return student, lesson, datetime(2026, 10, 9, tzinfo=UTC)


def send(actor, lesson, start, sequence, now, position, state="playing", **kwargs):
    from pwd301.services.playback_service import record_playback_heartbeat

    return record_playback_heartbeat(
        actor,
        lesson.public_id,
        {
            "playback_session_id": start["session_id"],
            "sequence": sequence,
            "media_id": "youtube:abcdefghijk",
            "position_seconds": position,
            "playback_rate": 1,
            "state": state,
            **kwargs,
        },
        now=now,
    )


def test_first_spam_retry_gap_and_resume(playback_setup):
    from pwd301.services.playback_service import start_playback_session

    actor, lesson, t = playback_setup
    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    first = send(actor, lesson, start, 1, t, 0)
    assert first["credited_seconds"] == 0
    second = send(actor, lesson, start, 2, t + timedelta(seconds=10), 10)
    assert second["credited_seconds"] == 10 and second["frontier"] == 10
    assert send(actor, lesson, start, 2, t + timedelta(seconds=11), 10) == second
    spam = send(actor, lesson, start, 3, t + timedelta(seconds=10), 20)
    assert spam["credited_seconds"] == 0 and spam["frontier"] == 10
    gap = send(actor, lesson, start, 4, t + timedelta(seconds=50), 50)
    assert gap["credited_seconds"] == 0 and gap["frontier"] == 10
    resume = start_playback_session(
        actor, lesson.public_id, "youtube:abcdefghijk", now=t + timedelta(seconds=51)
    )
    assert resume["frontier"] == 10 and resume["next_sequence"] == 1
    from pwd301.models.playback import PlaybackReceipt

    assert db.session.query(PlaybackReceipt).count() == 0
    with pytest.raises(LessonValidationError):
        send(actor, lesson, start, 5, t + timedelta(seconds=52), 10)


@pytest.mark.parametrize("state", ["paused", "buffering", "hidden", "blackout", "error"])
def test_nonplaying_stops_interval(playback_setup, state):
    from pwd301.services.playback_service import start_playback_session

    actor, lesson, t = playback_setup
    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    send(actor, lesson, start, 1, t, 0)
    expected = 10 if state == "paused" else 0
    assert (
        send(actor, lesson, start, 2, t + timedelta(seconds=10), 10, state)["credited_seconds"]
        == expected
    )
    assert send(actor, lesson, start, 3, t + timedelta(seconds=11), 10)["credited_seconds"] == 0


@pytest.mark.parametrize("rate", [0.75, 1, 2])
def test_delayed_heartbeat_cannot_credit_stalled_playback(playback_setup, rate):
    from pwd301.services.playback_service import start_playback_session

    actor, lesson, t = playback_setup
    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    send(actor, lesson, start, 1, t, 0, playback_rate=rate)
    result = send(actor, lesson, start, 2, t + timedelta(seconds=19), 10 * rate, playback_rate=rate)
    assert result["credited_seconds"] == 10
    assert (
        send(actor, lesson, start, 2, t + timedelta(seconds=20), 10 * rate, playback_rate=rate)
        == result
    )


def test_missing_sequence_and_forged_media_fail(playback_setup):
    from pwd301.services.playback_service import start_playback_session

    actor, lesson, t = playback_setup
    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    with pytest.raises(LessonValidationError):
        send(actor, lesson, start, 2, t, 0)
    with pytest.raises(LessonValidationError):
        start_playback_session(actor, lesson.public_id, "youtube:xxxxxxxxxxx", now=t)


def test_legacy_video_payload_cannot_credit(playback_setup):
    from pwd301.services.lesson_service import record_lesson_progress

    actor, lesson, t = playback_setup
    with pytest.raises(LessonValidationError):
        record_lesson_progress(actor, lesson.id, 60, 1, now=t)


def test_duration_unavailable_is_fail_closed(playback_setup, monkeypatch):
    from pwd301.services import playback_service

    actor, lesson, t = playback_setup
    monkeypatch.setattr(playback_service, "get_youtube_metadata", lambda _: {"valid": False})
    with pytest.raises(LessonValidationError):
        playback_service.start_playback_session(
            actor, lesson.public_id, "youtube:abcdefghijk", now=t
        )


def test_zero_reconciliation_cannot_forge_video_completion(playback_setup):
    from pwd301.services.playback_service import reconcile_lesson_progress

    actor, lesson, t = playback_setup
    result = reconcile_lesson_progress(actor, lesson.public_id, 1, now=t)
    assert result.seconds_spent == 0 and float(result.max_view_fraction) == 0


def test_data_api_duration_and_private_video_fail_closed(app, monkeypatch):
    import io
    import json

    from pwd301.services.youtube_validator_service import get_youtube_metadata

    app.config["YOUTUBE_API_KEY"] = "server-test-key"
    data = {
        "items": [
            {
                "contentDetails": {"duration": "PT1H2M3S"},
                "status": {
                    "embeddable": True,
                    "uploadStatus": "processed",
                    "privacyStatus": "unlisted",
                },
            }
        ]
    }
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *args, **kwargs: io.BytesIO(json.dumps(data).encode())
    )
    assert get_youtube_metadata("abcdefghijk")["duration_seconds"] == 3723
    data["items"][0]["status"]["privacyStatus"] = "private"
    assert not get_youtube_metadata("abcdefghijk")["valid"]


def test_hls_paths_are_isolated_by_asset_and_revision(app):
    from types import SimpleNamespace

    from pwd301.services.video_drm_service import get_asset_hls_directory

    lesson = SimpleNamespace(course_id=1, id=2)
    asset = SimpleNamespace(public_id="11111111-1111-1111-1111-111111111111")
    rev1 = SimpleNamespace(public_id="22222222-2222-2222-2222-222222222222")
    rev2 = SimpleNamespace(public_id="33333333-3333-3333-3333-333333333333")
    first = get_asset_hls_directory(lesson, asset, rev1)
    assert first != get_asset_hls_directory(lesson, asset, rev2)
    assert str(asset.public_id) in str(first)


def test_unrecognized_video_cannot_fallback_to_content_session(playback_setup):
    from pwd301.services.playback_service import start_playback_session

    actor, lesson, t = playback_setup
    lesson.markdown_content = "<!-- video_url: https://example.com/untrusted.mp4 -->"
    db.session.commit()
    with pytest.raises(LessonValidationError):
        start_playback_session(actor, lesson.public_id, f"content:{lesson.public_id}", now=t)


def test_web_session_contract_and_replay_after_session_restart(playback_setup, client):
    from pwd301.models.identity import User
    from tests.conftest import login_web_user

    actor, lesson, t = playback_setup
    actor_id, lesson_id = actor.id, str(lesson.public_id)
    login_web_user(client, actor)
    start_response = client.post(
        f"/student/lessons/{lesson_id}/playback-sessions", json={"media_id": "youtube:abcdefghijk"}
    )
    assert start_response.status_code == 200
    start = start_response.get_json()["data"]
    payload = {
        "playback_session_id": start["session_id"],
        "sequence": 1,
        "media_id": "youtube:abcdefghijk",
        "position_seconds": 0,
        "playback_rate": 1,
        "state": "playing",
    }
    first = client.post(f"/student/lessons/{lesson_id}/progress", json=payload)
    assert first.status_code == 200 and first.get_json()["data"]["credited_seconds"] == 0
    db.session.remove()
    replay = client.post(f"/student/lessons/{lesson_id}/progress", json=payload)
    assert replay.get_json()["data"] == first.get_json()["data"]
    legacy = client.post(
        f"/student/lessons/{lesson_id}/progress", json={"seconds_increment": 60, "view_fraction": 1}
    )
    assert legacy.status_code == 400
    assert db.session.get(User, actor_id) is not None


def test_video_completion_preserves_minimum_and_quiz(playback_setup):
    from pwd301.services.playback_service import start_playback_session

    actor, lesson, t = playback_setup
    lesson.minimum_completion_seconds = 300
    lesson.markdown_content += '\n<!-- mini_quiz: [{"type":"TRUE_FALSE","correct_value":true}] -->'
    db.session.commit()
    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    send(actor, lesson, start, 1, t, 0)
    for index in range(1, 10):
        result = send(
            actor, lesson, start, index + 1, t + timedelta(seconds=10 * index), index * 10
        )
    assert result["is_video_complete"] and not result["is_completed"]
    assert result["seconds_spent"] == 90


def test_rate_transition_and_invalid_seek_reconcile(playback_setup):
    from pwd301.services.playback_service import start_playback_session

    actor, lesson, t = playback_setup
    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    send(actor, lesson, start, 1, t, 0)
    assert send(actor, lesson, start, 2, t + timedelta(seconds=10), 10)["credited_seconds"] == 10
    send(actor, lesson, start, 3, t + timedelta(seconds=10), 10, state="paused", playback_rate=2)
    send(actor, lesson, start, 4, t + timedelta(seconds=10), 10, playback_rate=2)
    fast = send(actor, lesson, start, 5, t + timedelta(seconds=20), 30, playback_rate=2)
    assert fast["credited_seconds"] == 10 and fast["frontier"] == 30
    forged = send(actor, lesson, start, 6, t + timedelta(seconds=21), 90, playback_rate=2)
    assert forged["seek_required"] and forged["frontier"] == 30
    from pwd301.models.notification_audit import AuditEvent

    assert (
        db.session.query(AuditEvent).filter_by(action="LESSON_PROGRESS_PACE_ANOMALY").count() == 1
    )


def test_receipt_cleanup_does_not_change_progress(playback_setup):
    from pwd301.models.playback import PlaybackReceipt
    from pwd301.services.playback_service import cleanup_playback_receipts, start_playback_session

    actor, lesson, t = playback_setup
    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    send(actor, lesson, start, 1, t, 0)
    send(actor, lesson, start, 2, t + timedelta(seconds=10), 10)
    assert cleanup_playback_receipts(now=t + timedelta(days=2)) == 2
    assert db.session.query(PlaybackReceipt).count() == 0
    with pytest.raises(LessonValidationError, match="Expected heartbeat"):
        send(actor, lesson, start, 1, t + timedelta(days=2), 0)


def test_preexisting_completion_keeps_seek_permission(playback_setup):
    from pwd301.models.course import LessonProgress
    from pwd301.services.playback_service import start_playback_session

    actor, lesson, t = playback_setup
    period = db.session.query(EnrollmentPeriod).one()
    db.session.add(
        LessonProgress(
            enrollment_period_id=period.id,
            lesson_id=lesson.id,
            seconds_spent=300,
            max_view_fraction=1,
            completed_at=t,
            acknowledged_revision_no=lesson.revision_no,
        )
    )
    db.session.commit()
    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    assert start["is_completed"] and start["is_video_complete"]
    assert start["frontier"] == start["duration"]


def test_sequence_integer_limit_requires_new_lease(playback_setup):
    from pwd301.models.playback import PlaybackSession
    from pwd301.services.playback_service import start_playback_session

    actor, lesson, t = playback_setup
    start = start_playback_session(actor, lesson.public_id, "youtube:abcdefghijk", now=t)
    lease = db.session.query(PlaybackSession).one()
    lease.next_sequence = 2_147_483_647
    db.session.commit()
    with pytest.raises(LessonValidationError, match="sequence"):
        send(actor, lesson, start, 2_147_483_647, t, 0)


def test_studio_oembed_cannot_override_data_api_embed_denial(app, monkeypatch):
    import io

    from pwd301.services import youtube_validator_service as service

    app.config["YOUTUBE_API_KEY"] = "server-test-key"
    response = io.BytesIO(b'{"title":"Public-looking title","author_name":"Author"}')
    response.status = 200
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: response)
    monkeypatch.setattr(
        service,
        "get_youtube_metadata",
        lambda *args, **kwargs: {"valid": False, "embeddable": False, "reason": "not_playable"},
    )
    check = service.verify_youtube_embeddability("abcdefghijk")
    assert not check["valid"] and check["validation_source"] == "youtube_data_api"
