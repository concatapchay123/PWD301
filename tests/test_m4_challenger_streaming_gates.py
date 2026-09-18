"""Adversarial challenge test suite for Milestone 4: Streaming & Access Gate Security.

Challenger: challenger_m4_2 (Empirical Challenger)
Focus:
1. Video Range Streaming (HTTP 206 Partial Content, Range: bytes=0-100,
   disposition=inline, exactly 101 bytes).
2. Fail-Closed Security & Access Gates:
   - Enrolled student accessing resource on a DRAFT lesson -> MUST return 403 Forbidden.
   - Enrolled student accessing resource on a PUBLISHED lesson in an UNPUBLISHED course
     -> MUST return 403 Forbidden.
   - UNENROLLED student accessing resource on a PUBLISHED lesson -> MUST return 403 Forbidden.
   - Student accessing a QUARANTINED or INFECTED file -> MUST return 403 Forbidden
     (Invariant 18 / ADR-008).
   - Foreign instructor attempting to attach/detach resources to another instructor's course
     -> MUST return 403 Forbidden.
3. Edge cases:
   - Boundary range requests (mid-range, suffix range, unsatisfiable range).
   - Security gate preservation under Range requests (Range request must NOT bypass 403).
   - Student with LEFT enrollment status accessing resources -> 403 Forbidden.
   - Cross-course URL tampering attempts -> 403 (unenrolled) or 404 (mismatched course).
"""

from __future__ import annotations

import io
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.file_import import FileAsset
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.file_service import (
    attach_resource_to_lesson,
    store_file_stream,
)
from pwd301.services.lesson_service import change_lesson_status, create_lesson
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist."""
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
def instructor_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Primary instructor owning the course."""
    u = register_user("chal_inst_a@example.com", "Password@123", "Instructor A")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Foreign instructor with no permissions on Instructor A's course."""
    u = register_user("chal_inst_b@example.com", "Password@123", "Instructor B")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_enrolled(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Enrolled student user."""
    return register_user("chal_student_enrolled@example.com", "Password@123", "Enrolled Student")


@pytest.fixture
def student_unenrolled(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Unenrolled student user."""
    return register_user(
        "chal_student_unenrolled@example.com", "Password@123", "Unenrolled Student"
    )


@pytest.fixture
def published_course(app: Flask, instructor_a: User) -> Course:
    """A published course managed by instructor_a."""
    c = create_course(
        instructor_a,
        {
            "course_code": f"CHAL-{uuid.uuid4().hex[:4].upper()}",
            "title": "Challenger Testing Course",
            "category": "Web Security",
            "difficulty": "INTERMEDIATE",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


@pytest.fixture
def video_asset(
    app: Flask, instructor_a: User, published_course: Course
) -> tuple[FileAsset, bytes]:
    """Store a 5000-byte synthetic MP4 video asset."""
    payload = b"\x00\x00\x00\x20ftypisom" + bytes([i % 256 for i in range(4988)])
    assert len(payload) == 5000
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.id,
        file_stream=io.BytesIO(payload),
        filename="lecture_5000.mp4",
        content_type="video/mp4",
        asset_type="RESOURCE",
        title="5000 Byte Lecture Video",
        session=db.session,
    )
    db.session.commit()
    return asset, payload


class TestVideoRangeStreaming:
    """Empirical challenge for HTTP 206 Partial Content video streaming."""

    def test_video_streaming_range_0_100_inline(
        self,
        client: FlaskClient,
        instructor_a: User,
        student_enrolled: User,
        published_course: Course,
        video_asset: tuple[FileAsset, bytes],
    ) -> None:
        """Requirement 1: Send GET Range: bytes=0-100 to student download URL.

        Must respond with HTTP 206, Content-Range header, and exactly 101 bytes.
        """
        asset, payload = video_asset

        lesson = create_lesson(
            instructor_a,
            published_course.id,
            {"title": "Streaming Lecture", "markdown_content": "# Video Lecture"},
        )
        attach_resource_to_lesson(
            actor=instructor_a,
            lesson_id=lesson.id,
            asset_id=asset.id,
            session=db.session,
        )
        change_lesson_status(instructor_a, lesson.id, "PUBLISHED", session=db.session)

        enroll_student(student_enrolled, published_course.id, session=db.session)
        db.session.commit()

        login_web_user(client, student_enrolled)

        url = (
            f"/student/courses/{published_course.public_id}"
            f"/files/{asset.public_id}/download?disposition=inline"
        )
        response = client.get(url, headers={"Range": "bytes=0-100"})

        assert response.status_code == 206, f"Expected 206, got {response.status_code}"
        assert len(response.data) == 101, f"Expected 101 bytes, got {len(response.data)}"
        assert response.data == payload[0:101], "Returned bytes do not match expected slice"

        content_range = response.headers.get("Content-Range")
        assert content_range is not None, "Missing Content-Range header"
        assert content_range == "bytes 0-100/5000", f"Unexpected Content-Range: {content_range}"

        assert response.mimetype == "video/mp4"
        cd = response.headers.get("Content-Disposition", "")
        assert "attachment" not in cd.lower(), f"Unexpected attachment disposition: {cd}"

    def test_video_streaming_mid_range_and_suffix_range(
        self,
        client: FlaskClient,
        instructor_a: User,
        student_enrolled: User,
        published_course: Course,
        video_asset: tuple[FileAsset, bytes],
    ) -> None:
        """Challenge mid-range (bytes=500-999) and suffix range (bytes=-200)."""
        asset, payload = video_asset

        lesson = create_lesson(
            instructor_a,
            published_course.id,
            {"title": "Range Lecture", "markdown_content": "# Range"},
        )
        attach_resource_to_lesson(
            actor=instructor_a,
            lesson_id=lesson.id,
            asset_id=asset.id,
            session=db.session,
        )
        change_lesson_status(instructor_a, lesson.id, "PUBLISHED", session=db.session)

        enroll_student(student_enrolled, published_course.id, session=db.session)
        db.session.commit()

        login_web_user(client, student_enrolled)
        url = (
            f"/student/courses/{published_course.public_id}"
            f"/files/{asset.public_id}/download?disposition=inline"
        )

        # 1. Mid-stream range: bytes=500-999 (500 bytes)
        resp_mid = client.get(url, headers={"Range": "bytes=500-999"})
        assert resp_mid.status_code == 206
        assert len(resp_mid.data) == 500
        assert resp_mid.data == payload[500:1000]
        assert resp_mid.headers.get("Content-Range") == "bytes 500-999/5000"

        # 2. Suffix range: bytes=-200 (last 200 bytes: 4800-4999)
        resp_suffix = client.get(url, headers={"Range": "bytes=-200"})
        assert resp_suffix.status_code == 206
        assert len(resp_suffix.data) == 200
        assert resp_suffix.data == payload[4800:5000]
        assert resp_suffix.headers.get("Content-Range") == "bytes 4800-4999/5000"

    def test_video_streaming_unsatisfiable_range_returns_416(
        self,
        client: FlaskClient,
        instructor_a: User,
        student_enrolled: User,
        published_course: Course,
        video_asset: tuple[FileAsset, bytes],
    ) -> None:
        """Challenge range beyond file size: bytes=6000-7000 must return HTTP 416."""
        asset, _ = video_asset

        lesson = create_lesson(
            instructor_a,
            published_course.id,
            {"title": "Unsatisfiable Range Lecture", "markdown_content": "# Range 416"},
        )
        attach_resource_to_lesson(
            actor=instructor_a,
            lesson_id=lesson.id,
            asset_id=asset.id,
            session=db.session,
        )
        change_lesson_status(instructor_a, lesson.id, "PUBLISHED", session=db.session)

        enroll_student(student_enrolled, published_course.id, session=db.session)
        db.session.commit()

        login_web_user(client, student_enrolled)
        url = (
            f"/student/courses/{published_course.public_id}"
            f"/files/{asset.public_id}/download?disposition=inline"
        )

        resp = client.get(url, headers={"Range": "bytes=6000-7000"})
        assert resp.status_code == 416, f"Expected 416, got {resp.status_code}"


class TestFailClosedAccessGates:
    """Empirical challenge for fail-closed security and access gates."""

    def test_enrolled_student_accessing_draft_lesson_resource_returns_403(
        self,
        client: FlaskClient,
        instructor_a: User,
        student_enrolled: User,
        published_course: Course,
    ) -> None:
        """Gate 1: Enrolled student accessing resource on a DRAFT lesson -> 403."""
        asset = store_file_stream(
            actor=instructor_a,
            course_id=published_course.id,
            file_stream=io.BytesIO(b"Confidential draft lesson content"),
            filename="draft_exam_solutions.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Draft Exam Solutions",
            session=db.session,
        )
        draft_lesson = create_lesson(
            instructor_a,
            published_course.id,
            {"title": "Unreleased Draft Lesson", "markdown_content": "# Draft Content"},
        )
        assert draft_lesson.status == "DRAFT"

        attach_resource_to_lesson(
            actor=instructor_a,
            lesson_id=draft_lesson.id,
            asset_id=asset.id,
            session=db.session,
        )

        enroll_student(student_enrolled, published_course.id, session=db.session)
        db.session.commit()

        login_web_user(client, student_enrolled)
        url = f"/student/courses/{published_course.public_id}/files/{asset.public_id}/download"

        # 1. Standard download request -> 403 Forbidden
        resp_std = client.get(url)
        assert resp_std.status_code == 403, (
            f"Expected 403 Forbidden on draft resource, got {resp_std.status_code}"
        )

        # 2. Inline streaming request with Range header -> MUST NOT bypass 403
        resp_range = client.get(f"{url}?disposition=inline", headers={"Range": "bytes=0-10"})
        assert resp_range.status_code == 403, (
            f"Expected 403 Forbidden on Range draft resource, got {resp_range.status_code}"
        )

    def test_enrolled_student_accessing_published_lesson_in_unpublished_course_returns_403(
        self,
        client: FlaskClient,
        instructor_a: User,
        student_enrolled: User,
    ) -> None:
        """Gate 2: Enrolled student accessing resource on unpublished course -> 403."""
        course = create_course(
            instructor_a,
            {
                "course_code": f"UNPUB-{uuid.uuid4().hex[:4].upper()}",
                "title": "Course To Be Unpublished",
                "category": "CS",
            },
        )
        course.status = "PUBLISHED"
        db.session.commit()

        enroll_student(student_enrolled, course.id, session=db.session)

        asset = store_file_stream(
            actor=instructor_a,
            course_id=course.id,
            file_stream=io.BytesIO(b"Notes for unpublished course"),
            filename="lecture_notes.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Lecture Notes",
            session=db.session,
        )
        lesson = create_lesson(
            instructor_a,
            course.id,
            {"title": "Published Lesson in Unpub Course", "markdown_content": "# Lesson"},
        )
        attach_resource_to_lesson(
            actor=instructor_a,
            lesson_id=lesson.id,
            asset_id=asset.id,
            session=db.session,
        )
        change_lesson_status(instructor_a, lesson.id, "PUBLISHED", session=db.session)

        # Unpublish course
        course.status = "DRAFT"
        db.session.commit()

        login_web_user(client, student_enrolled)
        url = f"/student/courses/{course.public_id}/files/{asset.public_id}/download"

        resp = client.get(url)
        assert resp.status_code == 403, (
            f"Expected 403 on unpublished course, got {resp.status_code}"
        )

        resp_range = client.get(f"{url}?disposition=inline", headers={"Range": "bytes=0-10"})
        assert resp_range.status_code == 403, (
            f"Expected 403 on unpublished course with Range, got {resp_range.status_code}"
        )

    def test_unenrolled_student_accessing_published_lesson_returns_403(
        self,
        client: FlaskClient,
        instructor_a: User,
        student_unenrolled: User,
        published_course: Course,
    ) -> None:
        """Gate 3: UNENROLLED student accessing resource on a PUBLISHED lesson -> 403."""
        asset = store_file_stream(
            actor=instructor_a,
            course_id=published_course.id,
            file_stream=io.BytesIO(b"Resource for enrolled only"),
            filename="syllabus.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Course Syllabus",
            session=db.session,
        )
        lesson = create_lesson(
            instructor_a,
            published_course.id,
            {"title": "Published Lesson", "markdown_content": "# Published Content"},
        )
        attach_resource_to_lesson(
            actor=instructor_a,
            lesson_id=lesson.id,
            asset_id=asset.id,
            session=db.session,
        )
        change_lesson_status(instructor_a, lesson.id, "PUBLISHED", session=db.session)
        db.session.commit()

        login_web_user(client, student_unenrolled)
        url = f"/student/courses/{published_course.public_id}/files/{asset.public_id}/download"

        resp = client.get(url)
        assert resp.status_code == 403, (
            f"Expected 403 Forbidden for unenrolled student, got {resp.status_code}"
        )

        resp_range = client.get(f"{url}?disposition=inline", headers={"Range": "bytes=0-5"})
        assert resp_range.status_code == 403, (
            f"Expected 403 for unenrolled student with Range, got {resp_range.status_code}"
        )

    def test_student_with_left_enrollment_returns_403(
        self,
        client: FlaskClient,
        instructor_a: User,
        student_enrolled: User,
        published_course: Course,
    ) -> None:
        """Gate 3 Edge: Student whose enrollment was LEFT -> MUST return 403 Forbidden."""
        asset = store_file_stream(
            actor=instructor_a,
            course_id=published_course.id,
            file_stream=io.BytesIO(b"Active students only"),
            filename="bonus.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            session=db.session,
        )
        lesson = create_lesson(
            instructor_a,
            published_course.id,
            {"title": "Bonus Lesson", "markdown_content": "# Bonus"},
        )
        attach_resource_to_lesson(
            actor=instructor_a,
            lesson_id=lesson.id,
            asset_id=asset.id,
            session=db.session,
        )
        change_lesson_status(instructor_a, lesson.id, "PUBLISHED", session=db.session)

        enr = enroll_student(student_enrolled, published_course.id, session=db.session)
        enr.status = "LEFT"
        db.session.commit()

        login_web_user(client, student_enrolled)
        url = f"/student/courses/{published_course.public_id}/files/{asset.public_id}/download"
        resp = client.get(url)
        assert resp.status_code == 403, (
            f"Expected 403 Forbidden for left student, got {resp.status_code}"
        )

    def test_student_accessing_quarantined_or_infected_file_returns_403(
        self,
        client: FlaskClient,
        instructor_a: User,
        student_enrolled: User,
        published_course: Course,
    ) -> None:
        """Gate 4: Student accessing QUARANTINED or INFECTED file -> 403 (ADR-008)."""
        enroll_student(student_enrolled, published_course.id, session=db.session)

        lesson = create_lesson(
            instructor_a,
            published_course.id,
            {"title": "Security Gate Lesson", "markdown_content": "# Security"},
        )
        change_lesson_status(instructor_a, lesson.id, "PUBLISHED", session=db.session)

        # 1. Quarantined file
        asset_q = store_file_stream(
            actor=instructor_a,
            course_id=published_course.id,
            file_stream=io.BytesIO(b"Potentially dangerous quarantined content"),
            filename="quarantined_attachment.bin",
            content_type="application/octet-stream",
            asset_type="RESOURCE",
            session=db.session,
        )
        attach_resource_to_lesson(
            actor=instructor_a,
            lesson_id=lesson.id,
            asset_id=asset_q.id,
            session=db.session,
        )
        rev_q = asset_q.current_revision
        assert rev_q is not None
        rev_q.status = "QUARANTINED"
        db.session.commit()

        # 2. Infected file
        asset_inf = store_file_stream(
            actor=instructor_a,
            course_id=published_course.id,
            file_stream=io.BytesIO(b"Malware infected payload"),
            filename="infected_trojan.bin",
            content_type="application/octet-stream",
            asset_type="RESOURCE",
            session=db.session,
        )
        attach_resource_to_lesson(
            actor=instructor_a,
            lesson_id=lesson.id,
            asset_id=asset_inf.id,
            session=db.session,
        )
        rev_inf = asset_inf.current_revision
        assert rev_inf is not None
        rev_inf.status = "REJECTED"
        db.session.commit()

        login_web_user(client, student_enrolled)

        # Quarantined download attempt
        url_q = f"/student/courses/{published_course.public_id}/files/{asset_q.public_id}/download"
        resp_q = client.get(url_q)
        assert resp_q.status_code == 403, (
            f"Expected 403 Forbidden for QUARANTINED file, got {resp_q.status_code}"
        )

        resp_q_range = client.get(f"{url_q}?disposition=inline", headers={"Range": "bytes=0-10"})
        assert resp_q_range.status_code == 403, (
            f"Expected 403 on Range for QUARANTINED file, got {resp_q_range.status_code}"
        )

        # Infected download attempt
        url_inf = (
            f"/student/courses/{published_course.public_id}/files/{asset_inf.public_id}/download"
        )
        resp_inf = client.get(url_inf)
        assert resp_inf.status_code == 403, (
            f"Expected 403 Forbidden for INFECTED file, got {resp_inf.status_code}"
        )

        resp_inf_range = client.get(
            f"{url_inf}?disposition=inline", headers={"Range": "bytes=0-10"}
        )
        assert resp_inf_range.status_code == 403, (
            f"Expected 403 on Range for INFECTED file, got {resp_inf_range.status_code}"
        )

    def test_foreign_instructor_cannot_attach_or_detach_resources_returns_403(
        self,
        client: FlaskClient,
        instructor_a: User,
        instructor_b: User,
        published_course: Course,
    ) -> None:
        """Gate 5: Foreign instructor attempting attach/detach -> MUST return 403."""
        legit_asset = store_file_stream(
            actor=instructor_a,
            course_id=published_course.id,
            file_stream=io.BytesIO(b"Legitimate instructor resource"),
            filename="legit_lecture.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Legitimate Resource",
            session=db.session,
        )
        lesson = create_lesson(
            instructor_a,
            published_course.id,
            {"title": "Target Lesson", "markdown_content": "# Lesson Content"},
        )
        res_link = attach_resource_to_lesson(
            actor=instructor_a,
            lesson_id=lesson.id,
            asset_id=legit_asset.id,
            session=db.session,
        )
        db.session.commit()

        login_web_user(client, instructor_b)

        # 1. Foreign instructor attach attempt -> 403
        attach_url = (
            f"/instructor/courses/{published_course.public_id}/lessons/{lesson.public_id}/resources"
        )
        attach_resp = client.post(
            attach_url,
            data={
                "file": (io.BytesIO(b"Hostile injected resource"), "malicious.pdf"),
                "label": "Hostile File",
            },
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert attach_resp.status_code == 403, (
            f"Expected 403 on unauthorized attach, got {attach_resp.status_code}"
        )

        # 2. Foreign instructor detach attempt -> 403
        detach_url = (
            f"/instructor/courses/{published_course.public_id}"
            f"/lessons/{lesson.public_id}/resources/{res_link.public_id}/delete"
        )
        detach_resp = client.post(
            detach_url,
            headers={"Accept": "application/json"},
        )
        assert detach_resp.status_code == 403, (
            f"Expected 403 on unauthorized detach, got {detach_resp.status_code}"
        )

        # 3. Verify integrity: Resource is still attached to the lesson
        db.session.expire_all()
        reloaded_lesson = db.session.get(Lesson, lesson.id)
        assert reloaded_lesson is not None
        assert len(reloaded_lesson.resources) == 1, "Foreign instructor corrupted lesson resources!"
        assert reloaded_lesson.resources[0].id == res_link.id, "Resource was detached or modified!"

    def test_unauthenticated_user_cannot_stream_or_download_video(
        self,
        client: FlaskClient,
        published_course: Course,
        video_asset: tuple[FileAsset, bytes],
    ) -> None:
        """Anonymous / unauthenticated user must NOT be able to stream or download resources."""
        asset, _ = video_asset
        url = (
            f"/student/courses/{published_course.public_id}"
            f"/files/{asset.public_id}/download?disposition=inline"
        )
        resp = client.get(url, headers={"Range": "bytes=0-100"})
        assert resp.status_code in (302, 401, 403), (
            f"Expected 302/401/403 for anonymous streaming, got {resp.status_code}"
        )
        assert len(resp.data) != 101, "Data leaked to unauthenticated user!"

    def test_cross_course_tampering_download_returns_403_or_404(
        self,
        client: FlaskClient,
        instructor_a: User,
        student_enrolled: User,
        published_course: Course,
    ) -> None:
        """Cross-course tampering:

        1. If unenrolled in Course B, accessing Course B asset via Course A URL -> 403.
        2. If enrolled in both, accessing Course B asset via Course A URL -> 404.
        """
        course_b = create_course(
            instructor_a,
            {
                "course_code": f"CRSB-{uuid.uuid4().hex[:4].upper()}",
                "title": "Course B",
                "category": "CS",
            },
        )
        course_b.status = "PUBLISHED"
        db.session.commit()

        asset_b = store_file_stream(
            actor=instructor_a,
            course_id=course_b.id,
            file_stream=io.BytesIO(b"Asset belonging to course B"),
            filename="course_b.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            session=db.session,
        )
        db.session.commit()

        # Enroll in Course A only
        enroll_student(student_enrolled, published_course.id, session=db.session)
        db.session.commit()

        login_web_user(client, student_enrolled)

        # 1. Accessing Course B asset via Course A URL without enrollment in B -> 403
        tamper_url = (
            f"/student/courses/{published_course.public_id}/files/{asset_b.public_id}/download"
        )
        resp1 = client.get(tamper_url)
        assert resp1.status_code == 403, (
            f"Expected 403 Forbidden when unenrolled in B, got {resp1.status_code}"
        )

        # 2. Now also enroll in Course B, but request via Course A's URL -> 404
        enroll_student(student_enrolled, course_b.id, session=db.session)
        db.session.commit()

        resp2 = client.get(tamper_url)
        assert resp2.status_code == 404, (
            f"Expected 404 Not Found for mismatched course URL, got {resp2.status_code}"
        )
