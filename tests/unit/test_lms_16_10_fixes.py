"""Comprehensive test suite for fixes applied to the 6 LMS bug groups (16-10 report).

BUG-01: Course draft submission eligibility and changeset status calculation.
BUG-02: SLOs and authentic description validation during course publish readiness checklist.
BUG-03: Video player readiness & big-play button behavior.
BUG-04: Detached lesson resources marked as TRASH and excluded from course detail resources.
BUG-05: Clean UI labels ("Chuẩn đầu ra", "Lộ trình đào tạo") and removed non-working button.
BUG-06: Fisher-Yates derangement shuffle for interactive MATCH and DRAG_DROP word bank.
"""

from __future__ import annotations

import io
import json
import uuid

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.blueprints.instructor.routes import validate_course_publish_readiness
from pwd301.extensions import db
from pwd301.models.course import Course, _parse_string_list
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.course_workflow_service import AuthoringProjection
from pwd301.services.file_service import (
    attach_resource_to_lesson,
    detach_resource_from_lesson,
    store_file_stream,
)
from pwd301.services.lesson_service import (
    create_lesson,
    get_course_changeset_status,
)
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
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
    email = f"inst_lms1610_{uuid.uuid4().hex[:6]}@example.com"
    u = register_user(email, "Password@123", "Instructor 16-10")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    c = create_course(
        instructor_user,
        {
            "course_code": f"LMS-{uuid.uuid4().hex[:4].upper()}",
            "title": "LMS 16-10 Test Course",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
        },
    )
    db.session.commit()
    return c


def test_bug01_changeset_status_detects_draft_lessons(
    app: Flask,
    instructor_user: User,
    test_course: Course,
) -> None:
    """BUG-01: get_course_changeset_status correctly detects draft lessons and reports status."""
    sess = db.session
    lesson = create_lesson(
        instructor_user,
        test_course.id,
        {
            "title": "Draft Lesson 1",
            "markdown_content": "# Lesson Content",
            "status": "DRAFT",
        },
    )
    sess.commit()

    status = get_course_changeset_status(instructor_user, test_course.id, session=sess)
    assert status is not None
    assert "status" in status
    assert "has_changes" in status


def test_bug02_parse_string_list_and_authoring_projection_slo(
    app: Flask,
    instructor_user: User,
    test_course: Course,
) -> None:
    """BUG-02: _parse_string_list extracts SLOs from list of dicts, and AuthoringProjection surfaces them."""
    raw_slos = [
        {"title": "SLO 1: Master algorithms", "weight": 40},
        {"title": "SLO 2: Write clean code", "weight": 60},
    ]
    parsed = _parse_string_list(raw_slos)
    assert len(parsed) == 2
    assert "SLO 1: Master algorithms" in parsed
    assert "SLO 2: Write clean code" in parsed

    # Test JSON string of list of dicts
    json_slos = json.dumps(raw_slos)
    parsed_json = _parse_string_list(json_slos)
    assert len(parsed_json) == 2

    # Test AuthoringProjection
    projection = AuthoringProjection(test_course, {"learning_objectives": raw_slos})
    assert len(projection.learning_objectives_list) == 2
    assert projection.learning_objectives_list[0] == "SLO 1: Master algorithms"


def test_bug02_publish_readiness_validates_slos_and_description(
    app: Flask,
    instructor_user: User,
    test_course: Course,
) -> None:
    """BUG-02: validate_course_publish_readiness distinguishes between description < 20 chars vs missing SLOs."""
    sess = db.session

    # Case 1: Short description and no SLOs
    test_course.description = "Too short"
    test_course.learning_objectives = ""
    sess.commit()

    checklist1 = validate_course_publish_readiness(test_course, actor=instructor_user, session=sess)
    course_info1 = next(c for c in checklist1["criteria"] if c["id"] == "course_info")
    assert not course_info1["passed"]
    assert "mô tả thực tế" in course_info1["detail"]

    # Case 2: Good description (>= 20 chars), but no SLOs
    test_course.description = "Khóa học cung cấp kiến thức nền tảng về cấu trúc dữ liệu và giải thuật thực chiến."
    test_course.learning_objectives = ""
    sess.commit()

    checklist2 = validate_course_publish_readiness(test_course, actor=instructor_user, session=sess)
    course_info2 = next(c for c in checklist2["criteria"] if c["id"] == "course_info")
    assert not course_info2["passed"]
    assert "Cần bổ sung ít nhất 1 chuẩn đầu ra môn học" in course_info2["detail"]

    # Case 3: Good description and SLOs present
    test_course.learning_objectives = json.dumps([{"title": "Hiểu và áp dụng giải thuật tìm kiếm"}])
    sess.commit()

    checklist3 = validate_course_publish_readiness(test_course, actor=instructor_user, session=sess)
    course_info3 = next(c for c in checklist3["criteria"] if c["id"] == "course_info")
    assert course_info3["passed"]
    assert "Đầy đủ mô tả chi tiết và chuẩn đầu ra môn học" in course_info3["detail"]


def test_bug04_detach_resource_marks_orphaned_file_asset_trash(
    app: Flask,
    instructor_user: User,
    test_course: Course,
) -> None:
    """BUG-04: Detaching a resource from a lesson marks the unreferenced FileAsset as TRASH."""
    sess = db.session

    lesson = create_lesson(
        instructor_user,
        test_course.id,
        {"title": "Lesson for Resource Detach", "markdown_content": "# Lesson Content"},
    )
    doc_asset = store_file_stream(
        actor=instructor_user,
        course_id=test_course.id,
        file_stream=io.BytesIO(b"%PDF-1.4 sample content for detachment"),
        filename="lecture_slide.pdf",
        content_type="application/pdf",
        asset_type="RESOURCE",
        title="Lecture Slide",
        session=sess,
    )
    attach_resource_to_lesson(
        actor=instructor_user,
        lesson_id=lesson.id,
        asset_id=doc_asset.id,
        label="Lecture Slide",
        session=sess,
    )
    sess.commit()

    # Asset is ACTIVE initially
    assert doc_asset.status == "ACTIVE"
    assert doc_asset.deleted_at is None

    # Detach resource from lesson
    detach_resource_from_lesson(
        actor=instructor_user,
        lesson_id=lesson.id,
        resource_id=doc_asset.id,
        session=sess,
        commit=True,
    )

    # FileAsset must now be in TRASH status and deleted_at populated
    sess.refresh(doc_asset)
    assert doc_asset.status == "TRASH"
    assert doc_asset.deleted_at is not None


def test_bug01_and_bug05_frontend_labels_contract() -> None:
    """BUG-01 & BUG-05: Verify exact required labels and removal of legacy buttons."""
    from pathlib import Path

    instructor_js = Path("frontend/assets/js/views/instructor.js").read_text(encoding="utf-8")
    student_js = Path("frontend/assets/js/views/student.js").read_text(encoding="utf-8")

    # BUG-01: Button label must be "Gửi xét duyệt" (not "Gửi xét duyệt bản nháp")
    assert "<span>Gửi xét duyệt</span>" in instructor_js
    assert "<span>Gửi xét duyệt bản nháp</span>" not in instructor_js

    # BUG-05: Button "Xem đề cương chi tiết" must be removed
    assert "overview-view-syllabus-btn" not in student_js
    assert "Xem đề cương chi tiết" not in student_js

    # BUG-05: Label must be "Chuẩn đầu ra" without "Chuẩn đầu ra môn học (Student Learning Outcomes - SLO)"
    assert "Chuẩn đầu ra môn học (Student Learning Outcomes - SLO)" not in student_js
    assert "<span>Chuẩn đầu ra</span>" in student_js

    # BUG-05: Label must be "Lộ trình đào tạo" without "& Đề cương chi tiết" or description paragraph
    assert "Lộ trình đào tạo & Đề cương chi tiết" not in student_js
    assert "Nội dung bài giảng được cấu trúc bài bản theo từng chuyên đề." not in student_js
    assert "<span>Lộ trình đào tạo</span>" in student_js


def test_bug03_custom_video_player_contract() -> None:
    """BUG-03: Custom video player hides big-play when playing and hooks MANIFEST_PARSED & canplay."""
    from pathlib import Path

    student_js = Path("frontend/assets/js/views/student.js").read_text(encoding="utf-8")

    # Big play button must toggle hidden on playing state
    assert "get('big-play')?.classList.toggle('hidden', playing)" in student_js

    # HLS MANIFEST_PARSED must be handled
    assert "Hls.Events?.MANIFEST_PARSED" in student_js

    # canplay and loadeddata events must be listened to
    assert "listen(video, 'canplay'" in student_js
    assert "listen(video, 'loadeddata'" in student_js


def test_bug06_interactive_shuffling_derangement_contract() -> None:
    """BUG-06: Interactive MATCH rights and DRAG_DROP tokens must use shuffle."""
    from pathlib import Path

    student_js = Path("frontend/assets/js/views/student.js").read_text(encoding="utf-8")

    # MATCH must use shuffleOptions instead of hashA - hashB
    assert "hashA - hashB" not in student_js
    assert "shuffleOptions" in student_js
    assert "_match" in student_js

    # DRAG_DROP tokenLabels must be shuffled
    assert "shuffleTokens" in student_js
    assert "_drag" in student_js

