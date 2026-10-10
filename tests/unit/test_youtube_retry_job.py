import urllib.error

import pytest

from pwd301.services import youtube_validator_service as youtube


def test_provider_server_error_is_transient_not_broken_video(app, monkeypatch):
    def unavailable(*args, **kwargs):
        raise urllib.error.HTTPError("https://www.youtube.com/oembed", 503, "Unavailable", {}, None)

    monkeypatch.setattr(youtube.urllib.request, "urlopen", unavailable)
    with app.app_context():
        result = youtube.verify_youtube_embeddability("abcdefghijk")
    assert result["network_error"] is True


def test_background_scan_propagates_transient_error_for_retry(app, monkeypatch):
    monkeypatch.setattr(
        youtube,
        "verify_youtube_embeddability",
        lambda *args, **kwargs: {"valid": False, "network_error": True, "reason": "offline"},
    )
    with app.app_context():
        from pwd301.extensions import db
        from pwd301.models.course import Course, LearningUnit, Lesson
        from pwd301.services.user_service import register_user

        owner = register_user("youtube-probe@example.com", "Password@123", "YouTube Probe")
        course = Course(
            course_code="YT-PROBE",
            title="YouTube Retry",
            owner_instructor_id=owner.id,
            status="PUBLISHED",
        )
        db.session.add(course)
        db.session.flush()
        unit = LearningUnit(course_id=course.id, title="Unit", position=1)
        db.session.add(unit)
        db.session.flush()
        lesson = Lesson(
            course_id=course.id,
            learning_unit_id=unit.id,
            title="YouTube",
            position=1,
            status="PUBLISHED",
            markdown_content="<!-- video_url: https://youtu.be/abcdefghijk -->",
        )
        db.session.add(lesson)
        db.session.commit()
        app.config["YOUTUBE_API_KEY"] = "synthetic-server-key-for-scheduler-test"
        from pwd301.models.operations import BackgroundJob
        from pwd301.services import background_job_service as jobs

        assert jobs._schedule_youtube_checks() == 1
        assert jobs._schedule_youtube_checks() == 1
        assert (
            db.session.query(BackgroundJob)
            .filter_by(dedupe_key=f"youtube-lesson-validation:{lesson.id}")
            .count()
            == 1
        )
        with pytest.raises(RuntimeError, match="retry"):
            youtube.scan_and_notify_broken_youtube_videos(
                course_id=course.id, lesson_id=lesson.id, retry_network_errors=True
            )


def test_durable_video_validation_job_uses_existing_retrying_scanner(app, monkeypatch):
    from pwd301.extensions import db
    from pwd301.services import background_job_service as jobs

    calls = []
    monkeypatch.setattr(
        youtube, "scan_and_notify_broken_youtube_videos", lambda **kwargs: calls.append(kwargs)
    )
    with app.app_context():
        job = jobs.enqueue_background_job(
            "CLEANUP",
            payload={"scope": "youtube-lesson-validation", "course_id": 1, "lesson_id": 2},
            run_async=False,
        )
        db.session.commit()
        assert jobs.execute_background_job(job, session=db.session) is True
    assert calls == [{"course_id": 1, "lesson_id": 2, "retry_network_errors": True}]


def test_transient_video_job_enters_existing_backoff_queue(app, monkeypatch):
    from pwd301.extensions import db
    from pwd301.services import background_job_service as jobs

    def unavailable(**kwargs):
        raise RuntimeError("Transient provider error; retry")

    monkeypatch.setattr(youtube, "scan_and_notify_broken_youtube_videos", unavailable)
    with app.app_context():
        job = jobs.enqueue_background_job(
            "CLEANUP",
            payload={"scope": "youtube-lesson-validation", "course_id": 1, "lesson_id": 2},
            run_async=False,
        )
        db.session.commit()
        claimed = jobs.claim_next_background_job()
        db.session.commit()
        assert jobs.execute_background_job(claimed) is False
        db.session.refresh(job)
        assert job.status == "QUEUED"
        assert job.attempt_count == 1
        assert job.available_at > job.created_at
