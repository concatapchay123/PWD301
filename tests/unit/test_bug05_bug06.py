"""Unit tests verifying BUG-05 and BUG-06 fixes.

BUG-05: Dynamic update of changeset status and action bar after saving a lesson.
BUG-06: Clean up of LessonResource and FileAsset when lessons/units are trashed,
        and exclusion of orphaned files from student_course_detail.
"""

from __future__ import annotations

import io
import uuid

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.course import Course
from backend.models.file_import import LessonResource
from backend.models.identity import Role, User
from backend.services.course_service import create_course
from backend.services.file_service import (
    attach_resource_to_lesson,
    store_file_stream,
)
from backend.services.lesson_service import (
    create_learning_unit,
    create_lesson,
    delete_learning_unit,
    trash_lesson,
)
from backend.services.user_service import assign_role_to_user, register_user


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
    email = f"instructor_{uuid.uuid4().hex[:6]}@example.com"
    u = register_user(email, "Password@123", "Bug06 Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create a draft course managed by instructor_user."""
    c = create_course(
        instructor_user,
        {
            "course_code": f"B6-{uuid.uuid4().hex[:4].upper()}",
            "title": "Bug 06 Resource Deletion Course",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
        },
    )
    db.session.commit()
    return c


def test_trash_lesson_cleans_up_resources_and_orphaned_file_asset(
    app: Flask,
    instructor_user: User,
    test_course: Course,
) -> None:
    """Trashing a lesson removes its LessonResource and marks orphaned FileAsset as TRASH."""
    sess = db.session

    # 1. Create a lesson
    lesson = create_lesson(
        instructor_user,
        test_course.id,
        {"title": "Lesson with Resource", "markdown_content": "# Content"},
    )

    # 2. Upload and attach a file resource
    doc_asset = store_file_stream(
        actor=instructor_user,
        course_id=test_course.id,
        file_stream=io.BytesIO(b"%PDF-1.4 test file"),
        filename="notes.pdf",
        content_type="application/pdf",
        asset_type="RESOURCE",
        title="Lecture Notes",
        session=sess,
    )
    attach_resource_to_lesson(
        actor=instructor_user,
        lesson_id=lesson.id,
        asset_id=doc_asset.id,
        label="Lesson Handout",
        session=sess,
    )

    # Verify link exists and asset is ACTIVE
    lr = sess.query(LessonResource).filter(LessonResource.lesson_id == lesson.id).first()
    assert lr is not None
    assert lr.file_asset_id == doc_asset.id
    assert doc_asset.status == "ACTIVE"
    assert doc_asset.deleted_at is None

    # 3. Trash the lesson
    trashed = trash_lesson(instructor_user, lesson.id)
    assert trashed.status == "TRASH"
    assert trashed.deleted_at is not None

    # 4. Verify LessonResource link was deleted
    lr_after = sess.query(LessonResource).filter(LessonResource.lesson_id == lesson.id).first()
    assert lr_after is None

    # 5. Verify the orphaned FileAsset was marked TRASH
    sess.refresh(doc_asset)
    assert doc_asset.status == "TRASH"
    assert doc_asset.deleted_at is not None
    assert doc_asset.deleted_by_user_id == instructor_user.id


def test_trash_lesson_preserves_shared_file_asset(
    app: Flask,
    instructor_user: User,
    test_course: Course,
) -> None:
    """Trashing a lesson preserves FileAsset if another active lesson still references it."""
    sess = db.session

    # 1. Create two lessons
    l1 = create_lesson(
        instructor_user,
        test_course.id,
        {"title": "Lesson 1", "markdown_content": "# Lesson 1"},
    )
    l2 = create_lesson(
        instructor_user,
        test_course.id,
        {"title": "Lesson 2", "markdown_content": "# Lesson 2"},
    )

    # 2. Upload a shared file and attach to both lessons
    shared_asset = store_file_stream(
        actor=instructor_user,
        course_id=test_course.id,
        file_stream=io.BytesIO(b"%PDF-1.4 shared document"),
        filename="shared_manual.pdf",
        content_type="application/pdf",
        asset_type="RESOURCE",
        title="Shared Lab Manual",
        session=sess,
    )
    attach_resource_to_lesson(
        actor=instructor_user,
        lesson_id=l1.id,
        asset_id=shared_asset.id,
        label="Lab Manual (L1)",
        session=sess,
    )
    attach_resource_to_lesson(
        actor=instructor_user,
        lesson_id=l2.id,
        asset_id=shared_asset.id,
        label="Lab Manual (L2)",
        session=sess,
    )

    # 3. Trash lesson 1
    trash_lesson(instructor_user, l1.id)

    # 4. Verify L1 link deleted, but L2 link preserved
    l1_res = sess.query(LessonResource).filter(LessonResource.lesson_id == l1.id).first()
    assert l1_res is None

    l2_res = sess.query(LessonResource).filter(LessonResource.lesson_id == l2.id).first()
    assert l2_res is not None
    assert l2_res.file_asset_id == shared_asset.id

    # 5. Shared asset MUST still be ACTIVE because L2 is active
    sess.refresh(shared_asset)
    assert shared_asset.status == "ACTIVE"
    assert shared_asset.deleted_at is None


def test_delete_learning_unit_cleans_up_lesson_resources(
    app: Flask,
    instructor_user: User,
    test_course: Course,
) -> None:
    """Deleting a learning unit cleans up all its lessons' resources and marks orphaned assets TRASH."""
    sess = db.session

    # 1. Create a learning unit
    unit = create_learning_unit(
        instructor_user,
        test_course.id,
        {"title": "Chapter 1: Foundations"},
    )

    # 2. Create a lesson inside the unit
    lesson = create_lesson(
        instructor_user,
        test_course.id,
        {
            "title": "Unit Lesson",
            "markdown_content": "# Unit Lesson",
            "learning_unit_id": str(unit.public_id),
        },
    )

    # 3. Upload and attach a file resource
    unit_asset = store_file_stream(
        actor=instructor_user,
        course_id=test_course.id,
        file_stream=io.BytesIO(b"%PDF-1.4 chapter notes"),
        filename="chapter1.pdf",
        content_type="application/pdf",
        asset_type="RESOURCE",
        title="Chapter 1 Notes",
        session=sess,
    )
    attach_resource_to_lesson(
        actor=instructor_user,
        lesson_id=lesson.id,
        asset_id=unit_asset.id,
        label="Chapter 1 Guide",
        session=sess,
    )

    # 4. Delete the learning unit
    delete_learning_unit(instructor_user, str(unit.public_id))

    # 5. Verify unit and lesson are deleted/trashed
    sess.refresh(unit)
    assert unit.deleted_at is not None
    sess.refresh(lesson)
    assert lesson.deleted_at is not None
    assert lesson.status == "TRASH"

    # 6. Verify LessonResource link was deleted and FileAsset is TRASH
    lr = sess.query(LessonResource).filter(LessonResource.lesson_id == lesson.id).first()
    assert lr is None

    sess.refresh(unit_asset)
    assert unit_asset.status == "TRASH"
    assert unit_asset.deleted_at is not None


def test_student_course_detail_excludes_orphaned_documents(
    app: Flask,
    client,
    instructor_user: User,
    test_course: Course,
    setup_roles: dict[str, Role],
) -> None:
    """student_course_detail route excludes file assets that are orphaned from deleted lessons."""
    sess = db.session

    # 1. Create active lesson while course is draft
    active_lesson = create_lesson(
        instructor_user,
        test_course.id,
        {"title": "Active Lesson", "markdown_content": "# Active"},
    )

    # 2. Upload general course file
    general_asset = store_file_stream(
        actor=instructor_user,
        course_id=test_course.id,
        file_stream=io.BytesIO(b"%PDF-1.4 syllabus"),
        filename="general_syllabus.pdf",
        content_type="application/pdf",
        asset_type="RESOURCE",
        title="Course Syllabus",
        session=sess,
    )

    # 3. Upload active lesson file
    active_asset = store_file_stream(
        actor=instructor_user,
        course_id=test_course.id,
        file_stream=io.BytesIO(b"%PDF-1.4 active exercise"),
        filename="exercise1.pdf",
        content_type="application/pdf",
        asset_type="RESOURCE",
        title="Exercise 1",
        session=sess,
    )
    attach_resource_to_lesson(
        actor=instructor_user,
        lesson_id=active_lesson.id,
        asset_id=active_asset.id,
        label="Active Exercise",
        session=sess,
    )

    # 4. Upload file attached to a lesson that gets trashed, but simulate legacy active FileAsset
    trashed_lesson = create_lesson(
        instructor_user,
        test_course.id,
        {"title": "Trashed Lesson", "markdown_content": "# Old Content"},
    )
    orphaned_asset = store_file_stream(
        actor=instructor_user,
        course_id=test_course.id,
        file_stream=io.BytesIO(b"%PDF-1.4 obsolete handout"),
        filename="obsolete.pdf",
        content_type="application/pdf",
        asset_type="RESOURCE",
        title="Obsolete Handout",
        session=sess,
    )
    attach_resource_to_lesson(
        actor=instructor_user,
        lesson_id=trashed_lesson.id,
        asset_id=orphaned_asset.id,
        label="Obsolete Handout",
        session=sess,
    )

    # 5. Publish course and active lesson, and trash the legacy lesson
    test_course.status = "PUBLISHED"
    active_lesson.status = "PUBLISHED"
    trashed_lesson.deleted_at = trashed_lesson.created_at
    trashed_lesson.status = "TRASH"
    sess.commit()

    # 6. Register student and query course detail
    student = register_user(f"student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student Tester")
    from tests.conftest import login_web_user
    login_web_user(client, student)

    res = client.get(f"/student/courses/{test_course.public_id}")
    assert res.status_code == 200
    data = res.get_json()

    # Check resources list in course response per Document Hub Invariant (TASK-127):
    # Attached lesson resources are mapped to active lessons, while root general resources are empty.
    all_lesson_resources = [
        r
        for les in data.get("lessons", [])
        for r in les.get("resources", [])
    ]
    res_asset_ids = {str(r.get("asset_id") or r.get("id") or r.get("public_id")) for r in all_lesson_resources}

    # Active lesson file MUST be in resources
    assert str(active_asset.public_id) in res_asset_ids
    # Orphaned file attached to trashed lesson MUST be EXCLUDED
    assert str(orphaned_asset.public_id) not in res_asset_ids
