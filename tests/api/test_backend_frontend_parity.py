"""Integration tests for Backend-Frontend Parity and Full Stack Convergence.

Verifies:
1. Course Prerequisites API Parity (DAG cycle detection, add, list, delete, ADR-002)
2. Course Completion Rules API Parity (get defaults, update, persistence, ADR-002)
3. Question Bank Lifecycle & Revisions Parity (create, patch, revisions, trash, restore)
4. Frontend Static Assets & ApiClient Contract Parity (100% method alignment, 0 missing)
"""

from __future__ import annotations

import os
import re
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import create_course
from pwd301.services.lesson_service import create_lesson
from pwd301.services.user_service import assign_role_to_user, register_user

UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def assert_adr002(data: Any) -> None:
    """Recursively verify no internal BigInt PKs/FKs are leaked in API responses (ADR-002)."""
    if isinstance(data, dict):
        for k, v in data.items():
            assert k != "id", f"Internal primary key 'id' leaked: {data}"
            assert k != "creator_user_id", f"Internal foreign key 'creator_user_id' leaked: {data}"
            assert k != "question_revision_id", (
                f"Internal foreign key 'question_revision_id' leaked: {data}"
            )
            if (
                k.endswith("_id")
                and v is not None
                and k not in ("choice_key", "temp_id", "question_type")
            ):
                assert isinstance(v, str), f"Expected UUID string for {k}, got {type(v)}: {v}"
                assert UUID_REGEX.match(v), f"Field '{k}' is not a valid UUID: {v}"
            assert_adr002(v)
    elif isinstance(data, list):
        for item in data:
            assert_adr002(item)


@pytest.fixture
def parity_env(app: Flask) -> dict[str, Any]:
    """Setup test fixture with instructor, student, courses, and lessons."""
    sess: Session = db.session
    seed_baseline(sess)

    # 1. Register instructor and student
    instructor = register_user(
        email="instructor_parity@pwd301.local",
        password="Password@123",
        display_name="TS. Parity Instructor",
        session=sess,
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR", session=sess)

    student = register_user(
        email="student_parity@pwd301.local",
        password="Password@123",
        display_name="Le Van Parity",
        session=sess,
    )
    assign_role_to_user(student.id, "STUDENT", session=sess)

    # 2. Create courses
    course_a = create_course(
        actor=instructor,
        data={
            "course_code": "CS-PARITY-101",
            "title": "Lap trinh Mang Can ban",
            "category": "Computer Science",
            "capacity": 60,
        },
        session=sess,
    )
    course_a.status = "PUBLISHED"

    course_b = create_course(
        actor=instructor,
        data={
            "course_code": "CS-PARITY-102",
            "title": "He dieu hanh va Kien truc may tinh",
            "category": "Computer Science",
            "capacity": 60,
        },
        session=sess,
    )
    course_b.status = "PUBLISHED"

    sess.flush()

    lesson = create_lesson(
        actor=instructor,
        course_id=course_a.id,
        data={
            "title": "Bai 01: Gioi thieu mo hinh OSI",
            "markdown_content": "# Mo hinh OSI 7 tang\nNoi dung chi tiet...",
            "estimated_duration_minutes": 50,
            "status": "PUBLISHED",
        },
        session=sess,
    )

    sess.commit()

    return {
        "instructor": instructor,
        "student": student,
        "course_a": course_a,
        "course_b": course_b,
        "lesson": lesson,
    }


def login_instructor(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    """Helper to authenticate instructor session and obtain CSRF token."""
    csrf_res = client.get("/auth/login")
    csrf_token = csrf_res.get_json().get("csrf_token", "")
    login_res = client.post(
        "/auth/login",
        json={"email": email, "password": password, "remember": False},
        headers={"X-CSRFToken": csrf_token},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.get_data(as_text=True)}"
    return csrf_token


# ============================================================================
# 1. Course Prerequisites API Parity
# ============================================================================
def test_course_prerequisites_api_parity(client: FlaskClient, parity_env: dict[str, Any]) -> None:
    """Test full lifecycle of course prerequisites: Add, List, Cycle Check, and Delete."""
    inst = parity_env["instructor"]
    c_a = parity_env["course_a"]
    c_b = parity_env["course_b"]

    csrf_token = login_instructor(client, inst.email)

    # 1. Add course_b as prerequisite for course_a
    add_resp = client.post(
        f"/instructor/courses/{c_a.public_id}/prerequisites",
        json={"prerequisite_course_id": str(c_b.public_id)},
        headers={"X-CSRFToken": csrf_token},
    )
    assert add_resp.status_code == 201, f"Add prereq failed: {add_resp.get_data(as_text=True)}"
    add_data = add_resp.get_json()
    assert add_data["course_id"] == str(c_a.public_id)
    assert add_data["prerequisite_course_id"] == str(c_b.public_id)
    assert_adr002(add_data)

    # 2. List prerequisites for course_a
    list_resp = client.get(f"/instructor/courses/{c_a.public_id}/prerequisites")
    assert list_resp.status_code == 200
    list_data = list_resp.get_json()
    assert "prerequisites" in list_data
    assert len(list_data["prerequisites"]) == 1
    prereq_item = list_data["prerequisites"][0]
    assert prereq_item["course_id"] == str(c_b.public_id)
    assert prereq_item["course_code"] == c_b.course_code
    assert_adr002(list_data)

    # 3. Verify DAG cycle detection (Cannot add course_a as prerequisite to course_b)
    cycle_resp = client.post(
        f"/instructor/courses/{c_b.public_id}/prerequisites",
        json={"prerequisite_course_id": str(c_a.public_id)},
        headers={"X-CSRFToken": csrf_token},
    )
    assert cycle_resp.status_code in (400, 409, 422)
    cycle_data = cycle_resp.get_json()
    has_cycle_msg = "cycle" in str(cycle_data).lower()
    has_cycle_code = cycle_data.get("error", {}).get("code") == "CYCLE_DETECTED"
    assert has_cycle_msg or has_cycle_code

    # 4. Remove prerequisite
    del_resp = client.delete(
        f"/instructor/courses/{c_a.public_id}/prerequisites/{c_b.public_id}",
        headers={"X-CSRFToken": csrf_token},
    )
    assert del_resp.status_code == 200
    del_data = del_resp.get_json()
    assert del_data.get("removed") is True

    # 5. Verify list is empty
    verify_resp = client.get(f"/instructor/courses/{c_a.public_id}/prerequisites")
    assert verify_resp.status_code == 200
    assert len(verify_resp.get_json()["prerequisites"]) == 0


# ============================================================================
# 2. Course Completion Rules API Parity
# ============================================================================
def test_course_completion_rules_api_parity(
    client: FlaskClient, parity_env: dict[str, Any]
) -> None:
    """Test retrieving and persisting Course Completion Rules."""
    inst = parity_env["instructor"]
    c_a = parity_env["course_a"]

    csrf_token = login_instructor(client, inst.email)

    # 1. Get default completion rules
    get_resp = client.get(f"/instructor/courses/{c_a.public_id}/completion-rules")
    assert get_resp.status_code == 200
    get_data = get_resp.get_json()
    assert get_data["course_id"] == str(c_a.public_id)
    assert "require_all_required_lessons" in get_data
    assert "require_required_assessments" in get_data
    assert "minimum_progress_percent" in get_data
    assert_adr002(get_data)

    # 2. Update completion rules
    update_payload = {
        "require_all_required_lessons": True,
        "require_required_assessments": False,
        "minimum_progress_percent": 85.0,
    }
    put_resp = client.put(
        f"/instructor/courses/{c_a.public_id}/completion-rules",
        json=update_payload,
        headers={"X-CSRFToken": csrf_token},
    )
    assert put_resp.status_code == 200, f"Put rules failed: {put_resp.get_data(as_text=True)}"
    put_data = put_resp.get_json()
    assert put_data["require_all_required_lessons"] is True
    assert put_data["require_required_assessments"] is False
    assert float(put_data["minimum_progress_percent"]) == 85.0
    assert_adr002(put_data)

    # 3. Confirm persistence via subsequent GET
    reget_resp = client.get(f"/instructor/courses/{c_a.public_id}/completion-rules")
    assert reget_resp.status_code == 200
    reget_data = reget_resp.get_json()
    assert reget_data["require_all_required_lessons"] is True
    assert reget_data["require_required_assessments"] is False
    assert float(reget_data["minimum_progress_percent"]) == 85.0


# ============================================================================
# 3. Question Bank Lifecycle & Revisions Parity
# ============================================================================
def test_question_bank_lifecycle_and_revisions_parity(
    client: FlaskClient, parity_env: dict[str, Any]
) -> None:
    """Test Question creation, detail viewing, patch, revision incrementing, trash and restore."""
    inst = parity_env["instructor"]
    course = parity_env["course_a"]
    lesson = parity_env["lesson"]

    csrf_token = login_instructor(client, inst.email)

    # 1. Create a question via POST /instructor/courses/<id>/questions
    create_payload = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "APPLY",
        "content": "Giao thuc nao hoat dong tai tang Transport trong mo hinh OSI?",
        "lesson_id": str(lesson.public_id),
        "choices": [
            {"content": "TCP", "is_correct": True, "position": 1},
            {"content": "IP", "is_correct": False, "position": 2},
            {"content": "HTTP", "is_correct": False, "position": 3},
        ],
    }
    create_resp = client.post(
        f"/instructor/courses/{course.public_id}/questions",
        json=create_payload,
        headers={"X-CSRFToken": csrf_token},
    )
    assert create_resp.status_code == 201, (
        f"Create question failed: {create_resp.get_data(as_text=True)}"
    )
    q_data = create_resp.get_json()
    q_id = q_data["question_id"]
    assert q_id is not None
    assert_adr002(q_data)

    # 2. Get question detail via GET /instructor/questions/<id>
    detail_resp = client.get(f"/instructor/questions/{q_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.get_json()
    assert detail_data["question_id"] == q_id
    assert "TCP" in str(detail_data["choices"])
    assert_adr002(detail_data)

    # 3. Patch question metadata via PATCH /instructor/questions/<id>
    patch_resp = client.patch(
        f"/instructor/questions/{q_id}",
        json={"difficulty": "UNDERSTAND"},
        headers={"X-CSRFToken": csrf_token},
    )
    assert patch_resp.status_code == 200
    patch_data = patch_resp.get_json()
    assert patch_data["difficulty"] == "UNDERSTAND"
    assert_adr002(patch_data)

    # 4. Create explicit revision via POST /instructor/questions/<id>/revisions
    rev_payload = {
        "change_type": "CONTENT_CHANGE",
        "reason": "Cap nhat bo sung lua chon UDP",
        "content": "Giao thuc nao sau day thuoc tang Giao van (Transport) trong bo TCP/IP?",
        "choices": [
            {"content": "TCP & UDP", "is_correct": True, "position": 1},
            {"content": "IP", "is_correct": False, "position": 2},
            {"content": "ICMP", "is_correct": False, "position": 3},
        ],
    }
    rev_create_resp = client.post(
        f"/instructor/questions/{q_id}/revisions",
        json=rev_payload,
        headers={"X-CSRFToken": csrf_token},
    )
    assert rev_create_resp.status_code == 201, (
        f"Create revision failed: {rev_create_resp.get_data(as_text=True)}"
    )
    rev_create_data = rev_create_resp.get_json()
    assert "revision" in rev_create_data
    assert rev_create_data["revision"]["revision_no"] >= 2
    assert_adr002(rev_create_data)

    # 5. List revisions via GET /instructor/questions/<id>/revisions
    rev_list_resp = client.get(f"/instructor/questions/{q_id}/revisions")
    assert rev_list_resp.status_code == 200
    rev_list_data = rev_list_resp.get_json()
    assert "items" in rev_list_data
    assert rev_list_data["total"] >= 2
    assert_adr002(rev_list_data)

    # 6. Trash question via POST /instructor/questions/<id>/trash
    trash_resp = client.post(
        f"/instructor/questions/{q_id}/trash",
        json={"reason": "Tam an cau hoi khoi de thi"},
        headers={"X-CSRFToken": csrf_token},
    )
    assert trash_resp.status_code == 200
    trash_data = trash_resp.get_json()
    assert trash_data["question"]["status"] == "TRASH"
    assert_adr002(trash_data)

    # 7. Restore question via POST /instructor/questions/<id>/restore
    restore_resp = client.post(
        f"/instructor/questions/{q_id}/restore",
        json={"reason": "Phuc hoi cau hoi vao ngan hang"},
        headers={"X-CSRFToken": csrf_token},
    )
    assert restore_resp.status_code == 200
    restore_data = restore_resp.get_json()
    assert restore_data["question"]["status"] != "TRASH"
    assert_adr002(restore_data)


# ============================================================================
# 4. Frontend Static Assets and Contract Parity
# ============================================================================
def test_frontend_static_assets_and_contract_parity(client: FlaskClient) -> None:
    """Verify that Frontend SPA assets are served and ApiClient covers all called methods."""
    # 1. Verify frontend JS assets exist and serve HTTP 200 with X-Frame-Options: SAMEORIGIN
    for asset_path in [
        "/frontend/assets/js/api.js",
        "/frontend/assets/js/router.js",
        "/frontend/assets/js/views/instructor.js",
        "/frontend/assets/js/views/student.js",
        "/frontend/assets/js/views/admin.js",
    ]:
        resp = client.get(asset_path)
        assert resp.status_code == 200, f"Asset failed to load: {asset_path}"
        assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"

    # 2. Verify all newly added and critical methods exist on ApiClient in api.js
    api_resp = client.get("/frontend/assets/js/api.js")
    api_source = api_resp.data.decode("utf-8")

    critical_methods = [
        "getCoursePrerequisites",
        "addCoursePrerequisite",
        "deleteCoursePrerequisite",
        "getCourseCompletionRules",
        "updateCourseCompletionRules",
        "getQuestionDetail",
        "updateQuestion",
        "trashQuestion",
        "restoreQuestion",
        "getQuestionRevisions",
        "createQuestionRevision",
        "getEnrolledCourses",
        "getCourses",
        "getCourseQuestionSummary",
        "attachLessonResource",
        "deleteLessonResource",
        "createAssessmentQuestion",
        "batchCreateAssessmentQuestions",
    ]
    for method in critical_methods:
        pattern = rf"(async\s+)?{method}\s*\("
        assert re.search(pattern, api_source), f"ApiClient missing critical method: {method}"

    # 3. Static contract parity check across all frontend view files
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "assets", "js")
    js_files = [
        os.path.join(frontend_dir, "router.js"),
        os.path.join(frontend_dir, "views", "instructor.js"),
        os.path.join(frontend_dir, "views", "student.js"),
        os.path.join(frontend_dir, "views", "admin.js"),
    ]

    # Extract all ApiClient.<method> calls
    called_methods: set[str] = set()
    call_regex = re.compile(r"ApiClient\.([a-zA-Z0-9_]+)\(")

    for js_file in js_files:
        if os.path.exists(js_file):
            with open(js_file, encoding="utf-8") as f:
                content = f.read()
                matches = call_regex.findall(content)
                called_methods.update(matches)

    # Extract all defined methods in ApiClient
    defined_regex = re.compile(r"static\s+(?:async\s+)?([a-zA-Z0-9_]+)\s*\(")
    defined_methods = set(defined_regex.findall(api_source))

    # Calculate any called methods that are missing from ApiClient
    missing_from_api = called_methods - defined_methods
    msg = f"Frontend views call {len(missing_from_api)} missing methods: {sorted(missing_from_api)}"
    assert not missing_from_api, msg
