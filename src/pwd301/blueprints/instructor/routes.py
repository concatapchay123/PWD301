from __future__ import annotations

import uuid
from typing import Any

from flask import Response, jsonify, render_template, request

from pwd301.blueprints.instructor import instructor_bp
from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.services.analytics_service import (
    get_instructor_course_analytics,
    get_instructor_overview_analytics,
)
from pwd301.services.assessment_service import (
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
    CourseValidationError,
    LessonValidationError,
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


@instructor_bp.route("/courses/<course_id>/manage", methods=["GET"])
@instructor_required
def manage_course(course_id: str) -> tuple[Response, int] | Response:
    """Manage course view protected by resource-level ownership check.

    Invariants enforced:
    - Instructor A accessing Instructor B's course is rejected with 403 Forbidden.
    - Admin can access any course.
    """
    actor = require_authenticated_actor()

    sess = db.session
    course = require_course_manager(actor, course_id, session=sess)

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
        "progress_percent": float(enrollment.current_progress_percent) if enrollment else 0.0,
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
def create_course_route() -> tuple[Response, int] | Response:
    """Create a new course in DRAFT status."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    course = create_course(actor, payload)
    return jsonify(_serialize_course(course)), 201


@instructor_bp.route("/courses/<course_id>", methods=["GET"])
@instructor_required
def get_course_route(course_id: str) -> tuple[Response, int] | Response:
    """Get detailed course information for managing."""
    actor = require_authenticated_actor()

    course = get_course_detail(actor, course_id)
    return jsonify(_serialize_course(course)), 200


@instructor_bp.route("/courses/<course_id>", methods=["PATCH", "PUT"])
@instructor_required
def update_course_route(course_id: str) -> tuple[Response, int] | Response:
    """Update editable course metadata with mass-assignment defense."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    course = update_course(actor, course_id, payload)
    return jsonify(_serialize_course(course)), 200


@instructor_bp.route("/courses/<course_id>/submit", methods=["POST"])
@instructor_bp.route("/courses/<course_id>/publish-request", methods=["POST"])
@instructor_required
def submit_course_route(course_id: str) -> tuple[Response, int] | Response:
    """Submit a DRAFT course for admin review."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    course = change_course_status(
        actor,
        course_id,
        "SUBMITTED_FOR_REVIEW",
        reason=reason,
    )
    return jsonify(_serialize_course(course)), 200


@instructor_bp.route("/courses/<course_id>/trash", methods=["POST", "DELETE"])
@instructor_required
def trash_course_route(course_id: str) -> tuple[Response, int] | Response:
    """Soft-delete a course to TRASH."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    course = trash_course(actor, course_id, reason=reason)
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
def create_lesson_route(course_id: str) -> tuple[Response, int] | Response:
    """Create a new lesson in a managed course."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    lesson = create_lesson(actor, course_id, payload)
    return jsonify(_serialize_lesson(lesson)), 201


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
        "current_progress_percent": float(e.current_progress_percent),
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
    return (
        jsonify(
            {
                "course_id": str(link.course.public_id) if link.course else str(link.course_id),
                "prerequisite_course_id": (
                    str(link.prerequisite_course.public_id)
                    if link.prerequisite_course
                    else str(link.prerequisite_course_id)
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
def create_course_question_route(course_id: str) -> tuple[Response, int] | Response:
    """Create a new question in the instructor question authoring workflow."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
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


@instructor_bp.route("/courses/<course_id>/assessments", methods=["POST"])
@instructor_required
def create_instructor_course_assessment_route(course_id: str) -> tuple[Response, int] | Response:
    """Create a new Assessment for a course in instructor view."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    assessment = create_assessment(actor, course_id, payload, session=db.session)

    return jsonify(_serialize_assessment(assessment, full=False)), 201


@instructor_bp.route("/assessments/<assessment_id>", methods=["GET"])
@instructor_required
def get_instructor_assessment_detail_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Retrieve detailed assessment configuration."""
    actor = require_authenticated_actor()

    data = get_assessment_detail(actor, assessment_id, session=db.session)
    return jsonify(data), 200


@instructor_bp.route("/assessments/<assessment_id>", methods=["PATCH", "PUT"])
@instructor_required
def update_instructor_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Update assessment configuration."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    assessment = update_assessment(actor, assessment_id, payload, session=db.session)

    return jsonify(_serialize_assessment(assessment, full=False)), 200


@instructor_bp.route("/assessments/<assessment_id>/publish", methods=["POST"])
@instructor_required
def publish_instructor_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Publish assessment (DRAFT -> PUBLISHED)."""
    actor = require_authenticated_actor()

    assessment = publish_assessment(actor, assessment_id, session=db.session)

    return jsonify(_serialize_assessment(assessment, full=False)), 200


@instructor_bp.route("/assessments/<assessment_id>/cancel", methods=["POST"])
@instructor_required
def cancel_instructor_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Cancel a published assessment."""
    actor = require_authenticated_actor()

    body = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = body.get("reason")

    assessment = cancel_assessment(actor, assessment_id, reason=reason, session=db.session)

    return jsonify(
        {
            "message": "Assessment cancelled.",
            "assessment": _serialize_assessment(assessment, full=False),
        }
    ), 200


@instructor_bp.route("/assessments/<assessment_id>/trash", methods=["POST"])
@instructor_required
def trash_instructor_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Move assessment to TRASH."""
    actor = require_authenticated_actor()

    body = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = body.get("reason")

    assessment = trash_assessment(actor, assessment_id, reason=reason, session=db.session)

    return jsonify(
        {
            "message": "Assessment moved to trash.",
            "assessment": _serialize_assessment(assessment, full=False),
        }
    ), 200


@instructor_bp.route("/assessments/<assessment_id>/restore", methods=["POST"])
@instructor_required
def restore_instructor_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Restore assessment from TRASH."""
    actor = require_authenticated_actor()

    assessment = restore_assessment(actor, assessment_id, session=db.session)

    return jsonify(
        {
            "message": "Assessment restored from trash.",
            "assessment": _serialize_assessment(assessment, full=False),
        }
    ), 200


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
def assign_instructor_question_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Assign a fixed question to assessment."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    assignment = assign_question(actor, assessment_id, payload, session=db.session)

    return jsonify(_serialize_assignment(assignment)), 201


@instructor_bp.route("/assessments/<assessment_id>/questions/<question_id>", methods=["DELETE"])
@instructor_required
def remove_instructor_question_route(
    assessment_id: str, question_id: str
) -> tuple[Response, int] | Response:
    """Remove a fixed question from assessment."""
    actor = require_authenticated_actor()

    remove_question_assignment(actor, assessment_id, question_id, session=db.session)

    return jsonify({"message": "Question unassigned successfully."}), 200


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
def get_instructor_attempt_grading_route(attempt_id: str) -> tuple[Response, int] | Response:
    """Retrieve detailed attempt answers for grading evaluation."""
    actor = require_authenticated_actor()
    data = get_attempt_grading_detail(actor, attempt_id, session=db.session)
    return jsonify(data), 200


@instructor_bp.route("/attempts/<attempt_id>/grades/<attempt_question_id>", methods=["POST"])
@instructor_required
def grade_instructor_essay_route(
    attempt_id: str,
    attempt_question_id: str,
) -> tuple[Response, int] | Response:
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
