"""Approval is object-bound, audited and respects the caller's transaction."""

import json

import pytest

from pwd301.extensions import db
from pwd301.models.course import CourseChangeRequest, Lesson
from pwd301.models.notification_audit import AuditEvent
from pwd301.services.lesson_service import approve_course_change_request, create_lesson
from tests.api.test_video_preview_stream import video_env as video_fixture
from tests.conftest import login_web_user


@pytest.fixture
def video_env(app):
    return video_fixture.__wrapped__(app)


@pytest.fixture
def approval_env(video_env):
    users, asset, _, _, _ = video_env
    course = asset.course
    lesson = create_lesson(
        users["owner"], course.id, {"title": "Original", "markdown_content": "Old"}
    )
    req = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=users["owner"].id,
        change_type="LESSON_CONTENT",
        target_type="LESSON",
        target_id=lesson.id,
        proposed_payload_json=json.dumps({"title": "Updated"}),
        status="PENDING",
    )
    db.session.add(req)
    db.session.commit()
    return users, course, lesson, req


@pytest.mark.parametrize("payload", [[], [1]])
def test_non_object_saved_payload_is_business_error(client, approval_env, payload):
    users, _, _, req = approval_env
    req.proposed_payload_json = json.dumps(payload)
    db.session.commit()
    login_web_user(client, users["reviewer"])
    response = client.post(f"/admin/change-requests/{req.id}/review", json={"action": "approve"})
    assert response.status_code == 400
    db.session.expire_all()
    assert req.status == "PENDING"


def test_non_object_payload_diff_is_business_error(client, approval_env):
    users, _, _, req = approval_env
    req.proposed_payload_json = "[]"
    db.session.commit()
    login_web_user(client, users["reviewer"])
    assert client.get(f"/admin/change-requests/{req.id}/diff").status_code == 400


@pytest.mark.parametrize("changes", [None, {}, [None]])
def test_malformed_resource_changes_return_business_errors(client, approval_env, changes):
    users, _, _, req = approval_env
    req.proposed_payload_json = json.dumps({"action": "RESOURCE_CHANGES", "changes": changes})
    db.session.commit()
    login_web_user(client, users["reviewer"])
    assert client.get("/admin/change-requests?status=PENDING").status_code == 400
    assert client.get(f"/admin/change-requests/{req.id}/diff").status_code == 400
    assert (
        client.post(
            f"/admin/change-requests/{req.id}/review", json={"action": "approve"}
        ).status_code
        == 400
    )
    assert req.status == "PENDING"


def test_resource_proposal_preview_uses_public_file_handle(client, approval_env, video_env):
    users, _, _, req = approval_env
    _, asset, _, _, _ = video_env
    req.proposed_payload_json = json.dumps(
        {"action": "RESOURCE_CHANGES", "changes": [{"action": "ATTACH", "asset_id": asset.id}]}
    )
    db.session.commit()
    login_web_user(client, users["reviewer"])
    response = client.get("/admin/change-requests?status=PENDING")
    item = next(item for item in response.json["items"] if item["id"] == req.id)
    assert item["proposed_payload"]["changes"][0]["asset_id"] == str(asset.public_id)


def test_resource_detach_unknown_link_does_not_approve(client, approval_env):
    users, _, _, req = approval_env
    req.proposed_payload_json = json.dumps(
        {"action": "RESOURCE_CHANGES", "changes": [{"action": "DETACH", "resource_id": 999999}]}
    )
    db.session.commit()
    login_web_user(client, users["reviewer"])
    response = client.post(f"/admin/change-requests/{req.id}/review", json={"action": "approve"})
    assert response.status_code == 400
    db.session.expire_all()
    assert req.status == "PENDING"


def test_approval_persists_required_audit_and_retry_has_no_second_mutation(client, approval_env):
    users, _, lesson, req = approval_env
    login_web_user(client, users["reviewer"])
    response = client.post(f"/admin/change-requests/{req.id}/review", json={"action": "approve"})
    assert response.status_code == 200
    assert lesson.title == "Updated"
    audits = (
        db.session.query(AuditEvent)
        .filter_by(
            target_type="COURSE_CHANGE_REQUEST", target_id=req.id, action="COURSE_CHANGE_APPROVED"
        )
        .all()
    )
    assert len(audits) == 1
    retry = client.post(f"/admin/change-requests/{req.id}/review", json={"action": "approve"})
    assert retry.status_code in (400, 409)
    assert (
        db.session.query(AuditEvent)
        .filter_by(target_type="COURSE_CHANGE_REQUEST", target_id=req.id)
        .count()
        == 1
    )


def test_service_does_not_commit_caller_owned_transaction(approval_env):
    users, course, lesson, req = approval_env
    staged = Lesson(
        course_id=course.id,
        learning_unit_id=lesson.learning_unit_id,
        title="Staged",
        position=lesson.position,
        status="DRAFT",
        previous_lesson_id=lesson.id,
        change_request_id=req.id,
        markdown_content="New",
    )
    db.session.add(staged)
    db.session.commit()
    req_id, staged_id = req.id, staged.id
    approve_course_change_request(users["reviewer"], req_id, session=db.session)
    db.session.rollback()
    assert db.session.get(CourseChangeRequest, req_id).status == "PENDING"
    assert db.session.get(Lesson, staged_id).status == "DRAFT"


def test_foreign_lesson_target_cannot_be_mutated(client, approval_env):
    users, course, lesson, req = approval_env
    # A valid foreign course is used so integrity validation cannot mask authorization.
    from pwd301.services.course_service import create_course

    foreign_course = create_course(
        users["foreign"], {"course_code": "FOREIGN090", "title": "Foreign course"}
    )
    req.course_id = foreign_course.id
    db.session.commit()
    login_web_user(client, users["reviewer"])
    response = client.post(f"/admin/change-requests/{req.id}/review", json={"action": "approve"})
    assert response.status_code == 400
    db.session.expire_all()
    assert lesson.title == "Original"


def test_reviewer_course_preview_retains_chapter_identity_without_creating_lessons(
    client, approval_env
):
    users, _, lesson, req = approval_env
    login_web_user(client, users["reviewer"])
    count_before = db.session.query(Lesson).count()
    response = client.get("/admin/change-requests?status=PENDING")
    assert response.status_code == 200
    item = next(item for item in response.json["items"] if item["id"] == req.id)
    preview_lesson = next(item for item in item["course_lessons"] if item["id"] == lesson.id)
    assert preview_lesson["learning_unit_id"] == str(lesson.learning_unit.public_id)
    assert preview_lesson["learning_unit_title"] == lesson.learning_unit.title
    assert db.session.query(Lesson).count() == count_before
