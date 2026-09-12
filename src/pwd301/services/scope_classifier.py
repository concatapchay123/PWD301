"""Query Scope Classifier and Security Guardrails for PWD301 AI Assistant.

Implements multi-layer defense-in-depth:
1. Malicious/Adversarial threat detection: SQL injection against platform, DDoS, malware/trojan,
   credential harvesting, system sabotage, and prompt injection/jailbreak attempts.
2. Out-of-scope topic detection: Cooking/recipes, romantic creative writing, gambling/lottery,
   financial speculation, astrology/horoscopes, showbiz gossip, weather forecasts, and politics.
3. In-scope academic confirmation: Web development (HTML, CSS, JS, Python, Flask, SQL, etc.),
   algorithms, data structures, software engineering, course curriculum, and polite greetings.
4. Distinguishes defensive pedagogical cybersecurity (e.g. how to prevent XSS/SQLi) from
   offensive malicious exploitation.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScopeResult:
    """Evaluation result from query scope classifier."""

    is_in_scope: bool
    is_malicious: bool
    category: str
    reason: str
    refusal_message: str
    error_code: str | None = None


# Refusal messages
REFUSAL_MESSAGE_SECURITY = (
    "⚠️ Cảnh báo an ninh: Yêu cầu của bạn đã bị từ chối do vi phạm chính sách an toàn thông tin "
    "của hệ thống. Trợ lý AI chỉ phục vụ mục đích học tập và nghiêm cấm mọi hành vi tấn công, "
    "khai thác lỗ hổng, bẻ khóa (jailbreak) hoặc can thiệp trái phép vào hệ thống."
)

REFUSAL_MESSAGE_OUT_OF_SCOPE = (
    "Chào bạn! Mình là Bạch Tuộc Trợ lý AI 🐙 — trợ lý học tập chuyên biệt của hệ thống LMS.\n"
    "Câu hỏi của bạn nằm ngoài phạm vi học tập và công nghệ của hệ thống (lập trình Web, "
    "giải thuật, cơ sở dữ liệu, phát triển phần mềm và các khóa học trên nền tảng).\n"
    "Bạn vui lòng đặt câu hỏi liên quan đến nội dung bài học hoặc kiến thức lập trình để "
    "mình có thể hỗ trợ bạn tốt nhất nhé!"
)

REFUSAL_MESSAGE_EXTERNAL_PROJECT = (
    "Chào bạn! Bạch Tuộc Trợ lý AI 🐙 là trợ lý học tập và hướng dẫn sử dụng hệ thống PWD301. "
    "Hệ thống không hỗ trợ lập trình gia công, xây dựng website thương mại hoặc viết mã nguồn\n"
    "dự án bên ngoài theo yêu cầu cá nhân.\n"
    "Bạn vui lòng tham khảo các khóa học Lập trình Web trên hệ thống để tự trang bị kiến thức và "
    "thực hành xây dựng trang web nhé!"
)

REFUSAL_MESSAGE_GLOBAL_CONTEXT = (
    "Ở trang chính, Bạch Tuộc Trợ lý AI 🐙 chỉ hỗ trợ giải đáp thông tin về hệ thống PWD301, "
    "các khóa học và hướng dẫn sử dụng các tính năng nền tảng (cách đăng ký khóa học, "
    "làm bài kiểm tra, xem bảng điểm, nộp đơn giảng viên...). Để học lập trình và thực hành "
    "viết code HTML/Web, bạn vui lòng đăng ký và truy cập vào khóa học tương ứng trên hệ thống nhé!"
)

REFUSAL_MESSAGE_AI_ABUSE = (
    "Chào bạn! Bạch Tuộc Trợ lý AI 🐙 được thiết kế độc quyền cho việc học tập "
    "trên nền tảng PWD301.\n"
    "Hệ thống không hỗ trợ giải đáp các câu hỏi chung ngoài lề, gia công code dự án ngoài, "
    "viết văn hoặc làm bài tập không thuộc chương trình học của nền tảng.\n"
    "Bạn vui lòng đặt câu hỏi liên quan đến hệ thống PWD301 hoặc nội dung bài học trong khóa học "
    "của bạn nhé!"
)


# ---------------------------------------------------------------------------
# Regex Patterns: Malicious / Attacks / Prompt Injections
# ---------------------------------------------------------------------------

_MALICIOUS_PATTERNS: list[re.Pattern[str]] = [
    # Jailbreak / DAN / Prompt Injection
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s+prompt\s+(reveal|leak|show|print|display)", re.IGNORECASE),
    re.compile(r"(show|reveal|display|output|repeat)\s+(your\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
    re.compile(r"\bDAN\s+mode\b", re.IGNORECASE),
    re.compile(r"bypass\s+(all\s+)?(security|guardrails|safety|rules|policy)", re.IGNORECASE),
    re.compile(
        r"override\s+(all\s+)?(system|safety|security)\s+(rules|prompts|settings)", re.IGNORECASE
    ),
    re.compile(r"you\s+are\s+no\s+longer\s+an?\s+AI", re.IGNORECASE),
    re.compile(r"developer\s+mode\s+(enabled?|activate|on)", re.IGNORECASE),
    # Vietnamese adversarial prompt injections
    re.compile(
        r"bỏ\s+qua\s+(toàn\s+bộ\s+|tất\s+cả\s+)?(các\s+)?(lệnh|chỉ\s+thị|hướng\s+dẫn|quy\s+tắc)\s+(trước|ở\s+trên|ban\s+đầu)",
        re.IGNORECASE,
    ),
    re.compile(
        r"quên\s+(hết|toàn\s+bộ|tất\s+cả)?\s+(các\s+)?(lệnh|hướng\s+dẫn|quy\s+tắc|chỉ\s+thị)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(tiết\s+lộ|hiển\s+thị|in\s+ra|cho\s+xem)\s+(toàn\s+bộ\s+)?(system\s+prompt|prompt\s+hệ\s+thống|chỉ\s+thị\s+hệ\s+thống)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(in\s+ra|cung\s+cấp|cho\s+biết|lộ)\s+(toàn\s+bộ\s+)?(đáp\s+án|đề\s+thi)\s+(trước|kỳ\s+thi)",
        re.IGNORECASE,
    ),
    re.compile(
        r"chế\s+độ\s+(nhà\s+phát\s+triển|bẻ\s+khóa|jailbreak)",
        re.IGNORECASE,
    ),
    re.compile(
        r"bây\s+giờ\s+bạn\s+là\s+(hacker|dan|người\s+xấu|nhân\s+vật\s+phản\s+diện)",
        re.IGNORECASE,
    ),
    # Exploits, Platform Sabotage, Cyber Attacks
    re.compile(
        r"(cách|hướng\s+dẫn|làm\s+sao\s+để|viết\s+code\s+để)\s+(hack|đánh\s+cắp|chiếm\s+đoạt)\s+(tài\s+khoản|mật\s+khẩu|facebook|gmail|ngân\s+hàng)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(tấn\s+công|hướng\s+dẫn\s+tấn\s+công|code\s+tấn\s+công)\s+(ddos|từ\s+chối\s+dịch\s+vụ|dos|deface)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(tạo|viết|phát\s+tán)\s+(mã\s+độc|virus|trojan|ransomware|keylogger|spyware|sâu\s+máy\s+tính)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(create|generate|write)\s+(malware|trojan|ransomware|keylogger|exploit\s+payload|ddos\s+script)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(hack|tấn\s+công|phá\s+hủy|xóa\s+sạch|xâm\s+nhập|phá\s+hoại).*(hệ\s+thống|cơ\s+sở\s+dữ\s+liệu|database|server|máy\s+chủ)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(lấy|trích\s+xuất|leak|dump)\s+(toàn\s+bộ\s+)?(mật\s+khẩu|database|tài\s+khoản|bảng\s+users|thông\s+tin\s+admin)",
        re.IGNORECASE,
    ),
    # Dangerous / Weapons / Illegal Content
    re.compile(
        r"(chế\s+tạo|cách\s+làm|hướng\s+dẫn\s+làm)\s+(bom|thuốc\s+nổ|chất\s+nổ|vũ\s+khí\s+sát\s+thương|chất\s+độc|ma\s+túy)",
        re.IGNORECASE,
    ),
    # Destructive SQL Injection & Database Sabotage
    re.compile(
        r"(\bdrop\s+table\b|\btruncate\s+table\b|\bdelete\s+from\s+\w+\s*;|\bunion\s+select\b|'\s*or\s+'1'\s*=\s*'1)",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------------
# Regex Patterns: Clearly Out-of-Scope Topics (Non-Academic)
# ---------------------------------------------------------------------------

_OUT_OF_SCOPE_TOPIC_PATTERNS: list[re.Pattern[str]] = [
    # Culinary / Cooking / Food Recipes
    re.compile(
        r"(cách|hướng\s+dẫn|công\s+thức)\s+(nấu|làm|chế\s+biến)\s+(món|phở|bún|cơm|bánh|lẩu|thịt|cá|gà|vịt|chè|canh|xào|nướng|kho)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(công\s+thức\s+nấu|nấu\s+ăn|món\s+ngon\s+mỗi\s+ngày|thực\s+đơn\s+bữa\s+tối|pha\s+chế\s+nước|nấu\s+phở)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(recipe\s+for|how\s+to\s+cook|baking\s+recipe|prepare\s+dinner)\b",
        re.IGNORECASE,
    ),
    # Romantic poetry, love confessions, dating advice
    re.compile(
        r"(làm|viết)\s+(bài\s+)?(thơ\s+tình|thơ\s+lục\s+bát\s+về\s+tình\s+yêu|bức\s+thư\s+tỏ\s+tình|văn\s+tán\s+gái)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(cách\s+tán|làm\s+sao\s+để\s+người\s+yêu\s+hết\s+giận|tư\s+vấn\s+tình\s+cảm|bạn\s+gái\s+chia\s+tay)",
        re.IGNORECASE,
    ),
    # Lottery, gambling, betting, sports match predictions
    re.compile(
        r"(xổ\s+số|lô\s+đề|soi\s+cầu|dự\s+đoán\s+kết\s+quả\s+xổ\s+số|kết\s+quả\s+vietlott|con\s+số\s+may\s+mắn)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(cá\s+độ|kèo\s+bóng\s+đá|dự\s+đoán\s+tỷ\s+số|casino|đánh\s+bạc|bài\s+bạc|tài\s+xỉu)",
        re.IGNORECASE,
    ),
    # Financial speculation, crypto trading, gold investment
    re.compile(
        r"(giá\s+vàng\s+hôm\s+nay|nên\s+mua\s+vàng\s+hay\s+đô|dự\s+đoán\s+giá\s+vàng|đầu\s+tư\s+vàng)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(mua\s+cổ\s+phiếu\s+nào|phân\s+tích\s+kỹ\s+thuật\s+chứng\s+khoán|lướt\s+sóng\s+chứng\s+khoán)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(mua\s+coin\s+nào|dự\s+đoán\s+giá\s+bitcoin|tiền\s+ảo\s+nào\s+sắp\s+x10|crypto\s+trading)",
        re.IGNORECASE,
    ),
    # Astrology, horoscopes, tarot, fortune telling
    re.compile(
        r"(xem\s+bói|bói\s+toán|bói\s+bài\s+tarot|tử\s+vi\s+ngày\s+hôm\s+nay|cung\s+hoàng\s+đạo|xem\s+chỉ\s+tay)",
        re.IGNORECASE,
    ),
    # Showbiz, celebrity gossip, pop drama
    re.compile(
        r"(scandal|drama\s+showbiz|chuyện\s+tình\s+cảm\s+của\s+sao|tin\s+tức\s+giới\s+nghệ\s+sĩ)",
        re.IGNORECASE,
    ),
    # Weather forecasts & general tourism
    re.compile(
        r"(thời\s+tiết\s+hôm\s+nay|dự\s+báo\s+thời\s+tiết|nhiệt\s+độ\s+ngày\s+mai\s+ở\s+đâu|trời\s+có\s+mưa\s+không)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(địa\s+điểm\s+du\s+lịch\s+đẹp|kinh\s+nghiệm\s+phượt|khách\s+sạn\s+giá\s+rẻ\s+ở)",
        re.IGNORECASE,
    ),
    # Partisan Politics & General Geopolitics
    re.compile(
        r"(ai\s+là\s+tổng\s+thống\s+mỹ|bầu\s+cử\s+tổng\s+thống|chính\s+trị\s+gia|đảng\s+phái\s+chính\s+trị|chiến\s+tranh\s+quân\s+sự)",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------------
# Regex Patterns: External Project Creation & Commercial Outsourcing Requests
# (Banned everywhere — LMS is an educational platform, not a freelance developer)
# ---------------------------------------------------------------------------

_EXTERNAL_PROJECT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(lập\s+trình|viết|code|làm|tạo|xây\s+dựng|build)\s+(cho\s+mình|cho\s+tôi|hộ\s+mình|hộ\s+tôi|giúp\s+mình|giúp\s+tôi|dùm\s+mình|dùm\s+tôi)?\s*(1\s+|một\s+)?(trang\s+web|website|web|ứng\s+dụng|app|phần\s+mềm|game|dự\s+án)\s+(bán\s+hàng|thương\s+mại|tin\s+tức|đặt\s+xe|quản\s+lý|bất\s+động\s+sản|mạng\s+xã\s+hội|nhạc|xem\s+phim)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(lập\s+trình|viết|code|làm|build)\s+(cho\s+mình|cho\s+tôi|hộ|giúp|dùm)\s+(1\s+|một\s+)?(trang\s+web|website|web|ứng\s+dụng|app|phần\s+mềm|dự\s+án)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(lập\s+trình|viết\s+code|code\s+giúp|làm\s+hộ|tạo\s+giúp).*(1\s+|một\s+)?(trang\s+web|website|web\s+bán\s+hàng|app\s+bán\s+hàng)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(write|code|build|create)\s+(me\s+)?(a\s+|an\s+)?(full\s+|complete\s+)?(website|web\s+page|store|e-?commerce|shopping|app|application|game|software|project)",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------------
# Keywords / Patterns: In-Scope Domain Indicators (Academic & LMS)
# ---------------------------------------------------------------------------

_GLOBAL_LMS_KEYWORDS: tuple[str, ...] = (
    # LMS Platform & System ("Hệ thống")
    "hệ thống",
    "nền tảng",
    "pwd301",
    "tài khoản",
    "đăng ký",
    "đăng nhập",
    "mật khẩu",
    "email",
    "hồ sơ",
    "vai trò",
    "role",
    "chuyển vai trò",
    "switch role",
    "admin",
    "giảng viên",
    "học viên",
    "ứng tuyển giảng viên",
    "nộp đơn",
    "trở thành giảng viên",
    "xét duyệt",
    "thông báo",
    "chính sách",
    "quy định",
    "hỗ trợ",
    "trợ giúp",
    "help",
    "system",
    "platform",
    "account",
    "password",
    "login",
    "register",
    "enroll",
    "enrollment",
    # Courses & Catalog Guidance ("Khóa học")
    "khóa học",
    "khoá học",
    "course",
    "courses",
    "lộ trình",
    "roadmap",
    "môn học",
    "danh mục",
    "catalog",
    "tìm khóa học",
    "gợi ý khóa học",
    "tư vấn",
    "điều kiện tiên quyết",
    "prerequisite",
    "prerequisites",
    "học phí",
    "miễn phí",
    "chứng chỉ",
    "certificate",
    "chứng nhận",
    "tiến độ",
    "progress",
    "hoàn thành",
    # Platform Usage ("Cách dùng đồ")
    "cách dùng",
    "cách sử dụng",
    "hướng dẫn",
    "how to use",
    "how to",
    "làm sao để",
    "cách học",
    "cách nộp bài",
    "nộp bài",
    "submit",
    "submission",
    "bài tập",
    "assignment",
    "kiểm tra",
    "bài thi",
    "exam",
    "quiz",
    "assessment",
    "bảng điểm",
    "grade",
    "grades",
    "chấm điểm",
    "grading",
    "phúc khảo",
    "regrade",
    "kết quả",
    "result",
    "results",
    "tải chứng chỉ",
    "download certificate",
)

_IN_SCOPE_KEYWORDS: tuple[str, ...] = (
    # Languages & Frameworks
    "html",
    "css",
    "javascript",
    "js",
    "typescript",
    "python",
    "flask",
    "django",
    "sql",
    "postgresql",
    "mysql",
    "sql server",
    "react",
    "vue",
    "angular",
    "node",
    "express",
    "java",
    "spring",
    "c#",
    "c++",
    "golang",
    "rust",
    "php",
    "laravel",
    # Web Concepts & Standards
    "api",
    "rest",
    "restful",
    "json",
    "jwt",
    "http",
    "https",
    "dom",
    "frontend",
    "backend",
    "fullstack",
    "web",
    "website",
    "server",
    "client",
    "session",
    "cookie",
    "cors",
    "csrf",
    "xss",
    "database",
    "cơ sở dữ liệu",
    "bảng",
    "table",
    "truy vấn",
    "query",
    "orm",
    "sqlalchemy",
    "migration",
    "alembic",
    "git",
    "github",
    "docker",
    "container",
    # Computer Science & Algorithms
    "thuật toán",
    "giải thuật",
    "algorithm",
    "cấu trúc dữ liệu",
    "data structure",
    "đệ quy",
    "recursion",
    "sắp xếp",
    "sorting",
    "tìm kiếm",
    "searching",
    "mảng",
    "array",
    "linked list",
    "ngăn xếp",
    "stack",
    "hàng đợi",
    "queue",
    "cây",
    "tree",
    "đồ thị",
    "graph",
    "độ phức tạp",
    "big o",
    "big-o",
    "time complexity",
    "asymptotic",
    "notation",
    "complexity",
    "bộ nhớ",
    "memory",
    "lập trình",
    "coding",
    "code",
    "programming",
    "software",
    "developer",
    "debug",
    "gỡ lỗi",
    "lỗi",
    "error",
    "exception",
    "hàm",
    "function",
    "biến",
    "variable",
    "vòng lặp",
    "loop",
    "loops",
    "syntax",
    "lớp",
    "class",
    "đối tượng",
    "object",
    "kế thừa",
    "oop",
    # Security concepts (defensive/academic)
    "bảo mật",
    "an toàn thông tin",
    "phòng chống",
    "mã hóa",
    "hashing",
    "sha-256",
    "bcrypt",
    "authentication",
    "xác thực",
    "authorization",
    "phân quyền",
    "tấn công xss",
    "tấn công csrf",
    "phòng chống sql injection",
    # LMS & Academic Learning
    "khóa học",
    "course",
    "bài học",
    "lesson",
    "học viên",
    "student",
    "giảng viên",
    "instructor",
    "tutor",
    "study",
    "learn",
    "bài tập",
    "assignment",
    "đề thi",
    "quiz",
    "kiểm tra",
    "assessment",
    "chấm điểm",
    "grading",
    "tiến độ",
    "progress",
    "chứng chỉ",
    "certificate",
    "tài liệu",
    "gợi ý học",
    "lộ trình",
    "roadmap",
    "hướng dẫn học",
    "explain",
)

_POLITE_GREETING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"^(xin\s+)?chào(\s+[a-zA-Z0-9_À-ỹ]+){0,4}[\s!.,?~0-9]*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(hello|hi|hey|good\s+morning|good\s+afternoon)(\s+[a-zA-Z0-9_]+){0,4}[\s!.,?~0-9]*$",
        re.IGNORECASE,
    ),
    re.compile(r"^(bạn\s+là\s+ai|bạn\s+tên\s+gì|giới\s+thiệu\s+về\s+bạn)[\s!?.]*$", re.IGNORECASE),
    re.compile(
        r"^bạn\s+(có\s+thể\s+làm\s+gì|giúp\s+được\s+gì|làm\s+được\s+gì|chức\s+năng\s+là\s+gì).*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(cảm\s+ơn|cảm\s+tạ|thanks|thank\s+you|tạm\s+biệt|bye)(\s+[a-zA-Z0-9_À-ỹ]+){0,4}[\s!.,?~0-9]*$",
        re.IGNORECASE,
    ),
]


def _normalize_text(text: str) -> str:
    """Normalize text for consistent pattern and keyword evaluation."""
    if not text:
        return ""
    # Strip excess whitespace
    return " ".join(text.strip().split())


def classify_query_scope(text: str, context: str | None = None) -> ScopeResult:
    """Evaluate a user query against LMS scope and security guardrails.

    Returns:
        ScopeResult with classification decision, category, refusal message, and reason.
    """
    raw_query = text or ""
    clean_query = _normalize_text(raw_query)

    if not clean_query:
        return ScopeResult(
            is_in_scope=False,
            is_malicious=False,
            category="EMPTY",
            reason="Tin nhắn trống.",
            refusal_message="Vui lòng nhập nội dung câu hỏi học tập.",
            error_code="VALIDATION_ERROR",
        )

    # 1. Check for Malicious / Adversarial / Prompt Injection attacks
    for pat in _MALICIOUS_PATTERNS:
        if pat.search(clean_query):
            logger.warning("Security violation / prompt injection pattern matched: %s", pat.pattern)
            return ScopeResult(
                is_in_scope=False,
                is_malicious=True,
                category="SECURITY_VIOLATION",
                reason="Phát hiện chỉ thị độc hại, hành vi tấn công hệ thống hoặc bẻ khóa prompt.",
                refusal_message=REFUSAL_MESSAGE_SECURITY,
                error_code="PROMPT_INJECTION_DETECTED",
            )

    # 2. Check for explicit Out-of-Scope Non-Academic Topics
    for pat in _OUT_OF_SCOPE_TOPIC_PATTERNS:
        if pat.search(clean_query):
            logger.info("Out-of-scope non-academic topic detected: %s", pat.pattern)
            return ScopeResult(
                is_in_scope=False,
                is_malicious=False,
                category="OUT_OF_SCOPE_TOPIC",
                reason="Chủ đề câu hỏi không thuộc phạm vi học tập hoặc kỹ thuật của hệ thống LMS.",
                refusal_message=REFUSAL_MESSAGE_OUT_OF_SCOPE,
                error_code="OUT_OF_SCOPE",
            )

    # 3. Check for External Project / Commercial Software / Freelance Requests
    for pat in _EXTERNAL_PROJECT_PATTERNS:
        if pat.search(clean_query):
            logger.info("External project creation request rejected: %s", pat.pattern)
            return ScopeResult(
                is_in_scope=False,
                is_malicious=False,
                category="OUT_OF_SCOPE_PROJECT",
                reason="Yêu cầu lập trình gia công hoặc xây dựng website/app ngoài phạm vi LMS.",
                refusal_message=REFUSAL_MESSAGE_EXTERNAL_PROJECT,
                error_code="OUT_OF_SCOPE",
            )

    # 4. Check for standard polite greetings and introductory interactions
    for pat in _POLITE_GREETING_PATTERNS:
        if pat.search(clean_query):
            return ScopeResult(
                is_in_scope=True,
                is_malicious=False,
                category="IN_SCOPE_GREETING",
                reason="Lời chào hoặc câu hỏi giới thiệu trợ lý hợp lệ.",
                refusal_message="",
                error_code=None,
            )

    lower_query = clean_query.lower()
    ctx_upper = (context or "").upper()
    is_course_context = bool("COURSE" in ctx_upper or "LESSON" in ctx_upper)
    is_global_context = bool("GLOBAL" in ctx_upper)
    is_main_page = bool("MAIN_PAGE" in ctx_upper or "PORTAL_SHELL" in ctx_upper)

    has_lms_guidance_kw = any(kw in lower_query for kw in _GLOBAL_LMS_KEYWORDS)
    has_code_syntax = bool(
        re.search(
            r"(\bdef\s+\w+|\bclass\s+\w+|\bimport\s+\w+|function\s*\(|console\.log|=>|;|{|}|<\w+>|<\/\w+>|\bselect\s+.*\s+from\b|\bprint\s*\(|\bvar\s+\w+|\blet\s+\w+|\bconst\s+\w+)",
            clean_query,
            re.IGNORECASE,
        )
    )

    # 5. Global / Main Page Context Enforcement
    is_course_info_query = any(
        w in lower_query
        for w in ("khóa học", "khoá học", "môn học", "lộ trình", "course", "catalog")
    )
    is_code_generation_request = bool(
        has_code_syntax
        or any(
            p in lower_query
            for p in (
                "viết code",
                "viet code",
                "code html",
                "code python",
                "code js",
                "code css",
                "hướng dẫn code",
                "lập trình code",
                "code mẫu",
                "cho xin code",
                "code giúp",
                "lập trình html",
                "lập trình python",
                "lập trình web",
                "lập trình cho",
                "tạo trang web",
                "viết trang web",
                "xây dựng website",
                "lập trình",
                "write code",
                "generate code",
                "program html",
                "coding",
            )
        )
    )

    if is_main_page:
        # On the web main page: strictly only system, courses, and platform usage are permitted
        if is_code_generation_request and not is_course_info_query:
            logger.info(
                "Code generation / technical coding request on main page rejected: %s",
                clean_query[:80],
            )
            return ScopeResult(
                is_in_scope=False,
                is_malicious=False,
                category="OUT_OF_SCOPE_GLOBAL_PAGE",
                reason=(
                    "Trên trang chính chỉ hỗ trợ thông tin hệ thống, khóa học và hướng dẫn "
                    "sử dụng; không lập trình/viết code."
                ),
                refusal_message=REFUSAL_MESSAGE_GLOBAL_CONTEXT,
                error_code="OUT_OF_SCOPE",
            )

        if has_lms_guidance_kw:
            return ScopeResult(
                is_in_scope=True,
                is_malicious=False,
                category="IN_SCOPE_LMS_GUIDANCE",
                reason=(
                    "Nội dung hỏi về hệ thống PWD301, danh mục khóa học hoặc hướng dẫn "
                    "sử dụng nền tảng."
                ),
                refusal_message="",
                error_code=None,
            )

        logger.info(
            "Query on main page outside system/course/usage scope rejected: %s",
            clean_query[:80],
        )
        return ScopeResult(
            is_in_scope=False,
            is_malicious=False,
            category="OUT_OF_SCOPE_GLOBAL_PAGE",
            reason=(
                "Trên trang chính chỉ hỗ trợ thông tin hệ thống, khóa học và hướng dẫn sử dụng; "
                "không giải đáp ngoài phạm vi này."
            ),
            refusal_message=REFUSAL_MESSAGE_GLOBAL_CONTEXT,
            error_code="OUT_OF_SCOPE",
        )

    if is_global_context:
        # In generic global context without course: refuse direct code writing
        if is_code_generation_request and not is_course_info_query:
            logger.info(
                "Code generation request in global context rejected: %s",
                clean_query[:80],
            )
            return ScopeResult(
                is_in_scope=False,
                is_malicious=False,
                category="OUT_OF_SCOPE_GLOBAL_PAGE",
                reason=(
                    "Trong ngữ cảnh chung không có khóa học, không hỗ trợ viết code trực tiếp. "
                    "Vui lòng vào khóa học tương ứng."
                ),
                refusal_message=REFUSAL_MESSAGE_GLOBAL_CONTEXT,
                error_code="OUT_OF_SCOPE",
            )

        if has_lms_guidance_kw:
            return ScopeResult(
                is_in_scope=True,
                is_malicious=False,
                category="IN_SCOPE_LMS_GUIDANCE",
                reason=(
                    "Nội dung hỏi về hệ thống PWD301, danh mục khóa học hoặc hướng dẫn "
                    "sử dụng nền tảng."
                ),
                refusal_message="",
                error_code=None,
            )

    # 6. Inside Course / Academic Context or default test context
    has_in_scope_keyword = any(kw in lower_query for kw in _IN_SCOPE_KEYWORDS)
    if has_in_scope_keyword or has_code_syntax or is_course_context or has_lms_guidance_kw:
        return ScopeResult(
            is_in_scope=True,
            is_malicious=False,
            category="IN_SCOPE_ACADEMIC",
            reason="Nội dung thuộc phạm vi kiến thức học tập, lập trình hoặc tài liệu LMS.",
            refusal_message="",
            error_code=None,
        )

    # 7. Short queries with generic academic questions: "giúp tôi học", "bài tập này làm sao"
    if (
        any(
            phrase in lower_query
            for phrase in ("giúp", "học", "bài", "sách", "lỗi", "sửa", "hướng dẫn", "tại sao")
        )
        and len(clean_query.split()) >= 3
    ):
        return ScopeResult(
            is_in_scope=True,
            is_malicious=False,
            category="IN_SCOPE_ACADEMIC",
            reason="Câu hỏi mang tính chất nhờ trợ giúp học tập tổng quát.",
            refusal_message="",
            error_code=None,
        )

    # 8. Default Fallback: Query contains no academic/technical content and is not recognized
    # Rather than freely answering unrelated questions, safely decline with educational guidance
    logger.info("Unrecognized query outside LMS domain: %s", clean_query[:80])
    return ScopeResult(
        is_in_scope=False,
        is_malicious=False,
        category="OUT_OF_SCOPE_TOPIC",
        reason=(
            "Nội dung không liên quan đến kiến thức lập trình, khoa học máy tính hoặc môn học LMS."
        ),
        refusal_message=REFUSAL_MESSAGE_OUT_OF_SCOPE,
        error_code="OUT_OF_SCOPE",
    )


def classify_query_scope_ai(
    text: str,
    context: str | None = None,
    client: Any = None,
) -> ScopeResult:
    """Evaluate query scope using an AI-powered zero-shot intent guardrail."""
    if client and hasattr(client, "classify_intent"):
        try:
            return client.classify_intent(text, context=context)
        except Exception as exc:
            logger.warning("AI client classify_intent encountered exception: %s", exc)
    return classify_query_scope(text, context=context)


def classify_query_scope_hybrid(
    text: str,
    context: str | None = None,
    client: Any = None,
) -> ScopeResult:
    """Hybrid scope filter combining fast system patterns and AI intent guardrails.

    Execution Flow:
    1. Stage 1 (Fast Pattern Filter - 0 token cost):
       - Instant block on malicious attacks (DDoS, SQLi, Jailbreak).
       - Instant block on known banned topics (cooking, betting, showbiz, crypto...).
       - Instant block on external project creation ('lập trình web bán hàng...').
       - Instant block on raw code generation when on main page surface.
       - Instant pass on polite greetings and LMS platform/course guidance keywords.
    2. Stage 2 (AI-Powered Intent Guardrail):
       - When a query passes Stage 1 or appears academic/technical, verify intent with AI.
       - Prevents tricky prompts designed to 'bào AI' (freelance projects, external homework,
         essays, translation, off-topic chat).
       - If AI classifies as out-of-scope/abuse, refuse immediately without full generation.
    """
    rule_res = classify_query_scope(text, context=context)

    # 1. Definite rejections from rule-based patterns (zero token cost)
    if rule_res.is_malicious:
        return rule_res
    if rule_res.category in (
        "OUT_OF_SCOPE_TOPIC",
        "OUT_OF_SCOPE_PROJECT",
        "OUT_OF_SCOPE_GLOBAL_PAGE",
    ):
        return rule_res

    # 2. Definite passes for greetings and clear system/course info
    if rule_res.category in ("IN_SCOPE_GREETING", "IN_SCOPE_LMS_GUIDANCE"):
        return rule_res

    # 3. If AI client provided, invoke AI intent guardrail to stop subtle 'bào AI' attempts
    if client and hasattr(client, "classify_intent"):
        ai_res = client.classify_intent(text, context=context)
        if not ai_res.is_in_scope or ai_res.is_malicious:
            return ai_res

    return rule_res

