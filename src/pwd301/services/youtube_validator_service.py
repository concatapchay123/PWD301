"""YouTube Video Validation & Health Scanner Service.

Provides real-time validation for YouTube video embeddability, availability,
and automated scanning to notify instructors when linked videos are deleted or blocked.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
import uuid
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from flask import current_app

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import User
from pwd301.services.notification_service import dispatch_notification

logger = logging.getLogger(__name__)

YOUTUBE_OEMBED_ENDPOINT = "https://www.youtube.com/oembed"
USER_AGENT = "PWD301-LMS/1.0 (HealthScanner)"


def get_youtube_metadata(video_id: str, timeout: float = 4.0) -> dict[str, Any]:
    """Fetch trusted duration/status; oEmbed alone never proves playback availability.

    API credentials are server-only. Do not include request URLs in errors/logs.
    """
    if not isinstance(video_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return {"valid": False, "reason": "invalid_id"}
    key = current_app.config.get("YOUTUBE_API_KEY")
    if not key:
        return {"valid": False, "reason": "metadata_not_configured"}
    params = urlencode({"part": "contentDetails,status", "id": video_id, "key": key})
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/videos?" + params,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read(1_000_001))
        items = data.get("items", [])
        if not items:
            return {"valid": False, "reason": "unavailable"}
        item = items[0]
        duration = item.get("contentDetails", {}).get("duration", "")
        match = re.fullmatch(r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", duration)
        seconds = (
            sum(
                float(value or 0) * scale
                for value, scale in zip(match.groups(), (86400, 3600, 60, 1), strict=True)
            )
            if match
            else 0
        )
        status = item.get("status", {})
        embeddable = status.get("embeddable") is True
        valid = (
            embeddable
            and seconds > 0
            and status.get("uploadStatus") == "processed"
            and status.get("privacyStatus") in {"public", "unlisted"}
        )
        return {
            "valid": valid,
            "video_id": video_id,
            "duration_seconds": seconds,
            "embeddable": embeddable,
            "reason": None if valid else "not_playable",
        }
    except (urllib.error.URLError, TimeoutError, ValueError, TypeError, KeyError):
        return {"valid": False, "reason": "metadata_network_error", "network_error": True}


def extract_youtube_id(url: str) -> str | None:
    """Extract standard 11-char YouTube ID from any valid YouTube URL."""
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or parsed.username or parsed.password:
        return None
    host = (parsed.hostname or "").lower()
    video_id = None
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/", "/v/")):
            parts = parsed.path.split("/")
            if len(parts) > 2:
                video_id = parts[2]
    elif host == "youtu.be":
        video_id = parsed.path.lstrip("/").split("/")[0]

    if video_id and re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return video_id
    return None


def verify_youtube_embeddability(url_or_id: str, timeout: float = 4.0) -> dict[str, Any]:
    """Perform preliminary oEmbed metadata validation, not a playback guarantee.

    Returns dict with:
        valid: bool
        video_id: str | None
        title: str | None
        author_name: str | None
        reason: str | None
        status_code: int | None
    """
    yt_id = extract_youtube_id(url_or_id) if "http" in url_or_id else url_or_id.strip()
    if not yt_id or not re.fullmatch(r"[A-Za-z0-9_-]{11}", yt_id):
        return {
            "valid": False,
            "video_id": None,
            "title": None,
            "author_name": None,
            "reason": "Liên kết hoặc ID video YouTube không đúng định dạng chuẩn.",
            "status_code": 400,
        }

    canonical_url = f"https://www.youtube.com/watch?v={yt_id}"
    oembed_url = f"{YOUTUBE_OEMBED_ENDPOINT}?url={canonical_url}&format=json"

    req = urllib.request.Request(
        oembed_url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                raw_data = response.read().decode("utf-8")
                info = json.loads(raw_data)
                metadata = (
                    get_youtube_metadata(yt_id, timeout=timeout)
                    if current_app.config.get("YOUTUBE_API_KEY")
                    else None
                )
                if metadata is not None and not metadata.get("valid"):
                    return {
                        "valid": False,
                        "video_id": yt_id,
                        "title": info.get("title"),
                        "author_name": info.get("author_name"),
                        "reason": (
                            "Không thể lấy metadata YouTube. Vui lòng thử lại."
                            if metadata.get("network_error")
                            else "Video không khả dụng hoặc không cho phép nhúng."
                        ),
                        "status_code": None if metadata.get("network_error") else 403,
                        "network_error": bool(metadata.get("network_error")),
                        "validation_source": "youtube_data_api",
                        "playback_guaranteed": False,
                    }
                return {
                    "valid": True,
                    "video_id": yt_id,
                    "title": info.get("title"),
                    "author_name": info.get("author_name"),
                    "reason": None,
                    "status_code": 200,
                    "validation_source": "youtube_data_api" if metadata else "oembed_preliminary",
                    "playback_guaranteed": False,
                    "duration_seconds": metadata.get("duration_seconds") if metadata else None,
                    "embeddable": metadata.get("embeddable") if metadata else None,
                }
    except urllib.error.HTTPError as err:
        transient = err.code == 429 or err.code >= 500
        if err.code == 404:
            reason = "Video không tồn tại hoặc đã bị tác giả gỡ bỏ khỏi YouTube."
        elif err.code in {400, 401, 403}:
            reason = "Video ở chế độ riêng tư, bị giới hạn bản quyền hoặc tác giả không cho phép nhúng (embed) vào hệ thống ngoài."
        else:
            reason = f"YouTube từ chối phát video này (Mã lỗi HTTP {err.code})."
        return {
            "valid": False,
            "video_id": yt_id,
            "title": None,
            "author_name": None,
            "reason": reason,
            "status_code": err.code,
            "network_error": transient,
        }
    except Exception as exc:
        logger.warning("YouTube oEmbed check encountered network/timeout error: %s", exc)
        return {
            "valid": False,
            "video_id": yt_id,
            "title": None,
            "author_name": None,
            "reason": "Không thể kết nối đến máy chủ YouTube để kiểm tra tính khả dụng của video.",
            "status_code": None,
            "network_error": True,
        }

    return {
        "valid": False,
        "video_id": yt_id,
        "title": None,
        "author_name": None,
        "reason": "Không xác định được trạng thái video trên YouTube.",
        "status_code": 500,
    }


def scan_and_notify_broken_youtube_videos(
    course_id: int | None = None,
    lesson_id: int | None = None,
    retry_network_errors: bool = False,
) -> list[dict[str, Any]]:
    """Scan published courses/lessons for broken or non-embeddable YouTube videos.

    If a broken video is detected, dispatches an in-app notification to the course instructor.
    """
    query = db.session.query(Course).filter(
        Course.status != "ARCHIVED", Course.deleted_at.is_(None)
    )
    if course_id:
        query = query.filter(Course.id == course_id)

    courses = query.all()
    broken_reports: list[dict[str, Any]] = []

    for course in courses:
        lessons_query = db.session.query(Lesson).filter(
            Lesson.course_id == course.id, Lesson.deleted_at.is_(None)
        )
        if lesson_id is not None:
            lessons_query = lessons_query.filter(Lesson.id == lesson_id)
        lessons = lessons_query.all()
        for lesson in lessons:
            from pwd301.blueprints.instructor.routes import _extract_video_urls_from_markdown

            video_urls = _extract_video_urls_from_markdown(lesson.markdown_content)
            for url in video_urls:
                yt_id = extract_youtube_id(url)
                if not yt_id:
                    continue  # Non-YouTube or uploaded video
                check = verify_youtube_embeddability(yt_id)
                if retry_network_errors and check.get("network_error"):
                    raise RuntimeError("YouTube metadata unavailable; retry this lesson scan.")
                if not check["valid"] and not check.get("network_error"):
                    report = {
                        "course_id": course.id,
                        "course_title": course.title,
                        "lesson_id": lesson.id,
                        "lesson_title": lesson.title,
                        "video_url": url,
                        "video_id": yt_id,
                        "reason": check["reason"],
                    }
                    broken_reports.append(report)

                    # Notify course owner/instructor
                    if course.owner_instructor_id:
                        instructor = db.session.get(User, course.owner_instructor_id)
                        if instructor:
                            title = f"Cảnh báo: Video YouTube bài học bị lỗi ({lesson.title})"
                            body = (
                                f"Video YouTube trong bài học '{lesson.title}' (Khóa học '{course.title}') "
                                f"không thể phát được do: {check['reason']}. "
                                f"Vui lòng cập nhật hoặc thay thế video để đảm bảo sinh viên có thể học tập bình thường."
                            )
                            try:
                                dispatch_notification(
                                    recipient_user=instructor,
                                    event_type="COURSE_LESSON_VIDEO_BROKEN",
                                    title=title,
                                    body=body,
                                    action_url=f"#/instructor/courses/{course.id}/lessons/{lesson.id}/edit",
                                    category="COURSE",
                                    event_key=uuid.uuid5(
                                        uuid.NAMESPACE_URL,
                                        f"pwd301:youtube-broken:{course.id}:{lesson.id}:{yt_id}:{instructor.id}",
                                    ),
                                    session=db.session,
                                )
                            except Exception as notif_err:
                                if retry_network_errors:
                                    raise RuntimeError(
                                        "Video notification could not persist; retry this lesson scan."
                                    ) from None
                                logger.error(
                                    "Failed to dispatch broken video notification: %s", notif_err
                                )

    if broken_reports:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    return broken_reports
