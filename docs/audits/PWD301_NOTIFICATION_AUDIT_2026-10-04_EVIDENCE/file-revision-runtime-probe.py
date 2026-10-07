"""Disposable rejected-file-revision notification probe using temporary storage."""

from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import Notification, NotificationEvent
from pwd301.services.file_service import add_file_revision, store_file_stream
from pwd301.services.scanner_service import EICAR_SIGNATURE_BYTES


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="pwd301-file-revision-probe-") as temp_dir:
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
                instructor = User(
                    email="file-revision.owner@pwd301.local",
                    password_hash="probe-only",
                    display_name="File Revision Probe Owner",
                    status="ACTIVE",
                    auth_version=1,
                )
                instructor.roles.append(Role(code="INSTRUCTOR", name="Instructor"))
                db.session.add(instructor)
                db.session.flush()

                course = Course(
                    course_code="FILE-REV-AUDIT",
                    title="File revision notification probe",
                    description="Disposable rejected-revision fixture",
                    owner_instructor_id=instructor.id,
                    status="PUBLISHED",
                )
                db.session.add(course)
                db.session.commit()

                asset = store_file_stream(
                    actor=instructor,
                    course_id=course.public_id,
                    file_stream=io.BytesIO(b"clean revision one"),
                    filename="revision-one.txt",
                    content_type="text/plain",
                    session=db.session,
                )
                rejected = add_file_revision(
                    actor=instructor,
                    asset_id=asset.public_id,
                    file_stream=io.BytesIO(b"revision two " + EICAR_SIGNATURE_BYTES),
                    filename="revision-two.txt",
                    content_type="text/plain",
                    session=db.session,
                )

                events = (
                    db.session.query(NotificationEvent)
                    .filter_by(event_type="FILE_REJECTED")
                    .all()
                )
                notifications = (
                    db.session.query(Notification)
                    .filter_by(recipient_user_id=instructor.id)
                    .all()
                )
                assert rejected.status == "REJECTED"
                assert rejected.blob_id is None
                assert len(events) == 1
                assert len(notifications) == 1
                assert notifications[0].category == "SECURITY"
                assert notifications[0].recipient_user_id == instructor.id

                print(
                    json.dumps(
                        {
                            "database": "sqlite-in-memory",
                            "revision_status": rejected.status,
                            "revision_blob_id": rejected.blob_id,
                            "event_type": events[0].event_type,
                            "event_count": len(events),
                            "notification_count": len(notifications),
                            "notification_category": notifications[0].category,
                            "recipient_matches_owner": (
                                notifications[0].recipient_user_id == instructor.id
                            ),
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
