"""Route handlers for the student role blueprint."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from flask import Response, flash, jsonify, redirect, render_template, request, session, url_for

from pwd301.blueprints.student import student_bp
from pwd301.extensions import db
from pwd301.models.course import Enrollment, Lesson, LessonProgress
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
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template("student/dashboard.html", overview=overview)
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
            try:
                _, raw_token = takeover_attempt_lease(
                    actor=actor,
                    attempt_id=attempt_id,
                    session=db.session,
                )
                session[f"attempt_lease_{attempt_id}"] = raw_token
            except Exception:
                raw_token = ""
    else:
        try:
            _, raw_token = takeover_attempt_lease(
                actor=actor,
                attempt_id=attempt_id,
                session=db.session,
            )
            session[f"attempt_lease_{attempt_id}"] = raw_token
        except Exception:
            raw_token = ""

    delivery = get_attempt_delivery(
        student_actor=actor,
        attempt_id=attempt_id,
        session=db.session,
    )
    delivery["lease_token"] = raw_token

    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template("student/attempt.html", delivery=delivery)
    return jsonify(delivery)


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
                if not request.is_json and request.accept_mimetypes.accept_html:
                    return redirect(
                        url_for("student.attempt_view", attempt_id=str(existing.public_id))
                    )
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

    if not request.is_json and request.accept_mimetypes.accept_html:
        return redirect(url_for("student.attempt_view", attempt_id=str(attempt.public_id)))

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
    if request.accept_mimetypes.accept_html and not request.is_json:
        lessons = (
            sess.query(Lesson)
            .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
            .order_by(Lesson.position.asc())
            .all()
        )
        if lessons:
            completed_lesson_ids: set[int] = set()
            if enrollment.current_period_id:
                lesson_ids = [les.id for les in lessons]
                progresses = (
                    sess.query(LessonProgress)
                    .filter(
                        LessonProgress.enrollment_period_id == enrollment.current_period_id,
                        LessonProgress.lesson_id.in_(lesson_ids),
                    )
                    .all()
                )
                completed_lesson_ids = {
                    p.lesson_id for p in progresses if p.completed_at is not None
                }
            # Target first uncompleted lesson or first lesson if none/all completed
            target_lesson = next(
                (les for les in lessons if les.id not in completed_lesson_ids),
                lessons[0],
            )
            return redirect(
                url_for(
                    "student.get_student_lesson_route",
                    course_id=str(course.public_id),
                    lesson_id=str(target_lesson.public_id),
                )
            )
        flash(f"Khóa học '{course.title}' chưa có bài học nào được xuất bản.", "info")
        return redirect(url_for("student.dashboard"))

    return jsonify(data), 200


def _serialize_student_lesson(les: Lesson, p: LessonProgress | None) -> dict[str, Any]:
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
        "progress": {
            "seconds_spent": p.seconds_spent if p else 0,
            "max_view_fraction": float(p.max_view_fraction) if p else 0.0,
            "is_completed": p.completed_at is not None if p else False,
            "completed_at": p.completed_at.isoformat() if p and p.completed_at else None,
        },
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

    if request.accept_mimetypes.accept_html and not request.is_json:
        all_lessons = (
            sess.query(Lesson)
            .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
            .order_by(Lesson.position.asc())
            .all()
        )
        return render_template(
            "student/lesson.html",
            course=course,
            lesson=lesson,
            progress=progress,
            all_lessons=all_lessons,
        )

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
    view_fraction = payload.get("view_fraction")

    if seconds_increment is None or view_fraction is None:
        raise LessonValidationError("Both seconds_increment and view_fraction are required.")

    try:
        sec_int = int(seconds_increment)
        vf_float = float(view_fraction)
    except (ValueError, TypeError):
        raise LessonValidationError(
            "seconds_increment must be an integer and view_fraction must be a float."
        ) from None

    progress = record_lesson_progress(
        actor=actor,
        lesson_id=lesson_id,
        seconds_increment=sec_int,
        view_fraction=vf_float,
    )

    data = {
        "lesson_id": str(progress.lesson.public_id) if progress.lesson else None,
        "seconds_spent": progress.seconds_spent,
        "max_view_fraction": float(progress.max_view_fraction),
        "is_completed": progress.completed_at is not None,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
    }
    return jsonify(data), 200


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

        if not request.is_json and request.accept_mimetypes.accept_html:
            flash("Ghi danh khóa học thành công! Chúc bạn có trải nghiệm học tập tốt.", "success")
            return redirect(url_for("student.course_progress", course_id=course_id))

        return jsonify(_serialize_enrollment(enrollment)), status_code
    except (
        EnrollmentPrerequisiteError,
        EnrollmentCapacityExceededError,
        CourseNotAvailableError,
        AccountNotActiveError,
        EnrollmentStateViolationError,
        EnrollmentError,
        ServiceError,
    ) as e:
        if not request.is_json and request.accept_mimetypes.accept_html:
            flash(f"Không thể ghi danh: {str(e)}", "danger")
            return redirect(url_for("student.student_course_detail", course_id=course_id))
        raise


@student_bp.route("/courses/<course_id>/leave", methods=["POST"])
@student_required
def student_leave_course(course_id: str) -> tuple[Response, int] | Response:
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
def student_re_enroll_course(course_id: str) -> tuple[Response, int] | Response:
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
    """Student Web notifications center page and AJAX endpoint."""
    from flask import render_template

    from pwd301.services.authorization_service import _is_api_or_json_request
    from pwd301.services.notification_service import (
        get_unread_count,
        get_user_preferences,
        list_user_notifications,
    )

    actor = require_authenticated_actor()
    items, total = list_user_notifications(actor=actor, session=db.session)
    prefs = get_user_preferences(actor=actor, session=db.session)
    unread = get_unread_count(actor=actor, session=db.session)

    if _is_api_or_json_request():
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

    rendered = render_template(
        "notifications/index.html",
        notifications=items,
        total=total,
        unread_count=unread,
        preferences=prefs,
    )
    from flask import make_response

    return make_response(rendered)


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
    if not request.is_json and request.accept_mimetypes.accept_html:
        flash("Đã đánh dấu thông báo là đã đọc.", "success")
        return redirect(url_for("student.notifications_center"))
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
    if not request.is_json and request.accept_mimetypes.accept_html:
        flash(f"Đã đánh dấu {count} thông báo là đã đọc.", "success")
        return redirect(url_for("student.notifications_center"))
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
        session=db.session,
    )
    session.pop(f"attempt_lease_{attempt_id}", None)

    if not request.is_json and request.accept_mimetypes.accept_html:
        flash("Nộp bài thi thành công!", "success")
        return redirect(url_for("student.attempt_result_view", attempt_id=attempt_id))

    return jsonify(result), 200


@student_bp.route("/my-learning", methods=["GET"])
@student_required
def my_learning() -> Any:
    """Student view for all enrolled courses with progress and completion summary."""
    actor = require_authenticated_actor()
    overview = get_student_learning_overview(actor, session=db.session)
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template("student/my_learning.html", overview=overview)
    return jsonify({"enrollments": overview["enrollments"]}), 200


@student_bp.route("/assessments", methods=["GET"])
@student_required
def assessments_view() -> Any:
    """Student view for upcoming and past assessments."""
    actor = require_authenticated_actor()
    overview = get_student_learning_overview(actor, session=db.session)
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template("student/assessments.html", overview=overview)
    return jsonify(
        {
            "upcoming": overview["upcoming_assessments"],
            "recent_results": overview["recent_results"],
        }
    ), 200


@student_bp.route("/assessments/<assessment_id>", methods=["GET"])
@student_required
def assessment_detail_view(assessment_id: str) -> Any:
    """Student view for assessment details and rules before starting."""
    from pwd301.models.attempt_regrade import AssessmentAttempt
    from pwd301.services.assessment_service import _resolve_assessment, get_assessment_detail

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
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template(
            "student/assessment_detail.html",
            assessment=assessment_data,
            active_attempt=active_attempt,
        )
    return (
        jsonify(
            {
                "assessment_id": str(assess_obj.public_id),
                "title": assessment_data.get("title"),
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
            if attempt.assessment.course:
                result_data["assessment_code"] = attempt.assessment.course.course_code
        result_data["started_at"] = attempt.started_at.isoformat() if attempt.started_at else None
        result_data["submitted_at"] = (
            attempt.submitted_at.isoformat() if attempt.submitted_at else None
        )
    result_data["is_released"] = result_data.get("score_status") == "RELEASED"

    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template("student/result.html", result=result_data)
    return jsonify(result_data), 200


@student_bp.route("/ai-assistant", methods=["GET"])
@student_required
def ai_assistant_view() -> Any:
    """Redirect to student dashboard with floating AI assistant."""
    require_authenticated_actor()
    if request.accept_mimetypes.accept_html and not request.is_json:
        return redirect(url_for("student.dashboard"))
    return (
        jsonify(
            {
                "status": "deprecated",
                "message": "Use floating AI assistant",
                "redirect_url": url_for("student.dashboard"),
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
    return redirect(
        url_for(
            "student.get_student_lesson_route",
            course_id=str(lesson.course.public_id),
            lesson_id=str(lesson.public_id),
        )
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

    prereq_items = []
    for p in prereqs:
        prereq_items.append(
            {
                "course": p,
                "is_satisfied": p.id in completed_ids,
            }
        )

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

    lessons = (
        db.session.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
        .order_by(Lesson.position.asc())
        .all()
    )

    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template(
            "student/course_detail.html",
            course=course,
            enrollment=enrollment,
            prerequisites=prereqs,
            prereq_items=prereq_items,
            is_eligible=is_eligible,
            missing_titles=missing_titles,
            active_count=active_count,
            is_full=is_full,
            lessons=lessons,
        )
    return jsonify({"course_id": str(course.public_id), "title": course.title}), 200


# ==============================================================================
# Instructor Application / Self-Nomination Portal
# ==============================================================================


def _wants_json() -> bool:
    """Check if the client specifically requested a JSON response."""
    if request.is_json:
        return True
    if request.path.startswith("/api/"):
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept and "text/html" not in accept


@student_bp.route("/become-instructor", methods=["GET"])
@student_required
def become_instructor() -> Any:
    """Page or API to view instructor nomination status or apply."""
    from pwd301.services.user_service import get_user_active_application

    actor = require_authenticated_actor()
    app_record = get_user_active_application(actor.id, session=db.session)

    if not _wants_json():
        return render_template(
            "student/become_instructor.html",
            application=app_record,
            is_already_instructor=actor.is_instructor,
        )

    return (
        jsonify(
            {
                "is_already_instructor": actor.is_instructor,
                "application": (
                    {
                        "id": app_record.id,
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
    from pathlib import Path

    from flask import current_app
    from werkzeug.utils import secure_filename

    from pwd301.services.exceptions import ValidationError
    from pwd301.services.user_service import submit_instructor_application

    actor = require_authenticated_actor()
    raw_payload = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    payload: dict[str, Any] = dict(raw_payload) if isinstance(raw_payload, dict) else {}

    # Xử lý các tệp tin minh chứng đính kèm nếu có
    attached_files = []
    if "evidence_files" in request.files:
        files = request.files.getlist("evidence_files")
        allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".zip", ".doc"}
        storage_root = Path(current_app.config.get("FILE_STORAGE_ROOT", "./storage"))
        user_storage = storage_root / "instructor_applications" / str(actor.id)
        user_storage.mkdir(parents=True, exist_ok=True)

        for f in files:
            if not f or not f.filename or not f.filename.strip():
                continue
            ext = Path(f.filename).suffix.lower()
            if ext not in allowed_extensions:
                msg = (
                    f"Định dạng tệp '{f.filename}' không được hỗ trợ. "
                    "Vui lòng tải file PDF, hình ảnh (PNG, JPG) hoặc Word/Excel/ZIP."
                )
                if not _wants_json():
                    flash(msg, "danger")
                    return redirect(url_for("student.become_instructor"))
                return jsonify({"error": {"code": "INVALID_FILE_TYPE", "message": msg}}), 400

            safe_stem = secure_filename(Path(f.filename).stem) or "evidence"
            saved_filename = f"{uuid.uuid4().hex[:8]}_{safe_stem}{ext}"
            dest_path = user_storage / saved_filename
            f.save(str(dest_path))
            file_size = dest_path.stat().st_size if dest_path.exists() else 0

            attached_files.append(
                {
                    "original_name": Path(f.filename).name,
                    "saved_filename": saved_filename,
                    "size": file_size,
                }
            )

    if attached_files:
        payload["attached_files"] = attached_files

    try:
        app_record = submit_instructor_application(
            user_id=actor.id,
            application_data=payload,
            session=db.session,
        )
    except ValidationError as exc:
        if not _wants_json():
            flash(str(exc), "danger")
            return redirect(url_for("student.become_instructor"))
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}), 400

    if not _wants_json():
        flash(
            "Hồ sơ đề cử giảng viên của bạn đã được gửi thành công! "
            "Quản trị viên sẽ sớm thẩm định và phản hồi.",
            "success",
        )
        return redirect(url_for("student.become_instructor"))

    return (
        jsonify(
            {
                "message": "Đơn đăng ký đã được gửi thành công.",
                "application_id": app_record.id,
                "status": app_record.status,
            }
        ),
        201,
    )


@student_bp.route("/become-instructor/cancel", methods=["POST"])
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
        if not _wants_json():
            flash("Không tìm thấy đơn đăng ký đang chờ xét duyệt để hủy.", "warning")
            return redirect(url_for("student.become_instructor"))
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
        if not _wants_json():
            flash(str(exc), "danger")
            return redirect(url_for("student.become_instructor"))
        return jsonify({"error": {"code": "ERROR", "message": str(exc)}}), 400

    if not _wants_json():
        flash("Bạn đã hủy đơn đăng ký thành công.", "info")
        return redirect(url_for("student.become_instructor"))

    return jsonify({"message": "Đã hủy đơn đăng ký.", "status": cancelled.status}), 200
