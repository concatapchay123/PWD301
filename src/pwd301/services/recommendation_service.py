"""Course Recommendation Engine implementing Algorithm 14 for PWD301.

Implements:
- Hybrid rule-based candidate filtering and scoring.
- Cold-start beginner recommendations for new learners.
- Prerequisite graph satisfaction enforcement.
- Category matching and natural difficulty progression ranking.
- Gemini AI explanation enrichment with graceful degradation fallback.
- ADR-002 Zero Internal PK Leakage.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.course import Course, CoursePrerequisite, Enrollment
from pwd301.models.identity import User
from pwd301.services.gemini_service import (
    get_gemini_client,
    record_ai_telemetry,
)

logger = logging.getLogger(__name__)

# Difficulty progression hierarchy
_DIFFICULTY_RANKS: dict[str, int] = {
    "BEGINNER": 1,
    "INTERMEDIATE": 2,
    "ADVANCED": 3,
}


def _get_student_completed_course_ids(
    student_id: int, session: Session | scoped_session[Any]
) -> set[int]:
    """Retrieve set of course IDs the student has successfully completed."""
    rows = (
        session.query(Enrollment.course_id)
        .filter(
            Enrollment.student_user_id == student_id,
            Enrollment.status == "COMPLETED",
        )
        .all()
    )
    return {r[0] for r in rows}


def _get_student_enrolled_course_ids(
    student_id: int, session: Session | scoped_session[Any]
) -> set[int]:
    """Retrieve set of course IDs the student is actively enrolled in or completed."""
    rows = (
        session.query(Enrollment.course_id)
        .filter(
            Enrollment.student_user_id == student_id,
            Enrollment.status.in_(("ACTIVE", "COMPLETED", "RETENTION_PENDING")),
        )
        .all()
    )
    return {r[0] for r in rows}


def _check_prerequisites_met(
    course_id: int,
    completed_course_ids: set[int],
    prereq_map: dict[int, list[int]],
) -> bool:
    """Verify whether all required prerequisites for a course are in completed_course_ids."""
    prereqs = prereq_map.get(course_id, [])
    if not prereqs:
        return True
    return all(p in completed_course_ids for p in prereqs)


def generate_course_recommendations(
    actor: User,
    limit: int = 5,
    session: Session | scoped_session[Any] | None = None,
) -> list[dict[str, Any]]:
    """Compute personalized course recommendations adhering to Algorithm 14.

    Args:
        actor: Authenticated student or user.
        limit: Maximum number of recommended courses to return.
        session: Optional SQLAlchemy session.

    Returns:
        List of recommended courses with deterministic ranking and AI explanation,
        conforming strictly to ADR-002 Zero Internal PK Leakage.
    """
    sess = session or db.session
    student_id = actor.id

    # 1. Inspect student's learning history
    completed_course_ids = _get_student_completed_course_ids(student_id, sess)
    excluded_course_ids = _get_student_enrolled_course_ids(student_id, sess)

    completed_courses = (
        sess.query(Course).filter(Course.id.in_(completed_course_ids)).all()
        if completed_course_ids
        else []
    )
    completed_categories = {c.category for c in completed_courses if c.category}
    completed_difficulties = [
        _DIFFICULTY_RANKS.get(c.difficulty or "BEGINNER", 1) for c in completed_courses
    ]
    max_completed_difficulty = max(completed_difficulties) if completed_difficulties else 0

    # 2. Query published, non-deleted candidate courses
    query = sess.query(Course).filter(
        Course.status == "PUBLISHED",
        Course.deleted_at.is_(None),
    )
    if excluded_course_ids:
        query = query.filter(~Course.id.in_(excluded_course_ids))

    all_candidates = query.all()
    if not all_candidates:
        return []

    candidate_ids = [c.id for c in all_candidates]

    # Pre-fetch prerequisite mappings for all candidate courses in a single query
    prereq_rows = (
        sess.query(CoursePrerequisite.course_id, CoursePrerequisite.prerequisite_course_id)
        .filter(CoursePrerequisite.course_id.in_(candidate_ids))
        .all()
    )
    prereq_map: dict[int, list[int]] = {}
    for cid, pid in prereq_rows:
        prereq_map.setdefault(cid, []).append(pid)

    # 3. Rule-based candidate scoring & filtering
    scored_candidates: list[dict[str, Any]] = []

    for course in all_candidates:
        # Enforce prerequisite satisfaction
        if not _check_prerequisites_met(course.id, completed_course_ids, prereq_map):
            continue

        score = 0
        reasons: list[str] = []
        c_diff_rank = _DIFFICULTY_RANKS.get(course.difficulty or "BEGINNER", 1)

        # Prerequisite bonus
        has_prereqs = bool(prereq_map.get(course.id))
        if has_prereqs:
            score += 25
            reasons.append("PREREQUISITES_SATISFIED")

        # Cold-start path vs Experienced path
        if not completed_course_ids:
            # Cold-start: prioritize beginner-friendly courses
            if course.difficulty == "BEGINNER":
                score += 30
                reasons.append("BEGINNER_FRIENDLY")
            else:
                score += 10
        else:
            # Category alignment
            if course.category and course.category in completed_categories:
                score += 30
                reasons.append("CATEGORY_MATCH")

            # Difficulty progression
            if max_completed_difficulty > 0:
                if c_diff_rank == max_completed_difficulty + 1:
                    score += 20
                    reasons.append("DIFFICULTY_PROGRESSION")
                elif c_diff_rank == max_completed_difficulty:
                    score += 10
                    reasons.append("SKILL_REINFORCEMENT")
                elif c_diff_rank <= max_completed_difficulty:
                    score += 5

        scored_candidates.append(
            {
                "course": course,
                "score": score,
                "reasons": reasons,
                "has_prereqs": has_prereqs,
            }
        )

    if not scored_candidates:
        return []

    # 4. Deterministic sorting: highest score first, then title tie-breaker
    scored_candidates.sort(key=lambda x: (x["score"], x["course"].title), reverse=True)
    top_candidates = scored_candidates[:limit]

    # 5. Prepare student profile and course facts for explanation
    student_profile = {
        "completed_count": len(completed_course_ids),
        "completed_courses": [c.title for c in completed_courses],
        "interests": sorted(list(completed_categories)),
    }

    client = get_gemini_client()
    results: list[dict[str, Any]] = []

    for item in top_candidates:
        cand_course: Course = item["course"]
        cand_reasons: list[str] = item["reasons"]
        course_facts = {
            "title": cand_course.title,
            "category": cand_course.category,
            "difficulty": cand_course.difficulty,
            "has_prerequisites": item["has_prereqs"],
        }

        # AI Explanation with Graceful Degradation Fallback
        explanation: str
        t_start = time.time()
        telemetry_status = "SUCCEEDED"
        telemetry_error: str | None = None

        try:
            explanation = client.explain_recommendation(student_profile, course_facts)
        except Exception as exc:
            telemetry_status = "FAILED"
            telemetry_error = type(exc).__name__
            logger.warning(
                "Gemini explanation failed for course %s, falling back to rule explanation: %s",
                cand_course.course_code,
                exc,
            )
            # Default deterministic explanation fallback
            if "CATEGORY_MATCH" in cand_reasons and "DIFFICULTY_PROGRESSION" in cand_reasons:
                explanation = (
                    f"Recommended because you completed foundational courses in "
                    f"{cand_course.category} and are ready for this "
                    f"{cand_course.difficulty} challenge."
                )
            elif "CATEGORY_MATCH" in cand_reasons:
                explanation = (
                    f"Expands your expertise in {cand_course.category} following "
                    "your completed coursework."
                )
            elif "PREREQUISITES_SATISFIED" in cand_reasons:
                explanation = (
                    "You have satisfied all prerequisites required to enroll in "
                    f"'{cand_course.title}'."
                )
            elif "BEGINNER_FRIENDLY" in cand_reasons:
                explanation = "An excellent introductory course to kickstart your learning path."
            else:
                explanation = (
                    f"A highly relevant {cand_course.difficulty or 'standard'} course suited for "
                    "your current learning progress."
                )

        latency_ms = int((time.time() - t_start) * 1000)

        # Telemetry logging into ai_requests in a bounded transaction
        try:
            record_ai_telemetry(
                user_id=actor.id,
                route_type="GEMINI" if telemetry_status == "SUCCEEDED" else "BACKEND_ONLY",
                prompt=f"Explain recommendation: {cand_course.course_code}",
                status=telemetry_status,
                latency_ms=latency_ms,
                scope_decision="IN_SCOPE",
                error_code=telemetry_error,
                session=sess,
            )
            sess.commit()
        except Exception as exc:
            logger.error("Failed to commit AI telemetry for recommendation: %s", exc)
            sess.rollback()

        # Strict ADR-002: Zero internal BIGINT IDs in output dictionary
        results.append(
            {
                "course_id": str(cand_course.public_id),
                "course_code": cand_course.course_code,
                "title": cand_course.title,
                "description": cand_course.description,
                "category": cand_course.category,
                "difficulty": cand_course.difficulty,
                "score": item["score"],
                "reasons": cand_reasons,
                "explanation": explanation,
            }
        )

    return results
