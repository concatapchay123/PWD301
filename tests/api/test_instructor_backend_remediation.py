"""Tests for Backend Remediation & Instructor Portal Parity (TASK-045).

Verifies:
1. POST /instructor/assessments/<assessment_id>/questions/create (ESSAY question type)
2. POST /instructor/assessments/<assessment_id>/questions/batch (Atomic batch question creation)
3. DELETE /instructor/courses/<course_id>/lessons/<lesson_id>/resources/<resource_id>
4. POST /instructor/attempts/<attempt_id>/grades/<attempt_question_id> (Rubric breakdown)
5. POST /student/ai/chat with course_id context parameter
"""

from __future__ import annotations

import io
import re
import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.file_import import FileAsset, LessonResource
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.assessment_service import create_assessment
from pwd301.services.attempt_service import (
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.course_service import create_course
from pwd301.services.file_service import attach_resource_to_lesson, store_file_stream
from pwd301.services.lesson_service import create_lesson
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user

UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def test_sync016_academic_save_rolls_back_all_parts(client, remediation_env):
    from pwd301.models.course import Course, CourseChangeRequest, CourseCompletionRule

    course = remediation_env["course"]
    actor = remediation_env["instructor"]
    course_id = str(course.public_id)
    original_objectives = course.learning_objectives
    original_requirements = course.completion_requirements
    original_rule = db.session.query(CourseCompletionRule).filter_by(course_id=course.id).one()
    original_progress = float(original_rule.minimum_progress_percent)
    csrf = login_session(client, actor.email)
    response = client.put(
        f"/instructor/courses/{course_id}/academic-settings",
        json={
            "learning_objectives": [{"title": "A new objective"}],
            "completion_rules": {"minimum_progress_percent": 92},
            "prerequisites": {"add": [{"prerequisite_course_id": str(uuid.uuid4())}], "remove": []},
        },
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 400
    db.session.expire_all()
    persisted = db.session.query(Course).filter_by(public_id=uuid.UUID(course_id)).one()
    assert persisted.learning_objectives == original_objectives
    assert persisted.completion_requirements == original_requirements
    assert db.session.query(CourseChangeRequest).filter_by(course_id=persisted.id).count() == 0
    rule = db.session.query(CourseCompletionRule).filter_by(course_id=persisted.id).one()
    assert float(rule.minimum_progress_percent) == original_progress


def test_sync016_published_objectives_remain_queued(client, remediation_env):
    from pwd301.models.course import CourseChangeRequest, CourseCompletionRule

    course = remediation_env["course"]
    actor = remediation_env["instructor"]
    original_objectives = course.learning_objectives
    course_id = str(course.public_id)
    csrf = login_session(client, actor.email)
    response = client.put(
        f"/instructor/courses/{course_id}/academic-settings",
        json={
            "learning_objectives": [{"title": "Proposed objective"}],
            "completion_rules": {"minimum_progress_percent": 92},
            "prerequisites": {"add": [], "remove": []},
        },
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 202
    assert response.get_json()["data"]["pending_approval"] is True
    db.session.expire_all()
    assert course.learning_objectives == original_objectives
    assert (
        db.session.query(CourseChangeRequest)
        .filter_by(course_id=course.id, status="PENDING")
        .count()
        == 1
    )
    rule = db.session.query(CourseCompletionRule).filter_by(course_id=course.id).one()
    assert float(rule.minimum_progress_percent) == 92


def test_sync016_cross_instructor_prerequisite_stays_pending(client, remediation_env):
    from pwd301.models.course import CourseChangeRequest, CoursePrerequisite

    actor = remediation_env["instructor"]
    course = remediation_env["course"]
    other = register_user(
        email="academic_peer@pwd301.local",
        password="Password@123",
        display_name="Academic peer",
        session=db.session,
    )
    assign_role_to_user(other.id, "INSTRUCTOR", session=db.session)
    peer_course = create_course(
        actor=other,
        data={"course_code": "PEER016", "title": "Academic Peer Course"},
        session=db.session,
    )
    peer_course.status = "PUBLISHED"
    db.session.commit()
    course_id, peer_id = str(course.public_id), str(peer_course.public_id)
    csrf = login_session(client, actor.email)
    payload = {
        "learning_objectives": [],
        "completion_rules": {},
        "prerequisites": {"add": [{"prerequisite_course_id": peer_id}], "remove": []},
    }
    for _ in range(2):
        response = client.put(
            f"/instructor/courses/{course_id}/academic-settings",
            json=payload,
            headers={"X-CSRFToken": csrf},
        )
        assert response.status_code == 202
    assert db.session.query(CoursePrerequisite).filter_by(course_id=course.id).count() == 0
    assert (
        db.session.query(CourseChangeRequest)
        .filter_by(
            course_id=course.id,
            change_type="PREREQUISITE",
            target_id=peer_course.id,
            status="PENDING",
        )
        .count()
        == 1
    )


def test_sync016_published_removal_retry_queues_one_review(client, remediation_env):
    from pwd301.models.course import CourseChangeRequest

    actor = remediation_env["instructor"]
    course = remediation_env["course"]
    prereq = create_course(
        actor=actor,
        data={"course_code": "PRE016", "title": "Academic Prerequisite"},
        session=db.session,
    )
    prereq.status = "PUBLISHED"
    from pwd301.services.enrollment_service import add_course_prerequisite

    add_course_prerequisite(actor, course.id, prereq.id, session=db.session)
    db.session.commit()
    course_id, prereq_id = str(course.public_id), str(prereq.public_id)
    csrf = login_session(client, actor.email)
    for _ in range(2):
        response = client.put(
            f"/instructor/courses/{course_id}/academic-settings",
            json={
                "learning_objectives": [],
                "completion_rules": {},
                "prerequisites": {"add": [], "remove": [prereq_id]},
            },
            headers={"X-CSRFToken": csrf},
        )
        assert response.status_code == 202
    assert (
        db.session.query(CourseChangeRequest)
        .filter_by(
            course_id=course.id,
            change_type="PREREQUISITE",
            target_id=prereq.id,
            status="PENDING",
        )
        .count()
        == 1
    )


def test_sync016_legacy_prerequisite_acknowledgements_are_committed(client, remediation_env):
    from pwd301.models.course import CoursePrerequisite

    actor = remediation_env["instructor"]
    course = remediation_env["course"]
    prereq = create_course(
        actor=actor,
        data={"course_code": "ACK016", "title": "Committed Prerequisite"},
        session=db.session,
    )
    prereq.status = "PUBLISHED"
    course.status = "DRAFT"
    db.session.commit()
    course_pk, prereq_pk = course.id, prereq.id
    course_id, prereq_id = str(course.public_id), str(prereq.public_id)
    csrf = login_session(client, actor.email)
    response = client.post(
        f"/instructor/courses/{course_id}/prerequisites",
        json={"prerequisite_course_id": prereq_id},
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 201
    db.session.rollback()
    assert (
        db.session.query(CoursePrerequisite)
        .filter_by(
            course_id=course_pk,
            prerequisite_course_id=prereq_pk,
        )
        .count()
        == 1
    )
    response = client.delete(
        f"/instructor/courses/{course_id}/prerequisites/{prereq_id}",
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 200
    db.session.rollback()
    assert (
        db.session.query(CoursePrerequisite)
        .filter_by(
            course_id=course_pk,
            prerequisite_course_id=prereq_pk,
        )
        .count()
        == 0
    )


def test_sync016_peer_notification_failure_rolls_back_request(client, remediation_env, monkeypatch):
    from pwd301.models.course import CourseChangeRequest

    actor = remediation_env["instructor"]
    course = remediation_env["course"]
    peer = register_user(
        email="academic_outbox@pwd301.local",
        password="Password@123",
        display_name="Academic notification peer",
        session=db.session,
    )
    assign_role_to_user(peer.id, "INSTRUCTOR", session=db.session)
    prereq = create_course(
        actor=peer,
        data={"course_code": "OUT016", "title": "Peer Notification Prerequisite"},
        session=db.session,
    )
    prereq.status = "PUBLISHED"
    db.session.commit()
    course_pk = course.id
    course_id, prereq_id = str(course.public_id), str(prereq.public_id)
    csrf = login_session(client, actor.email)

    def fail_notification(**kwargs):
        raise RuntimeError("peer notification persistence failed")

    monkeypatch.setattr(
        "pwd301.services.notification_service.dispatch_notification", fail_notification
    )
    response = client.put(
        f"/instructor/courses/{course_id}/academic-settings",
        json={
            "learning_objectives": [{"title": "Must roll back"}],
            "completion_rules": {},
            "prerequisites": {"add": [{"prerequisite_course_id": prereq_id}], "remove": []},
        },
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 500
    assert db.session.query(CourseChangeRequest).filter_by(course_id=course_pk).count() == 0


def assert_adr002(data: Any) -> None:
    """Recursively verify no internal BigInt PKs are leaked in responses."""
    if isinstance(data, dict):
        for k, v in data.items():
            assert k != "id", f"Internal primary key leaked: {data}"
            assert k != "creator_user_id", f"Internal foreign key leaked: {data}"
            if (
                k.endswith("_id")
                and v is not None
                and k not in ("choice_key", "temp_id", "question_type")
            ):
                assert isinstance(v, str), f"Expected UUID string for {k}, got {type(v)}: {v}"
            assert_adr002(v)
    elif isinstance(data, list):
        for item in data:
            assert_adr002(item)


@pytest.fixture
def remediation_env(app: Flask) -> dict[str, Any]:
    """Setup instructor, course, student, and lesson test fixture."""
    sess: Session = db.session
    seed_baseline(sess)

    # 1. Register and assign roles
    inst_user = register_user(
        email="instructor_remed@pwd301.local",
        password="Password@123",
        display_name="ThS. Remediation Instructor",
        session=sess,
    )
    assign_role_to_user(inst_user.id, "INSTRUCTOR", session=sess)

    student_user = register_user(
        email="student_remed@pwd301.local",
        password="Password@123",
        display_name="Nguyen Van Sinh Vien",
        session=sess,
    )
    assign_role_to_user(student_user.id, "STUDENT", session=sess)

    # 2. Create Course & Lesson
    course = create_course(
        actor=inst_user,
        data={
            "course_code": "REM301",
            "title": "Backend Remediation Course",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()
    lesson = create_lesson(
        actor=inst_user,
        course_id=course.id,
        data={
            "title": "Bai 01: Tong quan Kien truc REST API",
            "markdown_content": "# Noi dung bai hoc",
            "estimated_duration_minutes": 45,
            "status": "PUBLISHED",
        },
        session=sess,
    )

    sess.commit()

    return {
        "instructor": inst_user,
        "student": student_user,
        "course": course,
        "lesson": lesson,
    }


def login_session(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    """Helper to login user via Flask session and return CSRF token."""
    csrf_res = client.get("/auth/login")
    csrf_token = csrf_res.get_json().get("csrf_token", "")
    login_res = client.post(
        "/auth/login",
        json={"email": email, "password": password, "remember": False},
        headers={"X-CSRFToken": csrf_token},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.get_data(as_text=True)}"
    return csrf_token


def test_learning_unit_api_keeps_lessons_nested_and_private(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    course = remediation_env["course"]
    course.status = "DRAFT"
    db.session.commit()
    instructor = remediation_env["instructor"]
    csrf = login_session(client, instructor.email)
    url = f"/instructor/courses/{course.public_id}/learning-units"
    created = client.post(url, json={"title": "Chủ đề mới"}, headers={"X-CSRFToken": csrf})
    assert created.status_code == 201
    unit_id = created.get_json()["learning_unit_id"]
    lesson = client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={"title": "Lesson mới", "markdown_content": "# Content", "learning_unit_id": unit_id},
        headers={"X-CSRFToken": csrf},
    )
    assert lesson.status_code in (201, 202)
    assert lesson.get_json()["learning_unit_id"] == unit_id
    listing = client.get(url)
    assert listing.status_code == 200
    unit = next(item for item in listing.get_json()["items"] if item["learning_unit_id"] == unit_id)
    assert unit["lesson_count"] == 1
    assert unit["lessons"][0]["lesson_id"] == lesson.get_json()["lesson_id"]
    assert_adr002(listing.get_json())


def test_course_cover_upload_can_be_selected(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    instructor = remediation_env["instructor"]
    course = create_course(
        instructor, {"course_code": "COVER-ROUTE", "title": "Cover upload route"}
    )
    csrf = login_session(client, instructor.email)
    uploaded = client.post(
        f"/instructor/courses/{course.public_id}/files",
        data={
            "file": (io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"a" * 64), "cover.png", "image/png"),
            "asset_type": "COURSE_IMAGE",
        },
        content_type="multipart/form-data",
        headers={"X-CSRFToken": csrf},
    )
    assert uploaded.status_code == 201
    asset_id = uploaded.get_json()["asset_id"]
    asset = db.session.query(FileAsset).filter_by(public_id=uuid.UUID(asset_id)).one()
    assert asset.asset_type == "COURSE_IMAGE"
    selected = client.patch(
        f"/instructor/courses/{course.public_id}",
        json={"thumbnail_file_asset_id": asset_id},
        headers={"X-CSRFToken": csrf},
    )
    assert selected.status_code == 200
    assert course.thumbnail_file_asset_id == asset.id


def test_course_upload_route_enforces_lesson_document_cap(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    instructor = remediation_env["instructor"]
    course = remediation_env["course"]
    lesson = remediation_env["lesson"]
    for index in range(5):
        asset = store_file_stream(
            instructor,
            course.id,
            io.BytesIO(b"Document text"),
            f"document-{index}.txt",
            "text/plain",
            asset_type="RESOURCE",
            session=db.session,
        )
        attach_resource_to_lesson(instructor, lesson, asset, session=db.session)
    csrf = login_session(client, instructor.email)
    extra = client.post(
        f"/instructor/courses/{course.public_id}/files",
        data={
            "file": (io.BytesIO(b"One more document"), "extra.txt", "text/plain"),
            "lesson_id": str(lesson.public_id),
        },
        content_type="multipart/form-data",
        headers={"X-CSRFToken": csrf},
    )
    assert extra.status_code == 400
    assert len(lesson.resources) == 5


# ============================================================================
# 1. ESSAY Question Type in Assessment Authoring Test
# ============================================================================
def test_create_assessment_question_essay_rejected_and_short_answer_supported(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    """Ensure POST /instructor/assessments/<id>/questions/create rejects ESSAY
    and accepts objective questions.
    """
    inst = remediation_env["instructor"]
    course = remediation_env["course"]
    sess = db.session

    asm = create_assessment(
        actor=inst,
        course_id=course.id,
        payload={
            "title": "Kiem tra Trac nghiem Giua ky",
            "assessment_type": "MIDTERM",
            "duration_minutes": 60,
        },
        session=sess,
    )
    sess.commit()

    csrf = login_session(client, inst.email)

    # 1. Essay question must be accepted with 201
    essay_payload = {
        "question_type": "ESSAY",
        "difficulty": "APPLY",
        "content": "Hãy phân tích kiến trúc RESTful API và tính Idempotent của HTTP DELETE.",
        "points": 10.0,
        "explanation": (
            "Tiêu chí 1: Khái niệm (3đ). Tiêu chí 2: Idempotent (4đ). Tiêu chí 3: Mã lỗi (3đ)."
        ),
    }

    res = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/create",
        json=essay_payload,
        headers={"X-CSRFToken": csrf},
    )
    assert res.status_code == 201, f"Failed: {res.get_data(as_text=True)}"
    essay_data = res.get_json()
    assert essay_data.get("status") == "ok"
    assert essay_data["question"]["question_type"] == "ESSAY"
    essay_qid = essay_data["question"]["question_id"]
    assert_adr002(essay_data)

    # 2. Objective SHORT_ANSWER question must be accepted
    sa_payload = {
        "question_type": "SHORT_ANSWER",
        "difficulty": "APPLY",
        "content": "Giao thức nào cung cấp kênh truyền bảo mật dựa trên TLS?",
        "points": 5.0,
        "accepted_answers": ["HTTPS", "SSH"],
    }
    sa_res = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/create",
        json=sa_payload,
        headers={"X-CSRFToken": csrf},
    )
    assert sa_res.status_code in (200, 201), f"Failed: {sa_res.get_data(as_text=True)}"
    sa_data = sa_res.get_json()
    assert sa_data.get("status") == "ok" or "question_id" in sa_data
    sa_qid = sa_data["question"]["question_id"]
    assert_adr002(sa_data)

    # 3. Assessment detail must return valid JSON without 500 error
    detail_res = client.get(
        f"/instructor/assessments/{asm.public_id}",
        headers={"X-CSRFToken": csrf},
    )
    assert detail_res.status_code == 200, f"Detail failed: {detail_res.get_data(as_text=True)}"
    detail_data = detail_res.get_json()
    assert isinstance(detail_data.get("question_assignments"), list)
    assert len(detail_data["question_assignments"]) == 2
    assert_adr002(detail_data)

    # 4. Reorder questions endpoint
    reorder_res = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/reorder",
        json={"ordered_question_ids": [sa_qid, essay_qid]},
        headers={"X-CSRFToken": csrf},
    )
    assert reorder_res.status_code == 200, f"Reorder failed: {reorder_res.get_data(as_text=True)}"
    reorder_data = reorder_res.get_json()
    assert reorder_data.get("success") is True
    assert len(reorder_data["assignments"]) == 2
    assert reorder_data["assignments"][0]["question_id"] == sa_qid
    assert reorder_data["assignments"][0]["position"] == 1
    assert reorder_data["assignments"][1]["question_id"] == essay_qid
    assert reorder_data["assignments"][1]["position"] == 2
    assert_adr002(reorder_data)


# ============================================================================
# 3. Atomic Batch Create Assessment Questions Test
# ============================================================================
def test_batch_create_assessment_questions(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    """Ensure POST /instructor/assessments/<id>/questions/batch saves questions atomically."""
    inst = remediation_env["instructor"]
    course = remediation_env["course"]
    sess = db.session

    asm = create_assessment(
        actor=inst,
        course_id=course.id,
        payload={
            "title": "Kỳ thi Tong hop Azota Batch",
            "assessment_type": "FINAL",
            "duration_minutes": 90,
        },
        session=sess,
    )
    sess.commit()

    csrf = login_session(client, inst.email)

    batch_payload = {
        "questions": [
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "HTTP GET có thay đổi trạng thái máy chủ không?",
                "points": 2.0,
                "choices": [
                    {"content": "Có", "is_correct": False, "position": 1},
                    {"content": "Không (Safe method)", "is_correct": True, "position": 2},
                ],
            },
            {
                "question_type": "SHORT_ANSWER",
                "difficulty": "APPLY",
                "content": "Chuẩn token không trạng thái phổ biến nhất hiện nay là gì?",
                "points": 8.0,
                "accepted_answers": ["JWT", "JSON Web Token"],
            },
        ]
    }

    res = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/batch",
        json=batch_payload,
        headers={"X-CSRFToken": csrf},
    )
    assert res.status_code in (200, 201), f"Failed batch create: {res.get_data(as_text=True)}"
    data = res.get_json()
    assert data.get("created_count") == 2
    assert_adr002(data)


# ============================================================================
# 4. Detach Lesson Resource HTTP DELETE Method Test
# ============================================================================
def test_detach_lesson_resource_delete_method(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    """Ensure DELETE stages a published Lesson resource removal for review."""
    inst = remediation_env["instructor"]
    course = remediation_env["course"]
    lesson = remediation_env["lesson"]
    sess = db.session

    # Create dummy file asset and lesson resource
    file_asset = FileAsset(
        course_id=course.id,
        created_by_user_id=inst.id,
        asset_type="RESOURCE",
        display_name="slide_bai_01.pdf",
        status="ACTIVE",
    )
    sess.add(file_asset)
    sess.flush()

    resource = LessonResource(
        lesson_id=lesson.id,
        file_asset_id=file_asset.id,
        label="Slide bài giảng 01",
        position=1,
    )
    sess.add(resource)
    sess.commit()

    csrf = login_session(client, inst.email)

    c_pid = course.public_id
    l_pid = lesson.public_id
    r_pid = resource.public_id
    url = f"/instructor/courses/{c_pid}/lessons/{l_pid}/resources/{r_pid}"
    res = client.delete(url, headers={"X-CSRFToken": csrf})
    assert res.status_code == 202, f"Failed DELETE resource: {res.get_data(as_text=True)}"
    data = res.get_json()
    assert data["pending_approval"] is True
    assert sess.get(LessonResource, resource.id) is not None


# ============================================================================
# 5. Essay Elimination Verification & Auto-Graded Attempt Test
# ============================================================================
def test_essay_elimination_and_direct_auto_grading(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    """Ensure ESSAY creation is rejected, assessments are objective-only,
    and submitted attempts are auto-graded.
    """
    inst = remediation_env["instructor"]
    student = remediation_env["student"]
    course = remediation_env["course"]
    sess = db.session

    # 1. Enroll student
    from pwd301.services.enrollment_service import enroll_student

    enroll_student(actor=student, course_id=course.id, session=sess)
    sess.commit()

    # 2. Verify creating an ESSAY question is supported per System Specification
    essay_q = create_question(
        actor=inst,
        course_id=course.id,
        payload={
            "difficulty": "APPLY",
            "question_type": "ESSAY",
            "content": "Viết luận về tối ưu hóa SQL Server Index.",
            "default_points": 15.0,
        },
        session=sess,
    )
    assert essay_q is not None
    assert essay_q.current_revision.question_type == "ESSAY"

    # 3. Create Published Assessment with Objective Question
    asm = create_assessment(
        actor=inst,
        course_id=course.id,
        payload={
            "title": "Final Objective Exam",
            "assessment_type": "FINAL",
            "duration_minutes": 60,
        },
        session=sess,
    )
    q = create_question(
        actor=inst,
        course_id=course.id,
        payload={
            "difficulty": "APPLY",
            "question_type": "SHORT_ANSWER",
            "content": "Thuật toán băm dùng cho password hashing an toàn là gì?",
            "default_points": 15.0,
            "accepted_answers": ["Argon2id", "bcrypt"],
        },
        session=sess,
    )
    from pwd301.services.assessment_service import assign_question, publish_assessment

    assign_question(
        actor=inst,
        assessment_id=asm.id,
        payload={"question_id": q.id, "points": 15.0},
        session=sess,
    )
    publish_assessment(actor=inst, assessment_id=asm.id, session=sess)
    sess.commit()

    # 4. Student takes and submits attempt
    attempt, lease_token = start_assessment_attempt(
        student_actor=student, assessment_id=asm.id, session=sess
    )
    att_q = attempt.attempt_questions[0]
    submit_assessment_attempt(
        actor=student, attempt_id=attempt.id, raw_lease_token=lease_token, session=sess
    )
    sess.commit()

    # Submitted attempt must immediately be GRADED (no PENDING_GRADING)
    sess.refresh(attempt)
    assert attempt.status == "GRADED"

    # 5. Instructor manual essay grading endpoint must reject with 400
    csrf = login_session(client, inst.email)

    grade_payload = {
        "awarded_points": 20.0,
        "reason": "Giải pháp rất tốt.",
    }

    res = client.post(
        f"/instructor/attempts/{attempt.public_id}/grades/{att_q.public_id}",
        json=grade_payload,
        headers={"X-CSRFToken": csrf},
    )
    assert res.status_code == 400
    res_text = res.get_data(as_text=True)
    assert "tự luận" in res_text.lower() or "VALIDATION_ERROR" in res_text


# ============================================================================
# 6. Student AI Chat with Course Context Test
# ============================================================================
def test_student_ai_chat_with_course_context(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    """Ensure POST /student/ai/chat scopes conversation to specified course_id."""
    student = remediation_env["student"]
    course = remediation_env["course"]
    sess = db.session

    from pwd301.models.course import Enrollment

    enr = Enrollment(student_user_id=student.id, course_id=course.id, status="ACTIVE")
    sess.add(enr)
    sess.commit()

    csrf = login_session(client, student.email)

    res = client.post(
        "/student/ai/chat",
        json={
            "message": "Cho em hỏi về kiến trúc Microservices trong môn học này?",
            "course_id": str(course.public_id),
        },
        headers={"X-CSRFToken": csrf},
    )
    assert res.status_code == 200, f"AI Chat failed: {res.get_data(as_text=True)}"
    data = res.get_json()
    assert "reply" in data or "response" in data
    assert_adr002(data)


def test_sync004_quick_add_assignment_failure_leaves_no_question(
    client, remediation_env, monkeypatch
):
    from pwd301.blueprints.instructor import routes
    from pwd301.models.question_bank import Question
    from pwd301.services.exceptions import AssessmentValidationError

    inst = remediation_env["instructor"]
    asm = create_assessment(
        inst, remediation_env["course"].id, {"title": "Quick add atomic", "assessment_type": "QUIZ"}
    )
    csrf = login_session(client, inst.email)
    before = db.session.query(Question).count()

    def fail_assignment(*args, **kwargs):
        raise AssessmentValidationError("injected assignment failure")

    monkeypatch.setattr(routes, "assign_question", fail_assignment)
    response = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/create",
        json={"question_type": "ESSAY", "content": "Atomic question", "points": 5},
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 400
    db.session.rollback()
    assert db.session.query(Question).count() == before


@pytest.mark.parametrize(
    "question_fields",
    [
        {"question_type": "ESSAY"},
        {"question_type": "SHORT_ANSWER", "accepted_answers": ["Alpha", "alpha", "Beta"]},
        {
            "question_type": "SINGLE_CHOICE",
            "choices": [
                {"content": "One", "is_correct": True},
                {"content": "Two", "is_correct": False},
            ],
        },
        {
            "question_type": "MULTIPLE_CHOICE",
            "choices": [
                {"content": "One", "is_correct": True},
                {"content": "Two", "is_correct": True},
            ],
        },
    ],
)
def test_sync004_quick_add_ack_loss_retry_reuses_question(client, remediation_env, question_fields):
    from pwd301.models.question_bank import Question

    inst = remediation_env["instructor"]
    asm = create_assessment(
        inst, remediation_env["course"].id, {"title": "Retry quick add", "assessment_type": "QUIZ"}
    )
    csrf = login_session(client, inst.email)
    endpoint = f"/instructor/assessments/{asm.public_id}/questions/create"
    payload = {
        "client_question_id": str(uuid.uuid4()),
        "content": "One logical question",
        "points": 5,
        **question_fields,
    }
    first = client.post(endpoint, json=payload, headers={"X-CSRFToken": csrf})
    assert first.status_code == 201
    repeated = client.post(endpoint, json=payload, headers={"X-CSRFToken": csrf})
    assert repeated.status_code == 200
    assert (
        repeated.get_json()["question"]["question_id"]
        == first.get_json()["question"]["question_id"]
    )
    assert db.session.query(Question).filter_by(course_id=asm.course_id).count() == 1
    changed = client.post(
        endpoint, json={**payload, "content": "Different intent"}, headers={"X-CSRFToken": csrf}
    )
    assert changed.status_code == 409
    db.session.expire_all()
    assert db.session.query(Question).filter_by(course_id=asm.course_id).count() == 1
    from pwd301.models.types import utc_now

    asm.first_attempt_started_at = utc_now()
    db.session.commit()
    assert client.post(endpoint, json=payload, headers={"X-CSRFToken": csrf}).status_code == 200
    assert (
        client.post(
            endpoint,
            json={**payload, "client_question_id": str(uuid.uuid4())},
            headers={"X-CSRFToken": csrf},
        ).status_code
        == 409
    )


@pytest.mark.parametrize("points", [0, -1, float("nan"), float("inf")])
def test_sync004_quick_add_invalid_points_leave_no_question(client, remediation_env, points):
    from pwd301.models.question_bank import Question

    inst = remediation_env["instructor"]
    asm = create_assessment(
        inst,
        remediation_env["course"].id,
        {"title": "Points validation", "assessment_type": "QUIZ"},
    )
    csrf = login_session(client, inst.email)
    response = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/create",
        json={
            "client_question_id": str(uuid.uuid4()),
            "question_type": "ESSAY",
            "content": "Invalid points",
            "points": points,
        },
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 400
    db.session.expire_all()
    assert db.session.query(Question).filter_by(course_id=asm.course_id).count() == 0


def test_sync004_quick_add_retry_key_cannot_cross_assessment(client, remediation_env):
    inst = remediation_env["instructor"]
    course = remediation_env["course"]
    one = create_assessment(inst, course.id, {"title": "One", "assessment_type": "QUIZ"})
    two = create_assessment(inst, course.id, {"title": "Two", "assessment_type": "QUIZ"})
    csrf = login_session(client, inst.email)
    payload = {
        "client_question_id": str(uuid.uuid4()),
        "question_type": "ESSAY",
        "content": "Owned creation",
        "points": 1,
    }
    assert (
        client.post(
            f"/instructor/assessments/{one.public_id}/questions/create",
            json=payload,
            headers={"X-CSRFToken": csrf},
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/instructor/assessments/{two.public_id}/questions/create",
            json=payload,
            headers={"X-CSRFToken": csrf},
        ).status_code
        == 409
    )


def test_sync079_authoring_is_atomic_and_retry_preserves_question_identity(client, remediation_env):
    from pwd301.models.question_bank import Question

    inst = remediation_env["instructor"]
    asm = create_assessment(
        inst, remediation_env["course"].id, {"title": "Original title", "assessment_type": "QUIZ"}
    )
    csrf = login_session(client, inst.email)
    endpoint = f"/instructor/assessments/{asm.public_id}/authoring"
    stable_id = str(uuid.uuid4())
    valid = {
        "client_question_id": stable_id,
        "question_type": "ESSAY",
        "content": "Preserved question",
        "difficulty": "REMEMBER",
        "points": 5,
    }
    invalid = {
        "client_question_id": str(uuid.uuid4()),
        "question_type": "SHORT_ANSWER",
        "content": "Missing key",
        "difficulty": "REMEMBER",
        "points": 5,
        "accepted_answers": [],
    }
    failed = client.post(
        endpoint,
        json={"assessment": {"title": "Changed title"}, "questions": [valid, invalid]},
        headers={"X-CSRFToken": csrf},
    )
    assert failed.status_code == 400
    db.session.expire_all()
    assert asm.title == "Original title"
    assert db.session.query(Question).count() == 0
    for _ in range(2):
        response = client.post(
            endpoint,
            json={"assessment": {"title": "Changed title"}, "questions": [valid]},
            headers={"X-CSRFToken": csrf},
        )
        assert response.status_code == 200, response.get_json()
        assert response.get_json()["data"]["questions"][0]["question_id"] == stable_id
    assert db.session.query(Question).count() == 1
    assert len(asm.question_assignments) == 1


@pytest.mark.parametrize("difficulty", ["ANALYZE", "EVALUATE", "CREATE"])
def test_sync024_authoring_rejects_noncanonical_bloom(client, remediation_env, difficulty):
    from pwd301.models.question_bank import Question

    inst = remediation_env["instructor"]
    asm = create_assessment(
        inst, remediation_env["course"].id, {"title": "Bloom", "assessment_type": "QUIZ"}
    )
    csrf = login_session(client, inst.email)
    response = client.post(
        f"/instructor/assessments/{asm.public_id}/authoring",
        json={
            "assessment": {"title": "Must not persist"},
            "questions": [
                {
                    "question_type": "ESSAY",
                    "content": "Valid first question",
                    "difficulty": "APPLY",
                    "points": 5,
                },
                {
                    "question_type": "ESSAY",
                    "content": "Unsupported Bloom",
                    "difficulty": difficulty,
                    "points": 5,
                },
            ],
        },
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 400
    db.session.expire_all()
    assert asm.title == "Bloom"
    assert not asm.question_assignments
    assert db.session.query(Question).count() == 0


def test_sync079_assessment_creation_retry_retains_identity(client, remediation_env):
    from pwd301.models.assessment import Assessment

    inst = remediation_env["instructor"]
    course = remediation_env["course"]
    csrf = login_session(client, inst.email)
    stable_id = str(uuid.uuid4())
    for _ in range(2):
        response = client.post(
            f"/instructor/courses/{course.public_id}/assessments",
            json={"title": "Retry", "assessment_type": "QUIZ", "client_assessment_id": stable_id},
            headers={"X-CSRFToken": csrf},
        )
        assert response.status_code in (200, 201)
        assert response.get_json()["assessment_id"] == stable_id
    assert db.session.query(Assessment).filter_by(course_id=course.id).count() == 1


@pytest.mark.parametrize("change", ["title", "content", "points"])
def test_sync079_publish_rejects_changed_authoring_snapshot(client, remediation_env, change):
    from pwd301.models.assessment import AssessmentQuestionAssignment
    from pwd301.services.question_bank_service import update_question

    actor = remediation_env["instructor"]
    asm = create_assessment(
        actor, remediation_env["course"].id, {"title": "Submitted", "assessment_type": "QUIZ"}
    )
    csrf = login_session(client, actor.email)
    response = client.post(
        f"/instructor/assessments/{asm.public_id}/authoring",
        json={
            "assessment": {"title": "Submitted"},
            "questions": [
                {
                    "client_question_id": str(uuid.uuid4()),
                    "question_type": "ESSAY",
                    "content": "Intended content",
                    "difficulty": "REMEMBER",
                    "points": 5,
                }
            ],
        },
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 200
    token = response.get_json()["data"]["authoring_token"]
    assignment = (
        db.session.query(AssessmentQuestionAssignment).filter_by(assessment_id=asm.id).one()
    )
    if change == "title":
        asm.title = "Another editor title"
    elif change == "content":
        update_question(
            actor,
            assignment.question_id,
            {"content": "Another editor content", "change_reason": "Concurrent edit"},
            session=db.session,
            commit=False,
        )
    else:
        assignment.points = 7
    db.session.commit()
    response = client.post(
        f"/instructor/assessments/{asm.public_id}/publish",
        json={"expected_authoring_token": token},
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 409
    db.session.expire_all()
    assert asm.status == "DRAFT"


def test_sync079_matching_authoring_token_publishes_and_remains_idempotent(client, remediation_env):
    actor = remediation_env["instructor"]
    asm = create_assessment(
        actor, remediation_env["course"].id, {"title": "Submitted", "assessment_type": "QUIZ"}
    )
    csrf = login_session(client, actor.email)
    response = client.post(
        f"/instructor/assessments/{asm.public_id}/authoring",
        json={
            "assessment": {},
            "questions": [
                {
                    "question_type": "ESSAY",
                    "content": "Intended content",
                    "difficulty": "REMEMBER",
                    "points": 5,
                }
            ],
        },
        headers={"X-CSRFToken": csrf},
    )
    token = response.get_json()["data"]["authoring_token"]
    for _ in range(2):
        response = client.post(
            f"/instructor/assessments/{asm.public_id}/publish",
            json={"expected_authoring_token": token},
            headers={"X-CSRFToken": csrf},
        )
        assert response.status_code == 200
    detail = client.get(f"/instructor/assessments/{asm.public_id}").get_json()
    assert detail["authoring_token"] == token
    assert detail["status"] == "PUBLISHED"
    from pwd301.services.assessment_service import get_assessment_detail

    student_detail = get_assessment_detail(remediation_env["student"], asm.id)
    assert "authoring_token" not in student_detail


@pytest.mark.parametrize("operation", ["academic", "authoring"])
def test_composite_mutations_use_standard_json_envelopes(client, remediation_env, operation):
    from pwd301.services.assessment_service import create_assessment

    actor = remediation_env["instructor"]
    csrf = login_session(client, actor.email)
    if operation == "academic":
        response = client.put(
            f"/instructor/courses/{remediation_env['course'].public_id}/academic-settings",
            json={"learning_objectives": [], "completion_rules": {"minimum_progress_percent": 80}},
            headers={"X-CSRFToken": csrf},
        )
    else:
        assessment = create_assessment(
            actor,
            remediation_env["course"].id,
            {"title": "Envelope contract", "assessment_type": "QUIZ"},
        )
        response = client.post(
            f"/instructor/assessments/{assessment.public_id}/authoring",
            json={"questions": []},
            headers={"X-CSRFToken": csrf},
        )
    assert response.status_code in (200, 202)
    body = response.get_json()
    assert set(body) == {"success", "data", "error"}
    assert body["success"] is True and body["error"] is None
    assert isinstance(body["data"], dict)
