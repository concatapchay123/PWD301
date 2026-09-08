"""Unit tests for PWD301 domain models.

Validates the 71 canonical tables, column types, constraints, computed properties,
and entity relationships across all 9 domains.
"""

from __future__ import annotations

import datetime
import hashlib
import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from pwd301.extensions import db
from pwd301.models import (
    AIConversation,
    AIMessage,
    Assessment,
    AssessmentAttempt,
    AssessmentSection,
    AuditEvent,
    BackgroundJob,
    Course,
    Enrollment,
    EnrollmentPeriod,
    FileAsset,
    FileBlob,
    FileRevision,
    FileScanResult,
    Lesson,
    Question,
    QuestionRevision,
    QuestionRevisionAcceptedAnswer,
    QuestionRevisionChoice,
    Role,
    User,
)
from pwd301.models.types import utc_now

EXPECTED_71_TABLES = {
    # 1. Identity & Auth (8)
    "users",
    "roles",
    "user_roles",
    "auth_sessions",
    "jwt_token_grants",
    "user_security_tokens",
    "instructor_applications",
    "security_events",
    # 2. Course & Learning (10)
    "courses",
    "course_prerequisites",
    "course_completion_rules",
    "course_change_requests",
    "lessons",
    "enrollments",
    "enrollment_periods",
    "enrollment_events",
    "lesson_progress",
    "course_completion_summaries",
    # 3. Question Bank (5)
    "questions",
    "question_revisions",
    "question_revision_choices",
    "question_revision_accepted_answers",
    "question_provenance",
    # 4. Assessment Structure (6)
    "assessments",
    "assessment_sections",
    "assessment_question_assignments",
    "assessment_blueprints",
    "assessment_blueprint_rules",
    "assessment_question_pool",
    # 5. Assessment Attempt & Regrading (13)
    "assessment_attempts",
    "attempt_questions",
    "attempt_choice_snapshots",
    "attempt_answers",
    "attempt_answer_choices",
    "attempt_answer_events",
    "attempt_question_grades",
    "attempt_question_grade_history",
    "assessment_results",
    "assessment_result_history",
    "question_corrections",
    "regrade_jobs",
    "regrade_items",
    # 6. File Storage & Document Import (10)
    "file_blobs",
    "file_assets",
    "file_revisions",
    "file_scan_results",
    "lesson_resources",
    "question_revision_resources",
    "document_import_jobs",
    "import_questions",
    "import_duplicate_candidates",
    "import_question_resources",
    # 7. AI & RAG Retrieval (8)
    "ai_conversations",
    "ai_messages",
    "ai_requests",
    "ai_generated_question_drafts",
    "knowledge_documents",
    "knowledge_versions",
    "knowledge_chunks",
    "ai_source_usages",
    # 8. Notifications & Audit (5)
    "notification_events",
    "notifications",
    "notification_preferences",
    "email_deliveries",
    "audit_events",
    # 9. Operations & Health (6)
    "background_jobs",
    "system_alerts",
    "backup_runs",
    "grade_exports",
    "analytics_snapshots",
    "system_health_snapshots",
}


def test_exactly_71_tables_registered():
    """Verify exactly 71 canonical tables are registered in metadata."""
    registered = set(db.metadata.tables.keys())
    assert len(registered) == 71
    assert registered == EXPECTED_71_TABLES


def test_user_creation_and_defaults(app):
    """Verify User model instantiation, default values, and UUID generation."""
    with app.app_context():
        user = User(
            email="student1@pwd301.local",
            password_hash=generate_password_hash("Secret@123"),
            display_name="Student One",
        )
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.public_id is not None
        assert isinstance(user.public_id, uuid.UUID)
        assert user.status == "ACTIVE"
        assert user.auth_version == 1
        assert user.created_at is not None
        assert user.updated_at is not None


def test_user_status_check_constraint(app):
    """Verify CHECK constraint on user status."""
    with app.app_context():
        user = User(
            email="invalid_status@pwd301.local",
            password_hash="hash",
            display_name="Invalid",
            status="UNKNOWN_STATUS",
        )
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_role_code_check_constraint(app):
    """Verify CHECK constraint on role code."""
    with app.app_context():
        role = Role(code="SUPER_ADMIN", name="Super Admin")
        db.session.add(role)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_user_roles_many_to_many(app):
    """Verify many-to-many relationship between User and Role via UserRole junction."""
    with app.app_context():
        role_student = Role(code="STUDENT", name="Student")
        role_instructor = Role(code="INSTRUCTOR", name="Instructor")
        db.session.add_all([role_student, role_instructor])
        db.session.commit()

        user = User(
            email="dualrole@pwd301.local",
            password_hash=generate_password_hash("Secret@123"),
            display_name="Dual Role User",
        )
        user.roles.append(role_student)
        user.roles.append(role_instructor)
        db.session.add(user)
        db.session.commit()

        queried = db.session.get(User, user.id)
        assert queried is not None
        role_codes = {r.code for r in queried.roles}
        assert role_codes == {"STUDENT", "INSTRUCTOR"}
        assert len(queried.user_role_links) == 2


def test_course_and_lesson_hierarchy(app):
    """Verify Course and Lesson relationship with Instructor owner."""
    with app.app_context():
        instructor = User(
            email="instructor@pwd301.local",
            password_hash=generate_password_hash("Secret@123"),
            display_name="Instructor Prof",
        )
        db.session.add(instructor)
        db.session.commit()

        course = Course(
            course_code="CS101",
            title="Introduction to Computer Science",
            owner_instructor_id=instructor.id,
            status="PUBLISHED",
        )
        db.session.add(course)
        db.session.commit()

        lesson1 = Lesson(
            course_id=course.id,
            title="Lesson 1: Binary & Logic",
            markdown_content="# Binary and Boolean Logic",
            position=1,
            status="PUBLISHED",
        )
        lesson2 = Lesson(
            course_id=course.id,
            title="Lesson 2: Variables & Types",
            markdown_content="# Variables and Types",
            position=2,
            status="PUBLISHED",
        )
        db.session.add_all([lesson1, lesson2])
        db.session.commit()

        queried_course = db.session.get(Course, course.id)
        assert queried_course is not None
        assert queried_course.owner_instructor.display_name == "Instructor Prof"
        assert len(queried_course.lessons) == 2
        assert [les.position for les in queried_course.lessons] == [1, 2]


def test_enrollment_relationship(app):
    """Verify Enrollment linking Student to Course."""
    with app.app_context():
        student = User(
            email="enrolled@pwd301.local",
            password_hash="hash",
            display_name="Enrolled Student",
        )
        instructor = User(
            email="prof@pwd301.local",
            password_hash="hash",
            display_name="Course Prof",
        )
        db.session.add_all([student, instructor])
        db.session.commit()

        course = Course(
            course_code="MATH101",
            title="Calculus I",
            owner_instructor_id=instructor.id,
        )
        db.session.add(course)
        db.session.commit()

        enrollment = Enrollment(
            course_id=course.id,
            student_user_id=student.id,
            status="ACTIVE",
        )
        db.session.add(enrollment)
        db.session.commit()

        assert enrollment.id is not None
        assert enrollment.student.email == "enrolled@pwd301.local"
        assert enrollment.course.course_code == "MATH101"


def test_question_and_revisions(app):
    """Verify Question with QuestionRevision and Choices."""
    with app.app_context():
        author = User(
            email="author@pwd301.local",
            password_hash="hash",
            display_name="Question Author",
        )
        db.session.add(author)
        db.session.commit()

        course = Course(
            course_code="BIO101",
            title="Biology",
            owner_instructor_id=author.id,
        )
        db.session.add(course)
        db.session.commit()

        question = Question(
            course_id=course.id,
            creator_user_id=author.id,
            difficulty="REMEMBER",
            status="ACTIVE",
        )
        db.session.add(question)
        db.session.commit()

        revision = QuestionRevision(
            question_id=question.id,
            revision_no=1,
            question_type="SINGLE_CHOICE",
            content="What is 2 + 2?",
            created_by_user_id=author.id,
        )
        db.session.add(revision)
        db.session.commit()

        choice_a = QuestionRevisionChoice(
            question_revision_id=revision.id,
            position=1,
            content="3",
            is_correct=False,
        )
        choice_b = QuestionRevisionChoice(
            question_revision_id=revision.id,
            position=2,
            content="4",
            is_correct=True,
        )
        accepted = QuestionRevisionAcceptedAnswer(
            question_revision_id=revision.id,
            position=1,
            answer_text="4",
            answer_normalized="4",
        )
        db.session.add_all([choice_a, choice_b, accepted])
        db.session.commit()

        queried_q = db.session.get(Question, question.id)
        assert queried_q is not None
        assert len(queried_q.revisions) == 1
        rev = queried_q.revisions[0]
        assert rev.content == "What is 2 + 2?"
        assert len(rev.choices) == 2
        assert len(rev.accepted_answers) == 1


def test_assessment_and_attempt(app):
    """Verify Assessment structure and AssessmentAttempt creation."""
    with app.app_context():
        teacher = User(
            email="teacher@pwd301.local",
            password_hash="hash",
            display_name="Teacher",
        )
        student = User(
            email="test_taker@pwd301.local",
            password_hash="hash",
            display_name="Test Taker",
        )
        db.session.add_all([teacher, student])
        db.session.commit()

        course = Course(
            course_code="PHYS101",
            title="Physics I",
            owner_instructor_id=teacher.id,
        )
        db.session.add(course)
        db.session.commit()

        assessment = Assessment(
            course_id=course.id,
            title="Midterm Exam",
            assessment_type="MIDTERM",
            time_limit_minutes=60,
            status="PUBLISHED",
        )
        db.session.add(assessment)
        db.session.commit()

        section = AssessmentSection(
            assessment_id=assessment.id,
            title="Section 1: Mechanics",
            position=1,
        )
        db.session.add(section)

        enrollment = Enrollment(
            course_id=course.id,
            student_user_id=student.id,
            status="ACTIVE",
        )
        db.session.add(enrollment)
        db.session.commit()

        period = EnrollmentPeriod(
            enrollment_id=enrollment.id,
            period_no=1,
            status="ACTIVE",
        )
        db.session.add(period)
        db.session.commit()

        attempt = AssessmentAttempt(
            assessment_id=assessment.id,
            enrollment_period_id=period.id,
            student_user_id=student.id,
            attempt_number=1,
            status="IN_PROGRESS",
        )
        db.session.add(attempt)
        db.session.commit()

        assert attempt.id is not None
        assert attempt.attempt_number == 1
        assert attempt.status == "IN_PROGRESS"
        assert attempt.assessment.title == "Midterm Exam"


def test_file_blob_and_scan_results(app):
    """Verify FileBlob, FileAsset, FileRevision, and FileScanResult."""
    with app.app_context():
        uploader = User(
            email="uploader@pwd301.local",
            password_hash="hash",
            display_name="File Uploader",
        )
        db.session.add(uploader)
        db.session.commit()

        course = Course(
            course_code="CHEM101",
            title="Chemistry I",
            owner_instructor_id=uploader.id,
        )
        db.session.add(course)
        db.session.commit()

        content = b"Mock PDF file content for testing"
        sha256_hash = hashlib.sha256(content).digest()

        blob = FileBlob(
            sha256=sha256_hash,
            size_bytes=len(content),
            detected_mime_type="application/pdf",
            storage_key="blobs/test_sha256.pdf",
            status="PRESENT",
        )
        db.session.add(blob)
        db.session.commit()

        asset = FileAsset(
            course_id=course.id,
            created_by_user_id=uploader.id,
            asset_type="RESOURCE",
            display_name="Syllabus.pdf",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.commit()

        revision = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            blob_id=blob.id,
            original_filename="Syllabus.pdf",
            declared_mime_type="application/pdf",
            size_bytes=len(content),
            status="SAFE",
            uploaded_by_user_id=uploader.id,
        )
        db.session.add(revision)
        db.session.commit()

        scan = FileScanResult(
            file_revision_id=revision.id,
            scan_type="MALWARE",
            engine="CLAMAV",
            status="PASS",
        )
        db.session.add(scan)
        db.session.commit()

        assert blob.id is not None
        assert asset.id is not None
        assert revision.id is not None
        assert scan.id is not None
        assert revision.blob.storage_key == "blobs/test_sha256.pdf"


def test_ai_conversation_and_messages(app):
    """Verify AIConversation and AIMessage persistence."""
    with app.app_context():
        user = User(
            email="aistudent@pwd301.local",
            password_hash="hash",
            display_name="AI Student",
        )
        db.session.add(user)
        db.session.commit()

        expires = utc_now() + datetime.timedelta(minutes=30)
        conv = AIConversation(
            user_id=user.id,
            context_type="GLOBAL",
            expires_at=expires,
            status="ACTIVE",
        )
        db.session.add(conv)
        db.session.commit()

        msg = AIMessage(
            conversation_id=conv.id,
            sender="USER",
            content="Hello, tutor!",
            sequence_no=1,
        )
        db.session.add(msg)
        db.session.commit()

        assert conv.id is not None
        assert msg.id is not None
        assert msg.conversation.user.display_name == "AI Student"


def test_audit_event_and_background_job(app):
    """Verify AuditEvent and BackgroundJob models."""
    with app.app_context():
        admin = User(
            email="auditor@pwd301.local",
            password_hash="hash",
            display_name="Auditor",
        )
        db.session.add(admin)
        db.session.commit()

        audit = AuditEvent(
            actor_user_id=admin.id,
            actor_roles_snapshot="ADMIN",
            action="USER_LOGIN",
            target_type="users",
            target_id=admin.id,
            after_json='{"ip": "127.0.0.1"}',
        )
        db.session.add(audit)

        job = BackgroundJob(
            job_type="FILE_SCAN",
            status="QUEUED",
            priority=10,
            payload_json='{"file_id": 1}',
        )
        db.session.add(job)
        db.session.commit()

        assert audit.id is not None
        assert audit.event_id is not None
        assert job.id is not None
        assert job.job_key is not None
        assert job.status == "QUEUED"


def test_course_code_and_title_normalization(app):
    """Verify application-level normalization and uniqueness for course_code and title."""
    with app.app_context():
        course = Course(
            course_code="  cs101-web  ",
            title="  Web Development Fundamentals  ",
            status="DRAFT",
        )
        # Immediate in-memory normalization via @validates
        assert course.course_code_normalized == "CS101-WEB"
        assert course.title_normalized == "web development fundamentals"

        db.session.add(course)
        db.session.commit()

        queried = db.session.get(Course, course.id)
        assert queried is not None
        assert queried.course_code_normalized == "CS101-WEB"
        assert queried.title_normalized == "web development fundamentals"

        # Test update normalization
        queried.course_code = "  cs101-revised  "
        queried.title = "  Revised Web Fundamentals  "
        assert queried.course_code_normalized == "CS101-REVISED"
        assert queried.title_normalized == "revised web fundamentals"
        db.session.commit()

        refreshed = db.session.get(Course, course.id)
        assert refreshed is not None
        assert refreshed.course_code_normalized == "CS101-REVISED"
        assert refreshed.title_normalized == "revised web fundamentals"

        # Test uniqueness constraint on normalized course_code
        duplicate_code_course = Course(
            course_code="CS101-REVISED",
            title="Different Title",
            status="DRAFT",
        )
        db.session.add(duplicate_code_course)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test uniqueness constraint on normalized title
        duplicate_title_course = Course(
            course_code="UNIQUE-CODE",
            title="revised web fundamentals",
            status="DRAFT",
        )
        db.session.add(duplicate_title_course)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_soft_delete_architectural_docstrings():
    """Verify that models with deleted_at include the required architectural notice."""
    required_notice = (
        "Lưu ý kiến trúc: Model này sử dụng cơ chế Soft-delete (deleted_at). "
        "Do DB áp dụng mặc định NO ACTION cho Foreign Keys, tầng Application Service "
        "phải tự chịu trách nhiệm xử lý cascade data (ẩn/xóa dữ liệu con) bằng code Python."
    )
    models_with_soft_delete = [
        Course,
        Lesson,
        Question,
        Assessment,
        FileAsset,
        FileBlob,
    ]
    for model_cls in models_with_soft_delete:
        assert model_cls.__doc__ is not None, f"{model_cls.__name__} has no docstring"
        normalized_doc = " ".join(model_cls.__doc__.split())
        assert required_notice in normalized_doc, (
            f"{model_cls.__name__} missing soft-delete architectural notice"
        )


def test_filtered_indexes_in_metadata():
    """Verify that filtered indexes are defined with dialect-aware WHERE clauses."""
    from pwd301.models import (
        AIConversation,
        AttemptQuestionGrade,
        BackgroundJob,
        FileRevision,
        Notification,
    )

    models_and_indexes = [
        (AIConversation, "ix_ai_conversations_user_active"),
        (AIConversation, "ix_ai_conversations_expiry"),
        (AttemptQuestionGrade, "ix_question_grades_pending"),
        (FileRevision, "ux_file_revisions_active"),
        (FileRevision, "ix_file_revisions_recovery"),
        (Notification, "ix_notifications_user_unread"),
        (Notification, "ix_notifications_expiry"),
        (BackgroundJob, "ux_jobs_dedupe"),
    ]

    for model_cls, idx_name in models_and_indexes:
        table = model_cls.__table__  # type: ignore[attr-defined]
        matching = [idx for idx in table.indexes if idx.name == idx_name]
        assert len(matching) == 1, f"Missing index {idx_name} on {table.name}"
        idx = matching[0]
        assert idx.dialect_options["mssql"]["where"] is not None, (
            f"Index {idx_name} missing mssql_where"
        )
        assert idx.dialect_options["sqlite"]["where"] is not None, (
            f"Index {idx_name} missing sqlite_where"
        )
