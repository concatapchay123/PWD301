"""Route handlers for the student role blueprint."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from flask import (
    Response,
    current_app,
    jsonify,
    request,
    send_file,
    session,
)

from pwd301.blueprints.student import student_bp
from pwd301.extensions import db
from pwd301.models.course import Enrollment, Lesson, LessonProgress
from pwd301.models.types import utc_now
from pwd301.services.analytics_service import get_student_learning_overview
from pwd301.services.authorization_service import (
    _resolve_course,
    require_authenticated_actor,
    student_required,
)
from pwd301.services.completion_service import get_course_completion_summary
from pwd301.services.enrollment_service import (
    enroll_student,
    get_student_enrollments,
    leave_course,
    re_enroll_student,
)
from pwd301.services.exceptions import LessonValidationError, ResourceNotFoundError
from pwd301.services.file_service import (
    _serialize_lesson_resource,
    get_file_for_download,
    sanitize_filename,
)
from pwd301.services.lesson_service import (
    get_lesson_detail,
    get_lesson_progress,
    record_lesson_progress,
)

logger = logging.getLogger(__name__)


@student_bp.route("/dashboard", methods=["GET"])
@student_required
def dashboard() -> Any:
    """Student dashboard displaying learning overview and enrolled courses."""
    actor = require_authenticated_actor()
    overview = get_student_learning_overview(actor, session=db.session)
    return jsonify(overview), 200


@student_bp.route("/attempt/<attempt_id>", methods=["GET"])
@student_required
def attempt_view(attempt_id: str) -> Any:
    """Render the student exam taking view with server timer, lease token, and question palette."""
    actor = require_authenticated_actor()
    from pwd301.services.attempt_service import (
        get_attempt_delivery,
        renew_attempt_lease,
        takeover_attempt_lease,
    )

    raw_token = session.get(f"attempt_lease_{attempt_id}")
    if raw_token:
        try:
            renew_attempt_lease(
                actor=actor,
                attempt_id=attempt_id,
                raw_lease_token=raw_token,
                session=db.session,
            )
        except Exception:
            raw_token = None

    if not raw_token:
        try:
            _, raw_token = takeover_attempt_lease(
                actor=actor,
                attempt_id=attempt_id,
                session=db.session,
            )
            session[f"attempt_lease_{attempt_id}"] = raw_token
        except Exception:
            raw_token = None

    delivery = get_attempt_delivery(
        student_actor=actor,
        attempt_id=attempt_id,
        session=db.session,
    )
    delivery["lease_token"] = raw_token
    return jsonify(delivery), 200


@student_bp.route("/assessments/<assessment_id>/start", methods=["POST"])
@student_required
def student_start_assessment(assessment_id: str) -> Any:
    """Start an assessment attempt via Web session and redirect to exam view."""
    from pwd301.models.attempt_regrade import AssessmentAttempt
    from pwd301.services.attempt_service import _resolve_assessment, start_assessment_attempt
    from pwd301.services.exceptions import ActiveAttemptExistsError

    actor = require_authenticated_actor()
    try:
        attempt, raw_token = start_assessment_attempt(
            student_actor=actor,
            assessment_id=assessment_id,
            session=db.session,
        )
        session[f"attempt_lease_{attempt.public_id}"] = raw_token
        db.session.commit()
    except ActiveAttemptExistsError:
        assess = _resolve_assessment(assessment_id, session=db.session)
        if assess is not None:
            existing = (
                db.session.query(AssessmentAttempt)
                .filter(
                    AssessmentAttempt.assessment_id == assess.id,
                    AssessmentAttempt.student_user_id == actor.id,
                    AssessmentAttempt.status == "IN_PROGRESS",
                )
                .first()
            )
            if existing is not None:
                return (
                    jsonify(
                        {
                            "attempt_id": str(existing.public_id),
                            "lease_token": session.get(f"attempt_lease_{existing.public_id}", ""),
                            "status": existing.status,
                        }
                    ),
                    200,
                )
        raise

    return (
        jsonify(
            {
                "attempt_id": str(attempt.public_id),
                "lease_token": raw_token,
                "status": attempt.status,
            }
        ),
        201,
    )


@student_bp.route("/courses/<course_id>/progress", methods=["GET"])
@student_required
def course_progress(course_id: str) -> Any:
    """Get the authenticated student's progress in a specific course."""
    actor = require_authenticated_actor()

    sess = db.session
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    # Scoped strictly to current actor (IDOR prevention)
    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )
    if enrollment is None:
        raise ResourceNotFoundError("Enrollment record not found for this student.")

    data = {
        "course_id": str(course.public_id),
        "course_title": course.title,
        "student_id": str(actor.public_id),
        "progress_percent": float(enrollment.current_progress_percent or 0.0),
        "status": enrollment.status,
        "enrolled_at": enrollment.enrolled_at.isoformat(),
    }
    return jsonify(data), 200


def _serialize_student_lesson(les: Lesson, p: LessonProgress | None) -> dict[str, Any]:
    import json
    import re

    cleaned_markdown = les.markdown_content or ""
    video_url = None
    if cleaned_markdown:
        m = re.search(r"<!--\s*video_url:\s*(\S+?)\s*-->", cleaned_markdown)
        if m:
            video_url = m.group(1)
            # Remove comment so raw video URL is not leaked into student markdown text
            cleaned_markdown = re.sub(
                r"<!--\s*video_url:\s*(\S+?)\s*-->", "", cleaned_markdown
            ).strip()

    res_list = []
    primary_video_asset_id = None
    if hasattr(les, "resources") and les.resources:
        for r in les.resources:
            fa = r.file_asset
            if not fa:
                continue
            is_scan_ok = getattr(fa, "virus_scan_status", "CLEAN") in ("CLEAN", "UNSCANNED")
            is_status_ok = fa.status in ("ACTIVE", "PENDING_SCAN")
            if not (is_scan_ok and is_status_ok):
                continue

            mime = (fa.mime_type or "").lower()
            name = (fa.original_filename or "").lower()
            vid_exts = (".mp4", ".webm", ".mkv", ".mov")
            is_video = mime.startswith("video/") or name.endswith(vid_exts)

            if not video_url and is_video:
                video_url = f"/student/files/{fa.public_id}/download?disposition=inline"
                primary_video_asset_id = str(fa.public_id)
                # Primary video is played inline and NOT listed in downloadable resource list
                continue

            if primary_video_asset_id and str(fa.public_id) == primary_video_asset_id:
                continue

            ser_r = _serialize_lesson_resource(r)
            res_list.append(ser_r)

    personal_notes = ""
    notes_saved_at = None
    if p and p.completion_rule_snapshot_json:
        try:
            p_data = json.loads(p.completion_rule_snapshot_json)
            if isinstance(p_data, dict):
                personal_notes = p_data.get("personal_notes", "")
                notes_saved_at = p_data.get("notes_saved_at")
        except Exception:
            pass

    quiz = []
    if les.markdown_content:
        m_quiz = re.search(r"<!--\s*mini_quiz:\s*(.+?)\s*-->", les.markdown_content, re.DOTALL)
        if m_quiz:
            try:
                parsed_quiz = json.loads(m_quiz.group(1))
                if isinstance(parsed_quiz, list):
                    quiz = parsed_quiz
            except Exception:
                pass

    return {
        "lesson_id": str(les.public_id),
        "course_id": str(les.course.public_id) if les.course else None,
        "title": les.title,
        "summary": les.summary,
        "markdown_content": cleaned_markdown,
        "position": les.position,
        "estimated_duration_minutes": les.estimated_duration_minutes,
        "minimum_completion_seconds": les.minimum_completion_seconds,
        "viewed_fraction_required": float(les.viewed_fraction_required),
        "video_url": video_url,
        "quiz": quiz,
        "personal_notes": personal_notes,
        "notes_saved_at": notes_saved_at,
        "progress": {
            "seconds_spent": p.seconds_spent if p else 0,
            "max_view_fraction": float(p.max_view_fraction) if p else 0.0,
            "is_completed": p.completed_at is not None if p else False,
            "completed_at": p.completed_at.isoformat() if p and p.completed_at else None,
        },
        "resources": res_list,
    }


@student_bp.route("/courses/<course_id>/lessons/<lesson_id>", methods=["GET"])
@student_required
def get_student_lesson_route(course_id: str, lesson_id: str) -> Any:
    """Access lesson content for learning, protected by active enrollment check."""
    actor = require_authenticated_actor()

    sess = db.session
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    lesson = get_lesson_detail(actor, lesson_id)
    if lesson.course_id != course.id:
        raise ResourceNotFoundError("Lesson does not belong to this course.")

    progress = get_lesson_progress(actor, lesson_id)

    return jsonify(_serialize_student_lesson(lesson, progress)), 200


@student_bp.route("/lessons/<lesson_id>/progress", methods=["POST"])
@student_required
def record_student_progress_route(lesson_id: str) -> tuple[Response, int] | Response:
    """Heartbeat endpoint to record lesson engagement progress."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    if not isinstance(payload, dict):
        raise LessonValidationError("Invalid JSON payload.")

    seconds_increment = payload.get("seconds_increment")
    if seconds_increment is None:
        seconds_increment = payload.get("time_spent_seconds", 0)

    view_fraction = payload.get("view_fraction")
    if view_fraction is None:
        view_fraction = 1.0 if payload.get("completed") else 0.0

    try:
        sec_int = int(str(seconds_increment or 0))
        vf_float = float(view_fraction if view_fraction is not None else 0.0)
    except (ValueError, TypeError):
        raise LessonValidationError(
            "seconds_increment must be an integer and view_fraction must be a float."
        ) from None

    bounded_sec = max(1, min(sec_int, 60))
    bounded_vf = max(0.0, min(vf_float, 1.0))

    progress = record_lesson_progress(
        actor=actor,
        lesson_id=lesson_id,
        seconds_increment=bounded_sec,
        view_fraction=bounded_vf,
    )

    if payload.get("completed") and progress.completed_at is None:
        now = utc_now()
        progress.completed_at = now
        progress.updated_at = now
        db.session.commit()

    data = {
        "lesson_id": str(progress.lesson.public_id) if progress.lesson else None,
        "seconds_spent": progress.seconds_spent,
        "max_view_fraction": float(progress.max_view_fraction),
        "is_completed": progress.completed_at is not None,
        "completed": progress.completed_at is not None,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
    }
    return jsonify(data), 200


@student_bp.route("/lessons/<lesson_id>/notes", methods=["GET"])
@student_required
def get_student_lesson_notes(lesson_id: str) -> tuple[Response, int] | Response:
    """Retrieve personal notes for a lesson from lesson progress or session."""
    import json

    actor = require_authenticated_actor()
    notes = ""
    saved_at = None
    try:
        progress = get_lesson_progress(actor, lesson_id, session=db.session)
        if progress and progress.completion_rule_snapshot_json:
            try:
                p_data = json.loads(progress.completion_rule_snapshot_json)
                if isinstance(p_data, dict):
                    notes = p_data.get("personal_notes", "")
                    saved_at = p_data.get("notes_saved_at")
            except Exception:
                pass
    except Exception:
        pass

    if not notes:
        notes = session.get(f"lesson_notes_{lesson_id}", "")
        saved_at = session.get(f"lesson_notes_saved_{lesson_id}")

    return jsonify({"notes": notes, "saved_at": saved_at}), 200


@student_bp.route("/lessons/<lesson_id>/notes", methods=["POST"])
@student_required
def save_student_lesson_notes(lesson_id: str) -> tuple[Response, int] | Response:
    """Save personal notes for a lesson into lesson progress and session."""
    import json

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    notes = payload.get("notes", "")
    now_iso = utc_now().isoformat()

    session[f"lesson_notes_{lesson_id}"] = notes
    session[f"lesson_notes_saved_{lesson_id}"] = now_iso

    try:
        progress = get_lesson_progress(actor, lesson_id, session=db.session)
        if progress:
            existing = {}
            if progress.completion_rule_snapshot_json:
                try:
                    existing = json.loads(progress.completion_rule_snapshot_json)
                    if not isinstance(existing, dict):
                        existing = {}
                except Exception:
                    existing = {}
            existing["personal_notes"] = notes
            existing["notes_saved_at"] = now_iso
            progress.completion_rule_snapshot_json = json.dumps(existing)
            progress.updated_at = utc_now()
            db.session.commit()
    except Exception:
        pass

    return (
        jsonify(
            {
                "notes": notes,
                "saved_at": now_iso,
                "message": "Đã lưu ghi chú thành công.",
            }
        ),
        200,
    )


def _serialize_enrollment(e: Enrollment) -> dict[str, Any]:
    return {
        "enrollment_id": str(e.public_id),
        "course_id": str(e.course.public_id) if e.course else None,
        "course_code": e.course.course_code if e.course else None,
        "course_title": e.course.title if e.course else None,
        "student_id": str(e.student.public_id) if e.student else None,
        "status": e.status,
        "period_no": e.current_period.period_no if e.current_period else None,
        "current_progress_percent": float(e.current_progress_percent or 0.0),
        "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
        "left_at": e.left_at.isoformat() if e.left_at else None,
        "detail_retention_due_at": (
            e.detail_retention_due_at.isoformat() if e.detail_retention_due_at else None
        ),
    }


_serialize_enrollment_api = _serialize_enrollment


@student_bp.route("/courses/<course_id>/enroll", methods=["POST"])
@student_required
def student_enroll_course(course_id: str) -> Any:
    """Self-enroll in a published course."""
    actor = require_authenticated_actor()

    from pwd301.services.exceptions import (
        AccountNotActiveError,
        CourseNotAvailableError,
        EnrollmentCapacityExceededError,
        EnrollmentError,
        EnrollmentPrerequisiteError,
        EnrollmentStateViolationError,
        ServiceError,
    )

    try:
        enrollment = enroll_student(actor=actor, course_id=course_id, session=db.session)
        status_code = 201 if getattr(enrollment, "_is_new", False) else 200

        return jsonify(_serialize_enrollment(enrollment)), status_code
    except (
        EnrollmentPrerequisiteError,
        EnrollmentCapacityExceededError,
        CourseNotAvailableError,
        AccountNotActiveError,
        EnrollmentStateViolationError,
        EnrollmentError,
        ServiceError,
    ):
        raise


@student_bp.route("/courses/<course_id>/leave", methods=["POST"])
@student_required
def student_leave_course(course_id: str) -> Any:
    """Withdraw from an active course."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    if reason is not None and not isinstance(reason, str):
        reason = str(reason)

    enrollment = leave_course(actor=actor, course_id=course_id, reason=reason, session=db.session)
    return jsonify(_serialize_enrollment(enrollment)), 200


@student_bp.route("/courses/<course_id>/re-enroll", methods=["POST"])
@student_required
def student_re_enroll_course(course_id: str) -> Any:
    """Re-enroll in a previously left course."""
    actor = require_authenticated_actor()

    enrollment = re_enroll_student(actor=actor, course_id=course_id, session=db.session)
    return jsonify(_serialize_enrollment(enrollment)), 200


@student_bp.route("/enrollments", methods=["GET"])
@student_required
def student_list_enrollments() -> tuple[Response, int] | Response:
    """List all enrollments belonging to the authenticated student."""
    actor = require_authenticated_actor()

    status = request.args.get("status")
    enrollments = get_student_enrollments(actor=actor, status=status, session=db.session)
    return jsonify({"enrollments": [_serialize_enrollment(e) for e in enrollments]}), 200


@student_bp.route("/courses/<course_id>/completion", methods=["GET"])
@student_required
def get_student_course_completion_route(course_id: str) -> tuple[Response, int] | Response:
    """Get the authenticated student's completion summary for a course."""
    actor = require_authenticated_actor()

    course = _resolve_course(course_id, session=db.session)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    summary = get_course_completion_summary(
        actor=actor,
        course_id=course.id,
        student_user_id=actor.id,
        session=db.session,
    )

    enrollment = (
        db.session.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )

    data = {
        "course_id": str(course.public_id),
        "course_code": course.course_code,
        "course_title": course.title,
        "student_id": str(actor.public_id),
        "ever_completed": summary.ever_completed if summary else False,
        "first_completed_at": (
            summary.first_completed_at.isoformat()
            if summary and summary.first_completed_at
            else None
        ),
        "latest_completed_at": (
            summary.latest_completed_at.isoformat()
            if summary and summary.latest_completed_at
            else None
        ),
        "prerequisite_eligible": summary.prerequisite_eligible if summary else False,
        "current_status": enrollment.status if enrollment else None,
        "current_progress_percent": (
            float(enrollment.current_progress_percent or 0.0) if enrollment else 0.0
        ),
    }
    return jsonify(data), 200


@student_bp.route("/notifications", methods=["GET"])
@student_required
def notifications_center() -> tuple[Response, int] | Response:
    from pwd301.services.notification_service import (
        get_unread_count,
        get_user_preferences,
        list_user_notifications,
    )

    actor = require_authenticated_actor()
    items, total = list_user_notifications(actor=actor, session=db.session)
    prefs = get_user_preferences(actor=actor, session=db.session)
    unread = get_unread_count(actor=actor, session=db.session)

    return (
        jsonify(
            {
                "items": items,
                "total": total,
                "unread_count": unread,
                "preferences": prefs,
            }
        ),
        200,
    )


@student_bp.route("/notifications/<notification_id>/read", methods=["POST"])
@student_required
def student_mark_notification_read(notification_id: str) -> Any:
    """Mark a notification as read via Web UI or AJAX."""
    from pwd301.services.notification_service import mark_notification_as_read

    actor = require_authenticated_actor()
    result = mark_notification_as_read(
        actor=actor,
        notification_id=notification_id,
        session=db.session,
    )
    return jsonify(result), 200


@student_bp.route("/notifications/mark-all-read", methods=["POST"])
@student_required
def student_mark_all_read() -> Any:
    """Mark all unread notifications as read via Web UI or AJAX."""
    from pwd301.services.notification_service import mark_all_as_read

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    category = payload.get("category") or request.args.get("category")
    count = mark_all_as_read(actor=actor, category=category, session=db.session)
    return jsonify({"marked_count": count}), 200


@student_bp.route("/attempt/<attempt_id>/answers/<attempt_question_id>", methods=["POST", "PUT"])
@student_required
def save_student_attempt_answer(
    attempt_id: str,
    attempt_question_id: str,
) -> tuple[Response, int] | Response:
    """Autosave answer during active student attempt via Web UI / AJAX."""
    from pwd301.services.attempt_service import save_attempt_answer

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    raw_token = (
        request.headers.get("X-Attempt-Lease-Token")
        or request.headers.get("X-Lease-Token")
        or payload.get("lease_token")
        or payload.get("raw_lease_token")
        or session.get(f"attempt_lease_{attempt_id}")
        or ""
    )
    result = save_attempt_answer(
        actor=actor,
        attempt_id=attempt_id,
        attempt_question_id=attempt_question_id,
        payload=payload,
        raw_lease_token=raw_token,
        session=db.session,
    )
    return jsonify(result), 200


@student_bp.route("/attempt/<attempt_id>/lease/renew", methods=["POST"])
@student_required
def renew_student_attempt_lease(attempt_id: str) -> tuple[Response, int] | Response:
    """Renew editing lease for active exam attempt via Web session."""
    from pwd301.services.attempt_service import renew_attempt_lease

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    raw_token = (
        request.headers.get("X-Attempt-Lease-Token")
        or request.headers.get("X-Lease-Token")
        or payload.get("lease_token")
        or session.get(f"attempt_lease_{attempt_id}")
        or ""
    )
    result = renew_attempt_lease(
        actor=actor,
        attempt_id=attempt_id,
        raw_lease_token=raw_token,
        session=db.session,
    )
    return jsonify(result), 200


@student_bp.route("/attempt/<attempt_id>/lease/takeover", methods=["POST"])
@student_required
def takeover_student_attempt_lease(attempt_id: str) -> tuple[Response, int] | Response:
    """Take over editing lease for active exam attempt via Web session."""
    from pwd301.services.attempt_service import takeover_attempt_lease

    actor = require_authenticated_actor()
    attempt, raw_token = takeover_attempt_lease(
        actor=actor,
        attempt_id=attempt_id,
        session=db.session,
    )
    session[f"attempt_lease_{attempt_id}"] = raw_token
    return (
        jsonify(
            {
                "attempt_id": str(attempt.public_id),
                "status": attempt.status,
                "lease_token": raw_token,
                "lease_epoch": attempt.lease_epoch or 1,
            }
        ),
        200,
    )


@student_bp.route("/attempt/<attempt_id>/submit", methods=["POST"])
@student_required
def submit_student_attempt(attempt_id: str) -> Any:
    """Submit assessment attempt via Web UI / AJAX with idempotency and lease release."""
    from pwd301.services.attempt_service import submit_assessment_attempt

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    raw_token = (
        request.headers.get("X-Attempt-Lease-Token")
        or request.headers.get("X-Lease-Token")
        or payload.get("lease_token")
        or session.get(f"attempt_lease_{attempt_id}")
    )
    idempotency_key = (
        request.headers.get("X-Submission-Idempotency-Key")
        or request.headers.get("X-Idempotency-Key")
        or payload.get("submission_idempotency_key")
        or payload.get("idempotency_key")
        or uuid.uuid4()
    )

    result = submit_assessment_attempt(
        actor=actor,
        attempt_id=attempt_id,
        idempotency_key=idempotency_key,
        raw_lease_token=raw_token,
        auto_finalize_expired=True,
        session=db.session,
    )
    session.pop(f"attempt_lease_{attempt_id}", None)

    return jsonify(result), 200


@student_bp.route("/my-learning", methods=["GET"])
@student_required
def my_learning() -> Any:
    """Student view for all enrolled courses with progress and completion summary."""
    actor = require_authenticated_actor()
    overview = get_student_learning_overview(actor, session=db.session)
    enrollments_data = overview.get("enrollments", [])
    return (
        jsonify(
            {
                "enrollments": enrollments_data,
                "courses": enrollments_data,
                "overall_average_progress_percent": overview.get(
                    "overall_average_progress_percent", 0.0
                ),
            }
        ),
        200,
    )


@student_bp.route("/assessments", methods=["GET"])
@student_required
def assessments_view() -> Any:
    """Student view for upcoming and past assessments with full items listing."""
    from pwd301.models.assessment import Assessment
    from pwd301.models.attempt_regrade import AssessmentAttempt

    actor = require_authenticated_actor()
    sess = db.session
    overview = get_student_learning_overview(actor, session=sess)

    # Find active & completed enrollment course IDs
    enrollments = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.status.in_(("ACTIVE", "COMPLETED")),
        )
        .all()
    )
    enrolled_course_ids = [e.course_id for e in enrollments]

    items: list[dict[str, Any]] = []
    if enrolled_course_ids:
        assessments = (
            sess.query(Assessment)
            .filter(
                Assessment.course_id.in_(enrolled_course_ids),
                Assessment.status == "PUBLISHED",
                Assessment.deleted_at.is_(None),
            )
            .order_by(Assessment.created_at.desc())
            .all()
        )
        for a in assessments:
            attempts_for_a = (
                sess.query(AssessmentAttempt)
                .filter(
                    AssessmentAttempt.assessment_id == a.id,
                    AssessmentAttempt.student_user_id == actor.id,
                    AssessmentAttempt.status != "CANCELLED",
                )
                .order_by(AssessmentAttempt.id.asc())
                .all()
            )
            a_attempts_count = len(attempts_for_a)
            a_limit = a.attempt_limit
            a_is_limit_reached = bool(
                a_limit is not None and a_limit > 0 and a_attempts_count >= a_limit
            )
            a_remaining = (
                max(0, a_limit - a_attempts_count)
                if (a_limit is not None and a_limit > 0)
                else None
            )
            existing_attempt = attempts_for_a[-1] if attempts_for_a else None

            max_pts = float(
                getattr(a, "max_points", None)
                or (
                    sum(float(qa.points or 0.0) for qa in a.question_assignments)
                    if getattr(a, "question_assignments", None)
                    else 10.0
                )
                or 10.0
            )
            res_raw = None
            res_passed = None
            if existing_attempt and existing_attempt.result:
                if existing_attempt.result.raw_score is not None:
                    res_raw = float(existing_attempt.result.raw_score)
                if existing_attempt.result.passed is not None:
                    res_passed = bool(existing_attempt.result.passed)

            items.append(
                {
                    "assessment_id": str(a.public_id),
                    "id": str(a.public_id),
                    "title": a.title,
                    "course_code": a.course.course_code if a.course else None,
                    "course_title": a.course.title if a.course else None,
                    "assessment_type": a.assessment_type,
                    "time_limit_minutes": a.time_limit_minutes or 45,
                    "max_points": max_pts,
                    "status": a.status,
                    "open_at": a.open_at.isoformat() if a.open_at else None,
                    "close_at": a.close_at.isoformat() if a.close_at else None,
                    "attempt_id": str(existing_attempt.public_id) if existing_attempt else None,
                    "attempt_status": existing_attempt.status if existing_attempt else None,
                    "raw_score": res_raw,
                    "is_passed": res_passed,
                    "attempt_limit": a_limit,
                    "attempts_count": a_attempts_count,
                    "remaining_attempts": a_remaining,
                    "is_attempt_limit_reached": a_is_limit_reached,
                }
            )

    return (
        jsonify(
            {
                "items": items,
                "assessments": items,
                "upcoming": overview["upcoming_assessments"],
                "recent_results": overview["recent_results"],
            }
        ),
        200,
    )


@student_bp.route("/assessments/<assessment_id>", methods=["GET"])
@student_required
def assessment_detail_view(assessment_id: str) -> Any:
    """Student view for assessment details and rules before starting."""
    from pwd301.models.attempt_regrade import AssessmentAttempt
    from pwd301.models.course import Enrollment, EnrollmentPeriod
    from pwd301.models.types import utc_now
    from pwd301.services.assessment_service import (
        _normalize_dt,
        _resolve_assessment,
        get_assessment_detail,
    )

    actor = require_authenticated_actor()
    assess_obj = _resolve_assessment(assessment_id, session=db.session)
    if assess_obj is None:
        raise ResourceNotFoundError("Assessment not found.")

    assessment_data = get_assessment_detail(actor, assess_obj, session=db.session)
    if assess_obj.course:
        assessment_data["course_code"] = assess_obj.course.course_code
        assessment_data["course_title"] = assess_obj.course.title

    active_attempt = (
        db.session.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.assessment_id == assess_obj.id,
            AssessmentAttempt.student_user_id == actor.id,
            AssessmentAttempt.status == "IN_PROGRESS",
        )
        .first()
    )

    now_utc = utc_now()
    open_at_dt = _normalize_dt(assess_obj.open_at)
    close_at_dt = _normalize_dt(assess_obj.close_at)

    is_open = True
    seconds_until_open = 0
    if open_at_dt and now_utc < open_at_dt:
        is_open = False
        seconds_until_open = max(0, int((open_at_dt - now_utc).total_seconds()))

    is_closed = False
    if close_at_dt and now_utc >= close_at_dt:
        is_closed = True

    # Identify current enrollment period to calculate attempts accurately
    enrollment = (
        db.session.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.course_id == assess_obj.course_id,
            Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
        )
        .first()
    )
    current_period = None
    if enrollment and enrollment.current_period_id:
        current_period = (
            db.session.query(EnrollmentPeriod)
            .filter(
                EnrollmentPeriod.id == enrollment.current_period_id,
                EnrollmentPeriod.status == "ACTIVE",
            )
            .first()
        )

    attempts_query = db.session.query(AssessmentAttempt).filter(
        AssessmentAttempt.assessment_id == assess_obj.id,
        AssessmentAttempt.student_user_id == actor.id,
        AssessmentAttempt.status != "CANCELLED",
    )
    if current_period is not None:
        attempts_query = attempts_query.filter(
            AssessmentAttempt.enrollment_period_id == current_period.id
        )
    attempts = attempts_query.order_by(AssessmentAttempt.attempt_number.asc()).all()

    attempts_count = len(attempts)
    attempt_limit = assess_obj.attempt_limit
    is_attempt_limit_reached = bool(
        attempt_limit is not None and attempt_limit > 0 and attempts_count >= attempt_limit
    )
    remaining_attempts = (
        max(0, attempt_limit - attempts_count)
        if (attempt_limit is not None and attempt_limit > 0)
        else None
    )

    # Check score release policy for student
    policy = assess_obj.score_release_policy
    attempts_summary: list[dict[str, Any]] = []
    best_att = None
    highest_score = -1.0

    for att in attempts:
        is_score_released = False
        if policy == "IMMEDIATE":
            is_score_released = bool(att.result and att.result.status in ("FINAL", "RELEASED"))
        elif policy == "AFTER_CLOSE":
            is_score_released = bool(close_at_dt and now_utc >= close_at_dt)
        elif policy == "INSTRUCTOR_RELEASE":
            is_score_released = bool(att.result and att.result.status == "RELEASED")

        raw_score = None
        max_score = None
        passed = None
        if is_score_released and att.result:
            raw_score = float(att.result.raw_score) if att.result.raw_score is not None else None
            max_score = float(att.result.max_score) if att.result.max_score is not None else None
            passed = bool(att.result.passed) if att.result.passed is not None else None
            if raw_score is not None and raw_score > highest_score:
                highest_score = raw_score
                best_att = att

        attempts_summary.append(
            {
                "attempt_id": str(att.public_id),
                "attempt_number": att.attempt_number,
                "status": att.status,
                "started_at": att.started_at.isoformat() if att.started_at else None,
                "submitted_at": att.submitted_at.isoformat() if att.submitted_at else None,
                "raw_score": raw_score,
                "max_score": max_score,
                "passed": passed,
                "is_score_released": is_score_released,
            }
        )

    latest_attempt_id = str(attempts[-1].public_id) if attempts else None
    best_attempt_id = str(best_att.public_id) if best_att else latest_attempt_id

    can_start = bool(
        is_open and not is_closed and not is_attempt_limit_reached and active_attempt is None
    )

    return (
        jsonify(
            {
                "assessment_id": str(assess_obj.public_id),
                "title": assessment_data.get("title"),
                "assessment": assessment_data,
                "is_open": is_open,
                "is_closed": is_closed,
                "seconds_until_open": seconds_until_open,
                "server_now_iso": now_utc.isoformat(),
                "active_attempt_id": str(active_attempt.public_id) if active_attempt else None,
                "attempt_limit": attempt_limit,
                "attempts_count": attempts_count,
                "remaining_attempts": remaining_attempts,
                "is_attempt_limit_reached": is_attempt_limit_reached,
                "can_start": can_start,
                "attempts": attempts_summary,
                "latest_attempt_id": latest_attempt_id,
                "best_attempt_id": best_attempt_id,
            }
        ),
        200,
    )


@student_bp.route("/attempt/<attempt_id>/result", methods=["GET"])
@student_required
def attempt_result_view(attempt_id: str) -> Any:
    """Student view to view graded attempt results and score breakdown."""
    from pwd301.services.attempt_service import _resolve_attempt, get_attempt_result_for_student

    actor = require_authenticated_actor()
    result_data = get_attempt_result_for_student(
        actor=actor,
        attempt_id=attempt_id,
        session=db.session,
    )
    attempt = _resolve_attempt(attempt_id, session=db.session)
    if attempt:
        if attempt.assessment:
            result_data["assessment_title"] = attempt.assessment.title
            assess_type = getattr(attempt.assessment, "assessment_type", None)
            if assess_type is not None:
                result_data["assessment_type"] = (
                    assess_type.name if hasattr(assess_type, "name") else str(assess_type)
                )
            result_data["duration_minutes"] = getattr(attempt.assessment, "duration_minutes", 45)
            if attempt.assessment.course:
                result_data["course_id"] = str(attempt.assessment.course.public_id)
                result_data["assessment_code"] = attempt.assessment.course.course_code
                inst = getattr(attempt.assessment.course, "owner_instructor", None)
                if inst:
                    result_data["instructor_name"] = getattr(inst, "display_name", None) or getattr(
                        inst, "full_name", ""
                    )
        result_data["started_at"] = attempt.started_at.isoformat() if attempt.started_at else None
        result_data["submitted_at"] = (
            attempt.submitted_at.isoformat() if attempt.submitted_at else None
        )
    result_data["is_released"] = result_data.get("score_status") == "RELEASED"

    return jsonify(result_data), 200


@student_bp.route("/ai-assistant", methods=["GET"])
@student_required
def ai_assistant_view() -> Any:
    """Informative endpoint for student AI assistant."""
    require_authenticated_actor()
    return (
        jsonify(
            {
                "status": "ok",
                "message": "AI assistant ready.",
            }
        ),
        200,
    )


@student_bp.route("/ai/chat", methods=["POST"])
@student_required
def student_ai_chat() -> Any:
    from pwd301.services.ai_service import create_conversation, get_conversation, send_chat_message
    from pwd301.services.exceptions import (
        AIConversationExpiredError,
        AIOutOfScopeError,
        AIPromptInjectionError,
        AIQuotaExceededError,
        AISecurityViolationError,
    )
    from pwd301.services.rate_limit_service import check_ai_rate_limit

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    message = (payload.get("message") or payload.get("content") or "").strip()
    if not message:
        return jsonify({"error": {"message": "Vui lòng nhập nội dung tin nhắn."}}), 400

    conv_id = payload.get("conversation_id") or session.get("active_ai_conversation_id")
    conv = None
    if conv_id:
        try:
            conv = get_conversation(actor=actor, conversation_id=conv_id, session=db.session)
            if conv and (conv.is_expired or conv.status == "EXPIRED"):
                logger.info(
                    "Active AI conversation %s expired for actor %s, auto-renewing session.",
                    conv_id,
                    actor.id,
                )
                conv = None
                session.pop("active_ai_conversation_id", None)
        except Exception:
            conv = None
            session.pop("active_ai_conversation_id", None)

    if conv is None:
        course_id = payload.get("course_id")
        lesson_id = payload.get("lesson_id")
        if course_id:
            target_course = _resolve_course(course_id, session=db.session)
            if target_course is None:
                return (
                    jsonify({"error": {"message": "Khóa học không tồn tại.", "code": "NOT_FOUND"}}),
                    404,
                )
            enr_check = (
                db.session.query(Enrollment)
                .filter(
                    Enrollment.student_user_id == actor.id,
                    Enrollment.course_id == target_course.id,
                    Enrollment.status.in_(("ACTIVE", "COMPLETED")),
                )
                .first()
            )
            if not enr_check:
                return (
                    jsonify(
                        {
                            "error": {
                                "message": (
                                    "Bạn chưa ghi danh khóa học này nên không thể "
                                    "truy cập trợ lý AI ngữ cảnh."
                                ),
                                "code": "FORBIDDEN_NOT_ENROLLED",
                            },
                            "status": "refused",
                        }
                    ),
                    403,
                )
            course_id = str(target_course.public_id)

        context_type = "LESSON" if lesson_id else ("COURSE" if course_id else "GLOBAL")
        try:
            conv = create_conversation(
                actor=actor,
                context_type=context_type,
                course_id=course_id,
                lesson_id=lesson_id,
                session=db.session,
            )
            session["active_ai_conversation_id"] = str(conv.public_id)
            db.session.commit()
        except Exception as exc:
            logger.error("Failed creating AI conversation: %s", exc)

    try:
        check_ai_rate_limit(actor, role=actor.primary_role, client_ip=request.remote_addr)
    except AIQuotaExceededError as e:
        resp = jsonify({"error": {"message": str(e), "code": "RATE_LIMIT_EXCEEDED"}})
        resp.headers["Retry-After"] = str(getattr(e, "retry_after", 60))
        return resp, 429
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 429

    if conv is None:
        # Fallback friendly response
        return jsonify(
            {
                "reply": (
                    "Chào bạn! Mình là Bạch Tuộc Trợ lý AI 🐙. "
                    f"Đối với câu hỏi '{message}', "
                    "bạn hãy hỏi trực tiếp về bài học hoặc kiến thức lập trình Web nhé!"
                ),
                "status": "success",
            }
        ), 200

    try:
        is_on_main_page = not bool(conv.course_id or conv.lesson_id or payload.get("course_id"))
        surface_hint = "MAIN_PAGE" if is_on_main_page else None
        try:
            user_msg, asst_msg = send_chat_message(
                actor=actor,
                conversation_id=str(conv.public_id),
                content=message,
                raise_out_of_scope=True,
                session=db.session,
                surface_hint=surface_hint,
            )
        except AIConversationExpiredError:
            logger.info(
                "AI conversation %s expired during message dispatch, recreating session.",
                conv.public_id,
            )
            session.pop("active_ai_conversation_id", None)
            course_id = payload.get("course_id")
            lesson_id = payload.get("lesson_id")
            context_type = "LESSON" if lesson_id else ("COURSE" if course_id else "GLOBAL")
            conv = create_conversation(
                actor=actor,
                context_type=context_type,
                course_id=course_id,
                lesson_id=lesson_id,
                session=db.session,
            )
            session["active_ai_conversation_id"] = str(conv.public_id)
            db.session.commit()
            is_on_main_page = not bool(conv.course_id or conv.lesson_id or course_id)
            surface_hint = "MAIN_PAGE" if is_on_main_page else None
            user_msg, asst_msg = send_chat_message(
                actor=actor,
                conversation_id=str(conv.public_id),
                content=message,
                raise_out_of_scope=True,
                session=db.session,
                surface_hint=surface_hint,
            )

        db.session.commit()
        course_title = conv.course.title if (conv and conv.course) else None
        return jsonify(
            {
                "conversation_id": str(conv.public_id),
                "reply": asst_msg.content if asst_msg else "Không có phản hồi từ trợ lý.",
                "course_title": course_title,
                "status": "success",
            }
        ), 200
    except (AIPromptInjectionError, AISecurityViolationError) as exc:
        logger.warning("Student AI chat blocked security violation: %s", exc)
        return jsonify(
            {
                "conversation_id": str(conv.public_id) if conv else None,
                "reply": (
                    "⚠️ Cảnh báo an ninh: Yêu cầu của bạn đã bị từ chối do vi phạm chính sách "
                    "an toàn thông tin của hệ thống. Trợ lý AI chỉ phục vụ mục đích học tập và "
                    "nghiêm cấm mọi hành vi tấn công, khai thác lỗ hổng hoặc phá hoại."
                ),
                "status": "refused",
                "error_code": "SECURITY_VIOLATION",
            }
        ), 200
    except AIOutOfScopeError as exc:
        logger.info("Student AI chat refused out-of-scope query: %s", exc)
        return jsonify(
            {
                "conversation_id": str(conv.public_id) if conv else None,
                "reply": exc.message,
                "status": "refused",
                "error_code": "OUT_OF_SCOPE",
            }
        ), 200
    except Exception as exc:
        logger.warning("Student AI chat encountered error: %s", exc)
        return jsonify(
            {
                "conversation_id": str(conv.public_id) if conv else None,
                "reply": (
                    f"Chào bạn! Mình là Bạch Tuộc Trợ lý AI 🐙. Đối với câu hỏi '{message}':\n"
                    "Hiện tại kết nối AI đang bận hoặc có gián đoạn tạm thời. "
                    "Bạn có thể xem lại tài liệu bài học, ví dụ mã nguồn hoặc "
                    "đặt lại câu hỏi sau ít giây nhé!"
                ),
                "status": "success",
            }
        ), 200


@student_bp.route("/lessons/<lesson_id>", methods=["GET"])
@student_required
def get_student_lesson_by_id(lesson_id: str) -> Any:
    """Convenient shortcut route to view a lesson by lesson_id."""
    actor = require_authenticated_actor()
    lesson = get_lesson_detail(actor, lesson_id)
    if lesson.course is None:
        raise ResourceNotFoundError("Course not found for this lesson.")
    return get_student_lesson_route(
        course_id=str(lesson.course.public_id),
        lesson_id=str(lesson.public_id),
    )


@student_bp.route("/courses/<course_id>", methods=["GET"])
@student_required
def student_course_detail(course_id: str) -> Any:
    """Course detail view with prerequisites checking and enrollment."""
    import sqlalchemy as sa

    from pwd301.models.course import CourseCompletionSummary
    from pwd301.services.enrollment_service import (
        check_prerequisites_met,
        get_course_prerequisites,
    )

    actor = require_authenticated_actor()
    course = _resolve_course(course_id, session=db.session)
    if course is None:
        raise ResourceNotFoundError("Course not found.")
    enrollment = (
        db.session.query(Enrollment)
        .filter(Enrollment.student_user_id == actor.id, Enrollment.course_id == course.id)
        .first()
    )

    is_eligible, missing_titles = check_prerequisites_met(actor.id, course.id, session=db.session)
    prereqs = get_course_prerequisites(course_id=course.id, session=db.session)

    prereq_ids = [p.id for p in prereqs]
    completed_ids: set[int] = set()
    if prereq_ids:
        summaries = (
            db.session.query(CourseCompletionSummary.course_id)
            .filter(
                CourseCompletionSummary.student_user_id == actor.id,
                CourseCompletionSummary.course_id.in_(prereq_ids),
                CourseCompletionSummary.prerequisite_eligible == True,
            )
            .all()
        )
        completed_ids = {s[0] for s in summaries}
        completed_enrs = (
            db.session.query(Enrollment.course_id)
            .filter(
                Enrollment.student_user_id == actor.id,
                Enrollment.course_id.in_(prereq_ids),
                Enrollment.status == "COMPLETED",
            )
            .all()
        )
        for ce in completed_enrs:
            completed_ids.add(ce[0])

    prereq_items = [
        {
            "id": str(p.public_id),
            "code": p.course_code,
            "course_code": p.course_code,
            "title": p.title,
            "is_satisfied": p.id in completed_ids,
        }
        for p in prereqs
    ]

    active_count = (
        db.session.query(sa.func.count(Enrollment.id))
        .filter(
            Enrollment.course_id == course.id,
            Enrollment.status == "ACTIVE",
        )
        .scalar()
        or 0
    )
    is_full = bool(course.capacity and course.capacity > 0 and active_count >= course.capacity)

    from pwd301.models.assessment import Assessment
    from pwd301.models.attempt_regrade import AssessmentAttempt
    from pwd301.models.file_import import FileAsset

    lessons = (
        db.session.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
        .order_by(Lesson.position.asc())
        .all()
    )

    lesson_progress_map: dict[int, LessonProgress] = {}
    if enrollment and enrollment.current_period_id and lessons:
        progs = (
            db.session.query(LessonProgress)
            .filter(
                LessonProgress.enrollment_period_id == enrollment.current_period_id,
                LessonProgress.lesson_id.in_([les.id for les in lessons]),
            )
            .all()
        )
        for prg in progs:
            lesson_progress_map[prg.lesson_id] = prg

    assessments = (
        db.session.query(Assessment)
        .filter(
            Assessment.course_id == course.id,
            Assessment.status == "PUBLISHED",
            Assessment.deleted_at.is_(None),
        )
        .order_by(Assessment.created_at.asc())
        .all()
    )

    serialized_assessments = []
    for a in assessments:
        attempts_for_a = (
            db.session.query(AssessmentAttempt)
            .filter(
                AssessmentAttempt.assessment_id == a.id,
                AssessmentAttempt.student_user_id == actor.id,
                AssessmentAttempt.status != "CANCELLED",
            )
            .order_by(AssessmentAttempt.id.asc())
            .all()
        )
        a_attempts_count = len(attempts_for_a)
        a_limit = a.attempt_limit
        a_is_limit_reached = bool(
            a_limit is not None and a_limit > 0 and a_attempts_count >= a_limit
        )
        a_remaining = (
            max(0, a_limit - a_attempts_count) if (a_limit is not None and a_limit > 0) else None
        )
        existing_attempt = attempts_for_a[-1] if attempts_for_a else None

        serialized_assessments.append(
            {
                "assessment_id": str(a.public_id),
                "id": str(a.public_id),
                "title": a.title,
                "assessment_type": a.assessment_type,
                "time_limit_minutes": a.time_limit_minutes,
                "attempt_limit": a_limit,
                "attempts_count": a_attempts_count,
                "remaining_attempts": a_remaining,
                "is_attempt_limit_reached": a_is_limit_reached,
                "max_points": float(
                    getattr(a, "max_points", None)
                    or (
                        sum(float(qa.points or 0.0) for qa in a.question_assignments)
                        if getattr(a, "question_assignments", None)
                        else 10.0
                    )
                    or 10.0
                ),
                "status": a.status,
                "attempt_id": str(existing_attempt.public_id) if existing_attempt else None,
                "attempt_status": existing_attempt.status if existing_attempt else None,
            }
        )

    file_assets = (
        db.session.query(FileAsset)
        .filter(
            FileAsset.course_id == course.id,
            FileAsset.status == "ACTIVE",
            FileAsset.deleted_at.is_(None),
        )
        .all()
    )
    serialized_resources = []
    for fa in file_assets:
        if fa.virus_scan_status != "CLEAN":
            continue
        rev_name = fa.revisions[-1].original_filename if fa.revisions else None
        serialized_resources.append(
            {
                "resource_id": str(fa.public_id),
                "label": fa.display_name or rev_name or "Tài liệu môn học",
                "filename": rev_name or fa.display_name,
                "file_size_formatted": "Tài liệu giáo trình",
                "download_url": (
                    f"/student/courses/{course.public_id}/files/{fa.public_id}/download"
                ),
            }
        )

    serialized_lessons = []
    for les in lessons:
        les_prg = lesson_progress_map.get(les.id)
        serialized_lessons.append(
            {
                "id": str(les.public_id),
                "public_id": str(les.public_id),
                "lesson_id": str(les.public_id),
                "title": les.title,
                "summary": les.summary,
                "position": les.position,
                "estimated_duration_minutes": les.estimated_duration_minutes or 45,
                "is_completed": les_prg.completed_at is not None if les_prg else False,
                "progress": {
                    "seconds_spent": les_prg.seconds_spent if les_prg else 0,
                    "max_view_fraction": float(les_prg.max_view_fraction) if les_prg else 0.0,
                    "is_completed": les_prg.completed_at is not None if les_prg else False,
                    "completed_at": (
                        les_prg.completed_at.isoformat()
                        if les_prg and les_prg.completed_at
                        else None
                    ),
                },
                "resources": (
                    [
                        _serialize_lesson_resource(r)
                        for r in les.resources
                        if r.file_asset
                        and r.file_asset.status == "ACTIVE"
                        and r.file_asset.virus_scan_status == "CLEAN"
                    ]
                    if hasattr(les, "resources") and les.resources
                    else []
                ),
            }
        )

    contact_info = None
    clean_desc = course.description or ""
    if course.description and "<!-- contact_info:" in course.description:
        import contextlib
        import json
        import re

        m_contact = re.search(
            r"<!--\s*contact_info:\s*(\{.*?\})\s*-->", course.description, re.DOTALL
        )
        if m_contact:
            with contextlib.suppress(Exception):
                contact_info = json.loads(m_contact.group(1))
        clean_desc = re.sub(
            r"<!--\s*contact_info:\s*\{.*?\}\s*-->\n*", "", course.description, flags=re.DOTALL
        ).strip()

    instructor_email = course.owner_instructor.email if course.owner_instructor else None
    if not contact_info:
        contact_info = {
            "email": instructor_email or "",
            "phone": "",
            "group": "",
            "office_hours": "",
        }

    return jsonify(
        {
            "course": {
                "id": str(course.public_id),
                "public_id": str(course.public_id),
                "code": course.course_code,
                "course_code": course.course_code,
                "title": course.title,
                "description": clean_desc,
                "category": course.category,
                "difficulty": course.difficulty,
                "learning_objectives": course.learning_objectives,
                "target_audience": course.target_audience,
                "completion_requirements": course.completion_requirements,
                "status": course.status,
                "capacity": course.capacity,
                "is_full": is_full,
                "active_enrolled_count": active_count,
                "instructor_name": (
                    course.owner_instructor.display_name
                    if course.owner_instructor
                    else "Hội đồng Khoa học Khoa CNTT"
                ),
                "instructor_email": instructor_email,
                "contact_info": contact_info,
            },
            "enrollment": (
                {
                    "status": enrollment.status if enrollment else None,
                    "id": str(enrollment.public_id) if enrollment else None,
                    "enrollment_id": str(enrollment.public_id) if enrollment else None,
                }
                if enrollment
                else None
            ),
            "is_eligible": is_eligible,
            "missing_titles": missing_titles,
            "prerequisites": prereq_items,
            "lessons": serialized_lessons,
            "assessments": serialized_assessments,
            "resources": serialized_resources,
        }
    ), 200


# ==============================================================================
# Instructor Application / Self-Nomination Portal
# ==============================================================================


@student_bp.route("/become-instructor", methods=["GET"])
@student_required
def become_instructor() -> Any:
    """Page or API to view instructor nomination status or apply."""
    from pwd301.services.user_service import get_user_active_application

    actor = require_authenticated_actor()
    app_record = get_user_active_application(actor.id, session=db.session)

    return (
        jsonify(
            {
                "is_already_instructor": actor.is_instructor,
                "application": (
                    {
                        "id": str(app_record.public_id),
                        "application_id": str(app_record.public_id),
                        "status": app_record.status,
                        "status_label": app_record.status_label_vi,
                        "details": app_record.parsed_details,
                        "review_reason": app_record.review_reason,
                        "created_at": app_record.created_at.isoformat(),
                        "reviewed_at": (
                            app_record.reviewed_at.isoformat() if app_record.reviewed_at else None
                        ),
                    }
                    if app_record
                    else None
                ),
            }
        ),
        200,
    )


@student_bp.route("/become-instructor", methods=["POST"])
@student_required
def submit_become_instructor() -> Any:
    """Submit a self-nomination application to become an instructor."""

    from werkzeug.utils import secure_filename

    from pwd301.services.exceptions import ValidationError
    from pwd301.services.user_service import submit_instructor_application

    actor = require_authenticated_actor()
    raw_payload = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    payload: dict[str, Any] = dict(raw_payload) if isinstance(raw_payload, dict) else {}

    # Xử lý các tệp tin minh chứng đính kèm nếu có
    attached_files = []
    evidence_field_specs = [
        ("cv_file", "CV_PORTFOLIO"),
        ("portfolio_file", "CV_PORTFOLIO"),
        ("evidence_files", "EVIDENCE"),
        ("sheer_id_file", "SHEER_ID"),
        ("schedule_file", "SCHEDULE"),
        ("salary_file", "SALARY"),
        ("contract_file", "CONTRACT"),
    ]

    has_files = any(field_name in request.files for field_name, _ in evidence_field_specs)
    if has_files:
        import hashlib
        import shutil

        from werkzeug.utils import secure_filename

        from pwd301.services.file_service import LimitingStream, get_file_quarantine_root
        from pwd301.services.scanner_service import scan_file_all_engines

        allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx"}
        storage_root = Path(current_app.config.get("FILE_STORAGE_ROOT", "./storage")).resolve()
        # ADR-02: Use actor.public_id instead of internal BigInt actor.id
        user_storage = storage_root / "instructor_applications" / str(actor.public_id)
        user_storage.mkdir(parents=True, exist_ok=True)

        quarantine_root = get_file_quarantine_root()
        max_evidence_bytes = 50_000_000  # Enforce 50 MB ceiling (SEC-02 DoS prevention)

        for field_name, doc_type in evidence_field_specs:
            if field_name not in request.files:
                continue
            files = request.files.getlist(field_name)
            for f in files:
                if not f or not f.filename or not f.filename.strip():
                    continue
                clean_original_name = sanitize_filename(f.filename)
                ext = Path(clean_original_name).suffix.lower()
                if ext not in allowed_extensions:
                    msg = (
                        f"Định dạng tệp '{clean_original_name}' không được hỗ trợ. "
                        "Vui lòng tải file PDF, hình ảnh (PNG, JPG) hoặc Word/Excel (.docx, .xlsx)."
                    )
                    return jsonify({"error": {"code": "INVALID_FILE_TYPE", "message": msg}}), 400

                temp_filename = f"evidence_{uuid.uuid4().hex}.tmp"
                temp_path = quarantine_root / temp_filename
                hasher = hashlib.sha256()
                total_size = 0
                stream_reader = LimitingStream(f.stream, max_bytes=max_evidence_bytes)

                try:
                    with open(temp_path, "wb") as f_out:
                        while True:
                            chunk = stream_reader.read(64 * 1024)
                            if not chunk:
                                break
                            total_size += len(chunk)
                            hasher.update(chunk)
                            f_out.write(chunk)
                except Exception as read_err:
                    if temp_path.exists():
                        temp_path.unlink(missing_ok=True)
                    msg = f"Lỗi đọc tệp '{clean_original_name}': {str(read_err)}"
                    return jsonify({"error": {"code": "FILE_UPLOAD_ERROR", "message": msg}}), 400

                if total_size <= 0:
                    if temp_path.exists():
                        temp_path.unlink(missing_ok=True)
                    continue

                # Multi-engine malware scanning (SEC-02 ClamAV scan)
                scan_verdicts = scan_file_all_engines(temp_path)
                is_clean = all(v.status == "PASS" for v in scan_verdicts)
                if not is_clean:
                    if temp_path.exists():
                        temp_path.unlink(missing_ok=True)
                    msg = (
                        f"Tệp tin '{clean_original_name}' bị nghi ngờ chứa mã độc và đã bị từ chối."
                    )
                    return jsonify({"error": {"code": "FILE_INFECTED", "message": msg}}), 400

                safe_stem = secure_filename(Path(clean_original_name).stem) or "evidence"
                saved_filename = f"{uuid.uuid4().hex[:8]}_{safe_stem}{ext}"
                dest_path = user_storage / saved_filename

                try:
                    shutil.move(str(temp_path), str(dest_path))
                except Exception:
                    shutil.copy2(str(temp_path), str(dest_path))
                    temp_path.unlink(missing_ok=True)

                attached_files.append(
                    {
                        "original_name": clean_original_name,
                        "saved_filename": saved_filename,
                        "doc_type": doc_type,
                        "size": total_size,
                        "sha256": hasher.hexdigest(),
                        "virus_scan_status": "CLEAN",
                    }
                )

    if attached_files:
        payload["attached_files"] = attached_files

    # Defensively map alternate/brief web form fields
    if "institution_name" not in payload and "teaching_experience" in payload:
        parts = str(payload.get("teaching_experience", "")).split("tại", 1)
        if len(parts) == 2:
            payload.setdefault("institution_name", parts[1].strip() or "Đại học / Viện đào tạo")
            payload.setdefault("specialization", parts[0].strip() or "Công nghệ thông tin")
        else:
            payload.setdefault("institution_name", "Đại học / Viện đào tạo")
            payload.setdefault(
                "specialization", str(payload.get("teaching_experience", "Công nghệ thông tin"))
            )
    if "specialization" not in payload and "teaching_experience" in payload:
        payload["specialization"] = str(payload.get("teaching_experience", "Công nghệ thông tin"))
    if "statement_of_purpose" not in payload and "statement" in payload:
        payload["statement_of_purpose"] = payload.get("statement", "")
    if "statement_of_purpose" not in payload and "bio" in payload:
        payload["statement_of_purpose"] = payload.get("bio", "")
    if "evidence_urls" not in payload and "certificate_url" in payload:
        payload["evidence_urls"] = payload.get("certificate_url", "")
    if "evidence_urls" not in payload and "portfolio_url" in payload:
        payload["evidence_urls"] = payload.get("portfolio_url", "")

    try:
        app_record = submit_instructor_application(
            user_id=actor.id,
            application_data=payload,
            session=db.session,
        )
    except ValidationError as exc:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}), 400

    return (
        jsonify(
            {
                "message": "Đơn đăng ký đã được gửi thành công.",
                "application_id": str(app_record.public_id),
                "id": str(app_record.public_id),
                "status": app_record.status,
            }
        ),
        201,
    )


@student_bp.route("/attempts/<attempt_id>/appeal", methods=["POST"])
@student_required
def submit_attempt_appeal_route(attempt_id: str) -> Any:
    """Submit an appeal / regrading request for a completed attempt."""
    import json

    from pwd301.models.notification_audit import AuditEvent
    from pwd301.models.types import utc_now
    from pwd301.services.attempt_service import _resolve_attempt

    actor = require_authenticated_actor()
    attempt = _resolve_attempt(attempt_id, session=db.session)
    if attempt is None:
        raise ResourceNotFoundError("Lượt thi không tồn tại.")
    if attempt.student_user_id != actor.id:
        return (
            jsonify(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Bạn không có quyền khiếu nại bài thi này.",
                    }
                }
            ),
            403,
        )

    payload = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    payload = payload or {}
    reason = str(payload.get("reason", "Yêu cầu phúc khảo bài thi")).strip()
    note = str(payload.get("note", "")).strip()

    now = utc_now()
    appeal_details = {
        "reason": reason,
        "note": note,
        "status": "PENDING",
        "created_at": now.isoformat(),
    }

    audit_entry = AuditEvent(
        actor_user_id=actor.id,
        actor_roles_snapshot="STUDENT",
        action="STUDENT_ATTEMPT_APPEAL",
        target_type="ASSESSMENT_ATTEMPT",
        target_id=attempt.id,
        reason=f"Học viên gửi đơn phúc khảo bài thi: {reason}"[:1000],
        after_json=json.dumps(appeal_details, ensure_ascii=False),
        created_at=now,
    )
    db.session.add(audit_entry)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Đơn phúc khảo đã được gửi thành công đến Hội đồng Khảo thí.",
                "appeal": appeal_details,
            }
        ),
        201,
    )


@student_bp.route("/attempts/<attempt_id>/appeal", methods=["GET"])
@student_required
def get_attempt_appeal_route(attempt_id: str) -> Any:
    """Retrieve current appeal status for an attempt."""
    import json

    from pwd301.models.notification_audit import AuditEvent
    from pwd301.services.attempt_service import _resolve_attempt

    actor = require_authenticated_actor()
    attempt = _resolve_attempt(attempt_id, session=db.session)
    if attempt is None:
        raise ResourceNotFoundError("Lượt thi không tồn tại.")
    if attempt.student_user_id != actor.id and not actor.is_instructor and not actor.is_admin:
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Không có quyền truy cập."}}), 403

    event = (
        db.session.query(AuditEvent)
        .filter(
            AuditEvent.target_type == "ASSESSMENT_ATTEMPT",
            AuditEvent.target_id == attempt.id,
            AuditEvent.action.in_(["STUDENT_ATTEMPT_APPEAL", "INSTRUCTOR_APPEAL_DECISION"]),
        )
        .order_by(AuditEvent.id.desc())
        .first()
    )

    if not event or not event.after_json:
        return jsonify({"appeal": None}), 200

    try:
        data = json.loads(event.after_json)
    except Exception:
        data = {}

    appeal_info = {
        "status": data.get("status", "PENDING"),
        "reason": data.get("reason", event.reason),
        "note": data.get("note", ""),
        "created_at": data.get("created_at") or event.created_at.isoformat(),
        "reviewed_at": data.get("reviewed_at"),
        "reviewer_note": data.get("reviewer_note"),
        "score_delta": data.get("score_delta"),
    }
    return jsonify({"appeal": appeal_info}), 200


@student_bp.route("/become-instructor/cancel", methods=["POST"])
@student_bp.route(
    "/become-instructor/cancel", methods=["POST"], endpoint="cancel_instructor_application"
)
@student_required
def cancel_become_instructor() -> Any:
    """Cancel a pending instructor application."""
    from pwd301.services.exceptions import ResourceNotFoundError, ValidationError
    from pwd301.services.user_service import (
        cancel_instructor_application,
        get_user_active_application,
    )

    actor = require_authenticated_actor()
    app_record = get_user_active_application(actor.id, session=db.session)
    if app_record is None or app_record.status != "PENDING":
        return jsonify(
            {"error": {"code": "NOT_FOUND", "message": "Không có đơn đang chờ xét duyệt."}}
        ), 404

    try:
        cancelled = cancel_instructor_application(
            user_id=actor.id,
            application_id=app_record.id,
            session=db.session,
        )
    except (ValidationError, ResourceNotFoundError) as exc:
        return jsonify({"error": {"code": "ERROR", "message": str(exc)}}), 400

    return (
        jsonify(
            {
                "message": "Đã hủy đơn đăng ký thành công.",
                "application_id": str(cancelled.public_id),
                "id": str(cancelled.public_id),
                "status": cancelled.status,
            }
        ),
        200,
    )


@student_bp.route("/courses/<course_id>/files/<asset_id>/download", methods=["GET"])
@student_bp.route(
    "/courses/<course_id>/files/<asset_id>/download",
    methods=["GET"],
    endpoint="download_lesson_file",
)
@student_bp.route("/files/<asset_id>/download", methods=["GET"])
@student_required
def download_student_course_file_route(asset_id: str, course_id: str | None = None) -> Any:
    """Download or stream a course file asset for an enrolled student.

    Enforces active enrollment, published course status, and clean scan status (fail-closed).
    """
    actor = require_authenticated_actor()
    version_param = request.args.get("version")
    revision_no = int(version_param) if version_param and version_param.isdigit() else None

    asset, blob, physical_path = get_file_for_download(
        actor, asset_id, revision_no=revision_no, session=db.session
    )

    if course_id is not None:
        course = _resolve_course(course_id, session=db.session)
        if course is None or course.id != asset.course_id:
            raise ResourceNotFoundError("File asset not found for the specified course.")

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
