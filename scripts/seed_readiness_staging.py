"""Idempotent synthetic 20-course/50-learner fixture, guarded against live databases.

STAGING_DATABASE_URL and PWD301_TEST_DB_DISPOSABLE=1 are mandatory. Passwords
come from STAGING_ACCOUNT_PASSWORD, are never printed and are staging-only.
Optional STAGING_YOUTUBE_VIDEO_ID attaches real metadata-checkable videos; no
stubbed YouTube duration is persisted by this fixture.
"""

from __future__ import annotations

import os
import re

from sqlalchemy.engine import make_url


def main() -> None:
    target = os.environ.get("STAGING_DATABASE_URL", "")
    if not target or os.environ.get("PWD301_TEST_DB_DISPOSABLE") != "1":
        raise SystemExit("Staging target and explicit disposable acknowledgement required.")
    url = make_url(target)
    if not url.drivername.startswith("mssql") or not (url.database or "").startswith(
        "pwd301_test_"
    ):
        raise SystemExit("Only an isolated pwd301_test_* SQL Server database is supported.")
    password = os.environ.get("STAGING_ACCOUNT_PASSWORD", "")
    if len(password) < 12:
        raise SystemExit("STAGING_ACCOUNT_PASSWORD must contain at least 12 characters.")
    video_id = os.environ.get("STAGING_YOUTUBE_VIDEO_ID", "")
    if video_id and not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise SystemExit("Invalid STAGING_YOUTUBE_VIDEO_ID.")
    os.environ["TEST_DATABASE_URL"] = target
    from pwd301 import create_app
    from pwd301.extensions import db
    from pwd301.models.course import Course, LearningUnit, Lesson
    from pwd301.models.identity import Role, User
    from pwd301.services.enrollment_service import enroll_student
    from pwd301.services.user_service import assign_role_to_user, register_user

    app = create_app("testing", config_override={"SQLALCHEMY_DATABASE_URI": target})
    with app.app_context():
        for code in ("ADMIN", "INSTRUCTOR", "STUDENT"):
            if not db.session.query(Role).filter_by(code=code).first():
                db.session.add(Role(code=code, name=code.title()))
        db.session.commit()

        def account(email, name, role):
            user = db.session.query(User).filter_by(email=email).first()
            if user is None:
                user = register_user(email, password, name)
            if not user.has_role(role):
                user = assign_role_to_user(user.id, role)
            return user

        instructor = account("instructor@readiness.invalid", "Staging Instructor", "INSTRUCTOR")
        account("admin@readiness.invalid", "Staging Admin", "ADMIN")
        courses = []
        for number in range(1, 21):
            code = f"STAGING-{number:02d}"
            course = db.session.query(Course).filter_by(course_code=code).first()
            if course is None:
                course = Course(
                    course_code=code,
                    title=f"Synthetic staging course {number}",
                    owner_instructor_id=instructor.id,
                    status="PUBLISHED",
                    description="Disposable readiness fixture. No production data.",
                )
                db.session.add(course)
                db.session.flush()
                unit = LearningUnit(course_id=course.id, title="Staging lesson group", position=1)
                db.session.add(unit)
                db.session.flush()
                db.session.add(
                    Lesson(
                        course_id=course.id,
                        learning_unit_id=unit.id,
                        title="Content pacing fixture",
                        markdown_content="# Synthetic content",
                        position=1,
                        status="PUBLISHED",
                        minimum_completion_seconds=30,
                    )
                )
                if video_id:
                    db.session.add(
                        Lesson(
                            course_id=course.id,
                            learning_unit_id=unit.id,
                            title="Real YouTube playback fixture",
                            position=2,
                            status="PUBLISHED",
                            markdown_content=f"<!-- video_url: https://youtu.be/{video_id} -->",
                            minimum_completion_seconds=30,
                        )
                    )
                db.session.commit()
            courses.append(course)
        for number in range(1, 51):
            student = account(
                f"learner{number:02d}@readiness.invalid", f"Staging Learner {number}", "STUDENT"
            )
            enroll_student(student, courses[(number - 1) % 20].id)
        print("Created/retained 20 synthetic courses and 50 learners in disposable staging.")
        print(
            "YouTube fixtures attached."
            if video_id
            else "No YouTube fixture; live playback remains unverified."
        )


if __name__ == "__main__":
    main()
