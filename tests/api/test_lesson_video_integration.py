"""Tests for Lesson Video Integration, YouTube/Vimeo embedding, and CSP Security Policies.

Verifies:
1. Content-Security-Policy (CSP) allows framing YouTube and Vimeo, and media sources.
2. Instructor can create a lesson with a YouTube/external video URL.
3. GET /instructor/lessons/<id> returns video_url correctly.
4. Student can retrieve the lesson with video_url.
5. Instructor can update and remove video_url.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import User
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def instructor_user(app: Flask) -> User:
    sess: Session = db.session
    u = register_user(
        f"instructor_vid_{uuid.uuid4().hex[:6]}@pwd301.local",
        "Password@123",
        "TS. Video Tester",
    )
    u = assign_role_to_user(u.id, "INSTRUCTOR")
    u.email_verified_at = datetime.now(UTC)
    sess.commit()
    return u


@pytest.fixture
def student_user(app: Flask) -> User:
    sess: Session = db.session
    u = register_user(
        f"student_vid_{uuid.uuid4().hex[:6]}@pwd301.local",
        "Password@123",
        "Sinh viên Video",
    )
    u = assign_role_to_user(u.id, "STUDENT")
    u.email_verified_at = datetime.now(UTC)
    sess.commit()
    return u


@pytest.fixture
def sample_course(app: Flask, instructor_user: User) -> Course:
    sess: Session = db.session
    c = create_course(
        actor=instructor_user,
        data={
            "title": "Nhập môn Phát triển Web Video Test",
            "course_code": f"WEB{uuid.uuid4().hex[:4].upper()}",
            "description": "Khóa học kiểm thử tích hợp video bài giảng",
            "category": "Technology",
            "difficulty": "BEGINNER",
        },
        session=sess,
    )
    c.status = "DRAFT"
    sess.commit()
    return c


def test_csp_allows_video_framing_and_media(client: FlaskClient) -> None:
    """Verify CSP directives explicitly allow YouTube, Vimeo, and media sources."""
    resp = client.get("/")
    assert resp.status_code == 200
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "frame-src" in csp
    assert "https://www.youtube.com" in csp
    assert "https://www.youtube-nocookie.com" in csp
    assert "https://player.vimeo.com" in csp
    assert "media-src" in csp
    assert "data:" in csp
    assert "blob:" in csp
    assert "https://cdnjs.cloudflare.com" in csp


def test_lesson_video_lifecycle_instructor_and_student(
    client: FlaskClient,
    app: Flask,
    instructor_user: User,
    student_user: User,
    sample_course: Course,
) -> None:
    """Verify creating, fetching, updating, and removing video_url in lessons."""
    # 1. Login as instructor
    login_res = client.post(
        "/auth/login",
        json={"email": instructor_user.email, "password": "Password@123"},
    )
    assert login_res.status_code == 200

    course_uuid = str(sample_course.public_id)

    # 2. Create lesson with YouTube video URL
    yt_url = "https://www.youtube.com/watch?v=M7lc1UVf-VE"
    create_res = client.post(
        f"/instructor/courses/{course_uuid}/lessons",
        json={
            "title": "Bài giảng 1: Giới thiệu HTML & Video Embed",
            "summary": "Hướng dẫn nhúng video đa nền tảng vào bài giảng",
            "markdown_content": "<p>Nội dung bài học đầu tiên.</p>",
            "video_url": yt_url,
            "status": "DRAFT",
        },
    )
    assert create_res.status_code in (200, 201)
    lesson_data = create_res.get_json()
    lesson_id = lesson_data.get("lesson_id") or lesson_data.get("id")
    assert lesson_id is not None

    # 3. Instructor fetches lesson: video_url must match
    get_res = client.get(f"/instructor/lessons/{lesson_id}")
    assert get_res.status_code == 200
    inst_lesson = get_res.get_json().get("lesson", get_res.get_json())
    assert inst_lesson.get("video_url") == yt_url

    # 4. Instructor updates video URL while course is still in DRAFT
    new_yt_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    update_res = client.patch(
        f"/instructor/lessons/{lesson_id}",
        json={
            "video_url": new_yt_url,
        },
    )
    assert update_res.status_code == 200

    get_updated = client.get(f"/instructor/lessons/{lesson_id}")
    assert get_updated.status_code == 200
    updated_data = get_updated.get_json()
    updated_lesson = updated_data.get("lesson", updated_data)
    assert updated_lesson.get("video_url") == new_yt_url

    # 5. Instructor publishes the course and lesson for students
    sess: Session = db.session
    course_obj = sess.get(Course, sample_course.id)
    assert course_obj is not None
    course_obj.status = "PUBLISHED"

    from pwd301.services.lesson_service import _resolve_lesson
    lesson_obj = _resolve_lesson(lesson_id, session=sess)
    assert lesson_obj is not None
    lesson_obj.status = "PUBLISHED"
    sess.commit()

    # 6. Student enrolls and fetches lesson: video_url must be present
    enroll_student(student_user, sample_course.id, session=sess)
    sess.commit()

    # Login as student
    client.post("/auth/logout")
    stud_login = client.post(
        "/auth/login",
        json={"email": student_user.email, "password": "Password@123"},
    )
    assert stud_login.status_code == 200

    stud_lesson_res = client.get(f"/student/courses/{course_uuid}/lessons/{lesson_id}")
    assert stud_lesson_res.status_code == 200
    stud_lesson = stud_lesson_res.get_json().get("lesson", stud_lesson_res.get_json())
    assert stud_lesson.get("video_url") == new_yt_url
    assert stud_lesson.get("video_urls") == [new_yt_url]

    # 7. Verify lesson video removal when DRAFT
    course_obj.status = "DRAFT"
    lesson_obj.status = "DRAFT"
    sess.commit()

    client.post("/auth/logout")
    client.post(
        "/auth/login",
        json={"email": instructor_user.email, "password": "Password@123"},
    )
    clear_res = client.patch(
        f"/instructor/lessons/{lesson_id}",
        json={
            "video_url": "",
        },
    )
    assert clear_res.status_code == 200
    get_cleared = client.get(f"/instructor/lessons/{lesson_id}")
    assert get_cleared.status_code == 200
    cleared_data = get_cleared.get_json()
    cleared_lesson = cleared_data.get("lesson", cleared_data)
    assert not cleared_lesson.get("video_url")


def test_lesson_create_keeps_three_drafts_as_distinct_lessons(
    client: FlaskClient,
    instructor_user: User,
    sample_course: Course,
) -> None:
    """Three new draft submissions retain separate IDs, titles, and content."""
    client.post(
        "/auth/login",
        json={"email": instructor_user.email, "password": "Password@123"},
    )

    created = []
    for ordinal in range(1, 4):
        response = client.post(
            f"/instructor/courses/{sample_course.public_id}/lessons",
            json={
                "title": f"Draft {ordinal}",
                "markdown_content": f"<p>Content {ordinal}</p>",
                "status": "DRAFT",
            },
        )
        assert response.status_code == 201
        created.append(response.get_json()["lesson_id"])

    assert len(set(created)) == 3
    loaded = [client.get(f"/instructor/lessons/{lesson_id}").get_json() for lesson_id in created]
    assert [lesson["title"] for lesson in loaded] == ["Draft 1", "Draft 2", "Draft 3"]
    assert [lesson["markdown_content"] for lesson in loaded] == [
        "<p>Content 1</p>",
        "<p>Content 2</p>",
        "<p>Content 3</p>",
    ]


def test_lesson_resource_route_attaches_multiple_files(
    client: FlaskClient,
    instructor_user: User,
    sample_course: Course,
) -> None:
    """The existing lesson upload endpoint accepts multiple documents in one request."""
    import io

    from werkzeug.datastructures import MultiDict

    client.post(
        "/auth/login",
        json={"email": instructor_user.email, "password": "Password@123"},
    )
    lesson_response = client.post(
        f"/instructor/courses/{sample_course.public_id}/lessons",
        json={"title": "Multi-file lesson", "markdown_content": "<p>Body</p>"},
    )
    lesson_id = lesson_response.get_json()["lesson_id"]

    upload = client.post(
        f"/instructor/courses/{sample_course.public_id}/lessons/{lesson_id}/resources",
        data=MultiDict(
            [
                ("file", (io.BytesIO(b"first handout"), "first.txt")),
                ("file", (io.BytesIO(b"second handout"), "second.txt")),
            ]
        ),
        content_type="multipart/form-data",
    )

    assert upload.status_code == 201
    resources = client.get(f"/instructor/lessons/{lesson_id}").get_json()["resources"]
    assert [resource["title"] for resource in resources] == ["first.txt", "second.txt"]


def test_lesson_multi_file_upload_rolls_back_earlier_files_when_a_later_file_fails(
    client: FlaskClient,
    instructor_user: User,
    sample_course: Course,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed batch leaves no attached resources or active uploaded assets."""
    import io

    from werkzeug.datastructures import MultiDict

    from pwd301.models.file_import import FileAsset, LessonResource
    import pwd301.blueprints.instructor.routes as instructor_routes
    from pwd301.services.lesson_service import _resolve_lesson

    client.post(
        "/auth/login",
        json={"email": instructor_user.email, "password": "Password@123"},
    )
    lesson_response = client.post(
        f"/instructor/courses/{sample_course.public_id}/lessons",
        json={"title": "Atomic upload", "markdown_content": "<p>Body</p>"},
    )
    lesson_id = lesson_response.get_json()["lesson_id"]
    lesson = _resolve_lesson(lesson_id, session=db.session)
    original_store = instructor_routes.store_file_stream
    calls = 0

    def fail_on_second_file(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("Injected second-file failure")
        return original_store(*args, **kwargs)

    monkeypatch.setattr(instructor_routes, "store_file_stream", fail_on_second_file)
    response = client.post(
        f"/instructor/courses/{sample_course.public_id}/lessons/{lesson_id}/resources",
        data=MultiDict(
            [
                ("file", (io.BytesIO(b"first handout"), "atomic-first.txt")),
                ("file", (io.BytesIO(b"second handout"), "atomic-second.txt")),
            ]
        ),
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    assert db.session.query(LessonResource).filter_by(lesson_id=lesson.id).count() == 0
    first_asset = db.session.query(FileAsset).filter_by(display_name="atomic-first.txt").one()
    assert first_asset.status == "TRASH"


def test_lesson_rejects_six_youtube_videos(
    client: FlaskClient,
    instructor_user: User,
    sample_course: Course,
) -> None:
    """A lesson cannot be created with more than five combined video entries."""
    client.post(
        "/auth/login",
        json={"email": instructor_user.email, "password": "Password@123"},
    )
    response = client.post(
        f"/instructor/courses/{sample_course.public_id}/lessons",
        json={
            "title": "Too many videos",
            "markdown_content": "<p>Body</p>",
            "video_urls": [f"https://youtu.be/video{index:07}" for index in range(6)],
        },
    )

    assert response.status_code == 400
    assert "5" in response.get_json()["error"]["message"]


def test_lesson_accepts_five_youtube_videos(
    client: FlaskClient,
    instructor_user: User,
    sample_course: Course,
) -> None:
    """Exactly five YouTube links are accepted and returned by the lesson API."""
    client.post(
        "/auth/login",
        json={"email": instructor_user.email, "password": "Password@123"},
    )
    urls = [f"https://youtu.be/accepted{index:04}" for index in range(5)]
    response = client.post(
        f"/instructor/courses/{sample_course.public_id}/lessons",
        json={
            "title": "Five videos",
            "markdown_content": "<p>Body</p>",
            "video_urls": urls,
        },
    )

    assert response.status_code == 201
    assert response.get_json()["video_urls"] == urls


def test_lesson_mixed_video_limit_rejects_without_losing_existing_videos(
    client: FlaskClient,
    app: Flask,
    instructor_user: User,
    sample_course: Course,
) -> None:
    """Adding a sixth video is rejected while the current four links remain intact."""
    from pwd301.models.course import Lesson
    from pwd301.models.file_import import LessonResource

    client.post(
        "/auth/login",
        json={"email": instructor_user.email, "password": "Password@123"},
    )
    create_response = client.post(
        f"/instructor/courses/{sample_course.public_id}/lessons",
        json={
            "title": "Video limit lesson",
            "markdown_content": "<p>Body</p>",
            "video_urls": [f"https://youtu.be/initial{index:05}" for index in range(4)],
        },
    )
    lesson_id = create_response.get_json()["lesson_id"]

    from pwd301.services.lesson_service import _resolve_lesson

    lesson = _resolve_lesson(lesson_id, session=db.session)
    db.session.add(
        LessonResource(
            lesson_id=lesson.id,
            file_asset_id=_create_pending_video_asset(
                instructor_user,
                sample_course,
                "existing-video.mp4",
            ).id,
            position=1,
            label="existing-video.mp4",
        )
    )
    db.session.commit()

    update = client.patch(
        f"/instructor/lessons/{lesson_id}",
        json={"video_urls": [f"https://youtu.be/replaced{index:05}" for index in range(5)]},
    )

    assert update.status_code == 400
    loaded = client.get(f"/instructor/lessons/{lesson_id}").get_json()
    assert loaded["video_urls"] == [f"https://youtu.be/initial{index:05}" for index in range(4)]
    assert [item["title"] for item in loaded["resources"]] == ["existing-video.mp4"]


def _create_pending_video_asset(
    instructor_user: User,
    course: Course,
    filename: str,
) -> "FileAsset":
    from pwd301.models.file_import import FileAsset

    asset = FileAsset(
        course_id=course.id,
        created_by_user_id=instructor_user.id,
        asset_type="RESOURCE",
        display_name=filename,
        status="PENDING",
    )
    db.session.add(asset)
    db.session.flush()
    return asset
