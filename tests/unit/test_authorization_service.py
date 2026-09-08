"""Unit tests for authorization service, role management, and resource ownership rules."""

from __future__ import annotations

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.models.identity import AnonymousUser, Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import Question
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import (
    can_access_attempt,
    can_access_student_data,
    can_grade_attempt,
    can_manage_assessment,
    can_manage_course,
    can_manage_lesson,
    can_manage_question,
    can_submit_attempt,
    can_view_course,
    require_attempt_submission_owner,
    require_course_manager,
    require_student_data_access,
)
from pwd301.services.exceptions import (
    ForbiddenError,
    InvalidRoleAssignmentError,
    ResourceNotFoundError,
    UserNotFoundError,
)
from pwd301.services.user_service import (
    assign_role_to_user,
    register_user,
    remove_role_from_user,
    validate_role_combination,
)


@pytest.fixture
def test_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles are in the test database."""
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
def student_user(app: Flask, test_roles: dict[str, Role]) -> User:
    """Create a standard student user."""
    return register_user("student_test@example.com", "Password@123", "Student Tester")


@pytest.fixture
def student_user_2(app: Flask, test_roles: dict[str, Role]) -> User:
    """Create a second student user."""
    return register_user("student2_test@example.com", "Password@123", "Student Two")


@pytest.fixture
def instructor_user(app: Flask, test_roles: dict[str, Role]) -> User:
    """Create an instructor user with STUDENT + INSTRUCTOR roles."""
    user = register_user("instructor_test@example.com", "Password@123", "Instructor One")
    return assign_role_to_user(user.id, "INSTRUCTOR")


@pytest.fixture
def other_instructor(app: Flask, test_roles: dict[str, Role]) -> User:
    """Create a second instructor user."""
    user = register_user("instructor2_test@example.com", "Password@123", "Instructor Two")
    return assign_role_to_user(user.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, test_roles: dict[str, Role]) -> User:
    """Create an admin user with STUDENT + INSTRUCTOR + ADMIN roles."""
    user = register_user("admin_test@example.com", "Password@123", "Admin Tester")
    return assign_role_to_user(user.id, "ADMIN")


@pytest.fixture
def course_sample(app: Flask, instructor_user: User) -> Course:
    """Create a sample published course owned by instructor_user."""
    sess: Session = db.session
    course = Course(
        course_code="CS101",
        course_code_normalized="CS101",
        title="Introduction to Computer Science",
        title_normalized="introduction to computer science",
        status="PUBLISHED",
        owner_instructor_id=instructor_user.id,
    )
    sess.add(course)
    sess.commit()
    return course


@pytest.fixture
def draft_course(app: Flask, instructor_user: User) -> Course:
    """Create a sample draft course owned by instructor_user."""
    sess: Session = db.session
    course = Course(
        course_code="CS102",
        course_code_normalized="CS102",
        title="Advanced Data Structures",
        title_normalized="advanced data structures",
        status="DRAFT",
        owner_instructor_id=instructor_user.id,
    )
    sess.add(course)
    sess.commit()
    return course


# ==============================================================================
# 1. User Role Model & Cumulative Hierarchy Tests
# ==============================================================================


def test_user_role_methods_cumulative(
    student_user: User,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Verify cumulative role hierarchy (AUTH-002)."""
    # Student: only STUDENT
    assert student_user.has_role("STUDENT") is True
    assert student_user.has_role("INSTRUCTOR") is False
    assert student_user.has_role("ADMIN") is False
    assert student_user.is_student is True
    assert student_user.is_instructor is False
    assert student_user.is_admin is False

    # Instructor: INSTRUCTOR + STUDENT
    assert instructor_user.has_role("STUDENT") is True
    assert instructor_user.has_role("INSTRUCTOR") is True
    assert instructor_user.has_role("ADMIN") is False
    assert instructor_user.is_student is True
    assert instructor_user.is_instructor is True
    assert instructor_user.is_admin is False

    # Admin: ADMIN + INSTRUCTOR + STUDENT
    assert admin_user.has_role("STUDENT") is True
    assert admin_user.has_role("INSTRUCTOR") is True
    assert admin_user.has_role("ADMIN") is True
    assert admin_user.is_student is True
    assert admin_user.is_instructor is True
    assert admin_user.is_admin is True

    # Case insensitivity
    assert student_user.has_role("student") is True
    assert instructor_user.has_role("Instructor") is True
    assert admin_user.has_role("admin") is True

    # has_any_role and has_all_roles
    assert student_user.has_any_role("STUDENT", "ADMIN") is True
    assert student_user.has_any_role("INSTRUCTOR", "ADMIN") is False
    assert admin_user.has_all_roles("STUDENT", "INSTRUCTOR", "ADMIN") is True
    assert instructor_user.has_all_roles("STUDENT", "INSTRUCTOR") is True
    assert instructor_user.has_all_roles("STUDENT", "ADMIN") is False


def test_anonymous_user_safety() -> None:
    """Verify AnonymousUser returns safe default False without throwing exceptions."""
    anon = AnonymousUser()
    assert anon.has_role("STUDENT") is False
    assert anon.has_role("INSTRUCTOR") is False
    assert anon.has_role("ADMIN") is False
    assert anon.has_any_role("STUDENT", "ADMIN") is False
    assert anon.has_all_roles("STUDENT") is False
    assert anon.is_admin is False
    assert anon.is_instructor is False
    assert anon.is_student is False
    assert anon.role_codes == set()


# ==============================================================================
# 2. Role Assignment & Validation Lifecycle (AUTH-002)
# ==============================================================================


def test_validate_role_combinations() -> None:
    """Test allowed cumulative combinations per AUTH-002."""
    assert validate_role_combination({"STUDENT"}) is True
    assert validate_role_combination({"STUDENT", "INSTRUCTOR"}) is True
    assert validate_role_combination({"STUDENT", "INSTRUCTOR", "ADMIN"}) is True

    # Invalid partial sets
    assert validate_role_combination(set()) is False
    assert validate_role_combination({"INSTRUCTOR"}) is False
    assert validate_role_combination({"ADMIN"}) is False
    assert validate_role_combination({"STUDENT", "ADMIN"}) is False
    assert validate_role_combination({"GUEST"}) is False


def test_assign_and_remove_role_lifecycle(student_user: User, admin_user: User) -> None:
    """Test adding and removing roles with automatic closure and audit records."""
    sess: Session = db.session

    initial_auth_version = student_user.auth_version

    # Promote Student -> Instructor
    updated = assign_role_to_user(
        user_id=student_user.id,
        role_code="INSTRUCTOR",
        assigned_by_user_id=admin_user.id,
        reason="Promoted to instructor",
    )
    assert updated.has_role("INSTRUCTOR") is True
    assert updated.has_role("STUDENT") is True
    assert updated.auth_version > initial_auth_version

    # Check AuditEvent created
    audit = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.target_id == student_user.id,
            AuditEvent.action == "USER_ROLE_ASSIGNED",
        )
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert audit is not None
    assert audit.actor_user_id == admin_user.id
    assert audit.reason == "Promoted to instructor"
    assert audit.performed_as_admin is True

    # Promote further -> Admin
    updated = assign_role_to_user(student_user.id, "ADMIN")
    assert updated.has_role("ADMIN") is True
    assert updated.has_role("INSTRUCTOR") is True
    assert updated.has_role("STUDENT") is True

    # Downgrade: removing INSTRUCTOR removes ADMIN too to preserve cumulative rule
    updated = remove_role_from_user(student_user.id, "INSTRUCTOR")
    assert updated.has_role("ADMIN") is False
    assert updated.has_role("INSTRUCTOR") is False
    assert updated.has_role("STUDENT") is True

    # Cannot remove baseline STUDENT role
    with pytest.raises(InvalidRoleAssignmentError, match="Cannot remove baseline STUDENT"):
        remove_role_from_user(student_user.id, "STUDENT")

    # Invalid role code rejected
    with pytest.raises(InvalidRoleAssignmentError, match="Invalid role code"):
        assign_role_to_user(student_user.id, "SUPER_USER")

    # Non-existent user
    with pytest.raises(UserNotFoundError):
        assign_role_to_user(999999, "INSTRUCTOR")


# ==============================================================================
# 3. Course Access & Management Rules
# ==============================================================================


def test_can_view_course_rules(
    course_sample: Course,
    draft_course: Course,
    student_user: User,
    instructor_user: User,
    other_instructor: User,
    admin_user: User,
) -> None:
    """Test course visibility policies (02_PERMISSION_MATRIX.md)."""
    # 1. Published course is visible to everyone
    assert can_view_course(None, course_sample) is True
    assert can_view_course(student_user, course_sample) is True
    assert can_view_course(instructor_user, course_sample) is True
    assert can_view_course(other_instructor, course_sample) is True
    assert can_view_course(admin_user, course_sample) is True

    # 2. Draft course visible only to Owner or Admin
    assert can_view_course(None, draft_course) is False
    assert can_view_course(student_user, draft_course) is False
    assert can_view_course(other_instructor, draft_course) is False
    assert can_view_course(instructor_user, draft_course) is True
    assert can_view_course(admin_user, draft_course) is True

    # 3. Soft-deleted course visible only to Admin
    sess: Session = db.session
    course_sample.deleted_at = utc_now()
    sess.commit()

    assert can_view_course(None, course_sample) is False
    assert can_view_course(student_user, course_sample) is False
    assert can_view_course(instructor_user, course_sample) is False
    assert can_view_course(admin_user, course_sample) is True

    # Non-existent course
    assert can_view_course(admin_user, 999999) is False


def test_can_manage_course_rules(
    course_sample: Course,
    student_user: User,
    instructor_user: User,
    other_instructor: User,
    admin_user: User,
) -> None:
    """Test course management ownership policies."""
    # Owner Instructor can manage
    assert can_manage_course(instructor_user, course_sample) is True

    # Non-owner Instructor CANNOT manage (IDOR protection)
    assert can_manage_course(other_instructor, course_sample) is False

    # Student CANNOT manage
    assert can_manage_course(student_user, course_sample) is False

    # Admin CAN manage
    assert can_manage_course(admin_user, course_sample) is True

    # Unauthenticated cannot manage
    assert can_manage_course(None, course_sample) is False

    # Soft-deleted course can only be managed by Admin
    sess: Session = db.session
    course_sample.deleted_at = utc_now()
    sess.commit()
    assert can_manage_course(instructor_user, course_sample) is False
    assert can_manage_course(admin_user, course_sample) is True


# ==============================================================================
# 4. Student Data Access & IDOR Rules
# ==============================================================================


def test_can_access_student_data_rules(
    course_sample: Course,
    student_user: User,
    student_user_2: User,
    instructor_user: User,
    other_instructor: User,
    admin_user: User,
) -> None:
    """Test student data access permissions within a course."""
    sess: Session = db.session

    # Enroll student_user in course_sample
    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=course_sample.id,
        status="ACTIVE",
        current_progress_percent=25.0,
    )
    sess.add(enrollment)
    sess.commit()

    # 1. Student can access OWN data
    assert can_access_student_data(student_user, student_user, course_sample) is True

    # 2. Student CANNOT access other student's data
    assert can_access_student_data(student_user, student_user_2, course_sample) is False

    # 3. Course Owner Instructor CAN access enrolled student's data
    assert can_access_student_data(instructor_user, student_user, course_sample) is True

    # 4. Course Owner Instructor CANNOT access student who is NOT enrolled in this course
    assert can_access_student_data(instructor_user, student_user_2, course_sample) is False

    # 5. Non-owner Instructor CANNOT access student data in another instructor's course
    assert can_access_student_data(other_instructor, student_user, course_sample) is False

    # 6. Admin CAN access student data
    assert can_access_student_data(admin_user, student_user, course_sample) is True

    # 7. Unauthenticated or non-existent
    assert can_access_student_data(None, student_user, course_sample) is False
    assert can_access_student_data(instructor_user, 999999, course_sample) is False


# ==============================================================================
# 5. Lesson, Question, Assessment Management Delegation
# ==============================================================================


def test_lesson_question_assessment_management(
    course_sample: Course,
    instructor_user: User,
    other_instructor: User,
    student_user: User,
    admin_user: User,
) -> None:
    """Test sub-resource management delegation to Course."""
    sess: Session = db.session

    lesson = Lesson(
        course_id=course_sample.id,
        title="Lesson 1",
        markdown_content="# Hello World",
        position=1,
    )
    question = Question(
        course_id=course_sample.id,
        creator_user_id=instructor_user.id,
        difficulty="UNDERSTAND",
    )
    assessment = Assessment(
        course_id=course_sample.id,
        title="Midterm Exam",
        assessment_type="MIDTERM",
    )
    sess.add_all([lesson, question, assessment])
    sess.commit()

    # Owner instructor
    assert can_manage_lesson(instructor_user, lesson) is True
    assert can_manage_question(instructor_user, question) is True
    assert can_manage_assessment(instructor_user, assessment) is True

    # Other instructor denied
    assert can_manage_lesson(other_instructor, lesson) is False
    assert can_manage_question(other_instructor, question) is False
    assert can_manage_assessment(other_instructor, assessment) is False

    # Student denied
    assert can_manage_lesson(student_user, lesson) is False
    assert can_manage_question(student_user, question) is False
    assert can_manage_assessment(student_user, assessment) is False

    # Admin allowed
    assert can_manage_lesson(admin_user, lesson) is True
    assert can_manage_question(admin_user, question) is True
    assert can_manage_assessment(admin_user, assessment) is True


# ==============================================================================
# 6. Assessment Attempt Access & Submission Invariants
# ==============================================================================


def test_attempt_access_and_submission_invariants(
    course_sample: Course,
    student_user: User,
    student_user_2: User,
    instructor_user: User,
    other_instructor: User,
    admin_user: User,
) -> None:
    """Test Attempt Access vs Submission Invariant ("Own only")."""
    sess: Session = db.session

    # Create assessment & attempt
    assessment = Assessment(
        course_id=course_sample.id,
        title="Quiz 1",
        assessment_type="QUIZ",
    )
    sess.add(assessment)
    sess.flush()

    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        enrollment_period_id=1,
        student_user_id=student_user.id,
        attempt_number=1,
        status="IN_PROGRESS",
    )
    sess.add(attempt)
    sess.commit()

    # Viewing the attempt:
    # - Student owner: True
    # - Managing instructor: True
    # - Admin: True
    # - Other student: False
    # - Other instructor: False
    assert can_access_attempt(student_user, attempt) is True
    assert can_access_attempt(instructor_user, attempt) is True
    assert can_access_attempt(admin_user, attempt) is True
    assert can_access_attempt(student_user_2, attempt) is False
    assert can_access_attempt(other_instructor, attempt) is False

    # NON-NEGOTIABLE INVARIANT (02_PERMISSION_MATRIX.md):
    # Attempt answer save/submit is "Own only"!
    # Even Admin and Managing Instructor are strictly FORBIDDEN from submitting for student!
    assert can_submit_attempt(student_user, attempt) is True
    assert can_submit_attempt(student_user_2, attempt) is False
    assert can_submit_attempt(instructor_user, attempt) is False
    assert can_submit_attempt(other_instructor, attempt) is False
    assert can_submit_attempt(admin_user, attempt) is False

    # Grading:
    # Managing instructor: True
    # Admin: True
    # Student / other instructor: False
    assert can_grade_attempt(instructor_user, attempt) is True
    assert can_grade_attempt(admin_user, attempt) is True
    assert can_grade_attempt(student_user, attempt) is False
    assert can_grade_attempt(other_instructor, attempt) is False


# ==============================================================================
# 7. Assertion & Enforcement Helpers (Fail-Closed)
# ==============================================================================


def test_require_helpers_raise_expected_exceptions(
    course_sample: Course,
    student_user: User,
    instructor_user: User,
    other_instructor: User,
) -> None:
    """Test require_* helpers raise ResourceNotFoundError or ForbiddenError."""
    # 1. require_course_manager
    assert require_course_manager(instructor_user, course_sample) == course_sample

    with pytest.raises(ForbiddenError):
        require_course_manager(other_instructor, course_sample)

    with pytest.raises(ForbiddenError):
        require_course_manager(student_user, course_sample)

    with pytest.raises(ResourceNotFoundError):
        require_course_manager(instructor_user, 999999)

    # 2. require_student_data_access
    with pytest.raises(ResourceNotFoundError):
        require_student_data_access(instructor_user, 999999, course_sample)

    with pytest.raises(ResourceNotFoundError):
        require_student_data_access(instructor_user, student_user, 999999)

    with pytest.raises(ForbiddenError):
        # Student not enrolled yet
        require_student_data_access(instructor_user, student_user, course_sample)

    # 3. require_attempt_submission_owner
    sess: Session = db.session
    assessment = Assessment(course_id=course_sample.id, title="Q", assessment_type="QUIZ")
    sess.add(assessment)
    sess.flush()
    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        enrollment_period_id=1,
        student_user_id=student_user.id,
        attempt_number=1,
        status="IN_PROGRESS",
    )
    sess.add(attempt)
    sess.commit()

    assert require_attempt_submission_owner(student_user, attempt) == attempt

    with pytest.raises(ForbiddenError):
        require_attempt_submission_owner(instructor_user, attempt)
