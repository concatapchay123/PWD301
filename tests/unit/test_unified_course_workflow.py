"""Unified authoring must preserve the approved baseline and submitted evidence."""

import json

import pytest

from backend.extensions import db
from backend.models.course import CourseChangeRequest, CoursePrerequisite, LearningUnit, Lesson
from backend.models.types import utc_now
from backend.services.completion_service import (
    get_or_create_default_completion_rule,
    set_course_completion_rule,
)
from backend.services.course_service import create_course, update_course
from backend.services.enrollment_service import add_course_prerequisite
from backend.services.exceptions import ConflictError, CourseValidationError
from backend.services.lesson_service import (
    approve_course_change_request,
    create_learning_unit,
    create_lesson,
    get_course_changeset_status,
    reject_course_change_request,
    retract_course_changeset,
    submit_course_changeset,
)

pytest_plugins = ["tests.test_lesson_revision_lifecycle"]


def test_prerequisite_session_route_handles_composite_key(
    app, client, published_course, instructor_user
):
    from tests.conftest import login_web_user

    course, _ = published_course
    prerequisite = create_course(
        instructor_user, {"course_code": "PREREQ-API095", "title": "Prerequisite API"}
    )
    prerequisite.status = "PUBLISHED"
    prerequisite.approved_at = utc_now()
    db.session.commit()
    login_web_user(client, instructor_user)
    response = client.post(
        f"/instructor/courses/{course.public_id}/prerequisites",
        json={"prerequisite_course_id": str(prerequisite.public_id)},
    )
    assert response.status_code == 200, response.json
    assert response.json["data"]["is_draft"] is True
    assert db.session.query(CoursePrerequisite).filter_by(course_id=course.id).count() == 0


def test_jwt_lesson_edit_uses_saved_aggregate_without_fragment(
    app, client, published_course, instructor_user
):
    from backend.services.jwt_auth_service import create_token_pair

    course, lesson = published_course
    token = create_token_pair(instructor_user)["access_token"]
    response = client.patch(
        f"/api/lessons/{lesson.public_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "JWT proposed title"},
    )
    assert response.status_code == 200, response.json
    assert response.json["data"]["is_draft"] is True
    assert response.json["data"]["pending_approval"] is False
    record = active_requests(course)[0]
    assert record.status == "DRAFT"
    assert record.change_type == "COURSE_VERSION_CHANGESET"
    db.session.remove()
    assert db.session.query(CourseChangeRequest).filter_by(id=record.id).one().status == "DRAFT"


def test_jwt_discard_persists_the_working_lesson_change(
    app, client, published_course, instructor_user
):
    from backend.services.jwt_auth_service import create_token_pair
    from backend.services.lesson_service import create_lesson_change_request

    course, original = published_course
    _, draft = create_lesson_change_request(
        instructor_user,
        course.id,
        {"target_id": original.id, "title": "Discard proposed title"},
        session=db.session,
    )
    db.session.commit()
    identifier, public_id = draft.id, str(draft.public_id)
    token = create_token_pair(instructor_user)["access_token"]
    response = client.post(
        f"/api/lessons/{public_id}/draft/discard", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.json
    db.session.remove()
    assert db.session.get(Lesson, identifier).deleted_at is not None


@pytest.mark.parametrize(
    "operation", ["completion", "create_lesson", "reorder", "remove_prerequisite"]
)
def test_jwt_course_mutations_persist_one_draft_after_success(
    app, client, published_course, instructor_user, operation
):
    from backend.services.jwt_auth_service import create_token_pair

    course, original = published_course
    base = f"/api/courses/{course.public_id}"
    if operation == "remove_prerequisite":
        prerequisite = create_course(
            instructor_user, {"course_code": "REMOVE095", "title": "Remove prerequisite"}
        )
        prerequisite.status = "PUBLISHED"
        db.session.add(
            CoursePrerequisite(
                course_id=course.id,
                prerequisite_course_id=prerequisite.id,
                approval_status="APPROVED",
                created_by_user_id=instructor_user.id,
            )
        )
        endpoint, method, payload = f"{base}/prerequisites/{prerequisite.public_id}", "delete", {}
    elif operation == "create_lesson":
        endpoint, method, payload = (
            f"{base}/lessons",
            "post",
            {"title": "Persisted new lesson", "markdown_content": "New content"},
        )
    elif operation == "reorder":
        second = Lesson(
            course_id=course.id,
            learning_unit_id=original.learning_unit_id,
            title="Second approved lesson",
            markdown_content="Approved baseline",
            position=2,
            status="PUBLISHED",
        )
        db.session.add(second)
        db.session.flush()
        endpoint, method, payload = (
            f"{base}/lessons/reorder",
            "post",
            {"ordered_lesson_ids": [str(second.public_id), str(original.public_id)]},
        )
    else:
        endpoint, method, payload = f"{base}/completion-rules", "put", {"minimum_grade_score": 8}
    db.session.commit()
    course_id = course.id
    token = create_token_pair(instructor_user)["access_token"]
    response = getattr(client, method)(
        endpoint, headers={"Authorization": f"Bearer {token}"}, json=payload
    )
    assert response.status_code in (200, 201), response.json
    db.session.remove()
    records = (
        db.session.query(CourseChangeRequest).filter_by(course_id=course_id, status="DRAFT").all()
    )
    assert len(records) == 1
    assert records[0].change_type == "COURSE_VERSION_CHANGESET"
    if operation == "completion":
        response = client.get(
            f"{base}/completion-rules", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json.get("data", response.json)
        assert data.get("minimum_grade_score") == 8


def active_requests(course):
    return (
        db.session.query(CourseChangeRequest)
        .filter(
            CourseChangeRequest.course_id == course.id,
            CourseChangeRequest.status.in_(["DRAFT", "PENDING"]),
        )
        .all()
    )


def test_metadata_automatically_accumulates_one_draft(app, published_course, instructor_user):
    course, _ = published_course
    original = course.title
    first = update_course(
        instructor_user, course.id, {"title": "Proposed course name"}, session=db.session
    )
    second = update_course(
        instructor_user, course.id, {"category": "Proposed category"}, session=db.session
    )
    assert isinstance(first, CourseChangeRequest)
    assert first.status == "DRAFT"
    assert second.id == first.id
    assert course.title == original
    assert len(active_requests(course)) == 1
    assert json.loads(first.proposed_payload_json)["course_metadata"] == {
        "title": "Proposed course name",
        "category": "Proposed category",
    }


@pytest.mark.parametrize("status", ["APPROVED", "DRAFT", "ARCHIVED"])
def test_ever_approved_requires_review_in_every_later_state(
    app, published_course, instructor_user, status
):
    course, _ = published_course
    course.status = status
    course.approved_at = utc_now()
    db.session.flush()
    result = update_course(
        instructor_user, course.id, {"category": "Needs approval"}, session=db.session
    )
    assert isinstance(result, CourseChangeRequest)
    assert result.status == "DRAFT"
    assert course.category != "Needs approval"


def test_pending_changeset_freezes_metadata(app, published_course, instructor_user):
    course, _ = published_course
    update_course(instructor_user, course.id, {"title": "Proposed title"}, session=db.session)
    submit_course_changeset(
        instructor_user, course.id, {"version_title": "Review"}, session=db.session
    )
    with pytest.raises(ConflictError):
        update_course(instructor_user, course.id, {"category": "Blocked"}, session=db.session)


def test_withdraw_preserves_complete_metadata_in_successor_draft(
    app, published_course, instructor_user
):
    course, _ = published_course
    update_course(
        instructor_user,
        course.id,
        {"title": "Preserve proposed name", "as_draft": True},
        session=db.session,
    )
    pending = submit_course_changeset(
        instructor_user, course.id, {"version_title": "First"}, session=db.session
    )
    snapshot = pending.proposed_payload_json
    retract_course_changeset(instructor_user, course.id, session=db.session)
    assert pending.status == "CANCELLED"
    assert pending.proposed_payload_json == snapshot
    drafts = [r for r in active_requests(course) if r.status == "DRAFT"]
    assert len(drafts) == 1
    assert drafts[0].id != pending.id
    assert (
        json.loads(drafts[0].proposed_payload_json)["course_metadata"]["title"]
        == "Preserve proposed name"
    )
    assert get_course_changeset_status(instructor_user, course.id, session=db.session)[
        "has_changes"
    ]


def test_rejection_preserves_metadata_in_successor_draft(
    app, published_course, instructor_user, admin_user
):
    course, _ = published_course
    update_course(
        instructor_user,
        course.id,
        {"category": "Preserve category", "as_draft": True},
        session=db.session,
    )
    pending = submit_course_changeset(
        instructor_user, course.id, {"version_title": "First"}, session=db.session
    )
    reject_course_change_request(admin_user, pending.id, "Please revise", session=db.session)
    assert pending.status == "REJECTED"
    drafts = [r for r in active_requests(course) if r.status == "DRAFT"]
    assert len(drafts) == 1
    assert (
        json.loads(drafts[0].proposed_payload_json)["course_metadata"]["category"]
        == "Preserve category"
    )


def test_completion_rule_is_proposed_without_changing_live_values(
    app, published_course, instructor_user
):
    course, _ = published_course
    rule = get_or_create_default_completion_rule(course.id, session=db.session)
    original = rule.minimum_progress_percent
    set_course_completion_rule(
        instructor_user,
        course.id,
        {"minimum_progress_percent": 97, "minimum_grade_score": 8},
        session=db.session,
    )
    db.session.expire(rule)
    assert rule.minimum_progress_percent == original
    drafts = active_requests(course)
    assert len(drafts) == 1 and drafts[0].status == "DRAFT"
    assert (
        json.loads(drafts[0].proposed_payload_json)["completion_rules"]["minimum_progress_percent"]
        == 97
    )


def test_prerequisite_is_proposed_without_changing_live_graph(
    app, published_course, instructor_user
):
    course, _ = published_course
    prereq = create_course(
        instructor_user,
        {"course_code": "PREREQ-UNIFIED", "title": "Prerequisite example"},
        session=db.session,
    )
    prereq.status = "PUBLISHED"
    db.session.flush()
    add_course_prerequisite(instructor_user, course.id, prereq.id, session=db.session)
    assert db.session.query(CoursePrerequisite).filter_by(course_id=course.id).count() == 0
    draft = active_requests(course)[0]
    assert draft.status == "DRAFT"
    assert str(prereq.public_id) in json.loads(draft.proposed_payload_json)["prerequisites"]["add"]


def test_new_unit_is_owned_by_working_changeset(app, published_course, instructor_user):
    course, _ = published_course
    unit = create_learning_unit(
        instructor_user, course.id, {"title": "New draft unit"}, session=db.session
    )
    assert unit.change_request_id is not None
    assert db.session.get(CourseChangeRequest, unit.change_request_id).status == "DRAFT"


def test_approval_publishes_only_submitted_lesson_members(
    app, published_course, instructor_user, admin_user
):
    course, _ = published_course
    staged = create_lesson(
        instructor_user,
        course.id,
        {"title": "Submitted lesson", "markdown_content": "Submitted text"},
        session=db.session,
    )
    pending = submit_course_changeset(
        instructor_user, course.id, {"version_title": "Sealed submission"}, session=db.session
    )
    unit = db.session.query(LearningUnit).filter_by(course_id=course.id).first()
    unrelated = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Unrelated draft",
        markdown_content="Never submitted",
        position=999,
        status="DRAFT",
    )
    db.session.add(unrelated)
    db.session.flush()
    approve_course_change_request(admin_user, pending.id, session=db.session)
    assert staged.status == "PUBLISHED"
    assert unrelated.status == "DRAFT"


def test_initial_unapproved_authoring_stays_direct(app, instructor_user):
    course = create_course(
        instructor_user,
        {"course_code": "INITIAL-UNIFIED", "title": "Unapproved course"},
        session=db.session,
    )
    result = update_course(
        instructor_user, course.id, {"title": "Direct first draft"}, session=db.session
    )
    assert result is course
    assert course.title == "Direct first draft"
    assert active_requests(course) == []


def published_assessment(course, actor):
    from backend.services.assessment_service import create_assessment

    item = create_assessment(
        actor,
        course.id,
        {"title": "Approved examination", "assessment_type": "QUIZ"},
        session=db.session,
    )
    item.status = "PUBLISHED"
    item.published_at = utc_now()
    db.session.commit()
    return item


def test_assessment_metadata_edit_preserves_approved_identity(
    app, published_course, instructor_user, admin_user
):
    from backend.services.assessment_service import update_assessment

    course, _ = published_course
    original = published_assessment(course, admin_user)
    assert original.change_request_id is None
    result = update_assessment(
        instructor_user, original.id, {"title": "Proposed examination"}, session=db.session
    )
    assert original.title == "Approved examination"
    assert result.title == "Proposed examination"
    assert result.previous_assessment_id == original.id
    assert result.change_request_id == active_requests(course)[0].id


def test_assessment_sections_author_in_isolated_revision(
    app, published_course, instructor_user, admin_user
):
    from backend.models.assessment import AssessmentSection
    from backend.services.assessment_service import create_section

    course, _ = published_course
    original = published_assessment(course, admin_user)
    section = create_section(
        instructor_user, original.id, {"title": "Proposed section"}, session=db.session
    )
    assert section.assessment_id != original.id
    assert db.session.query(AssessmentSection).filter_by(assessment_id=original.id).count() == 0


def test_pending_course_review_blocks_assessment_mutation(
    app, published_course, instructor_user, admin_user
):
    from backend.services.assessment_service import update_assessment

    course, _ = published_course
    item = published_assessment(course, admin_user)
    update_course(instructor_user, course.id, {"category": "Review category"}, session=db.session)
    submit_course_changeset(
        instructor_user, course.id, {"version_title": "Review"}, session=db.session
    )
    with pytest.raises(ConflictError):
        update_assessment(
            instructor_user, item.id, {"title": "Blocked assessment"}, session=db.session
        )


def test_instructor_detail_projects_saved_draft(app, client, published_course, instructor_user):
    from tests.conftest import login_web_user

    course, _ = published_course
    update_course(instructor_user, course.id, {"title": "Authored draft title"}, session=db.session)
    db.session.commit()
    login_web_user(client, instructor_user)
    response = client.get(f"/instructor/courses/{course.public_id}")
    assert response.status_code == 200
    assert response.get_json()["title"] == "Authored draft title"
    assert course.title != "Authored draft title"


def test_atomic_landing_save_accepts_metadata_and_governance(
    app, client, published_course, instructor_user
):
    from tests.conftest import login_web_user

    course, _ = published_course
    original_title = course.title
    login_web_user(client, instructor_user)
    response = client.put(
        f"/instructor/courses/{course.public_id}/academic-settings",
        json={
            "course_metadata": {
                "title": "Atomic authored title",
                "contact_info": {"email": "instructor@example.com"},
            },
            "learning_objectives": ["Understand atomic review"],
            "completion_rules": {"minimum_progress_percent": 90, "minimum_grade_score": 7},
            "prerequisites": {"add": [], "remove": []},
        },
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["is_draft"] is True
    assert data["pending_approval"] is False
    assert data["course"]["title"] == "Atomic authored title"
    assert data["completion_rules"]["minimum_grade_score"] == 7
    assert course.title == original_title
    assert len(active_requests(course)) == 1


def test_admin_approval_requires_displayed_review_version(
    app, client, published_course, instructor_user, admin_user
):
    from tests.conftest import login_web_user

    course, _ = published_course
    update_course(
        instructor_user, course.id, {"category": "Needs review token"}, session=db.session
    )
    pending = submit_course_changeset(
        instructor_user, course.id, {"version_title": "Version fenced"}, session=db.session
    )
    db.session.commit()
    login_web_user(client, admin_user)
    response = client.post(
        f"/admin/course-changes/{pending.id}/approve",
        json={"request_id": pending.id, "review_version": "stale"},
    )
    assert response.status_code == 409
    assert pending.status == "PENDING"


def test_admin_queue_does_not_hide_distinct_legacy_requests(
    app, client, published_course, instructor_user, admin_user
):
    from tests.conftest import login_web_user

    course, _ = published_course
    for category in ("One proposal", "Another proposal"):
        db.session.add(
            CourseChangeRequest(
                course_id=course.id,
                requested_by_user_id=instructor_user.id,
                change_type="COURSE_METADATA",
                target_type="COURSE",
                target_id=course.id,
                status="PENDING",
                proposed_payload_json=json.dumps({"category": category}),
            )
        )
    db.session.commit()
    login_web_user(client, admin_user)
    response = client.get("/admin/change-requests?status=PENDING")
    assert response.status_code == 200
    assert response.get_json()["pending_count"] == 2
    assert len(response.get_json()["change_requests"]) == 2


def test_approval_rechecks_cover_ownership_and_scan(app, published_course, admin_user):
    course, _ = published_course
    with pytest.raises(CourseValidationError):
        update_course(
            admin_user,
            course.id,
            {"thumbnail_file_asset_id": "999999"},
            session=db.session,
            is_approved_review=True,
        )


def test_recorded_approval_history_cannot_be_downgraded_to_free_authoring(
    app, published_course, instructor_user
):
    course, _ = published_course
    course.status = "DRAFT"
    course.approved_at = None
    course.published_at = None
    course.approved_by_user_id = None
    db.session.flush()
    result = update_course(
        instructor_user, course.id, {"category": "Still needs review"}, session=db.session
    )
    assert isinstance(result, CourseChangeRequest)
    assert course.category != "Still needs review"


def test_legacy_fragment_cannot_bypass_sealed_aggregate_approval(
    app, client, published_course, instructor_user, admin_user
):
    from backend.services.course_workflow_service import review_version
    from tests.conftest import login_web_user

    course, _ = published_course
    old = course.category
    record = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=instructor_user.id,
        change_type="COURSE_METADATA",
        target_type="COURSE",
        target_id=course.id,
        status="PENDING",
        proposed_payload_json=json.dumps({"category": "Unsealed fragment"}),
    )
    db.session.add(record)
    db.session.commit()
    login_web_user(client, admin_user)
    response = client.post(
        f"/admin/change-requests/{record.id}/review",
        json={
            "action": "approve",
            "request_id": record.id,
            "review_version": review_version(record),
        },
    )
    assert response.status_code == 409
    assert course.category == old
    assert record.status == "PENDING"


def test_approved_initial_lessons_are_immutable_before_first_publish(
    app, instructor_user, admin_user
):
    from backend.services.course_service import change_course_status
    from backend.services.lesson_service import update_lesson

    course = create_course(
        instructor_user,
        {"course_code": "APPROVED-INITIAL", "title": "Approved initial graph"},
        session=db.session,
    )
    original = create_lesson(
        instructor_user,
        course.id,
        {"title": "Reviewed initial", "markdown_content": "Reviewed content"},
        session=db.session,
    )
    change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=db.session)
    change_course_status(admin_user, course.id, "APPROVED", session=db.session)
    db.session.commit()
    assert original.status == "DRAFT"
    staged = update_lesson(
        instructor_user, original.id, {"markdown_content": "Unreviewed content"}, session=db.session
    )
    added = create_lesson(
        instructor_user,
        course.id,
        {"title": "Unreviewed addition", "markdown_content": "New proposed content"},
        session=db.session,
    )
    assert staged.id != original.id
    assert original.markdown_content == "Reviewed content"
    change_course_status(instructor_user, course.id, "PUBLISHED", session=db.session)
    db.session.commit()
    assert original.status == "PUBLISHED"
    assert staged.status == added.status == "DRAFT"
    assert active_requests(course)[0].status == "DRAFT"


def test_legacy_prerequisite_review_cannot_create_unsealed_live_edge(
    app, instructor_user, published_course
):
    from backend.services.enrollment_service import review_prerequisite_request

    course, _ = published_course
    other = create_course(
        instructor_user,
        {"course_code": "LEGACY-PREREQ", "title": "Prerequisite legacy review"},
        session=db.session,
    )
    other.status = "PUBLISHED"
    db.session.commit()
    with pytest.raises(ConflictError):
        review_prerequisite_request(
            instructor_user, course.id, other.id, "APPROVE", session=db.session
        )
    assert db.session.query(CoursePrerequisite).filter_by(course_id=course.id).count() == 0


def test_two_cycle_approval_clears_live_markers_and_updates_fingerprint(
    app, instructor_user, admin_user, published_course
):
    from backend.services.course_workflow_service import course_review_version
    from backend.services.lesson_service import (
        approve_course_change_request,
        submit_course_changeset,
        update_lesson,
    )

    course, original_lesson = published_course
    v0 = course_review_version(course, session=db.session)

    # Cycle 1: Edit lesson in draft aggregate
    staged_lesson = update_lesson(
        instructor_user,
        original_lesson.id,
        {"title": "Lesson Title V2", "markdown_content": "Content V2"},
        session=db.session,
    )
    db.session.commit()
    assert staged_lesson.id != original_lesson.id
    assert staged_lesson.previous_lesson_id == original_lesson.id
    assert staged_lesson.status == "DRAFT"
    assert staged_lesson.change_request_id is not None

    req1 = submit_course_changeset(instructor_user, course.id, {}, session=db.session)
    db.session.commit()
    assert req1.status == "PENDING"

    # Admin approves cycle 1
    approve_course_change_request(
        admin_user, req1.id, review_reason="Approved Cycle 1", session=db.session
    )
    db.session.commit()

    db.session.expire_all()
    # Fresh session reads promoted live lesson
    live_v1 = db.session.get(Lesson, staged_lesson.id)
    assert live_v1.status == "PUBLISHED"
    # Invariant: live lesson marker must be None, not pointing to terminal req1
    assert live_v1.change_request_id is None

    # Review fingerprint must include live_v1 and differ from v0
    v1 = course_review_version(course, session=db.session)
    assert v1 != v0

    # Cycle 2: Edit again from fresh live_v1
    staged_v2 = update_lesson(
        instructor_user,
        live_v1.id,
        {"title": "Lesson Title V3", "markdown_content": "Content V3"},
        session=db.session,
    )
    db.session.commit()
    assert staged_v2.id != live_v1.id
    assert staged_v2.previous_lesson_id == live_v1.id
    assert staged_v2.status == "DRAFT"
    assert staged_v2.change_request_id is not None

    req2 = submit_course_changeset(instructor_user, course.id, {}, session=db.session)
    db.session.commit()
    assert req2.status == "PENDING"
    assert req2.id != req1.id

    # Admin approves cycle 2
    approve_course_change_request(
        admin_user, req2.id, review_reason="Approved Cycle 2", session=db.session
    )
    db.session.commit()

    db.session.expire_all()
    live_v2 = db.session.get(Lesson, staged_v2.id)
    assert live_v2.status == "PUBLISHED"
    assert live_v2.change_request_id is None

    # Review fingerprint must reflect V2
    v2 = course_review_version(course, session=db.session)
    assert v2 != v1 and v2 != v0
