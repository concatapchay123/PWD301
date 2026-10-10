"""Server-clock video progress. Callers own transactions when passing a Session.

Client playing/position signals cannot prove attention. A locked enrollment row
serializes session creation and heartbeat writes across Gunicorn processes.
"""

from __future__ import annotations

import json
import math
import re
import uuid
from datetime import timedelta
from typing import Any

from pwd301.extensions import db
from pwd301.models.course import Enrollment, EnrollmentPeriod
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.playback import MediaProgress, PlaybackReceipt, PlaybackSession
from pwd301.models.types import utc_now
from pwd301.services.exceptions import ForbiddenError, LessonValidationError
from pwd301.services.lesson_service import (
    _lesson_requires_video_watch,
    _to_naive_utc,
    get_lesson_detail,
    get_lesson_progress,
    record_lesson_progress,
)
from pwd301.services.youtube_validator_service import extract_youtube_id, get_youtube_metadata

STATES = {"playing", "paused", "buffering", "hidden", "blackout", "error"}


def lesson_media_ids(lesson: Any) -> list[str]:
    """Derive stable IDs from server content, never a client media array index."""
    content = lesson.markdown_content or ""
    urls: list[str] = []
    single = re.search(r"<!--\s*video_url:\s*(.*?)\s*-->", content)
    if single:
        urls.append(single.group(1).strip())
    multiple = re.search(r"<!--\s*video_urls:\s*(\[.*?\])\s*-->", content, re.S)
    if multiple:
        try:
            parsed = json.loads(multiple.group(1))
            if isinstance(parsed, list):
                urls.extend(url for url in parsed if isinstance(url, str))
        except ValueError:
            pass
    ids = [f"youtube:{yt}" for url in urls if (yt := extract_youtube_id(url))]
    resources = lesson.resources
    if not resources and lesson.previous_lesson:
        resources = lesson.previous_lesson.resources
    ids.extend(
        f"hls:{resource.file_asset.public_id}:{resource.file_asset.current_revision.public_id}"
        for resource in resources
        if resource.file_asset
        and resource.file_asset.is_video
        and resource.file_asset.status == "ACTIVE"
        and resource.file_asset.current_revision
        and resource.file_asset.virus_scan_status == "CLEAN"
    )
    return list(dict.fromkeys(ids))


def _context(actor: Any, lesson_id: Any, sess: Any) -> tuple[Any, Any, Any]:
    lesson = get_lesson_detail(actor, lesson_id, session=sess)
    if lesson.deleted_at is not None or lesson.status not in {"PUBLISHED", "HISTORICAL"}:
        raise LessonValidationError("Playback requires a published lesson.")
    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.course_id == lesson.course_id,
            Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
        )
        .with_hint(Enrollment, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql")
        .with_for_update()
        .populate_existing()
        .first()
    )
    if not enrollment or not enrollment.current_period_id:
        raise ForbiddenError("An active enrollment period is required.")
    period = sess.get(EnrollmentPeriod, enrollment.current_period_id)
    if not period or period.status not in {"ACTIVE", "COMPLETED"}:
        raise ForbiddenError("Enrollment period is no longer active.")
    return lesson, enrollment, period


def _duration(lesson: Any, media_id: str) -> float:
    if media_id.startswith("youtube:"):
        metadata = get_youtube_metadata(media_id.split(":", 1)[1])
        if not metadata.get("valid") or not metadata.get("embeddable"):
            raise LessonValidationError(
                "Trusted YouTube duration is unavailable. Please retry later."
            )
        duration = float(metadata.get("duration_seconds") or 0)
    elif media_id.startswith("hls:"):
        from pwd301.services.video_drm_service import get_asset_hls_directory

        asset_id, revision_id = media_id.split(":")[1:]
        resources = lesson.resources or (
            lesson.previous_lesson.resources if lesson.previous_lesson else []
        )
        asset = next(
            resource.file_asset
            for resource in resources
            if str(resource.file_asset.public_id) == asset_id
        )
        revision = asset.current_revision
        if str(revision.public_id) != revision_id:
            raise LessonValidationError("Video revision changed. Reload its stream.")
        playlist = get_asset_hls_directory(lesson, asset, revision) / "playlist.m3u8"
        if not playlist.is_file():
            raise LessonValidationError("Protected video is not ready. Open its stream and retry.")
        content = playlist.read_text(encoding="utf-8")
        if "#EXT-X-ENDLIST" not in content:
            raise LessonValidationError("Protected video duration is not ready.")
        duration = sum(float(value) for value in re.findall(r"#EXTINF:([0-9.]+),", content))
    else:
        duration = 1.0
    if not math.isfinite(duration) or duration <= 0:
        raise LessonValidationError("Video duration is unavailable.")
    return duration


def _snapshot(
    lease: Any, media: Any, lesson: Any, actor: Any, now: Any, sess: Any, credited: int = 0
) -> dict[str, Any]:
    progress = get_lesson_progress(actor, lesson.id, session=sess)
    return {
        "session_id": str(lease.public_id),
        "next_sequence": lease.next_sequence,
        "server_time": now.isoformat(),
        "media_id": media.media_id,
        "frontier": media.frontier_seconds,
        "resume_position": media.frontier_seconds,
        "duration": media.duration_seconds,
        "credited_seconds": credited,
        "is_video_complete": media.frontier_seconds >= media.duration_seconds * 0.9,
        "is_completed": bool(progress and progress.completed_at),
        "completed": bool(progress and progress.completed_at),
        "seconds_spent": progress.seconds_spent if progress else 0,
    }


def start_playback_session(
    actor: Any, lesson_id: Any, media_id: Any, session: Any = None, now: Any = None
) -> dict[str, Any]:
    sess = session if session is not None else db.session
    try:
        lesson, _, period = _context(actor, lesson_id, sess)
        ids = lesson_media_ids(lesson)
        if media_id not in ids and not (
            not _lesson_requires_video_watch(lesson) and media_id == f"content:{lesson.public_id}"
        ):
            raise LessonValidationError("Media is not attached to this lesson.")
        at = now if now is not None else utc_now()
        media = (
            sess.query(MediaProgress)
            .filter_by(enrollment_period_id=period.id, lesson_id=lesson.id, media_id=media_id)
            .first()
        )
        if media is None:
            duration = _duration(lesson, media_id)
            existing_progress = get_lesson_progress(actor, lesson.id, session=sess)
            historically_complete = bool(
                existing_progress and existing_progress.completed_at and ids and media_id == ids[0]
            )
            media = MediaProgress(
                enrollment_period_id=period.id,
                lesson_id=lesson.id,
                media_id=media_id,
                duration_seconds=duration,
                frontier_seconds=duration if historically_complete else 0,
                updated_at=at,
            )
            sess.add(media)
        lease = (
            sess.query(PlaybackSession)
            .filter_by(enrollment_period_id=period.id, lesson_id=lesson.id)
            .first()
        )
        if lease is None:
            lease = PlaybackSession(enrollment_period_id=period.id, lesson_id=lesson.id)
            sess.add(lease)
        else:
            # A replaced lease is rejected before replay; its receipts are no longer
            # usable. Removing only those receipts bounds normal course navigation
            # without touching frontiers, lesson completion or audit history.
            sess.query(PlaybackReceipt).filter_by(session_id=lease.id).delete(
                synchronize_session=False
            )
        lease.public_id = uuid.uuid4()
        lease.media_id, lease.state, lease.next_sequence = media_id, "paused", 1
        lease.last_heartbeat_at, lease.updated_at = None, at
        lease.last_position, lease.last_rate, lease.fractional_seconds = (
            media.frontier_seconds,
            1,
            0,
        )
        sess.flush()
        result = _snapshot(lease, media, lesson, actor, at, sess)
        if session is None:
            sess.commit()
        return result
    except Exception:
        if session is None:
            sess.rollback()
        raise


def reconcile_lesson_progress(
    actor: Any, lesson_id: Any, view_fraction: Any = 0, session: Any = None, now: Any = None
) -> Any:
    """Zero-time reconciliation for manual completion; cannot forge video evidence."""
    sess = session if session is not None else db.session
    try:
        from pwd301.services.lesson_service import _lesson_requires_video_watch

        lesson, _, _ = _context(actor, lesson_id, sess)
        existing = get_lesson_progress(actor, lesson.id, session=sess)
        fraction = (
            (float(existing.max_view_fraction or 0) if existing else 0)
            if _lesson_requires_video_watch(lesson)
            else view_fraction
        )
        progress = record_lesson_progress(
            actor, lesson.id, 0, fraction, session=sess, now=now, server_verified=True
        )
        if session is None:
            sess.commit()
        return progress
    except Exception:
        if session is None:
            sess.rollback()
        raise


def record_playback_heartbeat(
    actor: Any, lesson_id: Any, payload: dict[str, Any], session: Any = None, now: Any = None
) -> dict[str, Any]:
    sess = session if session is not None else db.session
    try:
        lesson, _, period = _context(actor, lesson_id, sess)
        try:
            token = uuid.UUID(str(payload.get("playback_session_id")))
            sequence = int(str(payload["sequence"]))
            position = float(payload.get("position_seconds", 0))
            rate = float(payload.get("playback_rate", 1))
        except (ValueError, TypeError, KeyError):
            raise LessonValidationError("Invalid playback heartbeat.") from None
        state = payload.get("state")
        if not 1 <= sequence <= 2_147_483_646:
            raise LessonValidationError("Playback sequence is out of range; start a new session.")
        if (
            not isinstance(state, str)
            or state not in STATES
            or sequence < 1
            or not math.isfinite(position)
            or not math.isfinite(rate)
            or position < 0
            or not 0.75 <= rate <= 2
        ):
            raise LessonValidationError("Invalid playback state, position or rate.")
        lease = (
            sess.query(PlaybackSession)
            .filter_by(enrollment_period_id=period.id, lesson_id=lesson.id)
            .populate_existing()
            .first()
        )
        if lease is None or lease.public_id != token:
            raise LessonValidationError("Playback session has been replaced. Resume this lesson.")
        if payload.get("media_id") != lease.media_id:
            raise LessonValidationError("Heartbeat media does not match the active session.")
        receipt = sess.query(PlaybackReceipt).filter_by(lease_id=token, sequence=sequence).first()
        if receipt:
            result = json.loads(receipt.response_json)
            if session is None:
                sess.commit()
            return result
        if sequence != lease.next_sequence:
            raise LessonValidationError(f"Expected heartbeat sequence {lease.next_sequence}.")
        ids = lesson_media_ids(lesson)
        if lease.media_id not in ids and not (
            not _lesson_requires_video_watch(lesson)
            and lease.media_id == f"content:{lesson.public_id}"
        ):
            raise LessonValidationError("Lesson media changed. Resume this lesson.")
        media = (
            sess.query(MediaProgress)
            .filter_by(enrollment_period_id=period.id, lesson_id=lesson.id, media_id=lease.media_id)
            .populate_existing()
            .one()
        )
        at = now if now is not None else utc_now()
        elapsed = (
            (_to_naive_utc(at) - _to_naive_utc(lease.last_heartbeat_at)).total_seconds()
            if lease.last_heartbeat_at
            else 0
        )
        credited = 0
        contiguous = max(0.0, position - lease.last_position)
        active = lease.state == "playing" and state in {"playing", "paused"} and 0 < elapsed <= 20
        # A client jumping beyond the watched frontier earns neither time nor frontier.
        allowed = elapsed * min(rate, lease.last_rate) if active else 0
        valid_motion = not ids or (
            contiguous > 0
            and contiguous <= allowed + 0.25
            and lease.last_position <= media.frontier_seconds + 0.25
        )
        if active and ids and not valid_motion and position > media.frontier_seconds + 0.25:
            sess.add(
                AuditEvent(
                    action="LESSON_PROGRESS_PACE_ANOMALY",
                    actor_user_id=actor.id,
                    actor_roles_snapshot=",".join(sorted(role.code for role in actor.roles))
                    or "STUDENT",
                    target_type="Lesson",
                    target_id=lesson.id,
                    after_json=json.dumps(
                        {
                            "claimed_position": position,
                            "frontier_seconds": media.frontier_seconds,
                            "elapsed_seconds": round(elapsed, 3),
                            "credited_seconds": 0,
                        }
                    ),
                    created_at=at,
                )
            )
        if active and valid_motion:
            # Delayed retries and stalls cannot turn idle server time into viewing time.
            observed_seconds = (
                min(elapsed, contiguous / max(rate, lease.last_rate)) if ids else elapsed
            )
            accumulated = observed_seconds + lease.fractional_seconds
            credited = int(accumulated)
            lease.fractional_seconds = accumulated - credited
            media.frontier_seconds = min(
                media.duration_seconds,
                max(media.frontier_seconds, min(position, lease.last_position + allowed)),
            )
        elif not active:
            lease.fractional_seconds = 0
        is_primary = bool(ids and lease.media_id == ids[0])
        current = get_lesson_progress(actor, lesson.id, session=sess)
        fraction = (
            media.frontier_seconds / media.duration_seconds
            if is_primary
            else (float(current.max_view_fraction or 0) if current else 0)
        )
        if not ids:
            fraction = float(payload.get("view_fraction", 0))
        record_lesson_progress(
            actor, lesson.id, credited, fraction, session=sess, now=at, server_verified=True
        )
        lease.state, lease.last_heartbeat_at, lease.updated_at = state, at, at
        # Clamp the origin after a forged seek; client must reconcile to frontier.
        lease.last_position = min(position, media.frontier_seconds)
        lease.last_rate = rate
        lease.next_sequence += 1
        media.updated_at = at
        sess.flush()
        result = _snapshot(lease, media, lesson, actor, at, sess, credited)
        result["seek_required"] = bool(ids and position > media.frontier_seconds + 0.25)
        sess.add(
            PlaybackReceipt(
                session_id=lease.id,
                lease_id=token,
                sequence=sequence,
                response_json=json.dumps(result),
                created_at=at,
            )
        )
        sess.flush()
        if session is None:
            sess.commit()
        return result
    except Exception:
        if session is None:
            sess.rollback()
        raise


def cleanup_playback_receipts(session: Any = None, now: Any = None) -> int:
    """Limit replay receipts to 24 hours; keep all frontiers/completion/audit rows.

    Expired duplicate sequences are rejected by next_sequence, never recredited.
    A replay read before cleanup can still return its accepted response; cleanup
    does not edit leases or change any progress counter.
    """
    sess = session if session is not None else db.session
    at = now if now is not None else utc_now()
    try:
        removed = (
            sess.query(PlaybackReceipt)
            .filter(PlaybackReceipt.created_at < at - timedelta(hours=24))
            .delete(synchronize_session=False)
        )
        if session is None:
            sess.commit()
        return removed
    except Exception:
        if session is None:
            sess.rollback()
        raise
