"""Integration tests for comprehensive demonstration dataset seeding (TASK-029).

Verifies demo accounts, roles, course hierarchy, prerequisite graph,
question bank diversity, assessment structure, attempts & grading,
idempotency, and Flask CLI commands.
"""

from __future__ import annotations

import decimal

from werkzeug.security import check_password_hash

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AssessmentResult,
    AttemptQuestion,
    AttemptQuestionGrade,
)
from pwd301.models.course import (
    Course,
    CourseCompletionSummary,
    CoursePrerequisite,
    Enrollment,
    Lesson,
)
from pwd301.models.file_import import LessonResource
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent, Notification
from pwd301.models.question_bank import Question
from pwd301.seeds.baseline import seed_baseline
from pwd301.seeds.demo import DEMO_PASSWORD, seed_demo


def test_seed_demo_success(app):
    """Verify seed_demo populates complete realistic platform dataset."""
    with app.app_context():
        summary = seed_demo(db.session)

        # 1. Accounts verification
        assert (
            "admin@pwd301.local" in summary["users_created"]
            or "admin@pwd301.local" in summary["users_existing"]
        )
        assert "instructor1@pwd301.local" in summary["users_created"]
        assert "student1@pwd301.local" in summary["users_created"]
        assert "student4@pwd301.local" in summary["users_created"]

        users = db.session.query(User).all()
        assert len(users) >= 7
        user_map = {u.email_normalized: u for u in users}

        for email in [
            "admin@pwd301.local",
            "instructor1@pwd301.local",
            "instructor2@pwd301.local",
            "student1@pwd301.local",
            "student2@pwd301.local",
            "student3@pwd301.local",
            "student4@pwd301.local",
        ]:
            assert email in user_map
            u = user_map[email]
            assert u.status == "ACTIVE"
            assert u.email_verified_at is not None
            assert check_password_hash(u.password_hash, DEMO_PASSWORD)

        # Check roles
        assert user_map["admin@pwd301.local"].role_codes == {"STUDENT", "INSTRUCTOR", "ADMIN"}
        assert user_map["instructor1@pwd301.local"].role_codes == {"STUDENT", "INSTRUCTOR"}
        assert user_map["instructor2@pwd301.local"].role_codes == {"STUDENT", "INSTRUCTOR"}
        assert user_map["student1@pwd301.local"].role_codes == {"STUDENT"}

        # 2. Courses verification
        courses = db.session.query(Course).all()
        course_map = {c.course_code: c for c in courses}
        assert "CS101" in course_map
        assert "CS201" in course_map
        assert "CS301" in course_map

        c1 = course_map["CS101"]
        c2 = course_map["CS201"]
        c3 = course_map["CS301"]

        assert c1.status == "PUBLISHED"
        assert c2.status == "DRAFT"
        assert c3.status == "SUBMITTED_FOR_REVIEW"

        # Prerequisite check: CS201 requires CS101
        prereq = (
            db.session.query(CoursePrerequisite)
            .filter(
                CoursePrerequisite.course_id == c2.id,
                CoursePrerequisite.prerequisite_course_id == c1.id,
            )
            .first()
        )
        assert prereq is not None

        # Lessons check
        lessons_c1 = db.session.query(Lesson).filter(Lesson.course_id == c1.id).all()
        assert len(lessons_c1) >= 2
        for les in lessons_c1:
            assert les.status == "PUBLISHED"
            assert len(les.markdown_content) > 100

        # 3. Question Bank verification: 5 question types
        questions = db.session.query(Question).filter(Question.course_id == c1.id).all()
        assert len(questions) >= 5
        q_types = {q.current_revision.question_type for q in questions if q.current_revision}
        expected_types = {"SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE", "SHORT_ANSWER", "ESSAY"}
        assert expected_types.issubset(q_types)

        # 4. Assessment verification
        asm = db.session.query(Assessment).filter(Assessment.course_id == c1.id).first()
        assert asm is not None
        assert asm.status == "PUBLISHED"
        assert len(asm.sections) == 2
        assert len(asm.question_assignments) == 5

        # 5. Enrollments & Attempts verification
        # Student 1: GRADED attempt with perfect score and CourseCompletionSummary
        s1 = user_map["student1@pwd301.local"]
        enr1 = (
            db.session.query(Enrollment)
            .filter(Enrollment.student_user_id == s1.id, Enrollment.course_id == c1.id)
            .first()
        )
        assert enr1 is not None
        assert enr1.status == "ACTIVE"
        assert enr1.current_progress_percent == decimal.Decimal("100.00")

        att1 = (
            db.session.query(AssessmentAttempt)
            .filter(AssessmentAttempt.student_user_id == s1.id)
            .first()
        )
        assert att1 is not None
        assert att1.status == "GRADED"

        res1 = (
            db.session.query(AssessmentResult)
            .filter(AssessmentResult.attempt_id == att1.id)
            .first()
        )
        assert res1 is not None
        assert res1.raw_score == decimal.Decimal("20.0000")
        assert res1.passed is True

        # Essay question grading verification for Student 1
        essay_aq = (
            db.session.query(AttemptQuestion)
            .filter(
                AttemptQuestion.attempt_id == att1.id,
                AttemptQuestion.question_type_snapshot == "ESSAY",
            )
            .first()
        )
        assert essay_aq is not None
        essay_grade = (
            db.session.query(AttemptQuestionGrade)
            .filter(AttemptQuestionGrade.attempt_question_id == essay_aq.id)
            .first()
        )
        assert essay_grade is not None
        assert essay_grade.grading_status == "MANUAL_GRADED"
        assert essay_grade.awarded_points == decimal.Decimal("4.0000")
        assert essay_grade.manual_reason is not None

        summary_rec = (
            db.session.query(CourseCompletionSummary)
            .filter(CourseCompletionSummary.student_user_id == s1.id)
            .first()
        )
        assert summary_rec is not None
        assert summary_rec.ever_completed is True

        # Student 2: SUBMITTED attempt with pending essay
        s2 = user_map["student2@pwd301.local"]
        att2 = (
            db.session.query(AssessmentAttempt)
            .filter(AssessmentAttempt.student_user_id == s2.id)
            .first()
        )
        assert att2 is not None
        assert att2.status == "SUBMITTED"

        essay_aq2 = (
            db.session.query(AttemptQuestion)
            .filter(
                AttemptQuestion.attempt_id == att2.id,
                AttemptQuestion.question_type_snapshot == "ESSAY",
            )
            .first()
        )
        assert essay_aq2 is not None
        essay_grade2 = (
            db.session.query(AttemptQuestionGrade)
            .filter(AttemptQuestionGrade.attempt_question_id == essay_aq2.id)
            .first()
        )
        assert essay_grade2 is not None
        assert essay_grade2.grading_status == "PENDING"

        # Student 4: Clean account with 0 enrollments for live demo
        s4 = user_map["student4@pwd301.local"]
        enr4_count = (
            db.session.query(Enrollment).filter(Enrollment.student_user_id == s4.id).count()
        )
        assert enr4_count == 0

        # Notifications and audit trail exist
        assert db.session.query(Notification).count() >= 4
        assert db.session.query(AuditEvent).count() >= 3


def test_seed_demo_idempotency(app):
    """Verify seed_demo can be safely run multiple times without duplicating data."""
    with app.app_context():
        # First execution
        summary1 = seed_demo(db.session)
        assert summary1 is not None
        user_count1 = db.session.query(User).count()
        course_count1 = db.session.query(Course).count()
        question_count1 = db.session.query(Question).count()
        attempt_count1 = db.session.query(AssessmentAttempt).count()
        notif_count1 = db.session.query(Notification).count()
        audit_count1 = db.session.query(AuditEvent).count()
        resource_count1 = db.session.query(LessonResource).count()

        # Second execution
        summary2 = seed_demo(db.session)
        assert summary2 is not None
        user_count2 = db.session.query(User).count()
        course_count2 = db.session.query(Course).count()
        question_count2 = db.session.query(Question).count()
        attempt_count2 = db.session.query(AssessmentAttempt).count()
        notif_count2 = db.session.query(Notification).count()
        audit_count2 = db.session.query(AuditEvent).count()
        resource_count2 = db.session.query(LessonResource).count()

        # Counts must remain identical
        assert user_count1 == user_count2
        assert course_count1 == course_count2
        assert question_count1 == question_count2
        assert attempt_count1 == attempt_count2
        assert notif_count1 == notif_count2
        assert audit_count1 == audit_count2
        assert resource_count1 == resource_count2
        assert len(summary2["users_created"]) == 0
        assert len(summary2["courses_created"]) == 0
        assert summary2["notifications_created"] == 0
        assert summary2["audit_events_created"] == 0


def test_seed_demo_cli_commands(app, runner):
    """Verify Flask CLI seed-demo commands execute cleanly."""
    with app.app_context():
        # Test 'flask seed-demo'
        res1 = runner.invoke(args=["seed-demo"])
        assert res1.exit_code == 0
        assert "Done!" in res1.output
        assert "Users:" in res1.output

        # Test 'flask seed demo' (grouped command)
        res2 = runner.invoke(args=["seed", "demo"])
        assert res2.exit_code == 0
        assert "Done!" in res2.output


def test_seed_baseline_then_demo_sequence(app):
    """Verify standard deployment bootstrap sequence: baseline first, then demo."""
    with app.app_context():
        # 1. Run baseline
        baseline_summary = seed_baseline(db.session)
        assert baseline_summary["admin_created"] is True

        admin = db.session.query(User).filter(User.email_normalized == "admin@pwd301.local").first()
        assert admin is not None
        assert check_password_hash(admin.password_hash, "Admin@123456")

        # 2. Run demo seed (as docker-entrypoint.sh does)
        demo_summary = seed_demo(db.session)
        assert "admin@pwd301.local" in demo_summary["users_existing"]

        # Admin password must be updated to unified demo password
        db.session.refresh(admin)
        assert check_password_hash(admin.password_hash, DEMO_PASSWORD)

        # 3. Running baseline again preserves demo password
        seed_baseline(db.session)
        db.session.refresh(admin)
        assert check_password_hash(admin.password_hash, DEMO_PASSWORD)
