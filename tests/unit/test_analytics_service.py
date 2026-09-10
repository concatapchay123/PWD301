"""Unit tests for Analytics Engine Service (TASK-025).

Verifies:
- Accurate calculation of Admin System Overview metrics (users by role/status,
  courses distribution, enrollments, assessment grading queue, and storage).
- Zero-division resilience across all calculations (empty courses, zero students,
  zero attempts).
- Exact 4-bucket progress distribution ([0-25%), [25-50%), [50-75%), [75-100%]).
- Assessment performance evaluation breakdown (attempts, averages, pass rate, pending essays).
- Student learning overview with server timer synchronization and score release policy enforcement.
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AssessmentResult,
)
from pwd301.models.course import EnrollmentPeriod
from pwd301.models.file_import import FileAsset, FileBlob, FileRevision
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.analytics_service import (
    get_admin_system_overview,
    get_instructor_course_analytics,
    get_instructor_overview_analytics,
    get_student_learning_overview,
)
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import ForbiddenError
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure standard roles exist in test database."""
    sess: Session = db.session
    role_map: dict[str, Role] = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = sess.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        role_map[code] = role
    sess.commit()
    return role_map


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test admin user."""
    u = register_user(f"admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin Tester")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user(
        f"inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor Tester"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    return register_user(
        f"student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student Tester"
    )


def test_admin_system_overview_metrics(
    app: Flask,
    admin_user: User,
    instructor_user: User,
    student_user: User,
) -> None:
    """Test Admin System Overview correctly aggregates users, courses, storage, and enrollments."""
    sess: Session = db.session

    # 1. Create courses with different statuses
    c1 = create_course(
        actor=admin_user,
        data={"course_code": f"ADM-{uuid.uuid4().hex[:4]}", "title": "Admin Test Course 1"},
        session=sess,
    )
    c1.status = "PUBLISHED"
    sess.flush()

    c2 = create_course(
        actor=admin_user,
        data={"course_code": f"ADM-{uuid.uuid4().hex[:4]}", "title": "Admin Test Course 2"},
        session=sess,
    )
    c2.status = "DRAFT"
    sess.flush()

    # 2. Create an enrollment
    enrollment = enroll_student(actor=student_user, course_id=c1.id, session=sess)
    enrollment.current_progress_percent = Decimal("50.00")
    sess.flush()

    # 3. Create a FileBlob and FileRevision
    blob = FileBlob(
        sha256=uuid.uuid4().bytes,
        size_bytes=2048,
        detected_mime_type="application/pdf",
        storage_key=f"blobs/{uuid.uuid4().hex}.pdf",
    )
    sess.add(blob)
    sess.flush()

    asset = FileAsset(
        course_id=c1.id,
        created_by_user_id=admin_user.id,
        asset_type="RESOURCE",
        display_name="Test Resource",
        status="ACTIVE",
    )
    sess.add(asset)
    sess.flush()

    rev = FileRevision(
        file_asset_id=asset.id,
        revision_no=1,
        is_current=True,
        blob_id=blob.id,
        original_filename="test.pdf",
        size_bytes=2048,
        status="ACTIVE",
        uploaded_by_user_id=admin_user.id,
    )
    sess.add(rev)
    sess.commit()

    # Call admin overview
    overview = get_admin_system_overview(admin_user, session=sess)

    # Assertions
    assert "total_users" in overview
    assert overview["total_users"] >= 3
    assert overview["users"]["by_role"]["ADMIN"] >= 1
    assert overview["users"]["by_role"]["INSTRUCTOR"] >= 1
    assert overview["users"]["by_role"]["STUDENT"] >= 1

    assert overview["courses"]["total_courses"] >= 2
    assert overview["courses"]["by_status"]["PUBLISHED"] >= 1
    assert overview["courses"]["by_status"]["DRAFT"] >= 1

    assert overview["enrollments"]["total_enrollments"] >= 1
    assert overview["storage"]["total_bytes"] >= 2048
    assert overview["storage"]["clean_files_count"] >= 1


def test_admin_system_overview_forbidden_for_non_admin(
    app: Flask,
    instructor_user: User,
    student_user: User,
) -> None:
    """Non-admin users calling get_admin_system_overview must be rejected with ForbiddenError."""
    sess: Session = db.session

    with pytest.raises(ForbiddenError):
        get_admin_system_overview(instructor_user, session=sess)

    with pytest.raises(ForbiddenError):
        get_admin_system_overview(student_user, session=sess)


def test_zero_division_resilience(
    app: Flask,
    instructor_user: User,
    student_user: User,
) -> None:
    """Verify zero-division resilience when courses have 0 students and 0 assessment submissions."""
    sess: Session = db.session

    empty_course = create_course(
        actor=instructor_user,
        data={"course_code": f"EMPTY-{uuid.uuid4().hex[:4]}", "title": "Empty Test Course"},
        session=sess,
    )
    sess.commit()

    # 1. Course analytics for empty course
    course_analytics = get_instructor_course_analytics(
        actor=instructor_user,
        course_id=str(empty_course.public_id),
        session=sess,
    )

    assert course_analytics["enrolled_students_count"] == 0
    assert course_analytics["completion_rate_percent"] == 0.0
    assert course_analytics["average_progress_percent"] == 0.0

    dist = course_analytics["progress_distribution"]
    for bucket in ("0-25", "25-50", "50-75", "75-100"):
        assert dist[bucket]["count"] == 0
        assert dist[bucket]["percentage"] == 0.0

    perf = course_analytics["assessment_performance"]
    assert perf["total_attempts"] == 0
    assert perf["average_score"] == 0.0
    assert perf["pass_rate_percent"] == 0.0
    assert perf["pending_grading_count"] == 0

    # 2. Instructor overview with no student enrollments
    inst_overview = get_instructor_overview_analytics(
        actor=instructor_user,
        session=sess,
    )
    assert inst_overview["total_students_count"] == 0
    assert inst_overview["average_progress_percent"] == 0.0
    assert inst_overview["pending_grading_count"] == 0

    # 3. Student learning overview with no enrollments
    student_overview = get_student_learning_overview(
        actor=student_user,
        session=sess,
    )
    assert student_overview["enrolled_courses_count"] == 0
    assert student_overview["active_courses_count"] == 0
    assert student_overview["completed_courses_count"] == 0
    assert student_overview["overall_average_progress_percent"] == 0.0
    assert student_overview["upcoming_assessments"] == []
    assert student_overview["recent_results"] == []


def test_progress_distribution_buckets(
    app: Flask,
    instructor_user: User,
    setup_roles: dict[str, Role],
) -> None:
    """Verify students are precisely categorized into 4 progress distribution buckets."""
    sess: Session = db.session

    course = create_course(
        actor=instructor_user,
        data={"course_code": f"BUCKET-{uuid.uuid4().hex[:4]}", "title": "Bucket Testing Course"},
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    # Create 4 students with distinct progress: 10%, 35%, 65%, 90%
    progress_values = [Decimal("10.00"), Decimal("35.00"), Decimal("65.00"), Decimal("90.00")]
    for idx, prog in enumerate(progress_values):
        student = register_user(
            f"bucket_student_{idx}_{uuid.uuid4().hex[:4]}@example.com",
            "Password@123",
            f"Bucket Student {idx}",
        )
        enr = enroll_student(actor=student, course_id=course.id, session=sess)
        enr.current_progress_percent = prog
        sess.flush()

    sess.commit()

    analytics = get_instructor_course_analytics(
        actor=instructor_user,
        course_id=str(course.public_id),
        session=sess,
    )

    assert analytics["enrolled_students_count"] == 4
    assert analytics["average_progress_percent"] == 50.0  # (10 + 35 + 65 + 90) / 4

    dist = analytics["progress_distribution"]
    assert dist["0-25"]["count"] == 1
    assert dist["0-25"]["percentage"] == 25.0

    assert dist["25-50"]["count"] == 1
    assert dist["25-50"]["percentage"] == 25.0

    assert dist["50-75"]["count"] == 1
    assert dist["50-75"]["percentage"] == 25.0

    assert dist["75-100"]["count"] == 1
    assert dist["75-100"]["percentage"] == 25.0


def test_assessment_performance_breakdown(
    app: Flask,
    instructor_user: User,
    student_user: User,
) -> None:
    """Verify assessment evaluation metrics, average scores, pass rate, and pending grading."""
    sess: Session = db.session

    course = create_course(
        actor=instructor_user,
        data={"course_code": f"PERF-{uuid.uuid4().hex[:4]}", "title": "Performance Testing Course"},
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    assessment = Assessment(
        course_id=course.id,
        creator_user_id=instructor_user.id,
        title="Midterm Examination",
        assessment_type="MIDTERM",
        status="PUBLISHED",
        score_release_policy="IMMEDIATE",
    )
    sess.add(assessment)
    sess.flush()

    enr = enroll_student(actor=student_user, course_id=course.id, session=sess)
    period = sess.query(EnrollmentPeriod).filter(EnrollmentPeriod.enrollment_id == enr.id).first()
    assert period is not None

    # Attempt 1: Graded and passed (80%)
    att1 = AssessmentAttempt(
        assessment_id=assessment.id,
        enrollment_period_id=period.id,
        student_user_id=student_user.id,
        attempt_number=1,
        status="GRADED",
        submitted_at=utc_now(),
        graded_at=utc_now(),
    )
    sess.add(att1)
    sess.flush()

    res1 = AssessmentResult(
        attempt_id=att1.id,
        raw_score=Decimal("80.0000"),
        max_score=Decimal("100.0000"),
        percent_score=Decimal("80.0000"),
        passed=True,
        status="FINAL",
    )
    sess.add(res1)

    # Attempt 2: PENDING_GRADING (essay requiring instructor attention)
    student2 = register_user(
        f"student2_{uuid.uuid4().hex[:4]}@example.com", "Password@123", "Student Two"
    )
    enr2 = enroll_student(actor=student2, course_id=course.id, session=sess)
    period2 = sess.query(EnrollmentPeriod).filter(EnrollmentPeriod.enrollment_id == enr2.id).first()
    assert period2 is not None

    att2 = AssessmentAttempt(
        assessment_id=assessment.id,
        enrollment_period_id=period2.id,
        student_user_id=student2.id,
        attempt_number=1,
        status="PENDING_GRADING",
        submitted_at=utc_now(),
    )
    sess.add(att2)
    sess.commit()

    analytics = get_instructor_course_analytics(
        actor=instructor_user,
        course_id=str(course.public_id),
        session=sess,
    )

    perf = analytics["assessment_performance"]
    assert perf["total_attempts"] == 2
    assert perf["pending_grading_count"] == 1
    assert perf["average_score"] == 80.0
    assert perf["pass_rate_percent"] == 100.0  # 1 graded attempt which passed

    assert len(perf["assessments"]) == 1
    assess_item = perf["assessments"][0]
    assert assess_item["assessment_id"] == str(assessment.public_id)
    assert assess_item["total_attempts"] == 2
    assert assess_item["pending_grading_count"] == 1
    assert assess_item["average_score"] == 80.0
    assert assess_item["pass_rate_percent"] == 100.0


def test_student_learning_overview_deadlines_and_score_release(
    app: Flask,
    instructor_user: User,
    student_user: User,
) -> None:
    """Verify server timer synchronization for upcoming deadlines and score release filtering."""
    sess: Session = db.session

    course = create_course(
        actor=instructor_user,
        data={"course_code": f"STU-{uuid.uuid4().hex[:4]}", "title": "Student Learning Course"},
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    enr = enroll_student(actor=student_user, course_id=course.id, session=sess)
    period = sess.query(EnrollmentPeriod).filter(EnrollmentPeriod.enrollment_id == enr.id).first()
    assert period is not None

    now = utc_now()

    # Upcoming assessment (deadline in future)
    future_close = now + datetime.timedelta(days=7)
    upcoming_assess = Assessment(
        course_id=course.id,
        creator_user_id=instructor_user.id,
        title="Final Project",
        assessment_type="FINAL",
        status="PUBLISHED",
        open_at=now,
        close_at=future_close,
        time_limit_minutes=120,
    )
    sess.add(upcoming_assess)

    # Past assessment (deadline in past)
    past_close = now - datetime.timedelta(days=2)
    past_assess = Assessment(
        course_id=course.id,
        creator_user_id=instructor_user.id,
        title="Old Quiz",
        assessment_type="QUIZ",
        status="PUBLISHED",
        open_at=past_close - datetime.timedelta(days=7),
        close_at=past_close,
        score_release_policy="AFTER_CLOSE",
    )
    sess.add(past_assess)
    sess.flush()

    # Attempt with released score (AFTER_CLOSE with past deadline)
    att_released = AssessmentAttempt(
        assessment_id=past_assess.id,
        enrollment_period_id=period.id,
        student_user_id=student_user.id,
        attempt_number=1,
        status="GRADED",
        submitted_at=past_close - datetime.timedelta(hours=1),
        graded_at=past_close - datetime.timedelta(hours=1),
    )
    sess.add(att_released)
    sess.flush()

    res_released = AssessmentResult(
        attempt_id=att_released.id,
        raw_score=Decimal("95.0000"),
        max_score=Decimal("100.0000"),
        percent_score=Decimal("95.0000"),
        passed=True,
        status="FINAL",
    )
    sess.add(res_released)

    # Attempt with UNRELEASED score (score_release_policy == AFTER_CLOSE, but deadline in future)
    unreleased_assess = Assessment(
        course_id=course.id,
        creator_user_id=instructor_user.id,
        title="Unreleased Midterm",
        assessment_type="MIDTERM",
        status="PUBLISHED",
        open_at=now,
        close_at=future_close,
        score_release_policy="AFTER_CLOSE",
    )
    sess.add(unreleased_assess)
    sess.flush()

    att_unreleased = AssessmentAttempt(
        assessment_id=unreleased_assess.id,
        enrollment_period_id=period.id,
        student_user_id=student_user.id,
        attempt_number=1,
        status="GRADED",
        submitted_at=now,
        graded_at=now,
    )
    sess.add(att_unreleased)
    sess.flush()

    res_unreleased = AssessmentResult(
        attempt_id=att_unreleased.id,
        raw_score=Decimal("85.0000"),
        max_score=Decimal("100.0000"),
        percent_score=Decimal("85.0000"),
        passed=True,
        status="FINAL",
    )
    sess.add(res_unreleased)
    sess.commit()

    overview = get_student_learning_overview(actor=student_user, session=sess)

    # 1. Server time present and valid
    assert "server_time" in overview

    # 2. Upcoming assessments includes future close_at assessments
    upcoming_ids = [a["assessment_id"] for a in overview["upcoming_assessments"]]
    assert str(upcoming_assess.public_id) in upcoming_ids
    assert str(unreleased_assess.public_id) in upcoming_ids
    assert str(past_assess.public_id) not in upcoming_ids

    # 3. Recent results only includes released score
    result_attempt_ids = [r["attempt_id"] for r in overview["recent_results"]]
    assert str(att_released.public_id) in result_attempt_ids
    assert str(att_unreleased.public_id) not in result_attempt_ids  # Held by policy
