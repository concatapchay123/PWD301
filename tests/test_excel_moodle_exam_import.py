"""Tests for Excel and Moodle XML/JSON exam import services and instructor endpoints."""

import io
import json
import pytest

from pwd301.extensions import db
from pwd301.services.excel_exam_service import generate_excel_exam_template, parse_excel_exam
from pwd301.services.moodle_exam_service import (
    generate_moodle_sample_xml,
    generate_sample_json,
    parse_moodle_json,
    parse_moodle_xml,
)
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


def _setup_instructor(email="inst_excel_test@test.edu"):
    user = register_user(
        email,
        "ValidPassword123!",
        "Instructor Excel Test",
        session=db.session,
    )
    assign_role_to_user(
        user.id,
        "INSTRUCTOR",
        session=db.session,
    )
    db.session.commit()
    return user


def test_excel_template_generation_and_parsing():
    """Verify generated Excel template can be parsed back with 100% accuracy."""
    template_bytes = generate_excel_exam_template()
    assert len(template_bytes) > 1000

    result = parse_excel_exam(template_bytes)
    assert result["success"] is True
    assert result["total_questions"] == 4
    assert result["total_points"] >= 4.0

    # Question 1: Single Choice (HTTPS)
    q1 = result["questions"][0]
    assert q1["type"] == "SINGLE_CHOICE"
    assert "SSL/TLS" in q1["stem"]
    correct_choices = [c for c in q1["choices"] if c["is_correct"]]
    assert len(correct_choices) == 1
    assert correct_choices[0]["label"] == "B"
    assert correct_choices[0]["content"] == "HTTPS"

    # Question 2: Multiple Choice
    q2 = result["questions"][1]
    assert q2["type"] == "MULTIPLE_CHOICE"
    assert sum(1 for c in q2["choices"] if c["is_correct"]) == 3

    # Question 3: True / False
    q3 = result["questions"][2]
    assert q3["type"] == "TRUE_FALSE"

    # Question 4: Short Answer
    q4 = result["questions"][3]
    assert q4["type"] == "SHORT_ANSWER"
    assert "JWT" in q4["accepted_answers"]


def test_moodle_xml_parsing():
    """Verify standard Moodle XML parsing parses multichoice, truefalse, shortanswer."""
    sample_xml = generate_moodle_sample_xml()
    result = parse_moodle_xml(sample_xml)
    assert result["success"] is True
    assert result["total_questions"] == 4

    q1 = result["questions"][0]
    assert q1["type"] == "SINGLE_CHOICE"
    assert any(c["label"] == "B" and c["is_correct"] for c in q1["choices"])

    q2 = result["questions"][1]
    assert q2["type"] == "MULTIPLE_CHOICE"

    q3 = result["questions"][2]
    assert q3["type"] == "TRUE_FALSE"

    q4 = result["questions"][3]
    assert q4["type"] == "SHORT_ANSWER"
    assert "JWT" in q4["accepted_answers"]


def test_moodle_json_parsing():
    """Verify standardized JSON question bank parsing."""
    sample_json = generate_sample_json()
    result = parse_moodle_json(sample_json)
    assert result["success"] is True
    assert result["total_questions"] == 4
    assert result["questions"][0]["type"] == "SINGLE_CHOICE"
    assert result["questions"][1]["type"] == "MULTIPLE_CHOICE"
    assert result["questions"][2]["type"] == "TRUE_FALSE"
    assert result["questions"][3]["type"] == "SHORT_ANSWER"


def test_excel_endpoints(client, app):
    """Verify GET /instructor/exams/excel-template and POST /instructor/exams/parse-excel."""
    with app.app_context():
        user = _setup_instructor("inst_endpoint_excel@test.edu")
        login_web_user(client, user)

    # 1. Download template
    tmpl_res = client.get("/instructor/exams/excel-template")
    assert tmpl_res.status_code == 200
    assert "application/vnd.openxmlformats" in tmpl_res.content_type
    excel_bytes = tmpl_res.data
    assert len(excel_bytes) > 500

    # 2. Upload template to parse-excel
    upload_res = client.post(
        "/instructor/exams/parse-excel",
        data={
            "file": (io.BytesIO(excel_bytes), "de_thi_test.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        },
        content_type="multipart/form-data",
    )
    assert upload_res.status_code == 200
    data = upload_res.get_json()
    assert data["success"] is True
    assert data["total_questions"] == 4
    assert data["filename"] == "de_thi_test.xlsx"


def test_moodle_xml_endpoints(client, app):
    """Verify POST /instructor/exams/parse-moodle-xml and sample download."""
    with app.app_context():
        user = _setup_instructor("inst_endpoint_xml@test.edu")
        login_web_user(client, user)

    # 1. Download XML sample
    sample_res = client.get("/instructor/exams/samples/moodle-xml")
    assert sample_res.status_code == 200
    xml_str = sample_res.data.decode("utf-8")
    assert "<quiz>" in xml_str

    # 2. Parse via JSON body
    post_res = client.post(
        "/instructor/exams/parse-moodle-xml",
        json={"xml": xml_str},
    )
    assert post_res.status_code == 200
    data = post_res.get_json()
    assert data["success"] is True
    assert data["total_questions"] == 4

    # 3. Parse via multipart file upload
    post_file_res = client.post(
        "/instructor/exams/parse-moodle-xml",
        data={
            "file": (io.BytesIO(xml_str.encode("utf-8")), "moodle.xml", "application/xml")
        },
        content_type="multipart/form-data",
    )
    assert post_file_res.status_code == 200
    assert post_file_res.get_json()["success"] is True


def test_json_endpoints(client, app):
    """Verify POST /instructor/exams/parse-json and sample download."""
    with app.app_context():
        user = _setup_instructor("inst_endpoint_json@test.edu")
        login_web_user(client, user)

    # 1. Download JSON sample
    sample_res = client.get("/instructor/exams/samples/json")
    assert sample_res.status_code == 200
    json_str = sample_res.data.decode("utf-8")
    parsed_dict = json.loads(json_str)
    assert "questions" in parsed_dict

    # 2. Parse via POST body
    post_res = client.post(
        "/instructor/exams/parse-json",
        json=parsed_dict,
    )
    assert post_res.status_code == 200
    data = post_res.get_json()
    assert data["success"] is True
    assert data["total_questions"] == 4
