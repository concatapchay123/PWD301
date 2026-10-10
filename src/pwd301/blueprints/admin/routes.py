import contextlib
import json
import uuid
from typing import Any

import sqlalchemy as sa
from flask import Response, jsonify, request

from pwd301.blueprints.admin import admin_bp
from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, LearningUnit, Lesson
from pwd301.models.file_import import FileAsset, LessonResource
from pwd301.models.identity import User
from pwd301.models.types import utc_now
from pwd301.services.analytics_service import get_admin_system_overview
from pwd301.services.authorization_service import (
    _resolve_user,
    admin_required,
    require_authenticated_actor,
    verify_sensitive_action_reauth,
)
from pwd301.services.course_service import (
    change_course_status,
    flag_lesson_content,
    reassign_course_owner,
    trash_course,
)
from pwd301.services.exceptions import (
    AdminActionForbiddenError,
    ForbiddenError,
    InvalidRoleAssignmentError,
    ResourceNotFoundError,
    ValidationError,
)
from pwd301.services.file_service import _serialize_file_asset, quarantine_override
from pwd301.services.operations_service import (
    _resolve_backup,
    check_system_health,
    create_database_backup,
    end_maintenance_window,
    execute_dry_run_restore,
    is_maintenance_active,
    list_backups,
    restore_database_snapshot,
    start_maintenance_window,
    verify_backup_integrity,
)
from pwd301.services.user_service import assign_role_to_user, remove_role_from_user


def _serialize_course(c: Course) -> dict[str, Any]:
    return {
        "course_id": str(c.public_id),
        "course_code": c.course_code,
        "title": c.title,
        "status": c.status,
        "owner_instructor_id": (str(c.owner_instructor.public_id) if c.owner_instructor else None),
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
    }


def _is_api_request() -> bool:
    """Determine whether the request expects JSON (Always True in headless mode)."""
    return True


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard() -> tuple[Response, int] | Response | str:
    """Administrator dashboard overview with comprehensive system analytics."""
    actor = require_authenticated_actor()
    overview = get_admin_system_overview(actor, session=db.session)
    return jsonify(overview), 200


@admin_bp.route("/courses", methods=["GET"])
@admin_required
def admin_courses() -> tuple[Response, int] | Response | str:
    """Administrator courses management page."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền quản lý và thẩm định khóa học.")
    sess = db.session
    courses = (
        sess.query(Course)
        .filter(Course.deleted_at.is_(None))
        .order_by(Course.created_at.desc())
        .all()
    )
    pending_courses = [c for c in courses if c.status == "SUBMITTED_FOR_REVIEW"]
    return (
        jsonify(
            {
                "courses": [_serialize_course(c) for c in courses],
                "pending_count": len(pending_courses),
            }
        ),
        200,
    )


@admin_bp.route("/courses/pending", methods=["GET"])
@admin_required
def list_pending_courses() -> tuple[Response, int] | Response:
    """List all courses currently submitted for review."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định đề cương khóa học.")

    sess = db.session
    pending_courses = (
        sess.query(Course)
        .filter(
            Course.status == "SUBMITTED_FOR_REVIEW",
            Course.deleted_at.is_(None),
        )
        .order_by(Course.created_at.desc())
        .all()
    )

    data = {
        "pending_count": len(pending_courses),
        "courses": [_serialize_course(c) for c in pending_courses],
    }
    return jsonify(data), 200


@admin_bp.route("/courses/<course_id>", methods=["GET"])
@admin_required
def admin_course_detail(course_id: str) -> tuple[Response, int] | Response:
    """Retrieve full course inspection dossier including syllabus, lessons, and SLOs."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền xem hồ sơ duyệt khóa học.")
    sess = db.session
    from pwd301.services.authorization_service import _resolve_course

    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError(f"Course '{course_id}' not found.")

    lessons = sorted(course.lessons, key=lambda item: getattr(item, "position", 0))
    lessons_data = [
        {
            "lesson_id": str(item.public_id),
            "learning_unit_id": str(item.learning_unit.public_id) if item.learning_unit else None,
            "learning_unit_title": item.learning_unit.title if item.learning_unit else None,
            "title": item.title,
            "order_index": getattr(item, "order_index", getattr(item, "position", 1)),
            "position": getattr(item, "position", 1),
            "status": item.status,
            "summary": item.summary,
            "markdown_content": item.markdown_content,
            "is_flagged": bool(
                item.material_change_summary
                and item.material_change_summary.startswith("[FLAGGED]: ")
            ),
            "flag_reason": (
                item.material_change_summary.replace("[FLAGGED]: ", "")
                if (
                    item.material_change_summary
                    and item.material_change_summary.startswith("[FLAGGED]: ")
                )
                else None
            ),
            "resources": [
                {
                    "resource_id": resource.id,
                    "asset_id": str(resource.file_asset.public_id),
                    "label": resource.label or resource.file_asset.display_name,
                    "filename": resource.file_asset.original_filename
                    or resource.file_asset.display_name,
                    "mime_type": resource.file_asset.mime_type or "application/octet-stream",
                    "file_url": f"/student/files/{resource.file_asset.public_id}/download?disposition=inline",
                    "download_url": f"/student/files/{resource.file_asset.public_id}/download",
                    "resource_type": resource.resource_type,
                    "scan_status": resource.file_asset.virus_scan_status,
                    "is_clean": resource.file_asset.virus_scan_status == "CLEAN",
                    "is_video": resource.file_asset.is_video,
                }
                for resource in item.resources
                if resource.file_asset is not None
            ],
        }
        for item in lessons
        if getattr(item, "deleted_at", None) is None
    ]

    return (
        jsonify(
            {
                "course_id": str(course.public_id),
                "course_code": course.course_code,
                "title": course.title,
                "description": course.description,
                "status": course.status,
                "difficulty": course.difficulty,
                "category": course.category,
                "learning_objectives": course.learning_objectives,
                "owner_instructor_id": (
                    str(course.owner_instructor.public_id) if course.owner_instructor else None
                ),
                "owner_instructor_name": (
                    course.owner_instructor.display_name
                    if course.owner_instructor
                    else "Unassigned"
                ),
                "owner_instructor_email": (
                    course.owner_instructor.email if course.owner_instructor else None
                ),
                "lessons": lessons_data,
                "created_at": course.created_at.isoformat(),
                "updated_at": course.updated_at.isoformat(),
            }
        ),
        200,
    )


@admin_bp.route("/faculty/workload", methods=["GET"])
@admin_required
def admin_faculty_workload() -> tuple[Response, int] | Response:
    """Retrieve faculty teaching workload metrics and SLA distribution (Admin only)."""
    require_authenticated_actor()
    from pwd301.services.course_service import get_faculty_workload_metrics

    data = get_faculty_workload_metrics(session=db.session)
    return jsonify(data), 200


@admin_bp.route("/users", methods=["GET"])
@admin_required
def admin_users() -> tuple[Response, int] | Response | str:
    """Administrator users management listing with server-side filter and search."""
    actor = require_authenticated_actor()
    if not actor.is_primary_admin:
        raise ForbiddenError(
            "Chỉ Quản trị viên chính mới có quyền truy cập danh sách người dùng và ma trận phân quyền."
        )
    sess = db.session

    query = sess.query(User)

    search_term = (request.args.get("search") or "").strip()
    if search_term:
        query = query.filter(
            sa.or_(
                User.display_name.ilike(f"%{search_term}%"),
                User.email.ilike(f"%{search_term}%"),
            )
        )

    role_filter = (request.args.get("role") or "").strip().upper()
    if role_filter and role_filter != "ALL":
        from pwd301.models.identity import Role

        query = query.filter(User.roles.any(Role.code == role_filter))

    status_filter = (request.args.get("status") or "").strip().upper()
    if status_filter and status_filter != "ALL":
        query = query.filter(User.status == status_filter)

    total = query.count()
    users = query.order_by(User.created_at.desc()).all()
    return (
        jsonify(
            {
                "users": [
                    {
                        "user_id": str(u.public_id),
                        "email": u.email,
                        "display_name": u.display_name,
                        "avatar_url": u.avatar_url,
                        "status": u.status,
                        "roles": sorted(u.role_codes),
                        "admin_sub_role": u.admin_sub_role,
                        "admin_sub_role_label": u.admin_sub_role_label,
                        "is_primary_admin": u.is_primary_admin,
                        "suspended_at": u.suspended_at.isoformat() if u.suspended_at else None,
                        "created_at": u.created_at.isoformat(),
                    }
                    for u in users
                ],
                "total": total,
            }
        ),
        200,
    )


@admin_bp.route("/users/<user_id>", methods=["GET"])
@admin_required
def admin_get_user(user_id: str) -> tuple[Response, int] | Response:
    """Retrieve detailed user profile for administrators."""
    actor = require_authenticated_actor()
    if not actor.is_primary_admin:
        raise ForbiddenError(
            "Chỉ Quản trị viên chính mới có quyền truy cập danh sách người dùng và ma trận phân quyền."
        )
    sess = db.session
    target_user = _resolve_user(user_id, session=sess)
    if target_user is None:
        raise ResourceNotFoundError(f"User '{user_id}' not found.")

    return (
        jsonify(
            {
                "user_id": str(target_user.public_id),
                "email": target_user.email,
                "display_name": target_user.display_name,
                "avatar_url": target_user.avatar_url,
                "status": target_user.status,
                "roles": sorted(target_user.role_codes),
                "admin_sub_role": target_user.admin_sub_role,
                "admin_sub_role_label": target_user.admin_sub_role_label,
                "is_primary_admin": target_user.is_primary_admin,
                "auth_version": target_user.auth_version,
                "suspended_at": (
                    target_user.suspended_at.isoformat() if target_user.suspended_at else None
                ),
                "created_at": target_user.created_at.isoformat(),
                "updated_at": (
                    target_user.updated_at.isoformat() if target_user.updated_at else None
                ),
            }
        ),
        200,
    )


@admin_bp.route("/analytics/overview", methods=["GET"])
@admin_required
def admin_analytics_overview() -> tuple[Response, int] | Response:
    """Administrator system analytics overview endpoint (JWT / Web Session)."""
    actor = require_authenticated_actor()
    overview = get_admin_system_overview(actor, session=db.session)
    return jsonify(overview), 200


@admin_bp.route("/users/<user_id>/roles", methods=["POST"])
@admin_required
def manage_user_roles(user_id: str) -> tuple[Response, int] | Response:
    """Assign or revoke user roles adhering to AUTH-002 cumulative hierarchy."""
    actor = require_authenticated_actor()

    sess = db.session
    target_user = _resolve_user(user_id, session=sess)
    if target_user is None:
        raise ResourceNotFoundError(f"User '{user_id}' not found.")

    payload = request.get_json(silent=True) or {}
    action = str(payload.get("action", "")).strip().lower()
    raw_roles = payload.get("roles")
    if raw_roles and isinstance(raw_roles, list):
        role_codes = [str(r).strip().upper() for r in raw_roles if str(r).strip()]
    elif payload.get("role"):
        role_codes = [str(payload.get("role")).strip().upper()]
    else:
        role_codes = []

    reason = payload.get("reason")

    if action not in ("assign", "remove"):
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Action must be 'assign' or 'remove'.",
                    }
                }
            ),
            400,
        )

    if not role_codes:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "At least one role code must be specified.",
                    }
                }
            ),
            400,
        )

    clean_reason = str(reason or "").strip()
    if len(clean_reason) < 5:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": (
                            "Lý do thay đổi phân quyền kiểm toán bắt buộc tối thiểu 5 ký tự."
                        ),
                    }
                }
            ),
            400,
        )

    admin_sub_role = payload.get("admin_sub_role")

    try:
        updated_user = target_user
        for role_code in role_codes:
            if action == "assign":
                updated_user = assign_role_to_user(
                    user_id=target_user.id,
                    role_code=role_code,
                    assigned_by_user_id=actor.id,
                    reason=reason,
                    admin_sub_role=admin_sub_role,
                    session=sess,
                    commit=False,
                )
            else:
                updated_user = remove_role_from_user(
                    user_id=target_user.id,
                    role_code=role_code,
                    removed_by_user_id=actor.id,
                    reason=reason,
                    session=sess,
                    commit=False,
                )
        sess.commit()
        sess.expire_all()
        sess.refresh(updated_user)
    except (InvalidRoleAssignmentError, ValidationError) as exc:
        sess.rollback()
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(exc),
                    }
                }
            ),
            400,
        )
    except AdminActionForbiddenError as exc:
        sess.rollback()
        return (
            jsonify(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": str(exc),
                    }
                }
            ),
            403,
        )

    return (
        jsonify(
            {
                "user_id": str(updated_user.public_id),
                "roles": sorted(updated_user.role_codes),
                "admin_sub_role": updated_user.admin_sub_role,
                "admin_sub_role_label": updated_user.admin_sub_role_label,
                "is_primary_admin": updated_user.is_primary_admin,
                "auth_version": updated_user.auth_version,
            }
        ),
        200,
    )


@admin_bp.route("/courses/<course_id>", methods=["GET"])
@admin_required
def admin_get_course_detail(course_id: str) -> tuple[Response, int] | Response:
    """Retrieve full course inspection dossier for Admin course review."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định đề cương khóa học.")

    from pwd301.services.authorization_service import _resolve_course

    course = _resolve_course(course_id, session=db.session)
    if course is None:
        raise ResourceNotFoundError(f"Course '{course_id}' not found.")

    course_data = _serialize_course(course)
    course_data["course_id"] = str(course.public_id)

    # Attach lessons and resources
    lessons = sorted(
        [les for les in course.lessons if les.deleted_at is None],
        key=lambda item: getattr(item, "position", 0),
    )
    lessons_data = []
    for item in lessons:
        res_list = []
        for r in item.resources or []:
            fa = r.file_asset
            if fa and fa.deleted_at is None:
                res_list.append(
                    {
                        "id": str(r.public_id if hasattr(r, "public_id") else r.id),
                        "resource_id": str(r.id),
                        "asset_id": str(fa.public_id),
                        "title": r.label or fa.display_name or fa.original_filename,
                        "filename": fa.original_filename or fa.display_name,
                        "mime_type": fa.mime_type,
                        "file_url": f"/api/files/{fa.public_id}/stream?disposition=inline",
                    }
                )
        lessons_data.append(
            {
                "lesson_id": str(item.public_id),
                "title": item.title,
                "order_index": getattr(item, "order_index", getattr(item, "position", 1)),
                "position": getattr(item, "position", 1),
                "status": item.status,
                "summary": item.summary,
                "markdown_content": item.markdown_content,
                "estimated_duration_minutes": item.estimated_duration_minutes,
                "learning_unit_id": str(item.learning_unit_id) if item.learning_unit_id else None,
                "learning_unit_title": item.learning_unit.title if item.learning_unit else None,
                "resources": res_list,
                "is_flagged": bool(
                    item.material_change_summary
                    and item.material_change_summary.startswith("[FLAGGED]: ")
                ),
                "flag_reason": (
                    item.material_change_summary.replace("[FLAGGED]: ", "")
                    if (
                        item.material_change_summary
                        and item.material_change_summary.startswith("[FLAGGED]: ")
                    )
                    else None
                ),
            }
        )
    course_data["lessons"] = lessons_data
    return jsonify(course_data), 200


@admin_bp.route("/courses/<course_id>/review", methods=["POST"])
@admin_required
def review_course(course_id: str) -> Any:
    """Approve or reject a submitted course (Admin only)."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định đề cương khóa học.")

    from pwd301.services.authorization_service import _resolve_course

    course_obj = _resolve_course(course_id, session=db.session)
    if (
        course_obj is not None
        and course_obj.owner_instructor_id == actor.id
        and not actor.is_primary_admin
    ):
        raise ForbiddenError(
            "Bạn không được phép tự duyệt khóa học do chính mình làm giảng viên quản lý. Khóa học phải được Admin khác thẩm định."
        )

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    action = str(payload.get("action", "")).strip().lower()
    reason = payload.get("reason")

    if action not in ("approve", "reject"):
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Action must be 'approve' or 'reject'.",
                    }
                }
            ),
            400,
        )

    if action == "reject":
        clean_reason = str(reason or "").strip()
        if len(clean_reason) < 5:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": (
                                "Lý do từ chối đề cương kiểm toán bắt buộc tối thiểu 5 ký tự."
                            ),
                        }
                    }
                ),
                400,
            )

    target_status = "APPROVED" if action == "approve" else "DRAFT"
    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status=target_status,
        reason=reason,
    )
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/courses/<course_id>/reassign", methods=["POST"])
@admin_required
def reassign_course(course_id: str) -> tuple[Response, int] | Response:
    """Reassign course instructor ownership (Admin only)."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("TEACHING_ASSIGNMENT"):
        raise ForbiddenError("Bạn không có quyền phân công và điều chuyển giảng viên.")

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    new_instructor_id = payload.get("new_instructor_id")
    reason = payload.get("reason")

    course = reassign_course_owner(
        admin_actor=actor,
        course_id=course_id,
        new_instructor_id=new_instructor_id,
        reason=reason,
    )
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/courses/<course_id>/publish", methods=["POST"])
@admin_required
def publish_course(course_id: str) -> Any:
    """Publish an approved course (Admin only)."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền xuất bản khóa học.")

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")

    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="PUBLISHED",
        reason=reason,
    )
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/courses/<course_id>/trash", methods=["POST", "DELETE"])
@admin_required
def trash_course_route(course_id: str) -> Any:
    """Soft-delete a course to TRASH (Admin)."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền đưa khóa học vào thùng rác.")

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    verify_sensitive_action_reauth(actor, payload)
    reason = payload.get("reason")

    course = trash_course(actor=actor, course_id=course_id, reason=reason)
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/courses/<course_id>/restore", methods=["POST"])
@admin_required
def restore_course(course_id: str) -> Any:
    """Restore a course from TRASH back to ARCHIVED (Admin only)."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền khôi phục khóa học.")

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")

    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="ARCHIVED",
        reason=reason,
    )
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/files/<asset_id>/quarantine-override", methods=["POST"])
@admin_required
def override_file_quarantine(asset_id: str) -> tuple[Response, int] | Response:
    """Admin override to release a quarantined/rejected file asset."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    verify_sensitive_action_reauth(actor, payload)
    reason = payload.get("reason", "")
    asset = quarantine_override(
        admin_actor=actor, asset_id=asset_id, reason=reason, session=db.session
    )
    return jsonify(_serialize_file_asset(asset)), 200


@admin_bp.route("/notifications/broadcast", methods=["POST"])
@admin_required
def admin_broadcast_notifications() -> tuple[Response, int] | Response:
    """Admin broadcast system notification to all or role-targeted users."""
    from pwd301.services.exceptions import ValidationError
    from pwd301.services.notification_service import broadcast_system_notification

    actor = require_authenticated_actor()
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    title = data.get("title")
    body = data.get("body")
    target_role = data.get("target_role")
    category = data.get("category", "SYSTEM")

    if not title:
        raise ValidationError("Field 'title' is required.")
    if not body:
        raise ValidationError("Field 'body' is required.")

    count, idempotent_replay = broadcast_system_notification(
        actor=actor,
        title=title,
        body=body,
        target_role=target_role,
        category=category,
        idempotency_key=request.headers.get("X-Idempotency-Key"),
        session=db.session,
    )
    response_data = {"broadcasted_count": count, "idempotent_replay": idempotent_replay}
    return jsonify({"success": True, "data": response_data, **response_data}), 200


@admin_bp.route("/emails/retry-failed", methods=["POST"])
@admin_required
def admin_retry_failed_emails() -> tuple[Response, int] | Response:
    """Admin trigger retry of failed email deliveries."""
    from pwd301.services.email_service import retry_failed_emails

    actor = require_authenticated_actor()
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    try:
        max_emails = int(data.get("max_emails", 50))
    except (ValueError, TypeError):
        max_emails = 50

    count = retry_failed_emails(
        actor=actor,
        max_emails=max_emails,
        session=db.session,
    )
    response_data = {"retried_count": count}
    return jsonify({"success": True, "data": response_data, **response_data}), 200


@admin_bp.route("/audit-logs", methods=["GET"])
@admin_required
def list_audit_logs() -> tuple[Response, int] | Response | str:
    """List and filter append-only audit trail logs with pagination (Admin only)."""
    from pwd301.services.audit_service import query_audit_logs

    actor = require_authenticated_actor()

    action = request.args.get("action")
    target_type = request.args.get("target_type")
    actor_id = request.args.get("actor_id")
    target_id = request.args.get("target_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    correlation_id = request.args.get("correlation_id")

    try:
        page = int(request.args.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(request.args.get("per_page", 20))
    except (ValueError, TypeError):
        per_page = 20

    filters: dict[str, Any] = {}
    if action:
        filters["action"] = action
    if target_type:
        filters["target_type"] = target_type
    if actor_id:
        filters["actor_id"] = actor_id
    if target_id:
        filters["target_id"] = target_id
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if correlation_id:
        filters["correlation_id"] = correlation_id

    items, total, p, pp, total_pages = query_audit_logs(
        actor=actor,
        filters=filters,
        page=page,
        per_page=per_page,
        session=db.session,
    )

    return (
        jsonify(
            {
                "items": items,
                "total": total,
                "page": p,
                "per_page": pp,
                "total_pages": total_pages,
            }
        ),
        200,
    )


@admin_bp.route("/audit-logs/<audit_id>", methods=["GET"])
@admin_required
def get_audit_log_by_id(audit_id: str) -> tuple[Response, int] | Response:
    """Retrieve detailed single audit log entry by Public UUID event_id (Admin only)."""
    from pwd301.services.audit_service import get_audit_log_detail

    actor = require_authenticated_actor()
    detail = get_audit_log_detail(actor=actor, audit_id=audit_id, session=db.session)
    return jsonify(detail), 200


@admin_bp.route("/users/<user_id>/suspend", methods=["POST"])
@admin_required
def admin_suspend_user(user_id: str) -> Any:
    """Suspend a user account with mandatory fail-closed audit log (Admin only)."""
    from pwd301.services.audit_service import suspend_user_account

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    verify_sensitive_action_reauth(actor, payload)
    reason = payload.get("reason", "")

    user = suspend_user_account(
        admin_actor=actor,
        target_user_id=user_id,
        reason=reason,
        session=db.session,
    )

    return (
        jsonify(
            {
                "user_id": str(user.public_id),
                "status": user.status,
                "auth_version": user.auth_version,
                "suspended_at": user.suspended_at.isoformat() if user.suspended_at else None,
                "message": "User account suspended successfully.",
            }
        ),
        200,
    )


@admin_bp.route("/users/<user_id>/unsuspend", methods=["POST"])
@admin_required
def admin_unsuspend_user(user_id: str) -> Any:
    """Reactivate a suspended user account with mandatory fail-closed audit log (Admin only)."""
    from pwd301.services.audit_service import unsuspend_user_account

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")

    user = unsuspend_user_account(
        admin_actor=actor,
        target_user_id=user_id,
        reason=reason,
        session=db.session,
    )

    return (
        jsonify(
            {
                "user_id": str(user.public_id),
                "status": user.status,
                "auth_version": user.auth_version,
                "message": "User account reactivated successfully.",
            }
        ),
        200,
    )


@admin_bp.route("/users/<user_id>/revoke-sessions", methods=["POST"])
@admin_required
def admin_force_revoke_sessions(user_id: str) -> Any:
    """Force revocation of all active sessions and tokens for a user (Admin only)."""
    from pwd301.services.audit_service import force_revoke_user_sessions

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    verify_sensitive_action_reauth(actor, payload)
    reason = payload.get("reason")

    user = force_revoke_user_sessions(
        admin_actor=actor,
        target_user_id=user_id,
        reason=reason,
        session=db.session,
    )

    return (
        jsonify(
            {
                "user_id": str(user.public_id),
                "auth_version": user.auth_version,
                "message": "All user sessions and tokens have been revoked.",
            }
        ),
        200,
    )


# =====================================================================
# Operational Health, Maintenance & Backup Engine Endpoints (TASK-026)
# =====================================================================


@admin_bp.route("/health", methods=["GET"])
@admin_required
def admin_health() -> tuple[Response, int] | Response | str:
    """Comprehensive system operational health evaluation for administrators."""
    require_authenticated_actor()
    report = check_system_health(include_details=True, session=db.session)
    return jsonify(report), 200


@admin_bp.route("/telemetry", methods=["GET"])
@admin_required
def admin_telemetry() -> tuple[Response, int]:
    """Real-time physical server hardware telemetry endpoint for administrators."""
    require_authenticated_actor()
    from pwd301.services.operations_service import get_real_system_telemetry

    return jsonify(get_real_system_telemetry()), 200


@admin_bp.route("/backups", methods=["GET"])
@admin_required
def admin_list_backups() -> tuple[Response, int] | Response | str:
    """List historical database backups ordered by execution timestamp."""
    actor = require_authenticated_actor()
    backups = list_backups(actor, session=db.session)
    return jsonify({"items": backups, "total": len(backups)}), 200


@admin_bp.route("/backups", methods=["POST"])
@admin_required
def admin_create_backup() -> Any:
    """Initiate an on-demand database snapshot with SHA-256 integrity calculation."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    backup_type = payload.get("backup_type", "MANUAL")
    notes = payload.get("notes")

    backup = create_database_backup(
        actor=actor,
        backup_type=backup_type,
        notes=notes,
        session=db.session,
    )
    return (
        jsonify(
            {
                "backup": backup.to_dict(),
                "message": "Database backup snapshot created successfully.",
            }
        ),
        201,
    )


@admin_bp.route("/backups/<backup_id>", methods=["GET"])
@admin_required
def admin_get_backup_detail(backup_id: str) -> tuple[Response, int] | Response:
    """Retrieve detailed metadata of a specific database backup snapshot."""
    require_authenticated_actor()
    backup = _resolve_backup(backup_id, db.session)
    return jsonify({"backup": backup.to_dict()}), 200


@admin_bp.route("/backups/<backup_id>/verify", methods=["POST"])
@admin_required
def admin_verify_backup(backup_id: str) -> Any:
    """Execute cryptographic SHA-256 verification and file structure check."""
    actor = require_authenticated_actor()
    result = verify_backup_integrity(actor, backup_id, session=db.session)
    return jsonify(result), 200


@admin_bp.route("/backups/<backup_id>/restore/dry-run", methods=["POST"])
@admin_required
def admin_dry_run_restore(backup_id: str) -> Any:
    """Execute a dry-run restoration drill verifying schema compatibility with zero mutations."""
    actor = require_authenticated_actor()
    result = execute_dry_run_restore(actor, backup_id, session=db.session)
    return jsonify(result), 200


@admin_bp.route("/backups/<backup_id>/restore", methods=["POST"])
@admin_required
def admin_restore_database(backup_id: str) -> tuple[Response, int] | Response:
    """Execute controlled database restoration under strict authentication safeguards."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    confirmation_phrase = payload.get("confirmation_phrase") or payload.get("confirmation_token")
    password = payload.get("password")
    reason = payload.get("reason")

    result = restore_database_snapshot(
        actor=actor,
        backup_id=backup_id,
        confirmation_phrase=confirmation_phrase,
        password=password,
        reason=reason,
        session=db.session,
    )
    return jsonify(result), 200


@admin_bp.route("/maintenance/start", methods=["POST"])
@admin_required
def admin_start_maintenance() -> tuple[Response, int] | Response:
    """Activate system maintenance window blocking non-admin traffic with HTTP 503."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    verify_sensitive_action_reauth(actor, payload)
    reason = payload.get("reason", "Scheduled platform maintenance")
    duration = int(payload.get("estimated_duration_minutes", 60))

    window = start_maintenance_window(
        actor=actor,
        reason=reason,
        estimated_duration_minutes=duration,
        session=db.session,
    )
    return (
        jsonify(
            {
                "maintenance_window": window.to_dict(),
                "message": "Maintenance window successfully activated.",
            }
        ),
        201,
    )


@admin_bp.route("/maintenance/end", methods=["POST"])
@admin_required
def admin_end_maintenance() -> tuple[Response, int] | Response:
    """Conclude active system maintenance window and restore normal platform access."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    window_id = payload.get("window_id")

    window = end_maintenance_window(
        actor=actor,
        window_id=window_id,
        session=db.session,
    )
    return (
        jsonify(
            {
                "maintenance_window": window.to_dict(),
                "message": "Maintenance window successfully concluded.",
            }
        ),
        200,
    )


@admin_bp.route("/maintenance/status", methods=["GET"])
@admin_required
def admin_maintenance_status() -> tuple[Response, int] | Response:
    """Inspect current maintenance window status and parameters."""
    require_authenticated_actor()
    is_active, window = is_maintenance_active(session=db.session)
    return (
        jsonify(
            {
                "is_active": is_active,
                "maintenance_window": window.to_dict() if window else None,
            }
        ),
        200,
    )


# ==============================================================================
# Operations Background Jobs Telemetry & Management
# ==============================================================================


@admin_bp.route("/operations/jobs", methods=["GET"])
@admin_required
def admin_operations_jobs() -> tuple[Response, int] | Response:
    """List asynchronous background worker jobs with telemetry summary (Admin only)."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("SYSTEM_MONITORING"):
        raise ForbiddenError("Bạn không có quyền giám sát và vận hành hệ thống.")
    from pwd301.services.operations_service import list_background_jobs

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status")
    job_type = request.args.get("job_type")
    data = list_background_jobs(
        page=page,
        per_page=per_page,
        status=status,
        job_type=job_type,
        session=db.session,
    )
    return jsonify(data), 200


@admin_bp.route("/operations/jobs/<job_id>/retry", methods=["POST"])
@admin_required
def admin_retry_job(job_id: str) -> tuple[Response, int] | Response:
    """Trigger manual re-execution of a failed or stuck background job (Admin only)."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("SYSTEM_MONITORING"):
        raise ForbiddenError("Bạn không có quyền giám sát và vận hành hệ thống.")
    from pwd301.services.operations_service import retry_background_job

    data = retry_background_job(admin_actor=actor, job_identifier=job_id, session=db.session)
    return jsonify(data), 200


# ==============================================================================
# Instructor Applications Management & Review
# ==============================================================================


@admin_bp.route("/instructor-applications", methods=["GET"])
@admin_required
def admin_instructor_applications() -> tuple[Response, int] | Response | str:
    """Administrator instructor applications review queue."""
    from pwd301.models.identity import InstructorApplication
    from pwd301.services.user_service import list_instructor_applications

    actor = require_authenticated_actor()
    if not actor.has_admin_permission("INSTRUCTOR_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định hồ sơ giảng viên.")
    sess = db.session

    status_filter = request.args.get("status", "PENDING").strip().upper()
    if status_filter not in ("PENDING", "APPROVED", "REJECTED", "CANCELLED", "ALL"):
        status_filter = "PENDING"

    applications = list_instructor_applications(status=status_filter, session=sess)
    all_apps = (
        sess.query(InstructorApplication).filter(InstructorApplication.status != "CANCELLED").all()
    )
    pending_count = sum(1 for a in all_apps if a.status == "PENDING")
    approved_count = sum(1 for a in all_apps if a.status == "APPROVED")
    rejected_count = sum(1 for a in all_apps if a.status == "REJECTED")

    return (
        jsonify(
            {
                "total": len(applications),
                "pending_count": pending_count,
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "applications": [
                    {
                        "id": str(a.public_id),
                        "applicant_user_id": (
                            str(a.applicant.public_id) if a.applicant else str(a.applicant_user_id)
                        ),
                        "applicant_name": a.applicant.display_name if a.applicant else "N/A",
                        "applicant_email": a.applicant.email if a.applicant else "N/A",
                        "status": a.status,
                        "status_label": a.status_label_vi,
                        "details": a.parsed_details,
                        "reviewed_by": a.reviewed_by.display_name if a.reviewed_by else None,
                        "review_reason": a.review_reason,
                        "created_at": a.created_at.isoformat(),
                        "reviewed_at": a.reviewed_at.isoformat() if a.reviewed_at else None,
                    }
                    for a in applications
                ],
            }
        ),
        200,
    )


@admin_bp.route("/instructor-applications/<app_id>", methods=["GET"])
@admin_required
def admin_instructor_application_detail(app_id: str) -> tuple[Response, int] | Response:
    """Get detailed view of a single instructor application."""
    from pwd301.services.user_service import get_instructor_application

    actor = require_authenticated_actor()
    if not actor.has_admin_permission("INSTRUCTOR_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định hồ sơ giảng viên.")
    app_record = get_instructor_application(app_id, session=db.session)
    if app_record is None:
        raise ResourceNotFoundError(f"Đơn đăng ký #{app_id} không tồn tại.")

    return (
        jsonify(
            {
                "id": str(app_record.public_id),
                "applicant_user_id": (
                    str(app_record.applicant.public_id)
                    if app_record.applicant
                    else str(app_record.applicant_user_id)
                ),
                "applicant_name": app_record.applicant.display_name
                if app_record.applicant
                else "N/A",
                "applicant_email": app_record.applicant.email if app_record.applicant else "N/A",
                "status": app_record.status,
                "status_label": app_record.status_label_vi,
                "details": app_record.parsed_details,
                "reviewed_by": app_record.reviewed_by.display_name
                if app_record.reviewed_by
                else None,
                "review_reason": app_record.review_reason,
                "created_at": app_record.created_at.isoformat(),
                "reviewed_at": app_record.reviewed_at.isoformat()
                if app_record.reviewed_at
                else None,
            }
        ),
        200,
    )


@admin_bp.route("/instructor-applications/<app_id>/review", methods=["POST"])
@admin_required
def admin_review_instructor_application(app_id: str) -> Any:
    """Approve or reject an instructor application (Admin only)."""
    from pwd301.services.exceptions import ValidationError
    from pwd301.services.user_service import review_instructor_application

    actor = require_authenticated_actor()
    if not actor.has_admin_permission("INSTRUCTOR_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định hồ sơ giảng viên.")
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    action = str(payload.get("action", "")).strip().lower()
    reason = str(payload.get("reason", "")).strip()

    try:
        app_record = review_instructor_application(
            application_id=app_id,
            admin_user_id=actor.id,
            action=action,
            reason=reason,
            session=db.session,
        )
    except (ValidationError, ResourceNotFoundError) as exc:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}), 400

    msg = (
        f"Đã phê duyệt đơn #{app_id} thành công! "
        "Người dùng đã được cấp quyền Giảng viên (Instructor)."
        if action == "approve"
        else f"Đã từ chối đơn #{app_id}. Thông báo phản hồi đã được gửi đến học viên."
    )

    return (
        jsonify(
            {
                "message": msg,
                "application_id": str(app_record.public_id),
                "status": app_record.status,
            }
        ),
        200,
    )


@admin_bp.route("/instructor-applications/<app_id>/evidence/<filename>", methods=["GET"])
@admin_required
def admin_download_application_evidence(app_id: str, filename: str) -> Any:
    """Download attached evidence file for an instructor application."""
    from pathlib import Path

    from flask import current_app, send_file
    from werkzeug.utils import secure_filename

    from pwd301.services.user_service import get_instructor_application

    actor = require_authenticated_actor()
    if not actor.has_admin_permission("INSTRUCTOR_REVIEW"):
        raise ForbiddenError("Bạn không có quyền xem tài liệu hồ sơ giảng viên.")
    app_record = get_instructor_application(app_id, session=db.session)
    if app_record is None:
        raise ResourceNotFoundError(f"Đơn đăng ký #{app_id} không tồn tại.")

    safe_name = secure_filename(filename)
    if not safe_name:
        raise ResourceNotFoundError("Tên tệp tin không hợp lệ.")

    # Tìm original_name từ metadata
    details = app_record.parsed_details
    attached_files = details.get("attached_files", [])
    matched_meta = next(
        (
            f
            for f in attached_files
            if (
                f.get("saved_filename") == safe_name
                or f.get("file") == safe_name
                or f.get("name") == safe_name
                or secure_filename(str(f.get("saved_filename") or f.get("file") or "")) == safe_name
            )
        ),
        None,
    )
    download_name = (
        matched_meta.get("original_name") or matched_meta.get("name") or safe_name
        if matched_meta
        else safe_name
    )

    storage_root = Path(current_app.config.get("FILE_STORAGE_ROOT", "./storage")).resolve()
    candidate_dirs: list[Path] = []
    app_dir_base = storage_root / "instructor_applications"
    if app_record.applicant:
        if getattr(app_record.applicant, "public_id", None):
            candidate_dirs.append(app_dir_base / str(app_record.applicant.public_id))
        if getattr(app_record.applicant, "id", None):
            candidate_dirs.append(app_dir_base / str(app_record.applicant.id))
    if getattr(app_record, "applicant_user_id", None):
        candidate_dirs.append(app_dir_base / str(app_record.applicant_user_id))
    if getattr(app_record, "public_id", None):
        candidate_dirs.append(app_dir_base / str(app_record.public_id))
    if getattr(app_record, "id", None):
        candidate_dirs.append(app_dir_base / str(app_record.id))

    file_path: Path | None = None
    target_names = [safe_name]
    if matched_meta:
        for k in ("saved_filename", "file", "name"):
            val = secure_filename(str(matched_meta.get(k) or ""))
            if val and val not in target_names:
                target_names.append(val)

    for c_dir in candidate_dirs:
        for t_name in target_names:
            test_p = (c_dir / t_name).resolve()
            if str(test_p).startswith(str(storage_root)) and test_p.is_file():
                file_path = test_p
                break
        if file_path:
            break

    # Chống Path Traversal và kiểm tra tồn tại
    if not file_path or not str(file_path).startswith(str(storage_root)) or not file_path.is_file():
        raise ResourceNotFoundError("Tệp tin minh chứng không tồn tại hoặc đã bị xóa.")

    # Fail-Closed Malware Verification (ClamAV & Heuristic Scanner)
    from pwd301.services.scanner_service import scan_blob_file

    verdict = scan_blob_file(file_path)
    if verdict.status != "PASS":
        sig = verdict.signature_name or verdict.details or "Malware detected"
        raise ForbiddenError(
            f"Tệp tin minh chứng không an toàn hoặc chưa qua kiểm duyệt bảo mật: {sig}"
        )

    preview = request.args.get("preview", "0") in ("1", "true", "yes")
    preview_suffix = Path(download_name).suffix.lower()
    if request.args.get("format") == "text" and preview_suffix in {".docx", ".xlsx"}:
        if file_path.stat().st_size > 25_000_000:
            raise ValidationError("Tệp vượt quá giới hạn xem trước 25 MB.")
        try:
            if preview_suffix == ".docx":
                from pwd301.services.import_service import extract_text_from_docx

                extracted_text = "\n".join(extract_text_from_docx(file_path))
            else:
                import zipfile

                import openpyxl

                with zipfile.ZipFile(file_path) as archive:
                    entries = archive.infolist()
                    if len(entries) > 1_000 or sum(item.file_size for item in entries) > 50_000_000:
                        raise ValidationError("Bảng tính vượt quá giới hạn an toàn để xem trước.")
                    if any(
                        ".." in item.filename
                        or item.filename.startswith(("/", "\\"))
                        or (
                            item.file_size > 1_000_000
                            and item.file_size / max(item.compress_size, 1) > 100
                        )
                        for item in entries
                    ):
                        raise ValidationError(
                            "Bảng tính có cấu trúc nén không an toàn để xem trước."
                        )
                workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
                sheets = []
                for worksheet in workbook.worksheets[:5]:
                    rows = []
                    for row in worksheet.iter_rows(max_row=100, max_col=30, values_only=True):
                        cells = ["" if value is None else str(value) for value in row]
                        rows.append("\t".join(cells).rstrip())
                    sheets.append(f"[{worksheet.title}]\n" + "\n".join(rows))
                workbook.close()
                extracted_text = "\n\n".join(sheets)
        except Exception as err:
            if isinstance(err, ValidationError):
                raise
            raise ValidationError("Không thể trích xuất nội dung xem trước từ tài liệu.") from err
        return jsonify({"success": True, "data": {"text": extracted_text}, "error": None})

    import mimetypes

    guessed_type, _ = mimetypes.guess_type(download_name)
    content_type = guessed_type or "application/octet-stream"

    return send_file(
        str(file_path),
        as_attachment=not preview,
        download_name=download_name,
        mimetype=content_type,
    )


def _load_change_request_payload(record: CourseChangeRequest) -> dict[str, Any]:
    try:
        payload = json.loads(record.proposed_payload_json or "{}")
    except (ValueError, TypeError):
        raise ValidationError("Change request payload is invalid.") from None
    if not isinstance(payload, dict):
        raise ValidationError("Change request payload must be a JSON object.")
    if payload.get("action") == "RESOURCE_CHANGES":
        changes = payload.get("changes")
        if (
            not isinstance(changes, list)
            or not changes
            or any(not isinstance(change, dict) for change in changes)
        ):
            raise ValidationError("Yêu cầu tài liệu Lesson không hợp lệ.")
    return payload


def build_change_request_diff_summary(
    r: CourseChangeRequest,
    original_data: dict[str, Any] | None,
    payload_data: dict[str, Any],
) -> dict[str, Any]:
    """Calculate structured granular field diffs for admin review."""
    orig = original_data or {}
    prop = payload_data or {}

    if r.change_type == "COURSE_METADATA" or (r.target_type == "COURSE" and not prop.get("action")):
        field_labels = {
            "title": "Tiêu đề khóa học",
            "category": "Danh mục môn học",
            "difficulty": "Độ khó khóa học",
            "description": "Mô tả khóa học",
            "learning_objectives": "Chuẩn đầu ra (SLOs)",
            "target_audience": "Đối tượng người học",
            "completion_requirements": "Tiêu chí hoàn thành & Chứng chỉ",
            "capacity": "Sĩ số tối đa",
            "storage_quota_bytes": "Dung lượng lưu trữ",
            "thumbnail_file_asset_id": "Ảnh bìa khóa học",
        }
        changed_fields: list[str] = []
        changes: list[dict[str, Any]] = []
        unchanged_fields: list[dict[str, Any]] = []

        for field, label in field_labels.items():
            old_val = orig.get(field)
            if field in prop:
                new_val = prop.get(field)
                old_cmp = str(old_val or "").strip()
                new_cmp = str(new_val or "").strip()
                if old_cmp != new_cmp:
                    changed_fields.append(field)
                    changes.append(
                        {
                            "field": field,
                            "label": label,
                            "old_value": old_val,
                            "new_value": new_val,
                            "change_type": "MODIFIED"
                            if old_val is not None and old_cmp != ""
                            else "ADDED",
                        }
                    )
                else:
                    unchanged_fields.append(
                        {
                            "field": field,
                            "label": label,
                            "value": old_val,
                        }
                    )
            else:
                unchanged_fields.append(
                    {
                        "field": field,
                        "label": label,
                        "value": old_val,
                    }
                )
                # Populate prop with original value so preview displays complete data
                prop[field] = old_val

        return {
            "category": "COURSE_METADATA",
            "category_label": "Thông tin Khóa học",
            "changed_fields": changed_fields,
            "changes": changes,
            "unchanged_fields": unchanged_fields,
            "total_changes": len(changes),
            "unchanged_count": len(unchanged_fields),
        }

    elif r.change_type in ("LESSON_CONTENT", "LESSON_STRUCTURE") or r.target_type == "LESSON":
        field_labels = {
            "title": "Tiêu đề bài giảng",
            "summary": "Tóm tắt bài học",
            "markdown_content": "Nội dung bài học",
            "estimated_duration_minutes": "Thời lượng dự tính (phút)",
            "minimum_completion_seconds": "Thời gian hoàn thành tối thiểu (giây)",
            "viewed_fraction_required": "Tỷ lệ xem bắt buộc",
        }
        changed_fields = []
        changes = []
        unchanged_fields = []

        for field, label in field_labels.items():
            old_val = orig.get(field)
            new_val = prop.get(field)
            old_cmp = str(old_val or "").strip()
            new_cmp = str(new_val or "").strip()
            if field in prop and old_cmp != new_cmp:
                changed_fields.append(field)
                changes.append(
                    {
                        "field": field,
                        "label": label,
                        "old_value": old_val,
                        "new_value": new_val,
                        "change_type": "MODIFIED" if old_val else "ADDED",
                    }
                )
            else:
                unchanged_fields.append(
                    {
                        "field": field,
                        "label": label,
                        "value": old_val,
                    }
                )
                if field not in prop and old_val is not None:
                    prop[field] = old_val

        old_res = orig.get("resources", [])
        new_res = prop.get("resources", old_res)
        if prop.get("action") == "RESOURCE_CHANGES":
            new_res = list(old_res)
            for change in prop.get("changes", []):
                if not isinstance(change, dict):
                    continue
                if change.get("action") == "DETACH":
                    new_res = [
                        item
                        for item in new_res
                        if str(item.get("resource_id")) != str(change.get("resource_id"))
                    ]
                elif change.get("action") == "ATTACH" and not any(
                    str(item.get("asset_id")) == str(change.get("asset_id")) for item in new_res
                ):
                    new_res.append(
                        {
                            "asset_id": change.get("asset_id"),
                            "title": change.get("title") or change.get("label") or "Tệp mới",
                        }
                    )
        if old_res != new_res:
            changed_fields.append("resources")
            changes.append(
                {
                    "field": "resources",
                    "label": "Tài liệu & Video đính kèm",
                    "old_value": old_res,
                    "new_value": new_res,
                    "change_type": "MODIFIED",
                }
            )

        return {
            "category": "LESSON_CONTENT",
            "category_label": "Nội dung Bài giảng",
            "changed_fields": changed_fields,
            "changes": changes,
            "unchanged_fields": unchanged_fields,
            "total_changes": len(changes),
            "unchanged_count": len(unchanged_fields),
        }

    elif (
        r.change_type == "COURSE_VERSION_CHANGESET"
        or prop.get("action") == "COURSE_VERSION_CHANGESET"
    ):
        return {
            "category": "CURRICULUM_CHANGESET",
            "category_label": "Khung Giáo trình & Cập nhật Khóa học",
            "changed_fields": ["curriculum"],
            "changes": [
                {
                    "field": "curriculum",
                    "label": "Đợt cập nhật giáo trình khóa học",
                    "old_value": f"{len(orig.get('course_lessons', []))} bài giảng hiện tại",
                    "new_value": prop.get("version_title") or "Bản cập nhật giáo trình mới",
                    "change_type": "MODIFIED",
                }
            ],
            "unchanged_fields": [],
            "total_changes": 1,
            "unchanged_count": 0,
        }

    return {
        "category": r.change_type or "OTHER",
        "category_label": "Yêu cầu thay đổi",
        "changed_fields": [k for k in prop if k != "action"],
        "changes": [
            {
                "field": k,
                "label": k,
                "old_value": orig.get(k),
                "new_value": v,
                "change_type": "MODIFIED",
            }
            for k, v in prop.items()
            if k != "action"
        ],
        "unchanged_fields": [],
        "total_changes": len([k for k in prop if k != "action"]),
        "unchanged_count": 0,
    }


def _build_change_request_diff_payload(req: CourseChangeRequest) -> dict[str, Any]:
    """Build unified change request diff payload for single review items."""
    c = (
        req.course
        or (db.session.get(Course, req.course_id) if req.course_id else None)
        or (db.session.get(Course, req.target_id) if req.target_id else None)
    )
    payload_data = _load_change_request_payload(req)
    original_data: dict[str, Any] = {}
    if req.change_type == "COURSE_METADATA" or (
        req.target_type == "COURSE" and not payload_data.get("action")
    ):
        if c:
            original_data = {
                "id": c.id,
                "public_id": str(c.public_id),
                "course_code": c.course_code,
                "title": c.title,
                "description": c.description or "",
                "learning_objectives": c.learning_objectives or "",
                "target_audience": c.target_audience or "",
                "completion_requirements": c.completion_requirements or "",
                "category": c.category or "",
                "difficulty": c.difficulty or "",
                "capacity": c.capacity,
                "storage_quota_bytes": c.storage_quota_bytes,
                "thumbnail_file_asset_id": (
                    str(thumbnail.public_id)
                    if c.thumbnail_file_asset_id is not None
                    and (thumbnail := db.session.get(FileAsset, c.thumbnail_file_asset_id))
                    is not None
                    else None
                ),
            }
    elif req.target_type == "LESSON" or req.change_type in ("LESSON_CONTENT", "LESSON_STRUCTURE"):
        les = db.session.get(Lesson, req.target_id) if req.target_id else None
        if les:
            original_data = {
                "id": les.id,
                "public_id": str(les.public_id),
                "title": les.title,
                "summary": les.summary or "",
                "markdown_content": les.markdown_content or "",
                "estimated_duration_minutes": les.estimated_duration_minutes,
                "minimum_completion_seconds": les.minimum_completion_seconds,
                "viewed_fraction_required": float(les.viewed_fraction_required or 0.0),
            }

    diff_summary = build_change_request_diff_summary(req, original_data, payload_data)
    return {
        "success": True,
        "request_id": req.id,
        "course_id": str(c.public_id) if c else str(req.course_id),
        "course_code": c.course_code if c else None,
        "course_title": c.title if c else None,
        "change_type": req.change_type,
        "status": req.status,
        "original_data": original_data,
        "proposed_payload": payload_data,
        "diff_summary": diff_summary,
    }


@admin_bp.route("/change-requests", methods=["GET"])
@admin_required
def admin_list_change_requests() -> tuple[Response, int] | Response:
    """List all course and lesson change requests for admin review."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định yêu cầu thay đổi khóa học.")

    status_filter = request.args.get("status", "ALL").strip().upper()
    query = db.session.query(CourseChangeRequest).order_by(
        CourseChangeRequest.created_at.desc(), CourseChangeRequest.id.desc()
    )
    if status_filter == "ALL":
        # In the admin review queue, completed requests (APPROVED, REJECTED, CANCELLED)
        # must automatically disappear, including from the 'ALL' tab. The queue only holds
        # active actionable requests waiting for admin review.
        query = query.filter(CourseChangeRequest.status == "PENDING")
    elif status_filter == "PENDING":
        query = query.filter(CourseChangeRequest.status == "PENDING")
    else:
        query = query.filter(CourseChangeRequest.status == status_filter)

    records = query.all()
    # Consolidate PENDING records per course to enforce exactly 1 consolidated row per course
    pending_by_course: dict[int, list[CourseChangeRequest]] = {}
    other_records: list[CourseChangeRequest] = []
    for record in records:
        if record.status == "PENDING" and record.course_id:
            pending_by_course.setdefault(record.course_id, []).append(record)
        else:
            other_records.append(record)

    consolidated_pending: list[CourseChangeRequest] = []
    for _cid, cr_list in pending_by_course.items():
        changeset_req = None
        for r in sorted(cr_list, key=lambda x: x.id, reverse=True):
            try:
                p = json.loads(r.proposed_payload_json or "{}")
            except Exception:
                p = {}
            if r.change_type == "COURSE_VERSION_CHANGESET" or (
                isinstance(p, dict) and p.get("action") == "COURSE_VERSION_CHANGESET"
            ):
                changeset_req = r
                break
        if changeset_req:
            consolidated_pending.append(changeset_req)
        else:
            consolidated_pending.append(max(cr_list, key=lambda x: x.id))

    visible_records = consolidated_pending + other_records
    visible_records.sort(key=lambda x: x.id, reverse=True)
    results = []
    for r in visible_records:
        payload_data = _load_change_request_payload(r)

        target_title = None
        if r.change_type == "COURSE_METADATA" or (
            r.target_type == "COURSE" and not payload_data.get("action")
        ):
            c = (
                r.course
                or (db.session.get(Course, r.course_id) if r.course_id else None)
                or (db.session.get(Course, r.target_id) if r.target_id else None)
            )
            if c:
                target_title = c.title
                original_data = {
                    "id": c.id,
                    "public_id": str(c.public_id),
                    "course_code": c.course_code,
                    "title": c.title,
                    "description": c.description or "",
                    "learning_objectives": c.learning_objectives or "",
                    "target_audience": c.target_audience or "",
                    "completion_requirements": c.completion_requirements or "",
                    "category": c.category or "",
                    "difficulty": c.difficulty or "",
                    "capacity": c.capacity,
                    "storage_quota_bytes": c.storage_quota_bytes,
                    "thumbnail_file_asset_id": (
                        str(thumbnail.public_id)
                        if c.thumbnail_file_asset_id is not None
                        and (thumbnail := db.session.get(FileAsset, c.thumbnail_file_asset_id))
                        is not None
                        else None
                    ),
                }
        elif payload_data.get("action") == "UPDATE_LEARNING_UNIT":
            try:
                unit_id = uuid.UUID(str(payload_data.get("learning_unit_id")))
            except (TypeError, ValueError, AttributeError):
                unit_id = None
            unit = (
                db.session.query(LearningUnit).filter(LearningUnit.public_id == unit_id).first()
                if unit_id
                else None
            )
            if unit and unit.course_id == r.course_id:
                target_title = unit.title
                original_data = {"title": unit.title}
        elif r.target_type == "LESSON" and r.target_id:
            les = db.session.get(Lesson, r.target_id)
            if les and les.status == "PENDING_APPROVAL":
                orig = (
                    db.session.query(Lesson)
                    .filter(
                        Lesson.course_id == r.course_id,
                        Lesson.position == les.position,
                        Lesson.status.in_(["ACTIVE", "PUBLISHED"]),
                        Lesson.id != les.id,
                        Lesson.deleted_at.is_(None),
                    )
                    .first()
                )
                if orig:
                    les = orig
            staged = db.session.query(Lesson).filter(Lesson.change_request_id == r.id).first()
            if staged:
                payload_data.setdefault("title", staged.title)
                payload_data.setdefault("summary", staged.summary or "")
                payload_data.setdefault("markdown_content", staged.markdown_content or "")
                payload_data.setdefault(
                    "estimated_duration_minutes", staged.estimated_duration_minutes
                )
                payload_data.setdefault(
                    "minimum_completion_seconds", staged.minimum_completion_seconds
                )
                payload_data.setdefault(
                    "viewed_fraction_required", float(staged.viewed_fraction_required or 0.0)
                )
            if les:
                target_title = les.title
                unit_title = les.learning_unit.title if les.learning_unit else None
                original_data = {
                    "id": les.id,
                    "title": les.title,
                    "learning_unit_id": str(les.learning_unit_id) if les.learning_unit_id else None,
                    "learning_unit_title": unit_title,
                    "summary": les.summary or "",
                    "markdown_content": les.markdown_content or "",
                    "status": les.status,
                    "estimated_duration_minutes": les.estimated_duration_minutes,
                    "minimum_completion_seconds": les.minimum_completion_seconds,
                    "viewed_fraction_required": float(les.viewed_fraction_required),
                    "required_for_periods_starting_at": (
                        les.required_for_periods_starting_at.isoformat()
                        if les.required_for_periods_starting_at
                        else None
                    ),
                    "order_index": les.order_index,
                    "resources": [
                        {
                            "resource_id": resource.id,
                            "asset_id": str(resource.file_asset.public_id)
                            if resource.file_asset
                            else None,
                            "title": resource.label
                            or (
                                resource.file_asset.display_name
                                if resource.file_asset
                                else "Tệp đính kèm"
                            ),
                            "filename": resource.file_asset.original_filename
                            if resource.file_asset
                            else (resource.label or "file"),
                            "mime_type": resource.file_asset.mime_type
                            if resource.file_asset
                            else "application/octet-stream",
                            "file_url": f"/student/files/{resource.file_asset.public_id}/download"
                            if resource.file_asset
                            else None,
                        }
                        for resource in les.resources
                        if resource.file_asset is not None
                    ],
                }
                if payload_data.get("action") == "RESOURCE_CHANGES":
                    for change in payload_data.get("changes", []):
                        if not isinstance(change, dict):
                            continue
                        if change.get("action") == "ATTACH":
                            asset = db.session.get(FileAsset, change.get("asset_id"))
                            if asset and asset.course_id == r.course_id:
                                change["asset_id"] = str(asset.public_id)
                                change["title"] = change.get("label") or asset.display_name
                                change["filename"] = asset.original_filename or asset.display_name
                                change["mime_type"] = asset.mime_type
                                change["file_url"] = (
                                    f"/api/files/{asset.public_id}/{'stream' if asset.is_video else 'download'}"
                                )
                        elif change.get("action") == "DETACH":
                            resource = db.session.get(LessonResource, change.get("resource_id"))
                            if resource and resource.lesson_id == les.id:
                                change["title"] = resource.label or resource.file_asset.display_name
        elif r.target_type == "PREREQUISITE" and r.target_id:
            c = db.session.get(Course, r.target_id)
            if c:
                target_title = c.title
                original_data = {
                    "course_id": str(c.public_id),
                    "course_code": c.course_code,
                    "title": c.title,
                    "description": c.description or "",
                }
        elif (
            r.target_type == "COURSE"
            or r.change_type
            in (
                "COURSE_METADATA",
                "COURSE_UPDATE",
                "COURSE_STATUS",
                "COURSE_VERSION_CHANGESET",
                "COMPLETION_RULE",
            )
            or payload_data.get("action") == "COURSE_VERSION_CHANGESET"
        ) and (r.target_id or r.course_id):
            cid = r.target_id or r.course_id
            c = db.session.get(Course, cid)
            if c:
                target_title = (
                    payload_data.get("version_title")
                    if (
                        r.change_type == "COURSE_VERSION_CHANGESET"
                        or payload_data.get("action") == "COURSE_VERSION_CHANGESET"
                    )
                    else c.title
                ) or c.title
                original_data = {
                    "course_id": str(c.public_id),
                    "course_code": c.course_code,
                    "title": c.title,
                    "description": c.description or "",
                    "category": getattr(c, "category", "") or "",
                    "status": c.status,
                    "completion_requirements": c.completion_requirements,
                    "course_lessons": [
                        {
                            "id": cles.id,
                            "public_id": str(cles.public_id),
                            "title": cles.title,
                            "summary": cles.summary,
                            "markdown_content": cles.markdown_content,
                            "estimated_duration_minutes": cles.estimated_duration_minutes,
                            "resources": [
                                {
                                    "resource_id": cres.id,
                                    "asset_id": str(cres.file_asset.public_id)
                                    if cres.file_asset
                                    else None,
                                    "title": cres.label
                                    or (
                                        cres.file_asset.display_name
                                        if cres.file_asset
                                        else "Tệp đính kèm"
                                    ),
                                    "filename": cres.file_asset.original_filename
                                    if cres.file_asset
                                    else (cres.label or "file"),
                                    "mime_type": cres.file_asset.mime_type
                                    if cres.file_asset
                                    else "application/octet-stream",
                                    "file_url": f"/student/files/{cres.file_asset.public_id}/download"
                                    if cres.file_asset
                                    else None,
                                }
                                for cres in cles.resources
                                if cres.file_asset is not None
                            ],
                        }
                        for cles in c.lessons
                        if cles.deleted_at is None and cles.status != "TRASH"
                    ],
                }

        if not target_title and r.course:
            target_title = r.course.title

        # Check for staged lesson associated with this change request
        staged_lesson = db.session.query(Lesson).filter(Lesson.change_request_id == r.id).first()
        if staged_lesson:
            if not payload_data.get("title") and staged_lesson.title:
                payload_data["title"] = staged_lesson.title
            if not payload_data.get("summary") and staged_lesson.summary:
                payload_data["summary"] = staged_lesson.summary
            if not payload_data.get("markdown_content") and staged_lesson.markdown_content:
                payload_data["markdown_content"] = staged_lesson.markdown_content
            if (
                not payload_data.get("estimated_duration_minutes")
                and staged_lesson.estimated_duration_minutes
            ):
                dur = staged_lesson.estimated_duration_minutes
                payload_data["estimated_duration_minutes"] = dur
            if staged_lesson.learning_unit_id:
                payload_data["learning_unit_id"] = str(staged_lesson.learning_unit_id)
                if staged_lesson.learning_unit:
                    payload_data["learning_unit_title"] = staged_lesson.learning_unit.title
            if "resources" not in payload_data or not payload_data["resources"]:
                payload_data["resources"] = [
                    {
                        "resource_id": resource.id,
                        "asset_id": str(resource.file_asset.public_id)
                        if resource.file_asset
                        else None,
                        "title": resource.label
                        or (
                            resource.file_asset.display_name
                            if resource.file_asset
                            else "Tệp đính kèm"
                        ),
                        "filename": resource.file_asset.original_filename
                        if resource.file_asset
                        else (resource.label or "file"),
                        "mime_type": resource.file_asset.mime_type
                        if resource.file_asset
                        else "application/octet-stream",
                        "file_url": (
                            f"/student/files/{resource.file_asset.public_id}/download?disposition=inline"
                            if resource.file_asset
                            else None
                        ),
                    }
                    for resource in staged_lesson.resources
                    if resource.file_asset is not None
                ]

        # Ensure course_lessons is populated for any change request associated with a course
        course_obj = r.course or (db.session.get(Course, r.course_id) if r.course_id else None)
        course_lessons_data = []
        if course_obj:
            from pwd301.blueprints.instructor.routes import _extract_video_urls_from_markdown

            active_lessons = [
                les
                for les in course_obj.lessons
                if les.deleted_at is None and les.status != "TRASH"
            ]
            active_lessons.sort(key=lambda x: (x.position or 0, x.id))
            for cles in active_lessons:
                course_lessons_data.append(
                    {
                        "id": cles.id,
                        "public_id": str(cles.public_id),
                        "title": cles.title,
                        "learning_unit_id": str(cles.learning_unit.public_id)
                        if cles.learning_unit
                        else None,
                        "learning_unit_title": cles.learning_unit.title
                        if cles.learning_unit
                        else None,
                        "summary": cles.summary,
                        "markdown_content": cles.markdown_content,
                        "estimated_duration_minutes": cles.estimated_duration_minutes,
                        "position": cles.position,
                        "status": cles.status,
                        "video_urls": _extract_video_urls_from_markdown(cles.markdown_content)
                        if cles.markdown_content
                        else [],
                        "resources": [
                            {
                                "resource_id": cres.id,
                                "asset_id": str(cres.file_asset.public_id)
                                if cres.file_asset
                                else None,
                                "title": cres.label
                                or (
                                    cres.file_asset.display_name
                                    if cres.file_asset
                                    else "Tệp đính kèm"
                                ),
                                "filename": cres.file_asset.original_filename
                                if cres.file_asset
                                else (cres.label or "file"),
                                "mime_type": cres.file_asset.mime_type
                                if cres.file_asset
                                else "application/octet-stream",
                                "file_url": f"/student/files/{cres.file_asset.public_id}/download?disposition=inline"
                                if cres.file_asset
                                else None,
                                "is_video": (
                                    (cres.file_asset.mime_type or "").lower().startswith("video/")
                                    or (cres.file_asset.original_filename or "")
                                    .lower()
                                    .endswith((".mp4", ".webm", ".mkv", ".mov"))
                                )
                                if cres.file_asset
                                else False,
                            }
                            for cres in cles.resources
                            if cres.file_asset is not None
                        ],
                    }
                )

        lesson_detail_data = None
        if staged_lesson:
            lesson_detail_data = {
                "id": staged_lesson.id,
                "public_id": str(staged_lesson.public_id),
                "title": staged_lesson.title,
                "summary": staged_lesson.summary,
                "markdown_content": staged_lesson.markdown_content,
                "estimated_duration_minutes": staged_lesson.estimated_duration_minutes,
                "resources": payload_data.get("resources", []),
            }

        results.append(
            {
                "id": r.id,
                "course_id": str(r.course.public_id) if r.course else str(r.course_id),
                "course_code": r.course.course_code if r.course else None,
                "course_title": r.course.title if r.course else None,
                "learning_unit_id": (
                    original_data.get("learning_unit_id")
                    if isinstance(original_data, dict) and original_data.get("learning_unit_id")
                    else (
                        payload_data.get("learning_unit_id")
                        if isinstance(payload_data, dict)
                        else None
                    )
                ),
                "learning_unit_title": (
                    original_data.get("learning_unit_title")
                    if isinstance(original_data, dict) and original_data.get("learning_unit_title")
                    else (
                        payload_data.get("learning_unit_title")
                        if isinstance(payload_data, dict)
                        else None
                    )
                ),
                "requested_by_id": str(r.requested_by.public_id) if r.requested_by else None,
                "requested_by_name": r.requested_by.display_name if r.requested_by else None,
                "change_type": r.change_type,
                "target_type": r.target_type,
                "target_id": r.target_id,
                "target_title": target_title,
                "original_data": original_data,
                "proposed_payload": payload_data,
                "diff_summary": build_change_request_diff_summary(r, original_data, payload_data),
                "course_lessons": course_lessons_data,
                "lesson": lesson_detail_data,
                "status": r.status,
                "review_reason": r.review_reason,
                "created_at": r.created_at.isoformat(),
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            }
        )

    pending_count = sum(1 for r in visible_records if r.status == "PENDING")
    return (
        jsonify({"change_requests": results, "items": results, "pending_count": pending_count}),
        200,
    )


@admin_bp.route("/change-requests/<int:req_id>/review", methods=["POST"])
@admin_required
def admin_review_change_request(req_id: int) -> tuple[Response, int] | Response:
    """Approve or reject a course/lesson change request (Admin only)."""
    from pwd301.services.enrollment_service import add_course_prerequisite
    from pwd301.services.lesson_service import (
        lock_course_change_request,
        record_change_request_review,
        trash_lesson,
        update_lesson,
    )
    from pwd301.services.notification_service import dispatch_notification

    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định yêu cầu thay đổi khóa học.")

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = str(payload.get("reason", "")).strip()
    raw_action = (
        str(payload.get("action") or payload.get("decision") or payload.get("status") or "")
        .strip()
        .lower()
    )
    if raw_action in ("approve", "approved"):
        action = "approve"
    elif raw_action in ("reject", "rejected"):
        action = "reject"
    else:
        raise ValidationError("Action must be 'approve' or 'reject'.")

    if action == "reject" and len(reason) < 5:
        raise ValidationError("Lý do từ chối yêu cầu bắt buộc tối thiểu 5 ký tự.")

    req_record = lock_course_change_request(db.session, req_id)

    if req_record.status != "PENDING":
        raise ValidationError(f"Change request is already in '{req_record.status}' status.")

    if req_record.requested_by_user_id == actor.id and not actor.is_primary_admin:
        raise ForbiddenError(
            "Bạn không được phép tự duyệt yêu cầu thay đổi do chính mình tạo ra. Yêu cầu phải được Admin khác thẩm định."
        )

    if req_record.target_type == "LESSON":
        sibling_query = db.session.query(CourseChangeRequest).filter_by(
            requested_by_user_id=req_record.requested_by_user_id,
            target_type="LESSON",
            target_id=req_record.target_id,
            change_type=req_record.change_type,
            status="PENDING",
        )
        newer = sibling_query.filter(CourseChangeRequest.id > req_record.id).first()
        if newer is not None:
            raise ValidationError("Yêu cầu này đã được thay thế bởi bản sửa mới hơn.")
    else:
        sibling_query = None

    now = utc_now()
    p_data = _load_change_request_payload(req_record)
    reviewed_in_service = False

    target_lesson = (
        db.session.get(Lesson, req_record.target_id)
        if req_record.target_type == "LESSON" and req_record.target_id
        else None
    )
    if target_lesson is not None and target_lesson.course_id != req_record.course_id:
        raise ValidationError("Lesson does not belong to the reviewed course.")
    if req_record.target_type == "LESSON" and target_lesson is not None:
        lesson_title = p_data.get("title") or (
            target_lesson.title if target_lesson else "được đề xuất"
        )
        subject = f"Lesson '{lesson_title}'"
    elif req_record.change_type == "PREREQUISITE":
        subject = f"Điều kiện tiên quyết của khóa học '{req_record.course.title}'"
    elif (
        req_record.change_type == "COURSE_VERSION_CHANGESET"
        or p_data.get("action") == "COURSE_VERSION_CHANGESET"
    ):
        subject = f"Đợt cập nhật khóa học '{req_record.course.title}'"
    else:
        subject = f"Khóa học '{req_record.course.title}'"
    action_url = f"#/instructor/courses/{req_record.course.public_id}/manage"

    if action == "approve":
        course_owner = (
            req_record.course.owner_instructor
            or (
                db.session.get(User, req_record.course.owner_instructor_id)
                if req_record.course and req_record.course.owner_instructor_id
                else None
            )
            or req_record.requested_by
            or actor
        )
        if p_data.get("action") == "UPDATE_LEARNING_UNIT":
            from pwd301.services.lesson_service import update_learning_unit

            try:
                public_unit_id = uuid.UUID(str(p_data.get("learning_unit_id")))
            except (TypeError, ValueError, AttributeError):
                raise ValidationError("Mã Bài học trong yêu cầu không hợp lệ.") from None
            unit = (
                db.session.query(LearningUnit)
                .filter(
                    LearningUnit.public_id == public_unit_id,
                    LearningUnit.course_id == req_record.course_id,
                    LearningUnit.deleted_at.is_(None),
                )
                .first()
            )
            if unit is None:
                raise ValidationError("Bài học không thuộc khóa học được yêu cầu xét duyệt.")
            update_learning_unit(
                course_owner,
                public_unit_id,
                {"title": p_data.get("title")},
                session=db.session,
            )
            msg = f"Đã phê duyệt tên Bài học #{req_record.id}."

        elif p_data.get("action") == "RESOURCE_CHANGES":
            from pwd301.services.file_service import (
                attach_resource_to_lesson,
                detach_resource_from_lesson,
            )

            if target_lesson is None or target_lesson.course_id != req_record.course_id:
                raise ValidationError("Lesson không thuộc khóa học được xét duyệt.")
            changes = p_data.get("changes")
            if not isinstance(changes, list) or not changes:
                raise ValidationError("Yêu cầu tài liệu Lesson không hợp lệ.")
            if any(not isinstance(change, dict) for change in changes):
                raise ValidationError("Yêu cầu tài liệu Lesson không hợp lệ.")
            lessons_to_update = [target_lesson]
            if target_lesson.status == "HISTORICAL":
                newer_active = (
                    db.session.query(Lesson)
                    .filter(
                        Lesson.course_id == target_lesson.course_id,
                        Lesson.position == target_lesson.position,
                        Lesson.status.in_(["ACTIVE", "PUBLISHED"]),
                        Lesson.deleted_at.is_(None),
                        Lesson.id != target_lesson.id,
                    )
                    .first()
                )
                if newer_active and newer_active not in lessons_to_update:
                    lessons_to_update.append(newer_active)

            for change in sorted(changes, key=lambda item: item.get("action") != "DETACH"):
                if change.get("action") == "DETACH":
                    res_id = change.get("resource_id")
                    original_resource = db.session.get(LessonResource, res_id)
                    if original_resource is None or original_resource.lesson_id != target_lesson.id:
                        raise ValidationError("Resource does not belong to the reviewed lesson.")
                    for l_target in lessons_to_update:
                        resource = (
                            db.session.get(LessonResource, res_id)
                            if l_target.id == target_lesson.id
                            else None
                        )
                        if resource is not None and resource.lesson_id == l_target.id:
                            detach_resource_from_lesson(
                                course_owner,
                                l_target.id,
                                resource.id,
                                session=db.session,
                                commit=False,
                            )
                        elif l_target.id != target_lesson.id:
                            orig_res = original_resource
                            if orig_res:
                                matching_res = (
                                    db.session.query(LessonResource)
                                    .filter(
                                        LessonResource.lesson_id == l_target.id,
                                        LessonResource.file_asset_id == orig_res.file_asset_id,
                                    )
                                    .first()
                                )
                                if matching_res:
                                    detach_resource_from_lesson(
                                        course_owner,
                                        l_target.id,
                                        matching_res.id,
                                        session=db.session,
                                        commit=False,
                                    )
                elif change.get("action") == "ATTACH":
                    asset = db.session.get(FileAsset, change.get("asset_id"))
                    if (
                        asset is None
                        or asset.course_id != req_record.course_id
                        or asset.asset_type != "RESOURCE"
                        or asset.status != "ACTIVE"
                        or asset.deleted_at is not None
                    ):
                        raise ValidationError("Tệp đề xuất không còn hợp lệ hoặc chưa quét sạch.")
                    for l_target in lessons_to_update:
                        attach_resource_to_lesson(
                            course_owner,
                            l_target.id,
                            asset.id,
                            label=change.get("label"),
                            session=db.session,
                            commit=False,
                        )
                else:
                    raise ValidationError("Thao tác tài liệu Lesson không hợp lệ.")
            msg = f"Đã phê duyệt thay đổi tài liệu Lesson #{req_record.id}."

        elif req_record.change_type == "LESSON_STRUCTURE" and p_data.get("action") == "DELETE":
            lesson_id = req_record.target_id or p_data.get("lesson_id")
            if lesson_id:
                trash_lesson(
                    course_owner,
                    lesson_id,
                    reason=reason or "Admin phê duyệt yêu cầu xóa",
                    session=db.session,
                )
            msg = f"Đã phê duyệt yêu cầu xóa bài giảng #{req_record.target_id}."

        elif (
            req_record.change_type == "LESSON_STRUCTURE"
            and p_data.get("action") == "DELETE_LEARNING_UNIT"
        ):
            from pwd301.services.lesson_service import delete_learning_unit

            target_unit_id = p_data.get("learning_unit_id")
            if target_unit_id:
                delete_learning_unit(course_owner, target_unit_id, session=db.session)
            msg = f"Đã phê duyệt yêu cầu xóa chương mục #{target_unit_id}."

        elif (
            req_record.change_type == "COURSE_VERSION_CHANGESET"
            or p_data.get("action") == "COURSE_VERSION_CHANGESET"
        ):
            from pwd301.services.lesson_service import approve_course_change_request

            approve_course_change_request(
                actor, req_record.id, review_reason=reason, session=db.session
            )
            reviewed_in_service = True
            msg = f"Đã phê duyệt đợt cập nhật khóa học #{req_record.course_id}."

        elif (
            req_record.change_type == "LESSON_STRUCTURE"
            and p_data.get("action") == "REORDER_LESSONS"
        ):
            from pwd301.services.lesson_service import reorder_lessons

            ordered_ids = p_data.get("ordered_lesson_ids") or []
            if ordered_ids:
                reorder_lessons(course_owner, req_record.course_id, ordered_ids, session=db.session)
            msg = f"Đã phê duyệt sắp xếp lại bài giảng khóa học #{req_record.course_id}."

        elif req_record.change_type == "COMPLETION_RULE":
            from pwd301.services.completion_service import set_course_completion_rule

            set_course_completion_rule(
                actor=course_owner,
                course_id=req_record.course_id,
                payload=p_data,
                session=db.session,
            )
            msg = f"Đã phê duyệt quy tắc hoàn thành khóa học #{req_record.course_id}."

        elif (
            req_record.change_type == "LESSON_STRUCTURE"
            and p_data.get("action") == "CREATE_LEARNING_UNIT"
        ):
            from pwd301.services.lesson_service import create_learning_unit

            create_learning_unit(course_owner, req_record.course_id, p_data, session=db.session)
            msg = f"Đã phê duyệt tạo chương mục mới cho khóa học #{req_record.course_id}."

        elif (
            req_record.change_type == "LESSON_STRUCTURE"
            and p_data.get("action") == "REORDER_LEARNING_UNITS"
        ):
            from pwd301.services.lesson_service import reorder_learning_units

            unit_ids = p_data.get("unit_ids") or []
            if unit_ids:
                reorder_learning_units(
                    course_owner, req_record.course_id, unit_ids, session=db.session
                )
            msg = f"Đã phê duyệt sắp xếp lại chương mục cho khóa học #{req_record.course_id}."

        elif req_record.change_type in ("LESSON_CONTENT", "LESSON_STRUCTURE"):
            staged = (
                db.session.query(Lesson).filter(Lesson.change_request_id == req_record.id).first()
            )
            if staged:
                from pwd301.services.lesson_service import approve_course_change_request

                approve_course_change_request(
                    actor, req_record.id, review_reason=reason, session=db.session
                )
                reviewed_in_service = True
            else:
                lesson_id = req_record.target_id
                if lesson_id:
                    update_data = {
                        k: v
                        for k, v in p_data.items()
                        if k
                        in (
                            "title",
                            "summary",
                            "markdown_content",
                            "estimated_duration_minutes",
                            "minimum_completion_seconds",
                            "viewed_fraction_required",
                            "required_for_periods_starting_at",
                            "status",
                        )
                    }
                    if update_data:
                        update_lesson(course_owner, lesson_id, update_data, session=db.session)
            msg = f"Đã phê duyệt thay đổi nội dung bài giảng #{req_record.target_id}."

        elif req_record.change_type == "PREREQUISITE":
            if p_data.get("action") == "REMOVE_PREREQUISITE":
                from pwd301.services.enrollment_service import remove_course_prerequisite

                remove_course_prerequisite(
                    actor=course_owner,
                    course_id=req_record.course_id,
                    prerequisite_course_id=req_record.target_id,
                    session=db.session,
                )
                msg = f"Đã phê duyệt xóa môn tiên quyết #{req_record.target_id}."
            else:
                add_course_prerequisite(
                    actor=course_owner,
                    course_id=req_record.course_id,
                    prerequisite_course_id=req_record.target_id,
                    session=db.session,
                )
                msg = f"Đã phê duyệt thiết lập môn tiên quyết #{req_record.target_id}."

        elif req_record.change_type == "COURSE_METADATA":
            from pwd301.services.course_service import update_course

            update_course(
                course_owner,
                req_record.course_id,
                p_data,
                session=db.session,
                is_approved_review=True,
            )
            msg = f"Đã phê duyệt cập nhật thông tin khóa học #{req_record.course_id}."

        else:
            msg = f"Đã phê duyệt yêu cầu thay đổi #{req_record.id}."

        req_record.status = "APPROVED"
        req_record.reviewed_by_user_id = actor.id
        req_record.review_reason = reason or "Admin đã phê duyệt"
        req_record.reviewed_at = now
        req_record.applied_at = now
        db.session.flush()

        if req_record.requested_by:
            with contextlib.suppress(Exception):
                dispatch_notification(
                    recipient_user=req_record.requested_by,
                    event_type="COURSE_CHANGE_APPROVED",
                    title=f"{subject} đã được phê duyệt",
                    body=f"Quản trị viên đã phê duyệt thay đổi đối với {subject}.",
                    action_url=action_url,
                    category="COURSE",
                    target_role="INSTRUCTOR",
                    event_key=uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"pwd301:course-change:{req_record.id}:COURSE_CHANGE_APPROVED:{req_record.requested_by_user_id}",
                    ),
                    session=db.session,
                )

    else:
        staged = db.session.query(Lesson).filter(Lesson.change_request_id == req_record.id).first()
        if staged:
            from pwd301.services.lesson_service import reject_course_change_request

            reject_course_change_request(
                actor, req_record.id, review_reason=reason, session=db.session
            )
            reviewed_in_service = True

        req_record.status = "REJECTED"
        req_record.reviewed_by_user_id = actor.id
        req_record.review_reason = reason or "Admin từ chối yêu cầu thay đổi"
        req_record.reviewed_at = now
        db.session.flush()

        if req_record.requested_by:
            with contextlib.suppress(Exception):
                dispatch_notification(
                    recipient_user=req_record.requested_by,
                    event_type="COURSE_CHANGE_REJECTED",
                    title=f"{subject} cần chỉnh sửa",
                    body=(
                        f"Thay đổi đối với {subject} chưa được duyệt. "
                        f"Lý do: {reason or 'Chưa nêu lý do'}."
                    ),
                    action_url=action_url,
                    category="COURSE",
                    target_role="INSTRUCTOR",
                    event_key=uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"pwd301:course-change:{req_record.id}:COURSE_CHANGE_REJECTED:{req_record.requested_by_user_id}",
                    ),
                    session=db.session,
                )
        msg = f"Đã từ chối yêu cầu thay đổi #{req_record.id}."

    if sibling_query is not None:
        for superseded in sibling_query.filter(CourseChangeRequest.id < req_record.id).all():
            superseded.status = "REJECTED"
            superseded.reviewed_by_user_id = actor.id
            superseded.review_reason = f"Đã được thay thế bởi yêu cầu #{req_record.id}"
            superseded.reviewed_at = now

    if not reviewed_in_service:
        record_change_request_review(db.session, actor, req_record, req_record.status)
    db.session.commit()
    return jsonify({"status": req_record.status, "message": msg}), 200


@admin_bp.route("/change-requests/<int:req_id>/diff", methods=["GET"])
@admin_bp.route("/course-changes/<int:req_id>/diff", methods=["GET"])
@admin_bp.route("/courses/<course_id>/changeset/diff", methods=["GET"])
@admin_required
def get_course_changeset_diff_route(
    req_id: int | None = None, course_id: str | None = None
) -> tuple[Response, int] | Response:
    """Get full Before vs. After diff of a course version changeset or single change request."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định yêu cầu thay đổi khóa học.")

    target = req_id if req_id is not None else course_id
    if target is None:
        return jsonify({"error": "Change request target not specified"}), 400

    if req_id is not None:
        req = db.session.get(CourseChangeRequest, req_id)
        if req is not None and req.change_type not in ("COURSE_VERSION_CHANGESET",):
            try:
                p_payload = json.loads(req.proposed_payload_json or "{}")
            except Exception:
                p_payload = {}
            if (
                not isinstance(p_payload, dict)
                or p_payload.get("action") != "COURSE_VERSION_CHANGESET"
            ):
                diff_data = _build_change_request_diff_payload(req)
                return jsonify(diff_data), 200

    from pwd301.services.lesson_service import get_course_changeset_diff

    diff_data = get_course_changeset_diff(actor, target, session=db.session)
    return jsonify(diff_data), 200


@admin_bp.route("/course-changes/<int:req_id>/approve", methods=["POST"])
@admin_bp.route("/courses/<course_id>/changeset/approve", methods=["POST"])
@admin_required
def approve_course_changeset_route(
    req_id: int | None = None, course_id: str | None = None
) -> tuple[Response, int] | Response:
    """Atomically approve and apply a course version changeset."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định yêu cầu thay đổi khóa học.")

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = str(payload.get("reason", "")).strip()

    target_req = None
    if req_id is not None:
        target_req = db.session.get(CourseChangeRequest, req_id)
    elif course_id:
        from pwd301.services.authorization_service import _resolve_course

        course = _resolve_course(course_id, session=db.session)
        if course:
            target_req = (
                db.session.query(CourseChangeRequest)
                .filter(
                    CourseChangeRequest.course_id == course.id,
                    CourseChangeRequest.status == "PENDING",
                    CourseChangeRequest.target_type == "COURSE",
                )
                .order_by(CourseChangeRequest.id.desc())
                .first()
            )

    if target_req is None:
        raise ResourceNotFoundError("Yêu cầu thay đổi không tồn tại.")

    if target_req.status != "PENDING":
        raise ValidationError(
            f"Yêu cầu đang ở trạng thái '{target_req.status}', không thể phê duyệt."
        )

    if target_req.requested_by_user_id == actor.id and not actor.is_primary_admin:
        raise ForbiddenError("Bạn không được phép tự duyệt yêu cầu thay đổi do chính mình tạo ra.")

    from pwd301.services.lesson_service import approve_course_change_request

    approved_req = approve_course_change_request(
        actor,
        target_req.id,
        review_reason=reason or "Quản trị viên đã phê duyệt đợt cập nhật.",
        session=db.session,
    )
    db.session.commit()
    return (
        jsonify(
            {
                "success": True,
                "status": "APPROVED",
                "message": "Đã phê duyệt và áp dụng đợt cập nhật thành công.",
                "change_request_id": approved_req.id,
            }
        ),
        200,
    )


@admin_bp.route("/course-changes/<int:req_id>/reject", methods=["POST"])
@admin_bp.route("/courses/<course_id>/changeset/reject", methods=["POST"])
@admin_required
def reject_course_changeset_route(
    req_id: int | None = None, course_id: str | None = None
) -> tuple[Response, int] | Response:
    """Reject a course version changeset with mandatory reason."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định yêu cầu thay đổi khóa học.")

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = str(payload.get("reason", "")).strip()
    if len(reason) < 5:
        raise ValidationError("Lý do từ chối yêu cầu bắt buộc tối thiểu 5 ký tự.")

    target_req = None
    if req_id is not None:
        target_req = db.session.get(CourseChangeRequest, req_id)
    elif course_id:
        from pwd301.services.authorization_service import _resolve_course

        course = _resolve_course(course_id, session=db.session)
        if course:
            target_req = (
                db.session.query(CourseChangeRequest)
                .filter(
                    CourseChangeRequest.course_id == course.id,
                    CourseChangeRequest.status == "PENDING",
                    CourseChangeRequest.target_type == "COURSE",
                )
                .order_by(CourseChangeRequest.id.desc())
                .first()
            )

    if target_req is None:
        raise ResourceNotFoundError("Yêu cầu thay đổi không tồn tại.")

    if target_req.status != "PENDING":
        raise ValidationError(
            f"Yêu cầu đang ở trạng thái '{target_req.status}', không thể từ chối."
        )

    from pwd301.models.notification_audit import AuditEvent
    from pwd301.services.notification_service import dispatch_notification

    course = target_req.course
    if course is None or course.public_id is None:
        raise ResourceNotFoundError("Khóa học của yêu cầu thay đổi không tồn tại.")

    course_public_id = str(course.public_id)
    course_code = course.course_code or course_public_id
    now = utc_now()
    target_req.status = "REJECTED"
    target_req.reviewed_by_user_id = actor.id
    target_req.review_reason = reason
    target_req.reviewed_at = now

    actor_roles = ",".join(sorted(actor.role_codes)) if actor and actor.role_codes else "ADMIN"
    audit = AuditEvent(
        actor_user_id=actor.id,
        actor_roles_snapshot=actor_roles,
        action="COURSE_CHANGESET_REJECTED",
        target_type="COURSE",
        target_id=target_req.course_id,
        reason=reason,
        performed_as_admin=True,
        after_json=json.dumps(
            {
                "course_id": course_public_id,
                "change_request_id": target_req.id,
                "reason": reason,
            },
            ensure_ascii=False,
        ),
        created_at=now,
    )
    db.session.add(audit)

    if target_req.requested_by:
        with contextlib.suppress(Exception):
            dispatch_notification(
                recipient_user=target_req.requested_by,
                event_type="COURSE_CHANGE_REJECTED",
                title=f"Đợt cập nhật khóa học {course_code} cần chỉnh sửa lại",
                body=f"Quản trị viên đã từ chối đợt cập nhật. Lý do: {reason}",
                action_url=f"#/instructor/courses/manage?id={course_public_id}",
                category="COURSE",
                target_role="INSTRUCTOR",
                payload={
                    "course_id": course_public_id,
                    "change_request_id": target_req.id,
                    "reason": reason,
                },
                event_key=uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"pwd301:course-change:{target_req.id}:COURSE_CHANGE_REJECTED:{target_req.requested_by_user_id}",
                ),
                session=db.session,
            )

    db.session.commit()
    return (
        jsonify({"success": True, "status": "REJECTED", "message": "Đã từ chối đợt cập nhật."}),
        200,
    )


@admin_bp.route("/courses/<course_id>/lessons/<lesson_id>/flag", methods=["POST"])
@admin_required
def flag_course_lesson(course_id: str, lesson_id: str) -> tuple[Response, int] | Response:
    """Flag a lesson or its contents (video/file/content) with reasons and notify instructor."""
    from pwd301.services.authorization_service import _resolve_course, _resolve_lesson

    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định và gắn cờ nội dung khóa học.")

    course = _resolve_course(course_id, session=db.session)
    if course is None:
        raise ResourceNotFoundError("Khóa học không tồn tại.")

    lesson = _resolve_lesson(lesson_id, session=db.session)
    if lesson is None or lesson.course_id != course.id:
        raise ResourceNotFoundError("Bài học không tồn tại trong khóa học này.")

    payload = request.get_json(silent=True)
    if payload is None:
        payload = request.form.to_dict()
    if not payload:
        payload = {}
    if not isinstance(payload, dict):
        raise ValidationError("Dữ liệu yêu cầu không hợp lệ.")
    reason = str(payload.get("reason", "")).strip()
    content_type = str(payload.get("content_type", "bài học")).strip()

    if len(reason) < 5:
        raise ValidationError("Lý do gắn cờ bắt buộc tối thiểu 5 ký tự.")

    flag_result = flag_lesson_content(
        actor=actor,
        course=course,
        lesson=lesson,
        reason=reason,
        content_type=content_type,
        idempotency_key=request.headers.get("X-Idempotency-Key"),
        session=db.session,
    )

    return jsonify(
        {
            "success": True,
            "message": f"Đã gắn cờ vi phạm nội dung '{lesson.title}' và gửi thông báo cho giảng viên thành công.",
            "lesson_id": str(lesson.public_id),
            "is_flagged": True,
            "flag_reason": reason,
            "idempotent_replay": bool(flag_result.get("idempotent_replay", False)),
        }
    ), 200


@admin_bp.route("/assessments/<assessment_id>/gradebook.pdf", methods=["GET"])
@admin_required
def admin_export_assessment_gradebook_pdf_route(assessment_id: str) -> Response:
    """Download full class gradebook & proctoring report as PDF (Admin)."""
    import io
    import re
    import urllib.parse

    from flask import send_file

    from pwd301.services.attempt_service import _resolve_assessment, list_assessment_student_results
    from pwd301.services.exceptions import ResourceNotFoundError
    from pwd301.services.file_service import sanitize_filename
    from pwd301.services.result_pdf_service import build_assessment_gradebook_pdf

    actor = require_authenticated_actor()
    assessment = _resolve_assessment(assessment_id, session=db.session)
    if assessment is None:
        raise ResourceNotFoundError("Bài khảo thí không tồn tại.")

    data = list_assessment_student_results(
        actor,
        assessment.id,
        page=1,
        per_page=100,
        session=db.session,
    )
    attempts = data.get("attempts") or []
    for page in range(2, int(data.get("pages") or 1) + 1):
        attempts.extend(
            list_assessment_student_results(
                actor, assessment.id, page=page, per_page=100, session=db.session
            ).get("attempts")
            or []
        )
    released = [a for a in attempts if a.get("score_status") == "RELEASED"]

    total_candidates = len(attempts)
    submitted_count = sum(1 for a in attempts if a.get("submitted_at"))
    passed_count = sum(1 for a in released if a.get("is_passed") or a.get("passed"))
    failed_count = len(released) - passed_count
    pass_rate = round((passed_count / len(released)) * 100, 2) if released else 0.0

    scores = [
        float(
            a.get("percentage")
            if a.get("percentage") is not None
            else (
                a.get("percent_score")
                if a.get("percent_score") is not None
                else (a.get("score") or 0)
            )
        )
        for a in released
    ]
    avg_score = round(sum(scores) / len(scores), 1) if scores else None
    highest_score = max(scores) if scores else None
    lowest_score = min(scores) if scores else None

    roster = []
    for a in attempts:
        user_obj = a.get("user") or a.get("student") or {}
        st_code = a.get("student_code") or user_obj.get("username") or "-"
        st_name = (
            a.get("student_name")
            or user_obj.get("display_name")
            or a.get("student_email")
            or "Thí sinh"
        )
        roster.append(
            {
                "student_code": st_code,
                "student_name": st_name,
                "submitted_at": a.get("submitted_at") or a.get("created_at"),
                "violation_count": int(a.get("violation_count") or a.get("focus_lost_count") or 0),
                "score": a.get("percentage")
                if a.get("percentage") is not None
                else (
                    a.get("percent_score")
                    if a.get("percent_score") is not None
                    else (a.get("score") or 0)
                ),
                "is_passed": bool(a.get("is_passed") or a.get("passed")),
                "score_status": a.get("score_status"),
            }
        )

    instructor_name = "Quản trị viên"
    if assessment.course and assessment.course.owner_instructor:
        instructor_name = (
            assessment.course.owner_instructor.display_name
            or assessment.course.owner_instructor.email
        )

    assess_type = getattr(assessment, "assessment_type", None)
    type_name = str(getattr(assess_type, "name", assess_type) or "")

    gradebook_payload = {
        "assessment_title": assessment.title,
        "assessment_type": type_name,
        "course_title": assessment.course.title if assessment.course else "Khóa học",
        "course_code": assessment.course.course_code if assessment.course else "-",
        "instructor_name": instructor_name,
        "duration_minutes": assessment.time_limit_minutes,
        "total_candidates": total_candidates,
        "submitted_count": submitted_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "pass_rate_pct": pass_rate,
        "average_score": avg_score,
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "attempts": roster,
    }

    pdf_bytes = build_assessment_gradebook_pdf(gradebook_payload)
    safe_title = sanitize_filename(
        f"Bang-diem-{assessment.course.course_code if assessment.course else 'PWD301'}-{assessment.title}.pdf"
    )
    if not safe_title.lower().endswith(".pdf"):
        safe_title = f"{safe_title}.pdf"

    import unicodedata

    ascii_clean = (
        unicodedata.normalize("NFKD", safe_title).encode("ascii", "ignore").decode("ascii")
    )
    ascii_fallback = re.sub(r"[^a-zA-Z0-9\.\-_]", "_", ascii_clean).strip("_") or "bang-diem.pdf"
    if not ascii_fallback.lower().endswith(".pdf"):
        ascii_fallback = f"{ascii_fallback}.pdf"
    encoded_name = urllib.parse.quote(safe_title.encode("utf-8"))

    response = send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=ascii_fallback,
        conditional=False,
    )
    response.headers["Content-Disposition"] = (
        f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded_name}"
    )
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
