"""Adversarial challenger test suite for Milestone 3 (R3).

Tests:
1. Question Type Validation & In-Place Edit:
   - SINGLE_CHOICE: verify rejection if 0 or >1 correct choice, or <2 choices.
   - MULTIPLE_CHOICE: verify rejection if 0 correct choices (JSON and form), or <2 choices.
   - TRUE_FALSE: verify rejection if choice count != 2, or both true/false.
   - SHORT_ANSWER: case-insensitive matching & whitespace handling (NORMALIZED & EXACT modes).
   - Question revision branching: when question is in assessment with attempt started,
     verify direct edit blocked by Invariant 14 (409); QuestionBank update creates rev 2
     while historical attempt preserves original revision 1 snapshot.
2. Document Import Pipeline:
   - Valid DOCX upload to draft assessment -> auto-assigned with source_type='IMPORT'.
   - Valid PDF upload to draft assessment -> auto-assigned with source_type='IMPORT'.
   - Invalid/empty/corrupt files -> verify graceful rejection (400/409) WITHOUT any 500 errors:
     * Non-docx/pdf extension -> 400
     * Missing file -> 400
     * 0-byte empty file -> 400
     * Corrupted DOCX (invalid zip bytes) -> 400
     * Corrupted PDF (invalid stream bytes) -> 400
     * Valid DOCX with no question patterns -> 400
     * Upload to assessment with attempt started -> 409
"""

from __future__ import annotations

import io
import uuid
import zipfile
from datetime import timedelta
from decimal import Decimal

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.assessment import Assessment, AssessmentQuestionAssignment
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.question_bank import Question, QuestionRevision
from pwd301.models.types import utc_now
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.question_bank_service import (
    create_question,
    update_question,
)
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


def create_sample_docx(paragraphs: list[str]) -> bytes:
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
    u = register_user(f"m3_ch_inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "M3 Inst")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user(f"m3_ch_stud_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "M3 Stud")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    crs = create_course(
        instructor_user,
        {
            "course_code": f"CHAL-{uuid.uuid4().hex[:6].upper()}",
            "title": "M3 Challenger Course",
            "summary": "Course for challenging assessment authoring",
        },
        session=db.session,
    )
    crs.status = "PUBLISHED"
    db.session.commit()
    return crs


@pytest.fixture
def test_assessment(app: Flask, instructor_user: User, test_course: Course) -> Assessment:
    now = utc_now()
    return create_assessment(
        instructor_user,
        test_course.id,
        {
            "title": "Challenger Draft Assessment",
            "assessment_type": "QUIZ",
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(days=2)).isoformat(),
            "time_limit_minutes": 60,
            "passing_percent": 50.0,
        },
        session=db.session,
    )


def test_single_choice_validation_rejects_zero_or_multiple_correct(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    login_web_user(client, instructor_user)
    url = f"/instructor/assessments/{test_assessment.public_id}/questions/create"

    # 0 correct choices -> 400
    res_zero = client.post(
        url,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Capital of Japan?",
            "points": 1.0,
            "choices": [
                {"content": "Tokyo", "is_correct": False},
                {"content": "Kyoto", "is_correct": False},
            ],
        },
    )
    assert res_zero.status_code == 400
    err_msg = res_zero.get_json()["error"]["message"]
    assert "exactly 1 correct answer" in err_msg

    # >1 correct choices (2 correct) -> 400
    res_multi = client.post(
        url,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Capital of Japan?",
            "points": 1.0,
            "choices": [
                {"content": "Tokyo", "is_correct": True},
                {"content": "Kyoto", "is_correct": True},
            ],
        },
    )
    assert res_multi.status_code == 400
    err_msg = res_multi.get_json()["error"]["message"]
    assert "exactly 1 correct answer" in err_msg

    # <2 choices -> 400
    res_few = client.post(
        url,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Capital of Japan?",
            "points": 1.0,
            "choices": [{"content": "Tokyo", "is_correct": True}],
        },
    )
    assert res_few.status_code == 400
    err_msg = res_few.get_json()["error"]["message"]
    assert "at least 2 choices" in err_msg

    # Exactly 1 correct -> 201
    res_valid = client.post(
        url,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Capital of Japan?",
            "points": 2.0,
            "choices": [
                {"content": "Tokyo", "is_correct": True},
                {"content": "Kyoto", "is_correct": False},
            ],
        },
    )
    assert res_valid.status_code == 201


def test_multiple_choice_validation_rejects_zero_correct(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    login_web_user(client, instructor_user)
    url = f"/instructor/assessments/{test_assessment.public_id}/questions/create"

    # JSON 0 correct choices -> 400
    res_zero = client.post(
        url,
        json={
            "question_type": "MULTIPLE_CHOICE",
            "content": "Select prime numbers:",
            "points": 2.0,
            "choices": [
                {"content": "2", "is_correct": False},
                {"content": "3", "is_correct": False},
            ],
        },
    )
    assert res_zero.status_code == 400
    err_msg = res_zero.get_json()["error"]["message"]
    assert "at least 1 correct answer" in err_msg

    # Form submission without correct_choices selected -> 400
    res_form_zero = client.post(
        url,
        data={
            "question_type": "MULTIPLE_CHOICE",
            "content": "Select prime numbers:",
            "points": "2.0",
            "choice_content": ["2", "3", "4"],
        },
        headers={"Accept": "application/json"},
    )
    assert res_form_zero.status_code == 400

    # <2 choices -> 400
    res_few = client.post(
        url,
        json={
            "question_type": "MULTIPLE_CHOICE",
            "content": "Select prime numbers:",
            "points": 2.0,
            "choices": [{"content": "2", "is_correct": True}],
        },
    )
    assert res_few.status_code == 400

    # Valid MULTIPLE_CHOICE -> 201
    res_valid = client.post(
        url,
        json={
            "question_type": "MULTIPLE_CHOICE",
            "content": "Select prime numbers:",
            "points": 3.0,
            "choices": [
                {"content": "2", "is_correct": True},
                {"content": "3", "is_correct": True},
                {"content": "4", "is_correct": False},
            ],
        },
    )
    assert res_valid.status_code == 201


def test_true_false_validation_requires_exactly_two_choices(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    login_web_user(client, instructor_user)
    url = f"/instructor/assessments/{test_assessment.public_id}/questions/create"

    # 3 choices -> 400
    res_three = client.post(
        url,
        json={
            "question_type": "TRUE_FALSE",
            "content": "Water freezes at 0C.",
            "points": 1.0,
            "choices": [
                {"content": "True", "is_correct": True},
                {"content": "False", "is_correct": False},
                {"content": "Maybe", "is_correct": False},
            ],
        },
    )
    assert res_three.status_code == 400
    err_msg = res_three.get_json()["error"]["message"]
    assert "exactly 2 choices" in err_msg

    # 1 choice -> 400
    res_one = client.post(
        url,
        json={
            "question_type": "TRUE_FALSE",
            "content": "Water freezes at 0C.",
            "points": 1.0,
            "choices": [{"content": "True", "is_correct": True}],
        },
    )
    assert res_one.status_code == 400
    err_msg = res_one.get_json()["error"]["message"]
    assert "exactly 2 choices" in err_msg

    # 2 choices both true -> 400
    res_both_true = client.post(
        url,
        json={
            "question_type": "TRUE_FALSE",
            "content": "Water freezes at 0C.",
            "points": 1.0,
            "choices": [
                {"content": "True", "is_correct": True},
                {"content": "False", "is_correct": True},
            ],
        },
    )
    assert res_both_true.status_code == 400
    err_msg = res_both_true.get_json()["error"]["message"]
    assert "exactly 1 correct answer" in err_msg

    # Valid TRUE_FALSE via form -> 201
    res_valid = client.post(
        url,
        data={
            "question_type": "TRUE_FALSE",
            "content": "Water freezes at 0C.",
            "points": "1.0",
            "tf_correct": "true",
        },
        headers={"Accept": "application/json"},
    )
    assert res_valid.status_code == 201


def test_short_answer_case_insensitivity_and_whitespace(
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    test_course: Course,
    test_assessment: Assessment,
) -> None:
    sess = db.session
    enroll_student(student_user, test_course.id, session=sess)
    login_web_user(client, instructor_user)
    url_create = f"/instructor/assessments/{test_assessment.public_id}/questions/create"

    res_q1 = client.post(
        url_create,
        json={
            "question_type": "SHORT_ANSWER",
            "content": "What relational database is standard in PWD301?",
            "points": 4.0,
            "accepted_answers": ["PostgreSQL", "MSSQL"],
        },
    )
    assert res_q1.status_code == 201

    publish_assessment(instructor_user, test_assessment.id, session=sess)
    attempt, lease_token = start_assessment_attempt(student_user, test_assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Submit lowercase with padded whitespace: "  postgresql  "
    save_attempt_answer(
        actor=student_user,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={"answer_text": "  postgresql  ", "client_sequence": 1},
        raw_lease_token=lease_token,
        session=sess,
    )

    sub_res = submit_assessment_attempt(
        actor=student_user,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease_token,
        session=sess,
    )
    assert sub_res["status"] in ("SUBMITTED", "GRADED")

    sess.refresh(aq)
    assert aq.current_grade is not None
    assert Decimal(str(aq.current_grade.awarded_points)) == Decimal("4.0000")

    # EXACT mode test:
    q_exact = create_question(
        actor=instructor_user,
        course_id=test_course.id,
        payload={
            "question_type": "SHORT_ANSWER",
            "content": "Enter API key token prefix (case sensitive):",
            "difficulty": "APPLY",
            "points": 5.0,
            "accepted_answers": ["BearerToken"],
            "match_type": "EXACT",
            "is_case_sensitive": True,
        },
        session=sess,
    )
    assert q_exact.current_revision.short_answer_match_mode == "EXACT"

    now = utc_now()
    asm_exact = create_assessment(
        instructor_user,
        test_course.id,
        {
            "title": "Exact Short Answer Quiz",
            "assessment_type": "QUIZ",
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(days=1)).isoformat(),
            "time_limit_minutes": 30,
            "passing_percent": 50.0,
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        asm_exact.id,
        {"question_id": q_exact.id, "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm_exact.id, session=sess)

    att_exact, token_exact = start_assessment_attempt(student_user, asm_exact.id, session=sess)
    aq_exact = att_exact.attempt_questions[0]

    save_attempt_answer(
        actor=student_user,
        attempt_id=att_exact.id,
        attempt_question_id=aq_exact.id,
        payload={"answer_text": "bearertoken", "client_sequence": 1},
        raw_lease_token=token_exact,
        session=sess,
    )
    submit_assessment_attempt(
        actor=student_user,
        attempt_id=att_exact.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token_exact,
        session=sess,
    )
    sess.refresh(aq_exact)
    assert aq_exact.current_grade is not None
    assert Decimal(str(aq_exact.current_grade.awarded_points)) == Decimal("0.0000")


def test_question_revision_branching_preserves_historical_attempt(
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    test_course: Course,
    test_assessment: Assessment,
) -> None:
    sess = db.session
    enroll_student(student_user, test_course.id, session=sess)
    login_web_user(client, instructor_user)

    url_create = f"/instructor/assessments/{test_assessment.public_id}/questions/create"
    res_q = client.post(
        url_create,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Revision Branching Test Stem v1",
            "points": 3.0,
            "explanation": "Explanation v1",
            "choices": [
                {"content": "Original Correct Choice", "is_correct": True, "position": 1},
                {"content": "Original Wrong Choice", "is_correct": False, "position": 2},
            ],
        },
    )
    assert res_q.status_code == 201
    q_public_id = res_q.get_json()["question"]["question_id"]

    q_obj = sess.query(Question).filter(Question.public_id == uuid.UUID(q_public_id)).one()
    rev1 = q_obj.current_revision
    assert rev1.revision_no == 1
    assert rev1.is_current is True

    publish_assessment(instructor_user, test_assessment.id, session=sess)
    attempt, lease_token = start_assessment_attempt(student_user, test_assessment.id, session=sess)
    aq = attempt.attempt_questions[0]
    assert aq.source_question_revision_id == rev1.id
    assert aq.content_snapshot == "Revision Branching Test Stem v1"

    submit_assessment_attempt(
        actor=student_user,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease_token,
        session=sess,
    )

    # In-place edit on frozen assessment must fail with 409
    url_edit = f"/instructor/assessments/{test_assessment.public_id}/questions/{q_public_id}/edit"
    res_edit_blocked = client.post(
        url_edit,
        json={"content": "Attempted In-Place Mutation on Frozen Assessment"},
    )
    assert res_edit_blocked.status_code == 409

    # Update question in QuestionBank (in-use branching)
    update_question(
        actor=instructor_user,
        question_id=q_obj.id,
        payload={
            "content": "Revision Branching Updated Stem v2",
            "explanation": "Updated explanation v2",
            "change_reason": "Curriculum update for subsequent exams",
            "correction_type": "CONTENT_OR_CHOICES",
            "choices": [
                {"content": "New Option Alpha", "is_correct": True, "position": 1},
                {"content": "New Option Beta", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )

    sess.expire_all()
    revisions = (
        sess.query(QuestionRevision)
        .filter(QuestionRevision.question_id == q_obj.id)
        .order_by(QuestionRevision.revision_no)
        .all()
    )
    assert len(revisions) == 2
    r1, r2 = revisions[0], revisions[1]
    assert r1.revision_no == 1
    assert r1.is_current is False
    assert r2.revision_no == 2
    assert r2.is_current is True
    assert r2.content == "Revision Branching Updated Stem v2"

    # Historical attempt retains Revision 1 snapshot intact!
    sess.refresh(aq)
    assert aq.source_question_revision_id == r1.id
    assert aq.content_snapshot == "Revision Branching Test Stem v1"
    assert aq.source_question_revision.content == "Revision Branching Test Stem v1"


def test_document_import_auto_assignment_to_draft_assessment(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    login_web_user(client, instructor_user)
    import_url = f"/instructor/assessments/{test_assessment.public_id}/import"

    # 1. DOCX upload
    docx_bytes = create_sample_docx(
        [
            "Question 1: Which protocol operates at the Transport layer?",
            "A. TCP",
            "B. IP",
            "C. HTTP",
            "D. Ethernet",
            "Answer: A",
        ]
    )
    res_docx = client.post(
        import_url,
        data={
            "file": (
                io.BytesIO(docx_bytes),
                "transport.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        content_type="multipart/form-data",
    )
    assert res_docx.status_code in (201, 302)

    assignments_1 = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == test_assessment.id)
        .all()
    )
    assert len(assignments_1) == 1
    assert assignments_1[0].source_type == "IMPORT"
    assert "Transport" in assignments_1[0].question.current_revision.content

    # 2. PDF upload
    pdf_bytes = create_sample_pdf(
        [
            "Question 2: What is the default port for DNS?",
            "A. 53",
            "B. 80",
            "C. 443",
            "D. 22",
            "Answer: A",
        ]
    )
    res_pdf = client.post(
        import_url,
        data={"file": (io.BytesIO(pdf_bytes), "dns.pdf", "application/pdf")},
        content_type="multipart/form-data",
    )
    assert res_pdf.status_code in (201, 302)

    assignments_2 = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == test_assessment.id)
        .all()
    )
    assert len(assignments_2) == 2
    for a in assignments_2:
        assert a.source_type == "IMPORT"


def test_document_import_graceful_rejection_no_500_errors(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    login_web_user(client, instructor_user)
    import_url = f"/instructor/assessments/{test_assessment.public_id}/import"

    # Case 1: Missing file in request -> MUST NOT return 500
    res_missing = client.post(import_url, data={}, content_type="multipart/form-data")
    assert res_missing.status_code != 500, "Missing file caused 500 Internal Server Error!"
    assert res_missing.status_code == 400

    # Case 2: Unsupported extension (.txt) -> MUST NOT return 500
    res_txt = client.post(
        import_url,
        data={"file": (io.BytesIO(b"some plain text"), "notes.txt", "text/plain")},
        content_type="multipart/form-data",
    )
    assert res_txt.status_code != 500, "Unsupported extension caused 500 Internal Server Error!"
    assert res_txt.status_code == 400

    # Case 3: Empty 0-byte file -> MUST NOT return 500
    res_empty = client.post(
        import_url,
        data={
            "file": (
                io.BytesIO(b""),
                "empty.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        content_type="multipart/form-data",
    )
    assert res_empty.status_code != 500, "Empty file caused 500 Internal Server Error!"
    assert res_empty.status_code == 400

    # Case 4: Corrupted DOCX (random garbage bytes) -> MUST NOT return 500
    garbage_bytes = b"\x00\xff\xfe\xca\xfe\xba\xbe" * 50
    res_corrupt_docx = client.post(
        import_url,
        data={
            "file": (
                io.BytesIO(garbage_bytes),
                "corrupt.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        content_type="multipart/form-data",
    )
    assert res_corrupt_docx.status_code != 500, "Corrupted DOCX caused 500 Internal Server Error!"
    assert res_corrupt_docx.status_code == 400

    # Case 5: Corrupted PDF (random garbage bytes) -> MUST NOT return 500
    res_corrupt_pdf = client.post(
        import_url,
        data={"file": (io.BytesIO(garbage_bytes), "corrupt.pdf", "application/pdf")},
        content_type="multipart/form-data",
    )
    assert res_corrupt_pdf.status_code != 500, "Corrupted PDF caused 500 Internal Server Error!"
    assert res_corrupt_pdf.status_code == 400

    # Case 6: Valid DOCX file with zero question patterns -> MUST NOT return 500
    prose_docx = create_sample_docx(
        [
            "Introduction to Computer Science.",
            "This is an introductory chapter on computational thinking.",
            "There are no exam questions in this syllabus section.",
        ]
    )
    res_no_q = client.post(
        import_url,
        data={
            "file": (
                io.BytesIO(prose_docx),
                "prose.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        content_type="multipart/form-data",
    )
    assert res_no_q.status_code != 500, "Prose DOCX caused 500 Internal Server Error!"
    assert res_no_q.status_code == 400
    assert "question structures could be identified" in res_no_q.get_json()["error"]["message"]

    # Case 7: Assessment structural freeze blocks import (HTTP 409 Conflict) -> MUST NOT return 500
    test_assessment.first_attempt_started_at = utc_now()
    db.session.commit()

    valid_docx = create_sample_docx(["Question 1: Test?", "A. 1", "B. 2", "Answer: A"])
    res_frozen = client.post(
        import_url,
        data={
            "file": (
                io.BytesIO(valid_docx),
                "freeze.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        content_type="multipart/form-data",
    )
    assert res_frozen.status_code != 500, "Frozen assessment caused 500 Internal Server Error!"
    assert res_frozen.status_code == 409


def test_direct_authoring_validation_error_no_500_errors(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Verify that client validation errors during direct question authoring or editing

    return HTTP 400 Bad Request and DO NOT crash with HTTP 500 Internal Server Error:
    1. Empty content / prompt -> MUST return 400, NOT 500.
    2. Invalid negative / zero points -> MUST return 400, NOT 500.
    3. Invalid question type -> MUST return 400, NOT 500.
    """
    login_web_user(client, instructor_user)
    url_create = f"/instructor/assessments/{test_assessment.public_id}/questions/create"

    # Case 1: Empty content
    res_empty_content = client.post(
        url_create,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "   ",
            "points": 1.0,
            "choices": [
                {"content": "A", "is_correct": True},
                {"content": "B", "is_correct": False},
            ],
        },
    )
    assert res_empty_content.status_code != 500, "Empty content caused 500 Internal Server Error!"
    assert res_empty_content.status_code == 400

    # Case 2: Negative points
    res_neg_points = client.post(
        url_create,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Valid Question?",
            "points": -2.0,
            "choices": [
                {"content": "A", "is_correct": True},
                {"content": "B", "is_correct": False},
            ],
        },
    )
    assert res_neg_points.status_code != 500, "Negative points caused 500 Internal Server Error!"
    assert res_neg_points.status_code == 400

    # Case 3: Invalid question type
    res_bad_type = client.post(
        url_create,
        json={
            "question_type": "UNSUPPORTED_TYPE_XYZ",
            "content": "Valid Question?",
            "points": 1.0,
        },
    )
    assert res_bad_type.status_code != 500, (
        "Invalid question type caused 500 Internal Server Error!"
    )
    assert res_bad_type.status_code == 400


def test_html_form_validation_errors_redirect_with_flash(
    client: FlaskClient, instructor_user: User, test_assessment: Assessment
) -> None:
    """Verify that validation errors return 400 Bad Request JSON envelopes gracefully."""
    login_web_user(client, instructor_user)

    # 1. Create Question with empty content returns 400 JSON
    create_url = f"/instructor/assessments/{test_assessment.public_id}/questions/create"
    res_create = client.post(
        create_url,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "   ",
            "points": 1.0,
        },
    )
    assert res_create.status_code == 400
    assert "error" in res_create.get_json()

    # 2. Edit Question with negative points returns 400 JSON
    res_valid_create = client.post(
        create_url,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Valid Question?",
            "points": 1.0,
            "choices": [
                {"content": "A", "is_correct": True},
                {"content": "B", "is_correct": False},
            ],
        },
    )
    assert res_valid_create.status_code == 201
    q_id = res_valid_create.get_json()["question"]["question_id"]

    edit_url = f"/instructor/assessments/{test_assessment.public_id}/questions/{q_id}/edit"
    res_edit = client.post(
        edit_url,
        json={"points": -5.0},
    )
    assert res_edit.status_code == 400
    assert "error" in res_edit.get_json()

    # 3. Import Document with missing file returns 400 JSON
    import_url = f"/instructor/assessments/{test_assessment.public_id}/import"
    res_import = client.post(
        import_url,
        data={},
        content_type="multipart/form-data",
    )
    assert res_import.status_code == 400
    assert "error" in res_import.get_json()
