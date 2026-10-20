"""Tests for Realtime Server-Sent Events (SSE) Infrastructure & Course Lifecycle.

Covers:
1. SSEManager connection subscriptions, role/user event routing, ping heartbeats.
2. Safe domain event emission (emit_domain_event).
3. SSE streaming HTTP endpoints (/api/events/stream, /auth/events/stream).
4. Domain event integration into course, lesson, changeset, and notification workflows.
5. Symmetrical course DELETE endpoints for Instructor and Admin.
6. Admin course management filtering out DRAFT courses with exclude_draft=true.
"""

from __future__ import annotations

import json
import queue
import uuid
from typing import Any
from unittest.mock import patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.course_service import (
    create_course,
    publish_course,
    trash_course,
    update_course,
)
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import create_lesson
from pwd301.services.notification_service import (
    broadcast_system_notification,
    dispatch_notification,
)
from pwd301.services.realtime_service import (
    SSEManager,
    emit_domain_event,
    get_sse_manager,
)
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def clean_sse_manager() -> SSEManager:
    """Create an isolated SSEManager instance for unit testing."""
    return SSEManager()


@pytest.fixture
def seeded_users(app: Flask) -> dict[str, int]:
    """Seed test admin and instructor accounts and return their persistent IDs."""
    with app.app_context():
        sess = db.session
        for code, name in [
            ("STUDENT", "Student"),
            ("INSTRUCTOR", "Instructor"),
            ("ADMIN", "System Administrator"),
        ]:
            role = sess.query(Role).filter(Role.code == code).first()
            if role is None:
                sess.add(Role(code=code, name=name))
        sess.commit()

        uid = uuid.uuid4().hex[:6]
        admin = register_user(f"admin_{uid}@example.com", "Password@123", f"Admin {uid}")
        admin = assign_role_to_user(admin.id, "ADMIN")

        instructor = register_user(f"inst_{uid}@example.com", "Password@123", f"Instructor {uid}")
        instructor = assign_role_to_user(instructor.id, "INSTRUCTOR")

        return {
            "admin_id": admin.id,
            "instructor_id": instructor.id,
        }


# ==============================================================================
# 1. SSEManager Unit Tests
# ==============================================================================


class TestSSEManagerUnit:
    """Unit tests for the thread-safe SSEManager pub/sub engine."""

    def test_subscribe_and_unsubscribe(self, clean_sse_manager: SSEManager) -> None:
        """Verify subscriber queues can be registered and clean up properly."""
        assert clean_sse_manager.active_subscribers_count() == 0
        q = clean_sse_manager.subscribe(user_id=10, role="INSTRUCTOR")
        assert clean_sse_manager.active_subscribers_count() == 1
        assert isinstance(q, queue.Queue)

        clean_sse_manager.unsubscribe(q)
        assert clean_sse_manager.active_subscribers_count() == 0

    def test_publish_event_broadcast_to_all(self, clean_sse_manager: SSEManager) -> None:
        """When neither target_roles nor target_user_ids is given, event goes to everyone."""
        q1 = clean_sse_manager.subscribe(user_id=1, role="ADMIN")
        q2 = clean_sse_manager.subscribe(user_id=2, role="STUDENT")

        count = clean_sse_manager.publish_event(
            event_type="test:broadcast",
            data={"msg": "hello all"},
        )
        assert count == 2

        msg1 = q1.get_nowait()
        msg2 = q2.get_nowait()
        assert "event: test:broadcast\n" in msg1
        assert '"msg": "hello all"' in msg1
        assert msg1 == msg2

    def test_publish_event_role_filtering(self, clean_sse_manager: SSEManager) -> None:
        """Targeting target_roles delivers only to subscribers with matching roles."""
        q_admin = clean_sse_manager.subscribe(user_id=1, role="ADMIN")
        q_instructor = clean_sse_manager.subscribe(user_id=2, role="INSTRUCTOR")
        q_student = clean_sse_manager.subscribe(user_id=3, role="STUDENT")

        count = clean_sse_manager.publish_event(
            event_type="changeset:submitted",
            data={"course_code": "CS101"},
            target_roles=["ADMIN"],
        )
        assert count == 1
        assert not q_admin.empty()
        assert q_instructor.empty()
        assert q_student.empty()

        admin_msg = q_admin.get_nowait()
        assert "event: changeset:submitted\n" in admin_msg
        assert '"course_code": "CS101"' in admin_msg

    def test_publish_event_user_id_filtering(self, clean_sse_manager: SSEManager) -> None:
        """Targeting target_user_ids delivers only to exact matching user IDs."""
        q_user1 = clean_sse_manager.subscribe(user_id=42, role="STUDENT")
        q_user2 = clean_sse_manager.subscribe(user_id=99, role="STUDENT")

        count = clean_sse_manager.publish_event(
            event_type="notification:new",
            data={"id": 100, "title": "Welcome"},
            target_user_ids=[42],
        )
        assert count == 1
        assert not q_user1.empty()
        assert q_user2.empty()

        msg = q_user1.get_nowait()
        assert "event: notification:new\n" in msg
        assert '"title": "Welcome"' in msg

    def test_stream_events_generator_lifecycle(self, clean_sse_manager: SSEManager) -> None:
        """Generator yields initial connected event, incoming message, and cleans up on exit."""
        gen = clean_sse_manager.stream_events(user_id=5, role="ADMIN", timeout=0.1)

        first_frame = next(gen)
        assert first_frame.startswith("event: connected\ndata: ")
        assert '"status": "connected"' in first_frame
        assert '"user_id": 5' in first_frame

        clean_sse_manager.publish_event("test:event", {"value": 123}, target_user_ids=[5])
        second_frame = next(gen)
        assert second_frame.startswith("event: test:event\ndata: ")
        assert '"value": 123' in second_frame

        # Heartbeat ping on timeout
        third_frame = next(gen)
        assert third_frame.startswith("event: ping\ndata: ")
        assert '"time":' in third_frame

        gen.close()
        assert clean_sse_manager.active_subscribers_count() == 0

    def test_emit_domain_event_safety(self) -> None:
        """emit_domain_event never raises exceptions even when SSE manager encounters errors."""
        with patch.object(
            get_sse_manager(), "publish_event", side_effect=RuntimeError("queue error")
        ):
            emit_domain_event("course:test", {"data": "test"})


# ==============================================================================
# 2. SSE HTTP Endpoints (/api/events/stream & /auth/events/stream)
# ==============================================================================


class TestSSEEndpoints:
    """HTTP integration tests for SSE stream endpoints."""

    def test_sse_stream_unauthenticated_fails(self, client: FlaskClient) -> None:
        """Unauthenticated requests to /api/events/stream and /auth/events/stream return 401."""
        res_api = client.get("/api/events/stream")
        assert res_api.status_code == 401
        data_api = res_api.get_json()
        assert data_api["error"]["code"] == "UNAUTHORIZED"

        res_auth = client.get("/auth/events/stream")
        assert res_auth.status_code == 401
        data_auth = res_auth.get_json()
        assert data_auth["error"]["code"] == "UNAUTHORIZED"

    def test_sse_stream_session_authenticated(
        self, client: FlaskClient, app: Flask, seeded_users: dict[str, int]
    ) -> None:
        """Session-authenticated user connects to /auth/events/stream with proper headers."""
        with app.app_context():
            admin = db.session.get(User, seeded_users["admin_id"])
            login_web_user(client, admin)

        res = client.get("/auth/events/stream")
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("Content-Type", "")
        assert "no-cache" in res.headers.get("Cache-Control", "")
        assert res.headers.get("X-Accel-Buffering") == "no"

        # Check initial connected frame in stream
        first_chunk = next(res.response)
        assert isinstance(first_chunk, (str, bytes))
        chunk_str = first_chunk.decode() if isinstance(first_chunk, bytes) else first_chunk
        assert "event: connected" in chunk_str
        assert "connected" in chunk_str

    def test_sse_stream_api_session_authenticated(
        self, client: FlaskClient, app: Flask, seeded_users: dict[str, int]
    ) -> None:
        """Session-authenticated user can also stream from /api/events/stream."""
        with app.app_context():
            instructor = db.session.get(User, seeded_users["instructor_id"])
            login_web_user(client, instructor)

        res = client.get("/api/events/stream")
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("Content-Type", "")

        first_chunk = next(res.response)
        chunk_str = first_chunk.decode() if isinstance(first_chunk, bytes) else first_chunk
        assert "event: connected" in chunk_str

    def test_sse_stream_jwt_bearer_authenticated(
        self, client: FlaskClient, app: Flask, seeded_users: dict[str, int]
    ) -> None:
        """REST client authenticated with Bearer JWT connects successfully to /api/events/stream."""
        with app.app_context():
            admin = db.session.get(User, seeded_users["admin_id"])
            token = create_token_pair(admin)["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/events/stream", headers=headers)
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("Content-Type", "")

        first_chunk = next(res.response)
        chunk_str = first_chunk.decode() if isinstance(first_chunk, bytes) else first_chunk
        assert "event: connected" in chunk_str

    def test_sse_stream_query_token_authenticated(
        self, client: FlaskClient, app: Flask, seeded_users: dict[str, int]
    ) -> None:
        """Browser EventSource supplying ?token= query parameter connects successfully."""
        with app.app_context():
            instructor = db.session.get(User, seeded_users["instructor_id"])
            token = create_token_pair(instructor)["access_token"]

        res = client.get(f"/api/events/stream?token={token}")
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("Content-Type", "")


# ==============================================================================
# 3. Domain Event Hooks in CRUD Mutations
# ==============================================================================


class TestDomainEventHooks:
    """Verify that service operations trigger expected domain events."""

    def test_course_events_hooked(
        self, app: Flask, seeded_users: dict[str, int]
    ) -> None:
        """create_course, update_course, publish_course, trash_course emit domain events."""
        with app.app_context():
            instructor = db.session.get(User, seeded_users["instructor_id"])
            admin = db.session.get(User, seeded_users["admin_id"])

            published_events: list[tuple[str, dict[str, Any]]] = []

            def fake_publish(event_type: str, data: Any, **kwargs: Any) -> int:
                published_events.append((event_type, data))
                return 1

            with patch.object(get_sse_manager(), "publish_event", side_effect=fake_publish):
                # 1. Create course -> course:created
                code_sfx = uuid.uuid4().hex[:6].upper()
                course = create_course(
                    actor=instructor,
                    data={
                        "course_code": f"SSE-{code_sfx}",
                        "title": f"SSE Realtime Course {code_sfx}",
                        "description": "Testing realtime events.",
                    },
                    session=db.session,
                )
                assert any(ev[0] == "course:created" for ev in published_events)

                # 2. Update course -> course:updated
                published_events.clear()
                update_course(
                    actor=instructor,
                    course_id=course.id,
                    data={"title": f"Updated SSE Course {code_sfx}"},
                    session=db.session,
                )
                assert any(ev[0] == "course:updated" for ev in published_events)

                # 3. Publish course -> course:published
                published_events.clear()
                create_lesson(
                    actor=instructor,
                    course_id=course.id,
                    data={
                        "title": "Intro Lesson",
                        "lesson_type": "TEXT",
                        "markdown_content": "Content",
                    },
                    session=db.session,
                )
                course.status = "APPROVED"
                db.session.commit()

                publish_course(
                    actor=admin,
                    course_id=course.id,
                    session=db.session,
                )
                assert any(ev[0] == "course:published" for ev in published_events)

                # 4. Trash course -> course:trashed
                published_events.clear()
                trash_course(
                    actor=admin,
                    course_id=course.id,
                    reason="Cleanup after test",
                    session=db.session,
                )
                assert any(ev[0] == "course:trashed" for ev in published_events)

    def test_notification_events_hooked(
        self, app: Flask, seeded_users: dict[str, int]
    ) -> None:
        """dispatch_notification and broadcast_system_notification emit domain events."""
        with app.app_context():
            instructor = db.session.get(User, seeded_users["instructor_id"])
            admin = db.session.get(User, seeded_users["admin_id"])

            published_events: list[tuple[str, dict[str, Any]]] = []

            def fake_publish(event_type: str, data: Any, **kwargs: Any) -> int:
                published_events.append((event_type, data))
                return 1

            with patch.object(get_sse_manager(), "publish_event", side_effect=fake_publish):
                # 1. Dispatch individual notification -> notification:new
                dispatch_notification(
                    recipient_user=instructor,
                    event_type="SYSTEM_ALERT",
                    title="Realtime Alert",
                    body="This is a test notification.",
                    session=db.session,
                )
                assert any(ev[0] == "notification:new" for ev in published_events)

                # 2. Broadcast system notification -> notification:broadcast
                published_events.clear()
                broadcast_system_notification(
                    actor=admin,
                    title="System Broadcast",
                    body="Maintenance scheduled tonight.",
                    session=db.session,
                )
                assert any(ev[0] == "notification:broadcast" for ev in published_events)

    def test_changeset_events_hooked(
        self, client: FlaskClient, app: Flask, seeded_users: dict[str, int]
    ) -> None:
        """Submitting, retracting, and discarding changesets emit proper SSE domain events."""
        with app.app_context():
            instructor = db.session.get(User, seeded_users["instructor_id"])
            sfx = uuid.uuid4().hex[:6].upper()
            c = create_course(
                actor=instructor,
                data={
                    "course_code": f"CHG-{sfx}",
                    "title": f"Changeset Course {sfx}",
                    "description": "Test changeset events",
                },
                session=db.session,
            )
            l1 = create_lesson(
                actor=instructor,
                course_id=c.id,
                data={"title": "Lesson 1", "lesson_type": "TEXT", "markdown_content": "Content"},
                session=db.session,
            )
            c.status = "PUBLISHED"
            l1.status = "PUBLISHED"
            db.session.commit()
            cid = str(c.public_id)

        published_events: list[tuple[str, dict[str, Any], Any]] = []

        def fake_publish(event_type: str, data: Any, **kwargs: Any) -> int:
            published_events.append((event_type, data, kwargs))
            return 1

        with patch.object(get_sse_manager(), "publish_event", side_effect=fake_publish):
            with app.app_context():
                instructor = db.session.get(User, seeded_users["instructor_id"])
                login_web_user(client, instructor)

            # 1. Submit changeset
            payload = {
                "version_title": "Đợt cập nhật v1",
                "summary": "Thêm nội dung",
                "course_metadata": {"description": "Updated description for changeset test"},
            }
            resp_sub = client.post(f"/instructor/courses/{cid}/changeset/submit", json=payload)
            assert resp_sub.status_code in (200, 201, 202)
            assert any(ev[0] == "changeset:submitted" for ev in published_events)
            sub_ev = [ev for ev in published_events if ev[0] == "changeset:submitted"][0]
            assert sub_ev[2].get("target_roles") == ["ADMIN"]

            # 2. Retract changeset
            published_events.clear()
            resp_retract = client.post(f"/instructor/courses/{cid}/changeset/retract")
            assert resp_retract.status_code == 200
            assert any(ev[0] == "changeset:retracted" for ev in published_events)

            # 3. Discard working changeset
            published_events.clear()
            resp_discard = client.post(f"/instructor/courses/{cid}/changeset/discard")
            assert resp_discard.status_code == 200
            assert any(ev[0] == "changeset:discarded" for ev in published_events)


# ==============================================================================
# 4. Symmetrical DELETE Endpoints for Courses
# ==============================================================================


class TestCourseDeleteRoutes:
    """Verify HTTP DELETE /courses/<course_id> on both Instructor and Admin routes."""

    def test_instructor_delete_course_route(
        self, client: FlaskClient, app: Flask, seeded_users: dict[str, int]
    ) -> None:
        """Instructor can DELETE /instructor/courses/<course_id>."""
        with app.app_context():
            instructor = db.session.get(User, seeded_users["instructor_id"])
            code_sfx = uuid.uuid4().hex[:6].upper()
            course = create_course(
                actor=instructor,
                data={
                    "course_code": f"DEL-{code_sfx}",
                    "title": f"Course to Delete {code_sfx}",
                },
                session=db.session,
            )
            course_id = str(course.public_id)

        with app.app_context():
            instructor = db.session.get(User, seeded_users["instructor_id"])
            login_web_user(client, instructor)

        res = client.delete(
            f"/instructor/courses/{course_id}",
            json={"reason": "Instructor decided to remove"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["status"] == "TRASH"

    def test_admin_delete_course_route(
        self, client: FlaskClient, app: Flask, seeded_users: dict[str, int]
    ) -> None:
        """Admin can DELETE /admin/courses/<course_id>."""
        with app.app_context():
            instructor = db.session.get(User, seeded_users["instructor_id"])
            code_sfx = uuid.uuid4().hex[:6].upper()
            course = create_course(
                actor=instructor,
                data={
                    "course_code": f"ADM-DEL-{code_sfx}",
                    "title": f"Course for Admin Delete {code_sfx}",
                },
                session=db.session,
            )
            course_id = str(course.public_id)

        with app.app_context():
            admin = db.session.get(User, seeded_users["admin_id"])
            login_web_user(client, admin)

        res = client.delete(
            f"/admin/courses/{course_id}",
            json={"reason": "Administrative removal"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "TRASH"


# ==============================================================================
# 5. Admin Courses Filtering (exclude_draft)
# ==============================================================================


class TestAdminCoursesFiltering:
    """Verify Admin courses listing supports exclude_draft=true."""

    def test_admin_courses_excludes_draft_when_requested(
        self, client: FlaskClient, app: Flask, seeded_users: dict[str, int]
    ) -> None:
        """exclude_draft=true filters out DRAFT courses from Admin list."""
        with app.app_context():
            instructor = db.session.get(User, seeded_users["instructor_id"])
            sfx = uuid.uuid4().hex[:6].upper()

            draft_course = create_course(
                actor=instructor,
                data={"course_code": f"DRF-{sfx}", "title": f"Draft Course {sfx}"},
                session=db.session,
            )
            draft_id = str(draft_course.public_id)

            pub_course = create_course(
                actor=instructor,
                data={"course_code": f"PUB-{sfx}", "title": f"Published Course {sfx}"},
                session=db.session,
            )
            pub_course.status = "PUBLISHED"
            pub_course.published_at = utc_now()
            db.session.commit()
            pub_id = str(pub_course.public_id)

        with app.app_context():
            admin = db.session.get(User, seeded_users["admin_id"])
            login_web_user(client, admin)

        # 1. Without exclude_draft: both courses returned
        res_all = client.get("/admin/courses")
        assert res_all.status_code == 200
        course_ids_all = [c["course_id"] for c in res_all.get_json()["courses"]]
        assert draft_id in course_ids_all
        assert pub_id in course_ids_all

        # 2. With exclude_draft=true: only published course returned
        res_filtered = client.get("/admin/courses?exclude_draft=true")
        assert res_filtered.status_code == 200
        course_ids_filtered = [c["course_id"] for c in res_filtered.get_json()["courses"]]
        assert pub_id in course_ids_filtered
        assert draft_id not in course_ids_filtered
