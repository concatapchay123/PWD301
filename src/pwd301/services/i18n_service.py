"""Internationalization (i18n) and Timezone Display Service.

Provides zero-overhead bilingual dictionary translations (Vietnamese / English)
and robust GMT/UTC timezone formatting helpers for globally synchronized exams.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from flask import has_request_context, request, session

# ============================================================================
# TIMEZONE OFFSET HELPERS & REPOSITORIES
# ============================================================================

STANDARD_TIMEZONES: list[dict[str, str]] = [
    {"value": "-12:00", "label": "GMT-12:00 (Baker Island, Howland Island)"},
    {"value": "-11:00", "label": "GMT-11:00 (Samoa, Niue)"},
    {"value": "-10:00", "label": "GMT-10:00 (Honolulu, Hawaii)"},
    {"value": "-09:00", "label": "GMT-09:00 (Anchorage, Alaska)"},
    {"value": "-08:00", "label": "GMT-08:00 (Los Angeles, San Francisco, Vancouver)"},
    {"value": "-07:00", "label": "GMT-07:00 (Denver, Phoenix, Calgary)"},
    {"value": "-06:00", "label": "GMT-06:00 (Chicago, Dallas, Mexico City)"},
    {"value": "-05:00", "label": "GMT-05:00 (New York, Toronto, Miami)"},
    {"value": "-04:00", "label": "GMT-04:00 (Santiago, Halifax, Caracas)"},
    {"value": "-03:00", "label": "GMT-03:00 (Sao Paulo, Buenos Aires)"},
    {"value": "-02:00", "label": "GMT-02:00 (South Georgia)"},
    {"value": "-01:00", "label": "GMT-01:00 (Azores, Cape Verde)"},
    {"value": "+00:00", "label": "GMT+00:00 (UTC, London, Dublin, Lisbon, Edinburgh)"},
    {"value": "+01:00", "label": "GMT+01:00 (Paris, Berlin, Rome, Madrid, Warsaw)"},
    {"value": "+02:00", "label": "GMT+02:00 (Athens, Cairo, Helsinki, Kyiv, Jerusalem)"},
    {"value": "+03:00", "label": "GMT+03:00 (Moscow, Istanbul, Riyadh, Nairobi)"},
    {"value": "+03:30", "label": "GMT+03:30 (Tehran)"},
    {"value": "+04:00", "label": "GMT+04:00 (Dubai, Baku, Tbilisi)"},
    {"value": "+04:30", "label": "GMT+04:30 (Kabul)"},
    {"value": "+05:00", "label": "GMT+05:00 (Karachi, Tashkent, Islamabad)"},
    {"value": "+05:30", "label": "GMT+05:30 (New Delhi, Mumbai, Colombo)"},
    {"value": "+05:45", "label": "GMT+05:45 (Kathmandu)"},
    {"value": "+06:00", "label": "GMT+06:00 (Dhaka, Almaty)"},
    {"value": "+06:30", "label": "GMT+06:30 (Yangon)"},
    {"value": "+07:00", "label": "GMT+07:00 (Hà Nội, TP. Hồ Chí Minh, Bangkok, Jakarta)"},
    {"value": "+08:00", "label": "GMT+08:00 (Singapore, Beijing, Hong Kong, Taipei, Perth)"},
    {"value": "+09:00", "label": "GMT+09:00 (Tokyo, Seoul, Osaka)"},
    {"value": "+09:30", "label": "GMT+09:30 (Adelaide, Darwin)"},
    {"value": "+10:00", "label": "GMT+10:00 (Sydney, Melbourne, Brisbane, Vladivostok)"},
    {"value": "+11:00", "label": "GMT+11:00 (Solomon Islands, Noumea)"},
    {"value": "+12:00", "label": "GMT+12:00 (Auckland, Wellington, Fiji)"},
    {"value": "+13:00", "label": "GMT+13:00 (Nuku'alofa, Tonga)"},
    {"value": "+14:00", "label": "GMT+14:00 (Kiritimati, Line Islands)"},
]

# Named zone mappings to standard offsets
NAMED_TIMEZONE_OFFSETS: dict[str, str] = {
    "asia/ho_chi_minh": "+07:00",
    "asia/bangkok": "+07:00",
    "asia/jakarta": "+07:00",
    "asia/singapore": "+08:00",
    "asia/hong_kong": "+08:00",
    "asia/shanghai": "+08:00",
    "asia/taipei": "+08:00",
    "asia/tokyo": "+09:00",
    "asia/seoul": "+09:00",
    "europe/london": "+00:00",
    "europe/paris": "+01:00",
    "europe/berlin": "+01:00",
    "europe/rome": "+01:00",
    "europe/madrid": "+01:00",
    "america/new_york": "-05:00",
    "america/chicago": "-06:00",
    "america/denver": "-07:00",
    "america/los_angeles": "-08:00",
    "australia/sydney": "+10:00",
}


def parse_tz_offset(val: str | None) -> int:
    """Parse a timezone string into total seconds offset from UTC.

    Supports formats:
    - '+07:00', '-05:00'
    - 'GMT+7', 'GMT-5', 'UTC+1', 'UTC-04:00'
    - 'Asia/Ho_Chi_Minh', 'Europe/Paris'
    - 'UTC', 'GMT', 'Z' -> 0
    """
    if not val:
        return 0
    cleaned = val.strip().lower()

    if cleaned in ("utc", "gmt", "z", "+00:00", "-00:00", "+00", "-00"):
        return 0

    # Match named timezone
    if cleaned in NAMED_TIMEZONE_OFFSETS:
        cleaned = NAMED_TIMEZONE_OFFSETS[cleaned].lower()

    # Regex for GMT/UTC with optional sign and hours:minutes
    m = re.match(r"^(?:gmt|utc)?([+-])(\d{1,2})(?::?(\d{2}))?$", cleaned)
    if m:
        sign = -1 if m.group(1) == "-" else 1
        hours = int(m.group(2))
        minutes = int(m.group(3)) if m.group(3) else 0
        return sign * (hours * 3600 + minutes * 60)

    return 0


def format_tz_offset_label(seconds: int) -> str:
    """Format total seconds offset as friendly GMT string, e.g.

    'GMT+7', 'GMT-5', 'GMT+0'.
    """
    if seconds == 0:
        return "GMT+0"
    sign = "+" if seconds >= 0 else "-"
    abs_sec = abs(seconds)
    hours = abs_sec // 3600
    mins = (abs_sec % 3600) // 60
    if mins > 0:
        return f"GMT{sign}{hours}:{mins:02d}"
    return f"GMT{sign}{hours}"


def format_tz_datetime(
    val: datetime | str | None,
    tz_offset_str: str | None = None,
    fmt: str = "%Y-%m-%d %H:%M",
) -> str:
    """Convert UTC datetime into target timezone string with GMT label."""
    if val is None:
        return ""

    dt: datetime
    if isinstance(val, str):
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return val
    else:
        dt = val

    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)

    offset_seconds = parse_tz_offset(tz_offset_str) if tz_offset_str else 25200  # Default GMT+7
    local_dt = dt + timedelta(seconds=offset_seconds)
    gmt_label = format_tz_offset_label(offset_seconds)
    return f"{local_dt.strftime(fmt)} ({gmt_label})"


# ============================================================================
# BILINGUAL TRANSLATION DICTIONARIES (VI / EN)
# ============================================================================

TRANSLATIONS: dict[str, dict[str, str]] = {
    "vi": {
        # Common UI & Actions
        "common.save": "Lưu thay đổi",
        "common.cancel": "Hủy bỏ",
        "common.back": "Quay lại",
        "common.confirm": "Xác nhận",
        "common.delete": "Xóa",
        "common.edit": "Chỉnh sửa",
        "common.create": "Tạo mới",
        "common.loading": "Đang tải dữ liệu...",
        "common.actions": "Thao tác",
        "common.close": "Đóng",
        "common.view": "Xem",
        "common.search": "Tìm kiếm",
        "common.filter": "Bộ lọc",
        "common.status": "Trạng thái",
        "common.detail": "Chi tiết",
        "common.success": "Thành công",
        "common.error": "Lỗi",
        "common.warning": "Cảnh báo",
        "common.info": "Thông tin",
        "common.reload": "Làm mới",
        "common.all": "Tất cả",
        "common.unlimited": "Không giới hạn",
        "common.system_lms": "Hệ thống Quản lý Học tập PWD301",
        # Navigation
        "nav.dashboard": "Tổng quan",
        "nav.my_learning": "Khóa học của tôi",
        "nav.courses": "Khóa học",
        "nav.assessments": "Bài kiểm tra",
        "nav.grades": "Điểm số",
        "nav.ai_assistant": "Trợ lý AI",
        "nav.become_instructor": "Đăng ký Giảng viên",
        "nav.notifications": "Thông báo",
        "nav.settings": "Cài đặt",
        "nav.logout": "Đăng xuất",
        "nav.login": "Đăng nhập",
        "nav.register": "Đăng ký",
        "nav.switch_role": "Vai trò (Chuyển đổi)",
        "nav.admin_panel": "Quản trị hệ thống",
        "nav.instructor_hub": "Không gian Giảng viên",
        # Roles
        "role.admin": "Quản trị viên (Admin)",
        "role.instructor": "Giảng viên (Instructor)",
        "role.student": "Học viên (Student)",
        "role.guest": "Khách vãng lai",
        # Assessment & Timezone Anti-cheat
        "assessment.title": "Bài kiểm tra & Đánh giá",
        "assessment.upcoming": "Bài kiểm tra đang mở",
        "assessment.results_history": "Lịch sử Điểm số & Đã hoàn thành",
        "assessment.waiting_room": "Phòng chờ thi trực tuyến",
        "assessment.opens_in": "Bài thi sẽ mở sau {minutes} phút",
        "assessment.opens_at": "Thời gian mở đề",
        "assessment.closes_at": "Hạn chót nộp bài",
        "assessment.time_limit": "Thời gian làm bài",
        "assessment.passing_score": "Điểm đạt tối thiểu",
        "assessment.start_exam": "Bắt đầu làm bài thi →",
        "assessment.continue_exam": "Tiếp tục làm bài đang dở →",
        "assessment.exam_closed": "Bài thi đã kết thúc",
        "assessment.not_open_yet": "Chưa đến giờ mở bài thi",
        "assessment.server_time": "Thời gian máy chủ (UTC)",
        "assessment.local_time": "Thời gian theo múi giờ của bạn",
        "assessment.synchronized_notice": (
            "Bài thi được đồng bộ thời gian tuyệt đối trên toàn cầu. "
            "Tất cả thí sinh mở và đóng đề cùng một thời khắc."
        ),
        "assessment.anti_cheat_notice": (
            "Đồng hồ đếm ngược được khóa bảo mật theo thời gian máy chủ. "
            "Việc chỉnh giờ trên máy tính sẽ không thay đổi thời gian làm bài."
        ),
        "assessment.remaining_time": "THỜI GIAN CÒN LẠI",
        "assessment.submit_exam": "Nộp bài thi ngay",
        "assessment.confirm_submit": "Xác nhận nộp bài thi",
        "assessment.confirm_submit_desc": (
            "Bạn có chắc chắn muốn nộp bài thi này không? "
            "Sau khi nộp, bạn sẽ không thể chỉnh sửa câu trả lời."
        ),
        "assessment.autosave_synced": "✓ Đã đồng bộ với máy chủ",
        "assessment.autosave_saving": "Đang lưu tự động...",
        "assessment.autosave_error": "⚠ Lỗi kết nối máy chủ",
        "assessment.lease_lost": "⚠ Mất phiên chỉnh sửa (được mở ở thiết bị khác)",
        "assessment.timezone": "Múi giờ áp dụng",
        "assessment.select_timezone": "Chọn múi giờ",
        "assessment.utc_preview": "Tương đương giờ UTC máy chủ",
        "assessment.live_countdown": "Thời gian đếm ngược đến giờ mở đề",
        "assessment.starts_automatically": (
            "Nút làm bài sẽ tự động mở khi hết thời gian đếm ngược."
        ),
        # Language Switcher
        "lang.vietnamese": "Tiếng Việt",
        "lang.english": "English",
        "lang.current": "Ngôn ngữ",
    },
    "en": {
        # Common UI & Actions
        "common.save": "Save changes",
        "common.cancel": "Cancel",
        "common.back": "Back",
        "common.confirm": "Confirm",
        "common.delete": "Delete",
        "common.edit": "Edit",
        "common.create": "Create",
        "common.loading": "Loading data...",
        "common.actions": "Actions",
        "common.close": "Close",
        "common.view": "View",
        "common.search": "Search",
        "common.filter": "Filter",
        "common.status": "Status",
        "common.detail": "Detail",
        "common.success": "Success",
        "common.error": "Error",
        "common.warning": "Warning",
        "common.info": "Info",
        "common.reload": "Refresh",
        "common.all": "All",
        "common.unlimited": "Unlimited",
        "common.system_lms": "PWD301 Learning Management System",
        # Navigation
        "nav.dashboard": "Dashboard",
        "nav.my_learning": "My Learning",
        "nav.courses": "Courses",
        "nav.assessments": "Assessments",
        "nav.grades": "Grades",
        "nav.ai_assistant": "AI Assistant",
        "nav.become_instructor": "Become Instructor",
        "nav.notifications": "Notifications",
        "nav.settings": "Settings",
        "nav.logout": "Log out",
        "nav.login": "Log in",
        "nav.register": "Register",
        "nav.switch_role": "Switch Role",
        "nav.admin_panel": "System Admin",
        "nav.instructor_hub": "Instructor Hub",
        # Roles
        "role.admin": "Administrator (Admin)",
        "role.instructor": "Instructor",
        "role.student": "Student",
        "role.guest": "Guest",
        # Assessment & Timezone Anti-cheat
        "assessment.title": "Assessments & Evaluations",
        "assessment.upcoming": "Active Assessments",
        "assessment.results_history": "Grade History & Completed",
        "assessment.waiting_room": "Online Exam Waiting Room",
        "assessment.opens_in": "Exam opens in {minutes} minutes",
        "assessment.opens_at": "Opening Time",
        "assessment.closes_at": "Closing Deadline",
        "assessment.time_limit": "Time Limit",
        "assessment.passing_score": "Passing Score",
        "assessment.start_exam": "Start Exam →",
        "assessment.continue_exam": "Continue In-Progress Exam →",
        "assessment.exam_closed": "Exam has closed",
        "assessment.not_open_yet": "Exam is not open yet",
        "assessment.server_time": "Server Time (UTC)",
        "assessment.local_time": "Time in your timezone",
        "assessment.synchronized_notice": (
            "This exam is globally synchronized. "
            "All candidates begin and finish at the exact same physical moment."
        ),
        "assessment.anti_cheat_notice": (
            "Countdown timer is server-authoritative. "
            "Adjusting your local system clock will not extend or alter exam time."
        ),
        "assessment.remaining_time": "TIME REMAINING",
        "assessment.submit_exam": "Submit Exam",
        "assessment.confirm_submit": "Confirm Exam Submission",
        "assessment.confirm_submit_desc": (
            "Are you sure you want to submit your exam? "
            "You cannot modify your answers after submission."
        ),
        "assessment.autosave_synced": "✓ Synced with server",
        "assessment.autosave_saving": "Autosaving...",
        "assessment.autosave_error": "⚠ Connection error",
        "assessment.lease_lost": "⚠ Active editing lease lost (opened elsewhere)",
        "assessment.timezone": "Assessment Timezone",
        "assessment.select_timezone": "Select Timezone",
        "assessment.utc_preview": "Equivalent Server UTC Time",
        "assessment.live_countdown": "Live Countdown to Exam Start",
        "assessment.starts_automatically": (
            "The start exam button will unlock automatically when the countdown reaches zero."
        ),
        # Language Switcher
        "lang.vietnamese": "Tiếng Việt",
        "lang.english": "English",
        "lang.current": "Language",
    },
}


def get_current_locale() -> str:
    """Resolve current user locale ('vi' or 'en').

    Precedence:
    1. Flask session: session['lang']
    2. Cookie: request.cookies['pwd301_lang']
    3. Accept-Language header
    4. Default: 'vi'
    """
    if has_request_context():
        # 1. Session
        lang = session.get("lang")
        if lang in ("vi", "en"):
            return lang

        # 2. Cookie
        cookie_lang = request.cookies.get("pwd301_lang")
        if cookie_lang in ("vi", "en"):
            return cookie_lang

        # 3. Header
        best = request.accept_languages.best_match(["vi", "en"])
        if best:
            return best

    return "vi"


def get_current_timezone() -> str:
    """Resolve current user timezone offset string ('+07:00', '+01:00', etc.).

    Precedence:
    1. Flask session: session['user_timezone']
    2. Cookie: request.cookies['pwd301_timezone']
    3. Default: '+07:00' (Vietnam Standard Time)
    """
    if has_request_context():
        tz = session.get("user_timezone")
        if tz:
            return tz
        cookie_tz = request.cookies.get("pwd301_timezone")
        if cookie_tz:
            return cookie_tz

    return "+07:00"


def t(key: str, lang: str | None = None, **kwargs: Any) -> str:
    """Translate key for target locale with parameter interpolation.

    Falls back cleanly to alternative locale or the raw key.
    """
    target_lang = lang or get_current_locale()
    locale_dict = TRANSLATIONS.get(target_lang, TRANSLATIONS["vi"])

    template = locale_dict.get(key)
    if template is None:
        # Fallback to Vietnamese if requested English and key missing
        template = TRANSLATIONS["vi"].get(key)
    if template is None:
        # Fallback to English if key still missing
        template = TRANSLATIONS["en"].get(key)
    if template is None:
        # Final fallback: return key
        return key

    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return template

    return template
