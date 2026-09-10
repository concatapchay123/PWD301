"""Analytics and learning performance optimization engine for PWD301.

Implements high-performance database-level analytical queries:
- get_admin_system_overview: System-wide counts of users by role/status, courses by status,
  enrollments, assessment submissions, pending grading essays, and storage safety.
- get_instructor_overview_analytics: Aggregate multi-course statistics for instructors.
- get_instructor_course_analytics: Course-level enrollment metrics, completion rate,
  average progress, 4-bucket progress distribution, and assessment performance breakdown.
- get_student_learning_overview: Student personal dashboard metrics, active/completed counts,
  overall progress, server-synchronized upcoming assessment deadlines, and published results.

Invariants enforced:
- O(1) query complexity using database aggregation (COUNT, AVG, SUM, CASE, GROUP BY).
- Zero-division resilience (safely handles empty courses, 0 students, 0 submissions).
- ADR-002 Zero Internal PK Leakage: Exclusively public UUIDs are exposed externally.
- Strict object-level authorization & IDOR defense (require_course_manager, fail-closed).
"""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session, scoped_session

from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AssessmentResult,
)
from pwd301.models.course import Course, Enrollment
from pwd301.models.file_import import FileBlob, FileRevision
from pwd301.models.identity import Role, User, UserRole
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import (
    require_course_manager,
)
from pwd301.services.exceptions import (
    ForbiddenError,
    UnauthorizedError,
)


def _ensure_utc(dt: datetime.datetime | None) -> datetime.datetime | None:
    """Ensure datetime has UTC timezone for safe comparison."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.UTC)
    return dt


def get_admin_system_overview(
    actor: User,
    session: Session | scoped_session[Any],
) -> dict[str, Any]:
    """Retrieve platform-wide operational and learning metrics for Administrators.

    Authorization:
    - Strictly requires ADMIN role. Raises ForbiddenError otherwise.

    Returns:
        JSON-compliant dictionary containing system user counts by role/status,
        courses distribution, enrollments, assessment grading queue, and storage stats.
    """
    if not actor.is_admin:
        raise ForbiddenError("Administrator access required for system analytics.")

    sess = session

    # 1. Total and status breakdown for users
    user_status_row = sess.query(
        func.count(User.id).label("total"),
        func.count(
            case(
                (
                    and_(
                        User.status == "ACTIVE",
                        User.suspended_at.is_(None),
                        User.email_verified_at.isnot(None),
                    ),
                    1,
                )
            )
        ).label("active"),
        func.count(
            case(
                (
                    or_(
                        User.status == "SUSPENDED",
                        User.suspended_at.isnot(None),
                    ),
                    1,
                )
            )
        ).label("suspended"),
        func.count(
            case(
                (
                    and_(
                        User.email_verified_at.is_(None),
                        User.status == "ACTIVE",
                        User.suspended_at.is_(None),
                    ),
                    1,
                )
            )
        ).label("pending_verification"),
    ).one()

    total_users = int(user_status_row.total or 0)
    by_status = {
        "ACTIVE": int(user_status_row.active or 0),
        "SUSPENDED": int(user_status_row.suspended or 0),
        "PENDING_VERIFICATION": int(user_status_row.pending_verification or 0),
    }

    # 2. Users by role breakdown
    role_rows = (
        sess.query(Role.code, func.count(UserRole.user_id))
        .join(UserRole, Role.id == UserRole.role_id)
        .group_by(Role.code)
        .all()
    )
    by_role = {"STUDENT": 0, "INSTRUCTOR": 0, "ADMIN": 0}
    for code, cnt in role_rows:
        if code in by_role:
            by_role[code] = int(cnt)

    # 3. Courses distribution by status
    course_status_rows = (
        sess.query(Course.status, func.count(Course.id)).group_by(Course.status).all()
    )
    courses_by_status: dict[str, int] = {
        "DRAFT": 0,
        "SUBMITTED_FOR_REVIEW": 0,
        "APPROVED": 0,
        "PUBLISHED": 0,
        "ARCHIVED": 0,
        "TRASH": 0,
    }
    for st, cnt in course_status_rows:
        courses_by_status[st] = int(cnt)
    total_courses = sum(courses_by_status.values())

    # 4. Enrollments statistics
    enr_row = sess.query(
        func.count(Enrollment.id).label("total"),
        func.count(case((Enrollment.status == "ACTIVE", 1))).label("active"),
        func.count(case((Enrollment.status == "COMPLETED", 1))).label("completed"),
    ).one()
    total_enrollments = int(enr_row.total or 0)
    active_enrollments = int(enr_row.active or 0)
    completed_enrollments = int(enr_row.completed or 0)

    # 5. Assessment attempts & grading queue
    att_row = sess.query(
        func.count(case((AssessmentAttempt.submitted_at.isnot(None), 1))).label("submitted"),
        func.count(case((AssessmentAttempt.status == "PENDING_GRADING", 1))).label("needs_grading"),
    ).one()
    total_submissions = int(att_row.submitted or 0)
    needs_grading_count = int(att_row.needs_grading or 0)

    # 6. File storage and security scan statistics
    total_storage_bytes = int(
        sess.query(func.coalesce(func.sum(FileBlob.size_bytes), 0))
        .filter(FileBlob.deleted_at.is_(None))
        .scalar()
        or 0
    )
    file_rev_row = sess.query(
        func.count(case((FileRevision.status.in_(["ACTIVE", "SAFE"]), 1))).label("clean"),
        func.count(case((FileRevision.status.in_(["QUARANTINED", "REJECTED"]), 1))).label(
            "quarantined"
        ),
    ).one()
    clean_files_count = int(file_rev_row.clean or 0)
    quarantined_files_count = int(file_rev_row.quarantined or 0)

    now = utc_now()
    return {
        "admin_id": str(actor.public_id),
        "admin_name": actor.display_name,
        "total_users": total_users,
        "total_courses": total_courses,
        "users": {
            "total_users": total_users,
            "by_role": by_role,
            "by_status": by_status,
        },
        "courses": {
            "total_courses": total_courses,
            "by_status": courses_by_status,
        },
        "enrollments": {
            "total_enrollments": total_enrollments,
            "active_enrollments": active_enrollments,
            "completed_enrollments": completed_enrollments,
        },
        "assessments": {
            "total_submissions": total_submissions,
            "needs_grading_count": needs_grading_count,
        },
        "storage": {
            "total_bytes": total_storage_bytes,
            "clean_files_count": clean_files_count,
            "quarantined_files_count": quarantined_files_count,
        },
        "generated_at": now.isoformat(),
    }


def get_instructor_overview_analytics(
    actor: User,
    session: Session | scoped_session[Any],
) -> dict[str, Any]:
    """Retrieve multi-course teaching analytics overview for Instructors.

    Authorization:
    - Requires INSTRUCTOR or ADMIN role. Raises ForbiddenError otherwise.

    Returns:
        Summary of managed courses, total enrolled students, completion and progress metrics,
        and essay grading workload.
    """
    if not (actor.has_role("INSTRUCTOR") or actor.is_admin):
        raise ForbiddenError("Instructor access required.")

    sess = session

    # Resolve managed courses
    if actor.is_admin:
        courses = (
            sess.query(Course)
            .filter(Course.deleted_at.is_(None))
            .order_by(Course.created_at.desc())
            .all()
        )
    else:
        courses = (
            sess.query(Course)
            .filter(
                Course.owner_instructor_id == actor.id,
                Course.deleted_at.is_(None),
            )
            .order_by(Course.created_at.desc())
            .all()
        )

    now = utc_now()
    managed_courses_count = len(courses)
    if managed_courses_count == 0:
        return {
            "instructor_id": str(actor.public_id),
            "instructor_name": actor.display_name,
            "managed_courses_count": 0,
            "total_students_count": 0,
            "active_enrollments_count": 0,
            "completed_enrollments_count": 0,
            "average_progress_percent": 0.0,
            "pending_grading_count": 0,
            "courses": [],
            "generated_at": now.isoformat(),
        }

    course_ids = [c.id for c in courses]

    # Global enrollment aggregates for managed courses
    enr_stats = (
        sess.query(
            func.count(Enrollment.id).label("total_students"),
            func.count(case((Enrollment.status == "ACTIVE", 1))).label("active"),
            func.count(case((Enrollment.status == "COMPLETED", 1))).label("completed"),
            func.coalesce(func.avg(Enrollment.current_progress_percent), 0.0).label("avg_progress"),
        )
        .filter(Enrollment.course_id.in_(course_ids))
        .one()
    )

    total_students_count = int(enr_stats.total_students or 0)
    active_enrollments_count = int(enr_stats.active or 0)
    completed_enrollments_count = int(enr_stats.completed or 0)
    overall_avg_progress = round(float(enr_stats.avg_progress or 0.0), 2)

    # Pending essay grading count across managed courses
    pending_grading_count = int(
        sess.query(func.count(AssessmentAttempt.id))
        .join(Assessment, AssessmentAttempt.assessment_id == Assessment.id)
        .filter(
            Assessment.course_id.in_(course_ids),
            AssessmentAttempt.status == "PENDING_GRADING",
        )
        .scalar()
        or 0
    )

    # Per-course summaries (single grouped query)
    course_enr_rows = (
        sess.query(
            Enrollment.course_id,
            func.count(Enrollment.id).label("enrolled_count"),
            func.count(case((Enrollment.status == "COMPLETED", 1))).label("completed_count"),
            func.coalesce(func.avg(Enrollment.current_progress_percent), 0.0).label("avg_progress"),
        )
        .filter(Enrollment.course_id.in_(course_ids))
        .group_by(Enrollment.course_id)
        .all()
    )
    enr_by_course: dict[int, dict[str, Any]] = {
        row.course_id: {
            "enrolled_count": int(row.enrolled_count),
            "completed_count": int(row.completed_count),
            "avg_progress": float(row.avg_progress),
        }
        for row in course_enr_rows
    }

    courses_data: list[dict[str, Any]] = []
    for c in courses:
        c_stat = enr_by_course.get(
            c.id,
            {"enrolled_count": 0, "completed_count": 0, "avg_progress": 0.0},
        )
        enrolled_c = c_stat["enrolled_count"]
        comp_rate = (
            round((c_stat["completed_count"] / enrolled_c) * 100.0, 2) if enrolled_c > 0 else 0.0
        )
        courses_data.append(
            {
                "course_id": str(c.public_id),
                "course_code": c.course_code,
                "title": c.title,
                "status": c.status,
                "capacity": c.capacity,
                "enrolled_count": enrolled_c,
                "completion_rate_percent": comp_rate,
                "average_progress_percent": round(c_stat["avg_progress"], 2),
                "created_at": c.created_at.isoformat(),
            }
        )

    return {
        "instructor_id": str(actor.public_id),
        "instructor_name": actor.display_name,
        "managed_courses_count": managed_courses_count,
        "total_students_count": total_students_count,
        "active_enrollments_count": active_enrollments_count,
        "completed_enrollments_count": completed_enrollments_count,
        "average_progress_percent": overall_avg_progress,
        "pending_grading_count": pending_grading_count,
        "courses": courses_data,
        "generated_at": now.isoformat(),
    }


def get_instructor_course_analytics(
    actor: User,
    course_id: str,
    session: Session | scoped_session[Any],
) -> dict[str, Any]:
    """Retrieve detailed learning performance report for a single Course.

    Authorization:
    - Enforced via require_course_manager:
      - Instructor managing this course -> Granted.
      - Administrator -> Granted.
      - Instructor managing other course -> HTTP 403 Forbidden (Strict IDOR Defense).
      - Student/Guest -> HTTP 403 Forbidden.

    Returns:
        Course enrollment counts, completion rate, average progress, 4-bucket
        progress distribution, and assessment evaluation breakdown.
    """
    sess = session
    course = require_course_manager(actor, course_id, session=sess)

    # 1. Course Enrollment Aggregates
    enr_stats = (
        sess.query(
            func.count(Enrollment.id).label("total_enrolled"),
            func.count(case((Enrollment.status == "ACTIVE", 1))).label("active_enrolled"),
            func.count(case((Enrollment.status == "COMPLETED", 1))).label("completed_enrolled"),
            func.coalesce(func.avg(Enrollment.current_progress_percent), 0.0).label("avg_progress"),
        )
        .filter(Enrollment.course_id == course.id)
        .one()
    )

    total_enrolled = int(enr_stats.total_enrolled or 0)
    active_enrolled = int(enr_stats.active_enrolled or 0)
    completed_enrolled = int(enr_stats.completed_enrolled or 0)
    avg_progress = round(float(enr_stats.avg_progress or 0.0), 2)

    # Zero-division resilience for completion rate
    completion_rate = (
        round((completed_enrolled / total_enrolled) * 100.0, 2) if total_enrolled > 0 else 0.0
    )

    # 2. Progress Distribution Buckets: [0-25), [25-50), [50-75), [75-100]
    bucket_stats = (
        sess.query(
            func.count(
                case(
                    (
                        and_(
                            Enrollment.current_progress_percent >= 0,
                            Enrollment.current_progress_percent < 25,
                        ),
                        1,
                    )
                )
            ).label("b_0_25"),
            func.count(
                case(
                    (
                        and_(
                            Enrollment.current_progress_percent >= 25,
                            Enrollment.current_progress_percent < 50,
                        ),
                        1,
                    )
                )
            ).label("b_25_50"),
            func.count(
                case(
                    (
                        and_(
                            Enrollment.current_progress_percent >= 50,
                            Enrollment.current_progress_percent < 75,
                        ),
                        1,
                    )
                )
            ).label("b_50_75"),
            func.count(
                case(
                    (
                        Enrollment.current_progress_percent >= 75,
                        1,
                    )
                )
            ).label("b_75_100"),
        )
        .filter(
            Enrollment.course_id == course.id,
        )
        .one()
    )

    b0 = int(bucket_stats.b_0_25 or 0)
    b1 = int(bucket_stats.b_25_50 or 0)
    b2 = int(bucket_stats.b_50_75 or 0)
    b3 = int(bucket_stats.b_75_100 or 0)

    distribution = {
        "0-25": {
            "count": b0,
            "percentage": round((b0 / total_enrolled) * 100.0, 2) if total_enrolled > 0 else 0.0,
        },
        "25-50": {
            "count": b1,
            "percentage": round((b1 / total_enrolled) * 100.0, 2) if total_enrolled > 0 else 0.0,
        },
        "50-75": {
            "count": b2,
            "percentage": round((b2 / total_enrolled) * 100.0, 2) if total_enrolled > 0 else 0.0,
        },
        "75-100": {
            "count": b3,
            "percentage": round((b3 / total_enrolled) * 100.0, 2) if total_enrolled > 0 else 0.0,
        },
    }

    # 3. Assessment Performance Breakdown
    assessments = (
        sess.query(Assessment)
        .filter(Assessment.course_id == course.id, Assessment.deleted_at.is_(None))
        .order_by(Assessment.created_at.asc())
        .all()
    )

    assessment_ids = [a.id for a in assessments]
    stats_by_assess: dict[int, dict[str, Any]] = {}
    if assessment_ids:
        att_rows = (
            sess.query(
                AssessmentAttempt.assessment_id,
                func.count(AssessmentAttempt.id).label("total_attempts"),
                func.count(case((AssessmentAttempt.status == "PENDING_GRADING", 1))).label(
                    "pending_grading"
                ),
                func.count(AssessmentResult.attempt_id).label("graded_attempts"),
                func.coalesce(func.avg(AssessmentResult.percent_score), 0.0).label("avg_score"),
                func.count(case((AssessmentResult.passed.is_(True), 1))).label("passed_attempts"),
            )
            .outerjoin(AssessmentResult, AssessmentAttempt.id == AssessmentResult.attempt_id)
            .filter(AssessmentAttempt.assessment_id.in_(assessment_ids))
            .group_by(AssessmentAttempt.assessment_id)
            .all()
        )
        for r in att_rows:
            stats_by_assess[r.assessment_id] = {
                "total_attempts": int(r.total_attempts),
                "pending_grading": int(r.pending_grading),
                "graded_attempts": int(r.graded_attempts),
                "avg_score": float(r.avg_score),
                "passed_attempts": int(r.passed_attempts),
            }

    assessments_breakdown: list[dict[str, Any]] = []
    total_course_attempts = 0
    total_course_pending_grading = 0
    total_course_graded = 0
    sum_course_scores = 0.0
    total_course_passed = 0

    for a in assessments:
        s = stats_by_assess.get(
            a.id,
            {
                "total_attempts": 0,
                "pending_grading": 0,
                "graded_attempts": 0,
                "avg_score": 0.0,
                "passed_attempts": 0,
            },
        )
        n_att = s["total_attempts"]
        n_graded = s["graded_attempts"]
        n_pending = s["pending_grading"]
        n_passed = s["passed_attempts"]
        avg_sc = round(s["avg_score"], 2)
        pass_rt = round((n_passed / n_graded) * 100.0, 2) if n_graded > 0 else 0.0

        total_course_attempts += n_att
        total_course_pending_grading += n_pending
        total_course_graded += n_graded
        sum_course_scores += s["avg_score"] * n_graded
        total_course_passed += n_passed

        assessments_breakdown.append(
            {
                "assessment_id": str(a.public_id),
                "title": a.title,
                "assessment_type": a.assessment_type,
                "status": a.status,
                "total_attempts": n_att,
                "average_score": avg_sc,
                "pass_rate_percent": pass_rt,
                "pending_grading_count": n_pending,
            }
        )

    course_avg_score = (
        round(sum_course_scores / total_course_graded, 2) if total_course_graded > 0 else 0.0
    )
    course_pass_rate = (
        round((total_course_passed / total_course_graded) * 100.0, 2)
        if total_course_graded > 0
        else 0.0
    )

    now = utc_now()
    return {
        "course_id": str(course.public_id),
        "course_code": course.course_code,
        "title": course.title,
        "status": course.status,
        "enrolled_students_count": total_enrolled,
        "active_students_count": active_enrolled,
        "completed_students_count": completed_enrolled,
        "completion_rate_percent": completion_rate,
        "average_progress_percent": avg_progress,
        "progress_distribution": distribution,
        "assessment_performance": {
            "total_attempts": total_course_attempts,
            "average_score": course_avg_score,
            "pass_rate_percent": course_pass_rate,
            "pending_grading_count": total_course_pending_grading,
            "assessments": assessments_breakdown,
        },
        "generated_at": now.isoformat(),
    }


def get_student_learning_overview(
    actor: User,
    session: Session | scoped_session[Any],
) -> dict[str, Any]:
    """Retrieve personalized learning dashboard and analytics for a Student.

    Authorization:
    - Actor must be authenticated and active.
    - Strictly scoped to the actor's own data (Absolute IDOR Defense).

    Returns:
        Personal enrollment metrics, overall progress, server-synchronized upcoming
        assessments, and release-policy filtered recent assessment scores.
    """
    if actor is None or not actor.is_active:
        raise UnauthorizedError("User is not authenticated or account is not active.")

    sess = session
    now = utc_now()

    # 1. Student Enrollments & Course Progress
    enrollments = sess.query(Enrollment).filter(Enrollment.student_user_id == actor.id).all()

    active_enrollments = [e for e in enrollments if e.status == "ACTIVE"]
    completed_enrollments = [e for e in enrollments if e.status == "COMPLETED"]

    active_courses_count = len(active_enrollments)
    completed_courses_count = len(completed_enrollments)

    if enrollments:
        overall_avg_progress = round(
            sum(float(e.current_progress_percent) for e in enrollments) / len(enrollments), 2
        )
    else:
        overall_avg_progress = 0.0

    # Backwards-compatible enrollment cards payload
    serialized_enrollments: list[dict[str, Any]] = [
        {
            "enrollment_id": str(e.public_id),
            "course_id": str(e.course.public_id) if e.course else None,
            "course_title": e.course.title if e.course else None,
            "progress_percent": round(float(e.current_progress_percent), 2),
            "status": e.status,
        }
        for e in enrollments
    ]

    # 2. Upcoming Assessments Deadline (Server Timer Synchronization)
    upcoming_assessments_data: list[dict[str, Any]] = []
    active_course_ids = [e.course_id for e in active_enrollments]
    if active_course_ids:
        assessments = (
            sess.query(Assessment)
            .filter(
                Assessment.course_id.in_(active_course_ids),
                Assessment.status == "PUBLISHED",
                Assessment.deleted_at.is_(None),
                or_(Assessment.close_at.is_(None), Assessment.close_at > now),
            )
            .order_by(Assessment.close_at.asc().nullslast())
            .all()
        )
        for a in assessments:
            upcoming_assessments_data.append(
                {
                    "assessment_id": str(a.public_id),
                    "course_id": str(a.course.public_id) if a.course else None,
                    "course_code": a.course.course_code if a.course else None,
                    "course_title": a.course.title if a.course else None,
                    "title": a.title,
                    "assessment_type": a.assessment_type,
                    "open_at": a.open_at.isoformat() if a.open_at else None,
                    "close_at": a.close_at.isoformat() if a.close_at else None,
                    "time_limit_minutes": a.time_limit_minutes,
                }
            )

    # 3. Recent Graded Assessment Results (ScoreReleasePolicy Enforced)
    graded_attempts = (
        sess.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.student_user_id == actor.id,
            AssessmentAttempt.status == "GRADED",
        )
        .order_by(AssessmentAttempt.graded_at.desc().nullslast(), AssessmentAttempt.id.desc())
        .limit(20)
        .all()
    )

    recent_results_data: list[dict[str, Any]] = []
    for att in graded_attempts:
        assess = att.assessment
        result = att.result
        if assess is None or result is None:
            continue

        policy = assess.score_release_policy
        is_score_released = False
        if policy == "IMMEDIATE":
            is_score_released = result.status in ("FINAL", "RELEASED")
        elif policy == "AFTER_CLOSE":
            close_utc = _ensure_utc(assess.close_at)
            now_utc = _ensure_utc(now)
            is_score_released = bool(close_utc and now_utc and now_utc >= close_utc)
        elif policy == "INSTRUCTOR_RELEASE":
            is_score_released = result.status == "RELEASED"

        if is_score_released:
            recent_results_data.append(
                {
                    "attempt_id": str(att.public_id),
                    "assessment_id": str(assess.public_id),
                    "assessment_title": assess.title,
                    "course_id": str(assess.course.public_id) if assess.course else None,
                    "course_code": assess.course.course_code if assess.course else None,
                    "attempt_number": att.attempt_number,
                    "raw_score": round(float(result.raw_score), 2),
                    "max_score": round(float(result.max_score), 2),
                    "percent_score": (
                        round(float(result.percent_score), 2)
                        if result.percent_score is not None
                        else 0.0
                    ),
                    "passed": bool(result.passed) if result.passed is not None else False,
                    "graded_at": att.graded_at.isoformat() if att.graded_at else None,
                }
            )

    return {
        "student_id": str(actor.public_id),
        "student_name": actor.display_name,
        "enrolled_courses_count": len(enrollments),
        "active_courses_count": active_courses_count,
        "completed_courses_count": completed_courses_count,
        "overall_average_progress_percent": overall_avg_progress,
        "server_time": now.isoformat(),
        "enrollments": serialized_enrollments,
        "upcoming_assessments": upcoming_assessments_data,
        "recent_results": recent_results_data,
    }
