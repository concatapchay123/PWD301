"""REST API route handlers for Course catalog and lifecycle per 04_COURSE_API.md."""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.api_courses import api_course_bp
from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.services.assessment_service import (
    _serialize_assessment,
    create_assessment,
    list_course_assessments,
)
from pwd301.services.authorization_service import (
    _resolve_course,
    get_authenticated_actor,
    instructor_required,
    require_course_manager,
    require_student_data_access,
)
from pwd301.services.completion_service import (
    calculate_course_progress,
    get_or_create_default_completion_rule,
    set_course_completion_rule,
)
from pwd301.services.course_service import (
    change_course_status,
    create_course,
    get_course_detail,
    list_courses,
    update_course,
)
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    enroll_student,
    get_course_enrollments,
    get_course_prerequisites,
    leave_course,
    re_enroll_student,
    remove_course_prerequisite,
)
from pwd301.services.exceptions import (
    CourseValidationError,
    ForbiddenError,
    ResourceNotFoundError,
)
from pwd301.services.jwt_auth_service import jwt_required
from pwd301.services.lesson_service import get_course_lessons
from pwd301.services.question_bank_service import (
    _serialize_question,
    create_question,
    list_course_questions,
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
        "published_at": c.published_at.isoformat() if c.published_at else None,
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
    }


@api_course_bp.route("", methods=["GET"])
def list_courses_catalog() -> tuple[Response, int] | Response:
    """Course catalog with pagination and filtering.

    Authentication is optional. Published courses are discoverable by everyone.
    """
    actor = get_authenticated_actor()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    q = request.args.get("q")
    category = request.args.get("category")
    difficulty = request.args.get("difficulty")
    status = request.args.get("status")

    courses, total = list_courses(
        actor=actor,
        status=status,
        category=category,
        difficulty=difficulty,
        search=q,
        page=page,
        per_page=per_page,
    )

    data = {
        "items": [_serialize_course(c) for c in courses],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
        },
    }
    return jsonify(data), 200


@api_course_bp.route("", methods=["POST"])
@instructor_required
def create_course_api() -> tuple[Response, int] | Response:
    """Create a new course (Instructor/Admin required)."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    course = create_course(actor, payload)
    return jsonify(_serialize_course(course)), 201


@api_course_bp.route("/<course_id>", methods=["GET"])
def get_course_detail_api(course_id: str) -> tuple[Response, int] | Response:
    """Read course details adhering to visibility rules."""
    actor = get_authenticated_actor()
    course = get_course_detail(actor, course_id)
    return jsonify(_serialize_course(course)), 200


@api_course_bp.route("/<course_id>", methods=["PATCH"])
@instructor_required
def update_course_api(course_id: str) -> tuple[Response, int] | Response:
    """Update editable course metadata with mass-assignment defense."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    course = update_course(actor, course_id, payload)
    return jsonify(_serialize_course(course)), 200


@api_course_bp.route("/<course_id>/publish-request", methods=["POST"])
@instructor_required
def publish_request_api(course_id: str) -> tuple[Response, int] | Response:
    """Submit course for review."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    reason = payload.get("reason")
    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="SUBMITTED_FOR_REVIEW",
        reason=reason,
    )
    return jsonify(_serialize_course(course)), 200


@api_course_bp.route("/<course_id>/archive", methods=["POST"])
@instructor_required
def archive_course_api(course_id: str) -> tuple[Response, int] | Response:
    """Archive a course."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    reason = payload.get("reason")
    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="ARCHIVED",
        reason=reason,
    )
    return jsonify(_serialize_course(course)), 200


def _serialize_lesson_summary(les: Lesson) -> dict[str, Any]:
    return {
        "lesson_id": str(les.public_id),
        "title": les.title,
        "summary": les.summary,
        "position": les.position,
        "estimated_duration_minutes": les.estimated_duration_minutes,
        "minimum_completion_seconds": les.minimum_completion_seconds,
        "viewed_fraction_required": float(les.viewed_fraction_required),
        "status": les.status,
    }


@api_course_bp.route("/<course_id>/lessons", methods=["GET"])
def get_course_lessons_api(course_id: str) -> tuple[Response, int] | Response:
    """List lessons belonging to a course scoped by caller permissions."""
    actor = get_authenticated_actor()
    lessons = get_course_lessons(actor, course_id)
    return jsonify({"lessons": [_serialize_lesson_summary(les) for les in lessons]}), 200


def _serialize_enrollment_api(e: Enrollment) -> dict[str, Any]:
    return {
        "enrollment_id": str(e.public_id),
        "course_id": str(e.course.public_id) if e.course else None,
        "course_code": e.course.course_code if e.course else None,
        "course_title": e.course.title if e.course else None,
        "student_id": str(e.student.public_id) if e.student else None,
        "status": e.status,
        "period_no": e.current_period.period_no if e.current_period else None,
        "current_progress_percent": float(e.current_progress_percent),
        "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
        "left_at": e.left_at.isoformat() if e.left_at else None,
        "detail_retention_due_at": (
            e.detail_retention_due_at.isoformat() if e.detail_retention_due_at else None
        ),
    }


def _serialize_prerequisite_api(c: Course) -> dict[str, Any]:
    return {
        "course_id": str(c.public_id),
        "course_code": c.course_code,
        "title": c.title,
        "category": c.category,
        "difficulty": c.difficulty,
        "status": c.status,
    }


@api_course_bp.route("/<course_id>/enroll", methods=["POST"])
def enroll_course_api(course_id: str) -> tuple[Response, int] | Response:
    """Enroll authenticated student into a course per 05_ENROLLMENT_PROGRESS_API.md."""
    actor = get_authenticated_actor()
    if actor is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required to enroll in course.",
                    }
                }
            ),
            401,
        )

    enrollment = enroll_student(actor=actor, course_id=course_id, session=db.session)
    db.session.commit()
    status_code = 201 if getattr(enrollment, "_is_new", False) else 200
    return jsonify(_serialize_enrollment_api(enrollment)), status_code


@api_course_bp.route("/<course_id>/leave", methods=["POST"])
def leave_course_api(course_id: str) -> tuple[Response, int] | Response:
    """Withdraw authenticated student from a course per 05_ENROLLMENT_PROGRESS_API.md."""
    actor = get_authenticated_actor()
    if actor is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required to leave course.",
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    reason = payload.get("reason")
    if reason is not None and not isinstance(reason, str):
        reason = str(reason)

    enrollment = leave_course(actor=actor, course_id=course_id, reason=reason, session=db.session)
    db.session.commit()
    return jsonify(_serialize_enrollment_api(enrollment)), 200


@api_course_bp.route("/<course_id>/re-enroll", methods=["POST"])
def re_enroll_course_api(course_id: str) -> tuple[Response, int] | Response:
    """Re-enroll in a previously left course."""
    actor = get_authenticated_actor()
    if actor is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required to re-enroll.",
                    }
                }
            ),
            401,
        )

    enrollment = re_enroll_student(actor=actor, course_id=course_id, session=db.session)
    db.session.commit()
    return jsonify(_serialize_enrollment_api(enrollment)), 200


@api_course_bp.route("/<course_id>/prerequisites", methods=["GET"])
def get_course_prerequisites_api(course_id: str) -> tuple[Response, int] | Response:
    """Read prerequisite courses for a course."""
    prereqs = get_course_prerequisites(course_id, session=db.session)
    return jsonify({"prerequisites": [_serialize_prerequisite_api(c) for c in prereqs]}), 200


@api_course_bp.route("/<course_id>/prerequisites", methods=["POST"])
@instructor_required
def add_course_prerequisite_api(course_id: str) -> tuple[Response, int] | Response:
    """Add a prerequisite course dependency (Instructor/Admin required)."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    prerequisite_course_id = payload.get("prerequisite_course_id")
    if not prerequisite_course_id:
        raise CourseValidationError("prerequisite_course_id is required.")

    link = add_course_prerequisite(
        actor=actor,
        course_id=course_id,
        prerequisite_course_id=prerequisite_course_id,
        session=db.session,
    )
    db.session.commit()
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


@api_course_bp.route("/<course_id>/prerequisites/<prereq_id>", methods=["DELETE"])
@instructor_required
def remove_course_prerequisite_api(
    course_id: str, prereq_id: str
) -> tuple[Response, int] | Response:
    """Remove a prerequisite course dependency (Instructor/Admin required)."""
    actor = get_authenticated_actor()
    assert actor is not None

    removed = remove_course_prerequisite(
        actor=actor,
        course_id=course_id,
        prerequisite_course_id=prereq_id,
        session=db.session,
    )
    db.session.commit()
    return jsonify({"removed": removed}), 200


@api_course_bp.route("/<course_id>/enrollments", methods=["GET"])
@instructor_required
def get_course_enrollments_api(course_id: str) -> tuple[Response, int] | Response:
    """List enrolled students for managed course."""
    actor = get_authenticated_actor()
    assert actor is not None

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
                "items": [_serialize_enrollment_api(e) for e in items],
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


def _serialize_completion_rule_api(course: Course, rule: Any) -> dict[str, Any]:
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


@api_course_bp.route("/<course_id>/completion-rules", methods=["GET"])
@instructor_required
def get_course_completion_rules_api(course_id: str) -> tuple[Response, int] | Response:
    """Retrieve completion rule criteria for a managed course (REST API)."""
    actor = get_authenticated_actor()
    assert actor is not None

    course = require_course_manager(actor, course_id, session=db.session)
    rule = get_or_create_default_completion_rule(course.id, session=db.session)
    return jsonify(_serialize_completion_rule_api(course, rule)), 200


@api_course_bp.route("/<course_id>/completion-rules", methods=["PUT"])
@instructor_required
def set_course_completion_rules_api(course_id: str) -> tuple[Response, int] | Response:
    """Update completion rule criteria for a managed course (REST API)."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    course = require_course_manager(actor, course_id, session=db.session)
    rule = set_course_completion_rule(
        actor=actor,
        course_id=course.id,
        payload=payload,
        session=db.session,
    )
    db.session.commit()
    return jsonify(_serialize_completion_rule_api(course, rule)), 200


@api_course_bp.route("/<course_id>/progress", methods=["GET"])
def get_course_progress_api(course_id: str) -> tuple[Response, int] | Response:
    """Read course progress for the caller or an authorized target student.

    Rules (05_ENROLLMENT_PROGRESS_API.md):
    - Self (enrolled student) can read own progress.
    - Managing instructor or Admin can read any student's progress in this course.
    - Anonymous or unauthorized callers are rejected (401/403).
    """
    actor = get_authenticated_actor()
    if actor is None or not actor.is_active:
        raise ForbiddenError("Authentication required to access progress.")

    course = _resolve_course(course_id, session=db.session)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    student_id = request.args.get("student_id")
    if student_id:
        target_student, _ = require_student_data_access(
            actor, student_id, course.id, session=db.session
        )
    else:
        target_student = actor

    enrollment = (
        db.session.query(Enrollment)
        .filter(
            Enrollment.student_user_id == target_student.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )
    if enrollment is None:
        raise ResourceNotFoundError("Enrollment record not found for this student.")

    pct = calculate_course_progress(enrollment.id, session=db.session)
    db.session.commit()

    data = {
        "course_id": str(course.public_id),
        "course_code": course.course_code,
        "student_id": str(target_student.public_id),
        "current_progress_percent": pct,
        "status": enrollment.status,
        "period_no": enrollment.current_period.period_no if enrollment.current_period else None,
        "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
        "completed_at": enrollment.completed_at.isoformat() if enrollment.completed_at else None,
    }
    return jsonify(data), 200


@api_course_bp.route("/<course_id>/questions", methods=["POST"])
@jwt_required
def create_course_question_route(course_id: str) -> tuple[Response, int] | Response:
    """Create a new Question in the course's question bank.

    POST /api/courses/<course_id>/questions
    """
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    question = create_question(actor, course_id, payload, session=db.session)
    db.session.commit()

    return jsonify(_serialize_question(question)), 201


@api_course_bp.route("/<course_id>/questions", methods=["GET"])
@jwt_required
def list_course_questions_route(course_id: str) -> tuple[Response, int] | Response:
    """List questions in course question bank with filtering and pagination.

    GET /api/courses/<course_id>/questions
    """
    actor = get_authenticated_actor()
    assert actor is not None

    page = request.args.get("page", 1, type=int)
    raw_per_page = request.args.get("per_page") or request.args.get("page_size")
    try:
        per_page = int(raw_per_page) if raw_per_page is not None else 20
    except (ValueError, TypeError):
        per_page = 20

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
        "pagination": {
            "page": p,
            "per_page": pp,
            "page_size": pp,
            "total_items": total,
            "total_pages": total_pages,
        },
    }
    return jsonify(data), 200


@api_course_bp.route("/<course_id>/assessments", methods=["POST"])
@jwt_required
def create_course_assessment_route(course_id: str) -> tuple[Response, int] | Response:
    """Create a new Assessment for a course.

    POST /api/courses/<course_id>/assessments
    """
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    assessment = create_assessment(actor, course_id, payload, session=db.session)
    db.session.commit()

    return jsonify(_serialize_assessment(assessment, full=False)), 201


@api_course_bp.route("/<course_id>/assessments", methods=["GET"])
@jwt_required
def list_course_assessments_route(course_id: str) -> tuple[Response, int] | Response:
    """List assessments for a course with pagination and filtering.

    GET /api/courses/<course_id>/assessments
    """
    actor = get_authenticated_actor()
    assert actor is not None

    page = request.args.get("page", 1, type=int)
    raw_per_page = request.args.get("per_page") or request.args.get("page_size")
    try:
        per_page = int(raw_per_page) if raw_per_page is not None else 20
    except (ValueError, TypeError):
        per_page = 20

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
        "pagination": {
            "page": p,
            "per_page": pp,
            "page_size": pp,
            "total_items": total,
            "total_pages": total_pages,
        },
    }
    return jsonify(data), 200
