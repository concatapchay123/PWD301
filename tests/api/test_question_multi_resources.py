"""API and Service tests for Question Bank multi-image resources support."""

from __future__ import annotations

import io
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.file_import import FileAsset, QuestionRevisionResource
from pwd301.models.identity import Role, User
from pwd301.models.question_bank import Question
from pwd301.services.course_service import create_course
from pwd301.services.file_service import store_file_stream
from pwd301.services.question_bank_service import (
    create_question,
    create_question_revision,
    get_question_detail,
    update_question,
)
from pwd301.services.user_service import assign_role_to_user, register_user


def test_question_multi_resources_create_clone_and_update(app: Flask) -> None:
    sess: Session = db.session

    for code, name in [("STUDENT", "Student"), ("INSTRUCTOR", "Instructor"), ("ADMIN", "Admin")]:
        if not sess.query(Role).filter(Role.code == code).first():
            sess.add(Role(code=code, name=name))
    sess.commit()

    instructor = register_user("multi_res_inst@example.com", "Password@123", "Resource Inst")
    instructor = assign_role_to_user(instructor.id, "INSTRUCTOR")
    course = create_course(instructor, {"course_code": "CS-IMG1", "title": "Image Course"})

    # Create 2 dummy image file assets
    file_bytes_1 = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    file_bytes_2 = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x02\x08\x06\x00\x00\x00\x1f\x15c4"

    asset_1 = store_file_stream(
        actor=instructor,
        course_id=course.id,
        filename="diagram1.png",
        file_stream=io.BytesIO(file_bytes_1),
        content_type="image/png",
        session=sess,
    )
    asset_2 = store_file_stream(
        actor=instructor,
        course_id=course.id,
        filename="diagram2.png",
        file_stream=io.BytesIO(file_bytes_2),
        content_type="image/png",
        session=sess,
    )

    # 1. Create Question with 2 resources
    payload = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "APPLY",
        "content": "Quan sát sơ đồ dưới đây và chọn đáp án đúng [[PWD301:EXTRACTED_IMAGE:1]]",
        "choices": [
            {"content": "Đáp án A", "is_correct": True, "position": 1},
            {"content": "Đáp án B", "is_correct": False, "position": 2},
        ],
        "resources": [
            {"asset_id": str(asset_1.public_id), "position": 1, "resource_role": "IMAGE"},
            {"asset_id": str(asset_2.public_id), "position": 2, "resource_role": "IMAGE"},
        ],
    }

    q = create_question(instructor, course.id, payload, session=sess)
    assert q.id is not None
    assert len(q.current_revision.resources) == 2

    # 2. Verify get_question_detail includes serialized resources
    detail = get_question_detail(instructor, q.id, session=sess)
    assert "resources" in detail
    assert len(detail["resources"]) == 2
    assert detail["resources"][0]["asset_id"] == str(asset_1.public_id)
    assert detail["resources"][0]["filename"] == "diagram1.png"
    assert detail["resources"][0]["download_url"] == f"/instructor/files/{asset_1.public_id}/download"
    assert detail["resources"][1]["asset_id"] == str(asset_2.public_id)

    # 3. Test clone resources when creating revision without specifying resources
    rev_payload = {
        "content": "Quan sát sơ đồ đã cập nhật và chọn đáp án đúng",
        "change_reason": "Sửa câu chữ",
        "choices": [
            {"content": "Đáp án A mới", "is_correct": True, "position": 1},
            {"content": "Đáp án B mới", "is_correct": False, "position": 2},
        ],
    }
    new_rev, _ = create_question_revision(instructor, q.id, rev_payload, session=sess)
    assert new_rev.revision_no == 2
    assert len(new_rev.resources) == 2
    assert {r.file_asset_id for r in new_rev.resources} == {asset_1.id, asset_2.id}

    # 4. In-place update resources
    update_payload = {
        "content": "Chỉ còn 1 sơ đồ",
        "resources": [
            {"asset_id": str(asset_2.public_id), "position": 1, "resource_role": "IMAGE"},
        ],
    }
    update_question(instructor, q.id, update_payload, session=sess)
    detail_updated = get_question_detail(instructor, q.id, session=sess)
    assert len(detail_updated["resources"]) == 1
    assert detail_updated["resources"][0]["asset_id"] == str(asset_2.public_id)


def test_batch_create_assessment_questions_with_resources(app: Flask, client: FlaskClient) -> None:
    from pwd301.services.assessment_service import create_assessment
    from tests.conftest import login_web_user

    sess: Session = db.session

    for code, name in [("STUDENT", "Student"), ("INSTRUCTOR", "Instructor"), ("ADMIN", "Admin")]:
        if not sess.query(Role).filter(Role.code == code).first():
            sess.add(Role(code=code, name=name))
    sess.commit()

    instructor = register_user("batch_res_inst@example.com", "Password@123", "Batch Inst")
    instructor = assign_role_to_user(instructor.id, "INSTRUCTOR")
    course = create_course(instructor, {"course_code": "CS-BATCH1", "title": "Batch Course"})

    assessment = create_assessment(
        instructor,
        course.id,
        {
            "title": "Kiểm tra Batch Image",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 30,
            "max_attempts": 1,
        },
        session=sess,
    )

    # Create dummy image file asset
    file_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    asset = store_file_stream(
        actor=instructor,
        course_id=course.id,
        filename="batch_img.png",
        file_stream=io.BytesIO(file_bytes),
        content_type="image/png",
        session=sess,
    )

    login_web_user(client, instructor)
    with client.session_transaction() as session_data:
        session_data["active_role"] = "INSTRUCTOR"

    batch_payload = {
        "questions": [
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "Câu 1 kèm ảnh [[PWD301:EXTRACTED_IMAGE:1]]",
                "points": 2.0,
                "choices": [
                    {"content": "Đáp án 1", "is_correct": True, "position": 1},
                    {"content": "Đáp án 2", "is_correct": False, "position": 2},
                ],
                "resources": [
                    {"asset_id": str(asset.public_id), "position": 1, "resource_role": "IMAGE"}
                ],
            }
        ]
    }

    res = client.post(
        f"/instructor/assessments/{assessment.public_id}/questions/batch",
        json=batch_payload,
    )
    assert res.status_code == 201
    res_data = res.get_json()
    assert res_data["success"] is True
    assert len(res_data["data"]) == 1

    created_q_id = res_data["data"][0]["question_id"]
    q_detail = get_question_detail(instructor, created_q_id, session=sess)
    assert len(q_detail["resources"]) == 1
    assert q_detail["resources"][0]["asset_id"] == str(asset.public_id)

