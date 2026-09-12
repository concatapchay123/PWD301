"""Authorization and access control service for PWD301.

Implements:
- Role-Based Access Control (RBAC) route decorators (@require_roles, @admin_required, etc.).
- Uniform actor context resolution across Web session and JWT REST API.
- Resource/Object-level authorization to prevent Insecure Direct Object References (IDOR).
- Fail-closed enforcement for courses, lessons, questions, assessments, attempts, and student data.
- Conformance to canonical specs: 01_RBAC_MODEL.md, 02_PERMISSION_MATRIX.md,
  03_RESOURCE_AUTHORIZATION_RULES.md, 04_ADMIN_PERMISSION_RULES.md, 05_IDOR_PREVENTION.md.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import (
    abort,
    g,
    has_request_context,
    jsonify,
    redirect,
    request,
    url_for,
)
from flask_login import current_user
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import Question
from pwd301.models.types import utc_now
from pwd301.services.exceptions import (
    AdminActionForbiddenError,
    ForbiddenError,
    QuestionNotFoundError,
    ResourceNotFoundError,
    UnauthorizedError,
    ValidationError,
)


def _is_api_or_json_request() -> bool:
    """Determine whether the incoming request expects a JSON/API response."""
    if request.path == "/api" or request.path.startswith("/api/"):
        return True
    if request.is_json:
        return True
    if request.args.get("format") == "json":
        return True
    if request.accept_mimetypes.accept_html:
        return request.accept_mimetypes["application/json"] > request.accept_mimetypes["text/html"]
    return request.accept_mimetypes.accept_json


def get_authenticated_actor() -> User | None:
    """Resolve the currently authenticated User actor across both auth mechanisms.

    Checks:
    1. Bearer token in Authorization header (RFC 6750) if present in request.
       If an Authorization header is explicitly supplied, its verification is authoritative
       and will fail-closed rather than falling back to an unrelated Web session cookie.
    2. Flask `g.current_user` (set by REST API JWT middleware / @jwt_required).
    3. Flask-Login `current_user` (set by Web UI session authentication).

    Returns:
        The authenticated and active User model instance, or None if unauthenticated.
    """
    # 1. Extract and verify Bearer token from request headers if present
    if has_request_context():
        auth_header = request.headers.get("Authorization")
        if auth_header is not None:
            clean_header = auth_header.strip()
            if clean_header.lower().startswith("bearer "):
                parts = clean_header.split(None, 1)
                if len(parts) == 2 and parts[1].strip():
                    token = parts[1].strip()
                    try:
                        from pwd301.services.jwt_auth_service import verify_access_token

                        user, claims = verify_access_token(token)
                        if user and user.is_active:
                            g.current_user = user
                            g.jwt_claims = claims
                            return user
                    except Exception:
                        return None
            # If an Authorization header was supplied but invalid/malformed -> fail closed!
            return None

    # 2. JWT authentication context already resolved
    jwt_user = getattr(g, "current_user", None)
    if jwt_user is not None and isinstance(jwt_user, User) and jwt_user.is_active:
        return jwt_user

    # 3. Web session authentication context
    # Invariant: Web session cookies must NEVER authenticate requests to CSRF-exempt
    # API endpoints (/api/*) to prevent Cross-Site Request Forgery (CSRF).
    # REST API clients must supply Bearer JWT.
    if has_request_context() and (request.path == "/api" or request.path.startswith("/api/")):
        return None

    if (
        current_user
        and current_user.is_authenticated
        and isinstance(current_user, User)
        and current_user.is_active
    ):
        return current_user

    return None


def require_authenticated_actor() -> User:
    """Resolve the currently authenticated actor, raising UnauthorizedError if unauthenticated.

    This guarantees fail-closed security and avoids relying on `assert actor is not None`,
    which is removed when Python runs with optimization flags (-O).
    """
    actor = get_authenticated_actor()
    if actor is None:
        raise UnauthorizedError("Authentication required.")
    return actor


def require_roles(*role_codes: str) -> Callable[..., Any]:
    """Decorator protecting routes with Role-Based Access Control (RBAC).

    Enforces that the caller possesses at least one of the specified roles
    (accounting for the cumulative hierarchy: ADMIN > INSTRUCTOR > STUDENT).

    Behavior:
    - If unauthenticated:
        - REST API / JSON request: returns HTTP 401 Unauthorized JSON.
        - Web UI request: redirects to the login view with `next` URL.
    - If authenticated but missing required roles:
        - REST API / JSON request: returns HTTP 403 Forbidden JSON.
        - Web UI request: aborts with HTTP 403 (renders 403.html).

    Args:
        *role_codes: One or more role codes required to access the endpoint.
    """
    normalized_required = {code.strip().upper() for code in role_codes}

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            actor = get_authenticated_actor()
            correlation_id = getattr(g, "correlation_id", uuid.uuid4().hex)

            # 1. Unauthenticated check
            if actor is None:
                if _is_api_or_json_request():
                    return (
                        jsonify(
                            {
                                "error": {
                                    "code": "UNAUTHORIZED",
                                    "message": "Authentication required to access this resource.",
                                    "field_errors": {},
                                    "correlation_id": correlation_id,
                                }
                            }
                        ),
                        401,
                    )
                target_url = request.full_path.rstrip("?") if request.query_string else request.path
                return redirect(url_for("auth.login", next=target_url))

            # 2. Role authorization check
            has_permission = actor.has_any_role(*normalized_required)
            if not has_permission:
                if _is_api_or_json_request():
                    return (
                        jsonify(
                            {
                                "error": {
                                    "code": "FORBIDDEN",
                                    "message": "Access denied: insufficient role permissions.",
                                    "field_errors": {},
                                    "correlation_id": correlation_id,
                                }
                            }
                        ),
                        403,
                    )
                abort(403)

            return f(*args, **kwargs)

        return decorated

    return decorator


def admin_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Shorthand decorator requiring the ADMIN role."""
    return require_roles("ADMIN")(f)


def instructor_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Shorthand decorator requiring INSTRUCTOR or ADMIN role."""
    return require_roles("INSTRUCTOR", "ADMIN")(f)


def student_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Shorthand decorator requiring an authenticated user (STUDENT, INSTRUCTOR, or ADMIN)."""
    return require_roles("STUDENT", "INSTRUCTOR", "ADMIN")(f)


# ==============================================================================
# Resource Resolvers (Opaque Public ID or Internal BigInt PK)
# ==============================================================================


def _resolve_course(
    course_or_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Course | None:
    """Resolve a Course instance from model or identifier."""
    if isinstance(course_or_id, Course):
        return course_or_id

    sess = session if session is not None else db.session
    if isinstance(course_or_id, int):
        return sess.get(Course, course_or_id)

    if isinstance(course_or_id, uuid.UUID):
        return sess.query(Course).filter(Course.public_id == course_or_id).first()

    if isinstance(course_or_id, str):
        try:
            val_uuid = uuid.UUID(course_or_id)
            return sess.query(Course).filter(Course.public_id == val_uuid).first()
        except ValueError:
            pass
        if course_or_id.isdigit():
            return sess.get(Course, int(course_or_id))

    return None


def _resolve_user(
    user_or_id: User | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> User | None:
    """Resolve a User instance from model or identifier."""
    if isinstance(user_or_id, User):
        return user_or_id

    sess = session if session is not None else db.session
    if isinstance(user_or_id, int):
        return sess.get(User, user_or_id)

    if isinstance(user_or_id, uuid.UUID):
        return sess.query(User).filter(User.public_id == user_or_id).first()

    if isinstance(user_or_id, str):
        try:
            val_uuid = uuid.UUID(user_or_id)
            return sess.query(User).filter(User.public_id == val_uuid).first()
        except ValueError:
            pass
        if user_or_id.isdigit():
            return sess.get(User, int(user_or_id))

    return None


def _resolve_lesson(
    lesson_or_id: Lesson | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Lesson | None:
    """Resolve a Lesson instance from model or identifier."""
    if isinstance(lesson_or_id, Lesson):
        return lesson_or_id

    sess = session if session is not None else db.session
    if isinstance(lesson_or_id, int):
        return sess.get(Lesson, lesson_or_id)

    if isinstance(lesson_or_id, uuid.UUID):
        return sess.query(Lesson).filter(Lesson.public_id == lesson_or_id).first()

    if isinstance(lesson_or_id, str):
        try:
            val_uuid = uuid.UUID(lesson_or_id)
            return sess.query(Lesson).filter(Lesson.public_id == val_uuid).first()
        except ValueError:
            pass
        if lesson_or_id.isdigit():
            return sess.get(Lesson, int(lesson_or_id))

    return None


def _resolve_question(
    question_or_id: Question | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Question | None:
    """Resolve a Question instance from model or identifier."""
    if isinstance(question_or_id, Question):
        return question_or_id

    sess = session if session is not None else db.session
    if isinstance(question_or_id, int):
        return sess.get(Question, question_or_id)

    if isinstance(question_or_id, uuid.UUID):
        return sess.query(Question).filter(Question.public_id == question_or_id).first()

    if isinstance(question_or_id, str):
        try:
            val_uuid = uuid.UUID(question_or_id)
            return sess.query(Question).filter(Question.public_id == val_uuid).first()
        except ValueError:
            pass
        if question_or_id.isdigit():
            return sess.get(Question, int(question_or_id))

    return None


def _resolve_assessment(
    assessment_or_id: Assessment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Assessment | None:
    """Resolve an Assessment instance from model or identifier."""
    if isinstance(assessment_or_id, Assessment):
        return assessment_or_id

    sess = session if session is not None else db.session
    if isinstance(assessment_or_id, int):
        return sess.get(Assessment, assessment_or_id)

    if isinstance(assessment_or_id, uuid.UUID):
        return sess.query(Assessment).filter(Assessment.public_id == assessment_or_id).first()

    if isinstance(assessment_or_id, str):
        try:
            val_uuid = uuid.UUID(assessment_or_id)
            return sess.query(Assessment).filter(Assessment.public_id == val_uuid).first()
        except ValueError:
            pass
        if assessment_or_id.isdigit():
            return sess.get(Assessment, int(assessment_or_id))

    return None


def _resolve_attempt(
    attempt_or_id: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> AssessmentAttempt | None:
    """Resolve an AssessmentAttempt instance from model or identifier."""
    if isinstance(attempt_or_id, AssessmentAttempt):
        return attempt_or_id

    sess = session if session is not None else db.session
    if isinstance(attempt_or_id, int):
        return sess.get(AssessmentAttempt, attempt_or_id)

    if isinstance(attempt_or_id, uuid.UUID):
        return (
            sess.query(AssessmentAttempt)
            .filter(AssessmentAttempt.public_id == attempt_or_id)
            .first()
        )

    if isinstance(attempt_or_id, str):
        try:
            val_uuid = uuid.UUID(attempt_or_id)
            return (
                sess.query(AssessmentAttempt)
                .filter(AssessmentAttempt.public_id == val_uuid)
                .first()
            )
        except ValueError:
            pass
        if attempt_or_id.isdigit():
            return sess.get(AssessmentAttempt, int(attempt_or_id))

    return None


# ==============================================================================
# Resource Authorization Predicates
# ==============================================================================


def can_view_course(
    user: User | None,
    course_or_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Determine whether an actor can view course details.

    Rules (03_RESOURCE_AUTHORIZATION_RULES.md):
    - PUBLISHED courses: viewable by anyone (including anonymous/students).
    - DRAFT / ARCHIVED courses: viewable only by ADMIN or the course owner instructor.
    - Soft-deleted courses: viewable only by ADMIN.
    """
    course = _resolve_course(course_or_id, session=session)
    if course is None:
        return False

    if course.deleted_at is not None:
        return user is not None and user.is_active and user.is_admin

    if course.status == "PUBLISHED":
        return True

    if user is None or not user.is_active:
        return False

    if user.is_admin:
        return True

    return bool(user.has_role("INSTRUCTOR") and course.owner_instructor_id == user.id)


def can_manage_course(
    user: User | None,
    course_or_id: Course | int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Determine whether an actor can edit, update, or manage a course.

    Rules (02_PERMISSION_MATRIX.md & 04_ADMIN_PERMISSION_RULES.md):
    - Admin is authorized platform-wide (sensitive edits may require audit reason).
    - Instructors may manage only courses they currently own (owner_instructor_id == user.id).
    - Other instructors or students are denied.
    """
    if user is None or not user.is_active:
        return False

    course = _resolve_course(course_or_id, session=session)
    if course is None:
        return False

    if course.deleted_at is not None:
        return user.is_admin

    if user.is_admin:
        return True

    return bool(user.has_role("INSTRUCTOR") and course.owner_instructor_id == user.id)


def can_access_student_data(
    user: User | None,
    student_or_id: User | int | uuid.UUID | str,
    course_or_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Determine whether an actor can access a student's data within a course.

    Invariants enforced (AGENTS.md & 02_PERMISSION_MATRIX.md):
    - "Instructors may manage current student data only for Courses they currently manage."
    - Students can access only their OWN data (user.id == student.id).
    - Admin has platform-wide oversight.
    - An instructor cannot view student data for courses owned by other instructors.
    - The student must actually have an Enrollment in the specified course.
    """
    if user is None or not user.is_active:
        return False

    sess = session if session is not None else db.session
    student = _resolve_user(student_or_id, session=sess)
    course = _resolve_course(course_or_id, session=sess)

    if student is None or course is None:
        return False

    # 1. Student accessing own data
    if user.id == student.id:
        return True

    # 2. Admin platform oversight
    if user.is_admin:
        return True

    # 3. Instructor managing this course and student is enrolled
    if user.has_role("INSTRUCTOR") and course.owner_instructor_id == user.id:
        # Check active or historical enrollment in this course
        enrollment = (
            sess.query(Enrollment)
            .filter(
                Enrollment.student_user_id == student.id,
                Enrollment.course_id == course.id,
            )
            .first()
        )
        return enrollment is not None

    return False


def can_manage_lesson(
    user: User | None,
    lesson_or_id: Lesson | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Determine whether an actor can manage a lesson (delegates to parent Course)."""
    lesson = _resolve_lesson(lesson_or_id, session=session)
    if lesson is None:
        return False
    return can_manage_course(user, lesson.course_id, session=session)


def can_manage_question(
    user: User | None,
    question_or_id: Question | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Determine whether an actor can manage a question (delegates to parent Course)."""
    question = _resolve_question(question_or_id, session=session)
    if question is None:
        return False
    return can_manage_course(user, question.course_id, session=session)


def can_manage_assessment(
    user: User | None,
    assessment_or_id: Assessment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Determine whether an actor can manage an assessment (delegates to parent Course)."""
    assessment = _resolve_assessment(assessment_or_id, session=session)
    if assessment is None:
        return False
    return can_manage_course(user, assessment.course_id, session=session)


def can_access_attempt(
    user: User | None,
    attempt_or_id: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Determine whether an actor can view an assessment attempt.

    Rules:
    - The student who took the attempt can view their own attempt.
    - The managing instructor of the course containing the assessment can view it
      (requires INSTRUCTOR role).
    - Admin can view it.
    - Other instructors or students are denied.
    """
    if user is None or not user.is_active:
        return False

    sess = session if session is not None else db.session
    attempt = _resolve_attempt(attempt_or_id, session=sess)
    if attempt is None:
        return False

    # Own attempt
    if attempt.student_user_id == user.id:
        return True

    # Admin oversight
    if user.is_admin:
        return True

    # Course manager (must possess INSTRUCTOR role per Layer 1 RBAC)
    if user.has_role("INSTRUCTOR"):
        assessment = sess.get(Assessment, attempt.assessment_id)
        if assessment is not None:
            course = sess.get(Course, assessment.course_id)
            if course is not None and course.owner_instructor_id == user.id:
                return True

    return False


def can_submit_attempt(
    user: User | None,
    attempt_or_id: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Determine whether an actor can save answers or submit an assessment attempt.

    NON-NEGOTIABLE INVARIANT (02_PERMISSION_MATRIX.md):
    - "Attempt answer save/submit: Own only"
    - ONLY the student who owns the attempt may save answers or submit.
    - Even Admins or Instructors are strictly forbidden from submitting on behalf of a student.
    """
    if user is None or not user.is_active:
        return False

    attempt = _resolve_attempt(attempt_or_id, session=session)
    if attempt is None:
        return False

    return attempt.student_user_id == user.id


def can_grade_attempt(
    user: User | None,
    attempt_or_id: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Determine whether an actor can grade an attempt (manual essay scoring).

    Authorized actors:
    - Managing Instructor of the course (must possess INSTRUCTOR role per Layer 1 RBAC).
    - Admin.
    """
    if user is None or not user.is_active:
        return False

    sess = session if session is not None else db.session
    attempt = _resolve_attempt(attempt_or_id, session=sess)
    if attempt is None:
        return False

    if user.is_admin:
        return True

    if user.has_role("INSTRUCTOR"):
        assessment = sess.get(Assessment, attempt.assessment_id)
        if assessment is not None:
            course = sess.get(Course, assessment.course_id)
            if course is not None and course.owner_instructor_id == user.id:
                return True

    return False


# ==============================================================================
# Enforcement / Assertion Helpers (Fail-Closed, Raising Exceptions)
# ==============================================================================


def require_course_manager(
    user: User,
    course_or_id: Course | int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Course:
    """Enforce that the user is authorized to manage the specified course.

    Returns:
        The verified Course instance.

    Raises:
        ResourceNotFoundError: If the course does not exist.
        ForbiddenError: If the user lacks management permissions.
    """
    sess = session if session is not None else db.session
    course = _resolve_course(course_or_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    if not can_manage_course(user, course, reason=reason, session=sess):
        raise ForbiddenError("You do not have permission to manage this course.")

    return course


def require_student_data_access(
    user: User,
    student_or_id: User | int | uuid.UUID | str,
    course_or_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[User, Course]:
    """Enforce that the user is authorized to access the student's data for this course.

    Returns:
        Tuple of (student_user, course).

    Raises:
        ResourceNotFoundError: If student or course does not exist.
        ForbiddenError: If the user is not permitted to view this student data.
    """
    sess = session if session is not None else db.session
    student = _resolve_user(student_or_id, session=sess)
    if student is None:
        raise ResourceNotFoundError("Student not found.")

    course = _resolve_course(course_or_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    if not can_access_student_data(user, student, course, session=sess):
        raise ForbiddenError("You do not have permission to access this student's data.")

    return student, course


def require_attempt_access(
    user: User,
    attempt_or_id: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> AssessmentAttempt:
    """Enforce that the user can view the assessment attempt.

    Returns:
        The verified AssessmentAttempt instance.

    Raises:
        ResourceNotFoundError: If the attempt does not exist.
        ForbiddenError: If the user is not authorized to view the attempt.
    """
    sess = session if session is not None else db.session
    attempt = _resolve_attempt(attempt_or_id, session=sess)
    if attempt is None:
        raise ResourceNotFoundError("Assessment attempt not found.")

    if not can_access_attempt(user, attempt, session=sess):
        raise ForbiddenError("You do not have permission to access this assessment attempt.")

    return attempt


def require_attempt_submission_owner(
    user: User,
    attempt_or_id: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> AssessmentAttempt:
    """Enforce that ONLY the student owner is saving answers or submitting the attempt.

    Returns:
        The verified AssessmentAttempt instance.

    Raises:
        ResourceNotFoundError: If attempt does not exist.
        ForbiddenError: If caller is not the student owner.
    """
    sess = session if session is not None else db.session
    attempt = _resolve_attempt(attempt_or_id, session=sess)
    if attempt is None:
        raise ResourceNotFoundError("Assessment attempt not found.")

    if not can_submit_attempt(user, attempt, session=sess):
        raise ForbiddenError("Only the student owner can save answers or submit this attempt.")

    return attempt


def require_question_manager(
    user: User,
    question_or_id: Question | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Question:
    """Enforce that the user is authorized to manage the specified question.

    Returns:
        The verified Question instance.

    Raises:
        QuestionNotFoundError: If question does not exist.
        ForbiddenError: If user lacks management permissions.
    """
    sess = session if session is not None else db.session
    question = _resolve_question(question_or_id, session=sess)
    if question is None:
        raise QuestionNotFoundError("Question not found.")

    if not can_manage_question(user, question, session=sess):
        raise ForbiddenError("You do not have permission to manage this question.")

    return question


# ==============================================================================
# Parent-Child Consistency Validation & Enforcement (05_IDOR_PREVENTION.md)
# ==============================================================================


def check_lesson_course_consistency(
    lesson_or_id: Lesson | int | uuid.UUID | str,
    course_or_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Verify that a Lesson belongs to the specified Course (Parent-Child Consistency)."""
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_or_id, session=sess)
    course = _resolve_course(course_or_id, session=sess)
    if lesson is None or course is None:
        return False
    return lesson.course_id == course.id


def check_question_course_consistency(
    question_or_id: Question | int | uuid.UUID | str,
    course_or_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Verify that a Question belongs to the specified Course (Parent-Child Consistency)."""
    sess = session if session is not None else db.session
    question = _resolve_question(question_or_id, session=sess)
    course = _resolve_course(course_or_id, session=sess)
    if question is None or course is None:
        return False
    return question.course_id == course.id


def check_assessment_course_consistency(
    assessment_or_id: Assessment | int | uuid.UUID | str,
    course_or_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Verify that an Assessment belongs to the specified Course (Parent-Child Consistency)."""
    sess = session if session is not None else db.session
    assessment = _resolve_assessment(assessment_or_id, session=sess)
    course = _resolve_course(course_or_id, session=sess)
    if assessment is None or course is None:
        return False
    return assessment.course_id == course.id


def check_attempt_consistency(
    attempt_or_id: AssessmentAttempt | int | uuid.UUID | str,
    assessment_or_id: Assessment | int | uuid.UUID | str | None = None,
    student_or_id: User | int | uuid.UUID | str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Verify that an AssessmentAttempt belongs to the specified Assessment and Student."""
    sess = session if session is not None else db.session
    attempt = _resolve_attempt(attempt_or_id, session=sess)
    if attempt is None:
        return False

    if assessment_or_id is not None:
        assessment = _resolve_assessment(assessment_or_id, session=sess)
        if assessment is None or attempt.assessment_id != assessment.id:
            return False

    if student_or_id is not None:
        student = _resolve_user(student_or_id, session=sess)
        if student is None or attempt.student_user_id != student.id:
            return False

    return True


def require_lesson_course_consistency(
    lesson_or_id: Lesson | int | uuid.UUID | str,
    course_or_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[Lesson, Course]:
    """Enforce that a Lesson belongs to the specified Course.

    Raises:
        ResourceNotFoundError: If lesson or course not found.
        ForbiddenError: If lesson does not belong to course (IDOR mismatch).
    """
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_or_id, session=sess)
    if lesson is None:
        raise ResourceNotFoundError("Lesson not found.")
    course = _resolve_course(course_or_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    if lesson.course_id != course.id:
        raise ForbiddenError("Lesson does not belong to the specified course.")

    return lesson, course


def require_question_course_consistency(
    question_or_id: Question | int | uuid.UUID | str,
    course_or_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[Question, Course]:
    """Enforce that a Question belongs to the specified Course.

    Raises:
        QuestionNotFoundError: If question not found.
        ResourceNotFoundError: If course not found.
        ForbiddenError: If question does not belong to course (IDOR mismatch).
    """
    sess = session if session is not None else db.session
    question = _resolve_question(question_or_id, session=sess)
    if question is None:
        raise QuestionNotFoundError("Question not found.")
    course = _resolve_course(course_or_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    if question.course_id != course.id:
        raise ForbiddenError("Question does not belong to the specified course.")

    return question, course


def require_assessment_course_consistency(
    assessment_or_id: Assessment | int | uuid.UUID | str,
    course_or_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[Assessment, Course]:
    """Enforce that an Assessment belongs to the specified Course.

    Raises:
        ResourceNotFoundError: If assessment or course not found.
        ForbiddenError: If assessment does not belong to course (IDOR mismatch).
    """
    sess = session if session is not None else db.session
    assessment = _resolve_assessment(assessment_or_id, session=sess)
    if assessment is None:
        raise ResourceNotFoundError("Assessment not found.")
    course = _resolve_course(course_or_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    if assessment.course_id != course.id:
        raise ForbiddenError("Assessment does not belong to the specified course.")

    return assessment, course


def require_attempt_consistency(
    attempt_or_id: AssessmentAttempt | int | uuid.UUID | str,
    assessment_or_id: Assessment | int | uuid.UUID | str | None = None,
    student_or_id: User | int | uuid.UUID | str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> AssessmentAttempt:
    """Enforce that an AssessmentAttempt belongs to the specified Assessment and Student.

    Raises:
        ResourceNotFoundError: If attempt, assessment, or student not found.
        ForbiddenError: If attempt does not match assessment or student (IDOR mismatch).
    """
    sess = session if session is not None else db.session
    attempt = _resolve_attempt(attempt_or_id, session=sess)
    if attempt is None:
        raise ResourceNotFoundError("Assessment attempt not found.")

    if assessment_or_id is not None:
        assessment = _resolve_assessment(assessment_or_id, session=sess)
        if assessment is None:
            raise ResourceNotFoundError("Assessment not found.")
        if attempt.assessment_id != assessment.id:
            raise ForbiddenError("Attempt does not belong to the specified assessment.")

    if student_or_id is not None:
        student = _resolve_user(student_or_id, session=sess)
        if student is None:
            raise ResourceNotFoundError("Student not found.")
        if attempt.student_user_id != student.id:
            raise ForbiddenError("Attempt does not belong to the specified student.")

    return attempt


# ==============================================================================
# Admin Permission Rules Enforcement (04_ADMIN_PERMISSION_RULES.md)
# ==============================================================================


def record_admin_intervention(
    admin: User,
    owner_instructor_id: int,
    resource_type: str,
    resource_id: int,
    action: str,
    reason: str,
    session: Session | scoped_session[Any] | None = None,
) -> AuditEvent:
    """Record an administrative intervention on an instructor-owned resource.

    Enforces 04_ADMIN_PERMISSION_RULES.md:
    - Admin edits to instructor resources require non-empty justification reason.
    - Persists append-only AuditEvent with performed_as_admin=True.
    - Dispatches in-app notification to the owner instructor.

    Args:
        admin: The administrator performing the intervention.
        owner_instructor_id: User ID of the instructor owning the resource.
        resource_type: Type of resource (e.g. 'COURSE', 'QUESTION', 'ASSESSMENT').
        resource_id: Primary key of the affected resource.
        action: Specific administrative action (e.g. 'UPDATE', 'DELETE', 'PUBLISH').
        reason: Mandatory justification provided by the administrator.
        session: Optional SQLAlchemy session.

    Returns:
        The newly created AuditEvent.

    Raises:
        AdminActionForbiddenError: If caller is not an administrator.
        ValidationError: If justification reason is empty.
    """
    if not admin.is_admin:
        raise AdminActionForbiddenError(
            "Only administrators are permitted to perform administrative interventions."
        )

    clean_reason = (reason or "").strip()
    if not clean_reason:
        raise ValidationError(
            "Administrative intervention requires a mandatory justification reason."
        )

    sess = session if session is not None else db.session
    now = utc_now()

    audit_entry = AuditEvent(
        actor_user_id=admin.id,
        actor_roles_snapshot=",".join(sorted(admin.role_codes)),
        action=f"ADMIN_OVERRIDE_{action.upper()}",
        target_type=resource_type.upper(),
        target_id=resource_id,
        reason=clean_reason,
        performed_as_admin=True,
        created_at=now,
    )
    sess.add(audit_entry)

    # Notify instructor
    try:
        from pwd301.services.notification_service import dispatch_notification

        with sess.begin_nested():
            dispatch_notification(
                recipient_user=owner_instructor_id,
                event_type="SYSTEM_ADMIN_INTERVENTION",
                title=f"Quản trị viên can thiệp: {resource_type}",
                body=(
                    f"Quản trị viên đã thực hiện thao tác '{action}' trên "
                    f"{resource_type} (ID {resource_id}). Lý do: {clean_reason}"
                ),
                category="SYSTEM",
                session=sess,
            )
    except Exception:
        pass

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return audit_entry


def record_admin_student_detail_access(
    admin: User,
    student_id: int,
    course_id: int,
    reason: str,
    session: Session | scoped_session[Any] | None = None,
) -> AuditEvent:
    """Record admin inspection of individual student details with mandatory justification.

    Enforces 04_ADMIN_PERMISSION_RULES.md (Student result inspection requires reason).

    Args:
        admin: The administrator inspecting the student data.
        student_id: Primary key of the student whose details are accessed.
        course_id: Primary key of the course context.
        reason: Mandatory justification reason.
        session: Optional SQLAlchemy session.

    Returns:
        The created AuditEvent.

    Raises:
        AdminActionForbiddenError: If caller is not Admin.
        ValidationError: If reason is missing or empty.
    """
    if not admin.is_admin:
        raise AdminActionForbiddenError(
            "Only administrators are permitted to record admin student inspections."
        )

    clean_reason = (reason or "").strip()
    if not clean_reason:
        raise ValidationError(
            "Reason is required when administrators inspect detailed individual student data."
        )

    sess = session if session is not None else db.session
    now = utc_now()

    audit_entry = AuditEvent(
        actor_user_id=admin.id,
        actor_roles_snapshot=",".join(sorted(admin.role_codes)),
        action="ADMIN_INSPECT_STUDENT_DETAIL",
        target_type="STUDENT",
        target_id=student_id,
        reason=clean_reason,
        performed_as_admin=True,
        created_at=now,
    )
    sess.add(audit_entry)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return audit_entry
