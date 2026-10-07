"""Disposable Instructor prerequisite-rejection notification probe."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.course import Course, CoursePrerequisite
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import Notification, NotificationEvent
from pwd301.models.types import utc_now
from pwd301.services.session_auth_service import create_auth_session


def _login(client, actor: User) -> None:
    _, raw_session_key = create_auth_session(actor, session=db.session)
    db.session.commit()
    with client.session_transaction() as flask_session:
        flask_session["_user_id"] = str(actor.id)
        flask_session["auth_session_key"] = raw_session_key
        flask_session["auth_version"] = actor.auth_version
        flask_session["auth_source"] = "SESSION"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="pwd301-prereq-rejection-probe-") as temp_dir:
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
            try:
                role = Role(code="INSTRUCTOR", name="Instructor")
                requester = User(
                    email="prereq.requester@pwd301.local",
                    password_hash="probe-only",
                    display_name="Prerequisite Requester",
                    status="ACTIVE",
                    auth_version=1,
                )
                reviewer = User(
                    email="prereq.reviewer@pwd301.local",
                    password_hash="probe-only",
                    display_name="Prerequisite Reviewer",
                    status="ACTIVE",
                    auth_version=1,
                )
                requester.roles.append(role)
                reviewer.roles.append(role)
                db.session.add_all([requester, reviewer])
                db.session.flush()

                target = Course(
                    course_code="PREREQ-TARGET-AUDIT",
                    title="Target course",
                    owner_instructor_id=requester.id,
                    status="PUBLISHED",
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                prerequisite = Course(
                    course_code="PREREQ-OWNER-AUDIT",
                    title="Prerequisite course",
                    owner_instructor_id=reviewer.id,
                    status="PUBLISHED",
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                db.session.add_all([target, prerequisite])
                db.session.commit()

                client = app.test_client()
                _login(client, requester)
                staged = client.post(
                    f"/instructor/courses/{target.id}/prerequisites",
                    json={"prerequisite_course_id": prerequisite.id, "reason": "Probe request"},
                )
                assert staged.status_code == 202
                request_id = staged.get_json()["change_request_id"]

                _login(client, reviewer)
                rejected = client.post(
                    f"/instructor/prerequisite-requests/{request_id}/review",
                    json={"action": "reject", "reason": "Probe rejection"},
                )
                assert rejected.status_code == 200
                assert rejected.get_json()["status"] == "REJECTED"

                event = (
                    db.session.query(NotificationEvent)
                    .filter_by(event_type="COURSE_PREREQUISITE_REJECTED")
                    .one()
                )
                notification = (
                    db.session.query(Notification)
                    .filter_by(
                        notification_event_id=event.id,
                        recipient_user_id=requester.id,
                    )
                    .one()
                )
                assert (
                    db.session.query(CoursePrerequisite)
                    .filter_by(
                        course_id=target.id,
                        prerequisite_course_id=prerequisite.id,
                    )
                    .count()
                    == 0
                )
                assert notification.category == "COURSE"

                print(
                    json.dumps(
                        {
                            "database": "sqlite-in-memory",
                            "stage_status": staged.status_code,
                            "review_status": rejected.status_code,
                            "request_status": rejected.get_json()["status"],
                            "event_type": event.event_type,
                            "event_count": 1,
                            "notification_count": 1,
                            "recipient_matches_requester": (
                                notification.recipient_user_id == requester.id
                            ),
                            "prerequisite_link_count": 0,
                            "assertions": "passed",
                        },
                        ensure_ascii=False,
                    )
                )
            finally:
                db.session.rollback()
                db.drop_all()


if __name__ == "__main__":
    main()
