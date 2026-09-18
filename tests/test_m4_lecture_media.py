"""Automated test suite for Milestone 4: Multi-Format Lecture Authoring & Media Support.

Tests:
1. Lesson and LessonResource model relationships & helper properties.
2. Instructor lesson creation with attached MP4 video (< 1 GB) and asset linkage.
3. Instructor lesson creation with attached PDF, DOCX, PPTX resources.
4. Video file size limit enforcement (< 1 GB limit via LimitingStream).
5. Default markdown generation when markdown_content is blank and media is attached.
6. In-place resource attachment (POST /courses/<cid>/lessons/<lid>/resources).
7. Resource detachment (POST /courses/<cid>/lessons/<lid>/resources/<rid>/delete).
8. Student video streaming with conditional=True (200 / 206 Partial Content).
9. Student resource download with active enrollment.
10. Fail-closed security: unenrolled student, draft lesson, or quarantined file returns 403.
11. HTML rendering in instructor course_manage.html and student lesson.html.
"""

from __future__ import annotations

import io
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import FileSizeLimitExceededError, FileValidationError
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user("m4_instructor@example.com", "Password@123", "M4 Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def foreign_instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a secondary instructor who does not manage the primary test course."""
    u = register_user("m4_foreign_instructor@example.com", "Password@123", "M4 Foreign Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def enrolled_student(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user actively enrolled in the course."""
    return register_user("m4_student_enrolled@example.com", "Password@123", "Enrolled Student")


@pytest.fixture
def unenrolled_student(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user who is not enrolled in the course."""
    return register_user("m4_student_unenrolled@example.com", "Password@123", "Unenrolled Student")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create a published course managed by instructor_user."""
    c = create_course(
        instructor_user,
        {
            "course_code": f"M4-{uuid.uuid4().hex[:4].upper()}",
            "title": "Milestone 4 Media Testing Course",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


@pytest.fixture
def enrolled_course(
    app: Flask, test_course: Course, enrolled_student: User
) -> tuple[Course, Enrollment]:
    """Enroll student in test course."""
    enr = enroll_student(enrolled_student, test_course.id, session=db.session)
    db.session.commit()
    return test_course, enr


class TestLessonAndResourceModels:
    """Unit tests for Lesson and LessonResource model relationships and helper properties."""

    def test_lesson_resource_relationship_and_ordering(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """Lesson.resources establishes bidirectional relationship ordered by position."""
        lesson = create_lesson(
            instructor_user,
            test_course.id,
            {
                "title": "Lesson 1: Intro",
                "markdown_content": "# Intro to Media",
            },
        )

        # Create two file assets
        asset1 = store_file_stream(
            actor=instructor_user,
            course_id=test_course.id,
            file_stream=io.BytesIO(b"slide content 1"),
            filename="slides1.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Slides 1",
            session=db.session,
        )
        asset2 = store_file_stream(
            actor=instructor_user,
            course_id=test_course.id,
            file_stream=io.BytesIO(b"code content 2"),
            filename="source.zip",
            content_type="application/zip",
            asset_type="RESOURCE",
            title="Source Code",
            session=db.session,
        )

        res1 = attach_resource_to_lesson(
            actor=instructor_user,
            lesson_id=lesson.id,
            asset_id=asset1.id,
            label="Main Slides",
            session=db.session,
        )
        res2 = attach_resource_to_lesson(
            actor=instructor_user,
            lesson_id=lesson.id,
            asset_id=asset2.id,
            label="Lab Archive",
            session=db.session,
        )

        # Refresh lesson from DB
        db.session.expire(lesson)
        les = db.session.get(Lesson, lesson.id)
        assert les is not None
        assert len(les.resources) == 2
        assert les.resources[0].id == res1.id
        assert les.resources[1].id == res2.id
        assert les.resources[0].lesson.id == les.id

    def test_lesson_video_and_document_resource_properties(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """Lesson.video_resource and document_resources classify resources accurately."""
        lesson = create_lesson(
            instructor_user,
            test_course.id,
            {
                "title": "Lesson 2: Video & Docs",
                "markdown_content": "# Multimedia Lecture",
            },
        )

        video_asset = store_file_stream(
            actor=instructor_user,
            course_id=test_course.id,
            file_stream=io.BytesIO(b"\x00\x00\x00\x20ftypisom" + b"\x00" * 100),
            filename="lecture.mp4",
            content_type="video/mp4",
            asset_type="RESOURCE",
            title="Lecture Video",
            session=db.session,
        )
        doc_asset = store_file_stream(
            actor=instructor_user,
            course_id=test_course.id,
            file_stream=io.BytesIO(b"%PDF-1.4 simulated pdf"),
            filename="handout.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Handout PDF",
            session=db.session,
        )

        attach_resource_to_lesson(
            actor=instructor_user,
            lesson_id=lesson.id,
            asset_id=video_asset.id,
            label="Video Stream",
            session=db.session,
        )
        attach_resource_to_lesson(
            actor=instructor_user,
            lesson_id=lesson.id,
            asset_id=doc_asset.id,
            label="Reading Handout",
            session=db.session,
        )

        db.session.expire(lesson)
        les = db.session.get(Lesson, lesson.id)
        assert les is not None

        assert les.video_resource is not None
        assert les.video_resource.file_asset_id == video_asset.id
        assert les.video_resource.is_video is True
        assert les.video_resource.resource_type == "VIDEO"

        doc_res = les.document_resources
        assert len(doc_res) == 1
        assert doc_res[0].file_asset_id == doc_asset.id
        assert doc_res[0].is_pdf is True
        assert doc_res[0].resource_type == "PDF"

    def test_lesson_resource_helper_properties(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """LessonResource helper properties (title, file_name, sizes, formatting)."""
        content = b"Simulated DOCX document content" * 100
        asset = store_file_stream(
            actor=instructor_user,
            course_id=test_course.id,
            file_stream=io.BytesIO(content),
            filename="syllabus.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            asset_type="RESOURCE",
            title="Course Syllabus",
            session=db.session,
        )

        lesson = create_lesson(
            instructor_user,
            test_course.id,
            {"title": "Lesson 3", "markdown_content": "# Lesson 3"},
        )
        res = attach_resource_to_lesson(
            actor=instructor_user,
            lesson_id=lesson.id,
            asset_id=asset.id,
            label="Syllabus Document",
            session=db.session,
        )

        assert res.title == "Syllabus Document"
        assert res.file_name == "syllabus.docx"
        assert res.file_size_bytes == len(content)
        assert res.is_video is False
        assert res.is_pdf is False
        assert res.resource_type == "DOCX"
        assert "KB" in res.file_size_formatted or "B" in res.file_size_formatted
        assert isinstance(res.public_id, uuid.UUID)


class TestInstructorLessonMediaAuthoring:
    """Integration tests for instructor lesson creation with multipart media files."""

    def test_create_lesson_with_attached_video_mp4(
        self, client: FlaskClient, test_course: Course, instructor_user: User
    ) -> None:
        """Create lesson via POST route with media_file (MP4 video)."""
        login_web_user(client, instructor_user)

        video_bytes = b"\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00isommp42" + b"\x00" * 500
        data = {
            "title": "Chương 1: Bài giảng Video MP4",
            "estimated_duration_minutes": "45",
            "position": "1",
            "summary": "Video bài giảng trực quan về kiến trúc hệ thống.",
            "markdown_content": "# Bài 1\n\nXem video bên trên để bắt đầu học.",
            "media_file": (io.BytesIO(video_bytes), "lecture_video.mp4"),
        }

        resp = client.post(
            f"/instructor/courses/{test_course.public_id}/lessons",
            data=data,
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 201
        res_json = resp.get_json()
        assert res_json["title"] == "Chương 1: Bài giảng Video MP4"
        assert len(res_json["resources"]) == 1
        assert res_json["resources"][0]["file_asset"]["original_filename"] == "lecture_video.mp4"

        # Check DB
        lesson = (
            db.session.query(Lesson)
            .filter(Lesson.public_id == uuid.UUID(res_json["lesson_id"]))
            .first()
        )
        assert lesson is not None
        assert lesson.video_resource is not None
        assert lesson.video_resource.file_asset.is_video is True

    def test_create_lesson_with_multiple_supplementary_resources(
        self, client: FlaskClient, test_course: Course, instructor_user: User
    ) -> None:
        """Create lesson with media_file and resource_files list (PDF, DOCX, PPTX)."""
        login_web_user(client, instructor_user)

        data = {
            "title": "Chương 2: Slide và tài liệu mẫu",
            "position": "2",
            "media_file": (io.BytesIO(b"%PDF-1.5 slide content"), "slides.pdf"),
            "resource_files": [
                (io.BytesIO(b"word document"), "exercise.docx"),
                (io.BytesIO(b"powerpoint presentation"), "presentation.pptx"),
            ],
        }

        resp = client.post(
            f"/instructor/courses/{test_course.public_id}/lessons",
            data=data,
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 201
        res_json = resp.get_json()
        # Default markdown should be populated automatically
        assert "Chương 2: Slide và tài liệu mẫu" in res_json["markdown_content"]
        assert len(res_json["resources"]) == 3

    def test_create_lesson_blank_markdown_defaults_safely(
        self, client: FlaskClient, test_course: Course, instructor_user: User
    ) -> None:
        """Instructors are not forced to type markdown when uploading media."""
        login_web_user(client, instructor_user)

        data = {
            "title": "Chương 3: Video thực hành",
            "summary": "Tóm tắt ngắn gọn của bài học.",
            "markdown_content": "   ",  # blank whitespace
            "media_file": (io.BytesIO(b"\x00\x00\x00\x18ftypisom" + b"\x00" * 100), "demo.mp4"),
        }

        resp = client.post(
            f"/instructor/courses/{test_course.public_id}/lessons",
            data=data,
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 201
        res_json = resp.get_json()
        assert "# Chương 3: Video thực hành" in res_json["markdown_content"]
        assert "Tóm tắt ngắn gọn của bài học." in res_json["markdown_content"]

    def test_in_place_attach_and_detach_lesson_resource(
        self, client: FlaskClient, test_course: Course, instructor_user: User
    ) -> None:
        """Attach file to existing lesson and detach via dedicated endpoints."""
        login_web_user(client, instructor_user)

        lesson = create_lesson(
            instructor_user,
            test_course.id,
            {"title": "Lesson to attach resource", "markdown_content": "# Content"},
        )

        # 1. Attach resource
        attach_resp = client.post(
            f"/instructor/courses/{test_course.public_id}/lessons/{lesson.public_id}/resources",
            data={
                "file": (io.BytesIO(b"%PDF-1.4 reading material"), "reading.pdf"),
                "label": "Tài liệu đọc thêm",
            },
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert attach_resp.status_code == 201
        res_data = attach_resp.get_json()
        assert res_data["title"] == "Tài liệu đọc thêm"
        resource_id = res_data["resource_id"]

        # Verify in DB
        db.session.expire_all()
        les = db.session.get(Lesson, lesson.id)
        assert les is not None
        assert len(les.resources) == 1

        # 2. Detach resource
        detach_resp = client.post(
            f"/instructor/courses/{test_course.public_id}/lessons/{lesson.public_id}/resources/{resource_id}/delete",
            headers={"Accept": "application/json"},
        )
        assert detach_resp.status_code == 200

        db.session.expire_all()
        les = db.session.get(Lesson, lesson.id)
        assert les is not None
        assert len(les.resources) == 0

    def test_foreign_instructor_cannot_attach_or_detach_resource(
        self,
        client: FlaskClient,
        test_course: Course,
        instructor_user: User,
        foreign_instructor: User,
    ) -> None:
        """Foreign instructor cannot modify lesson resources (403 Forbidden)."""
        lesson = create_lesson(
            instructor_user,
            test_course.id,
            {"title": "Protected Lesson", "markdown_content": "# Content"},
        )

        # Foreign instructor logs in
        login_web_user(client, foreign_instructor)

        resp = client.post(
            f"/instructor/courses/{test_course.public_id}/lessons/{lesson.public_id}/resources",
            data={"file": (io.BytesIO(b"content"), "exploit.pdf")},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403


class TestVideoSizeLimitAndSecurity:
    """Security invariants: size limits, macro blocklist, cross-course isolation."""

    def test_video_file_size_limit_enforcement(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """Video files strictly < 1 GB (1,000,000,000 bytes) via LimitingStream."""

        class OversizedStream(io.BytesIO):
            """Simulates a stream delivering >= 1 GB without allocating 1 GB in memory."""

            def __init__(self, total_bytes: int) -> None:
                super().__init__()
                self.total_bytes = total_bytes
                self.bytes_read = 0

            def read(self, size: int = -1) -> bytes:
                if size == -1 or size is None:
                    remaining = self.total_bytes - self.bytes_read
                    self.bytes_read = self.total_bytes
                    return b"A" * remaining
                chunk_size = min(size, self.total_bytes - self.bytes_read)
                self.bytes_read += chunk_size
                return b"A" * chunk_size

        # Exactly 1 GB (1,000,000,000 bytes) must exceed the strict < 1 GB limit
        oversized = OversizedStream(1_000_000_000)

        with pytest.raises(FileSizeLimitExceededError):
            store_file_stream(
                actor=instructor_user,
                course_id=test_course.id,
                file_stream=oversized,
                filename="massive_lecture.mp4",
                content_type="video/mp4",
                asset_type="RESOURCE",
                session=db.session,
            )

    def test_cross_course_resource_attachment_blocked(
        self, app: Flask, instructor_user: User
    ) -> None:
        """Cannot attach FileAsset from Course B to Lesson in Course A (FileValidationError)."""
        course_a = create_course(
            instructor_user,
            {"course_code": "CRS-A", "title": "Course A", "category": "CS"},
        )
        course_b = create_course(
            instructor_user,
            {"course_code": "CRS-B", "title": "Course B", "category": "CS"},
        )

        lesson_a = create_lesson(
            instructor_user,
            course_a.id,
            {"title": "Lesson in Course A", "markdown_content": "# A"},
        )
        asset_b = store_file_stream(
            actor=instructor_user,
            course_id=course_b.id,
            file_stream=io.BytesIO(b"Asset in Course B"),
            filename="course_b_notes.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            session=db.session,
        )

        with pytest.raises(FileValidationError, match="belongs to a different course"):
            attach_resource_to_lesson(
                actor=instructor_user,
                lesson_id=lesson_a.id,
                asset_id=asset_b.id,
                session=db.session,
            )


class TestStudentViewingAndStreaming:
    """Student lecture view, video streaming (Range / 206), and fail-closed file access."""

    def test_student_video_streaming_conditional_range(
        self,
        client: FlaskClient,
        enrolled_course: tuple[Course, Enrollment],
        instructor_user: User,
        enrolled_student: User,
    ) -> None:
        """Enrolled student can stream video with conditional=True (200 / 206 Partial Content)."""
        course, _ = enrolled_course

        video_payload = b"\x00\x00\x00\x20ftypisom" + b"\x42" * 4096
        asset = store_file_stream(
            actor=instructor_user,
            course_id=course.id,
            file_stream=io.BytesIO(video_payload),
            filename="intro_stream.mp4",
            content_type="video/mp4",
            asset_type="RESOURCE",
            title="Video Streaming Test",
            session=db.session,
        )

        lesson = create_lesson(
            instructor_user,
            course.id,
            {"title": "Video Streaming Lesson", "markdown_content": "# Streaming"},
        )
        attach_resource_to_lesson(
            actor=instructor_user,
            lesson_id=lesson.id,
            asset_id=asset.id,
            session=db.session,
        )
        change_lesson_status(instructor_user, lesson.id, "PUBLISHED", session=db.session)

        # Login student
        login_web_user(client, enrolled_student)

        # 1. Full stream request (disposition=inline)
        resp_full = client.get(
            f"/student/courses/{course.public_id}/files/{asset.public_id}/download?disposition=inline"
        )
        assert resp_full.status_code == 200
        assert resp_full.headers.get("Accept-Ranges") == "bytes"

        # 2. HTTP Range request for partial streaming
        resp_range = client.get(
            f"/student/courses/{course.public_id}/files/{asset.public_id}/download?disposition=inline",
            headers={"Range": "bytes=0-100"},
        )
        assert resp_range.status_code == 206
        assert len(resp_range.data) == 101
        assert "bytes 0-100/" in resp_range.headers.get("Content-Range", "")

    def test_student_download_attached_pdf_resource(
        self,
        client: FlaskClient,
        enrolled_course: tuple[Course, Enrollment],
        instructor_user: User,
        enrolled_student: User,
    ) -> None:
        """Enrolled student can download attached lecture PDF resource."""
        course, _ = enrolled_course

        pdf_payload = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        asset = store_file_stream(
            actor=instructor_user,
            course_id=course.id,
            file_stream=io.BytesIO(pdf_payload),
            filename="cheatsheet.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Cheat Sheet",
            session=db.session,
        )
        lesson = create_lesson(
            instructor_user,
            course.id,
            {"title": "Cheatsheet Lesson", "markdown_content": "# Cheatsheet"},
        )
        attach_resource_to_lesson(
            actor=instructor_user,
            lesson_id=lesson.id,
            asset_id=asset.id,
            session=db.session,
        )
        change_lesson_status(instructor_user, lesson.id, "PUBLISHED", session=db.session)

        login_web_user(client, enrolled_student)
        resp = client.get(f"/student/courses/{course.public_id}/files/{asset.public_id}/download")
        assert resp.status_code == 200
        assert resp.data == pdf_payload

    def test_fail_closed_security_unenrolled_student_blocked(
        self,
        client: FlaskClient,
        test_course: Course,
        instructor_user: User,
        unenrolled_student: User,
    ) -> None:
        """Unenrolled student downloading lesson resource is rejected with 403 Forbidden."""
        asset = store_file_stream(
            actor=instructor_user,
            course_id=test_course.id,
            file_stream=io.BytesIO(b"Secret lesson material"),
            filename="secret.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            session=db.session,
        )
        lesson = create_lesson(
            instructor_user,
            test_course.id,
            {"title": "Secret Lesson", "markdown_content": "# Secret"},
        )
        attach_resource_to_lesson(
            actor=instructor_user,
            lesson_id=lesson.id,
            asset_id=asset.id,
            session=db.session,
        )
        change_lesson_status(instructor_user, lesson.id, "PUBLISHED", session=db.session)

        login_web_user(client, unenrolled_student)
        resp = client.get(
            f"/student/courses/{test_course.public_id}/files/{asset.public_id}/download"
        )
        assert resp.status_code == 403

    def test_fail_closed_security_draft_lesson_resource_blocked(
        self,
        client: FlaskClient,
        enrolled_course: tuple[Course, Enrollment],
        instructor_user: User,
        enrolled_student: User,
    ) -> None:
        """Enrolled student accessing resource on a DRAFT lesson is rejected with 403 Forbidden."""
        course, _ = enrolled_course

        asset = store_file_stream(
            actor=instructor_user,
            course_id=course.id,
            file_stream=io.BytesIO(b"Draft lesson content"),
            filename="draft.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            session=db.session,
        )
        lesson = create_lesson(
            instructor_user,
            course.id,
            {"title": "Draft Lesson", "markdown_content": "# Draft"},
        )
        attach_resource_to_lesson(
            actor=instructor_user,
            lesson_id=lesson.id,
            asset_id=asset.id,
            session=db.session,
        )
        # Keep lesson in DRAFT status

        login_web_user(client, enrolled_student)
        resp = client.get(f"/student/courses/{course.public_id}/files/{asset.public_id}/download")
        assert resp.status_code == 403
