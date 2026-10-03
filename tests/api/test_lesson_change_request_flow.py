import io
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, Lesson
from pwd301.models.file_import import LessonResource
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.file_service import attach_resource_to_lesson, store_file_stream
from pwd301.services.lesson_service import create_learning_unit, create_lesson
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    email = f"instructor_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Instructor Test")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Admin Test")
    return assign_role_to_user(u.id, "ADMIN")


def test_update_and_delete_lesson_in_published_course_requires_admin_approval(
    client: FlaskClient, instructor_user: User, admin_user: User
):
    """When a course is published, lesson edits and deletes must create a change request
    for admin review."""
    sess = db.session

    # 1. Create published course and lesson
    course = Course(
        course_code=f"PUB_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"PUB_{uuid.uuid4().hex[:4]}",
        title="Published Course",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()

    lesson = create_lesson(
        actor=instructor_user,
        course_id=course.id,
        data={
            "title": "Initial Lesson Title",
            "markdown_content": "# Initial Content",
            "status": "PUBLISHED",
        },
        session=sess,
    )
    sess.commit()

    login_web_user(client, instructor_user)

    # 2. Instructor edits lesson -> saves to working draft with 200 OK
    res_edit = client.put(
        f"/instructor/lessons/{lesson.id}",
        json={"title": "Updated Title That Needs Admin Approval"},
    )
    assert res_edit.status_code == 200
    edit_data = res_edit.get_json()
    assert edit_data["is_draft"] is True

    # Lesson title in DB remains unchanged until approved
    sess.expire_all()
    lesson_check = sess.get(Lesson, lesson.id)
    assert lesson_check.title == "Initial Lesson Title"

    # 3. Instructor stages deletion of lesson -> returns 200 OK
    res_del = client.post(
        f"/instructor/courses/{course.id}/lessons/{lesson.id}/delete",
        json={"reason": "Request to remove obsolete chapter"},
    )
    assert res_del.status_code == 200
    del_data = res_del.get_json()
    assert del_data.get("is_staged_delete") is True

    # Lesson is NOT trashed yet
    sess.expire_all()
    assert lesson_check.deleted_at is None

    # 4. Instructor submits consolidated changeset -> returns 202
    res_submit = client.post(
        f"/instructor/courses/{course.id}/changeset/submit",
        json={
            "version_title": "Cap Nhat Hoc Ky 1",
            "summary": "Sua tieu de bai hoc va xoa bai",
        },
    )
    assert res_submit.status_code == 202
    changeset_req_id = res_submit.get_json()["change_request_id"]

    # 5. Admin logs in and checks change requests
    login_web_user(client, admin_user)

    list_res = client.get("/admin/change-requests")
    assert list_res.status_code == 200
    list_json = list_res.get_json()
    assert list_json["pending_count"] >= 1

    # 6. Admin approves the changeset
    approve_res = client.post(
        f"/admin/change-requests/{changeset_req_id}/review",
        json={"action": "approve", "reason": "Syllabus revision accepted"},
    )
    assert approve_res.status_code == 200
    assert approve_res.get_json()["status"] == "APPROVED"

    # Live database reflects the approved updates
    sess.expire_all()
    active_lessons = (
        sess.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.status == "PUBLISHED", Lesson.deleted_at.is_(None))
        .all()
    )
    assert any(les.title == "Updated Title That Needs Admin Approval" for les in active_lessons)
    lesson_orig = sess.get(Lesson, lesson.id)
    assert lesson_orig.status == "HISTORICAL" or lesson_orig.deleted_at is not None


def test_repeated_lesson_edit_reuses_pending_review_and_notification(
    client: FlaskClient, instructor_user: User, admin_user: User
):
    sess = db.session
    code = f"REVIEW_{uuid.uuid4().hex[:8]}"
    course = Course(
        course_code=code,
        course_code_normalized=code,
        title=f"Review course {code}",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()
    lesson = create_lesson(
        instructor_user,
        course.id,
        {"title": "Original lesson", "markdown_content": "Original", "status": "PUBLISHED"},
        session=sess,
    )
    sess.commit()
    login_web_user(client, instructor_user)
    first = client.put(f"/instructor/lessons/{lesson.id}", json={"title": "Revision A"})
    second = client.put(f"/instructor/lessons/{lesson.id}", json={"title": "Revision A"})
    third = client.put(f"/instructor/lessons/{lesson.id}", json={"title": "Revision B"})
    assert [response.status_code for response in (first, second, third)] == [200, 200, 200]
    drafts = (
        sess.query(Lesson)
        .filter_by(course_id=course.id, status="DRAFT", previous_lesson_id=lesson.id)
        .all()
    )
    assert len(drafts) == 1
    assert drafts[0].title == "Revision B"
    sess.refresh(lesson)
    assert lesson.title == "Original lesson"


def test_partial_lesson_edit_preserves_fields_already_waiting_for_review(
    client: FlaskClient, instructor_user: User, admin_user: User
):
    sess = db.session
    code = f"PARTIAL_{uuid.uuid4().hex[:8]}"
    course = Course(
        course_code=code,
        course_code_normalized=code,
        title=f"Partial course {code}",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()
    lesson = create_lesson(
        instructor_user,
        course.id,
        {"title": "Original", "markdown_content": "Original content", "status": "PUBLISHED"},
        session=sess,
    )
    sess.commit()
    login_web_user(client, instructor_user)
    first = client.patch(f"/instructor/lessons/{lesson.id}", json={"title": "New title"})
    second = client.patch(f"/instructor/lessons/{lesson.id}", json={"summary": "New summary"})
    assert first.status_code == second.status_code == 200
    draft = (
        sess.query(Lesson)
        .filter_by(course_id=course.id, status="DRAFT", previous_lesson_id=lesson.id)
        .first()
    )
    assert draft is not None
    assert draft.title == "New title"
    assert draft.summary == "New summary"


def test_admin_approval_applies_lesson_completion_rules(
    client: FlaskClient, instructor_user: User, admin_user: User
):
    sess = db.session
    code = f"RULES_{uuid.uuid4().hex[:8]}"
    course = Course(
        course_code=code,
        course_code_normalized=code,
        title=f"Rules course {code}",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()
    lesson = create_lesson(
        instructor_user,
        course.id,
        {"title": "Original", "markdown_content": "Original content", "status": "PUBLISHED"},
        session=sess,
    )
    sess.commit()
    login_web_user(client, instructor_user)
    response = client.patch(
        f"/instructor/lessons/{lesson.id}",
        json={"minimum_completion_seconds": 90, "viewed_fraction_required": 0.9},
    )
    assert response.status_code == 200
    res_sub = client.post(
        f"/instructor/courses/{course.id}/changeset/submit",
        json={"version_title": "Cap nhat quy tac", "summary": "Sua completion rules"},
    )
    assert res_sub.status_code == 202
    request_id = res_sub.get_json()["change_request_id"]
    login_web_user(client, admin_user)
    reviewed = client.post(
        f"/admin/change-requests/{request_id}/review",
        json={"action": "approve"},
    )
    assert reviewed.status_code == 200
    sess.expire_all()
    active_lesson = (
        sess.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.status == "PUBLISHED", Lesson.deleted_at.is_(None))
        .first()
    )
    assert active_lesson.minimum_completion_seconds == 90
    assert float(active_lesson.viewed_fraction_required) == 0.9


def test_admin_queue_shows_latest_legacy_duplicate_only(
    client: FlaskClient, instructor_user: User, admin_user: User
):
    sess = db.session
    code = f"LEGACY_{uuid.uuid4().hex[:8]}"
    course = Course(
        course_code=code,
        course_code_normalized=code,
        title=f"Legacy course {code}",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()
    lesson = create_lesson(
        instructor_user,
        course.id,
        {"title": "Original", "markdown_content": "Original content"},
        session=sess,
    )
    sess.commit()
    old = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=instructor_user.id,
        change_type="LESSON_CONTENT",
        target_type="LESSON",
        target_id=lesson.id,
        proposed_payload_json='{"title":"Old proposal"}',
        status="PENDING",
        created_at=utc_now(),
    )
    latest = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=instructor_user.id,
        change_type="LESSON_CONTENT",
        target_type="LESSON",
        target_id=lesson.id,
        proposed_payload_json='{"title":"Latest proposal"}',
        status="PENDING",
        created_at=utc_now(),
    )
    sess.add_all([old, latest])
    sess.commit()
    login_web_user(client, admin_user)
    response = client.get("/admin/change-requests?status=PENDING")
    assert response.status_code == 200
    data = response.get_json()
    assert data["pending_count"] == 1
    assert [item["id"] for item in data["change_requests"]] == [latest.id]
    review = client.post(
        f"/admin/change-requests/{latest.id}/review",
        json={"action": "approve", "reason": "Latest proposal accepted"},
    )
    assert review.status_code == 200
    sess.refresh(old)
    assert old.status == "REJECTED"


def test_learning_unit_title_edit_waits_for_admin_review(
    client: FlaskClient, instructor_user: User, admin_user: User
):
    sess = db.session
    code = f"UNIT_{uuid.uuid4().hex[:8]}"
    course = Course(
        course_code=code,
        course_code_normalized=code,
        title=f"Unit course {code}",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="DRAFT",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()
    unit = create_learning_unit(instructor_user, course.id, {"title": "Tên cũ"})
    course.status = "PUBLISHED"
    sess.commit()
    login_web_user(client, instructor_user)
    response = client.patch(
        f"/instructor/learning-units/{unit.public_id}", json={"title": "Tên mới"}
    )
    assert response.status_code == 202
    request_id = response.get_json()["change_request_id"]
    sess.refresh(unit)
    assert unit.title == "Tên cũ"
    login_web_user(client, admin_user)
    listed = client.get("/admin/change-requests?status=PENDING").get_json()
    proposal = next(item for item in listed["change_requests"] if item["id"] == request_id)
    assert proposal["original_data"]["title"] == "Tên cũ"
    assert proposal["proposed_payload"]["title"] == "Tên mới"
    reviewed = client.post(
        f"/admin/change-requests/{request_id}/review",
        json={"action": "approve", "reason": "Phù hợp"},
    )
    assert reviewed.status_code == 200
    sess.refresh(unit)
    assert unit.title == "Tên mới"


def test_published_lesson_resources_change_only_after_admin_approval(
    client: FlaskClient, instructor_user: User, admin_user: User
):
    sess = db.session
    code = f"RESOURCE_{uuid.uuid4().hex[:8]}"
    course = Course(
        course_code=code,
        course_code_normalized=code,
        title=f"Resource course {code}",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="DRAFT",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()
    lesson = create_lesson(
        instructor_user,
        course.id,
        {"title": "Lesson", "markdown_content": "Content", "status": "PUBLISHED"},
        session=sess,
    )
    old_asset = store_file_stream(
        instructor_user,
        course.id,
        io.BytesIO(b"old file"),
        "old.pdf",
        "application/pdf",
        session=sess,
    )
    old_resource = attach_resource_to_lesson(
        instructor_user,
        lesson.id,
        old_asset.id,
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.commit()

    login_web_user(client, instructor_user)
    upload = client.post(
        f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
        data={"file": (io.BytesIO(b"new file"), "new.pdf")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 202
    assert upload.get_json()["pending_approval"] is True
    attach_review_id = upload.get_json()["change_request_id"]
    assert sess.query(LessonResource).filter_by(lesson_id=lesson.id).count() == 1

    removal = client.delete(
        f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}"
        f"/resources/{old_resource.public_id}"
    )
    assert removal.status_code == 202
    assert removal.get_json()["change_request_id"] == attach_review_id
    assert sess.query(LessonResource).filter_by(lesson_id=lesson.id).count() == 1

    login_web_user(client, admin_user)
    listed = client.get("/admin/change-requests?status=PENDING").get_json()
    proposal = next(item for item in listed["change_requests"] if item["id"] == attach_review_id)
    assert len(proposal["proposed_payload"]["changes"]) == 2
    approved = client.post(
        f"/admin/change-requests/{attach_review_id}/review",
        json={"action": "approve"},
    )
    assert approved.status_code == 200
    resources = sess.query(LessonResource).filter_by(lesson_id=lesson.id).all()
    assert len(resources) == 1
    assert resources[0].file_asset.display_name == "new.pdf"

    login_web_user(client, instructor_user)
    generic_upload = client.post(
        f"/instructor/courses/{course.public_id}/files",
        data={
            "file": (io.BytesIO(b"third file"), "third.pdf"),
            "lesson_id": str(lesson.public_id),
        },
        content_type="multipart/form-data",
    )
    assert generic_upload.status_code == 202
    assert generic_upload.get_json()["pending_approval"] is True
    assert sess.query(LessonResource).filter_by(lesson_id=lesson.id).count() == 1


def test_draft_lesson_in_published_course_can_be_edited_before_submission(
    client: FlaskClient, instructor_user: User
):
    sess = db.session
    code = f"DRAFT_{uuid.uuid4().hex[:8]}"
    course = Course(
        course_code=code,
        course_code_normalized=code,
        title=f"Draft course {code}",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="DRAFT",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()
    lesson = create_lesson(
        instructor_user,
        course.id,
        {"title": "Draft", "markdown_content": "# Draft", "status": "DRAFT"},
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.commit()
    login_web_user(client, instructor_user)
    edited = client.patch(
        f"/instructor/lessons/{lesson.public_id}", json={"title": "Draft revised"}
    )
    assert edited.status_code == 200
    sess.refresh(lesson)
    assert lesson.title == "Draft revised"
    assert sess.query(CourseChangeRequest).filter_by(course_id=course.id).count() == 0

    submitted = client.post(
        f"/instructor/lessons/{lesson.public_id}/status", json={"status": "PUBLISHED"}
    )
    assert submitted.status_code == 202
    sess.refresh(lesson)
    assert lesson.status == "DRAFT"
