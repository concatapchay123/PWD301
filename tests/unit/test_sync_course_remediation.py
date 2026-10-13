"""Service regressions for synchronization audit course findings."""

import io
import json
from datetime import timedelta

import pytest

from pwd301.extensions import db
from pwd301.models.course import (
    CourseChangeRequest,
    Enrollment,
    EnrollmentPeriod,
    Lesson,
    LessonProgress,
)
from pwd301.models.file_import import ImportQuestion, LessonResource
from pwd301.models.question_bank import Question
from pwd301.models.types import utc_now
from pwd301.services import import_service
from pwd301.services import lesson_service as service
from pwd301.services.file_service import store_file_stream
from tests.unit.test_import_service import create_sample_docx

pytest_plugins = ["tests.test_lesson_revision_lifecycle"]


@pytest.mark.parametrize("marker", ["mini_quiz_passing", "quiz_passing_percent"])
@pytest.mark.parametrize("threshold", [50, 100])
def test_student_delivery_preserves_both_authored_quiz_threshold_spellings(
    app, published_course, marker, threshold
):
    from pwd301.blueprints.student.routes import _serialize_student_lesson

    _, lesson = published_course
    lesson.markdown_content = (
        '<!-- mini_quiz:[{"question":"One?","options":["A","B"],"correct_index":0}] -->'
        f"\n<!-- {marker}:{threshold} -->"
    )
    db.session.commit()
    with app.test_request_context():
        delivery = _serialize_student_lesson(lesson, None)
    assert delivery["quiz_passing_percent"] == threshold


def test_quiz_acknowledgement_is_exposed_for_fresh_student_delivery(
    app, published_course, student_user
):
    from pwd301.blueprints.student.routes import _serialize_student_lesson

    course, lesson = published_course
    progress = enrolled_progress(course, lesson, student_user)
    progress.completion_rule_snapshot_json = json.dumps(
        {"mini_quiz_completed_at": "2026-10-12T00:00:00+00:00", "personal_notes": "Private notes"}
    )
    db.session.commit()
    db.session.expire_all()
    with app.test_request_context():
        delivery = _serialize_student_lesson(lesson, progress)
    assert delivery["progress"]["mini_quiz_completed_at"] == "2026-10-12T00:00:00+00:00"
    assert "completion_rule_snapshot_json" not in delivery["progress"]


def request(course, actor, payload):
    req = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=actor.id,
        change_type="LESSON_STRUCTURE",
        target_type="COURSE",
        target_id=course.id,
        status="PENDING",
        proposed_payload_json=json.dumps(payload),
    )
    db.session.add(req)
    db.session.commit()
    return req


def test_unrelated_structure_request_survives_submission(app, instructor_user, published_course):
    course, lesson = published_course
    unrelated = request(course, instructor_user, {"action": "REORDER_UNITS", "units_order": [1]})
    service.submit_course_changeset(
        instructor_user,
        course.id,
        {
            "version_title": "New",
            "modified_lessons": [{"lesson_id": str(lesson.public_id), "title": "New"}],
        },
        session=db.session,
    )
    assert unrelated.status == "PENDING"


@pytest.mark.parametrize("changeset", [False, True])
def test_approval_preserves_detached_resources(
    app, instructor_user, admin_user, published_course, changeset
):
    course, lesson = published_course
    asset = store_file_stream(
        instructor_user, course.id, io.BytesIO(b"document"), "notes.txt", session=db.session
    )
    db.session.add(LessonResource(lesson_id=lesson.id, file_asset_id=asset.id, position=1))
    db.session.commit()
    req, staged = service.create_lesson_change_request(
        instructor_user,
        course.id,
        {"position": lesson.position, "title": "Updated", "markdown_content": "Updated"},
        session=db.session,
    )
    db.session.query(LessonResource).filter_by(lesson_id=staged.id).delete()
    if changeset:
        req.proposed_payload_json = json.dumps({"action": "COURSE_VERSION_CHANGESET"})
    db.session.commit()
    service.approve_course_change_request(admin_user, req.id, session=db.session)
    assert db.session.query(LessonResource).filter_by(lesson_id=staged.id).count() == 0


def test_student_delivery_does_not_resurrect_removed_historical_resource(
    app, instructor_user, admin_user, published_course
):
    from pwd301.blueprints.student.routes import _serialize_student_lesson

    course, original = published_course
    asset = store_file_stream(
        instructor_user,
        course.id,
        io.BytesIO(b"Historic document"),
        "historical.txt",
        session=db.session,
    )
    db.session.add(LessonResource(lesson_id=original.id, file_asset_id=asset.id, position=1))
    db.session.commit()
    req, staged = service.create_lesson_change_request(
        instructor_user,
        course.id,
        {
            "target_id": original.id,
            "position": original.position,
            "title": "Detached current lesson",
            "markdown_content": "Current text",
        },
        session=db.session,
    )
    db.session.query(LessonResource).filter_by(lesson_id=staged.id).delete()
    db.session.commit()
    service.approve_course_change_request(admin_user, req.id, session=db.session)
    db.session.commit()
    db.session.expire_all()
    assert db.session.query(LessonResource).filter_by(lesson_id=original.id).count() == 1
    assert db.session.query(LessonResource).filter_by(lesson_id=staged.id).count() == 0
    with app.test_request_context():
        delivered = _serialize_student_lesson(staged, None)
    assert delivered["resources"] == []


@pytest.mark.parametrize("alternate", [False, True])
def test_two_payload_additions_allocate_distinct_positions(
    app, instructor_user, admin_user, published_course, alternate
):
    course, _ = published_course
    payload = {
        "action": "COURSE_VERSION_CHANGESET",
        "added_lessons": [{"title": "One"}, {"title": "Two"}],
    }
    if alternate:
        service.apply_course_version_changeset(admin_user, course.id, payload, session=db.session)
    else:
        req = request(course, instructor_user, payload)
        service.approve_course_change_request(admin_user, req.id, session=db.session)
    db.session.flush()
    lessons = db.session.query(Lesson).filter_by(course_id=course.id, status="PUBLISHED").all()
    assert len(lessons) == 3
    assert sorted(x.position for x in lessons) == [1, 2, 3]


def test_approval_propagates_deletion_failure(
    app, instructor_user, admin_user, published_course, monkeypatch
):
    course, lesson = published_course
    req = request(
        course,
        instructor_user,
        {"action": "COURSE_VERSION_CHANGESET", "deleted_lessons": [str(lesson.public_id)]},
    )

    def fail(*args, **kwargs):
        raise RuntimeError("delete failed")

    monkeypatch.setattr(service, "trash_lesson", fail)
    with pytest.raises(RuntimeError, match="delete failed"):
        service.approve_course_change_request(admin_user, req.id, session=db.session)
    db.session.rollback()
    assert db.session.get(CourseChangeRequest, req.id).status == "PENDING"


@pytest.mark.parametrize(
    "field,value", [("label", "Renamed"), ("is_required", True), ("position", 2)]
)
def test_resource_metadata_change_keeps_draft(app, instructor_user, published_course, field, value):
    course, lesson = published_course
    asset = store_file_stream(
        instructor_user, course.id, io.BytesIO(b"document"), "notes.txt", session=db.session
    )
    db.session.add(LessonResource(lesson_id=lesson.id, file_asset_id=asset.id, position=1))
    db.session.commit()
    _, staged = service.create_lesson_change_request(
        instructor_user,
        course.id,
        {
            "target_id": lesson.id,
            "position": lesson.position,
            "title": lesson.title,
            "markdown_content": lesson.markdown_content,
            "learning_unit_id": str(lesson.learning_unit.public_id),
            "minimum_completion_seconds": lesson.minimum_completion_seconds,
            "viewed_fraction_required": float(lesson.viewed_fraction_required),
        },
        session=db.session,
    )
    service._copy_lesson_resources(lesson.id, staged.id, session=db.session)
    staged.previous_lesson_id = lesson.id
    resource = db.session.query(LessonResource).filter_by(lesson_id=staged.id).one()
    setattr(resource, field, value)
    db.session.flush()
    service.submit_course_changeset(instructor_user, course.id, {}, session=db.session)
    assert staged.deleted_at is None


def enrolled_progress(course, lesson, student):
    enrollment = Enrollment(student_user_id=student.id, course_id=course.id, status="ACTIVE")
    db.session.add(enrollment)
    db.session.flush()
    period = EnrollmentPeriod(enrollment_id=enrollment.id, period_no=1, status="ACTIVE")
    db.session.add(period)
    db.session.flush()
    enrollment.current_period_id = period.id
    progress = LessonProgress(
        enrollment_period_id=period.id,
        lesson_id=lesson.id,
        seconds_spent=0,
        max_view_fraction=0,
        last_activity_at=utc_now(),
    )
    db.session.add(progress)
    db.session.commit()
    return progress


def test_progress_event_survives_worker_memory_reset(app, published_course, student_user):
    course, lesson = published_course
    progress = enrolled_progress(course, lesson, student_user)
    instant = utc_now()
    instant = instant.replace(microsecond=(instant.microsecond // 1000) * 1000)
    service.record_lesson_progress(student_user, lesson.id, 5, 0.1, "event-one", now=instant)
    if hasattr(service, "_RECENT_CLIENT_EVENT_IDS"):
        service._RECENT_CLIENT_EVENT_IDS.clear()
    service.record_lesson_progress(
        student_user, lesson.id, 5, 0.1, "event-one", now=instant + timedelta(seconds=5)
    )
    assert progress.seconds_spent == 5
    assert service._to_naive_utc(progress.last_activity_at) == service._to_naive_utc(instant)


def test_progress_event_rollback_can_be_retried(app, published_course, student_user):
    course, lesson = published_course
    progress = enrolled_progress(course, lesson, student_user)
    service.record_lesson_progress(student_user, lesson.id, 5, 0.1, "retry-one", session=db.session)
    db.session.rollback()
    service.record_lesson_progress(student_user, lesson.id, 5, 0.1, "retry-one")
    assert progress.seconds_spent == 5


def test_progress_refreshes_stale_identity_map(app, published_course, student_user):
    course, lesson = published_course
    progress = enrolled_progress(course, lesson, student_user)
    db.session.execute(
        LessonProgress.__table__.update()
        .where(LessonProgress.id == progress.id)
        .values(seconds_spent=9)
    )
    service.record_lesson_progress(student_user, lesson.id, 5, 0.1, session=db.session)
    assert progress.seconds_spent == 14


def import_job(course, actor):
    content = create_sample_docx(["Question 1: First?", "A. One", "B. Two", "Answer: A"])
    asset = store_file_stream(
        actor,
        course.id,
        io.BytesIO(content),
        "questions.docx",
        asset_type="IMPORT_SOURCE",
        session=db.session,
    )
    job = import_service.create_import_job(actor, course.id, asset.id, session=db.session)
    return job, content


def accepted_job(course, actor):
    job, _ = import_job(course, actor)
    job.status = "REVIEW_REQUIRED"
    for ordinal in (1, 2):
        db.session.add(
            ImportQuestion(
                import_job_id=job.id,
                ordinal=ordinal,
                detected_type="ESSAY",
                content_text=f"Essay {ordinal}",
                confidence_score=1,
                review_state="ACCEPTED",
            )
        )
    db.session.commit()
    return job


def test_import_failure_rolls_back_earlier_questions(
    app, published_course, instructor_user, monkeypatch
):
    course, _ = published_course
    job = accepted_job(course, instructor_user)
    original = import_service.create_question

    def create(*args, **kwargs):
        if kwargs["payload"]["content"] == "Essay 2":
            raise RuntimeError("second item failed")
        return original(*args, **kwargs)

    monkeypatch.setattr(import_service, "create_question", create)
    with pytest.raises(RuntimeError, match="second item failed"):
        import_service.commit_import_job(instructor_user, job.id, session=db.session)
    db.session.rollback()
    assert db.session.query(Question).filter_by(course_id=course.id).count() == 0
    assert job.status == "REVIEW_REQUIRED"


def test_import_commit_respects_caller_transaction(app, published_course, instructor_user):
    course, _ = published_course
    job = accepted_job(course, instructor_user)
    import_service.commit_import_job(instructor_user, job.id, session=db.session)
    db.session.rollback()
    assert db.session.query(Question).filter_by(course_id=course.id).count() == 0
    assert job.status == "REVIEW_REQUIRED"


def test_cloud_import_materializes_pruned_source(
    app, published_course, instructor_user, monkeypatch
):
    from pwd301.services import file_service

    course, _ = published_course
    job, content = import_job(course, instructor_user)
    blob = job.source_file_asset.current_revision.blob
    (file_service.get_file_storage_root() / blob.storage_key).unlink()
    blob.storage_backend = "s3"
    blob.cloud_verified_at = utc_now()
    db.session.commit()

    def download(key, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return True

    monkeypatch.setattr(file_service, "download_blob_from_cloud", download)
    result = import_service.process_import_job(instructor_user, job.id, session=db.session)
    assert result.status == "REVIEW_REQUIRED"
    assert result.question_count == 1


@pytest.mark.parametrize("transport", ["complete", "corrupt", "unavailable"])
def test_cloud_import_uses_local_s3_http_after_pruning(
    app, published_course, instructor_user, transport
):
    """Real boto3 HTTP against a local protocol fixture, without claiming B2 delivery."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    from pwd301.services import file_service
    from pwd301.services.exceptions import FileAccessDeniedError
    from pwd301.services.import_service import DocumentParsingError

    course, _ = published_course
    job, content = import_job(course, instructor_user)
    blob = job.source_file_asset.current_revision.blob
    key = blob.storage_key
    (file_service.get_file_storage_root() / key).unlink()
    blob.storage_backend = "s3"
    blob.cloud_verified_at = utc_now()
    db.session.commit()
    requests = []
    payload = content if transport == "complete" else b"!" * len(content)

    class LocalObjectHandler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def serve_object(self, send_body):
            requests.append((self.command, self.path, self.headers.get("Authorization", "")))
            if transport == "unavailable":
                self.send_response(503)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("ETag", '"local-object-test"')
            self.end_headers()
            if send_body:
                self.wfile.write(payload)

        def do_HEAD(self):
            self.serve_object(False)

        def do_GET(self):
            self.serve_object(True)

    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalObjectHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    app.config.update(
        STORAGE_BACKEND="s3",
        S3_BUCKET_NAME="local-import-test",
        S3_ENDPOINT_URL=f"http://127.0.0.1:{server.server_port}",
        S3_ACCESS_KEY_ID="local-test-key",
        S3_SECRET_ACCESS_KEY="local-test-secret",
        S3_REGION_NAME="us-east-1",
    )
    try:
        with pytest.raises(FileAccessDeniedError):
            file_service.get_file_for_download(None, job.source_file_asset_id, session=db.session)
        assert requests == []
        cache_path = file_service.get_file_storage_root() / "cache" / key
        if transport == "complete":
            result = import_service.process_import_job(instructor_user, job.id, session=db.session)
            db.session.expire_all()
            assert result.status == "REVIEW_REQUIRED"
            assert result.question_count == 1
            assert cache_path.read_bytes() == content
        else:
            with pytest.raises(DocumentParsingError):
                import_service.process_import_job(instructor_user, job.id, session=db.session)
            db.session.expire_all()
            assert job.status == "FAILED"
            assert db.session.query(ImportQuestion).filter_by(import_job_id=job.id).count() == 0
            assert not cache_path.exists()
            assert not list(cache_path.parent.glob("*.partial"))
        assert requests
        assert all(path == f"/local-import-test/{key}" for _, path, _ in requests)
        assert all(auth.startswith("AWS4-HMAC-SHA256 ") for _, _, auth in requests)
        if transport != "unavailable":
            assert {method for method, _, _ in requests} == {"HEAD", "GET"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_mini_quiz_uses_authored_passing_threshold(app, published_course, student_user):
    course, lesson = published_course
    enrolled_progress(course, lesson, student_user)
    quiz = [
        {"question": "One?", "options": ["A", "B"], "correct_index": 0},
        {"question": "Two?", "options": ["A", "B"], "correct_index": 0},
    ]
    lesson.markdown_content = (
        f"<!-- mini_quiz:{json.dumps(quiz)} -->\n<!-- mini_quiz_passing:50 -->"
    )
    db.session.commit()
    progress = service.complete_lesson_mini_quiz(
        student_user, lesson.id, [0, 1], session=db.session
    )
    assert "mini_quiz_completed_at" in json.loads(progress.completion_rule_snapshot_json)


def test_approval_keeps_unrelated_pending_request(
    app, published_course, instructor_user, admin_user
):
    course, lesson = published_course
    unrelated = request(course, instructor_user, {"action": "REORDER_UNITS"})
    req = request(course, instructor_user, {"action": "COURSE_VERSION_CHANGESET"})
    service.approve_course_change_request(admin_user, req.id, session=db.session)
    assert unrelated.status == "PENDING"


def test_change_request_resave_keeps_detached_resources(app, published_course, instructor_user):
    course, lesson = published_course
    asset = store_file_stream(
        instructor_user, course.id, io.BytesIO(b"document"), "notes.txt", session=db.session
    )
    db.session.add(LessonResource(lesson_id=lesson.id, file_asset_id=asset.id, position=1))
    db.session.commit()
    payload = {
        "target_id": lesson.id,
        "position": lesson.position,
        "title": "Updated",
        "markdown_content": "Updated",
    }
    _, staged = service.create_lesson_change_request(
        instructor_user, course.id, payload, session=db.session
    )
    db.session.query(LessonResource).filter_by(lesson_id=staged.id).delete()
    db.session.commit()
    service.create_lesson_change_request(instructor_user, course.id, payload, session=db.session)
    assert db.session.query(LessonResource).filter_by(lesson_id=staged.id).count() == 0


def test_staged_edit_retains_original_revision_identity(app, published_course, instructor_user):
    course, lesson = published_course
    _, staged = service.create_lesson_change_request(
        instructor_user,
        course.id,
        {
            "target_id": lesson.id,
            "position": lesson.position,
            "title": "Updated",
            "markdown_content": "Updated",
        },
        session=db.session,
    )
    assert staged.previous_lesson_id == lesson.id


def test_change_request_rejects_missing_target(app, published_course, instructor_user):
    from pwd301.services.exceptions import LessonValidationError

    course, lesson = published_course
    with pytest.raises(LessonValidationError):
        service.create_lesson_change_request(
            instructor_user,
            course.id,
            {
                "target_id": 99999,
                "position": lesson.position,
                "title": "Updated",
                "markdown_content": "Updated",
            },
            session=db.session,
        )


@pytest.mark.parametrize("alternate", [False, True])
def test_added_lesson_rejects_invalid_unit(
    app, published_course, instructor_user, admin_user, alternate
):
    from pwd301.services.exceptions import LessonValidationError

    course, _ = published_course
    payload = {
        "action": "COURSE_VERSION_CHANGESET",
        "added_lessons": [{"title": "Invalid", "learning_unit_id": "99999"}],
    }
    with pytest.raises(LessonValidationError):
        if alternate:
            service.apply_course_version_changeset(
                admin_user, course.id, payload, session=db.session
            )
        else:
            req = request(course, instructor_user, payload)
            service.approve_course_change_request(admin_user, req.id, session=db.session)
