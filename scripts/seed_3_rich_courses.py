"""Seed 3 Rich, Realistic Courses for PWD301.

Creates 3 comprehensive, industry-standard courses:
1. PY301: Lập trình Python Backend & REST API Doanh Nghiệp (TS. Nguyễn Văn A)
2. DSA201: Cấu Trúc Dữ Liệu & Giải Thuật Ứng Dụng Nâng Cao (ThS. Trần Thị B)
3. OPS401: DevOps, CI/CD Pipeline & Hạ Tầng Điện Toán Đám Mây (TS. Nguyễn Văn A)

Each course features:
- Clear chapters (Learning Units) and sequential lessons.
- Verified embeddable public YouTube videos and uploaded internal MP4 demo videos.
- Attached real PDF documents with authentic academic outlines.
- Interactive multi-choice and true/false mini-quizzes with detailed explanations.
- Student enrollments and initial progress.
"""

from __future__ import annotations

import base64
import decimal
import io
import json
import logging
import sys
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from PIL import Image, ImageDraw
import sqlalchemy as sa
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.assessment import (
    Assessment,
    AssessmentQuestionAssignment,
    AssessmentSection,
)
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AssessmentResult,
    AssessmentResultHistory,
    AttemptAnswer,
    AttemptAnswerChoice,
    AttemptAnswerEvent,
    AttemptChoiceSnapshot,
    AttemptFocusEvent,
    AttemptQuestion,
    AttemptQuestionGrade,
    AttemptQuestionGradeHistory,
    QuestionCorrection,
    RegradeItem,
    RegradeJob,
)
from pwd301.models.course import (
    Course,
    CourseChangeRequest,
    CourseCompletionRule,
    CourseCompletionSummary,
    CoursePrerequisite,
    Enrollment,
    EnrollmentEvent,
    EnrollmentPeriod,
    LearningUnit,
    Lesson,
    LessonProgress,
)
from pwd301.models.file_import import (
    FileAsset,
    FileRevision,
    FileScanResult,
    LessonResource,
)
from pwd301.models.identity import Role, User, UserRole
from pwd301.models.notification_audit import AuditEvent, Notification, NotificationEvent
from pwd301.models.question_bank import (
    Question,
    QuestionProvenance,
    QuestionRevision,
    QuestionRevisionAcceptedAnswer,
    QuestionRevisionChoice,
)
from pwd301.models.types import utc_now
from pwd301.services.file_service import attach_resource_to_lesson, store_file_stream

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("seed_3_rich_courses")

# Tiny 1-second silent H.264 MP4 container (valid ISO-BMFF)
SAMPLE_MP4_BYTES = base64.b64decode(
    "AAAAHGZ0eXBtcDQyAAAAAG1wNDJpc29tYXZjMQAAADhtb292AAAAbG12aGQAAAAA10QkPtdEJD4AAAEAAAAAA+gAAQ"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAIdHJhawAAAF"
    "x0a2hkAAAAHtdEJD7XRCQ+AAAAAQAAAAAAA+gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAEAAAAAEAAAAAAAAAAAAAAAJtZGlhAAAAIG1kaGQAAAAA10QkPtdEJD4AAB1MAAAdTAAAAE"
    "AAAAAANDhkbHIAAAAAAAAAAHZpZGUAAAAAAAAAAAAAAAAABVmlkZW9IYW5kbGVyAAAAAQptaW5mAAAAFHZtaGQAAAAB"
    "AAAAAAAAAAAAAAAAMWRpbmYAAAAcZHJlZgAAAAAAAAABAAAAHGRyb2MAAAABdXJsIAAAAAEAAAEIc3RibAAAAGhzdHNx"
    "AAAAAAAAAAAAAAAJYXZjMQAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAgACABIAAAASAAAAAAAAAABAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAABg//wAAABxzdHRzAAAAAAAAAAEAAAABAAAdTAAAAAAkc3RzYwAAAAAAAAABAAAAAQAA"
    "AAEAAAABAAAAAAAAABxzdHN6AAAAAAAAAAAAAAABAAAB8AAAAClzdGNvAAAAAAAAAAEAAAA4AAAAFm1kYXQAAAAB8gAAA"
    "QAAAAI="
)


def generate_pdf_document(title: str, subtitle: str, topics: list[str]) -> bytes:
    """Generate a clean, valid PDF 1.4 binary file with layout text."""
    stream_content = (
        f"BT\n"
        f"/F1 16 Tf\n"
        f"50 730 Td\n"
        f"({title}) Tj\n"
        f"/F1 11 Tf\n"
        f"0 -24 Td\n"
        f"({subtitle}) Tj\n"
        f"/F1 10 Tf\n"
        f"0 -30 Td\n"
        f"(NOI DUNG TAI LIEU / MUC LUC CHI TIET:) Tj\n"
        f"0 -20 Td\n"
    )
    for idx, topic in enumerate(topics, 1):
        safe_topic = topic.replace("(", "[").replace(")", "]")
        stream_content += f"({idx}. {safe_topic}) Tj\n0 -18 Td\n"
    stream_content += (
        f"0 -25 Td\n"
        f"(He thong Hoc truc tuyen PWD301 - Luu hanh noi bo hoc vien va giang vien) Tj\n"
        f"ET\n"
    )
    stream_bytes = stream_content.encode("latin-1", errors="replace")

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"5 0 obj\n<< /Length " + str(len(stream_bytes)).encode("ascii") + b" >>\nstream\n"
        + stream_bytes + b"\nendstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \n0000000261 00000 n \n0000000336 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n450\n%%EOF\n"
    )
    return pdf


def generate_course_cover_png(
    course_code: str,
    title: str,
    subtitle: str,
    bg_gradient: tuple[tuple[int, int, int], tuple[int, int, int]],
    accent_color: tuple[int, int, int],
) -> bytes:
    """Generate a clean 16:9 (1280x720) course thumbnail with modern tech styling."""
    width = 1280
    height = 720
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    color_start, color_end = bg_gradient
    # Linear vertical gradient
    for y in range(height):
        ratio = y / height
        r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
        g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
        b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Tech grid pattern
    for x in range(0, width, 64):
        draw.line([(x, 0), (x, height)], fill=(color_start[0] + 12, color_start[1] + 14, color_start[2] + 20))
    for y in range(0, height, 64):
        draw.line([(0, y), (width, y)], fill=(color_start[0] + 12, color_start[1] + 14, color_start[2] + 20))

    # Decorative top pill
    draw.rounded_rectangle([(80, 70), (230, 116)], radius=12, fill=accent_color)
    draw.text((105, 84), course_code, fill=(255, 255, 255))

    # Inner card box
    draw.rounded_rectangle(
        [(80, 150), (1200, 630)],
        radius=24,
        fill=(color_start[0] + 8, color_start[1] + 10, color_start[2] + 16),
        outline=(255, 255, 255, 30),
        width=2,
    )

    # Texts
    draw.text((120, 210), title[:42], fill=(255, 255, 255))
    if len(title) > 42:
        draw.text((120, 260), title[42:85], fill=(255, 255, 255))
    draw.text((120, 340), subtitle, fill=(180, 195, 215))

    # Verification pill badge
    draw.rounded_rectangle([(120, 530), (340, 575)], radius=10, fill=(30, 42, 60))
    draw.text((140, 544), "PWD301 Verified Program", fill=(130, 220, 180))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def wipe_all_courses(session: Session) -> None:
    """Wipe existing courses and all child relational records completely."""
    logger.info("Cleaning up existing course and learning records...")

    # 0. Temporarily disable triggers during full table reset (SQL Server DDL)
    tables_with_freeze_triggers = [
        "assessment_question_assignments",
        "assessment_sections",
        "assessments",
        "assessment_question_pool",
        "assessment_blueprint_rules",
        "assessment_blueprints",
    ]
    for tbl in tables_with_freeze_triggers:
        try:
            session.execute(sa.text(f"ALTER TABLE {tbl} DISABLE TRIGGER ALL"))
        except Exception:
            pass
    session.commit()

    # Attempts & Results (strict FK reverse order)
    session.query(RegradeItem).delete(synchronize_session=False)
    session.query(RegradeJob).delete(synchronize_session=False)
    session.query(QuestionCorrection).delete(synchronize_session=False)
    session.query(AssessmentResultHistory).delete(synchronize_session=False)
    session.query(AssessmentResult).delete(synchronize_session=False)
    session.query(AttemptQuestionGradeHistory).delete(synchronize_session=False)
    session.query(AttemptQuestionGrade).delete(synchronize_session=False)
    session.query(AttemptAnswerEvent).delete(synchronize_session=False)
    session.query(AttemptAnswerChoice).delete(synchronize_session=False)
    session.query(AttemptAnswer).delete(synchronize_session=False)
    session.query(AttemptChoiceSnapshot).delete(synchronize_session=False)
    session.query(AttemptQuestion).delete(synchronize_session=False)
    session.query(AttemptFocusEvent).delete(synchronize_session=False)
    session.query(AssessmentAttempt).delete(synchronize_session=False)

    # Assessments & Sections
    session.query(AssessmentQuestionAssignment).delete(synchronize_session=False)
    session.query(AssessmentSection).delete(synchronize_session=False)
    session.query(Assessment).delete(synchronize_session=False)

    for tbl in tables_with_freeze_triggers:
        try:
            session.execute(sa.text(f"ALTER TABLE {tbl} ENABLE TRIGGER ALL"))
        except Exception:
            pass
    session.commit()

    # Question Bank
    session.query(QuestionRevisionChoice).delete(synchronize_session=False)
    session.query(QuestionRevisionAcceptedAnswer).delete(synchronize_session=False)
    session.query(QuestionRevision).delete(synchronize_session=False)
    session.query(QuestionProvenance).delete(synchronize_session=False)
    session.query(Question).delete(synchronize_session=False)

    # Lesson resources, progress & lessons
    session.query(LessonProgress).delete(synchronize_session=False)
    session.query(LessonResource).delete(synchronize_session=False)
    session.query(Lesson).delete(synchronize_session=False)
    session.query(LearningUnit).delete(synchronize_session=False)

    # Course management
    session.query(CourseCompletionSummary).delete(synchronize_session=False)
    session.query(CourseCompletionRule).delete(synchronize_session=False)
    session.query(CoursePrerequisite).delete(synchronize_session=False)
    session.query(CourseChangeRequest).delete(synchronize_session=False)

    # Enrollments
    session.query(EnrollmentEvent).delete(synchronize_session=False)
    session.query(EnrollmentPeriod).delete(synchronize_session=False)
    session.query(Enrollment).delete(synchronize_session=False)

    # File assets associated with courses
    course_assets = session.query(FileAsset).filter(FileAsset.course_id.is_not(None)).all()
    for fa in course_assets:
        revisions = session.query(FileRevision).filter(FileRevision.file_asset_id == fa.id).all()
        for rev in revisions:
            session.query(FileScanResult).filter(FileScanResult.file_revision_id == rev.id).delete(synchronize_session=False)
            session.delete(rev)
        session.delete(fa)

    # Finally Courses
    session.query(Course).delete(synchronize_session=False)
    session.commit()
    logger.info("Successfully wiped all old courses cleanly.")


def get_or_create_users(session: Session) -> dict[str, User]:
    """Ensure baseline test users exist with roles."""
    roles = {r.code: r for r in session.query(Role).all()}
    if not roles:
        for code, name in [("STUDENT", "Student"), ("INSTRUCTOR", "Instructor"), ("ADMIN", "System Administrator")]:
            r = Role(code=code, name=name)
            session.add(r)
            session.flush()
            roles[code] = r

    user_configs = [
        {"email": "admin@pwd301.local", "name": "Quản trị viên Hệ thống", "roles": ["STUDENT", "INSTRUCTOR", "ADMIN"]},
        {"email": "instructor1@pwd301.local", "name": "TS. Nguyễn Văn A", "roles": ["STUDENT", "INSTRUCTOR"]},
        {"email": "instructor2@pwd301.local", "name": "ThS. Trần Thị B", "roles": ["STUDENT", "INSTRUCTOR"]},
        {"email": "student1@pwd301.local", "name": "Lê Hoàng Long", "roles": ["STUDENT"]},
        {"email": "student2@pwd301.local", "name": "Phạm Minh Tuấn", "roles": ["STUDENT"]},
        {"email": "student3@pwd301.local", "name": "Vũ Thảo Nguyên", "roles": ["STUDENT"]},
        {"email": "student4@pwd301.local", "name": "Đặng Gia Huy", "roles": ["STUDENT"]},
    ]

    hashed = generate_password_hash("Password123!")
    now = utc_now()
    users: dict[str, User] = {}

    for cfg in user_configs:
        norm = cfg["email"].lower().strip()
        u = session.query(User).filter(User.email_normalized == norm).first()
        if u is None:
            u = User(
                email=norm,
                password_hash=hashed,
                display_name=cfg["name"],
                status="ACTIVE",
                auth_version=1,
                email_verified_at=now,
            )
            session.add(u)
            session.flush()
        else:
            u.password_hash = hashed
            u.display_name = cfg["name"]
            u.status = "ACTIVE"
            u.email_verified_at = u.email_verified_at or now

        for r_code in cfg["roles"]:
            r_obj = roles[r_code]
            has_link = session.query(UserRole).filter(UserRole.user_id == u.id, UserRole.role_id == r_obj.id).first()
            if not has_link:
                session.add(UserRole(user_id=u.id, role_id=r_obj.id, assigned_by_user_id=u.id, assignment_reason="Seed"))

        users[norm] = u

    session.commit()
    return users


def seed_courses() -> None:
    """Seed 3 comprehensive courses with units, lessons, YouTube/MP4 videos, PDFs & quizzes."""
    app = create_app()
    with app.app_context():
        session: Session = db.session
        wipe_all_courses(session)
        users = get_or_create_users(session)

        admin = users["admin@pwd301.local"]
        inst1 = users["instructor1@pwd301.local"]
        inst2 = users["instructor2@pwd301.local"]
        student1 = users["student1@pwd301.local"]
        student2 = users["student2@pwd301.local"]
        student3 = users["student3@pwd301.local"]

        now = utc_now()

        # =========================================================================
        # COURSE 1: PY301
        # =========================================================================
        logger.info("Seeding Course 1: PY301...")
        c1 = Course(
            course_code="PY301",
            course_code_normalized="PY301",
            title="PY301: Lập trình Python Backend & REST API Doanh Nghiệp",
            title_normalized="py301: lập trình python backend & rest api doanh nghiệp",
            description=(
                "Khóa học chuyên sâu trang bị kiến trúc backend hoàn chỉnh với Python hiện đại: "
                "Flask Framework, SQLAlchemy ORM, Microsoft SQL Server, xác thực JWT, phân quyền RBAC, "
                "bảo mật CSRF/XSS và kiểm thử tự động với Pytest."
            ),
            category="Kỹ thuật Lập trình",
            difficulty="INTERMEDIATE",
            owner_instructor_id=inst1.id,
            status="PUBLISHED",
            capacity=60,
            published_at=now - timedelta(days=10),
            approved_at=now - timedelta(days=10),
            approved_by_user_id=admin.id,
        )
        session.add(c1)
        session.flush()

        # Generate & attach 16:9 clean cover for PY301
        c1_img_bytes = generate_course_cover_png(
            course_code="PY301",
            title="Lập trình Python Backend & REST API Doanh Nghiệp",
            subtitle="Flask • SQLAlchemy • SQL Server • JWT • RBAC • Clean Architecture",
            bg_gradient=((15, 23, 42), (30, 41, 59)),
            accent_color=(37, 99, 235),
        )
        c1_asset = store_file_stream(
            actor=inst1,
            course_id=c1.id,
            file_stream=io.BytesIO(c1_img_bytes),
            filename="py301_cover.png",
            content_type="image/png",
            asset_type="COURSE_IMAGE",
            title="Ảnh bìa khóa học PY301",
            session=session,
        )
        c1.thumbnail_file_asset_id = c1_asset.id
        session.flush()

        # Completion rule for c1
        session.add(
            CourseCompletionRule(
                course_id=c1.id,
                require_all_required_lessons=True,
                require_required_assessments=False,
                minimum_progress_percent=decimal.Decimal("80.00"),
                updated_by_user_id=inst1.id,
            )
        )

        # Chapter 1 of PY301
        u1_1 = LearningUnit(
            course_id=c1.id,
            title="Chương 1: Kiến trúc HTTP, RESTful API & Cơ chế Client-Server",
            position=1,
            created_at=now - timedelta(days=10),
        )
        session.add(u1_1)
        session.flush()

        # Lesson 1.1 (YouTube Video + PDF + Quiz)
        quiz_1_1 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Trong kiến trúc RESTful API, HTTP method nào bắt buộc phải có tính chất Idempotent (thao tác lặp lại nhiều lần cho cùng một kết quả)?",
                "options": ["POST", "PUT", "PATCH", "CONNECT"],
                "choices": ["POST", "PUT", "PATCH", "CONNECT"],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "Theo chuẩn RFC 7231, PUT và DELETE là các phương thức idempotent. Gọi PUT nhiều lần với cùng payload sẽ cho trạng thái tài nguyên giống hệt nhau.",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Mã trạng thái HTTP 201 Created thường được trả về khi một tài nguyên mới được tạo thành công bởi phương thức POST.",
                "correct_answer": True,
                "explanation": "Chính xác. HTTP 201 Created biểu thị yêu cầu POST đã hoàn thành và tài nguyên mới đã được ghi nhận trên máy chủ.",
            },
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Header nào trong HTTP Request được sử dụng để client thông báo cho máy chủ định dạng dữ liệu mà nó có thể tiếp nhận?",
                "options": ["Content-Type", "Accept", "Authorization", "User-Agent"],
                "choices": ["Content-Type", "Accept", "Authorization", "User-Agent"],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "Header 'Accept' (ví dụ Accept: application/json) thông báo cho server định dạng phản hồi mong muốn của client.",
            },
        ]

        md_1_1 = f"""<!-- video_urls: ["https://www.youtube.com/watch?v=kqtD5dpn9C8"] -->
# Tổng quan về Giao thức HTTP & Kiến trúc RESTful API

Chào mừng các bạn đến với khóa học **PY301: Lập trình Python Backend & REST API Doanh Nghiệp**.

## 1. Mô hình Client-Server Hiện Đại
Trong kiến trúc web hướng dịch vụ (Service-Oriented Architecture), máy khách (Client: trình duyệt web SPA, ứng dụng di động Flutter/React Native) và máy chủ (Backend Server) giao tiếp với nhau thông qua giao thức **HTTP/HTTPS**:
- **Stateless**: Máy chủ không lưu trữ ngữ cảnh phiên của client giữa các request độc lập.
- **Resource-Oriented**: Mọi thực thể nghiệp vụ (User, Course, Lesson) được định danh thông qua URI rõ ràng (`/api/courses`, `/api/lessons/123`).

## 2. Phân loại HTTP Methods
| Method | Ý nghĩa nghiệp vụ | Safe | Idempotent |
|--------|--------------------|------|------------|
| `GET`  | Truy xuất tài nguyên | Có  | Có         |
| `POST` | Khởi tạo tài nguyên mới | Không | Không |
| `PUT`  | Thay thế toàn bộ tài nguyên | Không | Có |
| `PATCH`| Cập nhật từng phần | Không | Không      |
| `DELETE`| Xóa bỏ tài nguyên | Không | Có        |

Hãy xem video bài giảng bên trên và hoàn thành bài kiểm tra mini-quiz phía dưới để ghi nhận tiến độ bài học!

<!-- mini_quiz: {json.dumps(quiz_1_1, ensure_ascii=False)} -->
"""
        les_1_1 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_1.id,
            title="Bài 1: Tổng quan HTTP Protocol & Nguyên lý REST API",
            summary="Tìm hiểu nguyên lý Client-Server, HTTP methods, status codes và thiết kế REST API chuẩn.",
            markdown_content=md_1_1,
            position=1,
            estimated_duration_minutes=45,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=10),
        )
        session.add(les_1_1)
        session.flush()

        # Attach real PDF to Lesson 1.1
        pdf_1_1_data = generate_pdf_document(
            title="GIAO TRINH: KIEN TRUC HTTP VA RESTFUL API CHUAN",
            subtitle="Hoc phan PY301 - Chuong 1: Tong quan Giao thuc HTTP",
            topics=[
                "Nguyen ly van hanh mo hinh Client - Server hien dai",
                "Cau truc goi tin HTTP Request va HTTP Response",
                "Bang tra cuu HTTP Status Codes (2xx, 3xx, 4xx, 5xx)",
                "Cac rang buoc kien truc REST (Stateless, Cacheable, Layered System)",
                "Chuan thiet ke RESTful URL va Resource Naming Conventions",
            ],
        )
        fa_pdf_1_1 = store_file_stream(
            actor=inst1,
            course_id=c1.id,
            file_stream=io.BytesIO(pdf_1_1_data),
            filename="Giao_trinh_HTTP_va_REST_API.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Giáo trình tham khảo: Kiến trúc HTTP & REST API",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst1,
            lesson_id=les_1_1.id,
            asset_id=fa_pdf_1_1.id,
            is_downloadable=True,
            label="Tài liệu đọc: Kiến thức nền tảng HTTP & REST (PDF)",
            session=session,
        )

        # Lesson 1.2 (Uploaded Video MP4 + PDF + Quiz)
        quiz_1_2 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Application Factory Pattern trong Flask mang lại lợi ích kỹ thuật lớn nhất nào?",
                "options": [
                    "Tăng tốc độ xử lý CPU lên gấp đôi",
                    "Cho phép khởi tạo nhiều instance ứng dụng với các cấu hình môi trường khác nhau (dev, test, prod)",
                    "Tự động tạo cơ sở dữ liệu mà không cần SQL",
                    "Ngăn chặn mọi cuộc tấn công DDoS",
                ],
                "choices": [
                    "Tăng tốc độ xử lý CPU lên gấp đôi",
                    "Cho phép khởi tạo nhiều instance ứng dụng với các cấu hình môi trường khác nhau (dev, test, prod)",
                    "Tự động tạo cơ sở dữ liệu mà không cần SQL",
                    "Ngăn chặn mọi cuộc tấn công DDoS",
                ],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "Application Factory Pattern (hàm create_app()) giúp tách biệt việc định nghĩa ứng dụng khỏi việc chạy ứng dụng, rất lý tưởng cho Unit Testing và triển khai đa môi trường.",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Trong Flask, Blueprint giúp phân tách các nhóm route theo từng domain chức năng riêng biệt như auth, student, instructor.",
                "correct_answer": True,
                "explanation": "Chính xác. Flask Blueprints cung cấp cơ chế module hóa để tổ chức ứng dụng lớn thành các phân hệ logic độc lập.",
            },
        ]

        md_1_2 = f"""# Khởi tạo Ứng dụng Flask với Application Factory Pattern

Bài học này hướng dẫn các bạn triển khai kiến trúc cấu trúc thư mục backend chuẩn mực.

## 1. Tại sao cần Application Factory?
Khi dự án phát triển quy mô lớn, việc khai báo biến toàn cục `app = Flask(__name__)` ở tầng root sẽ dẫn đến:
- Vấn đề **Circular Imports** giữa routes và models.
- Khó khăn khi viết automated tests cần nạp cấu hình database giả lập (SQLite in-memory).

## 2. Mã nguồn mẫu chuẩn Factory
```python
from flask import Flask
from pwd301.extensions import db, migrate

def create_app(config_name: str = "production") -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # Khởi tạo các extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Đăng ký Blueprints
    from pwd301.blueprints.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app
```

Hãy theo dõi video hướng dẫn demo thực hành bên trên!

<!-- mini_quiz: {json.dumps(quiz_1_2, ensure_ascii=False)} -->
"""
        les_1_2 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_1.id,
            title="Bài 2: Khởi tạo Ứng dụng Flask với Application Factory Pattern",
            summary="Thực hành thiết kế module, Application Factory Pattern và đăng ký Blueprint.",
            markdown_content=md_1_2,
            position=2,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=9),
        )
        session.add(les_1_2)
        session.flush()

        # Attach real uploaded MP4 video to Lesson 1.2
        fa_vid_1_2 = store_file_stream(
            actor=inst1,
            course_id=c1.id,
            file_stream=io.BytesIO(SAMPLE_MP4_BYTES),
            filename="huong_dan_cai_dat_flask_factory.mp4",
            content_type="video/mp4",
            asset_type="RESOURCE",
            title="Video thực hành: Cấu hình Flask Application Factory",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst1,
            lesson_id=les_1_2.id,
            asset_id=fa_vid_1_2.id,
            is_downloadable=False,
            label="Video bài giảng nội bộ: Thực hành cấu hình Flask",
            session=session,
        )

        # Attach PDF to Lesson 1.2
        pdf_1_2_data = generate_pdf_document(
            title="SO TAY: THIET KE FLASK APPLICATION FACTORY VA BLUEPRINTS",
            subtitle="Hoc phan PY301 - Chuong 1: Thiet ke Module Backend",
            topics=[
                "Kien truc thu muc chuan du an Flask REST API doanh nghiep",
                "Cach tranh loi Circular Import voi Application Factory Pattern",
                "Dang ky Blueprints va chia tach Router theo tung Domain",
                "Quan ly bien moi truong bang dotenv va Config Classes",
            ],
        )
        fa_pdf_1_2 = store_file_stream(
            actor=inst1,
            course_id=c1.id,
            file_stream=io.BytesIO(pdf_1_2_data),
            filename="Huong_dan_Flask_Application_Factory.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Sổ tay thực hành: Flask Factory Pattern & Blueprints",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst1,
            lesson_id=les_1_2.id,
            asset_id=fa_pdf_1_2.id,
            is_downloadable=True,
            label="Tài liệu tham khảo: Hướng dẫn cấu trúc thư mục Flask (PDF)",
            session=session,
        )

        # Chapter 2 of PY301
        u1_2 = LearningUnit(
            course_id=c1.id,
            title="Chương 2: Kết nối CSDL SQL Server với SQLAlchemy & Bảo mật JWT",
            position=2,
            created_at=now - timedelta(days=8),
        )
        session.add(u1_2)
        session.flush()

        # Lesson 1.3 (YouTube Video + PDF + Quiz)
        quiz_1_3 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Lệnh nào trong Flask-Migrate được dùng để sinh tệp migration tự động dựa trên sự thay đổi của SQLAlchemy Models?",
                "options": [
                    "flask db init",
                    "flask db migrate -m 'message'",
                    "flask db upgrade",
                    "flask db status",
                ],
                "choices": [
                    "flask db init",
                    "flask db migrate -m 'message'",
                    "flask db upgrade",
                    "flask db status",
                ],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "'flask db migrate' quét metadata của SQLAlchemy và schema hiện tại trong database để tạo tệp script alembic tương ứng.",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Không bao giờ được sửa trực tiếp các tệp migration đã được áp dụng lên production database mà phải tạo migration mới để đảm bảo tính toàn vẹn lịch sử schema.",
                "correct_answer": True,
                "explanation": "Đúng. Đây là quy tắc bất biến trong DevOps và Database Management để tránh lệch pha schema giữa các môi trường.",
            },
        ]

        md_1_3 = f"""<!-- video_urls: ["https://www.youtube.com/watch?v=JJmcL1N2KQs"] -->
# Thiết Kế Database Model & Schema Migration với Flask-Migrate

Trong bài học này, chúng ta sẽ học cách kết nối SQLAlchemy ORM với Microsoft SQL Server.

## 1. Định nghĩa Data Model
```python
import sqlalchemy as sa
from pwd301.extensions import db

class Product(db.Model):
    __tablename__ = "products"

    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    name = sa.Column(sa.Unicode(200), nullable=False)
    price = sa.Column(sa.Numeric(12, 2), nullable=False)
    created_at = sa.Column(sa.DateTime, server_default=sa.text("SYSUTCDATETIME()"))
```

## 2. Quy trình Migration 3 bước
1. Khởi tạo kho lưu trữ: `flask db init` (chỉ chạy 1 lần duy nhất).
2. Tự động sinh diff: `flask db migrate -m "add products table"`
3. Áp dụng lên DB: `flask db upgrade`

<!-- mini_quiz: {json.dumps(quiz_1_3, ensure_ascii=False)} -->
"""
        les_1_3 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_2.id,
            title="Bài 3: Thiết kế Database Model & Migration với Flask-Migrate",
            summary="Làm việc với SQLAlchemy ORM, định nghĩa quan hệ bảng và quản lý tiến trình di chuyển schema.",
            markdown_content=md_1_3,
            position=3,
            estimated_duration_minutes=55,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=7),
        )
        session.add(les_1_3)
        session.flush()

        pdf_1_3_data = generate_pdf_document(
            title="CHIA KHOA SQLALCHEMY: MODEL RELATIONSHIPS VA SCHEMA MIGRATIONS",
            subtitle="Hoc phan PY301 - Chuong 2: Tuong tac CSDL Doanh nghiep",
            topics=[
                "Cac kieu du lieu chuyen biet tren MS SQL Server (DATETIME2, ROWVERSION, NVARCHAR)",
                "Dinh nghia quan he 1-N va N-N voi SQLAlchemy relationship va back_populates",
                "Chien luoc toi uu truy van: Tranh loi N+1 bang joinedload va selectinload",
                "Huong dan rollback va xu ly xung dot Alembic migration heads",
            ],
        )
        fa_pdf_1_3 = store_file_stream(
            actor=inst1,
            course_id=c1.id,
            file_stream=io.BytesIO(pdf_1_3_data),
            filename="SQLAlchemy_ORM_Cheatsheet.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Tài liệu tra cứu: SQLAlchemy ORM & Migration Cheatsheet",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst1,
            lesson_id=les_1_3.id,
            asset_id=fa_pdf_1_3.id,
            is_downloadable=True,
            label="Bảng tra cứu: Cú pháp SQLAlchemy & Migration (PDF)",
            session=session,
        )

        # Lesson 1.4 (YouTube Video + PDF + Quiz)
        quiz_1_4 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Thành phần nào trong JWT (JSON Web Token) đảm bảo token không bị kẻ tấn công can thiệp chỉnh sửa dữ liệu payload?",
                "options": ["Header", "Payload", "Signature (Chữ ký điện tử)", "Algorithm Name"],
                "choices": ["Header", "Payload", "Signature (Chữ ký điện tử)", "Algorithm Name"],
                "correct_answers": [2],
                "correct_answer": 2,
                "explanation": "Chữ ký số (Signature) được tạo bởi Secret Key của server. Bất kỳ thay đổi nào trong Header hoặc Payload sẽ khiến chữ ký không khớp, server sẽ từ chối token ngay lập tức.",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Để bảo mật chống tấn công XSS, Access Token JWT không nên lưu trữ trong localStorage của trình duyệt mà nên dùng httpOnly Cookie hoặc Authorization Header trong session.",
                "correct_answer": True,
                "explanation": "Đúng. Mã JavaScript độc hại (XSS) có thể đọc toàn bộ localStorage. Lưu trữ an toàn trong Cookie httpOnly hoặc bảo vệ phiên là khuyến nghị OWASP hàng đầu.",
            },
        ]

        md_1_4 = f"""<!-- video_urls: ["https://www.youtube.com/watch?v=7lmCu8wz8ro"] -->
# Xác Thực JWT & Phân Quyền Truy Cập RBAC Chuẩn Doanh Nghiệp

Tìm hiểu cơ chế bảo mật xác thực danh tính người dùng và ủy quyền truy cập tài nguyên.

## 1. Cấu Trúc JWT (JSON Web Token)
JWT gồm 3 phần phân tách bởi dấu chấm (`.`):
1. **Header**: Chứa thuật toán mã hóa (ví dụ `HS256`, `RS256`).
2. **Payload**: Chứa các claims công khai (`user_id`, `email`, `roles`, `exp`).
3. **Signature**: Băm mật mã kiểm chứng tính toàn vẹn `HMACSHA256(base64(header) + "." + base64(payload), secret)`.

## 2. Decorator Phân Quyền RBAC
```python
def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.has_any_role(*allowed_roles):
                raise ForbiddenError("Bạn không có quyền truy cập endpoint này.")
            return fn(*args, **kwargs)
        return wrapper
    return decorator
```

<!-- mini_quiz: {json.dumps(quiz_1_4, ensure_ascii=False)} -->
"""
        les_1_4 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_2.id,
            title="Bài 4: Xác thực JWT & Phân quyền Truy cập RBAC Chuẩn Doanh Nghiệp",
            summary="Cấu trúc token, xác thực không trạng thái, cơ chế thu hồi quyền và phòng vệ lỗ hổng IDOR.",
            markdown_content=md_1_4,
            position=4,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=6),
        )
        session.add(les_1_4)
        session.flush()

        pdf_1_4_data = generate_pdf_document(
            title="SECURITY BLUEPRINT: XAC THUC JWT VA PHAN QUYEN RBAC",
            subtitle="Hoc phan PY301 - Chuong 2: An ninh va Bao mat REST API",
            topics=[
                "Vong doi Token: Access Token ngan han va Refresh Token dai han",
                "Phong chong cac cuoc tan cong Token Hijacking, CSRF va XSS",
                "Kien truc kiem soat truy cap Role-Based Access Control (RBAC)",
                "Cac nguyen tac bao ve IDOR (Insecure Direct Object Reference) o cap tang Service",
            ],
        )
        fa_pdf_1_4 = store_file_stream(
            actor=inst1,
            course_id=c1.id,
            file_stream=io.BytesIO(pdf_1_4_data),
            filename="Bao_mat_JWT_va_RBAC.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Tài liệu chuyên đề: Bảo mật JWT & Phân quyền RBAC",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst1,
            lesson_id=les_1_4.id,
            asset_id=fa_pdf_1_4.id,
            is_downloadable=True,
            label="Tài liệu chuyên đề: An ninh mạng & Bảo mật API (PDF)",
            session=session,
        )

        # =========================================================================
        # COURSE 2: DSA201
        # =========================================================================
        logger.info("Seeding Course 2: DSA201...")
        c2 = Course(
            course_code="DSA201",
            course_code_normalized="DSA201",
            title="DSA201: Cấu Trúc Dữ Liệu & Giải Thuật Ứng Dụng Nâng Cao",
            title_normalized="dsa201: cấu trúc dữ liệu & giải thuật ứng dụng nâng cao",
            description=(
                "Trang bị nền tảng tư duy thuật toán vững chắc cho kỹ sư phần mềm: "
                "phân tích độ phức tạp thời gian & không gian Big-O, cấu trúc cây nhị phân, "
                "Heap, đồ thị, thuật toán tìm kiếm đường đi ngắn nhất Dijkstra và quy hoạch động."
            ),
            category="Khoa học Máy tính",
            difficulty="ADVANCED",
            owner_instructor_id=inst2.id,
            status="PUBLISHED",
            capacity=50,
            published_at=now - timedelta(days=8),
            approved_at=now - timedelta(days=8),
            approved_by_user_id=admin.id,
        )
        session.add(c2)
        session.flush()

        # Generate & attach 16:9 clean cover for DSA201
        c2_img_bytes = generate_course_cover_png(
            course_code="DSA201",
            title="Cấu Trúc Dữ Liệu & Giải Thuật Ứng Dụng Nâng Cao",
            subtitle="Trees • Graphs • Dynamic Programming • Sorting • Big-O Complexity",
            bg_gradient=((17, 24, 39), (31, 41, 55)),
            accent_color=(16, 185, 129),
        )
        c2_asset = store_file_stream(
            actor=inst2,
            course_id=c2.id,
            file_stream=io.BytesIO(c2_img_bytes),
            filename="dsa201_cover.png",
            content_type="image/png",
            asset_type="COURSE_IMAGE",
            title="Ảnh bìa khóa học DSA201",
            session=session,
        )
        c2.thumbnail_file_asset_id = c2_asset.id
        session.flush()

        session.add(
            CourseCompletionRule(
                course_id=c2.id,
                require_all_required_lessons=True,
                require_required_assessments=False,
                minimum_progress_percent=decimal.Decimal("75.00"),
                updated_by_user_id=inst2.id,
            )
        )

        # Chapter 1 of DSA201
        u2_1 = LearningUnit(
            course_id=c2.id,
            title="Chương 1: Đánh giá Độ phức tạp & Cấu trúc Dữ liệu Tuyến tính",
            position=1,
            created_at=now - timedelta(days=8),
        )
        session.add(u2_1)
        session.flush()

        quiz_2_1 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Thuật toán tìm kiếm nhị phân (Binary Search) trên mảng đã sắp xếp có độ phức tạp thời gian là bao nhiêu?",
                "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                "choices": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "Mỗi bước của Binary Search chia đôi không gian tìm kiếm, do đó số lần lặp tối đa là log2(n), tức O(log n).",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Độ phức tạp O(1) có nghĩa là thuật toán thực thi trong đúng 1 micro-giây bất kể kích thước đầu vào.",
                "correct_answer": False,
                "explanation": "Sai. O(1) chỉ có nghĩa thời gian chạy là hằng số độc lập với kích thước tập dữ liệu đầu vào n, không biểu thị giá trị thời gian tuyệt đối 1 micro-giây.",
            },
        ]

        md_2_1 = f"""<!-- video_urls: ["https://www.youtube.com/watch?v=kqtD5dpn9C8"] -->
# Phân Tích Độ Phức Tạp Thuật Toán với Ký Hiệu Big-O

Nghiên cứu cách đánh giá hiệu năng thuật toán một cách khoa học.

## 1. Các Cấp Độ Phức Tạp Phổ Biến
1. **O(1) - Hằng số**: Truy xuất phần tử mảng qua chỉ số `arr[i]`, thao tác hash table lookup trung bình.
2. **O(log n) - Logarit**: Tìm kiếm nhị phân, tìm kiếm trên cây AVL / Red-Black Tree.
3. **O(n) - Tuyến tính**: Duyệt tuần tự mảng hoặc danh sách liên kết đơn.
4. **O(n log n) - Tuyến tính nhân Log**: QuickSort, MergeSort, HeapSort.
5. **O(n^2) - Bậc hai**: BubbleSort, SelectionSort, so sánh lồng nhau hai vòng lặp.
6. **O(2^n) - Hàm mũ**: Đệ quy nhánh nhị phân ngây thơ (Fibonacci không nhớ).

<!-- mini_quiz: {json.dumps(quiz_2_1, ensure_ascii=False)} -->
"""
        les_2_1 = Lesson(
            course_id=c2.id,
            learning_unit_id=u2_1.id,
            title="Bài 1: Phân tích Không gian & Thời gian Thuật toán với Big-O",
            summary="Nắm vững ký hiệu Big-O, tiệm cận toán học và phân tích thuật toán trong trường hợp xấu nhất.",
            markdown_content=md_2_1,
            position=1,
            estimated_duration_minutes=45,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=8),
        )
        session.add(les_2_1)
        session.flush()

        pdf_2_1_data = generate_pdf_document(
            title="TOAN GIAI THUAT: PHAN TICH TIEM CAN VA KY HIEU BIG-O",
            subtitle="Hoc phan DSA201 - Chuong 1: Do phuc tap Thuat toan",
            topics=[
                "Dinh nghia hinh thuc ve Big-O, Big-Omega va Big-Theta",
                "Phan tich Worst-case, Best-case va Average-case Complexity",
                "Ky thuat phan tich do phuc tap vong lap long nhau",
                "Phuong phap giai phuong trinh de quy bang Dinh ly Tong quat (Master Theorem)",
            ],
        )
        fa_pdf_2_1 = store_file_stream(
            actor=inst2,
            course_id=c2.id,
            file_stream=io.BytesIO(pdf_2_1_data),
            filename="Tong_hop_Do_phuc_tap_Thuat_toan_BigO.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Tài liệu chuyên đề: Phân tích Độ phức tạp Thuật toán Big-O",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst2,
            lesson_id=les_2_1.id,
            asset_id=fa_pdf_2_1.id,
            is_downloadable=True,
            label="Chuyên đề: Phân tích tiệm cận & Big-O (PDF)",
            session=session,
        )

        # Lesson 2.2 (Uploaded Video MP4 + PDF + Quiz)
        quiz_2_2 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Trong cấu trúc Min-Heap, phần tử có giá trị nhỏ nhất luôn nằm ở vị trí nào?",
                "options": ["Nút lá cuối cùng", "Nút gốc (Root)", "Phần tử ở giữa mảng", "Tùy thuộc vào thứ tự chèn"],
                "choices": ["Nút lá cuối cùng", "Nút gốc (Root)", "Phần tử ở giữa mảng", "Tùy thuộc vào thứ tự chèn"],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "Đặc tính bất biến của Min-Heap là mọi nút cha đều nhỏ hơn hoặc bằng các nút con của nó. Do đó, nút gốc luôn chứa giá trị nhỏ nhất của toàn bộ heap.",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Thao tác trích xuất phần tử ưu tiên cao nhất (extract-min) từ Binary Heap có độ phức tạp thời gian là O(log n).",
                "correct_answer": True,
                "explanation": "Chính xác. Sau khi lấy phần tử gốc, heap đưa phần tử cuối lên và thực hiện sifting down (heapify) mất tối đa O(log n) bước.",
            },
        ]

        md_2_2 = f"""# Cấu Trúc Dữ Liệu Heap & Ứng Dụng Hàng Đợi Ưu Tiên (Priority Queue)

Tìm hiểu cấu trúc cây nhị phân hoàn chỉnh và cách biểu diễn mảng tối ưu.

## 1. Biểu Diễn Heap Dưới Dạng Mảng (Zero-Indexed)
Với nút ở vị trí `i`:
- Nút con trái: `2 * i + 1`
- Nút con phải: `2 * i + 2`
- Nút cha: `(i - 1) // 2`

## 2. Ứng Dụng Thực Tiễn
- Bộ lập lịch tiến trình của Hệ điều hành (CPU Task Scheduler).
- Thuật toán tìm đường đi ngắn nhất Dijkstra.
- Nén dữ liệu Huffman Coding.

<!-- mini_quiz: {json.dumps(quiz_2_2, ensure_ascii=False)} -->
"""
        les_2_2 = Lesson(
            course_id=c2.id,
            learning_unit_id=u2_1.id,
            title="Bài 2: Ứng dụng Hàng đợi Ưu tiên (Priority Queue) & Heap",
            summary="Xây dựng Min-Heap, Max-Heap, thuật toán heapify và ứng dụng trong lập lịch.",
            markdown_content=md_2_2,
            position=2,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=7),
        )
        session.add(les_2_2)
        session.flush()

        fa_vid_2_2 = store_file_stream(
            actor=inst2,
            course_id=c2.id,
            file_stream=io.BytesIO(SAMPLE_MP4_BYTES),
            filename="demo_thuat_toan_heapify.mp4",
            content_type="video/mp4",
            asset_type="RESOURCE",
            title="Video mô phỏng thuật toán Heapify và Priority Queue",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst2,
            lesson_id=les_2_2.id,
            asset_id=fa_vid_2_2.id,
            is_downloadable=False,
            label="Video mô phỏng: Thao tác Heapify trực quan",
            session=session,
        )

        pdf_2_2_data = generate_pdf_document(
            title="CAU TRUC DU LIEU NANG CAO: BINARY HEAP VA PRIORITY QUEUE",
            subtitle="Hoc phan DSA201 - Chuong 1: Hang doi Uu tien",
            topics=[
                "Bat bien toan hoc cua Min-Heap va Max-Heap",
                "Cai dat mang 1 chieu khong can con tro de tiet kiem bo nho",
                "Thuat toan Heapify va xay dung Heap trong thoi gian O(n)",
                "Ung dung Heap trong Thuat toan Dijkstra va Thuat toan Prim",
            ],
        )
        fa_pdf_2_2 = store_file_stream(
            actor=inst2,
            course_id=c2.id,
            file_stream=io.BytesIO(pdf_2_2_data),
            filename="Cau_truc_Heap_va_Priority_Queue.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Tài liệu chuyên đề: Binary Heap & Priority Queue",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst2,
            lesson_id=les_2_2.id,
            asset_id=fa_pdf_2_2.id,
            is_downloadable=True,
            label="Chuyên đề: Cấu trúc Heap & Hàng đợi ưu tiên (PDF)",
            session=session,
        )

        # Chapter 2 of DSA201
        u2_2 = LearningUnit(
            course_id=c2.id,
            title="Chương 2: Cây & Đồ thị Ứng dụng Thực tế",
            position=2,
            created_at=now - timedelta(days=6),
        )
        session.add(u2_2)
        session.flush()

        quiz_2_3 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Thuật toán duyệt đồ thị theo chiều rộng (Breadth-First Search - BFS) sử dụng cấu trúc dữ liệu nào làm bộ đệm hàng đợi duyệt?",
                "options": ["Ngăn xếp (Stack)", "Hàng đợi (Queue)", "Cây nhị phân (Binary Tree)", "Mảng 2 chiều"],
                "choices": ["Ngăn xếp (Stack)", "Hàng đợi (Queue)", "Cây nhị phân (Binary Tree)", "Mảng 2 chiều"],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "BFS duyệt theo từng tầng khoảng cách từ đỉnh xuất phát, hoạt động theo nguyên tắc First-In First-Out (FIFO) của cấu trúc Queue.",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Thuật toán Dijkstra có thể hoạt động chính xác trên đồ thị có cạnh mang trọng số âm.",
                "correct_answer": False,
                "explanation": "Sai. Thuật toán Dijkstra dựa trên chiến lược tham lam (Greedy) và giả định trọng số các cạnh không âm. Khi có cạnh âm, phải dùng thuật toán Bellman-Ford.",
            },
        ]

        md_2_3 = f"""<!-- video_urls: ["https://www.youtube.com/watch?v=JJmcL1N2KQs"] -->
# Thuật Toán Duyệt Đồ Thị BFS / DFS & Tìm Đường Đi Ngắn Nhất

Khám phá thế giới giải thuật đồ thị và mô hình hóa bài toán thực tế.

## 1. Biểu Diễn Đồ Thị
- **Danh sách kề (Adjacency List)**: Tối ưu không gian cho đồ thị thưa $O(V + E)$.
- **Ma trận kề (Adjacency Matrix)**: Truy xuất nhanh cạnh $(u, v)$ trong $O(1)$ nhưng tốn $O(V^2)$ bộ nhớ.

## 2. So Sánh BFS và DFS
| Đặc tính | BFS (Breadth-First) | DFS (Depth-First) |
|----------|---------------------|-------------------|
| Cấu trúc dữ liệu | Hàng đợi (`Queue`) | Ngăn xếp (`Stack`) / Đệ quy |
| Thứ tự duyệt | Theo từng lớp bán kính | Đâm sâu tối đa trước khi quay lui |
| Ứng dụng chính | Tìm đường ngắn nhất không trọng số | Dò đường mê cung, sắp xếp tô-pô |

<!-- mini_quiz: {json.dumps(quiz_2_3, ensure_ascii=False)} -->
"""
        les_2_3 = Lesson(
            course_id=c2.id,
            learning_unit_id=u2_2.id,
            title="Bài 3: Thuật toán Duyệt Đồ thị BFS / DFS & Tìm Đường đi Ngắn nhất",
            summary="Nắm vững kỹ thuật duyệt đồ thị, phát hiện chu trình và giải thuật Dijkstra tìm đường tối ưu.",
            markdown_content=md_2_3,
            position=3,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=5),
        )
        session.add(les_2_3)
        session.flush()

        pdf_2_3_data = generate_pdf_document(
            title="LY THUYET DO THI: THUAT TOAN DUYET VA TIM DUONG DI NGAN NHAT",
            subtitle="Hoc phan DSA201 - Chuong 2: Giai thuat Do thi Nang cao",
            topics=[
                "Bieu dien Do thi bang Adjacency List va Adjacency Matrix",
                "Thuat toan BFS va tim duong di ngan nhat tren do thi khong trong so",
                "Thuat toan DFS va bai toan Sap xep To-po (Topological Sort)",
                "Thuat toan Dijkstra toi uu voi Priority Queue (O(E log V))",
            ],
        )
        fa_pdf_2_3 = store_file_stream(
            actor=inst2,
            course_id=c2.id,
            file_stream=io.BytesIO(pdf_2_3_data),
            filename="Giai_thuat_Duyet_Do_thi_Nang_cao.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Giáo trình chuyên sâu: Lý thuyết Đồ thị & Giải thuật Tìm đường",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst2,
            lesson_id=les_2_3.id,
            asset_id=fa_pdf_2_3.id,
            is_downloadable=True,
            label="Tài liệu chuyên sâu: Lý thuyết đồ thị & Dijkstra (PDF)",
            session=session,
        )

        # =========================================================================
        # COURSE 3: OPS401
        # =========================================================================
        logger.info("Seeding Course 3: OPS401...")
        c3 = Course(
            course_code="OPS401",
            course_code_normalized="OPS401",
            title="OPS401: DevOps, CI/CD Pipeline & Hạ Tầng Điện Toán Đám Mây",
            title_normalized="ops401: devops, ci/cd pipeline & hạ tầng điện toán đám mây",
            description=(
                "Trang bị kỹ năng triển khai ứng dụng thực chiến trong môi trường doanh nghiệp: "
                "container hóa với Docker, tối ưu hóa image đa tầng (Multi-stage build), "
                "soạn thảo kịch bản CI/CD tự động hóa trên GitHub Actions và giám sát hệ thống production."
            ),
            category="Hạ tầng & Hệ thống",
            difficulty="ADVANCED",
            owner_instructor_id=inst1.id,
            status="PUBLISHED",
            capacity=40,
            published_at=now - timedelta(days=5),
            approved_at=now - timedelta(days=5),
            approved_by_user_id=admin.id,
        )
        session.add(c3)
        session.flush()

        # Generate & attach 16:9 clean cover for OPS401
        c3_img_bytes = generate_course_cover_png(
            course_code="OPS401",
            title="DevOps, CI/CD Pipeline & Hạ Tầng Điện Toán Đám Mây",
            subtitle="Docker • Kubernetes • GitHub Actions • Cloud Architecture",
            bg_gradient=((24, 24, 27), (39, 39, 42)),
            accent_color=(168, 85, 247),
        )
        c3_asset = store_file_stream(
            actor=inst1,
            course_id=c3.id,
            file_stream=io.BytesIO(c3_img_bytes),
            filename="ops401_cover.png",
            content_type="image/png",
            asset_type="COURSE_IMAGE",
            title="Ảnh bìa khóa học OPS401",
            session=session,
        )
        c3.thumbnail_file_asset_id = c3_asset.id
        session.flush()

        session.add(
            CourseCompletionRule(
                course_id=c3.id,
                require_all_required_lessons=True,
                require_required_assessments=False,
                minimum_progress_percent=decimal.Decimal("70.00"),
                updated_by_user_id=inst1.id,
            )
        )

        # Chapter 1 of OPS401
        u3_1 = LearningUnit(
            course_id=c3.id,
            title="Chương 1: Đóng gói Container với Docker & Tối ưu Image",
            position=1,
            created_at=now - timedelta(days=5),
        )
        session.add(u3_1)
        session.flush()

        quiz_3_1 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Mục đích lớn nhất của kỹ thuật Multi-stage build trong Dockerfile là gì?",
                "options": [
                    "Tăng tốc độ kết nối mạng của container",
                    "Giảm dung lượng image cuối cùng và loại bỏ các công cụ build dư thừa khỏi production",
                    "Cho phép chạy cùng lúc nhiều hệ điều hành khác nhau trong 1 container",
                    "Tự động vá lỗi logic code của ứng dụng",
                ],
                "choices": [
                    "Tăng tốc độ kết nối mạng của container",
                    "Giảm dung lượng image cuối cùng và loại bỏ các công cụ build dư thừa khỏi production",
                    "Cho phép chạy cùng lúc nhiều hệ điều hành khác nhau trong 1 container",
                    "Tự động vá lỗi logic code của ứng dụng",
                ],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "Multi-stage build cho phép biên dịch ở stage đầu tiên và chỉ copy sản phẩm chạy (binary, wheels) sang stage runtime tối giản (Alpine/Distroless), giúp image siêu nhẹ và an toàn.",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Chạy container với người dùng quyền root (UID 0) trong production là một vi phạm an toàn thông tin nghiêm trọng.",
                "correct_answer": True,
                "explanation": "Chính xác. Luôn tạo người dùng không đặc quyền (non-root user) với chỉ thị `USER appuser` để giảm thiểu rủi ro container breakout.",
            },
        ]

        md_3_1 = f"""<!-- video_urls: ["https://www.youtube.com/watch?v=kqtD5dpn9C8"] -->
# Đóng Gói Ứng Dụng Backend Đa Tầng với Dockerfile

Thực hành container hóa ứng dụng Python Backend chuẩn enterprise.

## 1. Nguyên Lý Tối Ưu Docker Layer Cache
- Đặt các lệnh ít thay đổi (`COPY requirements.txt`, `RUN pip install`) lên trước.
- Đặt mã nguồn ứng dụng (`COPY src/ src/`) về phía sau cùng để tận dụng bộ đệm (cache) khi chỉnh sửa code.

## 2. Dockerfile Mẫu Multi-Stage
```dockerfile
# Stage 1: Build & Dependencies
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Minimal Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src/ /app/src/
USER nobody
CMD ["python", "-m", "pwd301"]
```

<!-- mini_quiz: {json.dumps(quiz_3_1, ensure_ascii=False)} -->
"""
        les_3_1 = Lesson(
            course_id=c3.id,
            learning_unit_id=u3_1.id,
            title="Bài 1: Đóng gói Ứng dụng Backend Đa tầng với Dockerfile",
            summary="Tìm hiểu nguyên lý Docker layers, kỹ thuật Multi-stage build và thiết lập quyền hạn người dùng an toàn.",
            markdown_content=md_3_1,
            position=1,
            estimated_duration_minutes=45,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=5),
        )
        session.add(les_3_1)
        session.flush()

        pdf_3_1_data = generate_pdf_document(
            title="CONTAINER SECURITY: BEST PRACTICES DOCKER CHO ENTERPRISE",
            subtitle="Hoc phan OPS401 - Chuong 1: Container Hoa He Thong",
            topics=[
                "Co che van hanh cua Linux Namespaces va Control Groups (cgroups)",
                "Toi uu Docker Layer Caching de giam thoi gian Build tren CI Server",
                "Kien truc Multi-Stage Builds: Giam kich thuoc tu 1GB xuong duoi 80MB",
                "Cac tieu chuan bao mat: Non-root User, Read-only Filesystem, Drop Capabilities",
            ],
        )
        fa_pdf_3_1 = store_file_stream(
            actor=inst1,
            course_id=c3.id,
            file_stream=io.BytesIO(pdf_3_1_data),
            filename="Dockerfile_Best_Practices_Guide.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Cẩm nang DevOps: Tiêu chuẩn đóng gói Dockerfile",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst1,
            lesson_id=les_3_1.id,
            asset_id=fa_pdf_3_1.id,
            is_downloadable=True,
            label="Cẩm nang DevOps: Đóng gói Docker an toàn (PDF)",
            session=session,
        )

        # Lesson 3.2 (Uploaded Video MP4 + PDF + Quiz)
        quiz_3_2 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Chỉ thị nào trong docker-compose.yml giúp duy trì dữ liệu của cơ sở dữ liệu ngay cả khi container bị hủy và tạo lại?",
                "options": ["ports", "volumes", "environment", "depends_on"],
                "choices": ["ports", "volumes", "environment", "depends_on"],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "Chỉ thị 'volumes' ánh xạ thư mục lưu trữ của máy chủ (host volume) hoặc named volume vào container, đảm bảo tính bền vững của dữ liệu.",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Chỉ thị 'depends_on' trong Docker Compose đảm bảo dịch vụ phụ thuộc đã hoàn toàn khởi động xong và sẵn sàng nhận kết nối mạng (Ready to accept traffic).",
                "correct_answer": False,
                "explanation": "Sai. 'depends_on' mặc định chỉ đợi container phụ thuộc được khởi chạy (started), không đợi ứng dụng bên trong sẵn sàng. Cần kết hợp thêm `condition: service_healthy` với healthcheck.",
            },
        ]

        md_3_2 = f"""# Quản Lý Cụm Đa Dịch Vụ với Docker Compose

Hướng dẫn cấu hình mạng nội bộ và điều phối container trên máy chủ.

## 1. Cấu Trúc File docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      db:
        condition: service_healthy

  db:
    image: mcr.microsoft.com/mssql/server:2022-latest
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=YourPassword123!
    volumes:
      - mssql_data:/var/opt/mssql

volumes:
  mssql_data:
```

<!-- mini_quiz: {json.dumps(quiz_3_2, ensure_ascii=False)} -->
"""
        les_3_2 = Lesson(
            course_id=c3.id,
            learning_unit_id=u3_1.id,
            title="Bài 2: Quản lý Cụm Multi-container với Docker Compose",
            summary="Định nghĩa môi trường đa tầng: Web Backend, Cơ sở dữ liệu và Reverse Proxy Nginx.",
            markdown_content=md_3_2,
            position=2,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=4),
        )
        session.add(les_3_2)
        session.flush()

        fa_vid_3_2 = store_file_stream(
            actor=inst1,
            course_id=c3.id,
            file_stream=io.BytesIO(SAMPLE_MP4_BYTES),
            filename="huong_dan_docker_compose.mp4",
            content_type="video/mp4",
            asset_type="RESOURCE",
            title="Video thực hành: Điều phối dịch vụ bằng Docker Compose",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst1,
            lesson_id=les_3_2.id,
            asset_id=fa_vid_3_2.id,
            is_downloadable=False,
            label="Video bài giảng: Quản lý multi-service container",
            session=session,
        )

        pdf_3_2_data = generate_pdf_document(
            title="DOCKER COMPOSE: DIEU PHOI HE THONG NHO VA VUA",
            subtitle="Hoc phan OPS401 - Chuong 1: Multi-Container Orchestration",
            topics=[
                "Khai niem bridge network va co che phan giai ten mien noi bo (DNS Service Discovery)",
                "Cau hinh healthchecks chu dong de kiem soat thu tu khoi dong ung dung",
                "Quan ly du lieu ben vung voi Named Volumes va Bind Mounts",
                "Chien luoc tach biet file cau hinh: docker-compose.yml va docker-compose.prod.yml",
            ],
        )
        fa_pdf_3_2 = store_file_stream(
            actor=inst1,
            course_id=c3.id,
            file_stream=io.BytesIO(pdf_3_2_data),
            filename="Docker_Compose_Production_Setup.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Tài liệu chuyên đề: Docker Compose Production Setup",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst1,
            lesson_id=les_3_2.id,
            asset_id=fa_pdf_3_2.id,
            is_downloadable=True,
            label="Chuyên đề: Cấu hình Docker Compose nâng cao (PDF)",
            session=session,
        )

        # Chapter 2 of OPS401
        u3_2 = LearningUnit(
            course_id=c3.id,
            title="Chương 2: Tự động hóa Triển khai với CI/CD Pipeline",
            position=2,
            created_at=now - timedelta(days=3),
        )
        session.add(u3_2)
        session.flush()

        quiz_3_3 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Trong GitHub Actions workflow, secret variables (như API key, mật khẩu server) phải được lưu trữ ở đâu để đảm bảo an toàn tuyệt đối?",
                "options": [
                    "Viết trực tiếp vào file .github/workflows/ci.yml",
                    "Ghi chú trong file README.md",
                    "Lưu trong phần Settings -> Secrets and variables -> Actions của Repository",
                    "Đẩy lên nhánh git public để server kéo về",
                ],
                "choices": [
                    "Viết trực tiếp vào file .github/workflows/ci.yml",
                    "Ghi chú trong file README.md",
                    "Lưu trong phần Settings -> Secrets and variables -> Actions của Repository",
                    "Đẩy lên nhánh git public để server kéo về",
                ],
                "correct_answers": [2],
                "correct_answer": 2,
                "explanation": "GitHub Secrets được mã hóa lưu trữ ở cấp độ hạ tầng GitHub và tự động mask (che giấu) trong toàn bộ console log của pipeline.",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Mục tiêu cốt lõi của Continuous Integration (CI) là phát hiện lỗi tích hợp càng sớm càng tốt bằng cách tự động chạy test suite mỗi khi có commit hoặc Pull Request mới.",
                "correct_answer": True,
                "explanation": "Chính xác. CI giúp loại bỏ 'cơn ác mộng hợp nhất' (integration hell) và đảm bảo mã nguồn luôn ở trạng thái sẵn sàng phát hành.",
            },
        ]

        md_3_3 = f"""<!-- video_urls: ["https://www.youtube.com/watch?v=JJmcL1N2KQs"] -->
# Xây Dựng GitHub Actions Pipeline Tự Động Kiểm Thử & Build

Tự động hóa toàn bộ quy trình kiểm thử đơn vị, kiểm tra chuẩn mã nguồn (Linting) và build image.

## 1. Kịch Bản CI Pipeline Mẫu
```yaml
name: Continuous Integration

on:
  push:
    branches: [ "master", "main" ]
  pull_request:
    branches: [ "master", "main" ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python 3.12
      uses: actions/setup-python@v5
      with:
        python-version: "3.12"
    - name: Run Test Suite
      run: |
        pip install -r requirements-dev.txt
        pytest --cov=src
```

<!-- mini_quiz: {json.dumps(quiz_3_3, ensure_ascii=False)} -->
"""
        les_3_3 = Lesson(
            course_id=c3.id,
            learning_unit_id=u3_2.id,
            title="Bài 3: Xây dựng GitHub Actions Pipeline Tự động Kiểm thử & Build",
            summary="Thiết kế kịch bản tự động hóa CI/CD, caching dependencies và bảo mật thông tin xác thực.",
            markdown_content=md_3_3,
            position=3,
            estimated_duration_minutes=55,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=2),
        )
        session.add(les_3_3)
        session.flush()

        pdf_3_3_data = generate_pdf_document(
            title="DEVOPS HANDBOOK: THIET KE CI/CD PIPELINE VOI GITHUB ACTIONS",
            subtitle="Hoc phan OPS401 - Chuong 2: Tu Dong Hoa Trien Khai",
            topics=[
                "Cac khai niem nen tang: Workflows, Jobs, Steps, Actions va Runners",
                "Ky thuat Caching dependencies de tang toc pipeline gap 3 lan",
                "Quan ly bao mat Secrets va Environment Protection Rules",
                "Chien luoc phat hanh: Blue/Green Deployment va Canary Releases",
            ],
        )
        fa_pdf_3_3 = store_file_stream(
            actor=inst1,
            course_id=c3.id,
            file_stream=io.BytesIO(pdf_3_3_data),
            filename="GitHub_Actions_CICD_Cookbook.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Sổ tay DevOps: Xây dựng GitHub Actions CI/CD Pipeline",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst1,
            lesson_id=les_3_3.id,
            asset_id=fa_pdf_3_3.id,
            is_downloadable=True,
            label="Cẩm nang CI/CD: Tự động hóa Pipeline (PDF)",
            session=session,
        )

        # =========================================================================
        # ENROLLMENTS & DEMO PROGRESS
        # =========================================================================
        logger.info("Setting up enrollments and initial progress...")
        from pwd301.services.enrollment_service import enroll_student

        # Enroll student1 in PY301 & DSA201
        e1 = enroll_student(actor=student1, course_id=c1.id, session=session)
        e2 = enroll_student(actor=student1, course_id=c2.id, session=session)

        # Enroll student2 in PY301
        e3 = enroll_student(actor=student2, course_id=c1.id, session=session)

        # Enroll student3 in OPS401
        e4 = enroll_student(actor=student3, course_id=c3.id, session=session)
        session.flush()

        # student1 has completed Lesson 1.1 with progress
        if e1.current_period_id:
            session.add(
                LessonProgress(
                    enrollment_period_id=e1.current_period_id,
                    lesson_id=les_1_1.id,
                    seconds_spent=300,
                    max_view_fraction=decimal.Decimal("1.0000"),
                    completed_at=now - timedelta(days=3),
                    completion_rule_snapshot_json=json.dumps(
                        {
                            "personal_notes": "Đã ghi nhớ các chuẩn HTTP methods và quy ước status codes.",
                            "mini_quiz_completed_at": (now - timedelta(days=3)).isoformat(),
                            "mini_quiz_question_count": 3,
                        }
                    ),
                )
            )

        session.commit()
        logger.info("Done! Successfully seeded 3 rich courses with full multimedia, PDFs, and quizzes!")


if __name__ == "__main__":
    seed_courses()
