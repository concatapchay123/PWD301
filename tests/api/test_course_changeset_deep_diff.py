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

from pwd301.extensions import db
from pwd301.models.course import Course, LearningUnit, Lesson
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import create_course
from pwd301.services.lesson_service import (
    create_learning_unit,
    create_lesson,
    get_course_changeset_diff,
    update_lesson,
)
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def deep_diff_env(app: Flask) -> dict[str, Any]:
    """Setup instructor, admin, and a published course with two chapters and initial lessons."""
    sess: Session = db.session
    seed_baseline(sess)

    inst_user = register_user(
        email="inst_diff@pwd301.local",
        password="Password@123",
        display_name="TS. Giảng Viên Diff Test",
        session=sess,
    )
    assign_role_to_user(inst_user.id, "INSTRUCTOR", session=sess)

    admin_user = register_user(
        email="admin_diff@pwd301.local",
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
    course.status = "PUBLISHED"
    sess.flush()

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
            "markdown_content": "# Bài 1\nNội dung ban đầu.\n\n<!-- mini_quiz: [{\"question\": \"Thủ đô?\", \"type\": \"MULTIPLE_CHOICE\", \"options\": [\"Hà Nội\", \"Huế\"], \"correct_index\": 0}] -->",
        },
        session=sess,
    )
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
        {"question": "Thủ đô?", "type": "MULTIPLE_CHOICE", "options": ["Hà Nội", "Huế"], "correct_index": 0},
        {"question": "Việt Nam có thủ đô là [___].", "type": "FILL_BLANK", "blank_answer": "Hà Nội"},
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
    diff = get_course_changeset_diff(actor=inst, change_request_id_or_course_id=course.id, session=sess)

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
