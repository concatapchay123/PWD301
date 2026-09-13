from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from flask import Response, flash, jsonify, redirect, render_template, request, url_for

from pwd301.blueprints.instructor import instructor_bp
from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.models.file_import import FileAsset, LessonResource
from pwd301.models.question_bank import Question
from pwd301.services.analytics_service import (
    get_instructor_course_analytics,
    get_instructor_overview_analytics,
)
from pwd301.services.assessment_service import (
    _resolve_assessment,
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
)
from pwd301.services.attempt_service import (
    get_attempt_grading_detail,
    grade_essay_question,
    list_pending_grading_attempts,
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
    AttemptValidationError,
    CourseAlreadyExistsError,
    CourseStateViolationError,
    CourseValidationError,
    ForbiddenError,
    LessonValidationError,
    ResourceNotFoundError,
)
from pwd301.services.file_service import (
    _serialize_file_asset,
    store_file_stream,
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


def _serialize_course(c: Course) -> dict[str, Any]:
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
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
    }


@instructor_bp.route("/dashboard", methods=["GET"])
@instructor_required
def dashboard() -> Any:
    """Instructor dashboard displaying courses managed by the actor with analytics overview."""
    actor = require_authenticated_actor()
    overview = get_instructor_overview_analytics(actor, session=db.session)
    if request.accept_mimetypes.accept_html and not request.is_json:
        courses = (
            db.session.query(Course)
            .filter(Course.owner_instructor_id == actor.id, Course.deleted_at.is_(None))
            .order_by(Course.created_at.desc())
            .all()
        )
        return render_template("instructor/dashboard.html", overview=overview, courses=courses)
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
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template("instructor/courses.html", courses=courses)

    return jsonify({"courses": [_serialize_course(c) for c in courses]}), 200


@instructor_bp.route("/courses", methods=["POST"])
@instructor_required
def create_course_route() -> Any:
    """Create a new course in DRAFT status."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    try:
        course = create_course(actor, payload)
    except (CourseValidationError, CourseAlreadyExistsError, ForbiddenError) as exc:
        if not request.is_json and request.accept_mimetypes.accept_html:
            flash(f"Không thể tạo khóa học: {str(exc)}", "danger")
            return redirect(url_for("instructor.my_courses"))
        raise
    except sa.exc.IntegrityError as exc:
        db.session.rollback()
        if not request.is_json and request.accept_mimetypes.accept_html:
            flash(
                "Không thể tạo khóa học do trùng lặp mã khóa học hoặc tên khóa học đã tồn tại.",
                "danger",
            )
            return redirect(url_for("instructor.my_courses"))
        raise CourseAlreadyExistsError("Course code or title violates unique constraint.") from exc
    except Exception as exc:
        db.session.rollback()
        if not request.is_json and request.accept_mimetypes.accept_html:
            flash(f"Đã xảy ra lỗi khi tạo khóa học: {str(exc)}", "danger")
            return redirect(url_for("instructor.my_courses"))
        raise

    if not request.is_json and request.accept_mimetypes.accept_html:
        flash("Khóa học mới đã được tạo thành công dưới dạng Bản thảo (DRAFT).", "success")
        return redirect(url_for("instructor.my_courses"))

    return jsonify(_serialize_course(course)), 201


@instructor_bp.route("/courses/<course_id>", methods=["GET"])
@instructor_required
def get_course_route(course_id: str) -> Any:
    """Get detailed course information for managing."""
    actor = require_authenticated_actor()
    course = get_course_detail(actor, course_id)
    if request.accept_mimetypes.accept_html and not request.is_json:
        return redirect(url_for("instructor.manage_course_hub", course_id=course.public_id))
    return jsonify(_serialize_course(course)), 200


@instructor_bp.route("/courses/<course_id>/manage", methods=["GET"])
@instructor_required
def manage_course_hub(course_id: str) -> Any:
    """Dedicated Course Management Hub for Instructors."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)

    if request.is_json or not request.accept_mimetypes.accept_html:
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
        return jsonify(data), 200

    # 1. Lessons
    lessons = (
        db.session.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
        .order_by(Lesson.position.asc())
        .all()
    )

    # 2. File Assets & Resources
    file_assets = (
        db.session.query(FileAsset)
        .filter(FileAsset.course_id == course.id, FileAsset.deleted_at.is_(None))
        .order_by(FileAsset.created_at.desc())
        .all()
    )

    # 3. Assessments
    assessments = (
        db.session.query(Assessment)
        .filter(Assessment.course_id == course.id, Assessment.deleted_at.is_(None))
        .order_by(Assessment.created_at.desc())
        .all()
    )

    # 4. Question Bank count
    questions_count = (
        db.session.query(Question)
        .filter(
            Question.course_id == course.id,
            Question.status != "TRASH",
            Question.deleted_at.is_(None),
        )
        .count()
    )

    active_tab = request.args.get("tab", "lessons")

    return render_template(
        "instructor/course_manage.html",
        course=course,
        lessons=lessons,
        file_assets=file_assets,
        assessments=assessments,
        questions_count=questions_count,
        active_tab=active_tab,
    )


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
    ) as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Không thể cập nhật khóa học: {str(exc)}", "danger")
            return redirect(
                url_for("instructor.manage_course_hub", course_id=course_id, tab="settings")
            )
        raise
    except Exception as exc:
        db.session.rollback()
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Đã xảy ra lỗi khi cập nhật: {str(exc)}", "danger")
            return redirect(
                url_for("instructor.manage_course_hub", course_id=course_id, tab="settings")
            )
        raise

    if request.accept_mimetypes.accept_html and not request.is_json:
        flash("Cập nhật thông tin khóa học thành công.", "success")
        return redirect(
            url_for("instructor.manage_course_hub", course_id=course.public_id, tab="settings")
        )
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
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(
                "Khóa học đã được gửi tới Quản trị viên để xét duyệt xuất bản thành công.",
                "success",
            )
            return redirect(
                request.referrer
                or url_for("instructor.manage_course_hub", course_id=course.public_id)
            )
        return jsonify(_serialize_course(course)), 200
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Không thể gửi duyệt: {str(exc)}", "danger")
            return redirect(request.referrer or url_for("instructor.my_courses"))
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
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(
                "Đã rút lại yêu cầu xét duyệt. Khóa học đã quay lại trạng thái Bản thảo (DRAFT).",
                "info",
            )
            return redirect(
                request.referrer
                or url_for("instructor.manage_course_hub", course_id=course.public_id)
            )
        return jsonify(_serialize_course(course)), 200
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Không thể rút lại yêu cầu: {str(exc)}", "danger")
            return redirect(request.referrer or url_for("instructor.my_courses"))
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
                if request.accept_mimetypes.accept_html and not request.is_json:
                    flash(
                        "Khóa học đang ở trạng thái Bản thảo (DRAFT). "
                        "Bạn cần bấm 'Gửi Admin xét duyệt' trước khi xuất bản.",
                        "warning",
                    )
                    return redirect(
                        request.referrer
                        or url_for(
                            "instructor.manage_course_hub",
                            course_id=course_obj.public_id,
                            tab="settings",
                        )
                    )
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
                if request.accept_mimetypes.accept_html and not request.is_json:
                    flash(
                        "Khóa học đang chờ Quản trị viên (Admin) xét duyệt. "
                        "Vui lòng chờ phê duyệt để xuất bản.",
                        "info",
                    )
                    return redirect(
                        request.referrer
                        or url_for(
                            "instructor.manage_course_hub",
                            course_id=course_obj.public_id,
                            tab="settings",
                        )
                    )
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

        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Khóa học '{course.title}' đã được xuất bản chính thức thành công!", "success")
            return redirect(
                request.referrer
                or url_for("instructor.manage_course_hub", course_id=course.public_id)
            )
        return jsonify(_serialize_course(course)), 200
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Không thể xuất bản: {str(exc)}", "danger")
            return redirect(request.referrer or url_for("instructor.my_courses"))
        raise


@instructor_bp.route("/courses/<course_id>/trash", methods=["POST", "DELETE"])
@instructor_required
def trash_course_route(course_id: str) -> Any:
    """Soft-delete a course to TRASH."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    course = trash_course(actor, course_id, reason=reason)
    if request.accept_mimetypes.accept_html and not request.is_json:
        flash(f"Khóa học '{course.title}' đã được chuyển vào thùng rác.", "warning")
        return redirect(url_for("instructor.my_courses"))
    return jsonify(_serialize_course(course)), 200


def _serialize_lesson(les: Lesson) -> dict[str, Any]:
    return {
        "lesson_id": str(les.public_id),
        "course_id": str(les.course.public_id) if les.course else None,
        "title": les.title,
        "summary": les.summary,
        "markdown_content": les.markdown_content,
        "position": les.position,
        "estimated_duration_minutes": les.estimated_duration_minutes,
        "minimum_completion_seconds": les.minimum_completion_seconds,
        "viewed_fraction_required": float(les.viewed_fraction_required),
        "status": les.status,
        "published_at": les.published_at.isoformat() if les.published_at else None,
        "created_at": les.created_at.isoformat(),
        "updated_at": les.updated_at.isoformat(),
    }


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

    try:
        lesson = create_lesson(actor, course.id, payload)
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Bài giảng '{lesson.title}' đã được thêm thành công vào khóa học!", "success")
            return redirect(
                url_for("instructor.manage_course_hub", course_id=course.public_id, tab="lessons")
            )
        return jsonify(_serialize_lesson(lesson)), 201
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Lỗi tạo bài giảng: {str(exc)}", "danger")
            return redirect(
                url_for("instructor.manage_course_hub", course_id=course.public_id, tab="lessons")
            )
        raise


@instructor_bp.route("/courses/<course_id>/lessons/<lesson_id>/delete", methods=["POST"])
@instructor_required
def delete_lesson_from_hub_route(course_id: str, lesson_id: str) -> Any:
    """Soft-delete a lesson from the course management hub."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)
    try:
        trash_lesson(actor, lesson_id)
        flash("Bài giảng đã được xóa thành công.", "info")
    except Exception as exc:
        flash(f"Lỗi xóa bài giảng: {str(exc)}", "danger")
    return redirect(
        url_for("instructor.manage_course_hub", course_id=course.public_id, tab="lessons")
    )


@instructor_bp.route("/courses/<course_id>/files", methods=["POST"])
@instructor_required
def upload_course_file_route(course_id: str) -> Any:
    """Upload a file asset for a course or lesson with virus scanning."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)

    if "file" not in request.files:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash("Vui lòng chọn một tệp tin để tải lên.", "danger")
            return redirect(
                url_for("instructor.manage_course_hub", course_id=course.public_id, tab="materials")
            )
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "No file uploaded."}}), 400

    file_obj = request.files["file"]
    if not file_obj or not file_obj.filename:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash("Tệp tin được chọn không hợp lệ hoặc không có tên.", "danger")
            return redirect(
                url_for("instructor.manage_course_hub", course_id=course.public_id, tab="materials")
            )
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

        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(
                f"Tải lên tệp '{asset.display_name}' thành công và đã vượt qua kiểm tra an toàn!",
                "success",
            )
            return redirect(
                url_for("instructor.manage_course_hub", course_id=course.public_id, tab="materials")
            )

        return jsonify(_serialize_file_asset(asset)), 201

    except Exception as exc:
        db.session.rollback()
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Lỗi tải lên tệp: {str(exc)}", "danger")
            return redirect(
                url_for("instructor.manage_course_hub", course_id=course.public_id, tab="materials")
            )
        raise


@instructor_bp.route("/courses/<course_id>/files/<asset_id>/download", methods=["GET"])
@instructor_required
def download_course_file_route(course_id: str, asset_id: str) -> Any:
    """Download a course file asset."""
    actor = require_authenticated_actor()
    require_course_manager(actor, course_id, session=db.session)
    return redirect(url_for("api_files.download_file_api", asset_id=asset_id))


@instructor_bp.route("/courses/<course_id>/assessments", methods=["POST"])
@instructor_required
def create_course_assessment_route(course_id: str) -> Any:
    """Create a new assessment for a course."""
    actor = require_authenticated_actor()
    course = require_course_manager(actor, course_id, session=db.session)

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    try:
        asm = create_assessment(actor, course.id, payload, session=db.session)
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Đã tạo bài kiểm tra '{asm.title}' thành công!", "success")
            return redirect(
                url_for(
                    "instructor.manage_course_hub", course_id=course.public_id, tab="assessments"
                )
            )
        return jsonify(_serialize_assessment(asm)), 201
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Lỗi tạo bài kiểm tra: {str(exc)}", "danger")
            return redirect(
                url_for(
                    "instructor.manage_course_hub", course_id=course.public_id, tab="assessments"
                )
            )
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
    """Update editable lesson fields."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    lesson = update_lesson(actor, lesson_id, payload)
    return jsonify(_serialize_lesson(lesson)), 200


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
    """Soft-delete a lesson to TRASH."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    lesson = trash_lesson(actor, lesson_id, reason=reason)
    return jsonify(_serialize_lesson(lesson)), 200


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
def add_course_prerequisite_route(course_id: str) -> tuple[Response, int] | Response:
    """Add a prerequisite course dependency (with DAG cycle detection)."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    prerequisite_course_id = payload.get("prerequisite_course_id")
    if not prerequisite_course_id:
        raise CourseValidationError("prerequisite_course_id is required.")

    link = add_course_prerequisite(
        actor=actor,
        course_id=course_id,
        prerequisite_course_id=prerequisite_course_id,
        session=db.session,
    )
    target_course = link.course or _resolve_course(course_id, session=db.session)
    prereq_course = link.prerequisite_course or _resolve_course(
        prerequisite_course_id, session=db.session
    )
    return (
        jsonify(
            {
                "course_id": (str(target_course.public_id) if target_course else str(course_id)),
                "prerequisite_course_id": (
                    str(prereq_course.public_id) if prereq_course else str(prerequisite_course_id)
                ),
                "created_at": link.created_at.isoformat(),
            }
        ),
        201,
    )


@instructor_bp.route("/courses/<course_id>/prerequisites/<prereq_id>", methods=["DELETE"])
@instructor_bp.route(
    "/courses/<course_id>/prerequisites/<prereq_id>/delete", methods=["POST", "DELETE"]
)
@instructor_required
def remove_course_prerequisite_route(
    course_id: str, prereq_id: str
) -> tuple[Response, int] | Response:
    """Remove a prerequisite dependency."""
    actor = require_authenticated_actor()

    removed = remove_course_prerequisite(
        actor=actor,
        course_id=course_id,
        prerequisite_course_id=prereq_id,
        session=db.session,
    )
    return jsonify({"removed": removed}), 200


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

    if request.accept_mimetypes.accept_html and not request.is_json:
        course = require_course_manager(actor, course_id, session=db.session)
        return render_template("instructor/question_bank.html", course=course, questions=items)

    data = {
        "items": items,
        "total": total,
        "page": p,
        "per_page": pp,
        "total_pages": total_pages,
    }
    return jsonify(data), 200


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

    if not request.is_json and request.accept_mimetypes.accept_html:
        flash("Đã thêm câu hỏi mới thành công vào ngân hàng câu hỏi.", "success")
        return redirect(url_for("instructor.list_course_questions_route", course_id=course_id))

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

    data = get_assessment_detail(actor, assessment_id, session=db.session)
    if request.accept_mimetypes.accept_html and not request.is_json:
        asm_obj = _resolve_assessment(assessment_id, session=db.session)
        if asm_obj is None:
            raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")
        course = db.session.query(Course).filter(Course.id == asm_obj.course_id).first()
        if course is None:
            raise ResourceNotFoundError("Associated course not found.")
        available_questions = (
            db.session.query(Question)
            .filter(Question.course_id == course.id, Question.status == "ACTIVE")
            .order_by(Question.created_at.desc())
            .all()
        )
        return render_template(
            "instructor/assessment_builder.html",
            assessment=data,
            asm_obj=asm_obj,
            course=course,
            available_questions=available_questions,
        )
    return jsonify(data), 200


@instructor_bp.route("/assessments/<assessment_id>", methods=["PATCH", "PUT", "POST"])
@instructor_required
def update_instructor_assessment_route(assessment_id: str) -> Any:
    """Update assessment configuration."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    try:
        assessment = update_assessment(actor, assessment_id, payload, session=db.session)
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Đã lưu thông số bài thi '{assessment.title}' thành công!", "success")
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
        return jsonify(_serialize_assessment(assessment, full=False)), 200
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Lỗi cập nhật bài thi: {str(exc)}", "danger")
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
        raise


@instructor_bp.route("/assessments/<assessment_id>/publish", methods=["POST"])
@instructor_required
def publish_instructor_assessment_route(assessment_id: str) -> Any:
    """Publish assessment (DRAFT -> PUBLISHED)."""
    actor = require_authenticated_actor()

    try:
        assessment = publish_assessment(actor, assessment_id, session=db.session)
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(
                f"Đã xuất bản bài thi '{assessment.title}' thành công! "
                "Khung giờ và thời lượng đã được khóa (Timing Lock).",
                "success",
            )
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
        return jsonify(_serialize_assessment(assessment, full=False)), 200
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Lỗi xuất bản bài thi: {str(exc)}", "danger")
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
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
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(
                f"Đã hủy bài thi '{assessment.title}'. Sinh viên không thể tiếp tục vào thi.",
                "warning",
            )
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
        return jsonify(
            {
                "message": "Assessment cancelled.",
                "assessment": _serialize_assessment(assessment, full=False),
            }
        ), 200
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Lỗi hủy bài thi: {str(exc)}", "danger")
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
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
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(
                f"Đã chuyển bài thi '{assessment.title}' vào thùng rác "
                "(lưu trữ 30 ngày trước khi thanh lý).",
                "info",
            )
            course = db.session.query(Course).filter(Course.id == assessment.course_id).first()
            if course:
                return redirect(
                    url_for(
                        "instructor.manage_course_hub",
                        course_id=course.public_id,
                        tab="assessments",
                    )
                )
            return redirect(url_for("instructor.my_courses"))
        return jsonify(
            {
                "message": "Assessment moved to trash.",
                "assessment": _serialize_assessment(assessment, full=False),
            }
        ), 200
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Lỗi xóa bài thi: {str(exc)}", "danger")
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
        raise


@instructor_bp.route("/assessments/<assessment_id>/restore", methods=["POST"])
@instructor_required
def restore_instructor_assessment_route(assessment_id: str) -> Any:
    """Restore assessment from TRASH."""
    actor = require_authenticated_actor()

    try:
        assessment = restore_assessment(actor, assessment_id, session=db.session)
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(
                f"Đã khôi phục bài thi '{assessment.title}' từ thùng rác thành công!",
                "success",
            )
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
        return jsonify(
            {
                "message": "Assessment restored from trash.",
                "assessment": _serialize_assessment(assessment, full=False),
            }
        ), 200
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Lỗi khôi phục bài thi: {str(exc)}", "danger")
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
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
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash("Đã gán câu hỏi vào đề thi thành công!", "success")
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
        return jsonify(_serialize_assignment(assignment)), 201
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Lỗi gán câu hỏi: {str(exc)}", "danger")
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
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
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash("Đã gỡ câu hỏi khỏi đề thi.", "info")
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
        return jsonify({"message": "Question unassigned successfully."}), 200
    except Exception as exc:
        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Lỗi gỡ câu hỏi: {str(exc)}", "danger")
            return redirect(
                url_for(
                    "instructor.get_instructor_assessment_detail_route",
                    assessment_id=assessment_id,
                )
            )
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


@instructor_bp.route("/grading", methods=["GET"])
@instructor_required
def instructor_grading_overview() -> Any:
    """Overview of pending grading attempts across courses for the instructor."""
    actor = require_authenticated_actor()
    from pwd301.models.assessment import Assessment

    courses = (
        db.session.query(Course)
        .filter(Course.owner_instructor_id == actor.id, Course.deleted_at.is_(None))
        .all()
    )
    course_ids = [c.id for c in courses]
    assessments = (
        db.session.query(Assessment)
        .filter(Assessment.course_id.in_(course_ids), Assessment.deleted_at.is_(None))
        .all()
        if course_ids
        else []
    )
    all_pending = []
    for ass in assessments:
        att_list = list_pending_grading_attempts(actor, ass.public_id, session=db.session)
        for a in att_list:
            a["assessment_title"] = ass.title
        all_pending.extend(att_list)

    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template("instructor/grading.html", pending_attempts=all_pending)
    return jsonify({"pending_attempts": all_pending, "total": len(all_pending)}), 200


@instructor_bp.route("/assessments/<assessment_id>/grading/pending", methods=["GET"])
@instructor_required
def list_instructor_pending_grading_route(assessment_id: str) -> Any:
    """List attempts for an assessment requiring manual grading."""
    actor = require_authenticated_actor()
    attempts = list_pending_grading_attempts(actor, assessment_id, session=db.session)
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template("instructor/grading.html", pending_attempts=attempts)
    return jsonify({"attempts": attempts, "total": len(attempts)}), 200


@instructor_bp.route("/attempts/<attempt_id>/grading", methods=["GET"])
@instructor_required
def get_instructor_attempt_grading_route(attempt_id: str) -> Any:
    """Retrieve detailed attempt answers for grading evaluation."""
    actor = require_authenticated_actor()
    data = get_attempt_grading_detail(actor, attempt_id, session=db.session)
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template("instructor/grade_attempt.html", attempt=data)
    return jsonify(data), 200


@instructor_bp.route("/attempts/<attempt_id>/grades/<attempt_question_id>", methods=["POST"])
@instructor_required
def grade_instructor_essay_route(
    attempt_id: str,
    attempt_question_id: str,
) -> Any:
    """Grade or revise manual score for an essay question."""
    actor = require_authenticated_actor()
    body = request.get_json(silent=True) or request.form.to_dict() or {}
    points = body.get("awarded_points")
    if points is None:
        points = body.get("score")
    if points is None:
        raise AttemptValidationError("awarded_points (or score) is required.")

    reason = body.get("reason") or body.get("feedback")
    result = grade_essay_question(
        actor=actor,
        attempt_id=attempt_id,
        attempt_question_id=attempt_question_id,
        awarded_points=points,
        reason=reason,
        session=db.session,
    )
    if not request.is_json and request.accept_mimetypes.accept_html:
        flash("Đã lưu điểm và nhận xét cho câu hỏi thành công.", "success")
        return redirect(
            url_for("instructor.get_instructor_attempt_grading_route", attempt_id=attempt_id)
        )

    return jsonify(result), 200


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
