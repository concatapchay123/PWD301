"""Regression coverage for Admin lesson-flag audit and notification delivery."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course, LearningUnit, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent, Notification, NotificationEvent
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def flag_roles(app: Any) -> dict[str, Role]:
    role_map: dict[str, Role] = {}
    for code, name in (
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ):
        role = db.session.query(Role).filter_by(code=code).first()
        if role is None:
            role = Role(code=code, name=name)
            db.session.add(role)
            db.session.flush()
        role_map[code] = role
    db.session.commit()
    return role_map


@pytest.fixture
def flag_fixture(app: Any, flag_roles: dict[str, Role]) -> dict[str, User | Course | Lesson]:
    admin = register_user(
        f"flag_admin_{uuid.uuid4().hex[:8]}@example.com", "Password@123", "Flag Admin"
    )
    admin = assign_role_to_user(admin.id, "ADMIN")
    instructor = register_user(
        f"flag_instructor_{uuid.uuid4().hex[:8]}@example.com",
        "Password@123",
        "Flag Instructor",
    )
    instructor = assign_role_to_user(instructor.id, "INSTRUCTOR")

    course = Course(
        course_code=f"FLG{uuid.uuid4().hex[:6].upper()}",
        title="Lesson Flag Regression Course",
        description="Course used to verify durable moderation outcomes.",
        owner_instructor_id=instructor.id,
        status="SUBMITTED_FOR_REVIEW",
    )
    db.session.add(course)
    db.session.flush()
    unit = LearningUnit(course_id=course.id, title="Flag Regression Unit", position=1)
    lesson = Lesson(
        course_id=course.id,
        learning_unit=unit,
        title="Flag Regression Lesson",
        order_index=1,
        status="PUBLISHED",
        markdown_content="# Content",
    )
    db.session.add(lesson)
    db.session.commit()
    return {"admin": admin, "instructor": instructor, "course": course, "lesson": lesson}


def _jwt_headers(admin: User) -> dict[str, str]:
    token = create_token_pair(admin)["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _assert_durable_flag(fixture: dict[str, User | Course | Lesson]) -> None:
    admin = fixture["admin"]
    instructor = fixture["instructor"]
    course = fixture["course"]
    lesson = fixture["lesson"]
    assert isinstance(admin, User)
    assert isinstance(instructor, User)
    assert isinstance(course, Course)
    assert isinstance(lesson, Lesson)

    db.session.expire_all()
    refreshed_lesson = db.session.get(Lesson, lesson.id)
    assert refreshed_lesson is not None
    assert refreshed_lesson.material_change_summary == "[FLAGGED]: abcde"

    audit = (
        db.session.query(AuditEvent)
        .filter_by(action="CONTENT_FLAGGED", target_type="LESSON", target_id=lesson.id)
        .one()
    )
    assert audit.actor_user_id == admin.id
    assert "ADMIN" in audit.actor_roles_snapshot.split(",")
    assert audit.after_state == {
        "course_id": str(course.public_id),
        "lesson_id": str(lesson.public_id),
        "content_type": "bài học",
        "reason": "abcde",
    }

    notification_rows = (
        db.session.query(Notification, NotificationEvent)
        .join(NotificationEvent, Notification.notification_event_id == NotificationEvent.id)
        .filter(
            Notification.recipient_user_id == instructor.id,
            NotificationEvent.event_type == "COURSE_CONTENT_FLAGGED",
        )
        .all()
    )
    assert len(notification_rows) == 1
    notification, _event = notification_rows[0]
    assert (
        notification.to_dict()["action_url"] == f"#/instructor/courses/manage?id={course.public_id}"
    )


def test_rest_lesson_flag_persists_audit_and_owner_notification(
    client: FlaskClient, flag_fixture: dict[str, User | Course | Lesson]
) -> None:
    admin = flag_fixture["admin"]
    course = flag_fixture["course"]
    lesson = flag_fixture["lesson"]
    assert isinstance(admin, User)
    assert isinstance(course, Course)
    assert isinstance(lesson, Lesson)

    response = client.post(
        f"/api/admin/courses/{course.public_id}/lessons/{lesson.public_id}/flag",
        json={"reason": "abcde"},
        headers=_jwt_headers(admin),
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    _assert_durable_flag(flag_fixture)


def test_rest_lesson_flag_idempotency_key_replays_without_duplicate_delivery(
    client: FlaskClient, flag_fixture: dict[str, User | Course | Lesson]
) -> None:
    """A retried moderation request must not duplicate durable notification side effects."""
    admin = flag_fixture["admin"]
    course = flag_fixture["course"]
    lesson = flag_fixture["lesson"]
    assert isinstance(admin, User)
    assert isinstance(course, Course)
    assert isinstance(lesson, Lesson)

    headers = {
        **_jwt_headers(admin),
        "X-Idempotency-Key": str(uuid.uuid4()),
    }
    path = f"/api/admin/courses/{course.public_id}/lessons/{lesson.public_id}/flag"
    first = client.post(path, json={"reason": "abcde"}, headers=headers)
    second = client.post(path, json={"reason": "abcde"}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.get_json()["idempotent_replay"] is False
    assert second.get_json()["idempotent_replay"] is True
    assert (
        db.session.query(AuditEvent)
        .filter_by(action="CONTENT_FLAGGED", target_type="LESSON", target_id=lesson.id)
        .count()
        == 1
    )
    assert (
        db.session.query(NotificationEvent)
        .filter_by(event_type="COURSE_CONTENT_FLAGGED", target_type="LESSON", target_id=lesson.id)
        .count()
        == 1
    )
    assert (
        db.session.query(Notification)
        .join(NotificationEvent, Notification.notification_event_id == NotificationEvent.id)
        .filter(
            Notification.recipient_user_id == flag_fixture["instructor"].id,
            NotificationEvent.event_type == "COURSE_CONTENT_FLAGGED",
        )
        .count()
        == 1
    )


def test_rest_lesson_flag_idempotency_key_rejects_changed_payload(
    client: FlaskClient, flag_fixture: dict[str, User | Course | Lesson]
) -> None:
    """A key reused for a different moderation reason must fail closed."""
    admin = flag_fixture["admin"]
    course = flag_fixture["course"]
    lesson = flag_fixture["lesson"]
    assert isinstance(admin, User)
    assert isinstance(course, Course)
    assert isinstance(lesson, Lesson)

    headers = {
        **_jwt_headers(admin),
        "X-Idempotency-Key": str(uuid.uuid4()),
    }
    path = f"/api/admin/courses/{course.public_id}/lessons/{lesson.public_id}/flag"
    first = client.post(path, json={"reason": "abcde"}, headers=headers)
    conflict = client.post(path, json={"reason": "different"}, headers=headers)

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert conflict.get_json()["error"]["code"] == "CONFLICT"
    assert (
        db.session.query(AuditEvent)
        .filter_by(action="CONTENT_FLAGGED", target_type="LESSON", target_id=lesson.id)
        .count()
        == 1
    )


def test_web_lesson_flag_persists_audit_and_owner_notification(
    client: FlaskClient, flag_fixture: dict[str, User | Course | Lesson]
) -> None:
    admin = flag_fixture["admin"]
    course = flag_fixture["course"]
    lesson = flag_fixture["lesson"]
    assert isinstance(admin, User)
    assert isinstance(course, Course)
    assert isinstance(lesson, Lesson)

    login_web_user(client, admin)
    response = client.post(
        f"/admin/courses/{course.public_id}/lessons/{lesson.public_id}/flag",
        json={"reason": "abcde"},
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    _assert_durable_flag(flag_fixture)


def test_web_lesson_flag_idempotency_key_replays_without_duplicate_delivery(
    client: FlaskClient, flag_fixture: dict[str, User | Course | Lesson]
) -> None:
    """The Web session route must share the same keyed retry contract as REST."""
    admin = flag_fixture["admin"]
    course = flag_fixture["course"]
    lesson = flag_fixture["lesson"]
    assert isinstance(admin, User)
    assert isinstance(course, Course)
    assert isinstance(lesson, Lesson)

    login_web_user(client, admin)
    path = f"/admin/courses/{course.public_id}/lessons/{lesson.public_id}/flag"
    headers = {"X-Idempotency-Key": str(uuid.uuid4())}
    first = client.post(path, json={"reason": "abcde"}, headers=headers)
    second = client.post(path, json={"reason": "abcde"}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.get_json()["idempotent_replay"] is False
    assert second.get_json()["idempotent_replay"] is True
    assert (
        db.session.query(NotificationEvent)
        .filter_by(event_type="COURSE_CONTENT_FLAGGED", target_type="LESSON", target_id=lesson.id)
        .count()
        == 1
    )


@pytest.mark.parametrize("payload", ["invalid", ["invalid"]])
def test_lesson_flag_rejects_non_object_json_without_mutation(
    client: FlaskClient,
    flag_fixture: dict[str, User | Course | Lesson],
    payload: object,
) -> None:
    admin = flag_fixture["admin"]
    course = flag_fixture["course"]
    lesson = flag_fixture["lesson"]
    assert isinstance(admin, User)
    assert isinstance(course, Course)
    assert isinstance(lesson, Lesson)

    response = client.post(
        f"/api/admin/courses/{course.public_id}/lessons/{lesson.public_id}/flag",
        json=payload,
        headers=_jwt_headers(admin),
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    db.session.expire_all()
    assert db.session.get(Lesson, lesson.id).material_change_summary is None
    assert (
        db.session.query(AuditEvent)
        .filter_by(action="CONTENT_FLAGGED", target_type="LESSON", target_id=lesson.id)
        .count()
        == 0
    )


def test_web_lesson_flag_rejects_non_object_json_without_mutation(
    client: FlaskClient, flag_fixture: dict[str, User | Course | Lesson]
) -> None:
    admin = flag_fixture["admin"]
    course = flag_fixture["course"]
    lesson = flag_fixture["lesson"]
    assert isinstance(admin, User)
    assert isinstance(course, Course)
    assert isinstance(lesson, Lesson)

    login_web_user(client, admin)
    response = client.post(
        f"/admin/courses/{course.public_id}/lessons/{lesson.public_id}/flag",
        json=["invalid"],
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"
    db.session.expire_all()
    assert db.session.get(Lesson, lesson.id).material_change_summary is None


def test_lesson_flag_rolls_back_when_owner_notification_fails(
    client: FlaskClient,
    flag_fixture: dict[str, User | Course | Lesson],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin = flag_fixture["admin"]
    course = flag_fixture["course"]
    lesson = flag_fixture["lesson"]
    assert isinstance(admin, User)
    assert isinstance(course, Course)
    assert isinstance(lesson, Lesson)

    def fail_dispatch(*args: object, **kwargs: object) -> tuple[None, None]:
        raise RuntimeError("notification sink unavailable")

    monkeypatch.setattr("pwd301.services.notification_service.dispatch_notification", fail_dispatch)
    response = client.post(
        f"/api/admin/courses/{course.public_id}/lessons/{lesson.public_id}/flag",
        json={"reason": "abcde"},
        headers=_jwt_headers(admin),
    )

    assert response.status_code == 500
    db.session.rollback()
    db.session.expire_all()
    assert db.session.get(Lesson, lesson.id).material_change_summary is None
    assert (
        db.session.query(AuditEvent)
        .filter_by(action="CONTENT_FLAGGED", target_type="LESSON", target_id=lesson.id)
        .count()
        == 0
    )
    assert (
        db.session.query(Notification)
        .join(NotificationEvent, Notification.notification_event_id == NotificationEvent.id)
        .filter(
            Notification.recipient_user_id == flag_fixture["instructor"].id,
            NotificationEvent.event_type == "COURSE_CONTENT_FLAGGED",
        )
        .count()
        == 0
    )
