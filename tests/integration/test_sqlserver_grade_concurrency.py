"""Opt-in SQL Server row-version race coverage for manual grading."""

from __future__ import annotations

import concurrent.futures
import os
import threading
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa
from flask_migrate import upgrade

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AttemptQuestion,
    AttemptQuestionGrade,
    AttemptQuestionGradeHistory,
)
from pwd301.models.course import Course, Enrollment, EnrollmentPeriod
from pwd301.models.identity import Role, User
from pwd301.models.question_bank import Question, QuestionRevision
from pwd301.services.attempt_service import grade_essay_question
from pwd301.services.exceptions import ConflictError
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import require_disposable_sqlserver_target


@pytest.mark.integration
def test_sqlserver_manual_grade_row_version_race(monkeypatch):
    database_url = os.environ.get("SQLSERVER_CONCURRENCY_URL")
    if not database_url:
        pytest.skip("SQLSERVER_CONCURRENCY_URL is required for disposable SQL Server coverage")
    require_disposable_sqlserver_target(database_url)

    monkeypatch.setenv("DATABASE_URL", database_url)
    app = create_app("development")

    with app.app_context():
        upgrade(directory="migrations")
        session = db.session
        for code, name in (("STUDENT", "Student"), ("INSTRUCTOR", "Instructor")):
            if session.query(Role).filter(Role.code == code).first() is None:
                session.add(Role(code=code, name=name))
        session.commit()

        suffix = uuid.uuid4().hex[:12]
        instructor = register_user(
            f"sqlserver-grade-instructor-{suffix}@example.com",
            "Password@123",
            "SQL Server Grade Instructor",
            session=session,
        )
        assign_role_to_user(instructor.id, "INSTRUCTOR", session=session)
        student = register_user(
            f"sqlserver-grade-student-{suffix}@example.com",
            "Password@123",
            "SQL Server Grade Student",
            session=session,
        )

        now = datetime.now(UTC)
        course = Course(
            course_code=f"SQL-RACE-{suffix}",
            course_code_normalized=f"SQL-RACE-{suffix}".upper(),
            title=f"SQL Server row-version race {suffix}",
            title_normalized=f"SQL SERVER ROW-VERSION RACE {suffix}".upper(),
            owner_instructor_id=instructor.id,
            status="PUBLISHED",
            published_at=now,
        )
        session.add(course)
        session.flush()

        assessment = Assessment(
            course_id=course.id,
            creator_user_id=instructor.id,
            title="Concurrent essay grading",
            assessment_type="QUIZ",
            status="PUBLISHED",
            open_at=now - timedelta(hours=1),
            close_at=now + timedelta(hours=1),
            passing_percent=50,
            published_at=now,
        )
        question = Question(
            course_id=course.id,
            creator_user_id=instructor.id,
            difficulty="REMEMBER",
            status="ACTIVE",
        )
        revision = QuestionRevision(
            question=question,
            revision_no=1,
            is_current=True,
            question_type="ESSAY",
            content="Explain optimistic concurrency.",
            change_type="INITIAL",
            created_by_user_id=instructor.id,
        )
        enrollment = Enrollment(student_user_id=student.id, course_id=course.id, status="ACTIVE")
        period = EnrollmentPeriod(enrollment=enrollment, period_no=1, status="ACTIVE")
        attempt = AssessmentAttempt(
            assessment=assessment,
            enrollment_period=period,
            student_user_id=student.id,
            attempt_number=1,
            status="PENDING_GRADING",
            started_at=now - timedelta(minutes=10),
            submitted_at=now,
        )
        attempt_question = AttemptQuestion(
            attempt=attempt,
            source_question=question,
            source_question_revision=revision,
            position=1,
            question_type_snapshot="ESSAY",
            content_snapshot=revision.content,
            points_assigned=10,
        )
        session.add_all([assessment, question, enrollment, attempt, attempt_question])
        session.commit()

        grade_essay_question(
            actor=instructor,
            attempt_id=attempt.id,
            attempt_question_id=attempt_question.id,
            awarded_points=4,
            reason="Initial manual grade",
            session=session,
        )
        session.expire_all()
        persisted_grade = session.get(AttemptQuestionGrade, attempt_question.id)
        assert persisted_grade is not None
        assert persisted_grade.row_version is not None
        expected_row_version = bytes(persisted_grade.row_version)

        barrier = threading.Barrier(2)
        attempt_id = attempt.id
        attempt_question_id = attempt_question.id
        instructor_id = instructor.id

        def worker(points: int):
            with app.app_context():
                worker_session = db.session
                actor = worker_session.get(User, instructor_id)
                grade = worker_session.get(AttemptQuestionGrade, attempt_question_id)
                assert actor is not None
                assert grade is not None
                assert grade.row_version == expected_row_version
                barrier.wait(timeout=15)
                try:
                    result = grade_essay_question(
                        actor=actor,
                        attempt_id=attempt_id,
                        attempt_question_id=attempt_question_id,
                        awarded_points=points,
                        reason=f"Concurrent grade {points}",
                        expected_row_version=expected_row_version,
                        session=worker_session,
                    )
                    return "winner", result
                except ConflictError:
                    worker_session.rollback()
                    return "conflict", None
                finally:
                    db.session.remove()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(worker, (7, 8)))

        assert [outcome[0] for outcome in outcomes].count("winner") == 1
        assert [outcome[0] for outcome in outcomes].count("conflict") == 1

        session.expire_all()
        final_grade = session.get(AttemptQuestionGrade, attempt_question_id)
        assert final_grade is not None
        assert final_grade.awarded_points in (7, 8)
        history_count = session.execute(
            sa.select(sa.func.count())
            .select_from(AttemptQuestionGradeHistory)
            .where(AttemptQuestionGradeHistory.attempt_question_id == attempt_question_id)
        ).scalar_one()
        assert history_count == 2
        db.session.remove()
