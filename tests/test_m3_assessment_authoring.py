"""Integration test suite for Milestone 3 (R3): Assessment Page Question Authoring,
Direct Editing & Document Import.

Tests:
1. Direct in-page question creation for all 4 types (SINGLE_CHOICE, MULTIPLE_CHOICE,
   TRUE_FALSE, SHORT_ANSWER).
2. In-place question content editing and point editing.
3. PDF and DOCX document upload and auto-assignment to draft assessment.
4. Invariant 13 (Timing Lock): timing parameters locked after publish; forward close_at extension.
5. Invariant 14 (Structural Freeze): question creation, editing, removal, points modification,
   and import strictly rejected with 409 AssessmentLockedError once first_attempt_started_at is set.
"""

from __future__ import annotations

import io
import zipfile
from datetime import timedelta

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment, AssessmentQuestionAssignment
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.assessment_service import (
    create_assessment,
    publish_assessment,
    update_assessment,
)
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import AssessmentLockedError
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


def create_sample_docx(paragraphs: list[str]) -> bytes:
    """Generate in-memory valid OpenXML DOCX bytes with given paragraphs."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        p_elements = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
            f"  <w:body>{p_elements}</w:body>\n"
            "</w:document>"
        )
        zf.writestr("word/document.xml", doc_xml.encode("utf-8"))
    return buffer.getvalue()


def create_sample_pdf(lines: list[str]) -> bytes:
    """Generate in-memory valid PDF bytes with given text lines."""
    text_commands = "\n".join(f"({line}) Tj T*" for line in lines)
    stream_bytes = f"BT /F1 12 Tf 50 700 Td 14 TL\n{text_commands}\nET".encode("latin-1")
    length = len(stream_bytes)
    pdf_content = (
        f"%PDF-1.4\n"
        f"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        f"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        f"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        f"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        f"4 0 obj << /Length {length} >>\nstream\n"
        f"{stream_bytes.decode('latin-1')}\nendstream\nendobj\n"
        f"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        f"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        f"0000000115 00000 n \n0000000234 00000 n \n0000000300 00000 n \n"
        f"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n380\n%%EOF\n"
    )
    return pdf_content.encode("latin-1")


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
    u = register_user("m3_instructor@example.com", "Password@123", "M3 Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create a course managed by instructor."""
    return create_course(
        instructor_user,
        {
            "course_code": f"M3-CRS-{instructor_user.id}",
            "title": "Milestone 3 Testing Course",
            "summary": "Course for testing assessment authoring",
        },
        session=db.session,
    )


@pytest.fixture
def test_assessment(app: Flask, instructor_user: User, test_course: Course) -> Assessment:
    """Create a draft assessment for testing."""
    now = utc_now()
    asm = create_assessment(
        instructor_user,
        test_course.id,
        {
            "title": "M3 Midterm Assessment",
            "assessment_type": "MIDTERM",
            "open_at": (now + timedelta(days=1)).isoformat(),
            "close_at": (now + timedelta(days=3)).isoformat(),
            "time_limit_minutes": 60,
            "passing_percent": 60.0,
        },
        session=db.session,
    )
    return asm


# ============================================================================
# 1. DIRECT IN-PAGE QUESTION CREATION (ALL 4 TYPES)
# ============================================================================


def test_direct_question_creation_single_choice(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Test creating a SINGLE_CHOICE question directly on assessment page."""
    login_web_user(client, instructor_user)

    url = f"/instructor/assessments/{test_assessment.public_id}/questions/create"
    payload = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "UNDERSTAND",
        "points": 2.5,
        "content": "What is the capital of Vietnam?",
        "explanation": "Hanoi is the official capital of Vietnam.",
        "choices": [
            {"content": "Hanoi", "is_correct": True, "position": 1},
            {"content": "Ho Chi Minh City", "is_correct": False, "position": 2},
            {"content": "Da Nang", "is_correct": False, "position": 3},
            {"content": "Hue", "is_correct": False, "position": 4},
        ],
    }

    res = client.post(url, json=payload)
    assert res.status_code == 201, res.get_data(as_text=True)
    body = res.get_json()
    assert body["message"] == "Question created and assigned successfully."
    assert body["assignment"]["points"] == 2.5

    # Verify assignment in DB
    assignment = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == test_assessment.id)
        .first()
    )
    assert assignment is not None
    assert float(assignment.points) == 2.5
    assert assignment.question.current_revision.question_type == "SINGLE_CHOICE"
    assert assignment.question.current_revision.content == "What is the capital of Vietnam?"
    assert len(assignment.question.current_revision.choices) == 4
    correct_choices = [c for c in assignment.question.current_revision.choices if c.is_correct]
    assert len(correct_choices) == 1
    assert correct_choices[0].content == "Hanoi"


def test_direct_question_creation_multiple_choice_form(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Test creating a MULTIPLE_CHOICE question via API."""
    login_web_user(client, instructor_user)

    url = f"/instructor/assessments/{test_assessment.public_id}/questions/create"
    payload = {
        "question_type": "MULTIPLE_CHOICE",
        "difficulty": "APPLY",
        "points": 3.0,
        "content": "Select all primary colors in the RGB model:",
        "explanation": "Red, Green, and Blue are the primary colors.",
        "choices": [
            {"content": "Red", "is_correct": True, "position": 1},
            {"content": "Green", "is_correct": True, "position": 2},
            {"content": "Yellow", "is_correct": False, "position": 3},
            {"content": "Blue", "is_correct": True, "position": 4},
        ],
    }

    res = client.post(url, json=payload)
    assert res.status_code == 201

    # Verify DB
    assignment = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == test_assessment.id)
        .first()
    )
    assert assignment is not None
    assert float(assignment.points) == 3.0
    rev = assignment.question.current_revision
    assert rev.question_type == "MULTIPLE_CHOICE"
    assert len(rev.choices) == 4
    correct_texts = {c.content for c in rev.choices if c.is_correct}
    assert correct_texts == {"Red", "Green", "Blue"}


def test_direct_question_creation_true_false(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Test creating a TRUE_FALSE question directly on assessment page."""
    login_web_user(client, instructor_user)

    url = f"/instructor/assessments/{test_assessment.public_id}/questions/create"
    payload = {
        "question_type": "TRUE_FALSE",
        "difficulty": "REMEMBER",
        "points": 1.0,
        "content": "Python is a compiled language only.",
        "choices": [
            {"content": "Đúng", "is_correct": False, "position": 1},
            {"content": "Sai", "is_correct": True, "position": 2},
        ],
    }

    res = client.post(url, json=payload)
    assert res.status_code == 201

    assignment = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == test_assessment.id)
        .first()
    )
    assert assignment is not None
    rev = assignment.question.current_revision
    assert rev.question_type == "TRUE_FALSE"
    assert len(rev.choices) == 2
    correct_choice = next(c for c in rev.choices if c.is_correct)
    assert correct_choice.content == "Sai"


def test_direct_question_creation_short_answer(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Test creating a SHORT_ANSWER question directly on assessment page."""
    login_web_user(client, instructor_user)

    url = f"/instructor/assessments/{test_assessment.public_id}/questions/create"
    payload = {
        "question_type": "SHORT_ANSWER",
        "difficulty": "UNDERSTAND",
        "points": 1.5,
        "content": "What is the standard port for HTTPS?",
        "accepted_answers": ["443", "tcp/443"],
    }

    res = client.post(url, json=payload)
    assert res.status_code == 201

    assignment = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == test_assessment.id)
        .first()
    )
    assert assignment is not None
    assert float(assignment.points) == 1.5
    rev = assignment.question.current_revision
    assert rev.question_type == "SHORT_ANSWER"
    ans_texts = {a.answer_text for a in rev.accepted_answers}
    assert ans_texts == {"443", "tcp/443"}


# ============================================================================
# 2. IN-PLACE QUESTION & POINTS EDITING
# ============================================================================


def test_inplace_question_content_and_points_edit(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Test in-place editing of question stem, choices, explanation, and assigned points."""
    login_web_user(client, instructor_user)

    # 1. Create initial question
    create_url = f"/instructor/assessments/{test_assessment.public_id}/questions/create"
    res = client.post(
        create_url,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Initial Prompt?",
            "points": 1.0,
            "difficulty": "UNDERSTAND",
            "choices": [
                {"content": "Alpha", "is_correct": True, "position": 1},
                {"content": "Beta", "is_correct": False, "position": 2},
            ],
        },
    )
    assert res.status_code == 201
    q_public_id = res.get_json()["question"]["question_id"]

    # 2. Edit points and content via edit endpoint
    edit_url = f"/instructor/assessments/{test_assessment.public_id}/questions/{q_public_id}/edit"
    edit_payload = {
        "points": 3.5,
        "content": "Updated Prompt Question?",
        "explanation": "Updated explanation.",
        "choices": [
            {"content": "Alpha Modified", "is_correct": False, "position": 1},
            {"content": "Beta Modified", "is_correct": True, "position": 2},
        ],
    }
    res_edit = client.post(edit_url, json=edit_payload)
    assert res_edit.status_code == 200

    # 3. Verify in DB
    assignment = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == test_assessment.id)
        .first()
    )
    assert assignment is not None
    assert float(assignment.points) == 3.5
    rev = assignment.question.current_revision
    assert rev.content == "Updated Prompt Question?"
    assert rev.explanation == "Updated explanation."
    correct_ch = next(c for c in rev.choices if c.is_correct)
    assert correct_ch.content == "Beta Modified"


def test_inplace_points_quick_edit_form(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Test quick inline points update form without modifying question content."""
    login_web_user(client, instructor_user)

    create_url = f"/instructor/assessments/{test_assessment.public_id}/questions/create"
    res = client.post(
        create_url,
        json={
            "question_type": "TRUE_FALSE",
            "content": "Earth is round.",
            "points": 1.0,
            "choices": [
                {"content": "Đúng", "is_correct": True, "position": 1},
                {"content": "Sai", "is_correct": False, "position": 2},
            ],
        },
    )
    q_public_id = res.get_json()["question"]["question_id"]

    # API submit with only points
    edit_url = f"/instructor/assessments/{test_assessment.public_id}/questions/{q_public_id}/edit"
    res_form = client.post(edit_url, json={"points": 4.5})
    assert res_form.status_code == 200

    assignment = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == test_assessment.id)
        .first()
    )
    assert float(assignment.points) == 4.5
    assert assignment.question.current_revision.content == "Earth is round."


# ============================================================================
# 3. DOCUMENT IMPORT (PDF / DOCX) AUTO-ASSIGNMENT
# ============================================================================


def test_docx_document_import_and_auto_assignment(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Test uploading a .docx document on assessment page parses and auto-assigns questions."""
    login_web_user(client, instructor_user)

    docx_paragraphs = [
        "Câu 1: Thủ đô của Việt Nam là gì?",
        "A. Hà Nội",
        "B. Hải Phòng",
        "C. Đà Nẵng",
        "D. Cần Thơ",
        "Đáp án: A",
        "Câu 2: Python là ngôn ngữ lập trình thông dịch.",
        "A. Đúng",
        "B. Sai",
        "Đáp án: A",
    ]
    docx_bytes = create_sample_docx(docx_paragraphs)

    import_url = f"/instructor/assessments/{test_assessment.public_id}/import"
    data = {
        "file": (
            io.BytesIO(docx_bytes),
            "test_exam.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    res = client.post(import_url, data=data, content_type="multipart/form-data")
    assert res.status_code in (201, 302)

    # Verify questions were imported and assigned to test_assessment
    assignments = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == test_assessment.id)
        .all()
    )
    assert len(assignments) >= 2
    for asm_q in assignments:
        assert asm_q.source_type == "IMPORT"
        assert float(asm_q.points) > 0


def test_pdf_document_import_and_auto_assignment(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Test uploading a .pdf document on assessment page parses and auto-assigns questions."""
    login_web_user(client, instructor_user)

    pdf_lines = [
        "Cau 1: Protocol HTTP mac dinh su dung port nao?",
        "A. 80",
        "B. 443",
        "C. 21",
        "D. 22",
        "Dap an: A",
    ]
    pdf_bytes = create_sample_pdf(pdf_lines)

    import_url = f"/instructor/assessments/{test_assessment.public_id}/import"
    data = {"file": (io.BytesIO(pdf_bytes), "exam.pdf", "application/pdf")}

    res = client.post(import_url, data=data, content_type="multipart/form-data")
    assert res.status_code in (201, 302)

    assignments = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == test_assessment.id)
        .all()
    )
    assert len(assignments) >= 1


# ============================================================================
# 4. INVARIANT 13: TIMING LOCK
# ============================================================================


def test_timing_lock_invariant_enforcement(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Test Invariant 13: Timing parameters immutable after publish; forward extension allowed."""
    # Add 1 question so assessment can be published
    url_create = f"/instructor/assessments/{test_assessment.public_id}/questions/create"
    login_web_user(client, instructor_user)
    client.post(
        url_create,
        json={
            "question_type": "TRUE_FALSE",
            "content": "Water boils at 100C.",
            "points": 1.0,
            "choices": [
                {"content": "Đúng", "is_correct": True, "position": 1},
                {"content": "Sai", "is_correct": False, "position": 2},
            ],
        },
    )

    # Publish the assessment
    publish_assessment(instructor_user, test_assessment.id, session=db.session)
    assert test_assessment.status == "PUBLISHED"
    assert test_assessment.published_at is not None

    # 1. Attempt to modify open_at -> MUST FAIL with AssessmentLockedError
    now = utc_now()
    with pytest.raises(AssessmentLockedError, match="Assessment timing .* is locked after publish"):
        update_assessment(
            instructor_user,
            test_assessment.id,
            {"open_at": (now + timedelta(days=2)).isoformat()},
            session=db.session,
        )

    # 2. Attempt to modify time_limit_minutes -> MUST FAIL with AssessmentLockedError
    with pytest.raises(AssessmentLockedError, match="Assessment timing .* is locked after publish"):
        update_assessment(
            instructor_user,
            test_assessment.id,
            {"time_limit_minutes": 90},
            session=db.session,
        )

    # 3. Extend close_at forward into the future -> MUST SUCCEED per Invariant 13 specification!
    future_close = test_assessment.close_at + timedelta(days=5)
    updated_asm = update_assessment(
        instructor_user,
        test_assessment.id,
        {"close_at": future_close.isoformat()},
        session=db.session,
    )
    assert updated_asm.close_at == future_close

    # 4. Attempt to shorten close_at -> MUST FAIL
    shortened_close = test_assessment.close_at - timedelta(days=2)
    with pytest.raises(AssessmentLockedError, match="close_at can only be extended forward"):
        update_assessment(
            instructor_user,
            test_assessment.id,
            {"close_at": shortened_close.isoformat()},
            session=db.session,
        )


# ============================================================================
# 5. INVARIANT 14: STRUCTURAL FREEZE
# ============================================================================


def test_structural_freeze_invariant_enforcement(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Test Invariant 14: Creating, editing, removing questions or points after first attempt

    is rejected with 409 AssessmentLockedError.
    """
    login_web_user(client, instructor_user)

    # Add a question first
    url_create = f"/instructor/assessments/{test_assessment.public_id}/questions/create"
    res_q = client.post(
        url_create,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Freeze Test Question?",
            "points": 2.0,
            "choices": [
                {"content": "Option 1", "is_correct": True, "position": 1},
                {"content": "Option 2", "is_correct": False, "position": 2},
            ],
        },
    )
    assert res_q.status_code == 201
    q_public_id = res_q.get_json()["question"]["question_id"]

    # Simulate first attempt started
    test_assessment.first_attempt_started_at = utc_now()
    db.session.commit()

    # 1. Direct question creation MUST be rejected with 409
    res_create = client.post(
        url_create,
        json={
            "question_type": "TRUE_FALSE",
            "content": "Post freeze question",
            "points": 1.0,
            "choices": [
                {"content": "Đúng", "is_correct": True, "position": 1},
                {"content": "Sai", "is_correct": False, "position": 2},
            ],
        },
    )
    assert res_create.status_code == 409

    # 2. In-place question content editing MUST be rejected with 409
    url_edit = f"/instructor/assessments/{test_assessment.public_id}/questions/{q_public_id}/edit"
    res_edit = client.post(url_edit, json={"content": "Mutated Content After Freeze"})
    assert res_edit.status_code == 409

    # 3. Points editing MUST be rejected with 409
    res_points = client.post(url_edit, json={"points": 5.0})
    assert res_points.status_code == 409

    # 4. Question removal MUST be rejected with 409
    asm_id = test_assessment.public_id
    url_remove = f"/instructor/assessments/{asm_id}/questions/{q_public_id}/remove"
    res_remove = client.post(url_remove, headers={"Accept": "application/json"})
    assert res_remove.status_code == 409

    # 5. Document import MUST be rejected with 409
    url_import = f"/instructor/assessments/{test_assessment.public_id}/import"
    sample_docx = create_sample_docx(["Câu 1: Đề thi sau khóa", "A. 1", "B. 2", "Đáp án: A"])
    docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    res_import = client.post(
        url_import,
        data={"file": (io.BytesIO(sample_docx), "freeze.docx", docx_mime)},
        content_type="multipart/form-data",
    )
    assert res_import.status_code == 409
