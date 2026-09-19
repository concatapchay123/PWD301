from __future__ import annotations

import contextlib
import json
import re
import uuid
from typing import Any

import sqlalchemy as sa
from flask import Response, jsonify, request, send_file

from pwd301.blueprints.instructor import instructor_bp
from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, CoursePrerequisite, Enrollment, Lesson
from pwd301.models.file_import import LessonResource
from pwd301.models.identity import Role, User
from pwd301.models.question_bank import Question, QuestionRevision
from pwd301.models.types import utc_now
from pwd301.services.analytics_service import (
    get_instructor_course_analytics,
    get_instructor_overview_analytics,
)
from pwd301.services.assessment_service import (
    _resolve_assessment,
    _resolve_question,
    _serialize_assessment,
    _serialize_assignment,
    _serialize_blueprint,
    _serialize_section,
    assign_question,
    cancel_assessment,
    configure_blueprint,
    create_assessment,
    create_section,
    delete_section,
    get_assessment_detail,
    list_course_assessments,
    materialize_blueprint_pool,
    publish_assessment,
    remove_question_assignment,
    restore_assessment,
    trash_assessment,
    trigger_assessment_regrade,
    update_assessment,
    update_question_assignment,
)
from pwd301.services.authorization_service import (
    _resolve_course,
    _resolve_lesson,
    instructor_required,
    require_authenticated_actor,
    require_course_manager,
    require_student_data_access,
)
from pwd301.services.completion_service import (
    get_or_create_default_completion_rule,
    set_course_completion_rule,
)
from pwd301.services.course_service import (
    change_course_status,
    create_course,
    get_course_detail,
    trash_course,
    update_course,
)
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    get_course_enrollments,
    get_course_prerequisites,
    remove_course_prerequisite,
)
from pwd301.services.exceptions import (
    AssessmentLockedError,
    CourseAlreadyExistsError,
    CourseStateViolationError,
    CourseValidationError,
    DocumentParsingError,
    ForbiddenError,
    LessonValidationError,
    ResourceNotFoundError,
    ValidationError,
)
from pwd301.services.file_service import (
    _serialize_file_asset,
    _serialize_lesson_resource,
    attach_resource_to_lesson,
    detach_resource_from_lesson,
    get_file_for_download,
    rescan_file_asset,
    sanitize_filename,
    store_file_stream,
    validate_file_metadata,
)
from pwd301.services.import_service import (
    commit_import_job,
    create_import_job,
    process_import_job,
)
from pwd301.services.lesson_service import (
    change_lesson_status,
    create_lesson,
    get_lesson_detail,
    reorder_lessons,
    trash_lesson,
    update_lesson,
)
from pwd301.services.question_bank_service import (
    _serialize_question,
    _serialize_question_correction,
    _serialize_question_revision,
    create_question,
    create_question_revision,
    get_question_detail,
    get_question_revision_detail,
    list_course_questions,
    list_question_corrections,
    list_question_revisions,
    restore_question,
    trash_question,
    update_question,
)
from pwd301.services.regrade_worker import (
    get_regrade_job_detail,
    retry_regrade_job,
)


def _extract_video_url_from_markdown(content: str | None) -> str | None:
    if not content:
        return None
    import re
    m = re.search(r"<!--\s*video_url:\s*(\S+?)\s*-->", content)
    return m.group(1) if m else None


def _serialize_lesson(les: Lesson) -> dict[str, Any]:
    video_url = _extract_video_url_from_markdown(les.markdown_content)
    if not video_url and hasattr(les, "resources") and les.resources:
        for r in les.resources:
            if getattr(r, "is_deleted", False):
                continue
            if (
                r.file_asset
                and r.file_asset.virus_scan_status == "CLEAN"
            ):
                mime = r.file_asset.mime_type or ""
                name = (r.file_asset.display_name or "").lower()
                if mime.startswith("video/") or name.endswith((".mp4", ".webm", ".mkv", ".mov")):
                    cid = str(les.course.public_id) if les.course else ""
                    rid = str(r.public_id)
                    fid = str(r.file_asset.public_id)
                    video_url = (
                        f"/student/courses/{cid}/files/{rid}/download?disposition=inline"
                        if cid
                        else f"/student/files/{fid}/download?disposition=inline"
                    )
                    break

    return {
        "lesson_id": str(les.public_id),
        "course_id": str(les.course.public_id) if les.course else None,
        "title": les.title,
        "summary": les.summary,
        "markdown_content": les.markdown_content,
        "video_url": video_url,
        "position": les.position,
        "estimated_duration_minutes": les.estimated_duration_minutes,
        "minimum_completion_seconds": les.minimum_completion_seconds,
        "viewed_fraction_required": float(les.viewed_fraction_required),
        "status": les.status,
        "published_at": les.published_at.isoformat() if les.published_at else None,
        "created_at": les.created_at.isoformat(),
        "updated_at": les.updated_at.isoformat(),
        "resources": (
            [_serialize_lesson_resource(r) for r in les.resources]
            if hasattr(les, "resources") and les.resources
            else []
        ),
    }


def _serialize_course(c: Course) -> dict[str, Any]:
    active_lessons = []
    if hasattr(c, "lessons") and c.lessons:
        active_lessons = [
            _serialize_lesson(les)
            for les in sorted(c.lessons, key=lambda x: x.position or 0)
            if not getattr(les, "deleted_at", None)
        ]
    instructor_name = c.owner_instructor.display_name if c.owner_instructor else None
    enrollments_count = len(c.enrollments) if hasattr(c, "enrollments") and c.enrollments else 0
    return {
        "course_id": str(c.public_id),
        "course_code": c.course_code,
        "title": c.title,
        "description": c.description,
        "category": c.category,
        "difficulty": c.difficulty,
        "capacity": c.capacity,
        "status": c.status,
        "owner_instructor_id": (str(c.owner_instructor.public_id) if c.owner_instructor else None),
        "instructor_name": instructor_name,
        "enrollments_count": enrollments_count,
        "enrolled_count": enrollments_count,
        "lessons": active_lessons,
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
    }


@instructor_bp.route("/dashboard", methods=["GET"])
@instructor_required
def dashboard() -> Any:
    """Instructor dashboard displaying courses managed by the actor with analytics overview."""
    actor = require_authenticated_actor()
    overview = get_instructor_overview_analytics(actor, session=db.session)
    return jsonify(overview), 200


@instructor_bp.route("/courses/<course_id>/analytics", methods=["GET"])
@instructor_required
def course_analytics_view(course_id: str) -> tuple[Response, int] | Response:
    """Course-level learning analytics and performance report."""
    actor = require_authenticated_actor()
    analytics = get_instructor_course_analytics(actor, course_id, session=db.session)
    return jsonify(analytics), 200


@instructor_bp.route("/courses/<course_id>/students/<student_id>", methods=["GET"])
@instructor_required
def get_student_detail(course_id: str, student_id: str) -> tuple[Response, int] | Response:
    """View student detail within a managed course.

    Invariants enforced:
    - Instructor must manage this course.
    - Student must be enrolled in this course.
    - Otherwise raises ForbiddenError (403).
    """
    actor = require_authenticated_actor()

    sess = db.session
    student, course = require_student_data_access(actor, student_id, course_id, session=sess)

    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == student.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )

    data = {
        "course_id": str(course.public_id),
        "course_title": course.title,
        "student_id": str(student.public_id),
        "student_name": student.display_name,
        "student_email": student.email,
        "progress_percent": (
            float(enrollment.current_progress_percent or 0.0) if enrollment else 0.0
        ),
        "enrollment_status": enrollment.status if enrollment else None,
    }
    return jsonify(data), 200


@instructor_bp.route("/courses", methods=["GET"])
@instructor_required
def my_courses() -> Any:
    """List courses managed by the instructor."""
    actor = require_authenticated_actor()
    courses = (
        db.session.query(Course)
        .filter(Course.owner_instructor_id == actor.id, Course.deleted_at.is_(None))
        .order_by(Course.created_at.desc())
        .all()
    )
    return jsonify({"courses": [_serialize_course(c) for c in courses]}), 200


@instructor_bp.route("/courses", methods=["POST"])
@instructor_required
def create_course_route() -> Any:
    """Create a new course in DRAFT status."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    try:
        course = create_course(actor, payload)
    except (CourseValidationError, CourseAlreadyExistsError, ForbiddenError):
        raise
    except sa.exc.IntegrityError as exc:
        db.session.rollback()
        raise CourseAlreadyExistsError("Course code or title violates unique constraint.") from exc
    except Exception:
        db.session.rollback()
        raise

    return jsonify(_serialize_course(course)), 201


@instructor_bp.route("/courses/<course_id>", methods=["GET"])
@instructor_required
def get_course_route(course_id: str) -> Any:
    """Get detailed course information for managing."""
    actor = require_authenticated_actor()
    course = get_course_detail(actor, course_id)
    return jsonify(_serialize_course(course)), 200


@instructor_bp.route("/courses/<course_id>/manage", methods=["GET"])
@instructor_required
def manage_course_hub(course_id: str) -> Any:
    """Dedicated Course Management Hub for Instructors."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)

    data = {
        "course_id": str(course.public_id),
        "course_code": course.course_code,
        "title": course.title,
        "status": course.status,
        "owner_instructor_id": (
            str(course.owner_instructor.public_id) if course.owner_instructor else None
        ),
        "lessons_count": len(course.lessons),
        "enrollments_count": len(course.enrollments),
    }
    accept_header = request.headers.get("Accept", "")
    if "text/html" in accept_header and "application/json" not in accept_header:
        from flask import get_flashed_messages

        flashed = get_flashed_messages(with_categories=True)
        flashes_html = "".join(
            f"<div class='alert alert-{item[0]}'>{item[1]}</div>"
            if isinstance(item, (tuple, list)) and len(item) == 2
            else f"<div class='alert alert-info'>{item}</div>"
            for item in flashed
        )
        html_body = (
            f"<!DOCTYPE html><html><body><div id='flashes'>{flashes_html}</div></body></html>"
        )
        return html_body, 200, {"Content-Type": "text/html; charset=utf-8"}

    return jsonify(data), 200


@instructor_bp.route("/courses/<course_id>", methods=["POST", "PATCH", "PUT"])
@instructor_required
def update_course_route(course_id: str) -> Any:
    """Update editable course metadata with mass-assignment defense."""
    actor = require_authenticated_actor()

    payload: dict[str, Any] = dict(request.get_json(silent=True) or request.form.to_dict() or {})
    if "max_enrollments" in payload and "capacity" not in payload:
        payload["capacity"] = payload.pop("max_enrollments")
    for key in ("capacity", "storage_quota_bytes", "thumbnail_file_asset_id"):
        if payload.get(key) == "":
            payload[key] = None

    try:
        course = update_course(actor, course_id, payload)
    except (
        CourseValidationError,
        CourseAlreadyExistsError,
        ForbiddenError,
        CourseStateViolationError,
    ):
        raise
    except Exception:
        db.session.rollback()
        raise

    return jsonify(_serialize_course(course)), 200


@instructor_bp.route("/courses/<course_id>/submit", methods=["POST"])
@instructor_bp.route("/courses/<course_id>/publish-request", methods=["POST"])
@instructor_required
def submit_course_route(course_id: str) -> Any:
    """Submit a DRAFT course for admin review."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason", "Giảng viên đề xuất phê duyệt giáo trình và xuất bản khóa học.")
    try:
        course = change_course_status(
            actor,
            course_id,
            "SUBMITTED_FOR_REVIEW",
            reason=reason,
        )
        return jsonify(_serialize_course(course)), 200
    except Exception:
        raise


@instructor_bp.route("/courses/<course_id>/cancel-submit", methods=["POST"])
@instructor_required
def cancel_submit_course_route(course_id: str) -> Any:
    """Cancel review submission and revert to DRAFT."""
    actor = require_authenticated_actor()
    try:
        course = change_course_status(
            actor,
            course_id,
            "DRAFT",
            reason="Giảng viên rút lại yêu cầu xét duyệt để chỉnh sửa thêm.",
        )
        return jsonify(_serialize_course(course)), 200
    except Exception:
        raise


@instructor_bp.route("/courses/<course_id>/publish", methods=["POST"])
@instructor_required
def publish_course_route(course_id: str) -> Any:
    """Publish an approved course (or direct publish if actor is Admin)."""
    actor = require_authenticated_actor()
    try:
        course_obj = _resolve_course(course_id)
        if course_obj is None:
            raise ResourceNotFoundError("Khóa học không tồn tại.")

        if course_obj.status == "DRAFT":
            if actor.is_admin:
                change_course_status(
                    actor, course_id, "SUBMITTED_FOR_REVIEW", reason="Admin xuất bản trực tiếp"
                )
                change_course_status(actor, course_id, "APPROVED", reason="Admin duyệt trực tiếp")
                course = change_course_status(
                    actor, course_id, "PUBLISHED", reason="Admin xuất bản trực tiếp"
                )
            else:
                return (
                    jsonify(
                        {
                            "error": {
                                "code": "COURSE_STATE_VIOLATION",
                                "message": (
                                    "Khóa học đang ở trạng thái DRAFT. "
                                    "Cần gửi duyệt trước khi xuất bản."
                                ),
                            }
                        }
                    ),
                    409,
                )
        elif course_obj.status == "SUBMITTED_FOR_REVIEW":
            if actor.is_admin:
                change_course_status(actor, course_id, "APPROVED", reason="Admin duyệt trực tiếp")
                course = change_course_status(
                    actor, course_id, "PUBLISHED", reason="Admin xuất bản trực tiếp"
                )
            else:
                return (
                    jsonify(
                        {
                            "error": {
                                "code": "COURSE_STATE_VIOLATION",
                                "message": "Khóa học đang chờ Admin xét duyệt.",
                            }
                        }
                    ),
                    409,
                )
        else:
            course = change_course_status(actor, course_id, "PUBLISHED")

        return jsonify(_serialize_course(course)), 200
    except Exception:
        raise


@instructor_bp.route("/courses/<course_id>/trash", methods=["POST", "DELETE"])
@instructor_required
def trash_course_route(course_id: str) -> Any:
    """Soft-delete a course to TRASH."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    course = trash_course(actor, course_id, reason=reason)
    return jsonify(_serialize_course(course)), 200


@instructor_bp.route("/courses/<course_id>/lessons", methods=["POST"])
@instructor_required
def create_lesson_route(course_id: str) -> Any:
    """Create a new lesson in a managed course."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    if not payload.get("estimated_duration_minutes"):
        payload.pop("estimated_duration_minutes", None)
    if not payload.get("summary"):
        payload.pop("summary", None)

    # Milestone 4: Default markdown_content if blank so instructors
    # are not forced to type manual markdown when uploading media.
    raw_md = payload.get("markdown_content")
    if not raw_md or not raw_md.strip():
        title = payload.get("title", "Bài giảng")
        summary = payload.get("summary") or "Nội dung bài giảng đa phương tiện."
        raw_md = f"# {title}\n\n{summary}"

    video_url = payload.get("video_url")
    if video_url and str(video_url).strip():
        import re
        if not re.search(r"<!--\s*video_url:\s*\S+?\s*-->", raw_md):
            raw_md = f"<!-- video_url: {str(video_url).strip()} -->\n\n" + raw_md
    payload["markdown_content"] = raw_md

    try:
        # Milestone 4 Remediation: Pre-validate all uploaded files BEFORE calling create_lesson
        # to ensure transaction atomicity and prevent ghost lessons if validation fails.
        if request.files:
            files_to_validate: list[Any] = []
            media_file = request.files.get("media_file")
            if media_file and media_file.filename and media_file.filename.strip():
                files_to_validate.append(media_file)

            for key in ("resource_files", "resource_file", "file"):
                for rf in request.files.getlist(key):
                    if rf and rf.filename and rf.filename.strip() and rf not in files_to_validate:
                        files_to_validate.append(rf)

            for f in files_to_validate:
                if f.filename:
                    clean_fn = sanitize_filename(f.filename)
                    validate_file_metadata(clean_fn, getattr(f, "content_type", None))

        lesson = create_lesson(actor, course.id, payload)
        attached_count = 0

        # Milestone 4: Process multipart uploaded media and resource files
        if request.files:
            try:
                media_file = request.files.get("media_file")
                if media_file and media_file.filename:
                    m_asset = store_file_stream(
                        actor=actor,
                        course_id=course.id,
                        file_stream=media_file.stream,
                        filename=media_file.filename,
                        content_type=media_file.content_type,
                        asset_type="RESOURCE",
                        title=f"Bài giảng: {lesson.title}",
                        session=db.session,
                    )
                    attach_resource_to_lesson(
                        actor=actor,
                        lesson_id=lesson.id,
                        asset_id=m_asset.id,
                        is_downloadable=True,
                        label=media_file.filename,
                        session=db.session,
                    )
                    attached_count += 1

                r_files: list[Any] = []
                for key in ("resource_files", "resource_file", "file"):
                    r_files.extend(request.files.getlist(key))

                for r_file in r_files:
                    if r_file and r_file.filename and r_file != media_file:
                        r_asset = store_file_stream(
                            actor=actor,
                            course_id=course.id,
                            file_stream=r_file.stream,
                            filename=r_file.filename,
                            content_type=r_file.content_type,
                            asset_type="RESOURCE",
                            title=r_file.filename,
                            session=db.session,
                        )
                        attach_resource_to_lesson(
                            actor=actor,
                            lesson_id=lesson.id,
                            asset_id=r_asset.id,
                            is_downloadable=True,
                            label=r_file.filename,
                            session=db.session,
                        )
                        attached_count += 1
            except Exception:
                # Cleanup guard: delete created lesson on storage failure to prevent orphan records
                try:
                    db.session.rollback()
                    l_to_del = (
                        db.session.get(Lesson, lesson.id)
                        if lesson and hasattr(lesson, "id")
                        else None
                    )
                    if l_to_del is not None:
                        db.session.delete(l_to_del)
                        db.session.commit()
                except Exception:
                    db.session.rollback()
                raise

        return jsonify(_serialize_lesson(lesson)), 201
    except Exception:
        raise


@instructor_bp.route("/courses/<course_id>/lessons/<lesson_id>/resources", methods=["POST"])
@instructor_required
def attach_lesson_resource_route(course_id: str, lesson_id: str) -> Any:
    """Attach an uploaded file to an existing lesson."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)
    lesson = _resolve_lesson(lesson_id, session=db.session)
    if lesson is None or lesson.course_id != course.id:
        raise ResourceNotFoundError("Lesson not found.")

    file = (
        request.files.get("file")
        or request.files.get("resource_file")
        or request.files.get("media_file")
    )
    if not file or not file.filename:
        raise ValidationError("No file provided.")

    label = request.form.get("label") or file.filename
    try:
        asset = store_file_stream(
            actor=actor,
            course_id=course.id,
            file_stream=file.stream,
            filename=file.filename,
            content_type=file.content_type,
            asset_type="RESOURCE",
            title=label,
            session=db.session,
        )
        resource = attach_resource_to_lesson(
            actor=actor,
            lesson_id=lesson.id,
            asset_id=asset.id,
            is_downloadable=True,
            label=label,
            session=db.session,
        )
        return jsonify(_serialize_lesson_resource(resource)), 201
    except Exception:
        raise


@instructor_bp.route(
    "/courses/<course_id>/lessons/<lesson_id>/resources/<resource_id>/delete",
    methods=["POST"],
)
@instructor_bp.route(
    "/courses/<course_id>/lessons/<lesson_id>/resources/<resource_id>",
    methods=["DELETE"],
)
@instructor_required
def detach_lesson_resource_route(course_id: str, lesson_id: str, resource_id: str) -> Any:
    """Detach a resource link from a lesson."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)
    lesson = _resolve_lesson(lesson_id, session=db.session)
    if lesson is None or lesson.course_id != course.id:
        raise ResourceNotFoundError("Lesson not found.")

    try:
        detach_resource_from_lesson(actor, lesson.id, resource_id, session=db.session)
        return jsonify({"status": "ok", "message": "Resource detached successfully"}), 200
    except Exception:
        raise


@instructor_bp.route("/courses/<course_id>/lessons/<lesson_id>/delete", methods=["POST"])
@instructor_required
def delete_lesson_from_hub_route(course_id: str, lesson_id: str) -> Any:
    """Soft-delete a lesson from the course management hub with admin approval gate."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)
    lesson = _resolve_lesson(lesson_id, session=db.session)
    if lesson is None or lesson.course_id != course.id:
        raise ResourceNotFoundError("Lesson not found.")

    if not actor.is_admin and (
        course.status in ("APPROVED", "PUBLISHED", "ARCHIVED") or lesson.status == "PUBLISHED"
    ):
        req = CourseChangeRequest(
            course_id=course.id,
            requested_by_user_id=actor.id,
            change_type="LESSON_STRUCTURE",
            target_type="LESSON",
            target_id=lesson.id,
            proposed_payload_json=json.dumps(
                {
                    "action": "DELETE",
                    "lesson_id": lesson.id,
                    "lesson_title": lesson.title,
                    "reason": "Giảng viên yêu cầu xóa bài giảng khỏi khóa học",
                },
                default=str,
            ),
            status="PENDING",
            created_at=utc_now(),
        )
        db.session.add(req)
        db.session.flush()

        from pwd301.services.notification_service import dispatch_notification

        admin_users = db.session.query(User).filter(User.roles.any(Role.code == "ADMIN")).all()
        for adm in admin_users:
            with contextlib.suppress(Exception):
                dispatch_notification(
                    recipient_user=adm,
                    event_type="LESSON_CHANGE_REQUEST",
                    title=f"Yêu cầu xóa bài giảng: {lesson.title}",
                    body=(
                        f"Giảng viên {actor.display_name} gửi yêu cầu xóa bài giảng "
                        f"'{lesson.title}' trong khóa học '{course.title}'. Cần Admin phê duyệt."
                    ),
                    category="COURSE",
                    session=db.session,
                )
        db.session.commit()

        return jsonify(
            {
                "status": "pending_approval",
                "pending_approval": True,
                "message": (
                    "Bài giảng thuộc khóa học đã ban hành. "
                    "Yêu cầu xóa bài giảng đã được gửi tới Quản trị viên để xét duyệt."
                ),
                "change_request_id": req.id,
            }
        ), 202

    trash_lesson(actor, lesson_id, session=db.session)
    return jsonify({"status": "success", "message": "Bài giảng đã được xóa thành công."}), 200


@instructor_bp.route("/courses/<course_id>/files", methods=["POST"])
@instructor_required
def upload_course_file_route(course_id: str) -> Any:
    """Upload a file asset for a course or lesson with virus scanning."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)

    if "file" not in request.files:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "No file uploaded."}}), 400

    file_obj = request.files["file"]
    if not file_obj or not file_obj.filename:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Invalid filename."}}), 400

    title = request.form.get("title") or file_obj.filename
    lesson_id_str = request.form.get("lesson_id")

    try:
        asset = store_file_stream(
            actor=actor,
            course_id=course.id,
            file_stream=file_obj.stream,
            filename=file_obj.filename,
            content_type=file_obj.content_type,
            asset_type="RESOURCE",
            title=title,
            session=db.session,
        )

        # If bound to a lesson, link it via LessonResource
        if lesson_id_str and str(lesson_id_str).strip():
            lesson = _resolve_lesson(lesson_id_str, session=db.session)
            if lesson and lesson.course_id == course.id:
                max_pos = (
                    db.session.query(sa.func.coalesce(sa.func.max(LessonResource.position), 0))
                    .filter(LessonResource.lesson_id == lesson.id)
                    .scalar()
                    or 0
                )
                res = LessonResource(
                    lesson_id=lesson.id,
                    file_asset_id=asset.id,
                    label=title or asset.display_name,
                    position=max_pos + 1,
                    is_required=False,
                )
                db.session.add(res)
                db.session.commit()

        return jsonify(_serialize_file_asset(asset)), 201

    except Exception:
        db.session.rollback()
        raise


@instructor_bp.route("/courses/<course_id>/files/<asset_id>/download", methods=["GET"])
@instructor_required
def download_course_file_route(course_id: str, asset_id: str) -> Any:
    """Download a course file asset with direct authenticated streaming."""
    actor = require_authenticated_actor()
    require_course_manager(actor, course_id, session=db.session)
    version_param = request.args.get("version")
    revision_no = int(version_param) if version_param and version_param.isdigit() else None
    asset, blob, physical_path = get_file_for_download(
        actor, asset_id, revision_no=revision_no, session=db.session
    )
    disposition = request.args.get("disposition", "attachment").lower()
    if disposition not in ("inline", "attachment"):
        disposition = "attachment"
    clean_filename = sanitize_filename(asset.original_filename or asset.display_name)
    return send_file(
        physical_path,
        mimetype=blob.detected_mime_type,
        as_attachment=(disposition == "attachment"),
        download_name=clean_filename,
        conditional=True,
    )


@instructor_bp.route("/courses/<course_id>/files/<asset_id>/rescan", methods=["POST"])
@instructor_required
def rescan_course_file_route(course_id: str, asset_id: str) -> Any:
    """Trigger on-demand malware rescan of a file asset and redirect to materials tab."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)
    try:
        asset = rescan_file_asset(actor, asset_id, session=db.session)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        if request.accept_mimetypes.accept_html and not request.is_json:
            from flask import flash, redirect, url_for

            flash(f"Không thể quét lại: {str(exc)}", "danger")
            return redirect(
                url_for("instructor.manage_course_hub", course_id=course.public_id, tab="materials")
            )
        raise

    asset_obj = locals().get("asset")
    asset_status = getattr(asset_obj, "status", None) if asset_obj else None
    virus_status = getattr(asset_obj, "virus_scan_status", None) if asset_obj else None
    return (
        jsonify(
            {
                "message": "Rescan completed",
                "asset_id": str(asset_id),
                "status": asset_status,
                "virus_scan_status": virus_status,
            }
        ),
        200,
    )


@instructor_bp.route("/courses/<course_id>/assessments", methods=["POST"])
@instructor_required
def create_course_assessment_route(course_id: str) -> Any:
    """Create a new assessment for a course."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    try:
        asm = create_assessment(actor, course.id, payload, session=db.session)
        return jsonify(_serialize_assessment(asm)), 201
    except Exception:
        raise


@instructor_bp.route("/lessons/<lesson_id>", methods=["GET"])
@instructor_required
def get_lesson_route(lesson_id: str) -> tuple[Response, int] | Response:
    """View lesson detail for authoring."""
    actor = require_authenticated_actor()

    lesson = get_lesson_detail(actor, lesson_id)
    return jsonify(_serialize_lesson(lesson)), 200


@instructor_bp.route("/lessons/<lesson_id>", methods=["PATCH", "PUT"])
@instructor_required
def update_lesson_route(lesson_id: str) -> tuple[Response, int] | Response:
    """Update editable lesson fields with admin approval gate for published content."""
    actor = require_authenticated_actor()

    lesson = _resolve_lesson(lesson_id, session=db.session)
    if lesson is None:
        raise LessonValidationError("Lesson not found.")

    course = require_course_manager(actor, lesson.course_id, session=db.session)
    payload = request.get_json(silent=True) or request.form.to_dict() or {}

    if "video_url" in payload:
        video_url = payload.pop("video_url")
        current_md = (
            payload.get("markdown_content")
            if "markdown_content" in payload
            else (lesson.markdown_content or "")
        )
        import re
        cleaned_md = re.sub(r"<!--\s*video_url:\s*\S+?\s*-->\n*", "", current_md or "").strip()
        if video_url and str(video_url).strip():
            payload["markdown_content"] = (
                f"<!-- video_url: {str(video_url).strip()} -->\n\n{cleaned_md}"
            )
        else:
            payload["markdown_content"] = cleaned_md

    # Strict Admin Approval Invariant:
    # If course is APPROVED or PUBLISHED (or lesson is already PUBLISHED), and actor is not Admin:
    if not actor.is_admin and (
        course.status in ("APPROVED", "PUBLISHED", "ARCHIVED") or lesson.status == "PUBLISHED"
    ):
        req = CourseChangeRequest(
            course_id=course.id,
            requested_by_user_id=actor.id,
            change_type="LESSON_CONTENT",
            target_type="LESSON",
            target_id=lesson.id,
            proposed_payload_json=json.dumps(payload, default=str),
            status="PENDING",
            created_at=utc_now(),
        )
        db.session.add(req)
        db.session.flush()

        from pwd301.services.notification_service import dispatch_notification

        admin_users = db.session.query(User).filter(User.roles.any(Role.code == "ADMIN")).all()
        for adm in admin_users:
            with contextlib.suppress(Exception):
                dispatch_notification(
                    recipient_user=adm,
                    event_type="LESSON_CHANGE_REQUEST",
                    title=f"Yêu cầu sửa bài giảng: {lesson.title}",
                    body=(
                        f"Giảng viên {actor.display_name} gửi yêu cầu chỉnh sửa bài giảng "
                        f"'{lesson.title}' trong khóa học '{course.title}'. Cần Admin phê duyệt."
                    ),
                    category="COURSE",
                    session=db.session,
                )
        db.session.commit()

        return jsonify(
            {
                "status": "pending_approval",
                "pending_approval": True,
                "message": (
                    "Bài giảng thuộc khóa học đã ban hành. "
                    "Yêu cầu chỉnh sửa bài giảng đã được gửi tới Quản trị viên để xét duyệt."
                ),
                "change_request_id": req.id,
                "lesson": _serialize_lesson(lesson),
            }
        ), 202

    updated_lesson = update_lesson(actor, lesson_id, payload, session=db.session)
    return jsonify(_serialize_lesson(updated_lesson)), 200


@instructor_bp.route("/courses/<course_id>/lessons/reorder", methods=["POST"])
@instructor_required
def reorder_lessons_route(course_id: str) -> tuple[Response, int] | Response:
    """Reorder lessons within a course."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    raw_ids = payload.get("ordered_lesson_ids")
    if not isinstance(raw_ids, list):
        raise LessonValidationError("ordered_lesson_ids must be a list of lesson IDs.")

    ordered_ids: list[int | uuid.UUID | str] = [
        item for item in raw_ids if isinstance(item, (int, uuid.UUID, str))
    ]
    reordered = reorder_lessons(actor, course_id, ordered_ids)
    return jsonify({"lessons": [_serialize_lesson(les) for les in reordered]}), 200


@instructor_bp.route("/lessons/<lesson_id>/status", methods=["POST"])
@instructor_required
def change_lesson_status_route(lesson_id: str) -> tuple[Response, int] | Response:
    """Change status of a lesson (PUBLISHED, HIDDEN, DRAFT)."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    new_status = payload.get("status")
    if not new_status or not isinstance(new_status, str):
        raise LessonValidationError("status is required and must be a string.")

    reason = payload.get("reason")
    if reason is not None and not isinstance(reason, str):
        reason = str(reason)

    lesson = change_lesson_status(actor, lesson_id, new_status, reason=reason)
    return jsonify(_serialize_lesson(lesson)), 200


@instructor_bp.route("/lessons/<lesson_id>/trash", methods=["POST", "DELETE"])
@instructor_required
def trash_lesson_route(lesson_id: str) -> tuple[Response, int] | Response:
    """Soft-delete a lesson to TRASH with admin approval gate for published content."""
    actor = require_authenticated_actor()

    lesson = _resolve_lesson(lesson_id, session=db.session)
    if lesson is None:
        raise LessonValidationError("Lesson not found.")

    course = require_course_manager(actor, lesson.course_id, session=db.session)
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")

    if not actor.is_admin and (
        course.status in ("APPROVED", "PUBLISHED", "ARCHIVED") or lesson.status == "PUBLISHED"
    ):
        req = CourseChangeRequest(
            course_id=course.id,
            requested_by_user_id=actor.id,
            change_type="LESSON_STRUCTURE",
            target_type="LESSON",
            target_id=lesson.id,
            proposed_payload_json=json.dumps(
                {
                    "action": "DELETE",
                    "lesson_id": lesson.id,
                    "lesson_title": lesson.title,
                    "reason": reason or "Giảng viên yêu cầu xóa bài giảng",
                },
                default=str,
            ),
            status="PENDING",
            created_at=utc_now(),
        )
        db.session.add(req)
        db.session.flush()

        from pwd301.services.notification_service import dispatch_notification

        admin_users = db.session.query(User).filter(User.roles.any(Role.code == "ADMIN")).all()
        for adm in admin_users:
            with contextlib.suppress(Exception):
                dispatch_notification(
                    recipient_user=adm,
                    event_type="LESSON_CHANGE_REQUEST",
                    title=f"Yêu cầu xóa bài giảng: {lesson.title}",
                    body=(
                        f"Giảng viên {actor.display_name} gửi yêu cầu xóa bài giảng "
                        f"'{lesson.title}' trong khóa học '{course.title}'. Cần Admin phê duyệt."
                    ),
                    category="COURSE",
                    session=db.session,
                )
        db.session.commit()

        return jsonify(
            {
                "status": "pending_approval",
                "pending_approval": True,
                "message": (
                    "Bài giảng thuộc khóa học đã ban hành. "
                    "Yêu cầu xóa bài giảng đã được gửi tới Quản trị viên để xét duyệt."
                ),
                "change_request_id": req.id,
            }
        ), 202

    trashed_lesson = trash_lesson(actor, lesson_id, reason=reason, session=db.session)
    return jsonify(_serialize_lesson(trashed_lesson)), 200


def _serialize_enrolled_student(e: Enrollment) -> dict[str, Any]:
    return {
        "enrollment_id": str(e.public_id),
        "student_id": str(e.student.public_id) if e.student else None,
        "student_name": e.student.display_name if e.student else None,
        "student_email": e.student.email if e.student else None,
        "status": e.status,
        "period_no": e.current_period.period_no if e.current_period else None,
        "current_progress_percent": float(e.current_progress_percent or 0.0),
        "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
        "left_at": e.left_at.isoformat() if e.left_at else None,
    }


def _serialize_prerequisite_course(c: Course) -> dict[str, Any]:
    return {
        "course_id": str(c.public_id),
        "course_code": c.course_code,
        "title": c.title,
        "category": c.category,
        "difficulty": c.difficulty,
        "status": c.status,
    }


@instructor_bp.route("/courses/<course_id>/students", methods=["GET"])
@instructor_required
def list_course_students_route(course_id: str) -> tuple[Response, int] | Response:
    """List students enrolled in the managed course with pagination and filtering."""
    actor = require_authenticated_actor()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status")

    items, total = get_course_enrollments(
        actor=actor,
        course_id=course_id,
        status=status,
        page=page,
        per_page=per_page,
        session=db.session,
    )
    return (
        jsonify(
            {
                "items": [_serialize_enrolled_student(e) for e in items],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_items": total,
                    "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
                },
            }
        ),
        200,
    )


@instructor_bp.route("/courses/<course_id>/prerequisites", methods=["GET"])
@instructor_required
def list_course_prerequisites_route(course_id: str) -> tuple[Response, int] | Response:
    """List direct prerequisite courses for a managed course."""
    actor = require_authenticated_actor()

    require_course_manager(actor, course_id, session=db.session)
    prereqs = get_course_prerequisites(course_id, session=db.session)
    return jsonify({"prerequisites": [_serialize_prerequisite_course(c) for c in prereqs]}), 200


@instructor_bp.route("/courses/<course_id>/prerequisites", methods=["POST"])
@instructor_required
def add_course_prerequisite_route(course_id: str) -> Any:
    """Add a prerequisite course dependency.

    Supports DAG cycle detection and cross-instructor approval.
    """
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    prerequisite_course_id = payload.get("prerequisite_course_id")
    if not prerequisite_course_id:
        raise CourseValidationError("prerequisite_course_id is required.")

    target_course = require_course_manager(actor, course_id, session=db.session)
    prereq_course = _resolve_course(prerequisite_course_id, session=db.session)
    if prereq_course is None:
        raise CourseValidationError("Prerequisite course not found.")

    if target_course.id == prereq_course.id:
        raise CourseValidationError("A course cannot be a prerequisite of itself.")

    # Cross-instructor permission check (Item 12):
    # If target course and prerequisite course have different owners, and actor is not admin:
    if (
        target_course.owner_instructor_id != prereq_course.owner_instructor_id
        and prereq_course.owner_instructor_id != actor.id
        and not actor.is_admin
    ):
        # 1. Check existing link
        existing_link = (
            db.session.query(CoursePrerequisite)
            .filter_by(course_id=target_course.id, prerequisite_course_id=prereq_course.id)
            .first()
        )
        if existing_link is not None:
            return jsonify(
                {
                    "status": "success",
                    "direct": True,
                    "message": "Môn học này đã nằm trong danh sách điều kiện tiên quyết.",
                    "course_id": str(target_course.public_id),
                    "prerequisite_course_id": str(prereq_course.public_id),
                }
            ), 200

        # 2. Check DAG cycle detection before sending request
        visited: set[int] = set()
        queue: list[int] = [prereq_course.id]
        while queue:
            curr_id = queue.pop(0)
            if curr_id == target_course.id:
                from pwd301.services.exceptions import PrerequisiteCycleError

                raise PrerequisiteCycleError(
                    f"Thêm môn tiên quyết '{prereq_course.title}' vào '{target_course.title}' "
                    f"sẽ tạo chu trình phụ thuộc vòng tròn (Cyclic Dependency)."
                )
            if curr_id in visited:
                continue
            visited.add(curr_id)
            child_links = (
                db.session.query(CoursePrerequisite.prerequisite_course_id)
                .filter(CoursePrerequisite.course_id == curr_id)
                .all()
            )
            for (next_prereq_id,) in child_links:
                if next_prereq_id not in visited:
                    queue.append(next_prereq_id)

        # 3. Check existing pending request
        pending_req = (
            db.session.query(CourseChangeRequest)
            .filter(
                CourseChangeRequest.course_id == target_course.id,
                CourseChangeRequest.change_type == "PREREQUISITE",
                CourseChangeRequest.target_id == prereq_course.id,
                CourseChangeRequest.status == "PENDING",
            )
            .first()
        )
        if pending_req is not None:
            return jsonify(
                {
                    "status": "pending_approval",
                    "direct": False,
                    "message": (
                        f"Yêu cầu xin thêm môn tiên quyết '{prereq_course.title}' "
                        f"đã được gửi và đang chờ giảng viên phụ trách phê duyệt."
                    ),
                    "change_request_id": pending_req.id,
                }
            ), 200

        # 4. Create staged change request
        req_payload = {
            "target_course_id": target_course.id,
            "target_course_title": target_course.title,
            "target_course_code": target_course.course_code,
            "prerequisite_course_id": prereq_course.id,
            "prerequisite_course_title": prereq_course.title,
            "prerequisite_course_code": prereq_course.course_code,
            "min_grade_point": payload.get("min_grade_point", 5.0),
            "reason": payload.get("reason", "Yêu cầu tiên quyết từ giảng viên phụ trách"),
        }
        change_req = CourseChangeRequest(
            course_id=target_course.id,
            requested_by_user_id=actor.id,
            change_type="PREREQUISITE",
            target_type="PREREQUISITE",
            target_id=prereq_course.id,
            proposed_payload_json=json.dumps(req_payload, default=str),
            status="PENDING",
            created_at=utc_now(),
        )
        db.session.add(change_req)
        db.session.flush()

        # 5. Dispatch notification to prerequisite course owner
        prereq_owner = prereq_course.owner_instructor
        if prereq_owner:
            with contextlib.suppress(Exception):
                from pwd301.services.notification_service import dispatch_notification

                dispatch_notification(
                    recipient_user=prereq_owner,
                    event_type="COURSE_PREREQUISITE_REQUEST",
                    title=f"Yêu cầu môn tiên quyết: {target_course.title}",
                    body=(
                        f"Giảng viên {actor.display_name} gửi yêu cầu thiết lập môn học "
                        f"'{prereq_course.title}' của bạn làm môn học tiên quyết cho khóa học "
                        f"'{target_course.title}' ({target_course.course_code}). "
                        f"Lý do: {payload.get('reason', 'Không có')}."
                    ),
                    category="COURSE",
                    session=db.session,
                )

        db.session.commit()

        owner_name = prereq_owner.display_name if prereq_owner else "khác"
        return jsonify(
            {
                "status": "pending_approval",
                "direct": False,
                "message": (
                    f"Môn học '{prereq_course.title}' thuộc sở hữu của giảng viên {owner_name}. "
                    f"Đã gửi thông báo và yêu cầu xin duyệt môn tiên quyết tới "
                    f"giảng viên phụ trách."
                ),
                "change_request_id": change_req.id,
                "course_id": str(target_course.public_id),
                "prerequisite_course_id": str(prereq_course.public_id),
            }
        ), 202

    # Direct addition (Same instructor or Admin)
    link = add_course_prerequisite(
        actor=actor,
        course_id=course_id,
        prerequisite_course_id=prerequisite_course_id,
        session=db.session,
    )

    return (
        jsonify(
            {
                "status": "success",
                "direct": True,
                "course_id": str(target_course.public_id),
                "prerequisite_course_id": str(prereq_course.public_id),
                "created_at": link.created_at.isoformat(),
                "message": "Đã thêm môn tiên quyết thành công!",
            }
        ),
        201,
    )


@instructor_bp.route("/courses/<course_id>/prerequisites/<prereq_id>", methods=["DELETE"])
@instructor_bp.route(
    "/courses/<course_id>/prerequisites/<prereq_id>/delete", methods=["POST", "DELETE"]
)
@instructor_required
def remove_course_prerequisite_route(course_id: str, prereq_id: str) -> Any:
    """Remove a prerequisite dependency."""
    actor = require_authenticated_actor()

    removed = remove_course_prerequisite(
        actor=actor,
        course_id=course_id,
        prerequisite_course_id=prereq_id,
        session=db.session,
    )

    return jsonify({"removed": removed}), 200


@instructor_bp.route("/prerequisite-requests", methods=["GET"])
@instructor_required
def list_instructor_prerequisite_requests_route() -> tuple[Response, int] | Response:
    """List incoming and outgoing prerequisite course change requests for the instructor."""
    actor = require_authenticated_actor()

    owned_course_ids = [
        c.id
        for c in db.session.query(Course.id).filter(Course.owner_instructor_id == actor.id).all()
    ]

    incoming = []
    if owned_course_ids:
        in_reqs = (
            db.session.query(CourseChangeRequest)
            .filter(
                CourseChangeRequest.change_type == "PREREQUISITE",
                CourseChangeRequest.target_id.in_(owned_course_ids),
                CourseChangeRequest.status == "PENDING",
            )
            .order_by(CourseChangeRequest.created_at.desc())
            .all()
        )
        for r in in_reqs:
            try:
                p_data = json.loads(r.proposed_payload_json) if r.proposed_payload_json else {}
            except Exception:
                p_data = {}
            incoming.append(
                {
                    "id": r.id,
                    "course_id": r.course_id,
                    "course_title": p_data.get("target_course_title")
                    or (r.course.title if r.course else None),
                    "course_code": p_data.get("target_course_code")
                    or (r.course.course_code if r.course else None),
                    "prerequisite_course_id": r.target_id,
                    "prerequisite_course_title": p_data.get("prerequisite_course_title"),
                    "prerequisite_course_code": p_data.get("prerequisite_course_code"),
                    "requested_by_name": r.requested_by.display_name if r.requested_by else None,
                    "reason": p_data.get("reason"),
                    "created_at": r.created_at.isoformat(),
                    "status": r.status,
                }
            )

    out_reqs = (
        db.session.query(CourseChangeRequest)
        .filter(
            CourseChangeRequest.change_type == "PREREQUISITE",
            CourseChangeRequest.requested_by_user_id == actor.id,
        )
        .order_by(CourseChangeRequest.created_at.desc())
        .limit(20)
        .all()
    )
    outgoing = []
    for r in out_reqs:
        try:
            p_data = json.loads(r.proposed_payload_json) if r.proposed_payload_json else {}
        except Exception:
            p_data = {}
        outgoing.append(
            {
                "id": r.id,
                "course_id": r.course_id,
                "course_title": p_data.get("target_course_title")
                or (r.course.title if r.course else None),
                "prerequisite_course_id": r.target_id,
                "prerequisite_course_title": p_data.get("prerequisite_course_title"),
                "status": r.status,
                "review_reason": r.review_reason,
                "created_at": r.created_at.isoformat(),
            }
        )

    return jsonify({"incoming": incoming, "outgoing": outgoing}), 200


@instructor_bp.route("/prerequisite-requests/<int:req_id>/review", methods=["POST"])
@instructor_required
def review_instructor_prerequisite_request_route(req_id: int) -> tuple[Response, int] | Response:
    """Approve or reject an incoming prerequisite request by the prerequisite course owner."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    action = str(payload.get("action", "")).strip().lower()
    reason = str(payload.get("reason", "")).strip()

    if action not in ("approve", "reject"):
        raise ValidationError("Action must be 'approve' or 'reject'.")

    req_record = db.session.get(CourseChangeRequest, req_id)
    if req_record is None or req_record.change_type != "PREREQUISITE":
        raise ResourceNotFoundError("Prerequisite change request not found.")

    prereq_course = db.session.get(Course, req_record.target_id)
    if prereq_course is None:
        raise ResourceNotFoundError("Prerequisite course not found.")

    if prereq_course.owner_instructor_id != actor.id and not actor.is_admin:
        raise ForbiddenError("You are not authorized to review this prerequisite request.")

    if req_record.status != "PENDING":
        raise CourseValidationError(f"Request is already in '{req_record.status}' status.")

    from pwd301.services.notification_service import dispatch_notification

    now = utc_now()
    if action == "approve":
        existing = (
            db.session.query(CoursePrerequisite)
            .filter_by(course_id=req_record.course_id, prerequisite_course_id=prereq_course.id)
            .first()
        )
        if existing is None:
            link = CoursePrerequisite(
                course_id=req_record.course_id,
                prerequisite_course_id=prereq_course.id,
                created_by_user_id=actor.id,
                created_at=now,
            )
            db.session.add(link)

        req_record.status = "APPROVED"
        req_record.reviewed_by_user_id = actor.id
        req_record.review_reason = reason or "Đã chấp thuận đề xuất môn tiên quyết"
        req_record.reviewed_at = now
        req_record.applied_at = now
        db.session.flush()

        if req_record.requested_by:
            with contextlib.suppress(Exception):
                dispatch_notification(
                    recipient_user=req_record.requested_by,
                    event_type="COURSE_PREREQUISITE_APPROVED",
                    title=f"Yêu cầu môn tiên quyết được chấp thuận: {prereq_course.title}",
                    body=(
                        f"Giảng viên {actor.display_name} đã phê duyệt yêu cầu sử dụng môn "
                        f"'{prereq_course.title}' làm môn tiên quyết cho khóa học của bạn."
                    ),
                    category="COURSE",
                    session=db.session,
                )

        msg = f"Đã phê duyệt yêu cầu sử dụng môn '{prereq_course.title}' làm môn tiên quyết."

    else:
        req_record.status = "REJECTED"
        req_record.reviewed_by_user_id = actor.id
        req_record.review_reason = reason or "Từ chối yêu cầu môn tiên quyết"
        req_record.reviewed_at = now
        db.session.flush()

        if req_record.requested_by:
            with contextlib.suppress(Exception):
                dispatch_notification(
                    recipient_user=req_record.requested_by,
                    event_type="COURSE_PREREQUISITE_REJECTED",
                    title=f"Yêu cầu môn tiên quyết bị từ chối: {prereq_course.title}",
                    body=(
                        f"Giảng viên {actor.display_name} đã từ chối yêu cầu sử dụng môn "
                        f"'{prereq_course.title}' làm môn tiên quyết. "
                        f"Lý do: {reason or 'Không có'}."
                    ),
                    category="COURSE",
                    session=db.session,
                )

        msg = f"Đã từ chối yêu cầu môn tiên quyết '{prereq_course.title}'."

    db.session.commit()
    return jsonify({"status": req_record.status, "message": msg}), 200


def _serialize_completion_rule(course: Course, rule: Any) -> dict[str, Any]:
    return {
        "course_id": str(course.public_id),
        "course_code": course.course_code,
        "title": course.title,
        "require_all_required_lessons": bool(rule.require_all_required_lessons),
        "require_required_assessments": bool(rule.require_required_assessments),
        "minimum_progress_percent": (
            float(rule.minimum_progress_percent)
            if rule.minimum_progress_percent is not None
            else None
        ),
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


@instructor_bp.route("/courses/<course_id>/completion-rules", methods=["GET"])
@instructor_required
def get_course_completion_rules_route(course_id: str) -> tuple[Response, int] | Response:
    """Retrieve completion rule criteria for a managed course."""
    actor = require_authenticated_actor()

    course = require_course_manager(actor, course_id, session=db.session)
    rule = get_or_create_default_completion_rule(course.id, session=db.session)
    return jsonify(_serialize_completion_rule(course, rule)), 200


@instructor_bp.route("/courses/<course_id>/completion-rules", methods=["POST", "PUT"])
@instructor_required
def set_course_completion_rules_route(course_id: str) -> tuple[Response, int] | Response:
    """Set or update completion rule criteria for a managed course."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    course = require_course_manager(actor, course_id, session=db.session)
    rule = set_course_completion_rule(
        actor=actor,
        course_id=course.id,
        payload=payload,
        session=db.session,
    )
    return jsonify(_serialize_completion_rule(course, rule)), 200


@instructor_bp.route("/courses/<course_id>/questions", methods=["GET"])
@instructor_required
def list_course_questions_route(course_id: str) -> Any:
    """List questions for a course in the instructor dashboard."""
    actor = require_authenticated_actor()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    filters = {
        "difficulty": request.args.get("difficulty"),
        "question_type": request.args.get("question_type") or request.args.get("type"),
        "lesson_id": request.args.get("lesson_id"),
        "status": request.args.get("status"),
        "search": request.args.get("search") or request.args.get("q"),
    }

    items, total, p, pp, total_pages = list_course_questions(
        actor=actor,
        course_id=course_id,
        filters=filters,
        page=page,
        per_page=per_page,
        session=db.session,
    )

    data = {
        "items": items,
        "total": total,
        "page": p,
        "per_page": pp,
        "total_pages": total_pages,
    }
    return jsonify(data), 200


@instructor_bp.route("/courses/<course_id>/questions/summary", methods=["GET"])
@instructor_required
def get_course_question_summary_route(course_id: str) -> Any:
    """Retrieve aggregated question metrics (Bloom difficulty, type, lesson) for a course."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)
    sess = db.session

    total = (
        sess.query(sa.func.count(Question.id))
        .filter(Question.course_id == course.id, Question.status != "TRASH")
        .scalar()
        or 0
    )

    by_difficulty: dict[str, int] = {"REMEMBER": 0, "UNDERSTAND": 0, "APPLY": 0}
    diff_rows = (
        sess.query(Question.difficulty, sa.func.count(Question.id))
        .filter(Question.course_id == course.id, Question.status != "TRASH")
        .group_by(Question.difficulty)
        .all()
    )
    for diff, count in diff_rows:
        if diff:
            by_difficulty[str(diff).upper()] = count

    by_type: dict[str, int] = {
        "SINGLE_CHOICE": 0,
        "MULTIPLE_CHOICE": 0,
        "TRUE_FALSE": 0,
        "SHORT_ANSWER": 0,
    }
    type_rows = (
        sess.query(QuestionRevision.question_type, sa.func.count(Question.id))
        .join(
            QuestionRevision,
            sa.and_(
                Question.id == QuestionRevision.question_id,
                QuestionRevision.is_current == True,
            ),
        )
        .filter(Question.course_id == course.id, Question.status != "TRASH")
        .group_by(QuestionRevision.question_type)
        .all()
    )
    for q_type, count in type_rows:
        if q_type:
            by_type[str(q_type).upper()] = count

    lesson_rows = (
        sess.query(Lesson.public_id, Lesson.title, sa.func.count(Question.id))
        .join(Lesson, Question.lesson_id == Lesson.id)
        .filter(Question.course_id == course.id, Question.status != "TRASH")
        .group_by(Lesson.public_id, Lesson.title)
        .all()
    )
    by_lesson: list[dict[str, Any]] = [
        {
            "lesson_id": str(lp_id),
            "lesson_title": str(ltitle),
            "question_count": count,
        }
        for lp_id, ltitle, count in lesson_rows
    ]

    unassigned_count = (
        sess.query(sa.func.count(Question.id))
        .filter(
            Question.course_id == course.id,
            Question.status != "TRASH",
            Question.lesson_id.is_(None),
        )
        .scalar()
        or 0
    )
    if unassigned_count > 0:
        by_lesson.append(
            {
                "lesson_id": None,
                "lesson_title": "Chưa phân bài học",
                "question_count": unassigned_count,
            }
        )

    return jsonify(
        {
            "total": total,
            "by_difficulty": by_difficulty,
            "by_type": by_type,
            "by_lesson": by_lesson,
        }
    ), 200


@instructor_bp.route("/courses/<course_id>/questions", methods=["POST"])
@instructor_required
def create_course_question_route(course_id: str) -> Any:
    """Create a new question in the instructor question authoring workflow."""
    actor = require_authenticated_actor()

    payload: dict[str, Any] = request.get_json(silent=True) or request.form.to_dict() or {}
    if not request.is_json and "choices" not in payload:
        raw_choices = []
        correct_choice = request.form.get("correct_choice", "1")
        for i in range(1, 10):
            c_text = request.form.get(f"choice_{i}")
            if c_text and c_text.strip():
                raw_choices.append(
                    {
                        "content": c_text.strip(),
                        "is_correct": str(correct_choice) == str(i),
                        "position": i,
                    }
                )
        if raw_choices:
            payload["choices"] = raw_choices
        elif payload.get("question_type") == "TRUE_FALSE":
            tf_correct = request.form.get("correct_tf", "TRUE").upper() == "TRUE"
            payload["choices"] = [
                {"content": "Đúng (True)", "is_correct": tf_correct, "position": 1},
                {"content": "Sai (False)", "is_correct": not tf_correct, "position": 2},
            ]

    question = create_question(actor, course_id, payload, session=db.session)

    return jsonify(_serialize_question(question)), 201


@instructor_bp.route("/questions/<question_id>", methods=["GET"])
@instructor_required
def get_question_detail_route(question_id: str) -> tuple[Response, int] | Response:
    """Retrieve question details for viewing or editing."""
    actor = require_authenticated_actor()

    data = get_question_detail(actor, question_id, session=db.session)
    return jsonify(data), 200


@instructor_bp.route("/questions/<question_id>/trash", methods=["POST"])
@instructor_required
def trash_question_route(question_id: str) -> tuple[Response, int] | Response:
    """Move a question to TRASH."""
    actor = require_authenticated_actor()

    body = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = body.get("reason")

    question = trash_question(actor, question_id, reason=reason, session=db.session)

    return jsonify(
        {
            "message": "Question moved to trash.",
            "question": _serialize_question(question),
        }
    ), 200


@instructor_bp.route("/questions/<question_id>/restore", methods=["POST"])
@instructor_required
def restore_question_route(question_id: str) -> tuple[Response, int] | Response:
    """Restore a question from TRASH back to ACTIVE."""
    actor = require_authenticated_actor()

    body = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = body.get("reason")

    question = restore_question(actor, question_id, reason=reason, session=db.session)

    return jsonify(
        {
            "message": "Question restored from trash.",
            "question": _serialize_question(question),
        }
    ), 200


@instructor_bp.route("/questions/<question_id>", methods=["PATCH", "PUT"])
@instructor_required
def update_question_route(question_id: str) -> tuple[Response, int] | Response:
    """Update question or create a revision if branched."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    question = update_question(actor, question_id, payload, session=db.session)

    return jsonify(_serialize_question(question)), 200


@instructor_bp.route("/questions/<question_id>/revisions", methods=["GET"])
@instructor_required
def list_question_revisions_route(question_id: str) -> tuple[Response, int] | Response:
    """List revisions for a question."""
    actor = require_authenticated_actor()

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    items, total, p, pp, total_pages = list_question_revisions(
        actor=actor,
        question_id=question_id,
        page=page,
        per_page=per_page,
        session=db.session,
    )

    data = {
        "items": items,
        "total": total,
        "page": p,
        "per_page": pp,
        "total_pages": total_pages,
    }
    return jsonify(data), 200


@instructor_bp.route("/questions/<question_id>/revisions", methods=["POST"])
@instructor_required
def create_question_revision_route(question_id: str) -> tuple[Response, int] | Response:
    """Create a new revision explicitly for a question."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    revision, correction = create_question_revision(
        actor=actor,
        question_id=question_id,
        payload=payload,
        session=db.session,
    )

    resp: dict[str, Any] = {
        "revision": _serialize_question_revision(revision),
    }
    if correction is not None:
        resp["correction"] = _serialize_question_correction(correction)

    return jsonify(resp), 201


@instructor_bp.route("/questions/<question_id>/revisions/<int:revision_no>", methods=["GET"])
@instructor_required
def get_question_revision_detail_route(
    question_id: str, revision_no: int
) -> tuple[Response, int] | Response:
    """Retrieve detailed information for a specific question revision."""
    actor = require_authenticated_actor()

    data = get_question_revision_detail(
        actor=actor,
        question_id=question_id,
        revision_no=revision_no,
        session=db.session,
    )
    return jsonify(data), 200


@instructor_bp.route("/questions/<question_id>/corrections", methods=["GET"])
@instructor_required
def list_question_corrections_route(question_id: str) -> tuple[Response, int] | Response:
    """List corrections for a question."""
    actor = require_authenticated_actor()

    items = list_question_corrections(
        actor=actor,
        question_id=question_id,
        session=db.session,
    )
    return jsonify({"items": items}), 200


# ============================================================================
# INSTRUCTOR ASSESSMENT BUILDER & MANAGEMENT ROUTES
# ============================================================================


@instructor_bp.route("/courses/<course_id>/assessments", methods=["GET"])
@instructor_required
def list_instructor_course_assessments_route(course_id: str) -> tuple[Response, int] | Response:
    """List assessments for a course in instructor view."""
    actor = require_authenticated_actor()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    filters = {
        "assessment_type": request.args.get("assessment_type") or request.args.get("type"),
        "status": request.args.get("status"),
    }

    items, total, p, pp, total_pages = list_course_assessments(
        actor=actor,
        course_id=course_id,
        filters=filters,
        page=page,
        per_page=per_page,
        session=db.session,
    )

    data = {
        "items": items,
        "total": total,
        "page": p,
        "per_page": pp,
        "total_pages": total_pages,
    }
    return jsonify(data), 200


@instructor_bp.route("/assessments/<assessment_id>", methods=["GET"])
@instructor_required
def get_instructor_assessment_detail_route(assessment_id: str) -> Any:
    """Retrieve detailed assessment configuration or render assessment builder page."""
    actor = require_authenticated_actor()
    asm_obj = _resolve_assessment(assessment_id, session=db.session)
    if asm_obj is None:
        raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")

    data = get_assessment_detail(actor, assessment_id, session=db.session)
    data["public_id"] = str(asm_obj.public_id)
    data["assessment_id"] = str(asm_obj.public_id)
    data["question_assignments"] = asm_obj.question_assignments

    return jsonify(data), 200


@instructor_bp.route("/assessments/<assessment_id>", methods=["PATCH", "PUT", "POST"])
@instructor_required
def update_instructor_assessment_route(assessment_id: str) -> Any:
    """Update assessment configuration."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    try:
        assessment = update_assessment(actor, assessment_id, payload, session=db.session)
        return jsonify(_serialize_assessment(assessment, full=False)), 200
    except Exception:
        raise


@instructor_bp.route("/assessments/<assessment_id>/publish", methods=["POST"])
@instructor_bp.route("/courses/<course_id>/assessments/<assessment_id>/publish", methods=["POST"])
@instructor_required
def publish_instructor_assessment_route(assessment_id: str, course_id: str | None = None) -> Any:
    """Publish assessment (DRAFT -> PUBLISHED)."""
    actor = require_authenticated_actor()

    try:
        assessment = publish_assessment(actor, assessment_id, session=db.session)
        return jsonify(_serialize_assessment(assessment, full=False)), 200
    except Exception:
        raise


@instructor_bp.route("/assessments/<assessment_id>/cancel", methods=["POST"])
@instructor_required
def cancel_instructor_assessment_route(assessment_id: str) -> Any:
    """Cancel a published assessment."""
    actor = require_authenticated_actor()

    body = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = body.get("reason", "Giảng viên chủ động hủy đợt thi")

    try:
        assessment = cancel_assessment(actor, assessment_id, reason=reason, session=db.session)
        return jsonify(
            {
                "message": "Assessment cancelled.",
                "assessment": _serialize_assessment(assessment, full=False),
            }
        ), 200
    except Exception:
        raise


@instructor_bp.route("/assessments/<assessment_id>/trash", methods=["POST"])
@instructor_required
def trash_instructor_assessment_route(assessment_id: str) -> Any:
    """Move assessment to TRASH."""
    actor = require_authenticated_actor()

    body = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = body.get("reason", "Xóa bởi Giảng viên")

    try:
        assessment = trash_assessment(actor, assessment_id, reason=reason, session=db.session)
        return jsonify(
            {
                "message": "Assessment moved to trash.",
                "assessment": _serialize_assessment(assessment, full=False),
            }
        ), 200
    except Exception:
        raise


@instructor_bp.route("/assessments/<assessment_id>/restore", methods=["POST"])
@instructor_required
def restore_instructor_assessment_route(assessment_id: str) -> Any:
    """Restore assessment from TRASH."""
    actor = require_authenticated_actor()

    try:
        assessment = restore_assessment(actor, assessment_id, session=db.session)
        return jsonify(
            {
                "message": "Assessment restored from trash.",
                "assessment": _serialize_assessment(assessment, full=False),
            }
        ), 200
    except Exception:
        raise


@instructor_bp.route("/assessments/<assessment_id>/sections", methods=["POST"])
@instructor_required
def create_instructor_section_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Create a new section in assessment."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    section = create_section(actor, assessment_id, payload, session=db.session)

    return jsonify(_serialize_section(section)), 201


@instructor_bp.route("/assessments/<assessment_id>/sections/<section_id>", methods=["DELETE"])
@instructor_required
def delete_instructor_section_route(
    assessment_id: str, section_id: str
) -> tuple[Response, int] | Response:
    """Delete a section from assessment."""
    actor = require_authenticated_actor()

    delete_section(actor, assessment_id, section_id, session=db.session)

    return jsonify({"message": "Section deleted successfully."}), 200


@instructor_bp.route("/assessments/<assessment_id>/questions", methods=["POST"])
@instructor_required
def assign_instructor_question_route(assessment_id: str) -> Any:
    """Assign a fixed question to assessment."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    try:
        assignment = assign_question(actor, assessment_id, payload, session=db.session)
        return jsonify(_serialize_assignment(assignment)), 201
    except Exception:
        raise


@instructor_bp.route("/assessments/<assessment_id>/questions/<question_id>", methods=["DELETE"])
@instructor_bp.route(
    "/assessments/<assessment_id>/questions/<question_id>/remove", methods=["POST"]
)
@instructor_required
def remove_instructor_question_route(assessment_id: str, question_id: str) -> Any:
    """Remove a fixed question from assessment."""
    actor = require_authenticated_actor()

    try:
        remove_question_assignment(actor, assessment_id, question_id, session=db.session)
        return jsonify({"message": "Question unassigned successfully."}), 200
    except Exception:
        raise


@instructor_bp.route("/assessments/<assessment_id>/questions/create", methods=["POST"])
@instructor_required
def create_instructor_assessment_question_route(assessment_id: str) -> Any:
    """Directly author and assign a question to an assessment from the assessment builder."""
    actor = require_authenticated_actor()
    asm_obj = _resolve_assessment(assessment_id, session=db.session)
    if asm_obj is None:
        raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")

    require_course_manager(actor, asm_obj.course_id, session=db.session)

    if asm_obj.first_attempt_started_at is not None:
        raise AssessmentLockedError(
            "Cấu trúc đề thi đã bị khóa do đã có thí sinh bắt đầu làm bài "
            "(Structural Freeze - Invariant 14)."
        )

    try:
        payload = request.get_json(silent=True) or request.form.to_dict() or {}

        raw_type = payload.get("question_type") or payload.get("type") or "SINGLE_CHOICE"
        q_type = str(raw_type).strip().upper()
        if q_type not in (
            "SINGLE_CHOICE",
            "MULTIPLE_CHOICE",
            "TRUE_FALSE",
            "SHORT_ANSWER",
        ):
            raise ValidationError(
                f"Loại câu hỏi '{q_type}' không hợp lệ. "
                "Chỉ hỗ trợ SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER."
            )

        raw_content = payload.get("content") or payload.get("prompt") or payload.get("stem") or ""
        content = str(raw_content).strip()
        if not content:
            raise ValidationError("Nội dung câu hỏi không được để trống.")

        difficulty = (
            str(payload.get("difficulty") or payload.get("bloom_difficulty") or "UNDERSTAND")
            .strip()
            .upper()
        )
        if difficulty not in ("REMEMBER", "UNDERSTAND", "APPLY"):
            difficulty = "UNDERSTAND"

        raw_points = payload.get("points") or payload.get("default_points") or 1.0
        try:
            points = float(raw_points)
            if points <= 0:
                raise ValueError()
        except (ValueError, TypeError) as err:
            raise ValidationError("Điểm phân bổ phải là một số lớn hơn 0.") from err

        raw_explanation = payload.get("explanation")
        explanation = str(raw_explanation).strip() if raw_explanation else None

        q_payload: dict[str, Any] = {
            "question_type": q_type,
            "difficulty": difficulty,
            "content": content,
            "default_points": points,
            "explanation": explanation,
            "provenance": {
                "source_type": "MANUAL",
                "notes": f"Directly authored in assessment builder {asm_obj.public_id}",
            },
        }

        # Choices / Accepted answers parsing
        if q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"):
            choices: list[dict[str, Any]] = []
            raw_choices = payload.get("choices")

            if isinstance(raw_choices, str):
                with contextlib.suppress(Exception):
                    raw_choices = json.loads(raw_choices)

            if isinstance(raw_choices, list) and raw_choices:
                for idx, c in enumerate(raw_choices, start=1):
                    if isinstance(c, dict):
                        c_text = str(c.get("content") or c.get("text") or "").strip()
                        is_corr = bool(c.get("is_correct", False))
                        if c_text:
                            choices.append(
                                {
                                    "content": c_text,
                                    "is_correct": is_corr,
                                    "position": int(c.get("position", idx)),
                                }
                            )
            elif "choice_content" in request.form or request.form.getlist("choice_content[]"):
                choice_list = request.form.getlist("choice_content") or request.form.getlist(
                    "choice_content[]"
                )
                if q_type == "SINGLE_CHOICE":
                    correct_idx = request.form.get("correct_choice", "0")
                    for idx, c_text in enumerate(choice_list):
                        t = c_text.strip()
                        if t:
                            choices.append(
                                {
                                    "content": t,
                                    "is_correct": (str(idx) == str(correct_idx)),
                                    "position": idx + 1,
                                }
                            )
                elif q_type == "MULTIPLE_CHOICE":
                    correct_indices = set(
                        request.form.getlist("correct_choices")
                        or request.form.getlist("correct_choices[]")
                    )
                    for idx, c_text in enumerate(choice_list):
                        t = c_text.strip()
                        if t:
                            choices.append(
                                {
                                    "content": t,
                                    "is_correct": (str(idx) in correct_indices),
                                    "position": idx + 1,
                                }
                            )
            elif q_type == "TRUE_FALSE":
                tf_correct_val = str(
                    request.form.get("tf_correct") or payload.get("tf_correct") or "true"
                ).lower()
                tf_is_true = tf_correct_val in ("true", "1", "dung", "đúng")
                choices = [
                    {"content": "Đúng", "is_correct": tf_is_true, "position": 1},
                    {"content": "Sai", "is_correct": not tf_is_true, "position": 2},
                ]

            q_payload["choices"] = choices

        elif q_type == "SHORT_ANSWER":
            accepted_answers: list[dict[str, Any]] = []
            raw_answers = payload.get("accepted_answers")

            if isinstance(raw_answers, str):
                with contextlib.suppress(Exception):
                    raw_answers = json.loads(raw_answers)

            if isinstance(raw_answers, list) and raw_answers:
                for idx, a in enumerate(raw_answers, start=1):
                    if isinstance(a, str) and a.strip():
                        accepted_answers.append({"answer_text": a.strip(), "position": idx})
                    elif isinstance(a, dict):
                        a_text = str(a.get("answer_text") or a.get("text") or "").strip()
                        if a_text:
                            accepted_answers.append({"answer_text": a_text, "position": idx})
            else:
                ans_str = str(
                    request.form.get("accepted_answers")
                    or payload.get("accepted_answers")
                    or request.form.get("short_answers")
                    or ""
                )
                parsed_lines = [
                    line.strip() for line in re.split(r"[\r\n,]+", ans_str) if line.strip()
                ]
                for idx, text in enumerate(parsed_lines, start=1):
                    accepted_answers.append({"answer_text": text, "position": idx})

            q_payload["accepted_answers"] = accepted_answers

        created_q = create_question(
            actor=actor,
            course_id=asm_obj.course_id,
            payload=q_payload,
            session=db.session,
        )

        assignment = assign_question(
            actor=actor,
            assessment_id=asm_obj.id,
            payload={"question_id": created_q.id, "points": points, "source_type": "MANUAL"},
            session=db.session,
        )

        return jsonify(
            {
                "status": "ok",
                "message": "Question created and assigned successfully.",
                "question": _serialize_question(created_q, include_answers=True),
                "assignment": _serialize_assignment(assignment),
            }
        ), 201
    except ValidationError:
        raise


@instructor_bp.route("/assessments/<assessment_id>/questions/batch", methods=["POST"])
@instructor_required
def batch_create_instructor_assessment_questions_route(assessment_id: str) -> Any:
    """Batch create questions and assign them atomically to an assessment."""
    actor = require_authenticated_actor()
    asm_obj = _resolve_assessment(assessment_id, session=db.session)
    if asm_obj is None:
        raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")

    require_course_manager(actor, asm_obj.course_id, session=db.session)

    if asm_obj.first_attempt_started_at is not None:
        raise AssessmentLockedError(
            "Cấu trúc đề thi đã bị khóa do đã có thí sinh bắt đầu làm bài "
            "(Structural Freeze - Invariant 14)."
        )

    payload = request.get_json(silent=True) or {}
    questions_data = payload.get("questions")
    if not isinstance(questions_data, list) or not questions_data:
        raise ValidationError("Danh sách câu hỏi 'questions' không được để trống.")

    created_items: list[dict[str, Any]] = []
    try:
        for idx, item in enumerate(questions_data, start=1):
            if not isinstance(item, dict):
                raise ValidationError(f"Câu hỏi #{idx} phải là một đối tượng JSON hợp lệ.")

            raw_type = item.get("question_type") or item.get("type") or "SINGLE_CHOICE"
            q_type = str(raw_type).strip().upper()
            if q_type not in (
                "SINGLE_CHOICE",
                "MULTIPLE_CHOICE",
                "TRUE_FALSE",
                "SHORT_ANSWER",
            ):
                raise ValidationError(
                    f"Câu hỏi #{idx}: Loại câu hỏi '{q_type}' không hợp lệ. "
                    "Chỉ hỗ trợ SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER."
                )

            raw_content = item.get("content") or item.get("prompt") or item.get("stem") or ""
            content = str(raw_content).strip()
            if not content:
                raise ValidationError(f"Câu hỏi #{idx}: Nội dung câu hỏi không được để trống.")

            difficulty = (
                str(item.get("difficulty") or item.get("bloom_difficulty") or "UNDERSTAND")
                .strip()
                .upper()
            )
            if difficulty not in ("REMEMBER", "UNDERSTAND", "APPLY"):
                difficulty = "UNDERSTAND"

            raw_points = item.get("points") or item.get("default_points") or 1.0
            try:
                points = float(raw_points)
                if points <= 0:
                    raise ValueError()
            except (ValueError, TypeError) as err:
                raise ValidationError(
                    f"Câu hỏi #{idx}: Điểm phân bổ phải là số lớn hơn 0."
                ) from err

            raw_explanation = item.get("explanation")
            explanation = str(raw_explanation).strip() if raw_explanation else None

            q_payload: dict[str, Any] = {
                "question_type": q_type,
                "difficulty": difficulty,
                "content": content,
                "default_points": points,
                "explanation": explanation,
                "provenance": {
                    "source_type": "MANUAL",
                    "notes": f"Batch imported into assessment {asm_obj.public_id}",
                },
            }

            raw_lesson = item.get("lesson_id")
            if raw_lesson:
                les_obj = _resolve_lesson(raw_lesson, session=db.session)
                if les_obj and les_obj.course_id == asm_obj.course_id:
                    q_payload["lesson_id"] = les_obj.id

            if q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"):
                choices: list[dict[str, Any]] = []
                raw_choices = item.get("choices")
                if isinstance(raw_choices, list) and raw_choices:
                    for c_idx, c in enumerate(raw_choices, start=1):
                        if isinstance(c, dict):
                            c_text = str(c.get("content") or c.get("text") or "").strip()
                            is_corr = bool(c.get("is_correct", False))
                            if c_text:
                                choices.append(
                                    {
                                        "content": c_text,
                                        "is_correct": is_corr,
                                        "position": int(c.get("position", c_idx)),
                                    }
                                )
                q_payload["choices"] = choices

            elif q_type == "SHORT_ANSWER":
                accepted_answers: list[dict[str, Any]] = []
                raw_answers = item.get("accepted_answers")
                if isinstance(raw_answers, list) and raw_answers:
                    for a_idx, a in enumerate(raw_answers, start=1):
                        if isinstance(a, str) and a.strip():
                            accepted_answers.append({"answer_text": a.strip(), "position": a_idx})
                        elif isinstance(a, dict):
                            a_text = str(a.get("answer_text") or a.get("text") or "").strip()
                            if a_text:
                                accepted_answers.append({"answer_text": a_text, "position": a_idx})
                q_payload["accepted_answers"] = accepted_answers

            created_q = create_question(
                actor=actor,
                course_id=asm_obj.course_id,
                payload=q_payload,
                session=db.session,
            )

            assignment = assign_question(
                actor=actor,
                assessment_id=asm_obj.id,
                payload={"question_id": created_q.id, "points": points, "source_type": "MANUAL"},
                session=db.session,
            )

            created_items.append(
                {
                    "question_id": str(created_q.public_id),
                    "assignment_id": _serialize_assignment(assignment)["assignment_id"],
                    "points": points,
                }
            )

        db.session.commit()
        return jsonify(
            {
                "status": "ok",
                "message": f"Successfully created and assigned {len(created_items)} questions.",
                "created_count": len(created_items),
                "questions": created_items,
            }
        ), 201
    except Exception:
        db.session.rollback()
        raise


@instructor_bp.route("/assessments/<assessment_id>/questions/<question_id>/edit", methods=["POST"])
@instructor_required
def edit_instructor_assessment_question_route(assessment_id: str, question_id: str) -> Any:
    """Direct in-place editing of question content, choices, answers, or assigned points."""
    actor = require_authenticated_actor()
    asm_obj = _resolve_assessment(assessment_id, session=db.session)
    if asm_obj is None:
        raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")

    require_course_manager(actor, asm_obj.course_id, session=db.session)

    if asm_obj.first_attempt_started_at is not None:
        raise AssessmentLockedError("Cấu trúc đề thi và phân bổ điểm số đã bị khóa (Invariant 14).")

    question = _resolve_question(question_id, session=db.session)
    if question is None:
        raise ResourceNotFoundError(f"Question '{question_id}' not found.")

    try:
        payload = request.get_json(silent=True) or request.form.to_dict() or {}

        # 1. Check points modification
        if "points" in payload or "points" in request.form:
            raw_points = payload.get("points") or request.form.get("points")
            if raw_points is not None and str(raw_points).strip():
                try:
                    pts = float(raw_points)
                    if pts <= 0:
                        raise ValueError()
                    update_question_assignment(
                        actor=actor,
                        assessment_id=asm_obj.id,
                        question_id=question.id,
                        payload={"points": pts},
                        session=db.session,
                    )
                except (ValueError, TypeError) as err:
                    raise ValidationError("Điểm phân bổ phải là một số lớn hơn 0.") from err

        # 2. Check question content / choices / explanation / accepted answers modification
        content_keys = (
            "content",
            "prompt",
            "stem",
            "choices",
            "choice_content",
            "accepted_answers",
            "short_answers",
            "explanation",
            "difficulty",
            "tf_correct",
        )
        has_content_updates = any(k in payload or k in request.form for k in content_keys)

        if has_content_updates:
            q_payload: dict[str, Any] = {
                "change_reason": payload.get("change_reason")
                or request.form.get("change_reason")
                or "Direct edit from assessment builder",
            }

            if "content" in payload or "prompt" in payload or "stem" in payload:
                content_val = str(
                    payload.get("content") or payload.get("prompt") or payload.get("stem") or ""
                ).strip()
                if content_val:
                    q_payload["content"] = content_val

            if "difficulty" in payload:
                diff_val = str(payload["difficulty"]).strip().upper()
                if diff_val in ("REMEMBER", "UNDERSTAND", "APPLY"):
                    q_payload["difficulty"] = diff_val

            if "explanation" in payload:
                q_payload["explanation"] = payload["explanation"]

            q_type = (
                question.current_revision.question_type
                if question.current_revision
                else "SINGLE_CHOICE"
            )

            if q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"):
                choices: list[dict[str, Any]] = []
                raw_choices = payload.get("choices")
                if isinstance(raw_choices, str):
                    with contextlib.suppress(Exception):
                        raw_choices = json.loads(raw_choices)

                if isinstance(raw_choices, list) and raw_choices:
                    for idx, c in enumerate(raw_choices, start=1):
                        if isinstance(c, dict):
                            c_text = str(c.get("content") or c.get("text") or "").strip()
                            is_corr = bool(c.get("is_correct", False))
                            if c_text:
                                choices.append(
                                    {
                                        "content": c_text,
                                        "is_correct": is_corr,
                                        "position": int(c.get("position", idx)),
                                    }
                                )
                    q_payload["choices"] = choices
                elif "choice_content" in request.form or request.form.getlist("choice_content[]"):
                    choice_list = request.form.getlist("choice_content") or request.form.getlist(
                        "choice_content[]"
                    )
                    if q_type == "SINGLE_CHOICE":
                        correct_idx = request.form.get("correct_choice", "0")
                        for idx, c_text in enumerate(choice_list):
                            t = c_text.strip()
                            if t:
                                choices.append(
                                    {
                                        "content": t,
                                        "is_correct": (str(idx) == str(correct_idx)),
                                        "position": idx + 1,
                                    }
                                )
                    elif q_type == "MULTIPLE_CHOICE":
                        correct_indices = set(
                            request.form.getlist("correct_choices")
                            or request.form.getlist("correct_choices[]")
                        )
                        for idx, c_text in enumerate(choice_list):
                            t = c_text.strip()
                            if t:
                                choices.append(
                                    {
                                        "content": t,
                                        "is_correct": (str(idx) in correct_indices),
                                        "position": idx + 1,
                                    }
                                )
                    q_payload["choices"] = choices
                elif q_type == "TRUE_FALSE" and (
                    "tf_correct" in request.form or "tf_correct" in payload
                ):
                    tf_val = str(
                        request.form.get("tf_correct") or payload.get("tf_correct") or "true"
                    ).lower()
                    tf_is_true = tf_val in ("true", "1", "dung", "đúng")
                    q_payload["choices"] = [
                        {"content": "Đúng", "is_correct": tf_is_true, "position": 1},
                        {"content": "Sai", "is_correct": not tf_is_true, "position": 2},
                    ]

            elif q_type == "SHORT_ANSWER":
                accepted_answers: list[dict[str, Any]] = []
                raw_answers = payload.get("accepted_answers")
                if isinstance(raw_answers, str):
                    with contextlib.suppress(Exception):
                        raw_answers = json.loads(raw_answers)

                if isinstance(raw_answers, list) and raw_answers:
                    for idx, a in enumerate(raw_answers, start=1):
                        if isinstance(a, str) and a.strip():
                            accepted_answers.append({"answer_text": a.strip(), "position": idx})
                        elif isinstance(a, dict):
                            a_text = str(a.get("answer_text") or a.get("text") or "").strip()
                            if a_text:
                                accepted_answers.append({"answer_text": a_text, "position": idx})
                    q_payload["accepted_answers"] = accepted_answers
                elif "accepted_answers" in request.form or "short_answers" in request.form:
                    ans_str = str(
                        request.form.get("accepted_answers")
                        or request.form.get("short_answers")
                        or ""
                    )
                    parsed_lines = [
                        line.strip() for line in re.split(r"[\r\n,]+", ans_str) if line.strip()
                    ]
                    for idx, text in enumerate(parsed_lines, start=1):
                        accepted_answers.append({"answer_text": text, "position": idx})
                    q_payload["accepted_answers"] = accepted_answers

            update_question(
                actor=actor,
                question_id=question.id,
                payload=q_payload,
                session=db.session,
            )

        return jsonify({"message": "Question updated successfully."}), 200
    except ValidationError:
        raise


@instructor_bp.route("/assessments/<assessment_id>/import", methods=["POST"])
@instructor_required
def import_assessment_document_route(assessment_id: str) -> Any:
    """Upload DOCX/PDF to extract, validate, and assign questions to this assessment."""
    actor = require_authenticated_actor()
    asm_obj = _resolve_assessment(assessment_id, session=db.session)
    if asm_obj is None:
        raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")

    require_course_manager(actor, asm_obj.course_id, session=db.session)

    if asm_obj.first_attempt_started_at is not None:
        raise AssessmentLockedError(
            "Cấu trúc đề thi đã bị khóa (Structural Freeze - Invariant 14). "
            "Không thể import câu hỏi mới."
        )

    try:
        if not request.files or "file" not in request.files:
            raise ValidationError("Vui lòng chọn file DOCX hoặc PDF để tải lên.")

        upload = request.files["file"]
        if not upload or not upload.filename:
            raise ValidationError("Tên file không hợp lệ.")

        filename = upload.filename.lower()
        if not (filename.endswith(".docx") or filename.endswith(".pdf")):
            raise ValidationError("Chỉ hỗ trợ định dạng tài liệu Word (.docx) hoặc PDF (.pdf).")

        # Store file stream with fail-closed security pipeline
        asset = store_file_stream(
            actor=actor,
            course_id=asm_obj.course_id,
            file_stream=upload.stream,
            filename=upload.filename,
            content_type=upload.mimetype or request.content_type,
            asset_type="IMPORT_SOURCE",
            session=db.session,
        )

        # Create import job bound to target assessment
        job = create_import_job(
            actor=actor,
            course_id=asm_obj.course_id,
            file_asset_id=asset.id,
            draft_assessment_id=asm_obj.id,
            session=db.session,
        )

        # Parse and detect questions
        job = process_import_job(
            actor=actor,
            job_id=job.public_id,
            session=db.session,
        )

        # Auto-accept ready and needs-review questions
        for iq in job.questions:
            if iq.review_state in ("READY", "NEEDS_REVIEW"):
                iq.review_state = "ACCEPTED"
        db.session.commit()

        # Commit approved questions and automatically assign into draft assessment
        commit_res = commit_import_job(
            actor=actor,
            job_id=job.public_id,
            session=db.session,
        )
        imported_count = commit_res.get("imported_count", 0)

        return jsonify(
            {
                "message": f"Successfully imported and assigned {imported_count} questions.",
                "job_id": str(job.public_id),
                "imported_count": imported_count,
                "commit": commit_res,
            }
        ), 201
    except (ValidationError, DocumentParsingError):
        raise


@instructor_bp.route("/assessments/<assessment_id>/blueprint", methods=["POST"])
@instructor_required
def configure_instructor_blueprint_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Configure assessment blueprint rules."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    blueprint = configure_blueprint(actor, assessment_id, payload, session=db.session)

    return jsonify(_serialize_blueprint(blueprint)), 200


@instructor_bp.route("/assessments/<assessment_id>/blueprint/materialize", methods=["POST"])
@instructor_required
def materialize_instructor_blueprint_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Materialize candidate question pool from blueprint rules (Algorithm 05)."""
    actor = require_authenticated_actor()

    pool = materialize_blueprint_pool(actor, assessment_id, session=db.session)

    return jsonify(
        {
            "message": "Candidate pool materialized successfully.",
            "pool_count": len(pool),
        }
    ), 200


@instructor_bp.route("/assessments/<assessment_id>/attempts", methods=["GET"])
@instructor_required
def list_instructor_assessment_attempts_route(
    assessment_id: str,
) -> tuple[Response, int] | Response:
    """List all candidate attempts and objective exam results for an assessment."""
    from pwd301.services.attempt_service import list_assessment_student_results

    actor = require_authenticated_actor()
    results = list_assessment_student_results(actor, assessment_id, session=db.session)
    return jsonify(results), 200


@instructor_bp.route("/attempts/<attempt_id>/results", methods=["GET"])
@instructor_required
def get_instructor_attempt_results_route(attempt_id: str) -> tuple[Response, int] | Response:
    """Retrieve question-by-question objective exam evaluation for an attempt."""
    from pwd301.services.attempt_service import get_instructor_attempt_evaluation

    actor = require_authenticated_actor()
    evaluation = get_instructor_attempt_evaluation(actor, attempt_id, session=db.session)
    return jsonify(evaluation), 200


@instructor_bp.route("/grading", methods=["GET"])
@instructor_required
def instructor_grading_overview() -> Any:
    """Overview of pending grading attempts across courses for the instructor."""
    return jsonify({"pending_attempts": [], "total": 0}), 200


@instructor_bp.route("/assessments/<assessment_id>/grading/pending", methods=["GET"])
@instructor_required
def list_instructor_pending_grading_route(assessment_id: str) -> Any:
    """List attempts for an assessment requiring manual grading."""
    from pwd301.services.attempt_service import list_pending_grading_attempts

    actor = require_authenticated_actor()
    attempts = list_pending_grading_attempts(actor, assessment_id, session=db.session)
    return jsonify({"attempts": attempts, "total": len(attempts)}), 200


@instructor_bp.route("/attempts/<attempt_id>/grading", methods=["GET"])
@instructor_required
def get_instructor_attempt_grading_route(attempt_id: str) -> Any:
    """Retrieve detailed attempt answers for grading evaluation."""
    from pwd301.services.attempt_service import get_attempt_grading_detail

    actor = require_authenticated_actor()
    detail = get_attempt_grading_detail(actor, attempt_id, session=db.session)
    return jsonify(detail), 200


@instructor_bp.route("/attempts/<attempt_id>/grades/<attempt_question_id>", methods=["POST"])
@instructor_required
def grade_instructor_essay_route(
    attempt_id: str,
    attempt_question_id: str,
) -> Any:
    """Grade or revise manual score for an essay question."""
    from pwd301.services.attempt_service import grade_essay_question

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    awarded_points = payload.get("awarded_points")
    if awarded_points is None:
        raise ValidationError("awarded_points is required.")
    reason = payload.get("reason") or payload.get("feedback")
    result = grade_essay_question(
        actor=actor,
        attempt_id=attempt_id,
        attempt_question_id=attempt_question_id,
        awarded_points=awarded_points,
        reason=reason,
        session=db.session,
    )
    return jsonify(result), 200


@instructor_bp.route("/attempts/<attempt_id>/appeal/review", methods=["POST"])
@instructor_required
def review_instructor_attempt_appeal_route(attempt_id: str) -> tuple[Response, int] | Response:
    """Approve or reject a student attempt appeal with score adjustment."""
    import json
    from decimal import Decimal

    from pwd301.models.attempt_regrade import (
        AssessmentResult,
        AssessmentResultHistory,
    )
    from pwd301.models.notification_audit import AuditEvent
    from pwd301.models.types import utc_now
    from pwd301.services.attempt_service import _resolve_attempt

    actor = require_authenticated_actor()
    attempt = _resolve_attempt(attempt_id, session=db.session)
    if attempt is None:
        raise ResourceNotFoundError("Lượt thi không tồn tại.")

    from pwd301.services.authorization_service import require_course_manager

    # Check that instructor owns or manages the course
    if attempt.assessment and attempt.assessment.course_id:
        require_course_manager(actor, attempt.assessment.course_id, session=db.session)

    payload = request.get_json(silent=True) if request.is_json else request.form.to_dict() or {}
    decision = str(payload.get("decision", "APPROVED")).upper()
    reviewer_note = str(payload.get("reviewer_note", "")).strip()
    score_delta = payload.get("score_delta")
    new_raw_score = payload.get("new_score")

    now = utc_now()
    result = db.session.query(AssessmentResult).filter(AssessmentResult.attempt_id == attempt.id).first()

    if decision == "APPROVED":
        if result is not None and (score_delta is not None or new_raw_score is not None):
            old_score = result.raw_score
            old_pct = result.percent_score
            if new_raw_score is not None:
                new_score = Decimal(str(new_raw_score))
            else:
                new_score = old_score + Decimal(str(score_delta))
            new_score = max(Decimal("0"), min(new_score, result.max_score))
            new_pct = (new_score / result.max_score) * Decimal("100")
            passing_percent = Decimal(str(attempt.assessment.passing_percent or "50.0")) if attempt.assessment else Decimal("50.0")
            passed = new_pct >= passing_percent

            result.raw_score = new_score
            result.percent_score = new_pct
            result.passed = passed
            result.updated_at = now

            history = AssessmentResultHistory(
                attempt_id=attempt.id,
                old_score=old_score,
                new_score=new_score,
                old_percent=old_pct,
                new_percent=new_pct,
                reason_code="MANUAL",
                reason=f"Phúc khảo khảo thí: {reviewer_note}"[:1000],
                actor_user_id=actor.id,
                created_at=now,
            )
            db.session.add(history)

    audit_entry = AuditEvent(
        actor_user_id=actor.id,
        actor_roles_snapshot="INSTRUCTOR",
        action="INSTRUCTOR_APPEAL_DECISION",
        target_type="ASSESSMENT_ATTEMPT",
        target_id=attempt.id,
        reason=f"Giảng viên {decision} đơn phúc khảo: {reviewer_note}"[:1000],
        after_json=json.dumps(
            {
                "status": decision,
                "reviewer_note": reviewer_note,
                "score_delta": float(score_delta) if score_delta is not None else None,
                "new_score": float(result.raw_score) if result is not None else None,
                "reviewed_at": now.isoformat(),
            },
            ensure_ascii=False,
        ),
        created_at=now,
    )
    db.session.add(audit_entry)
    db.session.commit()

    return jsonify({"message": f"Đã {('phê duyệt' if decision == 'APPROVED' else 'từ chối')} đơn phúc khảo thành công.", "status": decision}), 200


@instructor_bp.route("/assessments/<assessment_id>/regrade", methods=["POST"])
@instructor_required
def trigger_instructor_regrade_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Trigger regrade job for an assessment from instructor view."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    result = trigger_assessment_regrade(actor, assessment_id, payload=payload, session=db.session)
    return jsonify(result), 200


@instructor_bp.route("/regrade-jobs/<job_id>", methods=["GET"])
@instructor_required
def get_instructor_regrade_job_route(job_id: str) -> tuple[Response, int] | Response:
    """Retrieve regrade job progress for instructor view."""
    actor = require_authenticated_actor()
    result = get_regrade_job_detail(actor, job_id, session=db.session)
    return jsonify(result), 200


@instructor_bp.route("/regrade-jobs/<job_id>/retry", methods=["POST"])
@instructor_required
def retry_instructor_regrade_job_route(job_id: str) -> tuple[Response, int] | Response:
    """Retry failed items in a regrade job for instructor view."""
    actor = require_authenticated_actor()
    result = retry_regrade_job(job_id, actor=actor, session=db.session)
    return jsonify(result), 200


@instructor_bp.route("/courses/<course_id>/files", methods=["POST"])
@instructor_required
def instructor_upload_course_file(course_id: str) -> tuple[Response, int] | Response:
    """Upload a new FileAsset for a managed course from Instructor Web portal."""
    import io

    from pwd301.services.exceptions import FileValidationError
    from pwd301.services.file_service import _serialize_file_asset, store_file_stream

    actor = require_authenticated_actor()
    asset_type = request.form.get("asset_type", "RESOURCE")
    title = request.form.get("title")

    if request.files and "file" in request.files:
        upload = request.files["file"]
        file_stream = upload.stream
        filename = upload.filename or "unnamed_file"
        content_type = upload.mimetype or request.content_type
    elif request.data:
        file_stream = io.BytesIO(request.get_data())
        filename = request.headers.get("X-File-Name") or "unnamed_file"
        content_type = request.content_type
    else:
        raise FileValidationError("No file content provided in request.")

    asset = store_file_stream(
        actor=actor,
        course_id=course_id,
        file_stream=file_stream,
        filename=filename,
        content_type=content_type,
        asset_type=asset_type,
        title=title,
        session=db.session,
    )
    return jsonify(_serialize_file_asset(asset)), 201


@instructor_bp.route("/courses/<course_id>/files", methods=["GET"])
@instructor_required
def instructor_list_course_files(course_id: str) -> tuple[Response, int] | Response:
    """List FileAssets belonging to a course for Instructor Web portal."""
    from pwd301.services.file_service import _serialize_file_asset, list_course_files

    actor = require_authenticated_actor()
    status = request.args.get("status", "ACTIVE")
    files = list_course_files(actor=actor, course_id=course_id, status=status, session=db.session)
    return jsonify({"items": [_serialize_file_asset(f) for f in files]}), 200


@instructor_bp.route("/files/<asset_id>", methods=["DELETE"])
@instructor_bp.route("/files/<asset_id>/trash", methods=["POST"])
@instructor_required
def instructor_trash_file(asset_id: str) -> tuple[Response, int] | Response:
    """Soft-delete a course file asset from Instructor Web portal."""
    from pwd301.services.file_service import _serialize_file_asset, trash_file_asset

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    asset = trash_file_asset(actor=actor, asset_id=asset_id, reason=reason, session=db.session)
    return jsonify(_serialize_file_asset(asset)), 200


@instructor_bp.route("/files/<asset_id>/restore", methods=["POST"])
@instructor_required
def instructor_restore_file(asset_id: str) -> tuple[Response, int] | Response:
    """Restore a soft-deleted course file asset from Instructor Web portal."""
    from pwd301.services.file_service import _serialize_file_asset, restore_file_asset

    actor = require_authenticated_actor()
    asset = restore_file_asset(actor=actor, asset_id=asset_id, session=db.session)
    return jsonify(_serialize_file_asset(asset)), 200


@instructor_bp.route("/courses/<course_id>/imports", methods=["POST"])
@instructor_required
def instructor_create_course_import(course_id: str) -> tuple[Response, int] | Response:
    """Start DOCX/PDF import job from Instructor Web portal."""
    from pwd301.services.exceptions import ValidationError
    from pwd301.services.import_service import (
        create_import_job,
        get_import_job_detail,
        process_import_job,
    )

    actor = require_authenticated_actor()
    data = request.get_json(silent=True) or request.form.to_dict()
    file_asset_id = data.get("file_asset_id")

    if (not file_asset_id) and request.files and "file" in request.files:
        from pwd301.services.file_service import store_file_stream

        upload = request.files["file"]
        asset = store_file_stream(
            actor=actor,
            course_id=course_id,
            file_stream=upload.stream,
            filename=upload.filename or "import.docx",
            content_type=upload.mimetype or request.content_type,
            asset_type="IMPORT_SOURCE",
            session=db.session,
        )
        file_asset_id = str(asset.public_id)

    if not file_asset_id:
        raise ValidationError("Field 'file_asset_id' or uploaded 'file' is required.")

    auto_process = data.get("auto_process", True)
    if isinstance(auto_process, str):
        auto_process = auto_process.lower() in ("true", "1", "yes")

    job = create_import_job(
        actor=actor,
        course_id=course_id,
        file_asset_id=file_asset_id,
        session=db.session,
    )

    if auto_process:
        job = process_import_job(
            actor=actor,
            job_id=job.public_id,
            session=db.session,
        )

    detail = get_import_job_detail(actor, job.public_id, session=db.session)
    return jsonify(detail), 202


@instructor_bp.route("/courses/<course_id>/imports", methods=["GET"])
@instructor_required
def instructor_list_course_imports(course_id: str) -> tuple[Response, int] | Response:
    """List import jobs for a course in Instructor Web portal."""
    from pwd301.models.file_import import DocumentImportJob
    from pwd301.services.import_service import _resolve_course, get_import_job_detail

    actor = require_authenticated_actor()
    course = _resolve_course(course_id, session=db.session)
    require_course_manager(actor, course.id, session=db.session)

    jobs = (
        db.session.query(DocumentImportJob)
        .filter(DocumentImportJob.course_id == course.id)
        .order_by(DocumentImportJob.created_at.desc())
        .all()
    )
    return (
        jsonify(
            {"items": [get_import_job_detail(actor, j.public_id, session=db.session) for j in jobs]}
        ),
        200,
    )


@instructor_bp.route("/imports/<job_id>", methods=["GET"])
@instructor_required
def instructor_get_import_detail(job_id: str) -> tuple[Response, int] | Response:
    """View details of an import job in Instructor Web portal."""
    from pwd301.services.import_service import get_import_job_detail

    actor = require_authenticated_actor()
    detail = get_import_job_detail(actor, job_id, session=db.session)
    return jsonify(detail), 200


@instructor_bp.route("/imports/<job_id>/questions/<temp_id>", methods=["PATCH"])
@instructor_required
def instructor_update_import_question(job_id: str, temp_id: str) -> tuple[Response, int] | Response:
    """Update question draft in Instructor Web portal."""
    from pwd301.services.import_service import (
        set_import_question_decision,
        update_import_question,
    )

    actor = require_authenticated_actor()
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    decision = data.get("decision") or data.get("action")
    if decision:
        set_import_question_decision(
            actor=actor,
            job_id=job_id,
            temp_id=temp_id,
            decision=str(decision),
            session=db.session,
        )

    updated = update_import_question(
        actor=actor,
        job_id=job_id,
        temp_id=temp_id,
        payload=data,
        session=db.session,
    )
    return jsonify(updated), 200


@instructor_bp.route("/imports/<job_id>/questions/<temp_id>/decision", methods=["POST"])
@instructor_required
def instructor_set_import_decision(job_id: str, temp_id: str) -> tuple[Response, int] | Response:
    """Accept or reject question draft in Instructor Web portal."""
    from pwd301.services.exceptions import ValidationError
    from pwd301.services.import_service import set_import_question_decision

    actor = require_authenticated_actor()
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    decision = data.get("action") or data.get("decision")
    if not decision:
        raise ValidationError("Field 'action' or 'decision' is required (ACCEPTED / REJECTED).")

    updated = set_import_question_decision(
        actor=actor,
        job_id=job_id,
        temp_id=temp_id,
        decision=str(decision),
        session=db.session,
    )
    return jsonify(updated), 200


@instructor_bp.route("/imports/<job_id>/commit", methods=["POST"])
@instructor_required
def instructor_commit_import(job_id: str) -> tuple[Response, int] | Response:
    """Commit accepted import questions to Question Bank in Instructor Web portal."""
    from pwd301.services.import_service import commit_import_job

    actor = require_authenticated_actor()
    result = commit_import_job(actor, job_id, session=db.session)
    return jsonify(result), 200


@instructor_bp.route("/imports/<job_id>/cancel", methods=["POST"])
@instructor_required
def instructor_cancel_import(job_id: str) -> tuple[Response, int] | Response:
    """Cancel import job in Instructor Web portal."""
    from pwd301.services.import_service import cancel_import_job, get_import_job_detail

    actor = require_authenticated_actor()
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = data.get("reason")
    job = cancel_import_job(actor, job_id, reason=reason, session=db.session)
    detail = get_import_job_detail(actor, job.public_id, session=db.session)
    return jsonify(detail), 200


@instructor_bp.route("/ai/questions/draft", methods=["POST"])
@instructor_required
def instructor_draft_questions_route() -> tuple[Response, int] | Response:
    """Draft assessment questions with AI for instructor courses in Web portal."""
    from pwd301.services.ai_service import draft_course_questions
    from pwd301.services.exceptions import AIValidationError
    from pwd301.services.rate_limit_service import check_ai_rate_limit

    actor = require_authenticated_actor()
    check_ai_rate_limit(actor, role=actor.primary_role, client_ip=request.remote_addr)
    data: dict[str, Any] = request.get_json(silent=True) or request.form.to_dict() or {}

    course_id = data.get("course_id")
    if not course_id:
        raise AIValidationError("Field 'course_id' is required.")

    topic = data.get("topic") or data.get("learning_objective")
    if not topic:
        raise AIValidationError("Field 'topic' or 'learning_objective' is required.")

    difficulty = data.get("difficulty", "UNDERSTAND")
    q_types = data.get("question_types")
    if q_types is None and "question_type" in data:
        q_types = [data["question_type"]]
    elif isinstance(q_types, str):
        q_types = [t.strip() for t in q_types.split(",")]

    try:
        count = int(data.get("count", 3))
    except (ValueError, TypeError):
        count = 3

    lesson_id = data.get("lesson_id")

    drafts = draft_course_questions(
        actor=actor,
        course_id=course_id,
        topic=topic,
        difficulty=difficulty,
        question_types=q_types,
        count=count,
        lesson_id=lesson_id,
        session=db.session,
    )

    return (
        jsonify(
            {
                "drafts": [d.to_dict() for d in drafts],
                "count": len(drafts),
            }
        ),
        201,
    )


@instructor_bp.route("/ai/questions/drafts", methods=["GET"])
@instructor_required
def instructor_list_drafts_route() -> tuple[Response, int] | Response:
    """List pending AI question drafts for an instructor course in Web portal."""
    from pwd301.services.ai_service import get_course_drafts
    from pwd301.services.exceptions import AIValidationError

    actor = require_authenticated_actor()
    course_id = request.args.get("course_id")
    if not course_id:
        raise AIValidationError("Query parameter 'course_id' is required.")

    review_state = request.args.get("review_state") or request.args.get("status")
    drafts = get_course_drafts(
        actor=actor,
        course_id=course_id,
        review_state=review_state,
        session=db.session,
    )
    return jsonify({"drafts": [d.to_dict() for d in drafts], "count": len(drafts)}), 200


@instructor_bp.route("/ai/questions/drafts/<draft_id>/approve", methods=["POST"])
@instructor_required
def instructor_approve_draft_route(draft_id: str) -> tuple[Response, int] | Response:
    """Approve an AI question draft and persist to Question Bank in Web portal."""
    from pwd301.services.ai_service import approve_question_draft

    actor = require_authenticated_actor()
    data: dict[str, Any] = request.get_json(silent=True) or request.form.to_dict() or {}

    draft, question = approve_question_draft(
        actor=actor,
        draft_id=draft_id,
        edits=data,
        session=db.session,
    )
    return (
        jsonify(
            {
                "message": "Question draft successfully approved and added to Question Bank.",
                "draft": draft.to_dict(),
                "question_id": str(question.public_id),
            }
        ),
        200,
    )


@instructor_bp.route("/ai/questions/drafts/<draft_id>/reject", methods=["POST"])
@instructor_required
def instructor_reject_draft_route(draft_id: str) -> tuple[Response, int] | Response:
    """Reject an AI question draft in Web portal."""
    from pwd301.services.ai_service import reject_question_draft

    actor = require_authenticated_actor()
    draft = reject_question_draft(
        actor=actor,
        draft_id=draft_id,
        session=db.session,
    )
    return (
        jsonify(
            {
                "message": "Question draft rejected.",
                "draft": draft.to_dict(),
            }
        ),
        200,
    )


@instructor_bp.route("/exams/parse-file", methods=["POST"])
@instructor_required
def instructor_parse_exam_file_route() -> tuple[Response, int] | Response:
    """Parse an uploaded exam document (.docx, .pdf, .txt) and extract raw text for the exam editor."""
    import contextlib
    import logging
    import tempfile
    from pathlib import Path
    from pwd301.services.exceptions import ValidationError
    from pwd301.services.import_service import extract_text_from_docx, extract_text_from_pdf

    _logger = logging.getLogger(__name__)
    actor = require_authenticated_actor()
    if not request.files or "file" not in request.files:
        raise ValidationError("Vui lòng chọn tệp (.docx, .pdf, .txt) để tải lên.")

    upload = request.files["file"]
    if not upload or not upload.filename:
        raise ValidationError("Tên tệp không hợp lệ.")

    filename = upload.filename
    ext = Path(filename).suffix.lower()

    if ext not in (".docx", ".pdf", ".txt", ".md"):
        raise ValidationError("Chỉ hỗ trợ các định dạng tệp: .docx, .pdf, .txt, .md")

    if ext in (".txt", ".md"):
        try:
            content = upload.stream.read().decode("utf-8", errors="replace")
            return jsonify({
                "success": True,
                "raw_text": content,
                "text": content,
                "filename": filename,
                "format": ext.lstrip("."),
            }), 200
        except Exception as err:
            raise ValidationError(f"Không thể đọc tệp văn bản: {err}") from err

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        upload.stream.seek(0)
        tmp.write(upload.stream.read())

    try:
        if ext == ".docx":
            lines = extract_text_from_docx(tmp_path)
        else:
            lines = extract_text_from_pdf(tmp_path)

        raw_text = "\n".join(lines)
        return jsonify({
            "success": True,
            "raw_text": raw_text,
            "text": raw_text,
            "filename": filename,
            "format": ext.lstrip("."),
            "lines_count": len(lines),
        }), 200
    except Exception as err:
        _logger.warning("Error parsing uploaded exam file %s: %s", filename, err)
        raise ValidationError(f"Lỗi khi trích xuất nội dung từ tệp {filename}: {err}") from err
    finally:
        with contextlib.suppress(Exception):
            if tmp_path.exists():
                tmp_path.unlink()
