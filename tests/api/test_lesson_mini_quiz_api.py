"""Integration tests for Lesson Mini-Quiz API with diverse question types.

Verifies:
1. Lesson creation with diverse question types:
   - Multiple Choice (Single choice & Multi-select)
   - Fill in the Blank (Cloze with [___] and accepted answers)
   - Matching (Pairs)
   - True / False
2. Serialization and retrieval of mini_quiz in instructor routes.
3. Serialization and retrieval of mini_quiz in student routes.
4. Backward compatibility with legacy format (question, options/choices, correct_index).
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Enrollment, EnrollmentPeriod, Lesson
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def quiz_roles(app: Flask) -> dict[str, Role]:
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
def quiz_instructor(app: Flask, quiz_roles: dict[str, Role]) -> User:
    suffix = uuid.uuid4().hex[:6]
    u = register_user(f"quiz_inst_{suffix}@fpt.edu.vn", "Password@123", f"Quiz Instructor {suffix}")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def quiz_student(app: Flask, quiz_roles: dict[str, Role]) -> User:
    suffix = uuid.uuid4().hex[:6]
    u = register_user(f"quiz_stu_{suffix}@fpt.edu.vn", "Password@123", f"Quiz Student {suffix}")
    return assign_role_to_user(u.id, "STUDENT")


def test_create_and_fetch_lesson_with_all_question_types(
    client: FlaskClient,
    quiz_instructor: User,
    quiz_student: User,
) -> None:
    """Test creating a lesson with multiple choice, fill in the blank, matching, and true/false questions."""
    sess: Session = db.session

    # 1. Create a draft course owned by instructor
    course = create_course(
        quiz_instructor,
        {"course_code": f"QUIZ-{uuid.uuid4().hex[:4].upper()}", "title": "Mini Quiz Test Course"},
    )

    # 2. Authenticate instructor via login_web_user
    login_web_user(client, quiz_instructor)

    diverse_quiz: list[dict[str, Any]] = [
        {
            "type": "MULTIPLE_CHOICE",
            "question": "Thuật toán sắp xếp nào có độ phức tạp O(n log n)?",
            "allow_multiple": True,
            "options": ["Quicksort", "Bubble Sort", "Merge Sort", "Insertion Sort", "Heap Sort"],
            "choices": ["Quicksort", "Bubble Sort", "Merge Sort", "Insertion Sort", "Heap Sort"],
            "correct_answers": [0, 2, 4],
            "correct_index": 0,
            "explanation": "Quicksort, Merge Sort và Heap Sort đều có độ phức tạp trung bình O(n log n).",
        },
        {
            "type": "FILL_BLANK",
            "question": "Thủ đô của Việt Nam là [___]. Tiền tệ là [___].",
            "blanks": [
                {"accepted_answers": ["Hà Nội", "Ha Noi", "Hanoi"]},
                {"accepted_answers": ["VND", "Đồng", "Dong", "Việt Nam Đồng"]},
            ],
            "explanation": "Hà Nội là thủ đô, VND là tiền tệ chính thức.",
        },
        {
            "type": "MATCHING",
            "question": "Hãy nối các giao thức mạng với tầng tương ứng:",
            "pairs": [
                {"left": "HTTP", "right": "Tầng ứng dụng (Application)"},
                {"left": "TCP", "right": "Tầng truyền vận (Transport)"},
                {"left": "IP", "right": "Tầng mạng (Network)"},
            ],
            "explanation": "Mô hình TCP/IP phân chia HTTP ở Application, TCP ở Transport, IP ở Network.",
        },
        {
            "type": "TRUE_FALSE",
            "question": "Python là ngôn ngữ thông dịch (Interpreted Language).",
            "correct_value": True,
            "explanation": "Mã nguồn Python được thông dịch từng câu lệnh bởi Python bytecode interpreter.",
        },
    ]

    # 3. Create lesson via instructor route
    res_create = client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={
            "title": "Bài giảng Cấu trúc dữ liệu & Thuật toán",
            "summary": "Tổng quan các thuật toán và câu hỏi củng cố.",
            "markdown_content": "# Bài 1\nNội dung chính của bài giảng.",
            "quiz": diverse_quiz,
        },
    )
    assert res_create.status_code in (200, 201), f"Create failed: {res_create.get_data(as_text=True)}"
    les_data = res_create.get_json()
    assert "lesson_id" in les_data or "id" in les_data
    lesson_id = les_data.get("lesson_id") or les_data.get("id")

    # 4. Fetch lesson via instructor route and verify all question types are intact
    res_get_inst = client.get(f"/instructor/lessons/{lesson_id}")
    assert res_get_inst.status_code == 200
    inst_json = res_get_inst.get_json()
    quiz_fetched = inst_json.get("quiz", [])
    assert len(quiz_fetched) == 4

    # Validate Multiple Choice
    assert quiz_fetched[0]["type"] == "MULTIPLE_CHOICE"
    assert quiz_fetched[0]["allow_multiple"] is True
    assert len(quiz_fetched[0]["options"]) == 5
    assert quiz_fetched[0]["correct_answers"] == [0, 2, 4]

    # Validate Fill in Blank
    assert quiz_fetched[1]["type"] == "FILL_BLANK"
    assert len(quiz_fetched[1]["blanks"]) == 2
    assert "Hà Nội" in quiz_fetched[1]["blanks"][0]["accepted_answers"]

    # Validate Matching
    assert quiz_fetched[2]["type"] == "MATCHING"
    assert len(quiz_fetched[2]["pairs"]) == 3
    assert quiz_fetched[2]["pairs"][0]["left"] == "HTTP"

    # Validate True/False
    assert quiz_fetched[3]["type"] == "TRUE_FALSE"
    assert quiz_fetched[3]["correct_value"] is True

    # 5. Enroll student, publish course & lesson, and verify student route gets the quiz
    # DB enroll student
    enrollment = Enrollment(
        student_user_id=quiz_student.id,
        course_id=course.id,
        status="ACTIVE",
    )
    sess.add(enrollment)
    sess.flush()
    period = EnrollmentPeriod(
        enrollment_id=enrollment.id,
        period_no=1,
        status="ACTIVE",
    )
    sess.add(period)
    sess.flush()
    enrollment.current_period_id = period.id

    # Publish course and lesson for student visibility
    course.status = "PUBLISHED"
    les_obj = sess.query(Lesson).filter_by(public_id=uuid.UUID(lesson_id)).first()
    if les_obj:
        les_obj.status = "PUBLISHED"
    sess.commit()

    # Log in as student
    login_web_user(client, quiz_student)

    res_get_stu = client.get(f"/student/courses/{course.public_id}/lessons/{lesson_id}")
    assert res_get_stu.status_code == 200
    stu_json = res_get_stu.get_json()
    stu_quiz = stu_json.get("quiz", [])
    assert len(stu_quiz) == 4
    assert stu_quiz[0]["type"] == "MULTIPLE_CHOICE"
    assert stu_quiz[1]["type"] == "FILL_BLANK"
    assert stu_quiz[2]["type"] == "MATCHING"
    assert stu_quiz[3]["type"] == "TRUE_FALSE"


def test_legacy_format_compatibility(client: FlaskClient, quiz_instructor: User) -> None:
    """Test that legacy 4-choice questions without 'type' field are parsed and handled seamlessly."""
    course = create_course(
        quiz_instructor,
        {"course_code": f"LEG-{uuid.uuid4().hex[:4].upper()}", "title": "Legacy Quiz Course"},
    )

    login_web_user(client, quiz_instructor)

    legacy_quiz = [
        {
            "question": "Câu hỏi cũ dạng trắc nghiệm 4 lựa chọn?",
            "options": ["A", "B", "C", "D"],
            "correct_index": 1,
            "explanation": "Đáp án B là chính xác.",
        }
    ]

    res_create = client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={
            "title": "Legacy Lesson",
            "markdown_content": "# Legacy Content",
            "quiz": legacy_quiz,
        },
    )
    assert res_create.status_code in (200, 201)
    lesson_id = res_create.get_json().get("lesson_id") or res_create.get_json().get("id")

    res_get = client.get(f"/instructor/lessons/{lesson_id}")
    assert res_get.status_code == 200
    fetched_quiz = res_get.get_json().get("quiz", [])
    assert len(fetched_quiz) == 1
    assert fetched_quiz[0]["question"] == "Câu hỏi cũ dạng trắc nghiệm 4 lựa chọn?"
    assert fetched_quiz[0]["correct_index"] == 1


def test_update_lesson_mini_quiz_questions(client: FlaskClient, quiz_instructor: User) -> None:
    """Test updating an existing lesson's mini-quiz questions via PUT /instructor/lessons/<id>."""
    course = create_course(
        quiz_instructor,
        {"course_code": f"UPD-{uuid.uuid4().hex[:4].upper()}", "title": "Update Quiz Course"},
    )
    login_web_user(client, quiz_instructor)

    # Initial lesson without quiz
    res_create = client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={"title": "Draft Lesson", "markdown_content": "# Lesson"},
    )
    assert res_create.status_code in (200, 201)
    lesson_id = res_create.get_json().get("lesson_id") or res_create.get_json().get("id")

    # Update lesson to add new diverse questions
    updated_quiz = [
        {
            "type": "FILL_BLANK",
            "question": "Hà Nội là thủ đô của [___].",
            "blanks": [{"accepted_answers": ["Việt Nam", "Vietnam"]}],
            "explanation": "Hà Nội là thủ đô của Việt Nam.",
        },
        {
            "type": "TRUE_FALSE",
            "question": "Mặt trời mọc ở hướng Đông.",
            "correct_value": True,
            "explanation": "Đúng theo quy luật tự nhiên.",
        },
    ]

    res_put = client.put(
        f"/instructor/lessons/{lesson_id}",
        json={
            "title": "Draft Lesson (Updated)",
            "markdown_content": "# Lesson Content Updated",
            "quiz": updated_quiz,
        },
    )
    assert res_put.status_code == 200

    # Verify updated quiz
    res_get = client.get(f"/instructor/lessons/{lesson_id}")
    assert res_get.status_code == 200
    q_data = res_get.get_json().get("quiz", [])
    assert len(q_data) == 2
    assert q_data[0]["type"] == "FILL_BLANK"
    assert q_data[1]["type"] == "TRUE_FALSE"

