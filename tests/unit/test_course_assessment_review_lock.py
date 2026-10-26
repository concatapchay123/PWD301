"""Course approval must preserve exams admitted while their proposal was pending."""

import pytest
import sqlalchemy as sa

from backend.extensions import db
from backend.models.assessment import Assessment
from backend.models.types import utc_now
from backend.services.assessment_service import create_section, update_assessment
from backend.services.exceptions import AssessmentLockedError
from backend.services.lesson_service import approve_course_change_request, submit_course_changeset
from tests.unit.test_unified_course_workflow import published_assessment

pytest_plugins = ["tests.test_lesson_revision_lifecycle"]


def test_approval_refreshes_freeze_marker_before_replacing_reviewed_structure(
    app, published_course, instructor_user, admin_user
):
    course, _ = published_course
    original = published_assessment(course, admin_user)
    create_section(instructor_user, original.id, {"title": "Proposed section"}, session=db.session)
    pending = submit_course_changeset(
        instructor_user, course.id, {"title": "Section review"}, session=db.session
    )
    db.session.execute(
        sa.update(Assessment)
        .where(Assessment.id == original.id)
        .values(first_attempt_started_at=utc_now())
        .execution_options(synchronize_session=False)
    )
    assert original.first_attempt_started_at is None
    assert (
        db.session.query(Assessment.first_attempt_started_at).filter_by(id=original.id).scalar()
        is not None
    )
    with pytest.raises(AssessmentLockedError):
        approve_course_change_request(
            admin_user, pending.id, "Cannot partly approve", session=db.session
        )
    assert list(original.sections) == []


def test_metadata_only_review_keeps_frozen_graph_and_locks_assessment(
    app, published_course, instructor_user, admin_user, monkeypatch
):
    from backend.services import assessment_service

    course, _ = published_course
    original = published_assessment(course, admin_user)
    update_assessment(instructor_user, original.id, {"title": "Reviewed title"}, session=db.session)
    pending = submit_course_changeset(
        instructor_user, course.id, {"title": "Metadata review"}, session=db.session
    )
    original.first_attempt_started_at = utc_now()
    db.session.flush()
    acquired = []
    lock = assessment_service._lock_assessment_for_mutation

    def record_lock(assessment, session):
        acquired.append(assessment.id)
        return lock(assessment, session)

    monkeypatch.setattr(assessment_service, "_lock_assessment_for_mutation", record_lock)
    approve_course_change_request(admin_user, pending.id, "Approve metadata", session=db.session)
    assert original.title == "Reviewed title"
    assert acquired == [original.id]
