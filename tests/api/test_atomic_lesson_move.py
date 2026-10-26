import json
import uuid
from datetime import UTC, datetime

import pytest

from backend.extensions import db
from backend.models.course import CourseChangeRequest, Lesson
from backend.services.course_service import create_course
from backend.services.lesson_service import create_learning_unit, create_lesson, update_lesson
from tests.api.test_lesson_authoring_remediation import admin_user as admin_user
from tests.api.test_lesson_authoring_remediation import instructor_user as instructor_user
from tests.api.test_lesson_authoring_remediation import setup_roles as setup_roles
from tests.conftest import login_web_user


@pytest.fixture
def move_env(instructor_user):
    course = create_course(
        instructor_user,
        {
            "course_code": "MOVE-" + uuid.uuid4().hex[:8],
            "title": "Atomic move course",
        },
    )
    first_unit = create_learning_unit(instructor_user, course.id, {"title": "First unit"})
    target_unit = create_learning_unit(instructor_user, course.id, {"title": "Target unit"})
    first = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Moved lesson",
            "markdown_content": "Retained content",
            "learning_unit_id": str(first_unit.public_id),
        },
    )
    second = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Other lesson",
            "markdown_content": "Other content",
            "learning_unit_id": str(first_unit.public_id),
        },
    )
    third = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Target lesson",
            "markdown_content": "Target content",
            "learning_unit_id": str(target_unit.public_id),
        },
    )
    return course, first_unit, target_unit, first, second, third


def move_payload(env):
    _, _, target, first, second, third = env
    return {
        "ordered_lesson_ids": [str(second.public_id), str(first.public_id), str(third.public_id)],
        "move": {"lesson_id": str(first.public_id), "learning_unit_id": str(target.public_id)},
    }


def assert_moved(env):
    course, _, target, first, second, third = env
    db.session.expire_all()
    rows = db.session.query(Lesson).filter_by(course_id=course.id).order_by(Lesson.position).all()
    assert [row.id for row in rows] == [second.id, first.id, third.id]
    assert db.session.get(Lesson, first.id).learning_unit_id == target.id
    assert db.session.get(Lesson, first.id).markdown_content == "Retained content"


def test_move_and_order_apply_together(client, instructor_user, move_env):
    login_web_user(client, instructor_user)
    response = client.post(
        f"/instructor/courses/{move_env[0].public_id}/lessons/reorder", json=move_payload(move_env)
    )
    assert response.status_code == 200
    assert_moved(move_env)


def test_move_order_failure_rolls_back_placement(client, instructor_user, move_env, monkeypatch):
    from backend.services import lesson_service

    original = lesson_service._record_lesson_audit_event

    def fail_order_audit(*args, **kwargs):
        if kwargs.get("action") == "LESSON_REORDERED":
            raise RuntimeError("Controlled ordering audit fault")
        return original(*args, **kwargs)

    monkeypatch.setattr(lesson_service, "_record_lesson_audit_event", fail_order_audit)
    login_web_user(client, instructor_user)
    response = client.post(
        f"/instructor/courses/{move_env[0].public_id}/lessons/reorder", json=move_payload(move_env)
    )
    assert response.status_code == 500
    db.session.expire_all()
    assert db.session.get(Lesson, move_env[3].id).learning_unit_id == move_env[1].id
    assert [
        row.id
        for row in db.session.query(Lesson)
        .filter_by(course_id=move_env[0].id)
        .order_by(Lesson.position)
    ] == [row.id for row in move_env[3:]]


def test_published_move_waits_for_atomic_admin_approval(
    client, instructor_user, admin_user, move_env, monkeypatch
):
    course, source, _, first, _, _ = move_env
    course.status = "PUBLISHED"
    db.session.commit()
    login_web_user(client, instructor_user)
    response = client.post(
        f"/instructor/courses/{course.public_id}/lessons/reorder", json=move_payload(move_env)
    )
    assert response.status_code == 202
    request_id = response.get_json()["change_request_id"]
    proposal = json.loads(db.session.get(CourseChangeRequest, request_id).proposed_payload_json)
    assert proposal["move"]["lesson_title"] == "Moved lesson"
    assert proposal["move"]["source_unit_title"] == "First unit"
    assert proposal["move"]["target_unit_title"] == "Target unit"
    repeated = client.post(
        f"/instructor/courses/{course.public_id}/lessons/reorder", json=move_payload(move_env)
    )
    assert repeated.status_code == 202
    assert repeated.get_json()["change_request_id"] == request_id
    changed = move_payload(move_env)
    changed["ordered_lesson_ids"].reverse()
    conflict = client.post(f"/instructor/courses/{course.public_id}/lessons/reorder", json=changed)
    assert conflict.status_code == 409
    db.session.expire_all()
    assert db.session.get(Lesson, first.id).learning_unit_id == source.id
    login_web_user(client, admin_user)
    from backend.services import lesson_service

    original = lesson_service._record_lesson_audit_event

    def fail_order_audit(*args, **kwargs):
        if kwargs.get("action") == "LESSON_REORDERED":
            raise RuntimeError("Controlled review ordering fault")
        return original(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(lesson_service, "_record_lesson_audit_event", fail_order_audit)
        failed = client.post(
            f"/admin/change-requests/{request_id}/review",
            json={"status": "APPROVED", "reason": "Approve placement and order"},
        )
    assert failed.status_code == 500
    db.session.expire_all()
    assert db.session.get(CourseChangeRequest, request_id).status == "PENDING"
    assert db.session.get(Lesson, first.id).learning_unit_id == source.id
    accepted = client.post(
        f"/admin/change-requests/{request_id}/review",
        json={"status": "APPROVED", "reason": "Approve placement and order"},
    )
    assert accepted.status_code == 200
    assert_moved(move_env)


@pytest.mark.parametrize("published", [False, True])
def test_move_rejects_foreign_target_before_any_write(client, instructor_user, move_env, published):
    foreign = create_course(
        instructor_user, {"course_code": "FOREIGN-" + uuid.uuid4().hex[:8], "title": "Other course"}
    )
    unit = create_learning_unit(instructor_user, foreign.id, {"title": "Foreign unit"})
    if published:
        move_env[0].status = "PUBLISHED"
        db.session.commit()
    payload = move_payload(move_env)
    payload["move"]["learning_unit_id"] = str(unit.public_id)
    login_web_user(client, instructor_user)
    response = client.post(
        f"/instructor/courses/{move_env[0].public_id}/lessons/reorder", json=payload
    )
    assert response.status_code == 400
    db.session.expire_all()
    assert db.session.get(Lesson, move_env[3].id).learning_unit_id == move_env[1].id
    assert db.session.query(CourseChangeRequest).filter_by(course_id=move_env[0].id).count() == 0


@pytest.mark.parametrize(
    "invalid", ["deleted_unit", "missing_move_id", "incomplete_order", "historical"]
)
def test_published_move_validates_before_queue(client, instructor_user, move_env, invalid):
    payload = move_payload(move_env)
    move_env[0].status = "PUBLISHED"
    if invalid == "deleted_unit":
        move_env[2].deleted_at = datetime.now(UTC)
    elif invalid == "missing_move_id":
        payload["move"].pop("lesson_id")
    elif invalid == "historical":
        move_env[3].status = "HISTORICAL"
    else:
        payload["ordered_lesson_ids"].pop()
    db.session.commit()
    login_web_user(client, instructor_user)
    response = client.post(
        f"/instructor/courses/{move_env[0].public_id}/lessons/reorder", json=payload
    )
    assert response.status_code in (400, 409)
    db.session.expire_all()
    assert db.session.get(Lesson, move_env[3].id).learning_unit_id == move_env[1].id
    assert db.session.query(CourseChangeRequest).filter_by(course_id=move_env[0].id).count() == 0


def test_move_preserves_target_chapter_lesson_limit(client, instructor_user, move_env):
    for index in range(9):
        create_lesson(
            instructor_user,
            move_env[0].id,
            {
                "title": f"Target sibling {index}",
                "markdown_content": "Unchanged content",
                "learning_unit_id": str(move_env[2].public_id),
            },
        )
    payload = move_payload(move_env)
    payload["ordered_lesson_ids"] = [
        str(row.public_id)
        for row in db.session.query(Lesson)
        .filter_by(course_id=move_env[0].id)
        .order_by(Lesson.position)
    ]
    login_web_user(client, instructor_user)
    response = client.post(
        f"/instructor/courses/{move_env[0].public_id}/lessons/reorder", json=payload
    )
    assert response.status_code == 400
    db.session.expire_all()
    assert db.session.get(Lesson, move_env[3].id).learning_unit_id == move_env[1].id


def test_move_preserves_target_chapter_video_limit(client, instructor_user, move_env):
    content = '<!-- video_urls: ["https://youtu.be/fixture-one", "https://youtu.be/fixture-two"] -->\n\nRetained content'
    update_lesson(instructor_user, move_env[3].id, {"markdown_content": content})
    for index in range(3):
        create_lesson(
            instructor_user,
            move_env[0].id,
            {
                "title": f"Video sibling {index}",
                "markdown_content": content,
                "learning_unit_id": str(move_env[2].public_id),
            },
        )
    payload = move_payload(move_env)
    payload["ordered_lesson_ids"] = [
        str(row.public_id)
        for row in db.session.query(Lesson)
        .filter_by(course_id=move_env[0].id)
        .order_by(Lesson.position)
    ]
    login_web_user(client, instructor_user)
    response = client.post(
        f"/instructor/courses/{move_env[0].public_id}/lessons/reorder", json=payload
    )
    assert response.status_code == 400
    db.session.expire_all()
    assert db.session.get(Lesson, move_env[3].id).learning_unit_id == move_env[1].id
