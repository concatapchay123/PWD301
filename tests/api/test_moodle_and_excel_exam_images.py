"""Tests for Moodle XML and Excel Exam Import Image Recognition."""

import io
import uuid

import openpyxl
import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.excel_exam_service import parse_excel_exam
from pwd301.services.moodle_exam_service import parse_moodle_xml
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    sess = db.session
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
    email = f"moodle_inst_{uuid.uuid4().hex[:6]}@example.com"
    u = register_user(email, "Password@123", "Moodle Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def sample_course(app: Flask, instructor_user: User) -> Course:
    course = create_course(
        actor=instructor_user,
        data={
            "course_code": f"MDL{uuid.uuid4().hex[:4].upper()}",
            "title": "Moodle Course",
            "summary": "Moodle XML Course",
        },
        session=db.session,
    )
    return course


def test_excel_exam_with_image_markers():
    """Test parse_excel_exam extracts image tokens into resources."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(
        [
            "STT",
            "Loại câu hỏi",
            "Nội dung câu hỏi",
            "Phương án A",
            "Phương án B",
            "Đáp án đúng",
            "Điểm số",
        ]
    )

    asset_id = str(uuid.uuid4())
    stem = f"Quan sát sơ đồ sau:\n[[PWD301:IMAGE:{asset_id}]]\nChọn nhận định đúng?"
    ws.append([1, "Trắc nghiệm 1 đáp án", stem, "Đúng", "Sai", "A", 1.0])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    res = parse_excel_exam(buf)
    assert res["success"] is True
    assert len(res["questions"]) == 1
    q = res["questions"][0]
    assert q["image_asset_id"] == asset_id
    assert len(q["resources"]) == 1
    assert q["resources"][0]["asset_id"] == asset_id
    assert f"/instructor/files/{asset_id}/download" in q["resources"][0]["download_url"]


def test_moodle_xml_with_embedded_base64_image(
    app, client: FlaskClient, instructor_user, sample_course
):
    """Test parse_moodle_xml extracts base64 files and the route creates FileAsset."""
    sample_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    moodle_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Câu hỏi có hình ảnh</text></name>
    <questiontext format="html">
      <text><![CDATA[<p>Xem biểu đồ:</p><p><img src="@@PLUGINFILE@@/diagram.png" alt="Diagram" /></p><p>Biểu đồ thể hiện điều gì?</p>]]></text>
      <file name="diagram.png" path="/" encoding="base64">{sample_b64}</file>
    </questiontext>
    <defaultgrade>2.0</defaultgrade>
    <single>true</single>
    <answer fraction="100" format="html"><text><![CDATA[<p>Chính xác</p>]]></text></answer>
    <answer fraction="0" format="html"><text><![CDATA[<p>Sai</p>]]></text></answer>
  </question>
</quiz>
"""
    # 1. Direct service parse
    direct_res = parse_moodle_xml(moodle_xml)
    assert direct_res["success"] is True
    assert len(direct_res["questions"]) == 1
    q = direct_res["questions"][0]
    assert len(q["extracted_files"]) == 1
    assert q["extracted_files"][0]["filename"] == "diagram.png"

    # 2. Parse via instructor API route with course_id to test FileAsset persistence
    with app.app_context():
        login_web_user(client, instructor_user)
        with client.session_transaction() as sess:
            sess["active_role"] = "INSTRUCTOR"

        resp = client.post(
            "/instructor/exams/parse-moodle-xml",
            json={"xml": moodle_xml, "course_id": sample_course.id},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["questions"]) == 1
        q_saved = data["questions"][0]
        assert q_saved["image_asset_id"] is not None
        assert len(q_saved["resources"]) == 1
        assert "[[PWD301:IMAGE:" in q_saved["stem"]


def test_moodle_xml_essay_question():
    """Test parse_moodle_xml correctly parses essay questions."""
    essay_xml = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="essay">
    <name><text>Câu hỏi tự luận</text></name>
    <questiontext format="html">
      <text><![CDATA[<p>Hãy phân tích các ưu nhược điểm của kiến trúc Microservices so với Monolith.</p>]]></text>
    </questiontext>
    <defaultgrade>5.0</defaultgrade>
    <generalfeedback format="html">
      <text><![CDATA[<p>Hướng dẫn chấm: nêu rõ khả năng mở rộng, chi phí vận hành.</p>]]></text>
    </generalfeedback>
  </question>
</quiz>
"""
    result = parse_moodle_xml(essay_xml)
    assert result["success"] is True
    assert result["total_questions"] == 1
    q = result["questions"][0]
    assert q["type"] == "ESSAY"
    assert q["question_type"] == "Tự luận"
    assert q["points"] == 5.0
    assert "Microservices" in q["stem"]
    assert "chi phí vận hành" in q["explanation"]
    assert len(q["choices"]) == 0
