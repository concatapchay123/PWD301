"""Disposable YouTube notification producer probe; uses only an in-memory SQLite DB."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.course import Course, LearningUnit, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import Notification, NotificationEvent
from pwd301.services import youtube_validator_service as youtube_service


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="pwd301-youtube-probe-") as temp_dir:
        app = create_app(
            "testing",
            config_override={
                "FILE_STORAGE_ROOT": Path(temp_dir) / "storage",
                "FILE_QUARANTINE_ROOT": Path(temp_dir) / "quarantine",
                "FILE_BACKUP_ROOT": Path(temp_dir) / "backups",
            },
        )
        with app.app_context():
            db.create_all()
            original_verifier = youtube_service.verify_youtube_embeddability
            try:
                instructor = User(
                    email="youtube.owner@pwd301.local",
                    password_hash="probe-only",
                    display_name="YouTube Probe Owner",
                    status="ACTIVE",
                    auth_version=1,
                )
                instructor_role = Role(code="INSTRUCTOR", name="Instructor")
                instructor.roles.append(instructor_role)
                db.session.add(instructor)
                db.session.flush()

                course = Course(
                    course_code="YT-AUDIT",
                    title="YouTube notification probe",
                    description="Disposable notification producer fixture",
                    owner_instructor_id=instructor.id,
                    status="PUBLISHED",
                )
                db.session.add(course)
                db.session.flush()

                unit = LearningUnit(course_id=course.id, title="Probe unit", position=1)
                db.session.add(unit)
                db.session.flush()

                lesson = Lesson(
                    course_id=course.id,
                    learning_unit_id=unit.id,
                    title="Broken video lesson",
                    position=1,
                    status="PUBLISHED",
                    markdown_content=(
                        '<!-- video_urls: '
                        '["https://www.youtube.com/watch?v=dQw4w9WgXcQ"] -->'
                    ),
                )
                db.session.add(lesson)
                db.session.commit()

                def set_verifier(result: dict[str, object]) -> None:
                    youtube_service.verify_youtube_embeddability = lambda _video_id: result

                set_verifier(
                    {
                        "valid": True,
                        "video_id": "dQw4w9WgXcQ",
                        "title": "valid fixture",
                        "author_name": "fixture",
                        "reason": None,
                        "status_code": 200,
                    }
                )
                valid_reports = youtube_service.scan_and_notify_broken_youtube_videos(
                    course_id=course.id
                )

                set_verifier(
                    {
                        "valid": False,
                        "video_id": "dQw4w9WgXcQ",
                        "title": None,
                        "author_name": None,
                        "reason": "temporary oEmbed timeout",
                        "status_code": None,
                        "network_error": True,
                    }
                )
                network_reports = youtube_service.scan_and_notify_broken_youtube_videos(
                    course_id=course.id
                )

                set_verifier(
                    {
                        "valid": False,
                        "video_id": "dQw4w9WgXcQ",
                        "title": None,
                        "author_name": None,
                        "reason": "Video không tồn tại trong oEmbed fixture.",
                        "status_code": 404,
                    }
                )
                client = app.test_client()
                unauthenticated_response = client.post(
                    f"/instructor/courses/{course.public_id}/scan-videos",
                    headers={"Accept": "application/json"},
                )
                assert unauthenticated_response.status_code == 401

                from pwd301.services.session_auth_service import create_auth_session

                _, raw_session_key = create_auth_session(instructor, session=db.session)
                db.session.commit()
                with client.session_transaction() as flask_session:
                    flask_session["_user_id"] = str(instructor.id)
                    flask_session["auth_session_key"] = raw_session_key
                    flask_session["auth_version"] = instructor.auth_version
                    flask_session["auth_source"] = "SESSION"

                authenticated_response = client.post(
                    f"/instructor/courses/{course.public_id}/scan-videos",
                    headers={"Accept": "application/json"},
                )
                authenticated_payload = authenticated_response.get_json()
                assert authenticated_response.status_code == 200
                assert authenticated_payload["success"] is True
                assert authenticated_payload["broken_count"] == 1

                first_reports = youtube_service.scan_and_notify_broken_youtube_videos(
                    course_id=course.id
                )
                first_event_count = db.session.query(NotificationEvent).count()
                first_notification_count = db.session.query(Notification).count()

                second_reports = youtube_service.scan_and_notify_broken_youtube_videos(
                    course_id=course.id
                )
                second_event_count = db.session.query(NotificationEvent).count()
                second_notification_count = db.session.query(Notification).count()

                event = (
                    db.session.query(NotificationEvent)
                    .filter_by(event_type="COURSE_LESSON_VIDEO_BROKEN")
                    .one()
                )
                notification = (
                    db.session.query(Notification)
                    .filter_by(
                        notification_event_id=event.id,
                        recipient_user_id=instructor.id,
                    )
                    .one()
                )

                assert valid_reports == []
                assert network_reports == []
                assert len(first_reports) == 1
                assert len(second_reports) == 1
                assert first_event_count == 1
                assert first_notification_count == 1
                assert second_event_count == first_event_count
                assert second_notification_count == first_notification_count
                assert event.target_id == instructor.id
                assert notification.recipient_user_id == instructor.id
                assert notification.category == "COURSE"
                assert "không tồn tại" in notification.body

                print(
                    json.dumps(
                        {
                            "database": "sqlite-in-memory",
                            "valid_reports": len(valid_reports),
                            "network_error_reports": len(network_reports),
                            "first_broken_reports": len(first_reports),
                            "second_broken_reports": len(second_reports),
                            "event_type": event.event_type,
                            "event_target_id_matches_owner": event.target_id == instructor.id,
                            "notification_category": notification.category,
                            "event_count_first": first_event_count,
                            "event_count_second": second_event_count,
                            "notification_count_first": first_notification_count,
                            "notification_count_second": second_notification_count,
                            "unauthenticated_route_status": unauthenticated_response.status_code,
                            "authenticated_route_status": authenticated_response.status_code,
                            "authenticated_route_broken_count": authenticated_payload["broken_count"],
                            "assertions": "passed",
                        },
                        ensure_ascii=False,
                    )
                )
            finally:
                youtube_service.verify_youtube_embeddability = original_verifier
                db.session.rollback()
                db.drop_all()


if __name__ == "__main__":
    main()
