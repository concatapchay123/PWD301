"""Resource mutations use the same course draft boundary as content edits."""

import io
import json
from datetime import timedelta
from unittest.mock import patch

import pytest

from backend.extensions import db
from backend.models.course import CourseChangeRequest, Lesson
from backend.models.file_import import FileAsset, LessonResource, QuestionRevisionResource
from backend.models.question_bank import Question, QuestionRevision
from backend.services.course_service import create_course
from backend.services.exceptions import ConflictError
from backend.services.file_service import (
    add_file_revision,
    attach_resource_to_lesson,
    detach_resource_from_lesson,
    restore_file_asset,
    store_file_stream,
    trash_file_asset,
)
from backend.services.lesson_service import create_learning_unit, create_lesson
from backend.services.scanner_service import ScanVerdict

pytest_plugins = ["tests.test_lesson_revision_lifecycle"]


def _uploaded_resource(owner, course, verdict="PASS"):
    scan = ScanVerdict(status=verdict, engine_name="fixture")
    with (
        patch("backend.services.file_service.scan_file_all_engines", return_value=[scan]),
        patch("backend.services.file_service.scan_blob_file", return_value=scan),
    ):
        return store_file_stream(
            owner,
            course.id,
            io.BytesIO(b"Private upload lifecycle"),
            "lifecycle.txt",
            session=db.session,
        )


@pytest.mark.parametrize("decision", ["pending", "approve", "reject", "withdraw"])
def test_retention_preserves_bytes_and_verdicts_of_retained_course_submission(
    app, published_course, instructor_user, admin_user, decision
):
    from backend.models.file_import import FileBlob, FileRevision, FileScanResult
    from backend.models.types import utc_now
    from backend.services.file_service import get_file_storage_root
    from backend.services.lesson_service import (
        approve_course_change_request,
        reject_course_change_request,
        retract_course_changeset,
        submit_course_changeset,
    )
    from backend.services.retention_service import prune_trash_entities

    course, _ = published_course
    asset = _uploaded_resource(instructor_user, course)
    revision = asset.current_revision
    blob = revision.blob
    path = get_file_storage_root() / blob.storage_key
    original_bytes = path.read_bytes()
    scan_ids = [item.id for item in revision.scan_results]
    submitted = submit_course_changeset(instructor_user, course.id, {}, session=db.session)
    if decision == "approve":
        approve_course_change_request(admin_user, submitted.id, "Approve file", session=db.session)
    elif decision == "reject":
        reject_course_change_request(
            admin_user, submitted.id, "Replace handout", session=db.session
        )
    elif decision == "withdraw":
        retract_course_changeset(instructor_user, course.id, session=db.session)
    db.session.commit()
    retained_payload = submitted.proposed_payload_json
    trash_file_asset(admin_user, asset.id, session=db.session)
    asset.restore_until = utc_now() - timedelta(days=1)
    db.session.commit()
    result = prune_trash_entities(session=db.session)
    db.session.commit()
    assert result["file_assets"] == 0
    assert db.session.get(FileAsset, asset.id) is not None
    assert db.session.get(FileRevision, revision.id) is not None
    assert db.session.get(FileBlob, blob.id).status == "PRESENT"
    assert all(db.session.get(FileScanResult, identifier) is not None for identifier in scan_ids)
    assert path.read_bytes() == original_bytes
    assert submitted.proposed_payload_json == retained_payload


def test_retention_still_prunes_expired_unsubmitted_private_upload(
    app, published_course, instructor_user
):
    from backend.models.types import utc_now
    from backend.services.file_service import get_file_storage_root
    from backend.services.retention_service import prune_trash_entities

    course, _ = published_course
    asset = _uploaded_resource(instructor_user, course)
    path = get_file_storage_root() / asset.current_revision.blob.storage_key
    trash_file_asset(instructor_user, asset.id, session=db.session)
    asset.restore_until = utc_now() - timedelta(days=1)
    db.session.commit()
    result = prune_trash_entities(session=db.session)
    db.session.commit()
    assert result["file_assets"] == 1
    assert db.session.get(FileAsset, asset.id) is None
    assert not path.exists()


@pytest.mark.parametrize("operation", ["revision", "trash", "restore"])
def test_approved_standalone_upload_cannot_mutate_approved_bytes(
    app, published_course, instructor_user, admin_user, operation
):
    from backend.services.lesson_service import (
        approve_course_change_request,
        submit_course_changeset,
    )

    course, _ = published_course
    asset = _uploaded_resource(instructor_user, course)
    record = submit_course_changeset(instructor_user, course.id, {}, session=db.session)
    approve_course_change_request(admin_user, record.id, "Approve handout", session=db.session)
    db.session.commit()
    original = asset.current_revision
    with pytest.raises(ConflictError, match="bản nháp|thay thế"):
        _mutate_file(operation, instructor_user, course, asset)
    assert asset.status == "ACTIVE"
    assert asset.current_revision.id == original.id


@pytest.mark.parametrize("operation", ["revision", "trash", "restore"])
def test_legacy_unreferenced_resource_is_an_immutable_approved_baseline(
    app, published_course, instructor_user, operation
):
    course, _ = published_course
    asset = _resource_asset(course, instructor_user)
    with pytest.raises(ConflictError, match="bản nháp|thay thế"):
        _mutate_file(operation, instructor_user, course, asset)


@pytest.mark.parametrize("verdict", ["FAIL", "ERROR"])
def test_unsafe_upload_is_private_ledger_only_and_does_not_poison_submission(
    app, client, published_course, instructor_user, admin_user, student_user, verdict
):
    from backend.services.course_service import update_course
    from backend.services.enrollment_service import enroll_student
    from backend.services.lesson_service import (
        approve_course_change_request,
        submit_course_changeset,
    )
    from tests.conftest import login_web_user

    course, _ = published_course
    asset = _uploaded_resource(instructor_user, course, verdict)
    record = (
        db.session.query(CourseChangeRequest).filter_by(course_id=course.id, status="DRAFT").one()
    )
    payload = json.loads(record.proposed_payload_json)
    assert str(asset.public_id) in payload.get("uploaded_file_assets", [])
    assert str(asset.public_id) not in payload.get("new_file_assets", [])
    trash_file_asset(instructor_user, asset.id, session=db.session)
    update_course(
        instructor_user, course.id, {"description": "Independent valid edit"}, session=db.session
    )
    submitted = submit_course_changeset(instructor_user, course.id, {}, session=db.session)
    approve_course_change_request(
        admin_user, submitted.id, "Approve valid edit", session=db.session
    )
    db.session.commit()
    assert course.description == "Independent valid edit"
    assert str(asset.public_id) not in json.loads(submitted.proposed_payload_json).get(
        "new_file_assets", []
    )
    enroll_student(student_user, course.id)
    login_web_user(client, student_user)
    assert client.get(f"/api/files/{asset.public_id}/download").status_code == 403


def test_trash_removes_clean_file_from_submission_but_restore_explicitly_rejoins(
    app, published_course, instructor_user
):
    course, _ = published_course
    asset = _uploaded_resource(instructor_user, course)
    record = (
        db.session.query(CourseChangeRequest).filter_by(course_id=course.id, status="DRAFT").one()
    )
    trash_file_asset(instructor_user, asset.id, session=db.session)
    payload = json.loads(record.proposed_payload_json)
    assert str(asset.public_id) in payload.get("uploaded_file_assets", [])
    assert str(asset.public_id) not in payload.get("new_file_assets", [])
    restore_file_asset(instructor_user, asset.id, session=db.session)
    payload = json.loads(record.proposed_payload_json)
    assert str(asset.public_id) in payload.get("new_file_assets", [])


def test_background_scan_recovery_never_releases_private_upload_without_explicit_review(
    app, client, published_course, instructor_user, admin_user, student_user
):
    from backend.models.file_import import FileScanResult
    from backend.models.types import utc_now
    from backend.services.course_service import update_course
    from backend.services.enrollment_service import enroll_student
    from backend.services.lesson_service import (
        approve_course_change_request,
        submit_course_changeset,
    )
    from tests.conftest import login_web_user

    course, _ = published_course
    asset = _uploaded_resource(instructor_user, course, "ERROR")
    clean = _uploaded_resource(instructor_user, course)
    revision = asset.revisions[0]
    revision.is_current = True
    revision.status = "ACTIVE"
    revision.blob_id = clean.current_revision.blob_id
    db.session.add(
        FileScanResult(
            file_revision_id=revision.id,
            scan_type="MALWARE",
            engine="fixture",
            status="PASS",
            completed_at=utc_now(),
        )
    )
    update_course(
        instructor_user, course.id, {"description": "Other reviewed edit"}, session=db.session
    )
    submitted = submit_course_changeset(instructor_user, course.id, {}, session=db.session)
    approve_course_change_request(
        admin_user, submitted.id, "Approve other edits", session=db.session
    )
    db.session.commit()
    enroll_student(student_user, course.id)
    login_web_user(client, student_user)
    response = client.get(f"/api/files/{asset.public_id}/download")
    assert response.status_code == 403
    response.close()


@pytest.mark.parametrize("decision", ["draft", "discard", "approve"])
def test_new_course_upload_is_private_until_aggregate_approval(
    app, client, published_course, instructor_user, student_user, admin_user, decision
):
    from unittest.mock import patch

    from backend.services.enrollment_service import enroll_student
    from backend.services.lesson_service import (
        approve_course_change_request,
        discard_course_changeset,
        submit_course_changeset,
    )
    from backend.services.scanner_service import ScanVerdict
    from tests.conftest import login_web_user

    course, _ = published_course
    clean = ScanVerdict(status="PASS", engine_name="fixture")
    with (
        patch("backend.services.file_service.scan_file_all_engines", return_value=[clean]),
        patch("backend.services.file_service.scan_blob_file", return_value=clean),
    ):
        asset = store_file_stream(
            instructor_user,
            course.id,
            io.BytesIO(b"Private proposed course handout"),
            "private-handout.txt",
            session=db.session,
        )
    enroll_student(student_user, course.id)
    if decision == "approve":
        record = submit_course_changeset(instructor_user, course.id, {}, session=db.session)
        approve_course_change_request(
            admin_user, record.id, "Approve complete course update", session=db.session
        )
    elif decision == "discard":
        discard_course_changeset(instructor_user, course.id, session=db.session)
    db.session.commit()
    login_web_user(client, student_user)
    response = client.get(f"/api/files/{asset.public_id}/download")
    assert response.status_code == (200 if decision == "approve" else 403), response.json
    response.close()
    response = client.get(f"/student/courses/{course.public_id}")
    assert response.status_code == 200
    data = response.json.get("data", response.json)
    visible = any(str(asset.public_id) == item.get("asset_id") for item in data["resources"])
    assert visible is (decision == "approve")


def _resource_asset(course, owner):
    asset = FileAsset(
        course_id=course.id,
        created_by_user_id=owner.id,
        asset_type="RESOURCE",
        display_name="Governance link fixture.pdf",
        status="ACTIVE",
    )
    db.session.add(asset)
    db.session.flush()
    return asset


def test_attachment_to_approved_lesson_only_changes_shared_draft(
    app, published_course, instructor_user
):
    course, live = published_course
    asset = _resource_asset(course, instructor_user)
    result = attach_resource_to_lesson(
        instructor_user, live.id, asset.id, session=db.session, commit=False
    )
    assert result.lesson_id != live.id
    assert db.session.query(LessonResource).filter_by(lesson_id=live.id).count() == 0
    staged = db.session.get(Lesson, result.lesson_id)
    assert staged.previous_lesson_id == live.id and staged.status == "DRAFT"
    request = db.session.get(CourseChangeRequest, staged.change_request_id)
    assert request.change_type == "COURSE_VERSION_CHANGESET" and request.status == "DRAFT"
    assert (
        db.session.query(CourseChangeRequest).filter_by(course_id=course.id, status="DRAFT").count()
        == 1
    )


def test_detachment_maps_original_resource_to_copied_draft_link(
    app, published_course, instructor_user
):
    course, live = published_course
    asset = _resource_asset(course, instructor_user)
    original = LessonResource(
        lesson_id=live.id, file_asset_id=asset.id, position=1, label="Keep live"
    )
    db.session.add(original)
    db.session.flush()
    assert detach_resource_from_lesson(
        instructor_user, live.id, original.public_id, session=db.session, commit=False
    )
    assert db.session.get(LessonResource, original.id) is original
    staged = db.session.query(Lesson).filter_by(previous_lesson_id=live.id, status="DRAFT").one()
    assert db.session.query(LessonResource).filter_by(lesson_id=staged.id).count() == 0


@pytest.mark.parametrize("operation", ["attach", "detach"])
def test_initial_submission_freezes_resource_changes(app, instructor_user, operation):
    course = create_course(
        instructor_user,
        {"course_code": "RESOURCE-FREEZE", "title": "Initial review"},
        session=db.session,
    )
    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit"}, session=db.session)
    lesson = create_lesson(
        instructor_user,
        course.id,
        {"title": "Lesson", "markdown_content": "Content", "learning_unit_id": str(unit.public_id)},
        session=db.session,
    )
    asset = _resource_asset(course, instructor_user)
    resource = attach_resource_to_lesson(
        instructor_user, lesson.id, asset.id, session=db.session, commit=False
    )
    course.status = "SUBMITTED_FOR_REVIEW"
    db.session.flush()
    with pytest.raises(ConflictError):
        if operation == "attach":
            attach_resource_to_lesson(
                instructor_user,
                lesson.id,
                asset.id,
                label="Frozen",
                session=db.session,
                commit=False,
            )
        else:
            detach_resource_from_lesson(
                instructor_user, lesson.id, resource.id, session=db.session, commit=False
            )
    assert db.session.get(LessonResource, resource.id) is resource
    assert resource.label != "Frozen"


def test_resource_staging_never_commits_an_external_transaction(
    app, published_course, instructor_user
):
    course, live = published_course
    asset = _resource_asset(course, instructor_user)
    db.session.commit()
    result = attach_resource_to_lesson(
        instructor_user, live.id, asset.id, session=db.session, commit=False
    )
    staged_id = result.lesson_id
    db.session.rollback()
    assert db.session.get(Lesson, staged_id) is None
    assert (
        db.session.query(CourseChangeRequest).filter_by(course_id=course.id, status="DRAFT").count()
        == 0
    )


def _mutate_file(operation, actor, course, asset):
    if operation == "upload":
        return store_file_stream(
            actor, course.id, io.BytesIO(b"New content"), "new.txt", session=db.session
        )
    if operation == "revision":
        return add_file_revision(
            actor, asset.id, io.BytesIO(b"Revised content"), "new.txt", session=db.session
        )
    if operation == "trash":
        return trash_file_asset(actor, asset.id, session=db.session)
    return restore_file_asset(actor, asset.id, session=db.session)


@pytest.mark.parametrize("operation", ["upload", "revision", "trash", "restore"])
@pytest.mark.parametrize("pending", ["initial", "aggregate"])
def test_every_file_mutation_respects_pending_freeze(
    app, instructor_user, published_course, operation, pending
):
    if pending == "initial":
        course = create_course(
            instructor_user,
            {"course_code": "FILE-FROZEN", "title": "Initial submission"},
            session=db.session,
        )
        course.status = "SUBMITTED_FOR_REVIEW"
    else:
        course, _ = published_course
        db.session.add(
            CourseChangeRequest(
                course_id=course.id,
                requested_by_user_id=instructor_user.id,
                change_type="COURSE_VERSION_CHANGESET",
                target_type="COURSE",
                target_id=course.id,
                status="PENDING",
                proposed_payload_json='{"action":"COURSE_VERSION_CHANGESET"}',
            )
        )
    asset = _resource_asset(course, instructor_user)
    original_status = asset.status
    with pytest.raises(ConflictError):
        _mutate_file(operation, instructor_user, course, asset)
    assert asset.status == original_status


@pytest.mark.parametrize("operation", ["revision", "trash", "restore"])
@pytest.mark.parametrize("reference", ["cover", "lesson", "question", "historical_question"])
def test_approved_referenced_file_requires_staged_replacement(
    app, instructor_user, published_course, operation, reference
):
    course, live = published_course
    asset = _resource_asset(course, instructor_user)
    if reference == "cover":
        course.thumbnail_file_asset_id = asset.id
    elif reference == "lesson":
        db.session.add(LessonResource(lesson_id=live.id, file_asset_id=asset.id, position=1))
    else:
        question = Question(
            course_id=course.id,
            creator_user_id=instructor_user.id,
            difficulty="REMEMBER",
            status="ACTIVE" if reference == "question" else "DRAFT",
        )
        db.session.add(question)
        db.session.flush()
        revision = QuestionRevision(
            question_id=question.id,
            revision_no=1,
            question_type="SINGLE_CHOICE",
            content="Referenced image",
            was_student_exposed=reference == "historical_question",
        )
        db.session.add(revision)
        db.session.flush()
        db.session.add(
            QuestionRevisionResource(
                question_revision_id=revision.id, file_asset_id=asset.id, position=1
            )
        )
    db.session.flush()
    with pytest.raises(ConflictError, match="bản nháp|thay thế"):
        _mutate_file(operation, instructor_user, course, asset)
    assert asset.status == "ACTIVE"


def test_unreferenced_file_and_draft_only_reference_remain_editable(
    app, instructor_user, published_course
):
    course, live = published_course
    asset = _resource_asset(course, instructor_user)
    attached = attach_resource_to_lesson(
        instructor_user, live.id, asset.id, session=db.session, commit=False
    )
    assert attached.lesson_id != live.id
    trash_file_asset(instructor_user, asset.id, session=db.session)
    assert asset.status == "TRASH"
    restore_file_asset(instructor_user, asset.id, session=db.session)
    assert asset.status == "ACTIVE"


def test_unreferenced_upload_and_revision_remain_available_in_one_draft_after_approval(
    app, instructor_user, published_course
):
    course, _ = published_course
    asset = store_file_stream(
        instructor_user,
        course.id,
        io.BytesIO(b"Initial unreferenced content"),
        "standalone.txt",
        session=db.session,
    )
    revised = add_file_revision(
        instructor_user,
        asset.id,
        io.BytesIO(b"Revised unreferenced content"),
        "standalone.txt",
        session=db.session,
    )
    assert revised.file_asset_id == asset.id and revised.revision_no == 2
    assert (
        db.session.query(CourseChangeRequest).filter_by(course_id=course.id, status="DRAFT").count()
        == 1
    )
