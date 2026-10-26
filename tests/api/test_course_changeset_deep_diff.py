"""TDD Tests for Course Changeset Deep 5-Category Diff Engine (TASK-084).

Verifies that get_course_changeset_diff produces granular, categorized diffs:
1. curriculum_structure: tracks additions, deletions, renames, and moves across chapters.
2. content_blocks: tracks video and document attachments added or removed.
3. interactive_quizzes: tracks interactive questions added, removed, or modified.
4. assessments: tracks chapter quizzes and final exams created, updated, or removed.
5. governance_rules: tracks completion threshold changes (min GPA, completion %) and cover images.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.seeds.baseline import seed_baseline
from backend.services.course_service import create_course
from backend.services.lesson_service import (
    create_learning_unit,
    create_lesson,
    get_course_changeset_diff,
)
from backend.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def deep_diff_env(app: Flask) -> dict[str, Any]:
    """Setup instructor, admin, and a published course with two chapters and initial lessons."""
    sess: Session = db.session
    seed_baseline(sess)

    inst_user = register_user(
        email="inst_diff@backend.local",
        password="Password@123",
        display_name="TS. Giảng Viên Diff Test",
        session=sess,
    )
    assign_role_to_user(inst_user.id, "INSTRUCTOR", session=sess)

    admin_user = register_user(
        email="admin_diff@backend.local",
        password="Password@123",
        display_name="Quản Trị Viên Kiểm Thử",
        session=sess,
    )
    assign_role_to_user(admin_user.id, "ADMIN", session=sess)

    course = create_course(
        actor=inst_user,
        data={
            "course_code": "DIFF101",
            "title": "Nhập Môn Kiểm Thử Diff",
            "description": "Mô tả khóa học ban đầu.",
            "duration_hours": 30,
            "completion_requirements": json.dumps({"min_gpa": 5.0, "completion_percent": 80}),
        },
        session=sess,
    )
    unit1 = create_learning_unit(
        actor=inst_user,
        course_id=course.id,
        data={"title": "Chương 1: Khởi đầu", "position": 1},
        session=sess,
    )
    unit2 = create_learning_unit(
        actor=inst_user,
        course_id=course.id,
        data={"title": "Chương 2: Chuyên sâu", "position": 2},
        session=sess,
    )

    lesson1 = create_lesson(
        actor=inst_user,
        course_id=course.id,
        data={
            "title": "Bài 1: Giới thiệu",
            "position": 1,
            "learning_unit_id": unit1.id,
            "markdown_content": '# Bài 1\nNội dung ban đầu.\n\n<!-- mini_quiz: [{"question": "Thủ đô?", "type": "MULTIPLE_CHOICE", "options": ["Hà Nội", "Huế"], "correct_index": 0}] -->',
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    lesson1.status = "PUBLISHED"
    sess.commit()

    return {
        "instructor": inst_user,
        "admin": admin_user,
        "course": course,
        "unit1": unit1,
        "unit2": unit2,
        "lesson1": lesson1,
    }


def test_deep_diff_categorization_and_lesson_move(deep_diff_env: dict[str, Any]) -> None:
    """Test that moving a lesson to another unit and modifying quiz produces 5-category diff."""
    sess: Session = db.session
    inst = deep_diff_env["instructor"]
    course = deep_diff_env["course"]
    unit2 = deep_diff_env["unit2"]
    lesson1 = deep_diff_env["lesson1"]

    # Stage a modification to lesson1: draft version with modified content and moved to unit2
    new_quiz = [
        {
            "question": "Thủ đô?",
            "type": "MULTIPLE_CHOICE",
            "options": ["Hà Nội", "Huế"],
            "correct_index": 0,
        },
        {
            "question": "Việt Nam có thủ đô là [___].",
            "type": "FILL_BLANK",
            "blank_answer": "Hà Nội",
        },
    ]
    new_md = f"# Bài 1: Đã Đổi Tên\nNội dung đã được biên tập lại.\n\n<!-- mini_quiz: {json.dumps(new_quiz)} -->"

    draft_lesson = create_lesson(
        actor=inst,
        course_id=course.id,
        data={
            "title": "Bài 1: Đã Đổi Tên",
            "learning_unit_id": unit2.id,
            "position": 2,
            "markdown_content": new_md,
            "status": "DRAFT",
        },
        session=sess,
    )
    draft_lesson.previous_lesson_id = lesson1.id
    sess.commit()

    # Call get_course_changeset_diff
    diff = get_course_changeset_diff(
        actor=inst, change_request_id_or_course_id=course.id, session=sess
    )

    # 1. Must contain all 5 category keys
    assert "curriculum_structure" in diff
    assert "content_blocks" in diff
    assert "interactive_quizzes" in diff
    assert "assessments" in diff
    assert "governance_rules" in diff
    assert "total_changes_count" in diff

    # 2. Check curriculum structure tracks move or edit
    struct_changes = diff["curriculum_structure"]
    assert len(struct_changes) > 0
    # One of the changes should reflect unit move or title change
    titles = [c.get("title") for c in struct_changes]
    assert "Bài 1: Đã Đổi Tên" in titles

    # 3. Check interactive quiz diff detected the added fill-in-the-blank question
    quiz_changes = diff["interactive_quizzes"]
    assert len(quiz_changes) > 0
    added_quizzes = [q for q in quiz_changes if q.get("change_type") == "ADDED"]
    assert any("Việt Nam có thủ đô là [___]." in q.get("question", "") for q in added_quizzes)


def test_deep_diff_detects_question_bank_revisions(deep_diff_env: dict[str, Any]) -> None:
    """A draft with question revisions produces question_changes and nonzero total_changes_count."""
    sess: Session = db.session
    inst = deep_diff_env["instructor"]
    course = deep_diff_env["course"]

    from backend.services.question_bank_service import create_question

    q = create_question(
        actor=inst,
        course_id=course.id,
        payload={
            "question_type": "MULTIPLE_CHOICE",
            "content": "Câu hỏi ngân hàng mới trong bản nháp?",
            "explanation": "Giải thích chi tiết",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "Đáp án đúng", "is_correct": True, "position": 1},
                {"content": "Đáp án sai", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    sess.commit()

    diff = get_course_changeset_diff(
        actor=inst, change_request_id_or_course_id=course.id, session=sess
    )
    assert "question_changes" in diff
    assert len(diff["question_changes"]) > 0
    q_change = next(
        c for c in diff["question_changes"] if "Câu hỏi ngân hàng mới" in c.get("content", "")
    )
    assert q_change["change_type"] == "ADDED"
    assert q_change["question_type"] == "MULTIPLE_CHOICE"
    assert q_change["explanation"] == "Giải thích chi tiết"
    assert diff["total_changes_count"] > 0


def test_deep_diff_detects_prerequisite_changes_with_human_readable_titles(
    deep_diff_env: dict[str, Any],
) -> None:
    """Prerequisite changes show course code and title, not just raw UUIDs."""
    sess: Session = db.session
    inst = deep_diff_env["instructor"]
    course = deep_diff_env["course"]

    prereq_course = create_course(
        actor=inst,
        data={
            "course_code": "PRE101",
            "title": "Môn Tiên Quyết Mẫu",
            "description": "Mô tả tiên quyết.",
            "duration_hours": 15,
        },
        session=sess,
    )
    prereq_course.status = "PUBLISHED"
    sess.commit()

    from backend.services.course_workflow_service import stage_prerequisite

    stage_prerequisite(
        actor=inst, course=course, prerequisite=prereq_course, remove=False, session=sess
    )
    sess.commit()

    diff = get_course_changeset_diff(
        actor=inst, change_request_id_or_course_id=course.id, session=sess
    )
    assert "prerequisite_changes" in diff
    assert len(diff["prerequisite_changes"]) > 0
    p_change = diff["prerequisite_changes"][0]
    assert p_change["change_type"] == "ADDED"
    assert p_change["course_code"] == "PRE101"
    assert p_change["title"] == "Môn Tiên Quyết Mẫu"
    assert "PRE101" in p_change["description"]
    assert diff["total_changes_count"] > 0


def test_deep_diff_detects_standalone_file_assets(deep_diff_env: dict[str, Any]) -> None:
    """Standalone accepted files in draft are reported with file_name and size."""
    import io
    from unittest.mock import patch

    from backend.services.file_service import store_file_stream
    from backend.services.scanner_service import ScanVerdict

    sess: Session = db.session
    inst = deep_diff_env["instructor"]
    course = deep_diff_env["course"]

    scan = ScanVerdict(status="PASS", engine_name="fixture")
    with (
        patch("backend.services.file_service.scan_file_all_engines", return_value=[scan]),
        patch("backend.services.file_service.scan_blob_file", return_value=scan),
    ):
        fa = store_file_stream(
            inst,
            course.id,
            io.BytesIO(b"Giao trinh chuyen sau noi dung"),
            "GiaoTrinh_ChuyenSau.pdf",
            session=sess,
        )

    sess.commit()

    diff = get_course_changeset_diff(
        actor=inst, change_request_id_or_course_id=course.id, session=sess
    )
    assert "file_changes" in diff
    assert len(diff["file_changes"]) > 0
    f_change = diff["file_changes"][0]
    assert f_change["change_type"] == "ADDED"
    assert f_change["file_name"] == "GiaoTrinh_ChuyenSau.pdf"
    assert diff["total_changes_count"] > 0


def test_deep_diff_zero_false_positive_when_rules_and_cover_untouched(
    deep_diff_env: dict[str, Any],
) -> None:
    """When a working draft is created with unchanged metadata and rules, no false positives occur."""
    sess: Session = db.session
    inst = deep_diff_env["instructor"]
    course = deep_diff_env["course"]

    from backend.services.course_workflow_service import stage_course_fields, working_changeset

    # Stage metadata with exact same title and completion rules
    stage_course_fields(
        actor=inst,
        course=course,
        group="course_metadata",
        fields={
            "title": course.title,
            "description": course.description,
            "thumbnail_file_asset_id": course.thumbnail_file_asset_id,
        },
        session=sess,
    )
    stage_course_fields(
        actor=inst,
        course=course,
        group="completion_rules",
        fields={
            "minimum_progress_percent": 80,
            "require_all_required_lessons": True,
            "require_required_assessments": True,
        },
        session=sess,
    )
    sess.commit()

    diff = get_course_changeset_diff(
        actor=inst, change_request_id_or_course_id=course.id, session=sess
    )

    # 1. Total changes must be 0
    assert diff["total_changes_count"] == 0
    assert len(diff["metadata_changes"]) == 0

    # 2. Governance rules must not be marked changed
    gov = diff["governance_rules"]
    assert gov["is_changed"] is False
    assert gov["completion_rules_changed"] is False
    assert gov["cover_image_changed"] is False

    # 3. proposed_cover_url must not be in governance_rules when cover is unchanged
    assert "proposed_cover_url" not in gov
    assert gov.get("cover_image_url") is None

    # 4. Academic divisions must be present with all 7 groups
    assert "academic_divisions" in diff
    divisions = diff["academic_divisions"]
    assert "1_curriculum_structure" in divisions
    assert "2_content_blocks" in divisions
    assert "3_interactive_quizzes" in divisions
    assert "4_assessments_and_questions" in divisions
    assert "5_file_changes" in divisions
    assert "6_prerequisite_changes" in divisions
    assert "7_governance_and_metadata" in divisions


def test_deep_diff_detects_academic_divisions_and_trailer_contact(
    deep_diff_env: dict[str, Any],
) -> None:
    """Trailer URL, contact info, and completion threshold changes are correctly recognized in division 7."""
    sess: Session = db.session
    inst = deep_diff_env["instructor"]
    course = deep_diff_env["course"]

    from backend.services.course_workflow_service import stage_course_fields

    # Stage new trailer_url and changed GPA threshold
    stage_course_fields(
        actor=inst,
        course=course,
        group="course_metadata",
        fields={
            "trailer_url": "https://www.youtube.com/watch?v=TESTTRAILER123",
            "contact_info": {"email": "instructor@school.edu", "phone": "0987654321"},
        },
        session=sess,
    )
    stage_course_fields(
        actor=inst,
        course=course,
        group="completion_rules",
        fields={
            "minimum_grade_score": 8.0,
        },
        session=sess,
    )
    sess.commit()

    diff = get_course_changeset_diff(
        actor=inst, change_request_id_or_course_id=course.id, session=sess
    )

    # Must detect trailer_url, contact_info, and completion rule change
    assert diff["total_changes_count"] >= 3
    gov = diff["governance_rules"]
    assert gov["is_changed"] is True
    assert gov["completion_rules_changed"] is True

    # Trailer and contact info in metadata_changes
    meta_fields = [m["field"] for m in diff["metadata_changes"]]
    assert "trailer_url" in meta_fields
    assert "contact_info" in meta_fields

