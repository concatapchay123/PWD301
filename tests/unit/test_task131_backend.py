"""Unit tests for TASK-131:
1. student_assessment_summary with period_id=None, chapter assessment unlock logic, and case-insensitive GUID matching.
2. evaluate_course_completion requiring 100% lessons + all required assessments passed (FINAL & chapter QUIZ, excluding PRACTICE/PLACEMENT).
3. GET /student/courses/<course_id> serialized learning_unit_id matching chapter public_id.
4. GET /student/courses/<course_id>/certificate blocked when lessons or required assessments incomplete.
"""

from __future__ import annotations

import decimal
import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.assessment import Assessment
from backend.models.attempt_regrade import AssessmentAttempt, AssessmentResult
from backend.models.course import (
    Course,
    Enrollment,
    LearningUnit,
    Lesson,
    LessonProgress,
)
from backend.models.identity import Role, User
from backend.models.types import utc_now
from backend.services.assessment_student_service import student_assessment_summary
from backend.services.completion_service import evaluate_course_completion
from backend.services.course_service import change_course_status, create_course
from backend.services.enrollment_service import enroll_student
from backend.services.lesson_service import (
    approve_course_change_request,
    create_lesson,
    record_lesson_progress,
    submit_course_changeset,
)
from backend.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def task131_roles(app: Flask) -> dict[str, Role]:
    sess = db.session
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
def task131_data(app: Flask, task131_roles: dict[str, Role]) -> dict[str, Any]:
    sess: Session = db.session
    uid = uuid.uuid4().hex[:6]
    inst = register_user(f"inst_t131_{uid}@example.com", "Password@123", "T131 Instructor")
    inst = assign_role_to_user(inst.id, "INSTRUCTOR")

    adm = register_user(f"admin_t131_{uid}@example.com", "Password@123", "T131 Admin")
    adm = assign_role_to_user(adm.id, "ADMIN")

    stud = register_user(f"stud_t131_{uid}@example.com", "Password@123", "T131 Student")
    stud = assign_role_to_user(stud.id, "STUDENT")

    # Create published course
    course = create_course(
        inst,
        {
            "course_code": f"T131_{uid.upper()}",
            "title": "TASK 131 Test Course",
            "category": "Testing",
            "difficulty": "BEGINNER",
        },
    )
    course = change_course_status(inst, course.id, "SUBMITTED_FOR_REVIEW")
    course = change_course_status(adm, course.id, "APPROVED")
    course = change_course_status(inst, course.id, "PUBLISHED")
    sess.commit()

    # Create Chapter (LearningUnit)
    unit = LearningUnit(
        course_id=course.id,
        title="Chương 1: Khởi động",
        position=1,
    )
    sess.add(unit)
    sess.flush()

    # Create Lesson in Chapter
    lesson_data = {
        "title": "Bài 1.1: Giới thiệu",
        "markdown_content": "# Bài 1.1 Nội dung",
        "position": 1,
        "minimum_completion_seconds": 10,
        "viewed_fraction_required": 0.8,
        "status": "PUBLISHED",
    }
    lesson = create_lesson(inst, course.id, lesson_data)
    lesson.learning_unit_id = unit.id
    request = submit_course_changeset(inst, course.id, {})
    approve_course_change_request(adm, request.id, session=sess)
    sess.commit()

    return {
        "instructor": inst,
        "admin": adm,
        "student": stud,
        "course": course,
        "unit": unit,
        "lesson": lesson,
    }


def test_student_assessment_summary_period_id_none_and_chapter_unlock(
    app: Flask, task131_data: dict[str, Any]
) -> None:
    sess: Session = db.session
    student = task131_data["student"]
    course = task131_data["course"]
    unit = task131_data["unit"]
    lesson = task131_data["lesson"]
    instructor = task131_data["instructor"]

    # Create Chapter Assessment with UPPERCASE UUID in description
    unit_uuid_upper = str(unit.public_id).upper()
    assessment = Assessment(
        course_id=course.id,
        creator_user_id=instructor.id,
        title="Kiểm tra Chương 1",
        description=f"Bài kiểm tra cuối chương.\nunit_id: {unit_uuid_upper}",
        assessment_type="QUIZ",
        status="PUBLISHED",
        passing_percent=decimal.Decimal("60.00"),
    )
    sess.add(assessment)
    sess.commit()

    # Enroll student
    enrollment = enroll_student(student, course.id, session=sess)
    sess.commit()

    # Case 1: Lesson not yet completed -> locked=True, can_start=False
    # Test with period_id explicitly None
    summary_before = student_assessment_summary(
        student, assessment, session=sess, enrollment=enrollment
    )
    assert summary_before["is_locked"] is True
    assert summary_before["can_start"] is False
    assert summary_before["start_block_reason"] == "PREREQUISITE"
    assert "Bạn cần hoàn thành tất cả" in summary_before["lock_reason"]

    # Case 2: Complete lesson in unit
    record_lesson_progress(student, lesson.id, seconds_increment=15, view_fraction=0.9, session=sess)
    sess.commit()

    # Now verify when period_id is None (e.g. simulate enrollment with NULL current_period_id)
    enrollment.current_period_id = None
    sess.commit()

    summary_after = student_assessment_summary(
        student, assessment, session=sess, enrollment=enrollment
    )
    # When all published lessons in target unit are completed:
    assert summary_after["is_locked"] is False
    assert summary_after["can_start"] is True
    assert summary_after["start_block_reason"] is None
    assert summary_after["lock_reason"] is None


def test_evaluate_course_completion_requires_all_required_assessments(
    app: Flask, task131_data: dict[str, Any]
) -> None:
    sess: Session = db.session
    student = task131_data["student"]
    course = task131_data["course"]
    unit = task131_data["unit"]
    lesson = task131_data["lesson"]
    instructor = task131_data["instructor"]

    # Create Chapter Quiz
    chapter_quiz = Assessment(
        course_id=course.id,
        creator_user_id=instructor.id,
        title="Bài kiểm tra Chương 1",
        description=f"unit_id: {unit.public_id}",
        assessment_type="QUIZ",
        status="PUBLISHED",
        passing_percent=decimal.Decimal("60.00"),
    )
    # Create Final Exam
    final_exam = Assessment(
        course_id=course.id,
        creator_user_id=instructor.id,
        title="Thi Cuối Kỳ (Final Exam)",
        assessment_type="FINAL",
        status="PUBLISHED",
        passing_percent=decimal.Decimal("50.00"),
    )
    # Create Practice Exam (should be excluded)
    practice_exam = Assessment(
        course_id=course.id,
        creator_user_id=instructor.id,
        title="Luyện tập tự do",
        assessment_type="PRACTICE",
        status="PUBLISHED",
        passing_percent=decimal.Decimal("50.00"),
    )
    sess.add_all([chapter_quiz, final_exam, practice_exam])
    sess.commit()

    # Enroll student
    enrollment = enroll_student(student, course.id, session=sess)
    period = enrollment.current_period
    sess.commit()

    # 1. Complete lesson 100%
    record_lesson_progress(student, lesson.id, seconds_increment=15, view_fraction=0.9, session=sess)
    sess.commit()

    # Neither quiz nor final is attempted yet
    # evaluate_course_completion MUST return (False, None) and NOT mark COMPLETED
    completed, summary = evaluate_course_completion(enrollment.id, session=sess)
    sess.commit()
    assert completed is False
    assert summary is None
    sess.refresh(enrollment)
    assert enrollment.status == "ACTIVE"

    # 2. Student attempts chapter quiz but FAILS (score 40/100, passing is 60%)
    att1 = AssessmentAttempt(
        assessment_id=chapter_quiz.id,
        enrollment_period_id=period.id,
        student_user_id=student.id,
        attempt_number=1,
        status="GRADED",
    )
    sess.add(att1)
    sess.flush()
    res1 = AssessmentResult(
        attempt_id=att1.id,
        raw_score=decimal.Decimal("40.00"),
        max_score=decimal.Decimal("100.00"),
        percent_score=decimal.Decimal("40.00"),
        passed=False,
        status="FINAL",
    )
    sess.add(res1)
    sess.commit()

    completed, summary = evaluate_course_completion(enrollment.id, session=sess)
    sess.commit()
    assert completed is False
    assert summary is None
    sess.refresh(enrollment)
    assert enrollment.status == "ACTIVE"

    # 3. Student retakes chapter quiz and PASSES (score 80/100)
    att2 = AssessmentAttempt(
        assessment_id=chapter_quiz.id,
        enrollment_period_id=period.id,
        student_user_id=student.id,
        attempt_number=2,
        status="GRADED",
    )
    sess.add(att2)
    sess.flush()
    res2 = AssessmentResult(
        attempt_id=att2.id,
        raw_score=decimal.Decimal("80.00"),
        max_score=decimal.Decimal("100.00"),
        percent_score=decimal.Decimal("80.00"),
        passed=True,
        status="FINAL",
    )
    sess.add(res2)
    sess.commit()

    # Final Exam is still not passed
    completed, summary = evaluate_course_completion(enrollment.id, session=sess)
    sess.commit()
    assert completed is False
    assert summary is None
    sess.refresh(enrollment)
    assert enrollment.status == "ACTIVE"

    # 4. Student takes and PASSES Final Exam (score 70/100, passing is 50%)
    att_final = AssessmentAttempt(
        assessment_id=final_exam.id,
        enrollment_period_id=period.id,
        student_user_id=student.id,
        attempt_number=1,
        status="GRADED",
    )
    sess.add(att_final)
    sess.flush()
    res_final = AssessmentResult(
        attempt_id=att_final.id,
        raw_score=decimal.Decimal("70.00"),
        max_score=decimal.Decimal("100.00"),
        percent_score=decimal.Decimal("70.00"),
        passed=True,
        status="FINAL",
    )
    sess.add(res_final)
    sess.commit()

    # Note: practice_exam is untouched! (PRACTICE is excluded)
    # Now all required assessments are passed!
    completed, summary = evaluate_course_completion(enrollment.id, session=sess)
    sess.commit()
    assert completed is True
    assert summary is not None
    assert summary.ever_completed is True
    sess.refresh(enrollment)
    assert enrollment.status == "COMPLETED"


def test_student_course_detail_and_certificate_endpoint(
    client: FlaskClient, task131_data: dict[str, Any]
) -> None:
    sess: Session = db.session
    student = task131_data["student"]
    course = task131_data["course"]
    unit = task131_data["unit"]
    lesson = task131_data["lesson"]
    instructor = task131_data["instructor"]

    # Create chapter assessment with uppercase UUID in description
    unit_uuid_upper = str(unit.public_id).upper()
    chapter_quiz = Assessment(
        course_id=course.id,
        creator_user_id=instructor.id,
        title="Bài kiểm tra Chương 1",
        description=f"Bài kiểm tra trắc nghiệm.\nunit_id: {unit_uuid_upper}",
        assessment_type="QUIZ",
        status="PUBLISHED",
        passing_percent=decimal.Decimal("50.00"),
    )
    sess.add(chapter_quiz)
    sess.commit()

    login_web_user(client, student)

    # 1. Test GET /student/courses/<course_id>
    resp = client.get(f"/student/courses/{course.public_id}")
    assert resp.status_code == 200
    res_data = resp.get_json()
    serialized_quiz = next(
        (a for a in res_data["assessments"] if a["id"] == str(chapter_quiz.public_id)), None
    )
    assert serialized_quiz is not None
    # learning_unit_id MUST match unit's public_id string
    assert serialized_quiz["learning_unit_id"].lower() == str(unit.public_id).lower()

    # 2. Test GET /student/courses/<course_id>/certificate when incomplete
    # Student enrolled but has not completed lesson or passed quiz
    enrollment = enroll_student(student, course.id, session=sess)
    period = enrollment.current_period
    sess.commit()

    cert_resp1 = client.get(f"/student/courses/{course.public_id}/certificate")
    assert cert_resp1.status_code == 400
    err_data1 = cert_resp1.get_json()
    assert err_data1["success"] is False
    assert err_data1["error"]["code"] == "CERTIFICATE_NOT_AVAILABLE"

    # Complete lesson
    record_lesson_progress(student, lesson.id, seconds_increment=15, view_fraction=0.9, session=sess)
    sess.commit()

    # Still quiz not passed -> blocked
    cert_resp2 = client.get(f"/student/courses/{course.public_id}/certificate")
    assert cert_resp2.status_code == 400
    err_data2 = cert_resp2.get_json()
    assert err_data2["success"] is False

    # Pass the quiz
    att = AssessmentAttempt(
        assessment_id=chapter_quiz.id,
        enrollment_period_id=period.id,
        student_user_id=student.id,
        attempt_number=1,
        status="GRADED",
    )
    sess.add(att)
    sess.flush()
    res = AssessmentResult(
        attempt_id=att.id,
        raw_score=decimal.Decimal("90.00"),
        max_score=decimal.Decimal("100.00"),
        percent_score=decimal.Decimal("90.00"),
        passed=True,
        status="FINAL",
    )
    sess.add(res)
    sess.commit()

    # Mark completion or trigger evaluate_course_completion
    completed, summary = evaluate_course_completion(enrollment.id, session=sess)
    sess.commit()
    assert completed is True

    # Now certificate download MUST succeed (HTTP 200)
    cert_resp3 = client.get(f"/student/courses/{course.public_id}/certificate")
    assert cert_resp3.status_code == 200
    assert cert_resp3.mimetype == "application/pdf"
    assert cert_resp3.data.startswith(b"%PDF-")
