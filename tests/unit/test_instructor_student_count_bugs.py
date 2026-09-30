"""Unit tests for instructor dashboard student count bug fixes.

Verifies:
1. Student deduplication: 1 student enrolled in 2+ courses of the same instructor is counted as 1 student.
2. Left student exclusion: Students with status='LEFT' are excluded from total_students and enrolled_count.
3. Suspended student exclusion: Students with status='SUSPENDED' or suspended_at set are excluded.
4. Archived course exclusion: Courses with status='ARCHIVED' do not contribute to active student counts.
5. Endpoint consistency: enrolled_count from get_instructor_overview_analytics matches _serialize_course.
6. Progress calculation: overall_avg_progress excludes students who left.
7. Pure Headless REST envelope: /instructor/dashboard returns {"success": true, "data": ...} while preserving backwards compatibility.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.blueprints.instructor.routes import _serialize_course
from pwd301.extensions import db
from pwd301.models.identity import User
from pwd301.services.analytics_service import get_instructor_overview_analytics
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student, leave_course
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def instructor_actor(app: Flask) -> User:
    """Create test instructor user."""
    sess: Session = db.session
    user = register_user(
        f"test_inst_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Prof. Tester",
    )
    user = assign_role_to_user(user.id, "INSTRUCTOR")
    user.email_verified_at = user.created_at
    sess.commit()
    return user


@pytest.fixture
def student_factory(app: Flask) -> Any:
    """Factory to create student users."""
    def _create(name: str = "Student") -> User:
        sess: Session = db.session
        u = register_user(
            f"stu_{uuid.uuid4().hex[:6]}@example.com",
            "Password@123",
            name,
        )
        u = assign_role_to_user(u.id, "STUDENT")
        u.email_verified_at = u.created_at
        sess.commit()
        return u
    return _create


def test_unique_students_deduplication_across_courses(
    app: Flask,
    instructor_actor: User,
    student_factory: Any,
) -> None:
    """Bug B-01: 1 student enrolled in 2 courses must be counted as 1 unique student."""
    sess: Session = db.session

    c1 = create_course(
        instructor_actor,
        {"course_code": f"DEDUP1-{uuid.uuid4().hex[:4]}", "title": "Course 1"},
        session=sess,
    )
    c2 = create_course(
        instructor_actor,
        {"course_code": f"DEDUP2-{uuid.uuid4().hex[:4]}", "title": "Course 2"},
        session=sess,
    )
    c1.status = "PUBLISHED"
    c2.status = "PUBLISHED"
    sess.flush()

    student_shared = student_factory("Shared Student")
    enroll_student(student_shared, c1.id, session=sess)
    enroll_student(student_shared, c2.id, session=sess)
    sess.commit()

    overview = get_instructor_overview_analytics(instructor_actor, session=sess)

    # Must be 1 unique student, NOT 2 enrollments!
    assert overview["total_students"] == 1
    assert overview["total_students_count"] == 1
    assert overview["active_enrollments_count"] == 2  # 2 active enrollment records


def test_left_student_excluded_from_counts(
    app: Flask,
    instructor_actor: User,
    student_factory: Any,
) -> None:
    """Bug B-02: Student who withdrew (LEFT) must NOT be counted in total_students or enrolled_count."""
    sess: Session = db.session

    course = create_course(
        instructor_actor,
        {"course_code": f"LEFT-{uuid.uuid4().hex[:4]}", "title": "Left Testing Course"},
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    active_student = student_factory("Active Student")
    enroll_student(active_student, course.id, session=sess)

    left_student = student_factory("Left Student")
    enroll_student(left_student, course.id, session=sess)
    leave_course(left_student, course.id, session=sess)
    sess.commit()

    overview = get_instructor_overview_analytics(instructor_actor, session=sess)

    # Only active student should be counted
    assert overview["total_students"] == 1
    assert overview["total_students_count"] == 1
    assert overview["active_enrollments_count"] == 1

    # Check course level in overview
    c_overview = [c for c in overview["courses"] if c["course_id"] == str(course.public_id)][0]
    assert c_overview["enrolled_count"] == 1


def test_suspended_student_excluded_from_counts(
    app: Flask,
    instructor_actor: User,
    student_factory: Any,
) -> None:
    """Bug B-03: Student who is SUSPENDED must NOT be counted as active student."""
    sess: Session = db.session

    course = create_course(
        instructor_actor,
        {"course_code": f"SUSP-{uuid.uuid4().hex[:4]}", "title": "Suspended Test Course"},
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    active_student = student_factory("Active Student")
    enroll_student(active_student, course.id, session=sess)

    suspended_student = student_factory("Suspended Student")
    enroll_student(suspended_student, course.id, session=sess)

    # Suspend student
    suspended_student.status = "SUSPENDED"
    suspended_student.suspended_at = suspended_student.created_at
    sess.commit()

    overview = get_instructor_overview_analytics(instructor_actor, session=sess)

    # Only active non-suspended student should be counted
    assert overview["total_students"] == 1
    assert overview["total_students_count"] == 1


def test_dashboard_and_serialize_course_consistency(
    app: Flask,
    instructor_actor: User,
    student_factory: Any,
) -> None:
    """Bug B-05 & B-06: enrolled_count must match between overview analytics and _serialize_course."""
    sess: Session = db.session

    course = create_course(
        instructor_actor,
        {"course_code": f"SYNC-{uuid.uuid4().hex[:4]}", "title": "Consistency Test Course"},
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    s1 = student_factory("Student 1")
    s2 = student_factory("Student 2")
    s3 = student_factory("Student 3")

    enroll_student(s1, course.id, session=sess)
    enroll_student(s2, course.id, session=sess)
    enroll_student(s3, course.id, session=sess)
    leave_course(s3, course.id, session=sess)  # S3 left
    sess.commit()

    overview = get_instructor_overview_analytics(instructor_actor, session=sess)
    c_overview = [c for c in overview["courses"] if c["course_id"] == str(course.public_id)][0]

    serialized = _serialize_course(course)

    # Both must report exactly 2 active students
    assert c_overview["enrolled_count"] == 2
    assert serialized["enrolled_count"] == 2
    assert serialized["enrollments_count"] == 2


def test_progress_calculation_excludes_left_students(
    app: Flask,
    instructor_actor: User,
    student_factory: Any,
) -> None:
    """Bug B-08: Students who left (0% progress) must not pull down overall progress."""
    sess: Session = db.session

    course = create_course(
        instructor_actor,
        {"course_code": f"PROG-{uuid.uuid4().hex[:4]}", "title": "Progress Test Course"},
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    s1 = student_factory("Good Student")
    enr1 = enroll_student(s1, course.id, session=sess)
    enr1.current_progress_percent = Decimal("80.00")

    s2 = student_factory("Left Student")
    enr2 = enroll_student(s2, course.id, session=sess)
    enr2.current_progress_percent = Decimal("0.00")
    leave_course(s2, course.id, session=sess)
    sess.commit()

    overview = get_instructor_overview_analytics(instructor_actor, session=sess)

    # Progress should be 80.0% (from active student only), not (80 + 0) / 2 = 40.0%
    assert overview["average_progress_percent"] == 80.0


def test_archived_courses_excluded_from_active_student_count(
    app: Flask,
    instructor_actor: User,
    student_factory: Any,
) -> None:
    """Bug B-04: Archived courses must not contribute to active student counts."""
    sess: Session = db.session

    c_active = create_course(
        instructor_actor,
        {"course_code": f"ACTV-{uuid.uuid4().hex[:4]}", "title": "Active Course"},
        session=sess,
    )
    c_active.status = "PUBLISHED"

    c_archived = create_course(
        instructor_actor,
        {"course_code": f"ARCH-{uuid.uuid4().hex[:4]}", "title": "Old Archived Course"},
        session=sess,
    )
    c_archived.status = "PUBLISHED"
    sess.flush()

    s1 = student_factory("Current Student")
    enroll_student(s1, c_active.id, session=sess)

    s2 = student_factory("Past Student")
    enroll_student(s2, c_archived.id, session=sess)

    # Course archived at semester end
    c_archived.status = "ARCHIVED"
    sess.commit()

    overview = get_instructor_overview_analytics(instructor_actor, session=sess)

    # Active students should only count s1 (from active course)
    assert overview["total_students"] == 1
    assert overview["total_students_count"] == 1


def test_dashboard_endpoint_headless_envelope(
    client: FlaskClient,
    instructor_actor: User,
    student_factory: Any,
) -> None:
    """Bug B-09: /instructor/dashboard returns {"success": true, "data": ...} with root compatibility."""
    sess: Session = db.session

    course = create_course(
        instructor_actor,
        {"course_code": f"ENV-{uuid.uuid4().hex[:4]}", "title": "Envelope Test Course"},
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    s1 = student_factory("Enrolled Student")
    enroll_student(s1, course.id, session=sess)
    sess.commit()

    # Login as instructor
    client.post("/auth/login", json={"email": instructor_actor.email, "password": "Password@123"})

    resp = client.get("/instructor/dashboard")
    assert resp.status_code == 200
    json_data = resp.get_json()

    # Headless standard
    assert json_data.get("success") is True
    assert "data" in json_data
    assert json_data["data"]["total_students"] == 1

    # Backwards compatibility root level
    assert json_data["total_students"] == 1
    assert json_data["managed_courses_count"] >= 1


def test_dashboard_endpoint_scope_assigned_vs_all_for_admin(
    client: FlaskClient,
    instructor_actor: User,
    student_factory: Any,
) -> None:
    """Dashboard endpoint defaults to assigned courses for admin, allows scope=all."""
    sess: Session = db.session

    # 1. Course owned by regular instructor
    c_ins = create_course(
        instructor_actor,
        {"course_code": f"INS-{uuid.uuid4().hex[:4]}", "title": "Instructor Course"},
        session=sess,
    )
    c_ins.status = "PUBLISHED"

    # 2. Admin user who owns 1 course
    admin_u = register_user(
        f"admin_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Admin Guy",
        session=sess,
    )
    assign_role_to_user(admin_u.id, "INSTRUCTOR", session=sess)
    assign_role_to_user(admin_u.id, "ADMIN", session=sess)
    sess.commit()

    c_adm = create_course(
        admin_u,
        {"course_code": f"ADM-{uuid.uuid4().hex[:4]}", "title": "Admin Course"},
        session=sess,
    )
    c_adm.status = "PUBLISHED"
    sess.commit()

    # Login as admin
    client.post("/auth/login", json={"email": admin_u.email, "password": "Password@123"})

    # Default scope: assigned
    resp_def = client.get("/instructor/dashboard")
    assert resp_def.status_code == 200
    data_def = resp_def.get_json()["data"]
    assert data_def["scope"] == "assigned"
    assert data_def["managed_courses_count"] == 1
    assert len(data_def["courses"]) == 1
    assert data_def["courses"][0]["course_code"] == c_adm.course_code
    assert data_def["assigned_courses_count"] == 1
    assert data_def["total_platform_courses_count"] >= 2

    # Scope all
    resp_all = client.get("/instructor/dashboard?scope=all")
    assert resp_all.status_code == 200
    data_all = resp_all.get_json()["data"]
    assert data_all["scope"] == "all"
    assert data_all["managed_courses_count"] >= 2
    assert len(data_all["courses"]) >= 2

