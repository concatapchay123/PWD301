"""E2E Lifecycle Test: Instructor Course Authoring, Import, Assessment Freeze,
Manual Essay Grading, and Regrade Engine.

Verifies:
1. Instructor creates DRAFT course, chapter, and lesson.
2. Resource file upload with virus scanning and fail-closed quarantine verification.
3. Question Bank authoring (Manual + DOCX Import with review, decision, commit, and provenance).
4. Assessment Blueprint builder, question assignment, and publishing.
5. Student attempt initialization triggering immutable structural freeze (ASSESS-002).
6. Student submission requiring manual grading (PENDING_GRADING status).
7. Instructor manual essay grading (grade_essay_question, AttemptQuestionGradeHistory).
8. Question correction workflow triggering automatic regrading job (Algorithm 11).
9. AttemptScoreHistory audit trail and score recalculation.
"""

from __future__ import annotations

import io
import uuid
import zipfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import (
    AssessmentResultHistory,
    AttemptQuestionGrade,
    AttemptQuestionGradeHistory,
    RegradeJob,
)
from pwd301.models.identity import User
from pwd301.models.question_bank import Question, QuestionProvenance
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    grade_essay_question,
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    AssessmentLockedError,
    FileAccessDeniedError,
)
from pwd301.services.file_service import (
    attach_resource_to_lesson,
    get_file_for_download,
    store_file_stream,
)
from pwd301.services.import_service import (
    commit_import_job,
    create_import_job,
    process_import_job,
    set_import_question_decision,
)
from pwd301.services.lesson_service import change_lesson_status, create_lesson
from pwd301.services.question_bank_service import (
    create_question,
    create_question_revision,
)
from pwd301.services.regrade_worker import process_regrade_job
from pwd301.services.user_service import assign_role_to_user, register_user


def _create_sample_docx(paragraphs: list[str]) -> bytes:
    """Generate valid in-memory DOCX bytes containing specified paragraphs."""
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


@pytest.fixture
def instructor_user(app: Flask) -> User:
    """Register and return an instructor user."""
    sess: Session = db.session
    u = register_user(
        f"e2e_inst_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Professor Turing",
    )
    u = assign_role_to_user(u.id, "INSTRUCTOR")
    sess.commit()
    return u


@pytest.fixture
def admin_user(app: Flask) -> User:
    """Register and return an administrator user."""
    sess: Session = db.session
    u = register_user(
        f"e2e_admin_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Administrator Ops",
    )
    u = assign_role_to_user(u.id, "ADMIN")
    sess.commit()
    return u


@pytest.fixture
def student_user(app: Flask) -> User:
    """Register and return a student user."""
    sess: Session = db.session
    u = register_user(
        f"e2e_student_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Bob Learner",
    )
    u = assign_role_to_user(u.id, "STUDENT")
    u.email_verified_at = datetime.now(UTC)
    sess.commit()
    return u


def test_instructor_complete_lifecycle_e2e(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Execute complete instructor authoring, scanning, importing, grading,
    and regrading journey.
    """
    sess: Session = db.session

    # -------------------------------------------------------------------------
    # 1. Course Authoring, Chapters, Lessons & File Attachment
    # -------------------------------------------------------------------------
    course = create_course(
        instructor_user,
        {
            "course_code": f"CS-{uuid.uuid4().hex[:4].upper()}",
            "title": "Cloud Native Architecture & Distributed Systems",
            "category": "Computer Science",
            "difficulty": "ADVANCED",
            "capacity": 30,
        },
        session=sess,
    )
    sess.commit()
    assert course.status == "DRAFT"

    lesson = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Raft Algorithm Deep Dive",
            "markdown_content": "# Raft Consensus\nLeader election and log replication.",
            "lesson_type": "TEXT",
            "position": 1,
            "minimum_completion_seconds": 60,
        },
        session=sess,
    )
    sess.commit()

    # Upload PDF resource file
    pdf_content = b"%PDF-1.4\n% Sample Raft specification document\n%%EOF\n"
    file_stream = io.BytesIO(pdf_content)
    file_asset = store_file_stream(
        actor=instructor_user,
        course_id=course.id,
        file_stream=file_stream,
        filename="raft_paper.pdf",
        content_type="application/pdf",
        asset_type="RESOURCE",
        title="Raft Protocol Whitepaper",
        session=sess,
    )
    sess.commit()
    assert file_asset.status == "ACTIVE"
    assert file_asset.current_revision.status == "ACTIVE"
    assert len(file_asset.current_revision.scan_results) > 0
    assert file_asset.current_revision.scan_results[0].status == "PASS"

    # Attach file to lesson
    lesson_resource = attach_resource_to_lesson(
        actor=instructor_user,
        lesson_id=lesson.id,
        asset_id=file_asset.id,
        is_downloadable=True,
        label="Raft Protocol Whitepaper",
        session=sess,
    )
    sess.commit()
    assert lesson_resource.file_asset_id == file_asset.id

    # Fail-closed check: Student cannot download while course is still DRAFT
    with pytest.raises(
        FileAccessDeniedError, match="Cannot download files from an unpublished course"
    ):
        get_file_for_download(actor=student_user, asset_id=file_asset.id, session=sess)

    # -------------------------------------------------------------------------
    # 2. Question Authoring: Manual (Single Choice) + DOCX Import (Essay)
    # -------------------------------------------------------------------------
    # Manual Question: Single Choice with Bloom REMEMBER
    q_single = create_question(
        instructor_user,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Which server state in Raft initiates leader elections?",
            "default_points": 50.0,
            "choices": [
                {"content": "Candidate", "is_correct": True, "position": 1},
                {"content": "Follower", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()
    c_candidate = [c for c in q_single.current_revision.choices if c.content == "Candidate"][0]
    c_follower = [c for c in q_single.current_revision.choices if c.content == "Follower"][0]
    ck_candidate = c_candidate.choice_key
    ck_follower = c_follower.choice_key

    # Import Question via DOCX: Essay
    docx_paras = [
        (
            "Câu 1: Phân tích cơ chế Split-Brain trong hệ thống phân tán "
            "và cách Raft giải quyết. [ESSAY] [ANALYZE] [50 pts]"
        ),
        (
            "Giải thích: Raft giải quyết bằng Majority Quorum (N/2 + 1) "
            "và Leader Term số nguyên đơn điệu tăng."
        ),
    ]
    docx_bytes = _create_sample_docx(docx_paras)
    import_stream = io.BytesIO(docx_bytes)
    import_asset = store_file_stream(
        actor=instructor_user,
        course_id=course.id,
        file_stream=import_stream,
        filename="questions_import.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        asset_type="IMPORT_SOURCE",
        session=sess,
    )
    sess.commit()

    import_job = create_import_job(
        actor=instructor_user,
        course_id=course.id,
        file_asset_id=import_asset.id,
        session=sess,
    )
    sess.commit()
    import_job = process_import_job(actor=instructor_user, job_id=import_job.id, session=sess)
    sess.commit()
    assert import_job.status == "REVIEW_REQUIRED"
    assert len(import_job.questions) == 1

    # Accept question and commit to Question Bank
    set_import_question_decision(
        actor=instructor_user,
        job_id=import_job.id,
        temp_id=import_job.questions[0].ordinal,
        decision="ACCEPTED",
        session=sess,
    )
    sess.commit()
    commit_res = commit_import_job(actor=instructor_user, job_id=import_job.id, session=sess)
    sess.commit()
    assert commit_res["status"] == "COMPLETED"
    assert commit_res["imported_count"] == 1

    imported_q_uuid = uuid.UUID(commit_res["created_question_ids"][0])
    q_essay = sess.query(Question).filter(Question.public_id == imported_q_uuid).one()
    assert q_essay.current_revision.question_type == "ESSAY"

    # Verify Provenance tracking
    prov = (
        sess.query(QuestionProvenance)
        .filter(QuestionProvenance.question_revision_id == q_essay.current_revision.id)
        .first()
    )
    assert prov is not None
    assert prov.source_type == "IMPORT"

    # -------------------------------------------------------------------------
    # 3. Assessment Blueprint & Publishing
    # -------------------------------------------------------------------------
    now = datetime.now(UTC)
    asm_payload = {
        "title": "Midterm Architecture Exam",
        "assessment_type": "MIDTERM",
        "time_limit_minutes": 90,
        "open_at": (now - timedelta(hours=1)).isoformat(),
        "close_at": (now + timedelta(hours=48)).isoformat(),
        "passing_score": 60.0,
        "score_release_policy": "IMMEDIATE",
    }
    assessment = create_assessment(instructor_user, course.id, asm_payload, session=sess)
    sec = create_section(instructor_user, assessment.id, {"title": "Section 1"}, session=sess)

    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q_single.id, "section_id": sec.id, "position": 1, "points_assigned": 50.0},
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q_essay.id, "section_id": sec.id, "position": 2, "points_assigned": 50.0},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    # -------------------------------------------------------------------------
    # 4. Course Publishing & Student Resource Download
    # -------------------------------------------------------------------------
    change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin_user, course.id, "APPROVED", session=sess)
    change_course_status(instructor_user, course.id, "PUBLISHED", session=sess)
    change_lesson_status(instructor_user, lesson.id, "PUBLISHED", session=sess)
    sess.commit()

    # Student enrolls and accesses the downloadable resource
    enroll_student(actor=student_user, course_id=course.id, session=sess)
    sess.commit()

    _, blob_dl, dl_path = get_file_for_download(
        actor=student_user, asset_id=file_asset.id, session=sess
    )
    assert dl_path.exists()
    assert blob_dl.status == "PRESENT"

    # -------------------------------------------------------------------------
    # 5. Student Starts Attempt -> Enforces Structural Freeze (ASSESS-002)
    # -------------------------------------------------------------------------
    attempt, lease_tok = start_assessment_attempt(student_user, assessment.id, session=sess)
    sess.commit()
    assert attempt.status == "IN_PROGRESS"

    # Structural freeze invariant verification
    sess.refresh(assessment)
    assert assessment.first_attempt_started_at is not None

    # Instructor cannot modify questions after first attempt started
    with pytest.raises(AssessmentLockedError, match="Assessment questions cannot be modified"):
        assign_question(
            instructor_user,
            assessment.id,
            {
                "question_id": q_single.id,
                "section_id": sec.id,
                "position": 3,
                "points_assigned": 10.0,
            },
            session=sess,
        )

    # -------------------------------------------------------------------------
    # 6. Student Submits with Objective and Essay Answers
    # -------------------------------------------------------------------------
    delivery_qs = attempt.attempt_questions
    assert len(delivery_qs) == 2
    aq_mc = next(aq for aq in delivery_qs if aq.question_type_snapshot == "SINGLE_CHOICE")
    aq_es = next(aq for aq in delivery_qs if aq.question_type_snapshot == "ESSAY")

    # Answer MCQ (Selected Candidate = ck_candidate)
    save_attempt_answer(
        actor=student_user,
        attempt_id=attempt.id,
        attempt_question_id=aq_mc.id,
        payload={
            "client_sequence": 1,
            "selected_choice_keys": [str(ck_candidate)],
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=lease_tok,
        session=sess,
    )

    # Answer Essay
    save_attempt_answer(
        actor=student_user,
        attempt_id=attempt.id,
        attempt_question_id=aq_es.id,
        payload={
            "client_sequence": 2,
            "answer_text": (
                "Split-brain is prevented via majority quorum (N/2 + 1) and term numbering."
            ),
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=lease_tok,
        session=sess,
    )
    sess.commit()

    # Submit attempt -> Needs manual grading for essay
    submit_res = submit_assessment_attempt(
        actor=student_user,
        attempt_id=attempt.id,
        raw_lease_token=lease_tok,
        session=sess,
    )
    sess.commit()
    assert submit_res["status"] == "PENDING_GRADING"

    sess.refresh(attempt)
    assert attempt.status == "PENDING_GRADING"

    # MCQ was auto-graded for 50 pts, Essay is still pending
    grade_mc = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq_mc.id).one()
    assert grade_mc.awarded_points == Decimal("50.0000")
    assert grade_mc.grading_status == "AUTO_GRADED"

    # -------------------------------------------------------------------------
    # 7. Instructor Performs Manual Essay Grading
    # -------------------------------------------------------------------------
    manual_grade_res = grade_essay_question(
        actor=instructor_user,
        attempt_id=attempt.id,
        attempt_question_id=aq_es.id,
        awarded_points=40.0,
        reason="Good conceptual analysis of majority quorum.",
        session=sess,
    )
    sess.commit()
    assert manual_grade_res["attempt_status"] == "GRADED"
    assert manual_grade_res["is_finalized"] is True

    sess.refresh(attempt)
    assert attempt.status == "GRADED"
    assert attempt.result is not None
    # 50.0 (MCQ) + 40.0 (Essay) = 90.0
    assert attempt.result.raw_score == Decimal("90.0000")
    assert attempt.result.passed is True

    # Check AttemptQuestionGradeHistory
    es_hist = (
        sess.query(AttemptQuestionGradeHistory)
        .filter_by(attempt_question_id=aq_es.id)
        .order_by(AttemptQuestionGradeHistory.created_at.desc())
        .first()
    )
    assert es_hist is not None
    assert es_hist.new_points == Decimal("40.0000")
    assert es_hist.reason_code == "MANUAL_REVISION"

    # -------------------------------------------------------------------------
    # 8. Question Flaw Discovered -> QuestionRevision & Regrade Engine (Alg 11)
    # -------------------------------------------------------------------------
    # Instructor realizes Candidate is not the only initiator; Follower should be correct
    new_rev, corr = create_question_revision(
        instructor_user,
        q_single.id,
        {
            "change_type": "ANSWER_CHANGE",
            "correction_type": "ANSWER_ONLY",
            "change_reason": "Follower was deemed correct per updated textbook edition",
            "choices": [
                {
                    "choice_key": str(ck_candidate),
                    "content": "Candidate",
                    "is_correct": False,
                    "position": 1,
                },
                {
                    "choice_key": str(ck_follower),
                    "content": "Follower",
                    "is_correct": True,
                    "position": 2,
                },
            ],
        },
        session=sess,
    )
    sess.commit()
    assert corr is not None

    # Regrade job created
    job = sess.query(RegradeJob).filter(RegradeJob.question_correction_id == corr.id).one()
    assert job.status in ("QUEUED", "PENDING")
    assert job.total_items == 1

    # Process regrade job
    regrade_res = process_regrade_job(job.id, actor=instructor_user, session=sess)
    sess.commit()
    assert regrade_res["status"] == "COMPLETED"
    assert regrade_res["changed_results"] == 1

    # Verify student attempt result updated: MCQ score changed from 50.0 to 0.0
    # Total score becomes: 0.0 (MCQ) + 40.0 (Essay) = 40.0
    sess.refresh(attempt)
    sess.refresh(attempt.result)
    assert attempt.result.raw_score == Decimal("40.0000")
    # Passing score was 60.0 -> Student has now failed after regrade
    assert attempt.result.passed is False

    # Check AssessmentResultHistory audit trail
    res_hist = (
        sess.query(AssessmentResultHistory)
        .filter(
            AssessmentResultHistory.attempt_id == attempt.id,
            AssessmentResultHistory.regrade_job_id == job.id,
        )
        .first()
    )
    assert res_hist is not None
    assert res_hist.old_score == Decimal("90.0000")
    assert res_hist.new_score == Decimal("40.0000")
    assert res_hist.reason_code == "REGRADE"
