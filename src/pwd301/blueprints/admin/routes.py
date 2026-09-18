import contextlib
import json
from typing import Any

import sqlalchemy as sa
from flask import Response, flash, jsonify, redirect, request, url_for

from pwd301.blueprints.admin import admin_bp
from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, Lesson
from pwd301.models.identity import User
from pwd301.models.types import utc_now
from pwd301.services.analytics_service import get_admin_system_overview
from pwd301.services.authorization_service import (
    _resolve_user,
    admin_required,
    require_authenticated_actor,
)
from pwd301.services.course_service import (
    change_course_status,
    reassign_course_owner,
    trash_course,
)
from pwd301.services.exceptions import (
    AdminActionForbiddenError,
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
    require_authenticated_actor()
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


@admin_bp.route("/courses/<course_id>", methods=["GET"])
@admin_required
def admin_course_detail(course_id: str) -> tuple[Response, int] | Response:
    """Retrieve full course inspection dossier including syllabus, lessons, and SLOs."""
    require_authenticated_actor()
    sess = db.session
    from pwd301.services.authorization_service import _resolve_course

    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError(f"Course '{course_id}' not found.")

    lessons = sorted(course.lessons, key=lambda item: getattr(item, "position", 0))
    lessons_data = [
        {
            "lesson_id": str(item.public_id),
            "title": item.title,
            "order_index": getattr(item, "order_index", getattr(item, "position", 1)),
            "position": getattr(item, "position", 1),
            "status": item.status,
            "summary": item.summary,
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
    require_authenticated_actor()
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
                        "status": u.status,
                        "roles": sorted(u.role_codes),
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
    require_authenticated_actor()
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
                "status": target_user.status,
                "roles": sorted(target_user.role_codes),
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
    role_code = str(payload.get("role", "")).strip().upper()
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

    try:
        if action == "assign":
            updated_user = assign_role_to_user(
                user_id=target_user.id,
                role_code=role_code,
                assigned_by_user_id=actor.id,
                reason=reason,
                session=sess,
            )
        else:
            updated_user = remove_role_from_user(
                user_id=target_user.id,
                role_code=role_code,
                removed_by_user_id=actor.id,
                reason=reason,
                session=sess,
            )
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
                "auth_version": updated_user.auth_version,
            }
        ),
        200,
    )


@admin_bp.route("/courses/pending", methods=["GET"])
@admin_required
def list_pending_courses() -> tuple[Response, int] | Response:
    """List all courses currently submitted for review."""
    require_authenticated_actor()

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


@admin_bp.route("/courses/<course_id>/review", methods=["POST"])
@admin_required
def review_course(course_id: str) -> Any:
    """Approve or reject a submitted course (Admin only)."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    action = str(payload.get("action", "")).strip().lower()
    reason = payload.get("reason")

    if action not in ("approve", "reject"):
        if not _is_api_request():
            flash("Hành động duyệt không hợp lệ (chỉ chấp nhận 'approve' hoặc 'reject').", "danger")
            return redirect(url_for("admin.admin_courses"))
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
            if not _is_api_request():
                flash("Lý do từ chối đề cương kiểm toán bắt buộc tối thiểu 5 ký tự.", "danger")
                return redirect(url_for("admin.admin_courses"))
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
    if not _is_api_request():
        status_label = "được phê duyệt" if action == "approve" else "bị từ chối (trả về bản thảo)"
        flash(f"Khóa học '{course.title}' đã {status_label} thành công.", "success")
        return redirect(url_for("admin.admin_courses"))
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/courses/<course_id>/reassign", methods=["POST"])
@admin_required
def reassign_course(course_id: str) -> tuple[Response, int] | Response:
    """Reassign course instructor ownership (Admin only)."""
    actor = require_authenticated_actor()

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

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")

    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="PUBLISHED",
        reason=reason,
    )
    if not _is_api_request():
        flash(f"Khóa học '{course.title}' đã được xuất bản công khai.", "success")
        return redirect(url_for("admin.admin_courses"))
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/courses/<course_id>/trash", methods=["POST", "DELETE"])
@admin_required
def trash_course_route(course_id: str) -> Any:
    """Soft-delete a course to TRASH (Admin)."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")

    course = trash_course(actor=actor, course_id=course_id, reason=reason)
    if not _is_api_request():
        flash(f"Khóa học '{course.title}' đã được chuyển vào thùng rác.", "warning")
        return redirect(url_for("admin.admin_courses"))
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/courses/<course_id>/restore", methods=["POST"])
@admin_required
def restore_course(course_id: str) -> Any:
    """Restore a course from TRASH back to ARCHIVED (Admin only)."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")

    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="ARCHIVED",
        reason=reason,
    )
    if not _is_api_request():
        flash(f"Khóa học '{course.title}' đã được khôi phục về trạng thái lưu trữ.", "success")
        return redirect(url_for("admin.admin_courses"))
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/files/<asset_id>/quarantine-override", methods=["POST"])
@admin_required
def override_file_quarantine(asset_id: str) -> tuple[Response, int] | Response:
    """Admin override to release a quarantined/rejected file asset."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
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

    count = broadcast_system_notification(
        actor=actor,
        title=title,
        body=body,
        target_role=target_role,
        category=category,
        session=db.session,
    )
    return jsonify({"broadcasted_count": count}), 200


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
    return jsonify({"retried_count": count}), 200


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
    reason = payload.get("reason", "")

    user = suspend_user_account(
        admin_actor=actor,
        target_user_id=user_id,
        reason=reason,
        session=db.session,
    )

    if not _is_api_request():
        flash(f"Tài khoản {user.email} đã bị đình chỉ.", "warning")
        return redirect(url_for("admin.admin_users"))

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

    if not _is_api_request():
        flash(f"Tài khoản {user.email} đã được mở khóa/kích hoạt lại thành công.", "success")
        return redirect(url_for("admin.admin_users"))

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
    reason = payload.get("reason")

    user = force_revoke_user_sessions(
        admin_actor=actor,
        target_user_id=user_id,
        reason=reason,
        session=db.session,
    )

    if not _is_api_request():
        flash(
            f"Toàn bộ phiên đăng nhập của tài khoản {user.email} đã bị thu hồi "
            f"(auth_version={user.auth_version}).",
            "info",
        )
        return redirect(url_for("admin.admin_users"))

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
    if not _is_api_request():
        flash(f"Bản sao lưu '{backup.database_backup_name}' đã được tạo thành công.", "success")
        return redirect(url_for("admin.admin_list_backups"))
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
    if not _is_api_request():
        if result.get("integrity_status") == "VERIFIED":
            flash("Xác minh tính toàn vẹn SHA-256 thành công. Bản sao lưu hợp lệ.", "success")
        else:
            flash(f"Xác minh bản sao lưu: {result.get('integrity_status')}.", "warning")
        return redirect(url_for("admin.admin_list_backups"))
    return jsonify(result), 200


@admin_bp.route("/backups/<backup_id>/restore/dry-run", methods=["POST"])
@admin_required
def admin_dry_run_restore(backup_id: str) -> Any:
    """Execute a dry-run restoration drill verifying schema compatibility with zero mutations."""
    actor = require_authenticated_actor()
    result = execute_dry_run_restore(actor, backup_id, session=db.session)
    if not _is_api_request():
        flash(
            "Diễn tập khôi phục (dry-run) thành công. "
            "Tương thích cấu trúc 100%, không ghi đè CSDL.",
            "success",
        )
        return redirect(url_for("admin.admin_list_backups"))
    return jsonify(result), 200


@admin_bp.route("/backups/<backup_id>/restore", methods=["POST"])
@admin_required
def admin_restore_database(backup_id: str) -> tuple[Response, int] | Response:
    """Execute controlled database restoration under strict authentication safeguards."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    confirmation_phrase = payload.get("confirmation_phrase") or payload.get("confirmation_token")
    password = payload.get("password")

    result = restore_database_snapshot(
        actor=actor,
        backup_id=backup_id,
        confirmation_phrase=confirmation_phrase,
        password=password,
        session=db.session,
    )
    return jsonify(result), 200


@admin_bp.route("/maintenance/start", methods=["POST"])
@admin_required
def admin_start_maintenance() -> tuple[Response, int] | Response:
    """Activate system maintenance window blocking non-admin traffic with HTTP 503."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
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
    require_authenticated_actor()
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

    require_authenticated_actor()
    sess = db.session

    status_filter = request.args.get("status", "PENDING").strip().upper()
    if status_filter not in ("PENDING", "APPROVED", "REJECTED", "CANCELLED", "ALL"):
        status_filter = "PENDING"

    applications = list_instructor_applications(status=status_filter, session=sess)
    all_apps = sess.query(InstructorApplication).all()
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

    require_authenticated_actor()
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
        if not _is_api_request():
            flash(str(exc), "danger")
            return redirect(url_for("admin.admin_instructor_applications"))
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}), 400

    msg = (
        f"Đã phê duyệt đơn #{app_id} thành công! "
        "Người dùng đã được cấp quyền Giảng viên (Instructor)."
        if action == "approve"
        else f"Đã từ chối đơn #{app_id}. Thông báo phản hồi đã được gửi đến học viên."
    )

    if not _is_api_request():
        flash(msg, "success" if action == "approve" else "warning")
        return redirect(url_for("admin.admin_instructor_applications"))

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

    require_authenticated_actor()
    app_record = get_instructor_application(app_id, session=db.session)
    if app_record is None:
        raise ResourceNotFoundError(f"Đơn đăng ký #{app_id} không tồn tại.")

    safe_name = secure_filename(filename)
    if not safe_name:
        raise ResourceNotFoundError("Tên tệp tin không hợp lệ.")

    # Tìm original_name từ metadata
    details = app_record.parsed_details
    attached_files = details.get("attached_files", [])
    matched_meta = next((f for f in attached_files if f.get("saved_filename") == safe_name), None)
    download_name = matched_meta.get("original_name", safe_name) if matched_meta else safe_name

    storage_root = Path(current_app.config.get("FILE_STORAGE_ROOT", "./storage")).resolve()
    applicant_key = str(app_record.applicant.public_id) if app_record.applicant else ""
    app_dir = storage_root / "instructor_applications" / applicant_key
    file_path = (app_dir / safe_name).resolve()

    # Chống Path Traversal và kiểm tra tồn tại
    if not str(file_path).startswith(str(storage_root)) or not file_path.is_file():
        raise ResourceNotFoundError("Tệp tin minh chứng không tồn tại hoặc đã bị xóa.")

    return send_file(
        str(file_path),
        as_attachment=True,
        download_name=download_name,
    )


@admin_bp.route("/change-requests", methods=["GET"])
@admin_required
def admin_list_change_requests() -> tuple[Response, int] | Response:
    """List all course and lesson change requests for admin review."""
    require_authenticated_actor()

    status_filter = request.args.get("status", "ALL").strip().upper()
    query = db.session.query(CourseChangeRequest).order_by(CourseChangeRequest.created_at.desc())
    if status_filter != "ALL":
        query = query.filter(CourseChangeRequest.status == status_filter)

    records = query.all()
    results = []
    for r in records:
        try:
            payload_data = json.loads(r.proposed_payload_json) if r.proposed_payload_json else {}
        except Exception:
            payload_data = {}

        target_title = None
        if r.target_type == "LESSON" and r.target_id:
            les = db.session.get(Lesson, r.target_id)
            if les:
                target_title = les.title
        elif r.target_type == "PREREQUISITE" and r.target_id:
            c = db.session.get(Course, r.target_id)
            if c:
                target_title = c.title

        results.append(
            {
                "id": r.id,
                "course_id": str(r.course.public_id) if r.course else str(r.course_id),
                "course_code": r.course.course_code if r.course else None,
                "course_title": r.course.title if r.course else None,
                "requested_by_id": str(r.requested_by.public_id) if r.requested_by else None,
                "requested_by_name": r.requested_by.display_name if r.requested_by else None,
                "change_type": r.change_type,
                "target_type": r.target_type,
                "target_id": r.target_id,
                "target_title": target_title,
                "proposed_payload": payload_data,
                "status": r.status,
                "review_reason": r.review_reason,
                "created_at": r.created_at.isoformat(),
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            }
        )

    pending_count = sum(1 for r in records if r.status == "PENDING")
    return jsonify({"change_requests": results, "pending_count": pending_count}), 200


@admin_bp.route("/change-requests/<int:req_id>/review", methods=["POST"])
@admin_required
def admin_review_change_request(req_id: int) -> tuple[Response, int] | Response:
    """Approve or reject a course/lesson change request (Admin only)."""
    from pwd301.services.enrollment_service import add_course_prerequisite
    from pwd301.services.lesson_service import trash_lesson, update_lesson
    from pwd301.services.notification_service import dispatch_notification

    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    action = str(payload.get("action", "")).strip().lower()
    reason = str(payload.get("reason", "")).strip()

    if action not in ("approve", "reject"):
        raise ValidationError("Action must be 'approve' or 'reject'.")

    req_record = db.session.get(CourseChangeRequest, req_id)
    if req_record is None:
        raise ResourceNotFoundError("Change request not found.")

    if req_record.status != "PENDING":
        raise ValidationError(f"Change request is already in '{req_record.status}' status.")

    now = utc_now()
    try:
        p_data = (
            json.loads(req_record.proposed_payload_json) if req_record.proposed_payload_json else {}
        )
    except Exception:
        p_data = {}

    if action == "approve":
        if req_record.change_type == "LESSON_STRUCTURE" and p_data.get("action") == "DELETE":
            lesson_id = req_record.target_id or p_data.get("lesson_id")
            if lesson_id:
                trash_lesson(
                    actor,
                    lesson_id,
                    reason=reason or "Admin phê duyệt yêu cầu xóa",
                    session=db.session,
                )
            msg = f"Đã phê duyệt yêu cầu xóa bài giảng #{req_record.target_id}."

        elif req_record.change_type in ("LESSON_CONTENT", "LESSON_STRUCTURE"):
            staged = (
                db.session.query(Lesson).filter(Lesson.change_request_id == req_record.id).first()
            )
            if staged:
                from pwd301.services.lesson_service import approve_course_change_request

                approve_course_change_request(
                    actor, req_record.id, review_reason=reason, session=db.session
                )
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
                            "status",
                        )
                    }
                    if update_data:
                        update_lesson(actor, lesson_id, update_data, session=db.session)
            msg = f"Đã phê duyệt thay đổi nội dung bài giảng #{req_record.target_id}."

        elif req_record.change_type == "PREREQUISITE":
            add_course_prerequisite(
                actor=actor,
                course_id=req_record.course_id,
                prerequisite_course_id=req_record.target_id,
                session=db.session,
            )
            msg = f"Đã phê duyệt thiết lập môn tiên quyết #{req_record.target_id}."

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
                    title="Yêu cầu thay đổi đã được Admin phê duyệt",
                    body=(
                        f"Quản trị viên đã phê duyệt yêu cầu thay đổi #{req_record.id} "
                        f"({req_record.change_type})."
                    ),
                    category="COURSE",
                    session=db.session,
                )

    else:
        staged = db.session.query(Lesson).filter(Lesson.change_request_id == req_record.id).first()
        if staged:
            from pwd301.services.lesson_service import reject_course_change_request

            reject_course_change_request(
                actor, req_record.id, review_reason=reason, session=db.session
            )

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
                    title="Yêu cầu thay đổi bị Admin từ chối",
                    body=(
                        f"Quản trị viên đã từ chối yêu cầu thay đổi #{req_record.id}. "
                        f"Lý do: {reason or 'Không có'}."
                    ),
                    category="COURSE",
                    session=db.session,
                )
        msg = f"Đã từ chối yêu cầu thay đổi #{req_record.id}."

    db.session.commit()
    return jsonify({"status": req_record.status, "message": msg}), 200
