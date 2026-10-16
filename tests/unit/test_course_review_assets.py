"""Course review binds referenced bytes and fail-closed scan evidence."""

import hashlib

import pytest

from pwd301.extensions import db
from pwd301.models.course import CourseChangeRequest
from pwd301.models.file_import import (
    FileAsset,
    FileBlob,
    FileRevision,
    FileScanResult,
    LessonResource,
)
from pwd301.models.types import utc_now
from pwd301.services.course_service import update_course
from pwd301.services.course_workflow_service import course_review_version
from pwd301.services.exceptions import ConflictError
from pwd301.services.lesson_service import (
    approve_course_change_request,
    submit_course_changeset,
    update_lesson,
)

pytest_plugins = ["tests.test_lesson_revision_lifecycle"]


def clean_asset(course, owner):
    now = utc_now()
    asset = FileAsset(
        course_id=course.id,
        created_by_user_id=owner.id,
        asset_type="RESOURCE",
        display_name="review.png",
        status="ACTIVE",
    )
    blob = FileBlob(
        sha256=hashlib.sha256(b"review bytes").digest(),
        size_bytes=12,
        detected_mime_type="image/png",
        storage_key="review.png",
        status="PRESENT",
        reference_count=1,
    )
    db.session.add_all([asset, blob])
    db.session.flush()
    revision = FileRevision(
        file_asset_id=asset.id,
        revision_no=1,
        is_current=True,
        blob_id=blob.id,
        original_filename="review.png",
        detected_mime_type="image/png",
        size_bytes=12,
        status="ACTIVE",
        uploaded_by_user_id=owner.id,
        security_checks_completed_at=now,
        activated_at=now,
    )
    db.session.add(revision)
    db.session.flush()
    db.session.add(
        FileScanResult(
            file_revision_id=revision.id,
            scan_type="MALWARE",
            engine="fixture",
            status="PASS",
            started_at=now,
            completed_at=now,
        )
    )
    db.session.commit()
    return asset, revision, blob


@pytest.mark.parametrize("reference", ["lesson", "cover", "question"])
@pytest.mark.parametrize("mutation", ["quarantine", "revision", "scan"])
def test_changed_submitted_asset_blocks_atomic_approval(
    app, published_course, instructor_user, admin_user, reference, mutation
):
    course, lesson = published_course
    asset, revision, blob = clean_asset(course, instructor_user)
    if reference == "lesson":
        staged = update_lesson(
            instructor_user, lesson.id, {"title": "Sealed resource proposal"}, session=db.session
        )
        db.session.add(LessonResource(lesson_id=staged.id, file_asset_id=asset.id, position=1))
    elif reference == "cover":
        update_course(
            instructor_user, course.id, {"thumbnail_file_asset_id": asset.id}, session=db.session
        )
    else:
        from pwd301.services.question_bank_service import create_question

        create_question(
            instructor_user,
            course.id,
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "Reviewed question",
                "choices": [
                    {"content": "Yes", "is_correct": True},
                    {"content": "No", "is_correct": False},
                ],
                "resources": [{"asset_id": str(asset.public_id), "position": 1}],
            },
            session=db.session,
        )
    pending = submit_course_changeset(instructor_user, course.id, {}, session=db.session)
    db.session.commit()
    if mutation == "quarantine":
        revision.status = "QUARANTINED"
    elif mutation == "revision":
        revision.status = "REPLACED"
        revision.is_current = False
        db.session.flush()
        replacement = FileRevision(
            file_asset_id=asset.id,
            revision_no=2,
            is_current=True,
            blob_id=blob.id,
            original_filename="review.png",
            detected_mime_type="image/png",
            size_bytes=12,
            status="ACTIVE",
            uploaded_by_user_id=admin_user.id,
        )
        db.session.add(replacement)
        db.session.flush()
        db.session.add(
            FileScanResult(
                file_revision_id=replacement.id,
                scan_type="MALWARE",
                engine="fixture",
                status="PASS",
                started_at=utc_now(),
            )
        )
    else:
        db.session.add(
            FileScanResult(
                file_revision_id=revision.id,
                scan_type="MALWARE",
                engine="fixture",
                status="ERROR",
                started_at=utc_now(),
            )
        )
    db.session.commit()
    original_title = lesson.title
    with pytest.raises(ConflictError):
        approve_course_change_request(admin_user, pending.id, session=db.session)
    db.session.rollback()
    assert db.session.get(CourseChangeRequest, pending.id).status == "PENDING"
    assert lesson.title == original_title and lesson.status == "PUBLISHED"


def test_initial_review_identity_includes_referenced_asset_bytes(
    app, published_course, instructor_user
):
    course, lesson = published_course
    asset, revision, blob = clean_asset(course, instructor_user)
    course.status = "SUBMITTED_FOR_REVIEW"
    course.approved_at = course.published_at = course.approved_by_user_id = None
    db.session.add(LessonResource(lesson_id=lesson.id, file_asset_id=asset.id, position=1))
    db.session.commit()
    before = course_review_version(course)
    blob.sha256 = hashlib.sha256(b"different bytes").digest()
    db.session.commit()
    assert course_review_version(course) != before


def test_initial_review_identity_includes_current_question_answers(
    app, published_course, admin_user
):
    from pwd301.services.question_bank_service import create_question

    course, _ = published_course
    question = create_question(
        admin_user,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Reviewed question",
            "choices": [
                {"content": "Yes", "is_correct": True},
                {"content": "No", "is_correct": False},
            ],
        },
        session=db.session,
    )
    db.session.commit()
    before = course_review_version(course)
    question.current_revision.content = "Changed after displayed review"
    db.session.commit()
    assert course_review_version(course) != before
