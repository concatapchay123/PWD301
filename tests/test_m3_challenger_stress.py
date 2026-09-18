"""Milestone 3 Challenger Stress and Adversarial Test Suite.

Adversarially challenges:
1. Invariant 13 (Timing Lock - BR-031):
   - Publish an assessment (status == 'PUBLISHED').
   - Modify open_at, time_limit_minutes, attempt_limit -> rejected (409).
   - Extend close_at forward into future -> allowed.
   - Shorten close_at -> rejected with AssessmentLockedError / 409.
2. Invariant 14 (Structural Freeze - BR-030):
   - Simulate a started student attempt (set first_attempt_started_at).
   - Question create via POST /questions/create -> rejected (409).
   - Edit content/points via POST /questions/<id>/edit -> rejected (409).
   - Remove question via POST /questions/<id>/remove -> rejected (409).
   - Document import via POST /import -> rejected (409).
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
    assign_question,
    create_assessment,
    create_section,
    delete_section,
    publish_assessment,
    remove_question_assignment,
    update_assessment,
    update_question_assignment,
)
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import AssessmentLockedError
from pwd301.services.file_service import store_file_stream
from pwd301.services.import_service import create_import_job
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


def _make_sample_docx(paragraphs: list[str]) -> bytes:
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


def _make_sample_pdf(lines: list[str]) -> bytes:
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
def test_roles(app: Flask) -> dict[str, Role]:
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
def m3_instructor(app: Flask, test_roles: dict[str, Role]) -> User:
    user = register_user("challenger_m3_inst@example.com", "Password@123", "Challenger Instructor")
    assign_role_to_user(user.id, "INSTRUCTOR", session=db.session)
    return user


@pytest.fixture
def rogue_instructor(app: Flask, test_roles: dict[str, Role]) -> User:
    user = register_user("challenger_m3_rogue@example.com", "Password@123", "Rogue Instructor")
    assign_role_to_user(user.id, "INSTRUCTOR", session=db.session)
    return user


@pytest.fixture
def m3_student(app: Flask, test_roles: dict[str, Role]) -> User:
    user = register_user("challenger_m3_stud@example.com", "Password@123", "Challenger Student")
    assign_role_to_user(user.id, "STUDENT", session=db.session)
    return user


@pytest.fixture
def m3_course(app: Flask, m3_instructor: User) -> Course:
    return create_course(
        m3_instructor,
        {
            "course_code": "CHALLENGE-M3",
            "title": "Challenger Invariants Course",
            "description": "Course for testing invariants 13 and 14",
        },
        session=db.session,
    )


@pytest.fixture
def m3_assessment(app: Flask, m3_instructor: User, m3_course: Course) -> Assessment:
    now = utc_now()
    return create_assessment(
        m3_instructor,
        m3_course.id,
        {
            "title": "M3 Challenge Assessment",
            "assessment_type": "EXAM",
            "open_at": (now + timedelta(days=1)).isoformat(),
            "close_at": (now + timedelta(days=3)).isoformat(),
            "time_limit_minutes": 60,
            "attempt_limit": 2,
            "passing_score": 70.0,
            "total_points": 100.0,
        },
        session=db.session,
    )


# ============================================================================
# 1. INVARIANT 13: TIMING LOCK (BR-031) STRESS TESTS
# ============================================================================


def test_invariant_13_pre_publish_timing_mutations_allowed(
    m3_instructor: User, m3_assessment: Assessment
) -> None:
    """Verify that in DRAFT status (before publish), timing parameters CAN be modified."""
    assert m3_assessment.status == "DRAFT"
    assert m3_assessment.published_at is None

    now = utc_now()
    new_open = (now + timedelta(days=2)).isoformat()
    new_close = (now + timedelta(days=4)).isoformat()

    updated = update_assessment(
        m3_instructor,
        m3_assessment.id,
        {
            "open_at": new_open,
            "close_at": new_close,
            "time_limit_minutes": 90,
            "attempt_limit": 3,
        },
        session=db.session,
    )
    assert updated.time_limit_minutes == 90
    assert updated.attempt_limit == 3


def test_invariant_13_web_route_timing_lock_rejections(
    client: FlaskClient, m3_instructor: User, m3_assessment: Assessment
) -> None:
    """Verify Web UI routes reject open_at, time_limit, and attempt_limit once published."""
    login_web_user(client, m3_instructor)

    # Add question and publish
    url_create = f"/instructor/assessments/{m3_assessment.public_id}/questions/create"
    client.post(
        url_create,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Sample Question for Publish",
            "points": 10.0,
            "choices": [
                {"content": "Choice A", "is_correct": True, "position": 1},
                {"content": "Choice B", "is_correct": False, "position": 2},
            ],
        },
    )
    publish_assessment(m3_instructor, m3_assessment.id, session=db.session)
    assert m3_assessment.status == "PUBLISHED"
    assert m3_assessment.published_at is not None

    url_update = f"/instructor/assessments/{m3_assessment.public_id}"
    now = utc_now()

    # Attempt 1: Web JSON modifying open_at -> MUST return 409
    res = client.post(
        url_update,
        json={"open_at": (now + timedelta(days=5)).isoformat()},
        headers={"Accept": "application/json"},
    )
    assert res.status_code == 409

    # Attempt 2: Web JSON modifying time_limit_minutes -> MUST return 409
    res = client.post(
        url_update,
        json={"time_limit_minutes": 120},
        headers={"Accept": "application/json"},
    )
    assert res.status_code == 409

    # Attempt 3: Web JSON modifying attempt_limit -> MUST return 409
    res = client.post(
        url_update,
        json={"attempt_limit": 5},
        headers={"Accept": "application/json"},
    )
    assert res.status_code == 409

    # Attempt 4: Form-data modifying open_at -> MUST return 409 Conflict JSON
    res_form = client.post(
        url_update,
        data={"open_at": (now + timedelta(days=5)).isoformat()},
    )
    assert res_form.status_code == 409
    assert res_form.get_json()["error"]["code"] in ("CONFLICT", "ASSESSMENT_LOCKED")


def test_invariant_13_api_timing_lock_rejections_and_aliases(
    client: FlaskClient, m3_instructor: User, m3_assessment: Assessment
) -> None:
    """Verify that REST API (/api/assessments/<id>) and aliases strictly enforce timing lock."""
    # Publish assessment
    url_create = f"/instructor/assessments/{m3_assessment.public_id}/questions/create"
    login_web_user(client, m3_instructor)
    client.post(
        url_create,
        json={
            "question_type": "TRUE_FALSE",
            "content": "Published Question",
            "points": 5.0,
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
    )
    publish_assessment(m3_instructor, m3_assessment.id, session=db.session)

    # REST API with JWT tokens
    tokens = create_token_pair(m3_instructor)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    api_url = f"/api/assessments/{m3_assessment.public_id}"

    now = utc_now()

    # 1. API PATCH open_at -> 409
    res = client.patch(
        api_url,
        json={"open_at": (now + timedelta(days=10)).isoformat()},
        headers=headers,
    )
    assert res.status_code == 409

    # 2. API PATCH time_limit_minutes -> 409
    res = client.patch(api_url, json={"time_limit_minutes": 45}, headers=headers)
    assert res.status_code == 409

    # 3. API PATCH attempt_limit -> 409
    res = client.patch(api_url, json={"attempt_limit": 1}, headers=headers)
    assert res.status_code == 409

    # 4. Service-level alias checks: duration_minutes alias
    with pytest.raises(AssessmentLockedError, match="time_limit_minutes"):
        update_assessment(
            m3_instructor,
            m3_assessment.id,
            {"duration_minutes": 99},
            session=db.session,
        )

    # 5. Service-level alias checks: max_attempts alias
    with pytest.raises(AssessmentLockedError, match="attempt_limit"):
        update_assessment(
            m3_instructor,
            m3_assessment.id,
            {"max_attempts": 10},
            session=db.session,
        )


def test_invariant_13_close_at_forward_allowed_and_shorten_rejected(
    client: FlaskClient, m3_instructor: User, m3_assessment: Assessment
) -> None:
    """Verify that close_at can ONLY be extended forward into the future, never shortened."""
    login_web_user(client, m3_instructor)
    client.post(
        f"/instructor/assessments/{m3_assessment.public_id}/questions/create",
        json={
            "question_type": "SHORT_ANSWER",
            "content": "Capital of France?",
            "points": 1.0,
            "accepted_answers": ["Paris"],
        },
    )
    publish_assessment(m3_instructor, m3_assessment.id, session=db.session)
    original_close = m3_assessment.close_at

    # 1. Forward extension via Web route -> MUST SUCCEED (200 OK)
    future_close_1 = original_close + timedelta(days=3)
    res = client.post(
        f"/instructor/assessments/{m3_assessment.public_id}",
        json={"close_at": future_close_1.isoformat()},
        headers={"Accept": "application/json"},
    )
    assert res.status_code == 200

    db.session.refresh(m3_assessment)
    assert m3_assessment.close_at == future_close_1

    # 2. Forward extension via API PATCH -> MUST SUCCEED (200 OK)
    tokens = create_token_pair(m3_instructor)
    future_close_2 = future_close_1 + timedelta(days=2)
    res_api = client.patch(
        f"/api/assessments/{m3_assessment.public_id}",
        json={"close_at": future_close_2.isoformat()},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert res_api.status_code == 200

    db.session.refresh(m3_assessment)
    assert m3_assessment.close_at == future_close_2

    # 3. Shortening close_at via Web JSON -> MUST BE REJECTED (409)
    shortened_close = future_close_2 - timedelta(days=1)
    res_short = client.post(
        f"/instructor/assessments/{m3_assessment.public_id}",
        json={"close_at": shortened_close.isoformat()},
        headers={"Accept": "application/json"},
    )
    assert res_short.status_code == 409

    # 4. Shortening close_at via API PATCH -> MUST BE REJECTED (409)
    res_api_short = client.patch(
        f"/api/assessments/{m3_assessment.public_id}",
        json={"close_at": shortened_close.isoformat()},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert res_api_short.status_code == 409

    # 5. Shortening via service call -> MUST raise AssessmentLockedError
    with pytest.raises(AssessmentLockedError, match="close_at can only be extended forward"):
        update_assessment(
            m3_instructor,
            m3_assessment.id,
            {"close_at": shortened_close.isoformat()},
            session=db.session,
        )


# ============================================================================
# 2. INVARIANT 14: STRUCTURAL FREEZE (BR-030) STRESS TESTS
# ============================================================================


def test_invariant_14_direct_authoring_all_types_rejected_post_attempt(
    client: FlaskClient, m3_instructor: User, m3_assessment: Assessment
) -> None:
    """Verify that once student attempts start, creating ANY question type is rejected with 409."""
    login_web_user(client, m3_instructor)
    url_create = f"/instructor/assessments/{m3_assessment.public_id}/questions/create"

    # Simulate attempt started
    m3_assessment.first_attempt_started_at = utc_now()
    db.session.commit()

    # 1. SINGLE_CHOICE
    res1 = client.post(
        url_create,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Frozen SC?",
            "points": 2.0,
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
        },
    )
    assert res1.status_code == 409

    # 2. MULTIPLE_CHOICE
    res2 = client.post(
        url_create,
        json={
            "question_type": "MULTIPLE_CHOICE",
            "content": "Frozen MC?",
            "points": 3.0,
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": True, "position": 2},
            ],
        },
    )
    assert res2.status_code == 409

    # 3. TRUE_FALSE
    res3 = client.post(
        url_create,
        json={
            "question_type": "TRUE_FALSE",
            "content": "Frozen TF?",
            "points": 1.0,
            "choices": [
                {"content": "Đúng", "is_correct": True, "position": 1},
                {"content": "Sai", "is_correct": False, "position": 2},
            ],
        },
    )
    assert res3.status_code == 409

    # 4. SHORT_ANSWER
    res4 = client.post(
        url_create,
        json={
            "question_type": "SHORT_ANSWER",
            "content": "Frozen SA?",
            "points": 2.5,
            "accepted_answers": ["Python"],
        },
    )
    assert res4.status_code == 409

    # 5. Form-encoded submission
    res5 = client.post(
        url_create,
        data={
            "question_type": "SINGLE_CHOICE",
            "content": "Form question after freeze",
            "points": "1.0",
            "choices_text": "Choice 1\n*Choice 2",
        },
    )
    assert res5.status_code == 409

    # Verify no assignments exist
    assignments = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == m3_assessment.id)
        .all()
    )
    assert len(assignments) == 0


def test_invariant_14_in_place_question_editing_rejected_post_attempt(
    client: FlaskClient, m3_instructor: User, m3_assessment: Assessment
) -> None:
    """Verify that in-place editing of question content, choices, or points is rejected with 409."""
    login_web_user(client, m3_instructor)
    url_create = f"/instructor/assessments/{m3_assessment.public_id}/questions/create"

    # Add question before freeze
    res_q = client.post(
        url_create,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Original Stable Prompt",
            "points": 5.0,
            "explanation": "Original Explanation",
            "choices": [
                {"content": "Opt 1", "is_correct": True, "position": 1},
                {"content": "Opt 2", "is_correct": False, "position": 2},
            ],
        },
    )
    assert res_q.status_code == 201
    q_data = res_q.get_json()
    q_id = q_data["question"]["question_id"]

    # Now freeze assessment
    m3_assessment.first_attempt_started_at = utc_now()
    db.session.commit()

    edit_url = f"/instructor/assessments/{m3_assessment.public_id}/questions/{q_id}/edit"

    # 1. Modify question prompt -> 409
    res_edit_content = client.post(edit_url, json={"content": "Altered Prompt Post Freeze"})
    assert res_edit_content.status_code == 409

    # 2. Modify points via JSON -> 409
    res_edit_points = client.post(edit_url, json={"points": 10.0})
    assert res_edit_points.status_code == 409

    # 3. Modify points via Form -> 409
    res_edit_form = client.post(edit_url, data={"points": "15.0"})
    assert res_edit_form.status_code == 409

    # 4. Modify choices -> 409
    res_edit_choices = client.post(
        edit_url,
        json={
            "choices": [
                {"content": "Hacked Opt 1", "is_correct": False, "position": 1},
                {"content": "Hacked Opt 2", "is_correct": True, "position": 2},
            ]
        },
    )
    assert res_edit_choices.status_code == 409

    # 5. Modify explanation -> 409
    res_edit_exp = client.post(edit_url, json={"explanation": "Hacked Explanation"})
    assert res_edit_exp.status_code == 409

    # Database verification: Ensure original values are untouched
    assignment = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == m3_assessment.id)
        .first()
    )
    assert float(assignment.points) == 5.0
    assert assignment.question.current_revision.content == "Original Stable Prompt"
    assert assignment.question.current_revision.explanation == "Original Explanation"


def test_invariant_14_question_removal_rejected_post_attempt(
    client: FlaskClient, m3_instructor: User, m3_assessment: Assessment
) -> None:
    """Verify question removal via POST /remove & DELETE is rejected with 409 post attempt."""
    login_web_user(client, m3_instructor)
    url_create = f"/instructor/assessments/{m3_assessment.public_id}/questions/create"

    res_q = client.post(
        url_create,
        json={
            "question_type": "TRUE_FALSE",
            "content": "Question to be preserved",
            "points": 2.0,
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
    )
    assert res_q.status_code == 201
    q_id = res_q.get_json()["question"]["question_id"]

    # Freeze assessment
    m3_assessment.first_attempt_started_at = utc_now()
    db.session.commit()

    # 1. POST /remove -> 409
    remove_url = f"/instructor/assessments/{m3_assessment.public_id}/questions/{q_id}/remove"
    res_remove = client.post(remove_url, headers={"Accept": "application/json"})
    assert res_remove.status_code == 409

    # 2. DELETE -> 409
    del_url = f"/instructor/assessments/{m3_assessment.public_id}/questions/{q_id}"
    res_del = client.delete(del_url, headers={"Accept": "application/json"})
    assert res_del.status_code == 409

    # 3. Direct service call remove_question_assignment -> AssessmentLockedError
    with pytest.raises(AssessmentLockedError, match="Assessment questions cannot be removed"):
        remove_question_assignment(m3_instructor, m3_assessment.id, q_id, session=db.session)

    # Verify assignment still exists
    assignment = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == m3_assessment.id)
        .first()
    )
    assert assignment is not None


def test_invariant_14_document_import_rejected_post_attempt(
    client: FlaskClient, m3_instructor: User, m3_assessment: Assessment, m3_course: Course
) -> None:
    """Verify uploading DOCX or PDF import is rejected with 409 once attempts start."""
    login_web_user(client, m3_instructor)
    import_url = f"/instructor/assessments/{m3_assessment.public_id}/import"

    # Freeze assessment
    m3_assessment.first_attempt_started_at = utc_now()
    db.session.commit()

    # 1. DOCX upload attempt
    docx_bytes = _make_sample_docx(["Cau 1: Test?", "A. Yes", "B. No", "Dap an: A"])
    res_docx = client.post(
        import_url,
        data={
            "file": (
                io.BytesIO(docx_bytes),
                "test_import.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        content_type="multipart/form-data",
    )
    assert res_docx.status_code == 409

    # 2. PDF upload attempt
    pdf_bytes = _make_sample_pdf(["Cau 1: PDF Test?", "A. Yes", "B. No", "Dap an: A"])
    res_pdf = client.post(
        import_url,
        data={"file": (io.BytesIO(pdf_bytes), "test_import.pdf", "application/pdf")},
        content_type="multipart/form-data",
    )
    assert res_pdf.status_code == 409

    # 3. Direct service call import_service.create_import_job -> AssessmentLockedError
    file_asset = store_file_stream(
        actor=m3_instructor,
        course_id=m3_course.id,
        file_stream=io.BytesIO(docx_bytes),
        filename="job_test.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        asset_type="IMPORT_SOURCE",
        session=db.session,
    )
    with pytest.raises(
        AssessmentLockedError,
        match="Cannot import questions into an assessment whose attempts have started",
    ):
        create_import_job(
            actor=m3_instructor,
            course_id=m3_course.id,
            file_asset_id=file_asset.id,
            draft_assessment_id=m3_assessment.id,
            session=db.session,
        )


def test_invariant_14_service_level_structural_freezes(
    m3_instructor: User, m3_assessment: Assessment, m3_course: Course
) -> None:
    """Verify all service-level structural mutations raise AssessmentLockedError post-attempt."""
    # Create question in question bank
    bank_q = create_question(
        m3_instructor,
        m3_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Bank Question",
            "choices": [
                {"content": "1", "is_correct": True, "position": 1},
                {"content": "2", "is_correct": False, "position": 2},
            ],
        },
        session=db.session,
    )

    # Assign question initially
    assignment = assign_question(
        m3_instructor,
        m3_assessment.id,
        {"question_id": bank_q.id, "points": 5.0},
        session=db.session,
    )
    assert assignment is not None

    # Freeze assessment
    m3_assessment.first_attempt_started_at = utc_now()
    db.session.commit()

    # 1. assign_question -> AssessmentLockedError
    bank_q2 = create_question(
        m3_instructor,
        m3_course.id,
        {
            "question_type": "SHORT_ANSWER",
            "difficulty": "REMEMBER",
            "content": "Bank Question 2",
            "accepted_answers": ["Ans"],
        },
        session=db.session,
    )
    with pytest.raises(AssessmentLockedError, match="Assessment questions cannot be modified"):
        assign_question(
            m3_instructor,
            m3_assessment.id,
            {"question_id": bank_q2.id, "points": 2.0},
            session=db.session,
        )

    # 2. update_question_assignment -> AssessmentLockedError
    with pytest.raises(
        AssessmentLockedError, match="Assessment question points cannot be modified"
    ):
        update_question_assignment(
            m3_instructor,
            m3_assessment.id,
            bank_q.id,
            {"points": 10.0},
            session=db.session,
        )

    # 3. remove_question_assignment -> AssessmentLockedError
    with pytest.raises(AssessmentLockedError, match="Assessment questions cannot be removed"):
        remove_question_assignment(
            m3_instructor,
            m3_assessment.id,
            bank_q.id,
            session=db.session,
        )

    # 4. create_section & delete_section -> AssessmentLockedError
    with pytest.raises(AssessmentLockedError, match="Assessment sections cannot be added"):
        create_section(
            m3_instructor,
            m3_assessment.id,
            {"title": "New Section Post Freeze"},
            session=db.session,
        )

    with pytest.raises(AssessmentLockedError, match="Assessment sections cannot be deleted"):
        delete_section(
            m3_instructor,
            m3_assessment.id,
            9999,
            session=db.session,
        )

    # 5. update_assessment changing assessment_type -> AssessmentLockedError
    with pytest.raises(AssessmentLockedError, match="Assessment structure is locked"):
        update_assessment(
            m3_instructor,
            m3_assessment.id,
            {"assessment_type": "QUIZ"},
            session=db.session,
        )

    # 6. update_assessment changing random_question_count -> AssessmentLockedError
    with pytest.raises(AssessmentLockedError, match="Assessment structure is locked"):
        update_assessment(
            m3_instructor,
            m3_assessment.id,
            {"random_question_count": 10},
            session=db.session,
        )


def test_invariant_14_rest_api_structural_freeze(
    client: FlaskClient, m3_instructor: User, m3_assessment: Assessment, m3_course: Course
) -> None:
    """Verify REST API routes (/api/assessments/<id>/questions/...) return 409 post-attempt."""
    tokens = create_token_pair(m3_instructor)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    bank_q = create_question(
        m3_instructor,
        m3_course.id,
        {
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "content": "REST API Question",
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
        session=db.session,
    )
    assign_question(
        m3_instructor,
        m3_assessment.id,
        {"question_id": bank_q.id, "points": 4.0},
        session=db.session,
    )

    # Freeze assessment
    m3_assessment.first_attempt_started_at = utc_now()
    db.session.commit()

    base_api = f"/api/assessments/{m3_assessment.public_id}"

    # 1. POST /api/assessments/<id>/questions -> 409
    res_assign = client.post(
        f"{base_api}/questions",
        json={"question_id": str(bank_q.public_id), "points": 5.0},
        headers=headers,
    )
    assert res_assign.status_code == 409

    # 2. PATCH /api/assessments/<id>/questions/<qid> -> 409
    res_patch = client.patch(
        f"{base_api}/questions/{bank_q.public_id}",
        json={"points": 8.0},
        headers=headers,
    )
    assert res_patch.status_code == 409

    # 3. DELETE /api/assessments/<id>/questions/<qid> -> 409
    res_del = client.delete(
        f"{base_api}/questions/{bank_q.public_id}",
        headers=headers,
    )
    assert res_del.status_code == 409


def test_invariant_authorization_and_isolation(
    client: FlaskClient,
    rogue_instructor: User,
    m3_student: User,
    m3_assessment: Assessment,
) -> None:
    """Verify course boundary isolation and role checks on assessment authoring endpoints."""
    # Rogue instructor (not course manager) cannot author or edit questions
    login_web_user(client, rogue_instructor)
    url_create = f"/instructor/assessments/{m3_assessment.public_id}/questions/create"
    res = client.post(
        url_create,
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Unauthorized question",
            "choices": [{"content": "X", "is_correct": True, "position": 1}],
        },
    )
    assert res.status_code == 403

    # Student cannot access instructor assessment authoring endpoints
    login_web_user(client, m3_student)
    res_stud = client.post(url_create, json={"question_type": "TRUE_FALSE"})
    assert res_stud.status_code in (403, 302)


def test_invariant_13_identical_timestamp_resubmission_allowed(
    client: FlaskClient, m3_instructor: User, m3_assessment: Assessment
) -> None:
    """Verify unchanged timing fields do not trigger false-positive lock on title update."""
    login_web_user(client, m3_instructor)
    client.post(
        f"/instructor/assessments/{m3_assessment.public_id}/questions/create",
        json={
            "question_type": "TRUE_FALSE",
            "content": "Publish Test Question",
            "points": 1.0,
            "choices": [
                {"content": "T", "is_correct": True, "position": 1},
                {"content": "F", "is_correct": False, "position": 2},
            ],
        },
    )
    publish_assessment(m3_instructor, m3_assessment.id, session=db.session)

    # Submitting identical open_at, time_limit, attempt_limit with updated title
    res = client.post(
        f"/instructor/assessments/{m3_assessment.public_id}",
        json={
            "title": "Renamed Published Assessment",
            "open_at": m3_assessment.open_at.isoformat(),
            "time_limit_minutes": m3_assessment.time_limit_minutes,
            "attempt_limit": m3_assessment.attempt_limit,
        },
        headers={"Accept": "application/json"},
    )
    assert res.status_code == 200
    db.session.refresh(m3_assessment)
    assert m3_assessment.title == "Renamed Published Assessment"


def test_invariant_14_freeze_precedence_over_invalid_payload(
    client: FlaskClient, m3_instructor: User, m3_assessment: Assessment
) -> None:
    """Verify invariant 14 check precedes payload validation, returning 409 Conflict."""
    login_web_user(client, m3_instructor)
    m3_assessment.first_attempt_started_at = utc_now()
    db.session.commit()

    # Intentionally malformed payload: invalid question type, missing content & choices
    url_create = f"/instructor/assessments/{m3_assessment.public_id}/questions/create"
    res = client.post(
        url_create,
        json={"question_type": "TOTALLY_INVALID_TYPE", "content": ""},
        headers={"Accept": "application/json"},
    )
    # MUST return 409 (Invariant 14 lock), NOT 400 (Validation error)
    assert res.status_code == 409


def test_invariant_14_freeze_permanence_after_attempt_completion(
    client: FlaskClient, m3_instructor: User, m3_assessment: Assessment
) -> None:
    """Verify freeze remains strictly enforced after student attempts are completed/submitted."""
    login_web_user(client, m3_instructor)
    past_time = utc_now() - timedelta(days=2)
    m3_assessment.first_attempt_started_at = past_time
    db.session.commit()

    url_create = f"/instructor/assessments/{m3_assessment.public_id}/questions/create"
    res = client.post(
        url_create,
        json={
            "question_type": "SHORT_ANSWER",
            "content": "Post Attempt Completion Question",
            "points": 5.0,
            "accepted_answers": ["42"],
        },
    )
    assert res.status_code == 409
