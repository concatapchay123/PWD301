"""Comprehensive Traceability Test Suite for Core Learning & Question Bank Subsystem.

Validates the specification:
- T-COURSE-01 to T-COURSE-08 (Course Invariants, Prerequisites, DAG Cycle, Dependency Lock)
- T-LESSON-01 to T-LESSON-04 (Lesson Structure, Reordering, Completion, Supplementary)
- T-ENROLL-01 to T-ENROLL-04 (Capacity Control, Single Logical Enrollment, Durable Retention)
- T-QB-01 to T-QB-05 (Question Scope, Immutable Revisions, Choice Integrity, Type Lock)
"""

from __future__ import annotations

import datetime
import json

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import (
    Course,
    CourseCompletionSummary,
    Enrollment,
    EnrollmentPeriod,
    LessonProgress,
)
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.completion_service import (
    calculate_course_progress,
)
from pwd301.services.course_service import (
    change_course_status,
    create_course,
    reassign_course_owner,
    trash_course,
)
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    enroll_student,
    leave_course,
    re_enroll_student,
)
from pwd301.services.exceptions import (
    CourseAlreadyExistsError,
    CourseDependencyError,
    CourseStateViolationError,
    CourseValidationError,
    EnrollmentCapacityExceededError,
    EnrollmentPrerequisiteError,
    InvalidRoleAssignmentError,
    PrerequisiteCycleError,
    QuestionStateViolationError,
    QuestionValidationError,
)
from pwd301.services.lesson_service import (
    create_lesson,
    record_lesson_progress,
    reorder_lessons,
    restore_lesson,
    trash_lesson,
    update_lesson,
)
from pwd301.services.question_bank_service import (
    create_question,
    create_question_revision,
    trash_question,
    update_question,
)
from pwd301.services.retention_service import (
    prune_trash_entities,
    purge_expired_enrollment_details,
)
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist in test database."""
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a primary instructor."""
    u = register_user("trace_inst1@example.com", "Password@123", "Trace Instructor 1")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def other_instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a secondary instructor."""
    u = register_user("trace_inst2@example.com", "Password@123", "Trace Instructor 2")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an administrator."""
    u = register_user("trace_admin@example.com", "Password@123", "Trace Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary student."""
    return register_user("trace_student1@example.com", "Password@123", "Trace Student 1")


@pytest.fixture
def second_student(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create secondary student."""
    return register_user("trace_student2@example.com", "Password@123", "Trace Student 2")


def _publish_course(
    instructor: User, admin: User, code: str, title: str, capacity: int | None = None
) -> Course:
    """Helper to author, approve, and publish a course."""
    data = {
        "course_code": code,
        "title": title,
        "description": "Traceability test course",
        "category": "Testing",
        "difficulty": "BEGINNER",
    }
    if capacity is not None:
        data["capacity"] = capacity
    c = create_course(instructor, data)
    change_course_status(instructor, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, c.id, "APPROVED")
    change_course_status(instructor, c.id, "PUBLISHED")
    db.session.commit()
    return c


# ==============================================================================
# 1. BỘ TIÊU CHÍ KIỂM THỬ KHÓA HỌC (T-COURSE-01 ĐẾN T-COURSE-08)
# ==============================================================================


def test_t_course_01_unique_course_code_normalized(app: Flask, instructor_user: User) -> None:
    """T-COURSE-01: course_code uniqueness case/space normalized."""
    create_course(instructor_user, {"course_code": "cs101", "title": "First Course"})
    db.session.commit()

    with pytest.raises(CourseAlreadyExistsError):
        create_course(instructor_user, {"course_code": "  CS101  ", "title": "Second Course"})


def test_t_course_02_unique_title_normalized(app: Flask, instructor_user: User) -> None:
    """T-COURSE-02: title uniqueness case/space normalized."""
    create_course(instructor_user, {"course_code": "PY101", "title": "Lập trình Python Cơ bản"})
    db.session.commit()

    with pytest.raises(CourseAlreadyExistsError):
        create_course(
            instructor_user, {"course_code": "PY102", "title": "  lập trình python cơ bản  "}
        )


def test_t_course_03_owner_instructor_role_enforcement(
    app: Flask, admin_user: User, student_user: User, instructor_user: User
) -> None:
    """T-COURSE-03: owner_instructor_id must have INSTRUCTOR role."""
    course = create_course(instructor_user, {"course_code": "OWN101", "title": "Owner Test Course"})
    db.session.commit()

    # Reassigning to a student without INSTRUCTOR role must be rejected
    with pytest.raises(InvalidRoleAssignmentError):
        reassign_course_owner(admin_user, course.id, student_user.id)


def test_t_course_04_preserve_course_when_instructor_unassigned(
    app: Flask, admin_user: User, instructor_user: User
) -> None:
    """T-COURSE-04: unassigning instructor sets owner_instructor_id = NULL without losing course."""
    course = create_course(
        instructor_user, {"course_code": "UNASSIGN101", "title": "Unassign Course"}
    )
    db.session.commit()

    reassign_course_owner(admin_user, course.id, None, reason="Instructor departure")
    db.session.commit()

    db.session.refresh(course)
    assert course.owner_instructor_id is None
    assert course.status == "DRAFT"


def test_t_course_05_prerequisite_self_reference_blocked(app: Flask, instructor_user: User) -> None:
    """T-COURSE-05: course cannot be prerequisite of itself."""
    course = create_course(
        instructor_user, {"course_code": "SELF101", "title": "Self Prereq Course"}
    )
    db.session.commit()

    with pytest.raises(CourseValidationError, match="cannot be a prerequisite of itself"):
        add_course_prerequisite(instructor_user, course.id, course.id)


def test_t_course_06_prerequisite_cycle_detection_dfs(app: Flask, instructor_user: User) -> None:
    """T-COURSE-06: cyclic dependency A -> B -> C -> A is detected and blocked by DFS."""
    course_a = create_course(instructor_user, {"course_code": "CYC-A", "title": "Course A"})
    course_b = create_course(instructor_user, {"course_code": "CYC-B", "title": "Course B"})
    course_c = create_course(instructor_user, {"course_code": "CYC-C", "title": "Course C"})
    db.session.commit()

    # A requires B
    add_course_prerequisite(instructor_user, course_a.id, course_b.id)
    # B requires C
    add_course_prerequisite(instructor_user, course_b.id, course_c.id)
    db.session.commit()

    # Attempt C requires A -> forms cycle A -> B -> C -> A
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, course_c.id, course_a.id)


def test_t_course_07_prerequisite_not_met_blocks_enrollment(
    app: Flask, instructor_user: User, admin_user: User, student_user: User
) -> None:
    """T-COURSE-07: student missing prerequisite course cannot enroll."""
    course_a = _publish_course(instructor_user, admin_user, "PR-A", "Course Prereq A")
    course_b = _publish_course(instructor_user, admin_user, "PR-B", "Course Target B")

    # B requires A
    add_course_prerequisite(instructor_user, course_b.id, course_a.id)
    db.session.commit()

    # Student attempts to enroll in B without completing A
    with pytest.raises(EnrollmentPrerequisiteError, match="Prerequisite courses not completed"):
        enroll_student(student_user, course_b.id)


def test_t_course_08_prerequisite_dependency_blocks_archive_and_trash(
    app: Flask, instructor_user: User, admin_user: User
) -> None:
    """T-COURSE-08: archiving or trashing course A is blocked while active course B
    depends on it.
    """
    course_a = _publish_course(instructor_user, admin_user, "DEP-A", "Required Foundation")
    course_b = _publish_course(instructor_user, admin_user, "DEP-B", "Advanced Course")

    # B requires A
    add_course_prerequisite(instructor_user, course_b.id, course_a.id)
    db.session.commit()

    # Trashing course A must be blocked
    with pytest.raises(CourseDependencyError, match="Cannot archive or trash course"):
        trash_course(instructor_user, course_a.id)

    # Archiving course A must also be blocked
    with pytest.raises(CourseDependencyError, match="Cannot archive or trash course"):
        change_course_status(instructor_user, course_a.id, "ARCHIVED")


# ==============================================================================
# 2. BỘ TIÊU CHÍ KIỂM THỬ BÀI HỌC & TIẾN ĐỘ (T-LESSON-01 ĐẾN T-LESSON-04)
# ==============================================================================


def test_t_lesson_01_position_reordering_preserves_completion(
    app: Flask, instructor_user: User, admin_user: User, student_user: User
) -> None:
    """T-LESSON-01: reordering lesson positions does not reset lesson_progress completion."""
    course = _publish_course(instructor_user, admin_user, "ORD101", "Order Test Course")
    l1 = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Lesson 1",
            "markdown_content": "Text 1",
            "position": 1,
            "minimum_completion_seconds": 10,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
    )
    l2 = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Lesson 2",
            "markdown_content": "Text 2",
            "position": 2,
            "minimum_completion_seconds": 10,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
    )
    db.session.commit()

    enroll_student(student_user, course.id)
    db.session.commit()

    # Complete Lesson 1
    prog = record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()
    assert prog.completed_at is not None

    # Reorder lessons: swap positions (l2 -> 1, l1 -> 2)
    reorder_lessons(instructor_user, course.id, [l2.id, l1.id])
    db.session.commit()

    # Progress record for l1 still has completed_at preserved
    db.session.refresh(prog)
    assert prog.completed_at is not None
    assert prog.lesson_id == l1.id


def test_t_lesson_02_objective_completion_thresholds(
    app: Flask, instructor_user: User, admin_user: User, student_user: User
) -> None:
    """T-LESSON-02: requires both seconds_spent >= min and max_view_fraction >= req."""
    course = _publish_course(instructor_user, admin_user, "THRESH101", "Threshold Course")
    les = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Threshold Lesson",
            "markdown_content": "Detailed text content",
            "position": 1,
            "minimum_completion_seconds": 30,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
    )
    db.session.commit()

    enroll_student(student_user, course.id)
    db.session.commit()

    # Case 1: 10s < 30s -> incomplete
    p1 = record_lesson_progress(student_user, les.id, seconds_increment=10, view_fraction=0.9)
    db.session.commit()
    assert p1.completed_at is None

    # Case 2: total 35s >= 30s, but view_fraction is 0.50 (< 0.80) -> incomplete
    p1.seconds_spent = 25
    p1.max_view_fraction = 0.50
    db.session.commit()

    p2 = record_lesson_progress(student_user, les.id, seconds_increment=10, view_fraction=0.50)
    db.session.commit()
    assert p2.completed_at is None

    # Case 3: total seconds >= 30 and view_fraction >= 0.80 -> completed
    p3 = record_lesson_progress(student_user, les.id, seconds_increment=5, view_fraction=0.85)
    db.session.commit()
    assert p3.completed_at is not None
    assert p3.completion_rule_snapshot_json is not None
    snapshot = json.loads(p3.completion_rule_snapshot_json)
    assert snapshot["minimum_completion_seconds"] == 30
    assert snapshot["viewed_fraction_required"] == 0.8


def test_t_lesson_03_new_supplementary_lesson_does_not_drop_progress(
    app: Flask, instructor_user: User, admin_user: User, student_user: User
) -> None:
    """T-LESSON-03: supplementary lesson added later does not decrease student
    progress from 100%.
    """
    course = _publish_course(instructor_user, admin_user, "SUPP101", "Supplementary Course")
    l1 = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Lesson 1",
            "markdown_content": "Text",
            "position": 1,
            "minimum_completion_seconds": 10,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
    )
    l2 = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Lesson 2",
            "markdown_content": "Text",
            "position": 2,
            "minimum_completion_seconds": 10,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
    )
    db.session.commit()

    enrollment = enroll_student(student_user, course.id)
    db.session.commit()

    # Student completes both lessons -> 100%
    record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    record_lesson_progress(student_user, l2.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()

    db.session.refresh(enrollment)
    assert float(enrollment.current_progress_percent) == 100.00
    assert enrollment.status == "COMPLETED"

    # Instructor adds Lesson 3 with required_for_periods_starting_at set to future
    future_time = utc_now() + datetime.timedelta(days=1)
    create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Lesson 3 (Added Later)",
            "markdown_content": "Supplementary material",
            "position": 3,
            "minimum_completion_seconds": 10,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
            "required_for_periods_starting_at": future_time,
        },
    )
    db.session.commit()

    # Progress recalculation for the student's cohort still yields 100.00%
    current_progress = calculate_course_progress(enrollment.id)
    assert current_progress == 100.00
    assert float(enrollment.current_progress_percent) == 100.00


def test_t_lesson_04_rewrite_content_preserves_completion(
    app: Flask, instructor_user: User, admin_user: User, student_user: User
) -> None:
    """T-LESSON-04: material rewrite of lesson content never resets student completed_at."""
    course = _publish_course(instructor_user, admin_user, "REWRITE101", "Rewrite Course")
    l1 = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Lesson 1",
            "markdown_content": "Initial draft",
            "position": 1,
            "minimum_completion_seconds": 10,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
    )
    db.session.commit()

    enrollment = enroll_student(student_user, course.id)
    record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()

    prog = (
        db.session.query(LessonProgress)
        .filter(
            LessonProgress.enrollment_period_id == enrollment.current_period_id,
            LessonProgress.lesson_id == l1.id,
        )
        .first()
    )
    assert prog is not None
    original_completed_at = prog.completed_at
    assert original_completed_at is not None

    # Instructor completely updates markdown content
    update_lesson(
        instructor_user,
        l1.id,
        {"markdown_content": "# Completely rewritten curriculum content with new sections"},
    )
    db.session.commit()

    db.session.refresh(prog)
    assert prog.completed_at == original_completed_at


# ==============================================================================
# 3. BỘ TIÊU CHÍ KIỂM THỬ GHI DANH & SĨ SỐ (T-ENROLL-01 ĐẾN T-ENROLL-04)
# ==============================================================================


def test_t_enroll_01_capacity_concurrency_lock_no_overbooking(
    app: Flask, instructor_user: User, admin_user: User, student_user: User, second_student: User
) -> None:
    """T-ENROLL-01: enrollment capacity limit is strictly enforced."""
    course = _publish_course(instructor_user, admin_user, "CAP101", "Capacity Course", capacity=1)

    # First student enrolls -> success
    e1 = enroll_student(student_user, course.id)
    db.session.commit()
    assert e1.status == "ACTIVE"

    # Second student enrolls -> rejected with EnrollmentCapacityExceededError
    with pytest.raises(EnrollmentCapacityExceededError, match="Course capacity"):
        enroll_student(second_student, course.id)


def test_t_enroll_02_single_logical_enrollment_idempotent(
    app: Flask, instructor_user: User, admin_user: User, student_user: User
) -> None:
    """T-ENROLL-02: enrolling when already active is idempotent; no new row created."""
    course = _publish_course(instructor_user, admin_user, "IDEM-EN101", "Idempotent Enroll Course")

    e1 = enroll_student(student_user, course.id)
    db.session.commit()
    first_id = e1.id

    e2 = enroll_student(student_user, course.id)
    db.session.commit()

    assert e1.id == e2.id == first_id

    total_rows = (
        db.session.query(Enrollment)
        .filter(Enrollment.student_user_id == student_user.id, Enrollment.course_id == course.id)
        .count()
    )
    assert total_rows == 1


def test_t_enroll_03_re_enrollment_opens_new_period_resets_progress(
    app: Flask, instructor_user: User, admin_user: User, student_user: User
) -> None:
    """T-ENROLL-03: student leaves and re-enrolls -> period_no = 2, progress resets to 0.00%."""
    course = _publish_course(instructor_user, admin_user, "REENROLL101", "Re-enroll Course")
    l1 = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Lesson 1",
            "markdown_content": "Text",
            "position": 1,
            "minimum_completion_seconds": 10,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
    )
    create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Lesson 2",
            "markdown_content": "Text",
            "position": 2,
            "minimum_completion_seconds": 10,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
    )
    db.session.commit()

    enrollment = enroll_student(student_user, course.id)
    record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()

    db.session.refresh(enrollment)
    assert float(enrollment.current_progress_percent) == 50.00
    assert enrollment.status == "ACTIVE"

    # Student withdraws / leaves
    leave_course(student_user, course.id)
    db.session.commit()
    db.session.refresh(enrollment)
    assert enrollment.status == "LEFT"

    # Student re-enrolls
    reenrolled = re_enroll_student(student_user, course.id)
    db.session.commit()

    assert reenrolled.id == enrollment.id
    assert reenrolled.status == "ACTIVE"
    assert float(reenrolled.current_progress_percent) == 0.00

    # Check period_no = 2
    period = db.session.get(EnrollmentPeriod, reenrolled.current_period_id)
    assert period is not None
    assert period.period_no == 2
    assert period.status == "ACTIVE"


def test_t_enroll_04_retention_purging_preserves_durable_completion_summary(
    app: Flask, instructor_user: User, admin_user: User, student_user: User
) -> None:
    """T-ENROLL-04: purging expired enrollment details preserves
    CourseCompletionSummary indefinitely.
    """
    course_a = _publish_course(instructor_user, admin_user, "DUR-A", "Durable Foundation A")
    course_b = _publish_course(instructor_user, admin_user, "DUR-B", "Target Course B")
    add_course_prerequisite(instructor_user, course_b.id, course_a.id)

    l1 = create_lesson(
        instructor_user,
        course_a.id,
        {
            "title": "L1",
            "markdown_content": "Text",
            "position": 1,
            "minimum_completion_seconds": 10,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
    )
    db.session.commit()

    # Complete Course A
    enrollment = enroll_student(student_user, course_a.id)
    record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()

    summary = (
        db.session.query(CourseCompletionSummary)
        .filter(
            CourseCompletionSummary.student_user_id == student_user.id,
            CourseCompletionSummary.course_id == course_a.id,
        )
        .first()
    )
    assert summary is not None
    assert summary.ever_completed is True
    assert summary.prerequisite_eligible is True

    # Student re-enrolls then leaves course A
    enroll_student(student_user, course_a.id)
    leave_course(student_user, course_a.id)
    db.session.commit()

    # Fast-forward 31 days and run retention cleanup
    cutoff = utc_now() + datetime.timedelta(days=31)
    purged_count = purge_expired_enrollment_details(cutoff_date=cutoff)
    db.session.commit()
    assert purged_count >= 1

    # LessonProgress is purged
    progress_count = (
        db.session.query(LessonProgress)
        .filter(LessonProgress.enrollment_period_id == enrollment.current_period_id)
        .count()
    )
    assert progress_count == 0

    # But CourseCompletionSummary is preserved!
    db.session.refresh(summary)
    assert summary.ever_completed is True
    assert summary.prerequisite_eligible is True

    # Student can still enroll in Course B!
    enrolled_b = enroll_student(student_user, course_b.id)
    db.session.commit()
    assert enrolled_b.status == "ACTIVE"


# ==============================================================================
# 4. BỘ TIÊU CHÍ KIỂM THỬ NGÂN HÀNG CÂU HỎI (T-QB-01 ĐẾN T-QB-05)
# ==============================================================================


def test_t_qb_01_course_lesson_scope_validation(
    app: Flask, instructor_user: User, other_instructor: User
) -> None:
    """T-QB-01: cannot associate a question with a lesson from a different course."""
    course_a = create_course(instructor_user, {"course_code": "QA101", "title": "Course A"})
    course_b = create_course(other_instructor, {"course_code": "QB101", "title": "Course B"})
    lesson_b = create_lesson(
        other_instructor,
        course_b.id,
        {"title": "Lesson in B", "markdown_content": "Text", "position": 1},
    )
    db.session.commit()

    # Create question in course_a pointing to lesson_b (from course_b)
    payload = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Scope test question",
        "lesson_id": lesson_b.id,
        "choices": [
            {"content": "Yes", "is_correct": True},
            {"content": "No", "is_correct": False},
        ],
    }
    with pytest.raises(
        QuestionValidationError, match="Lesson does not belong to the specified course"
    ):
        create_question(instructor_user, course_a.id, payload)


def test_t_qb_02_immutable_revision_branching_after_student_exposed(
    app: Flask, instructor_user: User
) -> None:
    """T-QB-02: editing a question after student exposure branches into Revision 2
    and preserves Revision 1.
    """
    course = create_course(instructor_user, {"course_code": "EXPOSE101", "title": "Exposed Course"})
    q = create_question(
        instructor_user,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Original stem text",
            "choices": [
                {"content": "Paris", "is_correct": True},
                {"content": "London", "is_correct": False},
            ],
        },
    )
    db.session.commit()

    rev1 = q.current_revision
    rev1_id = rev1.id
    rev1.was_student_exposed = True
    db.session.commit()

    # Update question content
    updated = update_question(
        instructor_user,
        q.id,
        {
            "content": "Revised stem text after student exposed",
            "change_type": "CONTENT_CHANGE",
            "change_reason": "Clarity improvement",
        },
    )
    db.session.commit()

    # Current revision is now Revision 2
    assert updated.current_revision.revision_no == 2
    assert updated.current_revision.id != rev1_id
    assert updated.current_revision.content == "Revised stem text after student exposed"

    # Revision 1 remains intact with original content
    db.session.refresh(rev1)
    assert rev1.revision_no == 1
    assert rev1.content == "Original stem text"
    assert rev1.is_current is False


def test_t_qb_03_choice_integrity_validation_single_and_multi(
    app: Flask, instructor_user: User
) -> None:
    """T-QB-03: SINGLE_CHOICE must have exactly 1 correct; MULTIPLE_CHOICE at least 1."""
    course = create_course(
        instructor_user, {"course_code": "CHOICE101", "title": "Choice Integrity Course"}
    )
    db.session.commit()

    # SINGLE_CHOICE with 2 correct answers -> rejected
    with pytest.raises(QuestionValidationError, match="must have exactly 1 correct answer"):
        create_question(
            instructor_user,
            course.id,
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "Invalid SC question",
                "choices": [
                    {"content": "A", "is_correct": True},
                    {"content": "B", "is_correct": True},
                ],
            },
        )

    # SINGLE_CHOICE with 0 correct answers -> rejected
    with pytest.raises(QuestionValidationError, match="must have exactly 1 correct answer"):
        create_question(
            instructor_user,
            course.id,
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "Zero correct SC question",
                "choices": [
                    {"content": "A", "is_correct": False},
                    {"content": "B", "is_correct": False},
                ],
            },
        )

    # MULTIPLE_CHOICE with 0 correct answers -> rejected
    with pytest.raises(QuestionValidationError, match="must have at least 1 correct answer"):
        create_question(
            instructor_user,
            course.id,
            {
                "question_type": "MULTIPLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "Zero correct MC question",
                "choices": [
                    {"content": "A", "is_correct": False},
                    {"content": "B", "is_correct": False},
                ],
            },
        )


def test_t_qb_04_type_lock_after_first_answered(app: Flask, instructor_user: User) -> None:
    """T-QB-04: question_type cannot be changed once first_answered_at is set."""
    course = create_course(
        instructor_user, {"course_code": "TYPELOCK101", "title": "Type Lock Course"}
    )
    q = create_question(
        instructor_user,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Type locked question",
            "choices": [
                {"content": "Option A", "is_correct": True},
                {"content": "Option B", "is_correct": False},
            ],
        },
    )
    db.session.commit()

    # Simulate student answered this question
    q.first_answered_at = utc_now()
    db.session.commit()

    # Attempting to change question_type to ESSAY must be rejected with QuestionStateViolationError
    with pytest.raises(QuestionStateViolationError, match="Cannot change question_type"):
        update_question(
            instructor_user,
            q.id,
            {"question_type": "ESSAY", "change_reason": "Trying to convert to essay"},
        )

    with pytest.raises(QuestionStateViolationError, match="Cannot change question_type"):
        create_question_revision(
            instructor_user,
            q.id,
            {"question_type": "ESSAY", "change_reason": "Trying to convert revision to essay"},
        )


def test_t_qb_05_permanent_retention_used_for_grading_retires_question(
    app: Flask, instructor_user: User
) -> None:
    """T-QB-05: trashing a question that has was_used_for_grading=True retires it permanently."""
    course = create_course(instructor_user, {"course_code": "RETIRE101", "title": "Retire Course"})
    q = create_question(
        instructor_user,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Question used for grading",
            "choices": [
                {"content": "Choice 1", "is_correct": True},
                {"content": "Choice 2", "is_correct": False},
            ],
        },
    )
    db.session.commit()

    # Mark revision as used for grading
    q.current_revision.was_used_for_grading = True
    db.session.commit()

    # Trash / delete question
    retired = trash_question(instructor_user, q.id, reason="Retiring obsolete graded question")
    db.session.commit()

    # It must transition to RETIRED, not TRASH
    assert retired.status == "RETIRED"
    assert retired.deleted_at is not None
    # No 30-day restore deadline -> permanently preserved
    assert retired.restore_until is None


# ==============================================================================
# 5. BỔ SUNG KIỂM THỬ HARDENING CÁC KHIẾM KHUYẾT PHÁT HIỆN QUA AUDIT
# ==============================================================================


def test_course_trash_sets_restore_until_and_cannot_restore_to_draft_if_published(
    app: Flask, instructor_user: User, admin_user: User
) -> None:
    """Course TRASH sets 30-day restore_until; published course in TRASH cannot restore to DRAFT."""
    published = _publish_course(instructor_user, admin_user, "RST101", "Restore Test Course")
    assert published.status == "PUBLISHED"
    assert published.published_at is not None

    # Move to TRASH
    trashed = change_course_status(instructor_user, published.id, "TRASH")
    db.session.commit()
    assert trashed.status == "TRASH"
    assert trashed.deleted_at is not None
    assert trashed.restore_until is not None
    res_until = (
        trashed.restore_until.replace(tzinfo=datetime.UTC)
        if trashed.restore_until.tzinfo is None
        else trashed.restore_until
    )
    assert res_until > utc_now()

    # Spec Section 2.1: Published courses in TRASH can only restore to
    # PUBLISHED or ARCHIVED, never DRAFT
    with pytest.raises(
        CourseStateViolationError,
        match="Cannot restore a previously published course to DRAFT status",
    ):
        change_course_status(admin_user, published.id, "DRAFT")

    # Restoring to PUBLISHED succeeds and clears deletion metadata
    restored = change_course_status(admin_user, published.id, "PUBLISHED")
    db.session.commit()
    assert restored.status == "PUBLISHED"
    assert restored.deleted_at is None
    assert restored.deleted_by_user_id is None
    assert restored.restore_until is None


def test_retention_pruning_preserves_courses_with_first_student_enrolled(
    app: Flask, instructor_user: User, admin_user: User, student_user: User
) -> None:
    """Retention job must archive and never hard-delete courses where
    first_student_enrolled_at is set.
    """
    course = _publish_course(instructor_user, admin_user, "RETEN101", "Retention Course")
    enroll_student(student_user, course.id)
    db.session.commit()

    # Verify first_student_enrolled_at is populated
    assert course.first_student_enrolled_at is not None

    # Student leaves course
    leave_course(student_user, course.id)
    db.session.commit()

    # Put course in TRASH past its restore deadline
    course.status = "TRASH"
    past_deadline = utc_now() - datetime.timedelta(days=1)
    course.restore_until = (
        past_deadline.replace(tzinfo=None)
        if course.restore_until is not None and course.restore_until.tzinfo is None
        else past_deadline
    )
    db.session.commit()

    # Run retention pruning
    prune_trash_entities(cutoff_date=utc_now())
    db.session.commit()

    # Course must be ARCHIVED, NOT hard-deleted
    db.session.refresh(course)
    assert course.status == "ARCHIVED"
    assert course.restore_until is None


def test_lesson_trash_and_restore_cycle(app: Flask, instructor_user: User) -> None:
    """Lesson TRASH bumps position and sets restore_until; restore_lesson resets
    position and clears flags.
    """
    course = create_course(
        instructor_user, {"course_code": "LES101", "title": "Lesson Cycle Course"}
    )
    l1 = create_lesson(
        instructor_user,
        course.id,
        {"title": "Lesson 1", "markdown_content": "Content", "position": 1, "status": "PUBLISHED"},
    )
    db.session.commit()

    # Trash lesson
    trashed = trash_lesson(instructor_user, l1.id, reason="Temporary decommission")
    db.session.commit()
    assert trashed.status == "TRASH"
    assert trashed.deleted_at is not None
    assert trashed.restore_until is not None
    res_until = (
        trashed.restore_until.replace(tzinfo=datetime.UTC)
        if trashed.restore_until.tzinfo is None
        else trashed.restore_until
    )
    assert res_until > utc_now()
    assert trashed.position >= 10000000

    # Restore lesson
    restored = restore_lesson(instructor_user, l1.id)
    db.session.commit()
    assert restored.status in ("DRAFT", "PUBLISHED")
    assert restored.deleted_at is None
    assert restored.deleted_by_user_id is None
    assert restored.restore_until is None
    assert restored.position < 10000000


def test_lesson_progress_deduplication_via_client_event_id(
    app: Flask, instructor_user: User, admin_user: User, student_user: User
) -> None:
    """Duplicate progress events with same client_event_id are deduplicated
    and do not double-count.
    """
    course = _publish_course(instructor_user, admin_user, "DEDUP101", "Dedup Course")
    lesson = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Dedup Lesson",
            "markdown_content": "Video lesson",
            "position": 1,
            "minimum_completion_seconds": 60,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
    )
    enroll_student(student_user, course.id)
    db.session.commit()

    event_id = "ping-event-unique-001"

    # First event: 15 seconds
    p1 = record_lesson_progress(
        student_user,
        lesson.id,
        seconds_increment=15,
        view_fraction=0.25,
        client_event_id=event_id,
    )
    db.session.commit()
    assert p1.seconds_spent == 15
    assert float(p1.max_view_fraction or 0) == 0.25

    # Duplicate replay of identical client_event_id
    p2 = record_lesson_progress(
        student_user,
        lesson.id,
        seconds_increment=15,
        view_fraction=0.25,
        client_event_id=event_id,
    )
    db.session.commit()
    # Time must NOT be incremented to 30!
    assert p2.seconds_spent == 15

    # New distinct event: 10 seconds
    p3 = record_lesson_progress(
        student_user,
        lesson.id,
        seconds_increment=10,
        view_fraction=0.4,
        client_event_id="ping-event-unique-002",
    )
    db.session.commit()
    assert p3.seconds_spent == 25


def test_inplace_question_update_validation_and_scope(
    app: Flask, instructor_user: User, other_instructor: User
) -> None:
    """In-place question update enforces choice integrity, scope validation,
    and updates accepted answers.
    """
    course_a = create_course(
        instructor_user, {"course_code": "VAL101", "title": "Validation Course A"}
    )
    course_b = create_course(
        other_instructor, {"course_code": "VAL102", "title": "Validation Course B"}
    )
    lesson_b = create_lesson(
        other_instructor,
        course_b.id,
        {"title": "Lesson B", "markdown_content": "Text", "position": 1},
    )

    q = create_question(
        instructor_user,
        course_a.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Original in-place question",
            "choices": [
                {"content": "C1", "is_correct": True},
                {"content": "C2", "is_correct": False},
            ],
        },
    )
    db.session.commit()

    # Attempt in-place update with invalid choices (2 correct for SINGLE_CHOICE)
    with pytest.raises(QuestionValidationError, match="must have exactly 1 correct answer"):
        update_question(
            instructor_user,
            q.id,
            {
                "choices": [
                    {"content": "C1", "is_correct": True},
                    {"content": "C2", "is_correct": True},
                ]
            },
        )

    # Attempt in-place update pointing to lesson from another course
    with pytest.raises(
        QuestionValidationError, match="Lesson does not belong to the specified course"
    ):
        update_question(
            instructor_user,
            q.id,
            {"lesson_id": lesson_b.id},
        )

    # SHORT_ANSWER question accepted_answers update
    sa_q = create_question(
        instructor_user,
        course_a.id,
        {
            "question_type": "SHORT_ANSWER",
            "difficulty": "APPLY",
            "content": "What is 2+2?",
            "accepted_answers": ["4", "four"],
        },
    )
    db.session.commit()

    updated_sa = update_question(
        instructor_user,
        sa_q.id,
        {"accepted_answers": ["4", "four", "IV"]},
    )
    db.session.commit()
    assert {a.answer_text for a in updated_sa.current_revision.accepted_answers} == {
        "4",
        "four",
        "IV",
    }
