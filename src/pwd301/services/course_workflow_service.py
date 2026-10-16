"""Shared course authoring boundary and immutable review identities."""

from __future__ import annotations

import hashlib
import json
import uuid
from contextlib import contextmanager
from typing import Any

import sqlalchemy as sa

from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, LearningUnit, Lesson
from pwd301.models.file_import import FileAsset
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import require_course_manager
from pwd301.services.exceptions import ConflictError, CourseValidationError

CHANGESET = "COURSE_VERSION_CHANGESET"


def course_requires_review(course: Course) -> bool:
    """Approval history survives withdrawal, archiving and legacy missing timestamps."""
    known_approval = bool(
        course.approved_at is not None
        or course.approved_by_user_id is not None
        or course.published_at is not None
        or course.status in ("APPROVED", "PUBLISHED", "ARCHIVED")
    )
    if known_approval or course.id is None:
        return known_approval
    from pwd301.models.notification_audit import AuditEvent

    session = sa.orm.object_session(getattr(course, "_original", course)) or db.session
    return (
        session.query(AuditEvent.id)
        .filter_by(target_type="COURSE", target_id=course.id, action="COURSE_APPROVED")
        .first()
        is not None
    )


def applying_course_review(session) -> bool:
    return bool(session.info.get("course_workflow_applying"))


@contextmanager
def applying_review(session):
    previous = session.info.get("course_workflow_applying")
    session.info["course_workflow_applying"] = True
    try:
        yield
    finally:
        if previous is None:
            session.info.pop("course_workflow_applying", None)
        else:
            session.info["course_workflow_applying"] = previous


def lock_course(course: Course, session):
    return (
        session.query(Course)
        .filter(Course.id == course.id)
        .with_hint(Course, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql")
        .with_for_update()
        .populate_existing()
        .one()
    )


def active_changeset(course_id: int, session=None):
    sess = session if session is not None else db.session
    records = (
        sess.query(CourseChangeRequest)
        .filter(
            CourseChangeRequest.course_id == course_id,
            CourseChangeRequest.change_type == CHANGESET,
            CourseChangeRequest.status.in_(("DRAFT", "PENDING")),
        )
        .all()
    )
    if len(records) > 1:
        raise ConflictError(
            "Khóa học có nhiều bản nháp đang hoạt động; cần đối soát trước khi sửa."
        )
    return records[0] if records else None


def ensure_course_authoring(actor, course, session=None):
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course, session=sess)
    course = lock_course(course, sess)
    if applying_course_review(sess) or actor.is_admin:
        return course
    if course.status == "SUBMITTED_FOR_REVIEW":
        raise ConflictError("Khóa học đang chờ duyệt. Hãy rút lại xét duyệt trước khi chỉnh sửa.")
    active = active_changeset(course.id, sess)
    if active is not None and active.status == "PENDING":
        raise ConflictError(
            "Đợt cập nhật đang chờ duyệt. Hãy rút lại xét duyệt trước khi chỉnh sửa."
        )
    return course


def should_stage(actor, course, session) -> bool:
    return (
        course_requires_review(course)
        and not actor.is_admin
        and not applying_course_review(session)
    )


def payload_for(record) -> dict[str, Any]:
    try:
        value = json.loads(record.proposed_payload_json or "{}")
    except (TypeError, ValueError) as exc:
        raise CourseValidationError("Bản nháp khóa học chứa dữ liệu không hợp lệ.") from exc
    if not isinstance(value, dict):
        raise CourseValidationError("Bản nháp khóa học phải là một đối tượng JSON.")
    return value


def write_payload(record, payload, session):
    payload["_draft_revision"] = int(payload.get("_draft_revision") or 0) + 1
    record.proposed_payload_json = json.dumps(payload, ensure_ascii=False, default=str)
    session.flush()
    return record


def working_changeset(actor, course, session=None):
    sess = session if session is not None else db.session
    course = ensure_course_authoring(actor, course, session=sess)
    if not course_requires_review(course):
        raise ConflictError("Khóa học chưa được duyệt lần đầu; các chỉnh sửa thuộc bản nháp gốc.")
    existing = active_changeset(course.id, sess)
    if existing is not None:
        if existing.status != "DRAFT":
            raise ConflictError("Đợt cập nhật đã gửi duyệt; vui lòng rút lại trước khi sửa.")
        return existing
    record = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=actor.id,
        change_type=CHANGESET,
        target_type="COURSE",
        target_id=course.id,
        status="DRAFT",
        proposed_payload_json=json.dumps(
            {"action": CHANGESET, "version_title": "Bản nháp cập nhật"}
        ),
        created_at=utc_now(),
    )
    sess.add(record)
    sess.flush()
    return record


def stage_course_fields(actor, course, group, fields, session=None):
    sess = session if session is not None else db.session
    record = working_changeset(actor, course, sess)
    payload = payload_for(record)
    proposed = dict(payload.get(group) or {})
    proposed.update(fields)
    payload[group] = proposed
    return write_payload(record, payload, sess)


def stage_course_operation(actor, course, operation, *, key, session=None):
    sess = session if session is not None else db.session
    record = working_changeset(actor, course, sess)
    payload = payload_for(record)
    operations = dict(payload.get("operations") or {})
    previous = operations.get(key) or {}
    if previous.get("action") == operation.get("action") and isinstance(
        operation.get("data"), dict
    ):
        operation = {**operation, "data": {**(previous.get("data") or {}), **operation["data"]}}
    operations[key] = operation
    payload["operations"] = operations
    return write_payload(record, payload, sess)


def stage_prerequisite(actor, course, prerequisite, *, remove=False, session=None):
    sess = session if session is not None else db.session
    record = working_changeset(actor, course, sess)
    payload = payload_for(record)
    changes = payload.get("prerequisites") or {}
    additions = set(changes.get("add") or [])
    removals = set(changes.get("remove") or [])
    public_id = str(prerequisite.public_id)
    if remove:
        additions.discard(public_id)
        removals.add(public_id)
    else:
        removals.discard(public_id)
        additions.add(public_id)
    payload["prerequisites"] = {"add": sorted(additions), "remove": sorted(removals)}
    return write_payload(record, payload, sess)


def lock_prerequisite_graph(session):
    if session.get_bind().dialect.name == "mssql":
        result = session.execute(
            sa.text(
                "DECLARE @result int; EXEC @result = sys.sp_getapplock "
                "@Resource=N'pwd301:prerequisite-graph', @LockMode='Exclusive', "
                "@LockOwner='Transaction', @LockTimeout=5000; SELECT @result"
            )
        ).scalar()
        if result is None or result < 0:
            raise ConflictError("Đồ thị môn tiên quyết đang được cập nhật; vui lòng thử lại.")


def validate_prerequisite_graph(course, prerequisite, session):
    from pwd301.models.course import CoursePrerequisite
    from pwd301.services.exceptions import PrerequisiteCycleError

    courses = {str(item.public_id): item.id for item in session.query(Course).all()}
    edges = {
        (link.course_id, link.prerequisite_course_id)
        for link in session.query(CoursePrerequisite).all()
    }
    for record in (
        session.query(CourseChangeRequest)
        .filter(
            CourseChangeRequest.change_type == CHANGESET,
            CourseChangeRequest.status.in_(("DRAFT", "PENDING")),
        )
        .all()
    ):
        changes = payload_for(record).get("prerequisites") or {}
        for public_id in changes.get("remove") or []:
            edges.discard((record.course_id, courses.get(str(public_id))))
        for public_id in changes.get("add") or []:
            if str(public_id) in courses:
                edges.add((record.course_id, courses[str(public_id)]))
    edges.add((course.id, prerequisite.id))
    visited = set()
    pending = [prerequisite.id]
    while pending:
        current = pending.pop()
        if current == course.id:
            raise PrerequisiteCycleError("Môn tiên quyết sẽ tạo chu trình phụ thuộc.")
        if current not in visited:
            visited.add(current)
            pending.extend(target for origin, target in edges if origin == current)


def review_version(record) -> str:
    content = [record.id, record.status, payload_for(record)]
    return hashlib.sha256(json.dumps(content, sort_keys=True, default=str).encode()).hexdigest()


def _asset_review_identity(asset_id, course_id, session, *, lock=False):
    """Bind review to one owned revision, content blob and persisted scan verdicts."""
    from pwd301.models.file_import import FileBlob, FileRevision, FileScanResult

    query = session.query(FileAsset).filter(FileAsset.id == asset_id)
    if lock:
        query = query.with_hint(
            FileAsset, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql"
        ).with_for_update()
    asset = query.populate_existing().first()
    if asset is None or asset.course_id != course_id:
        raise ConflictError("Tệp trong bản xét duyệt không còn thuộc khóa học này.")
    query = session.query(FileRevision).filter_by(file_asset_id=asset.id, is_current=True)
    if lock:
        query = query.with_hint(
            FileRevision, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql"
        ).with_for_update()
    revision = query.populate_existing().first()
    blob = (
        session.query(FileBlob).filter_by(id=revision.blob_id).populate_existing().first()
        if revision
        else None
    )
    scans_query = (
        session.query(FileScanResult).filter_by(file_revision_id=revision.id) if revision else None
    )
    if scans_query is not None and lock:
        scans_query = scans_query.with_hint(
            FileScanResult, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql"
        ).with_for_update()
    scans = (
        scans_query.populate_existing().order_by(FileScanResult.id).all()
        if scans_query is not None
        else []
    )
    latest = {}
    for scan in scans:
        latest[(scan.scan_type, scan.engine)] = scan
    malware = [scan for scan in latest.values() if scan.scan_type == "MALWARE"]
    safe = bool(
        asset.status == "ACTIVE"
        and asset.deleted_at is None
        and revision
        and revision.status == "ACTIVE"
        and blob
        and blob.status == "PRESENT"
        and blob.deleted_at is None
        and malware
        and all(scan.status == "PASS" for scan in latest.values())
    )
    return {
        "asset_id": asset.id,
        "public_id": str(asset.public_id),
        "course_id": asset.course_id,
        "asset_status": asset.status,
        "deleted_at": str(asset.deleted_at) if asset.deleted_at else None,
        "revision_id": revision.id if revision else None,
        "revision_no": revision.revision_no if revision else None,
        "revision_status": revision.status if revision else None,
        "blob_id": blob.id if blob else None,
        "sha256": blob.sha256_hex if blob else None,
        "size_bytes": revision.size_bytes if revision else None,
        "mime_type": revision.detected_mime_type if revision else None,
        "safe": safe,
        "scan_verdicts": [
            {
                "id": scan.id,
                "type": scan.scan_type,
                "engine": scan.engine,
                "status": scan.status,
                "started_at": str(scan.started_at),
                "completed_at": str(scan.completed_at),
            }
            for scan in scans
        ],
    }


def course_asset_manifest(course, session, proposed=None, *, lock=False, include_drafts=True):
    """Capture all referenced course bytes, including proposed cover and question resources."""
    from pwd301.models.file_import import LessonResource, QuestionRevisionResource
    from pwd301.models.question_bank import Question, QuestionRevision

    ids = set()
    if course.thumbnail_file_asset_id:
        ids.add(course.thumbnail_file_asset_id)
    lesson_refs = (
        session.query(LessonResource.file_asset_id)
        .join(Lesson)
        .filter(
            Lesson.course_id == course.id,
            Lesson.deleted_at.is_(None),
            Lesson.status.notin_(("TRASH", "HISTORICAL")),
        )
    )
    if not include_drafts:
        lesson_refs = lesson_refs.filter(Lesson.change_request_id.is_(None))
        if course.status != "APPROVED":
            lesson_refs = lesson_refs.filter(Lesson.status.notin_(("DRAFT", "PENDING_APPROVAL")))
    ids.update(row[0] for row in lesson_refs.all())
    question_refs = (
        session.query(QuestionRevisionResource.file_asset_id)
        .join(
            QuestionRevision, QuestionRevision.id == QuestionRevisionResource.question_revision_id
        )
        .join(Question, Question.id == QuestionRevision.question_id)
        .filter(
            QuestionRevision.is_current == sa.true(),
            Question.course_id == course.id,
            Question.deleted_at.is_(None),
            Question.status.notin_(("TRASH", "RETIRED")),
        )
    )
    if not include_drafts:
        question_refs = question_refs.filter(Question.change_request_id.is_(None))
    ids.update(row[0] for row in question_refs.all())
    if proposed:
        for public_id in proposed.get("new_file_assets") or []:
            asset = session.query(FileAsset).filter_by(public_id=uuid.UUID(str(public_id))).first()
            if asset is None:
                raise ConflictError("Tệp mới trong bản xét duyệt không còn tồn tại.")
            ids.add(asset.id)
        cover = (proposed.get("course_metadata") or {}).get("thumbnail_file_asset_id")
        if cover:
            ids.add(int(cover))
        for operation in (proposed.get("operations") or {}).values():
            if operation.get("action") != "QUESTION_REVISION":
                continue
            for resource in (operation.get("snapshot") or {}).get("resources") or []:
                asset = (
                    session.query(FileAsset)
                    .filter_by(public_id=uuid.UUID(str(resource["asset_id"])))
                    .first()
                )
                if asset is None:
                    raise ConflictError("Tệp câu hỏi trong bản xét duyệt không còn tồn tại.")
                ids.add(asset.id)
    return {
        str(asset_id): _asset_review_identity(asset_id, course.id, session, lock=lock)
        for asset_id in sorted(ids)
    }


def validate_submitted_assets(course, manifest, session):
    """Recheck under transaction locks before any reviewed content is applied."""
    if not isinstance(manifest, dict):
        raise ConflictError("Bản gửi duyệt chưa khóa phiên bản tệp; hãy rút lại và gửi lại.")
    for key, expected in sorted(manifest.items(), key=lambda pair: int(pair[0])):
        actual = _asset_review_identity(int(key), course.id, session, lock=True)
        if not actual["safe"] or actual != expected:
            raise ConflictError(
                "Tệp hoặc kết quả quét đã thay đổi sau khi gửi. Hãy rút lại và kiểm tra bản nháp."
            )


def course_review_version(course, session=None) -> str:
    sess = session if session is not None else db.session
    fields = {column.key: getattr(course, column.key) for column in sa.inspect(Course).columns}
    lesson_query = sess.query(Lesson).filter(
        Lesson.course_id == course.id, Lesson.deleted_at.is_(None)
    )
    if course_requires_review(course):
        lesson_query = lesson_query.filter(
            Lesson.change_request_id.is_(None), Lesson.status.notin_(("TRASH", "HISTORICAL"))
        )
        if course.status != "APPROVED":
            lesson_query = lesson_query.filter(Lesson.status.notin_(("DRAFT", "PENDING_APPROVAL")))
    lessons = [
        {column.key: getattr(lesson, column.key) for column in sa.inspect(Lesson).columns}
        for lesson in lesson_query.order_by(Lesson.id).all()
    ]
    from pwd301.models.assessment import Assessment
    from pwd301.models.course import CourseCompletionRule, CoursePrerequisite
    from pwd301.services.course_assessment_workflow import assessment_snapshot

    units = [
        {column.key: getattr(item, column.key) for column in sa.inspect(LearningUnit).columns}
        for item in sess.query(LearningUnit)
        .filter(
            LearningUnit.course_id == course.id,
            LearningUnit.change_request_id.is_(None),
            LearningUnit.deleted_at.is_(None),
        )
        .order_by(LearningUnit.id)
        .all()
    ]
    assessments = [
        assessment_snapshot(item)
        for item in sess.query(Assessment)
        .filter(
            Assessment.course_id == course.id,
            Assessment.change_request_id.is_(None),
            Assessment.deleted_at.is_(None),
        )
        .order_by(Assessment.id)
        .all()
    ]
    # Student starts update lifecycle telemetry without changing the reviewed configuration.
    for snapshot in assessments:
        for key in ("updated_at", "first_attempt_started_at"):
            snapshot["fields"].pop(key, None)
    rules = [
        {
            column.key: getattr(item, column.key)
            for column in sa.inspect(CourseCompletionRule).columns
        }
        for item in sess.query(CourseCompletionRule).filter_by(course_id=course.id).all()
    ]
    prerequisites = [
        {column.key: getattr(item, column.key) for column in sa.inspect(CoursePrerequisite).columns}
        for item in sess.query(CoursePrerequisite)
        .filter_by(course_id=course.id)
        .order_by(CoursePrerequisite.prerequisite_course_id)
        .all()
    ]
    from pwd301.models.question_bank import Question
    from pwd301.services.course_question_workflow import question_version

    questions = [
        (item.id, question_version(item))
        for item in sess.query(Question)
        .filter(
            Question.course_id == course.id,
            Question.change_request_id.is_(None),
            Question.deleted_at.is_(None),
        )
        .order_by(Question.id)
        .populate_existing()
        .all()
        if item.current_revision is not None
    ]
    return hashlib.sha256(
        json.dumps(
            [
                fields,
                lessons,
                units,
                assessments,
                rules,
                prerequisites,
                questions,
                course_asset_manifest(course, sess, include_drafts=False),
            ],
            sort_keys=True,
            default=str,
        ).encode()
    ).hexdigest()


def require_review_identity(record, payload):
    supplied_id = payload.get("request_id", payload.get("change_request_id", record.id))
    if str(supplied_id) != str(record.id) or payload.get("review_version") != review_version(
        record
    ):
        raise ConflictError(
            "Bản xét duyệt đã thay đổi. Hãy tải lại và kiểm tra phiên bản mới trước khi duyệt."
        )


def successor_draft(actor, record, session):
    """Keep terminal review evidence immutable while retaining all authored proposals."""
    payload = payload_for(record)
    payload.pop("submitted_snapshot", None)
    payload.pop("baseline_version", None)
    payload.pop("asset_manifest", None)
    payload["previous_request_id"] = record.id
    successor = CourseChangeRequest(
        course_id=record.course_id,
        requested_by_user_id=record.requested_by_user_id,
        change_type=CHANGESET,
        target_type="COURSE",
        target_id=record.course_id,
        status="DRAFT",
        proposed_payload_json=json.dumps(payload, ensure_ascii=False, default=str),
        created_at=utc_now(),
    )
    session.add(successor)
    session.flush()
    for lesson in session.query(Lesson).filter(Lesson.change_request_id == record.id).all():
        lesson.status = "DRAFT"
        lesson.change_request_id = successor.id
    for unit in (
        session.query(LearningUnit).filter(LearningUnit.change_request_id == record.id).all()
    ):
        unit.change_request_id = successor.id
    from pwd301.models.assessment import Assessment

    for assessment in (
        session.query(Assessment).filter(Assessment.change_request_id == record.id).all()
    ):
        assessment.change_request_id = successor.id
    from pwd301.models.question_bank import Question

    for question in session.query(Question).filter(Question.change_request_id == record.id).all():
        question.change_request_id = successor.id
    session.flush()
    return successor


class AuthoringProjection:
    """Read-only view overrides never dirty the SQLAlchemy approved object."""

    def __init__(self, original, overrides):
        self._original = original
        self._overrides = overrides

    def __getattr__(self, name):
        return self._overrides[name] if name in self._overrides else getattr(self._original, name)


def effective_course(course, actor, session=None):
    sess = session if session is not None else db.session
    if actor is None or not (actor.id == course.owner_instructor_id or actor.is_admin):
        return course
    record = active_changeset(course.id, sess)
    if record is None:
        return course
    metadata = dict(payload_for(record).get("course_metadata") or {})
    if "thumbnail_file_asset_id" in metadata:
        metadata["thumbnail_url"] = cover_url(course, metadata["thumbnail_file_asset_id"], sess)
    return AuthoringProjection(course, metadata)


def cover_url(course, asset_id, session):
    if asset_id is None:
        return None
    asset = session.get(FileAsset, int(asset_id)) if str(asset_id).isdigit() else None
    if asset is None:
        return None
    mime = (asset.mime_type or "").split(";")[0].lower()
    if (
        asset.course_id != course.id
        or asset.deleted_at is not None
        or asset.virus_scan_status != "CLEAN"
        or not asset.has_passed_malware_scan
        or not mime.startswith("image/")
    ):
        return None
    return f"/api/files/{asset.public_id}/download?disposition=inline"


def cover_review_fields(course, payload, session):
    metadata = payload.get("course_metadata", payload)
    current = cover_url(course, course.thumbnail_file_asset_id, session)
    proposed_id = metadata.get("thumbnail_file_asset_id", course.thumbnail_file_asset_id)
    return {
        "current_cover_url": current,
        "proposed_cover_url": cover_url(course, proposed_id, session),
    }


def effective_prerequisites(course, actor, session):
    from pwd301.services.enrollment_service import get_course_prerequisites

    current = get_course_prerequisites(course.id, only_approved=False, session=session)
    record = (
        active_changeset(course.id, session)
        if actor and (actor.id == course.owner_instructor_id or actor.is_admin)
        else None
    )
    changes = payload_for(record).get("prerequisites") or {} if record else {}
    removed = set(changes.get("remove") or [])
    proposed = {str(item.public_id): item for item in current if str(item.public_id) not in removed}
    for public_id in changes.get("add") or []:
        try:
            candidate = session.query(Course).filter_by(public_id=uuid.UUID(str(public_id))).first()
        except (TypeError, ValueError):
            continue
        if candidate:
            proposed[str(candidate.public_id)] = candidate
    return sorted(proposed.values(), key=lambda item: item.course_code)
