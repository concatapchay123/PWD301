"""Seed 3 Rich, Realistic Courses for PWD301.

Creates 3 comprehensive, industry-standard courses:
1. PY301: Lập trình Python Backend & REST API Doanh Nghiệp (TS. Nguyễn Văn A)
2. DSA201: Cấu Trúc Dữ Liệu & Giải Thuật Ứng Dụng Nâng Cao (ThS. Trần Thị B)
3. OPS401: DevOps, CI/CD Pipeline & Hạ Tầng Điện Toán Đám Mây (TS. Nguyễn Văn A)

Each course features:
- Standard Learning Objectives (SLO), target audience, completion requirements.
- Full course banner cover image generated via pure Python stdlib PNG.
- Chapters (LearningUnits) and sequential lessons with rich Markdown, summary & duration.
- Verified embeddable public YouTube videos and uploaded internal MP4 demo videos.
- Attached real PDF documents with authentic academic outlines.
- Interactive mini-quizzes supporting all 4 question types (Multiple Choice, True/False,
  Fill in the Blank, Matching) with detailed explanations.
- Formal Assessment (Exam/Midterm) with question assignments totaling 100.00 points.
- Student enrollments and initial learning progress & attempt scores.
"""

from __future__ import annotations

import base64
import decimal
import io
import json
import logging
import struct
import sys
import uuid
import zlib
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

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


def generate_course_cover_png(
    course_code: str,
    bg_gradient: tuple[tuple[int, int, int], tuple[int, int, int]],
) -> bytes:
    """Generate a clean 16:9 (1280x720) valid PNG image using stdlib without external PIL dependency."""
    width = 1280
    height = 720
    color_start, color_end = bg_gradient

    raw_lines = []
    for y in range(height):
        ratio = y / float(height - 1)
        r = int(color_start[0] * (1.0 - ratio) + color_end[0] * ratio)
        g = int(color_start[1] * (1.0 - ratio) + color_end[1] * ratio)
        b = int(color_start[2] * (1.0 - ratio) + color_end[2] * ratio)

        line_bytes = bytearray([0])
        line_pixel = bytes([r, g, b])
        line_bytes.extend(line_pixel * width)
        raw_lines.append(bytes(line_bytes))

    raw_data = b"".join(raw_lines)
    compressed = zlib.compress(raw_data, level=6)

    def png_chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    idat = png_chunk(b"IDAT", compressed)
    iend = png_chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


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
        "0 -25 Td\n"
        "(He thong Hoc truc tuyen PWD301 - Luu hanh noi bo hoc vien va giang vien) Tj\n"
        "ET\n"
    )
    stream_bytes = stream_content.encode("latin-1", errors="replace")

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"5 0 obj\n<< /Length "
        + str(len(stream_bytes)).encode("ascii")
        + b" >>\nstream\n"
        + stream_bytes
        + b"\nendstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \n0000000261 00000 n \n0000000336 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n450\n%%EOF\n"
    )
    return pdf


def wipe_all_courses(session: Session) -> None:
    """Wipe existing courses and all child relational records completely."""
    logger.info("Cleaning up existing course and learning records...")

    all_tables_with_triggers = [
        "assessments",
        "assessment_question_assignments",
        "assessment_question_pool",
        "assessment_sections",
        "assessment_blueprint_rules",
        "question_revisions",
        "question_revision_choices",
        "question_revision_accepted_answers",
        "file_revisions",
        "knowledge_versions",
    ]
    for tbl in all_tables_with_triggers:
        try:
            session.execute(sa.text(f"ALTER TABLE {tbl} DISABLE TRIGGER ALL"))
        except Exception as e:
            logger.debug(f"Disable trigger warning on {tbl}: {e}")
    session.commit()

    # Nullify / remove dependent references
    try:
        session.execute(
            sa.text("UPDATE ai_conversations SET course_id = NULL WHERE course_id IS NOT NULL")
        )
    except Exception as e:
        logger.debug(f"Clear ai_conversations warning: {e}")

    try:
        session.execute(
            sa.text("DELETE FROM ai_generated_question_drafts WHERE course_id IS NOT NULL")
        )
    except Exception as e:
        logger.debug(f"Clear ai_generated_question_drafts warning: {e}")

    try:
        session.execute(
            sa.text(
                "DELETE FROM knowledge_chunks WHERE document_id IN (SELECT id FROM knowledge_documents WHERE course_id IS NOT NULL)"
            )
        )
        session.execute(sa.text("DELETE FROM knowledge_documents WHERE course_id IS NOT NULL"))
    except Exception as e:
        logger.debug(f"Clear knowledge_documents warning: {e}")

    try:
        session.execute(
            sa.text(
                "DELETE FROM import_question_options WHERE import_question_id IN (SELECT id FROM import_questions WHERE import_job_id IN (SELECT id FROM document_import_jobs WHERE course_id IS NOT NULL))"
            )
        )
        session.execute(
            sa.text(
                "DELETE FROM import_questions WHERE import_job_id IN (SELECT id FROM document_import_jobs WHERE course_id IS NOT NULL)"
            )
        )
        session.execute(sa.text("DELETE FROM document_import_jobs WHERE course_id IS NOT NULL"))
    except Exception as e:
        logger.debug(f"Clear document_import_jobs warning: {e}")

    try:
        session.execute(sa.text("DELETE FROM grade_exports WHERE course_id IS NOT NULL"))
    except Exception as e:
        logger.debug(f"Clear grade_exports warning: {e}")
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

    # Question Bank
    session.query(QuestionRevisionChoice).delete(synchronize_session=False)
    session.query(QuestionRevisionAcceptedAnswer).delete(synchronize_session=False)
    session.query(QuestionRevision).delete(synchronize_session=False)
    session.query(QuestionProvenance).delete(synchronize_session=False)
    session.query(Question).delete(synchronize_session=False)

    for tbl in all_tables_with_triggers:
        try:
            session.execute(sa.text(f"ALTER TABLE {tbl} ENABLE TRIGGER ALL"))
        except Exception:
            pass
    session.commit()

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
            session.query(FileScanResult).filter(FileScanResult.file_revision_id == rev.id).delete(
                synchronize_session=False
            )
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
        for code, name in [
            ("STUDENT", "Student"),
            ("INSTRUCTOR", "Instructor"),
            ("ADMIN", "System Administrator"),
        ]:
            r = Role(code=code, name=name)
            session.add(r)
            session.flush()
            roles[code] = r

    user_configs = [
        {
            "email": "admin@pwd301.local",
            "name": "Quản trị viên Hệ thống",
            "roles": ["STUDENT", "INSTRUCTOR", "ADMIN"],
        },
        {
            "email": "instructor1@pwd301.local",
            "name": "TS. Nguyễn Văn A",
            "roles": ["STUDENT", "INSTRUCTOR"],
        },
        {
            "email": "instructor2@pwd301.local",
            "name": "ThS. Trần Thị B",
            "roles": ["STUDENT", "INSTRUCTOR"],
        },
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
            has_link = (
                session.query(UserRole)
                .filter(UserRole.user_id == u.id, UserRole.role_id == r_obj.id)
                .first()
            )
            if not has_link:
                session.add(
                    UserRole(
                        user_id=u.id,
                        role_id=r_obj.id,
                        assigned_by_user_id=u.id,
                        assignment_reason="Seed",
                    )
                )

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
        c1_slo = [
            {
                "title": "SLO-1: Kiến trúc HTTP & RESTful API",
                "description": "Nắm vững nguyên lý Client-Server, các chuẩn HTTP methods (GET, POST, PUT, DELETE), status codes và thiết kế endpoint chuẩn RESTful.",
                "weight": "25%",
            },
            {
                "title": "SLO-2: ORM & Database Design với SQL Server",
                "description": "Làm chủ SQLAlchemy ORM, quan hệ bảng 1-N, N-N, tối ưu hóa truy vấn và schema migrations.",
                "weight": "35%",
            },
            {
                "title": "SLO-3: Xác thực JWT & Phân quyền RBAC",
                "description": "Triển khai xác thực JWT, session auth an toàn, phân quyền người dùng theo vai trò RBAC và phòng thủ các lỗ hổng OWASP phổ biến.",
                "weight": "40%",
            },
        ]
        c1_target = [
            "Sinh viên năm 3-4 chuyên ngành CNTT, Kỹ thuật Phần mềm cần củng cố kiến thức backend doanh nghiệp",
            "Lập trình viên muốn nâng cao kỹ năng thiết kế RESTful API chuẩn mực và bảo mật hệ thống",
            "Kỹ sư phần mềm cần làm chủ Microsoft SQL Server và SQLAlchemy ORM trong môi trường Production",
        ]
        c1_completion = {
            "minimum_grade_score": 80.0,
            "allow_certificate": True,
            "completion_grace_days": 14,
            "require_all_lessons": True,
        }

        c1 = Course(
            course_code="PY301",
            course_code_normalized="PY301",
            title="Lập trình Python Backend & REST API Doanh Nghiệp",
            title_normalized="lập trình python backend & rest api doanh nghiệp",
            description=(
                "Khóa học chuyên sâu trang bị kiến trúc backend hoàn chỉnh với Python hiện đại: "
                "Flask Framework, SQLAlchemy ORM, Microsoft SQL Server, xác thực JWT, phân quyền RBAC, "
                "bảo mật CSRF/XSS và kiểm thử tự động với Pytest."
            ),
            learning_objectives=json.dumps(c1_slo, ensure_ascii=False),
            target_audience=json.dumps(c1_target, ensure_ascii=False),
            completion_requirements=json.dumps(c1_completion, ensure_ascii=False),
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

        # Cover banner
        c1_img_bytes = generate_course_cover_png("PY301", ((15, 23, 42), (30, 41, 59)))
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

        session.add(
            CourseCompletionRule(
                course_id=c1.id,
                require_all_required_lessons=True,
                require_required_assessments=True,
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
                "type": "FILL_IN_BLANK",
                "question": "Mã trạng thái HTTP [___] đại diện cho lỗi Unauthorized khi người dùng chưa cung cấp thông tin xác thực danh tính hợp lệ.",
                "blanks": [
                    {
                        "placeholder": "[___]",
                        "answers": ["401", "HTTP 401"],
                    }
                ],
                "explanation": "Mã trạng thái HTTP 401 Unauthorized biểu thị người dùng chưa được xác thực danh tính.",
            },
            {
                "type": "MATCHING",
                "question": "Hãy ghép cặp mã trạng thái HTTP với ý nghĩa chuẩn xác tương ứng:",
                "pairs": [
                    {"left": "200 OK", "right": "Thành công truy xuất hoặc cập nhật tài nguyên"},
                    {"left": "201 Created", "right": "Khởi tạo tài nguyên mới thành công"},
                    {
                        "left": "403 Forbidden",
                        "right": "Đã đăng nhập nhưng không có quyền truy cập",
                    },
                    {"left": "404 Not Found", "right": "Tài nguyên được yêu cầu không tồn tại"},
                ],
                "explanation": "200 OK: Thành công; 201 Created: Tạo mới; 403 Forbidden: Không có quyền; 404 Not Found: Không tìm thấy.",
            },
        ]

        md_1_1 = f"""<!-- video_urls: ["https://www.youtube.com/watch?v=kqtD5dpn9C8"] -->
# Tổng quan về Giao thức HTTP & Kiến trúc RESTful API

Chào mừng các bạn đến với khóa học **Lập trình Python Backend & REST API Doanh Nghiệp (PY301)**.

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
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=10),
        )
        session.add(les_1_1)
        session.flush()

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
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=9),
        )
        session.add(les_1_2)
        session.flush()

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
            revision_no=1,
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
            filename="SQLAlchemy_ORM_va_Alembic_Guide.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Tài liệu chuyên đề: SQLAlchemy ORM & Alembic Migration",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst1,
            lesson_id=les_1_3.id,
            asset_id=fa_pdf_1_3.id,
            is_downloadable=True,
            label="Chuyên đề: Quản lý Migration CSDL SQL Server (PDF)",
            session=session,
        )

        # Lesson 1.4 (Uploaded Video MP4 + PDF + Quiz)
        quiz_1_4 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "JSON Web Token (JWT) bao gồm 3 phần cấu thành nào theo chuẩn RFC 7519?",
                "options": [
                    "Header, Payload, Signature",
                    "Username, Password, Salt",
                    "Request, Response, Status",
                    "Cookie, Session, Token",
                ],
                "choices": [
                    "Header, Payload, Signature",
                    "Username, Password, Salt",
                    "Request, Response, Status",
                    "Cookie, Session, Token",
                ],
                "correct_answers": [0],
                "correct_answer": 0,
                "explanation": "JWT có cấu trúc chuẩn gồm 3 phần phân tách bằng dấu chấm: Header.Payload.Signature.",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Dữ liệu lưu trữ trong phần Payload của JWT được mã hóa bảo mật bí mật tuyệt đối và client không thể đọc được.",
                "correct_answer": False,
                "explanation": "Sai. Payload chỉ được encode Base64Url chứ không hề mã hóa bí mật. Bất kỳ ai có token đều đọc được nội dung payload. Vì vậy không bao giờ lưu mật khẩu hoặc dữ liệu nhạy cảm vào payload.",
            },
        ]

        md_1_4 = f"""# Xác Thực JWT & Phân Quyền Truy Cập RBAC Chuẩn Doanh Nghiệp

Thiết lập cơ chế bảo mật xác thực danh tính stateless thông qua JSON Web Token.

## 1. Cơ Chế Hoạt Động của JWT
Khi người dùng đăng nhập thành công với Email và Mật khẩu, máy chủ sinh Access Token có thời hạn và trả về cho client:
- Header: Chứa thuật toán ký (`HS256`, `RS256`).
- Payload: Chứa thông tin định danh (`sub`: user_id, `roles`: list roles, `exp`: expiration time).
- Signature: Chữ ký HMAC băm từ Header, Payload và `JWT_SECRET_KEY`.

<!-- mini_quiz: {json.dumps(quiz_1_4, ensure_ascii=False)} -->
"""
        les_1_4 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_2.id,
            title="Bài 4: Xác thực JWT & Phân quyền Truy cập RBAC Chuẩn Doanh Nghiệp",
            summary="Tìm hiểu cấu trúc JSON Web Token, cơ chế ký số và kiểm soát phân quyền truy cập Role-Based Access Control.",
            markdown_content=md_1_4,
            position=4,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=6),
        )
        session.add(les_1_4)
        session.flush()

        fa_vid_1_4 = store_file_stream(
            actor=inst1,
            course_id=c1.id,
            file_stream=io.BytesIO(SAMPLE_MP4_BYTES),
            filename="xac_thuc_jwt_va_phan_quyen_rbac.mp4",
            content_type="video/mp4",
            asset_type="RESOURCE",
            title="Video thực hành: Cài đặt JWT và phân quyền RBAC trong Flask",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst1,
            lesson_id=les_1_4.id,
            asset_id=fa_vid_1_4.id,
            is_downloadable=False,
            label="Video thực hành: Thiết lập JWT & Phân quyền RBAC",
            session=session,
        )

        pdf_1_4_data = generate_pdf_document(
            title="AN NINH WEBSERVICE: KIEN TRUC XAC THUC JWT VA PHAN QUYEN RBAC",
            subtitle="Hoc phan PY301 - Chuong 2: Bao mat He thong Backend",
            topics=[
                "Chuan RFC 7519 ve JSON Web Token va chu ky so HMAC SHA256",
                "Thiet ke Refresh Token rotation phong chong chiem doat phien",
                "Phan quyen theo vai tro (Role-Based Access Control) voi Decorators",
                "Phong chong cac lo hong bao mat OWASP API Security Top 10",
            ],
        )
        fa_pdf_1_4 = store_file_stream(
            actor=inst1,
            course_id=c1.id,
            file_stream=io.BytesIO(pdf_1_4_data),
            filename="Bao_mat_JWT_va_RBAC_Guide.pdf",
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
            label="Chuyên đề: Bảo mật JWT và Phân quyền RBAC (PDF)",
            session=session,
        )

        # Formal Assessment for Course 1
        logger.info("Seeding formal assessment for Course 1...")
        asm1 = Assessment(
            course_id=c1.id,
            title="Kiểm tra Giữa kỳ: Kiến trúc Backend & RESTful API",
            description="Bài thi đánh giá tổng hợp năng lực thiết kế API, thao tác ORM và bảo mật JWT.",
            assessment_type="MIDTERM",
            status="PUBLISHED",
            time_limit_minutes=45,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("60.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=5),
        )
        session.add(asm1)
        session.flush()

        sec1 = AssessmentSection(
            assessment_id=asm1.id,
            title="Phần 1: Kiến thức Cốt lõi & Kỹ năng Backend",
            position=1,
            instructions="Đọc kỹ câu hỏi và chọn đáp án chính xác.",
        )
        session.add(sec1)
        session.flush()

        # Questions for Course 1 Assessment
        q1_1 = Question(
            course_id=c1.id,
            lesson_id=les_1_1.id,
            creator_user_id=inst1.id,
            difficulty="REMEMBER",
            learning_objective="REST HTTP methods",
            status="ACTIVE",
        )
        session.add(q1_1)
        session.flush()
        q1_1_rev = QuestionRevision(
            question_id=q1_1.id,
            revision_no=1,
            is_current=True,
            created_by_user_id=inst1.id,
            content="Phương thức HTTP nào được quy định để xóa bỏ hoàn toàn một tài nguyên theo chuẩn RESTful?",
            question_type="SINGLE_CHOICE",
            explanation="DELETE là phương thức chuẩn để xóa tài nguyên.",
            change_type="INITIAL",
            approved_at=now,
        )
        session.add(q1_1_rev)
        session.flush()
        for idx, (lbl, corr) in enumerate(
            [("GET", False), ("POST", False), ("DELETE", True), ("PATCH", False)], 1
        ):
            session.add(
                QuestionRevisionChoice(
                    question_revision_id=q1_1_rev.id,
                    choice_key=uuid.uuid4(),
                    content=lbl,
                    is_correct=corr,
                    position=idx,
                )
            )
        session.add(
            QuestionProvenance(
                question_id=q1_1.id, question_revision_id=q1_1_rev.id, source_type="MANUAL"
            )
        )

        q1_2 = Question(
            course_id=c1.id,
            lesson_id=les_1_3.id,
            creator_user_id=inst1.id,
            difficulty="UNDERSTAND",
            learning_objective="SQLAlchemy ORM",
            status="ACTIVE",
        )
        session.add(q1_2)
        session.flush()
        q1_2_rev = QuestionRevision(
            question_id=q1_2.id,
            revision_no=1,
            is_current=True,
            created_by_user_id=inst1.id,
            content="Trong SQLAlchemy, thuộc tính `back_populates` trong `relationship` có vai trò gì?",
            question_type="SINGLE_CHOICE",
            explanation="`back_populates` thiết lập đồng bộ hai chiều rõ ràng giữa hai models.",
            change_type="INITIAL",
            approved_at=now,
        )
        session.add(q1_2_rev)
        session.flush()
        for idx, (lbl, corr) in enumerate(
            [
                ("Thiết lập quan hệ đồng bộ hai chiều rõ ràng giữa hai model", True),
                ("Tự động xóa database khi khởi động lại", False),
                ("Chuyển đổi kiểu dữ liệu sang JSON", False),
                ("Tăng tốc độ mạng Internet", False),
            ],
            1,
        ):
            session.add(
                QuestionRevisionChoice(
                    question_revision_id=q1_2_rev.id,
                    choice_key=uuid.uuid4(),
                    content=lbl,
                    is_correct=corr,
                    position=idx,
                )
            )
        session.add(
            QuestionProvenance(
                question_id=q1_2.id, question_revision_id=q1_2_rev.id, source_type="MANUAL"
            )
        )

        session.add(
            AssessmentQuestionAssignment(
                assessment_id=asm1.id,
                question_id=q1_1.id,
                section_id=sec1.id,
                points=decimal.Decimal("50.00"),
                position=1,
            )
        )
        session.add(
            AssessmentQuestionAssignment(
                assessment_id=asm1.id,
                question_id=q1_2.id,
                section_id=sec1.id,
                points=decimal.Decimal("50.00"),
                position=2,
            )
        )

        # =========================================================================
        # COURSE 2: DSA201
        # =========================================================================
        logger.info("Seeding Course 2: DSA201...")
        c2_slo = [
            {
                "title": "SLO-1: Đánh giá Độ phức tạp & Tối ưu Thuật toán",
                "description": "Thành thạo phân tích Big-O thời gian và không gian cho các giải thuật lặp và đệ quy.",
                "weight": "30%",
            },
            {
                "title": "SLO-2: Cấu trúc Cây & Đồ thị Ứng dụng",
                "description": "Hiện thực cây nhị phân cân bằng, Heap, đồ thị và các thuật toán tìm đường đi ngắn nhất.",
                "weight": "40%",
            },
            {
                "title": "SLO-3: Kỹ thuật Quy hoạch Động Nâng cao",
                "description": "Phân rã bài toán con tối ưu và xây dựng bảng phương án giải quyết bài toán thực tế.",
                "weight": "30%",
            },
        ]
        c2_target = [
            "Sinh viên muốn chinh phục các vòng phỏng vấn kỹ thuật thuật toán tại các tập đoàn công nghệ",
            "Lập trình viên muốn rèn luyện tư duy tối ưu hiệu năng cho hệ thống phân tán chịu tải cao",
            "Kỹ sư phát triển phần mềm chuẩn bị thi các chứng chỉ lập trình quốc tế",
        ]
        c2_completion = {
            "minimum_grade_score": 75.0,
            "allow_certificate": True,
            "completion_grace_days": 10,
            "require_all_lessons": True,
        }

        c2 = Course(
            course_code="DSA201",
            course_code_normalized="DSA201",
            title="Cấu Trúc Dữ Liệu & Giải Thuật Ứng Dụng Nâng Cao",
            title_normalized="cấu trúc dữ liệu & giải thuật ứng dụng nâng cao",
            description=(
                "Nghiên cứu chuyên sâu về phân tích độ phức tạp thời gian/không gian thuật toán, "
                "cấu trúc dữ liệu tuyến tính và phi tuyến tính: Heap, Balanced Trees, Đồ thị, "
                "thuật toán Quy hoạch động và ứng dụng trong các bài toán quy mô lớn."
            ),
            learning_objectives=json.dumps(c2_slo, ensure_ascii=False),
            target_audience=json.dumps(c2_target, ensure_ascii=False),
            completion_requirements=json.dumps(c2_completion, ensure_ascii=False),
            category="Cấu trúc Dữ liệu & Giải thuật",
            difficulty="ADVANCED",
            owner_instructor_id=inst2.id,
            status="PUBLISHED",
            capacity=50,
            published_at=now - timedelta(days=9),
            approved_at=now - timedelta(days=9),
            approved_by_user_id=admin.id,
        )
        session.add(c2)
        session.flush()

        c2_img_bytes = generate_course_cover_png("DSA201", ((24, 24, 27), (39, 39, 42)))
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
                require_required_assessments=True,
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
            revision_no=1,
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

        # Lesson 2.2
        quiz_2_2 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Trong cấu trúc Min-Heap, phần tử có giá trị nhỏ nhất luôn nằm ở vị trí nào?",
                "options": [
                    "Nút lá cuối cùng",
                    "Nút gốc (Root)",
                    "Phần tử ở giữa mảng",
                    "Tùy thuộc vào thứ tự chèn",
                ],
                "choices": [
                    "Nút lá cuối cùng",
                    "Nút gốc (Root)",
                    "Phần tử ở giữa mảng",
                    "Tùy thuộc vào thứ tự chèn",
                ],
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
            revision_no=1,
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
                "question": "Thuật toán tìm kiếm theo chiều rộng (Breadth-First Search - BFS) sử dụng cấu trúc dữ liệu nào để quản lý các đỉnh chờ duyệt?",
                "options": [
                    "Ngăn xếp (Stack)",
                    "Hàng đợi (Queue)",
                    "Cây nhị phân",
                    "Bảng băm (Hash Table)",
                ],
                "choices": [
                    "Ngăn xếp (Stack)",
                    "Hàng đợi (Queue)",
                    "Cây nhị phân",
                    "Bảng băm (Hash Table)",
                ],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "BFS duyệt theo từng lớp khoảng cách từ đỉnh xuất phát, nên cần cơ chế FIFO của Hàng đợi (Queue). Trong khi DFS dùng LIFO (Stack).",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Thuật toán Dijkstra có thể hoạt động chính xác trên đồ thị có cạnh mang trọng số âm.",
                "correct_answer": False,
                "explanation": "Sai. Thuật toán Dijkstra dựa trên giả định tham lam rằng đường đi ngắn nhất không thể bị rút ngắn thêm bởi các cạnh tương lai, điều này không còn đúng khi có trọng số âm. Với trọng số âm cần dùng thuật toán Bellman-Ford.",
            },
        ]

        md_2_3 = f"""<!-- video_urls: ["https://www.youtube.com/watch?v=JJmcL1N2KQs"] -->
# Thuật Toán Duyệt Đồ Thị BFS / DFS & Tìm Đường Đi Ngắn Nhất

Nghiên cứu hai thuật toán nền tảng trong lý thuyết đồ thị và bài toán định tuyến.

## 1. So Sánh BFS và DFS
| Tiêu chí | BFS (Breadth-First Search) | DFS (Depth-First Search) |
|----------|----------------------------|--------------------------|
| Cấu trúc dữ liệu | Hàng đợi (Queue - FIFO) | Ngăn xếp (Stack - LIFO) |
| Thứ tự duyệt | Từng tầng khoảng cách | Đi sâu hết mức trước khi quay lui |
| Ứng dụng | Tìm đường đi ngắn nhất đồ thị không trọng số | Tìm thành phần liên thông, sắp xếp topo |

<!-- mini_quiz: {json.dumps(quiz_2_3, ensure_ascii=False)} -->
"""
        les_2_3 = Lesson(
            course_id=c2.id,
            learning_unit_id=u2_2.id,
            title="Bài 3: Thuật toán Duyệt Đồ thị BFS / DFS & Tìm Đường đi Ngắn nhất",
            summary="Khám phá thuật toán duyệt theo chiều rộng, chiều sâu và định tuyến ngắn nhất với Dijkstra.",
            markdown_content=md_2_3,
            position=3,
            estimated_duration_minutes=55,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=5),
        )
        session.add(les_2_3)
        session.flush()

        pdf_2_3_data = generate_pdf_document(
            title="LY THUYET DO THI NANG CAO: THUAT TOAN BFS, DFS VA DIJKSTRA",
            subtitle="Hoc phan DSA201 - Chuong 2: Do thi & Ung dung",
            topics=[
                "Bieu dien do thi: Ma tran ke vs Danh sach ke (Adjacency List)",
                "Cai dat thuat toan BFS va DFS bang ngon ngu Python",
                "Thuat toan Dijkstra voi Priority Queue giam do phuc tap xuong O(E log V)",
                "Phat hien chu trinh trong do thi co huong bang thuat toan Tarjan",
            ],
        )
        fa_pdf_2_3 = store_file_stream(
            actor=inst2,
            course_id=c2.id,
            file_stream=io.BytesIO(pdf_2_3_data),
            filename="Thuat_toan_Do_thi_Dijkstra_AStar.pdf",
            content_type="application/pdf",
            asset_type="RESOURCE",
            title="Tài liệu chuyên đề: Lý thuyết Đồ thị & Dijkstra",
            session=session,
        )
        attach_resource_to_lesson(
            actor=inst2,
            lesson_id=les_2_3.id,
            asset_id=fa_pdf_2_3.id,
            is_downloadable=True,
            label="Chuyên đề: Thuật toán Đồ thị nâng cao (PDF)",
            session=session,
        )

        # Formal Assessment for Course 2
        logger.info("Seeding formal assessment for Course 2...")
        asm2 = Assessment(
            course_id=c2.id,
            title="Kiểm tra Giữa kỳ: Cấu trúc Dữ liệu & Giải thuật Nâng cao",
            description="Bài đánh giá toàn diện về phân tích độ phức tạp Big-O, Heap và Đồ thị.",
            assessment_type="MIDTERM",
            status="PUBLISHED",
            time_limit_minutes=60,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("60.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=4),
        )
        session.add(asm2)
        session.flush()

        sec2 = AssessmentSection(
            assessment_id=asm2.id,
            title="Phần 1: Tư duy Giải thuật & Cấu trúc Dữ liệu",
            position=1,
            instructions="Đọc kỹ câu hỏi và chọn đáp án chính xác.",
        )
        session.add(sec2)
        session.flush()

        q2_1 = Question(
            course_id=c2.id,
            lesson_id=les_2_1.id,
            creator_user_id=inst2.id,
            difficulty="UNDERSTAND",
            learning_objective="Big-O Analysis",
            status="ACTIVE",
        )
        session.add(q2_1)
        session.flush()
        q2_1_rev = QuestionRevision(
            question_id=q2_1.id,
            revision_no=1,
            is_current=True,
            created_by_user_id=inst2.id,
            content="Độ phức tạp thời gian trung bình của giải thuật QuickSort khi phân hoạch ngẫu nhiên là gì?",
            question_type="SINGLE_CHOICE",
            explanation="QuickSort có độ phức tạp trung bình là O(n log n).",
            change_type="INITIAL",
            approved_at=now,
        )
        session.add(q2_1_rev)
        session.flush()
        for idx, (lbl, corr) in enumerate(
            [("O(n)", False), ("O(n log n)", True), ("O(n^2)", False), ("O(log n)", False)], 1
        ):
            session.add(
                QuestionRevisionChoice(
                    question_revision_id=q2_1_rev.id,
                    choice_key=uuid.uuid4(),
                    content=lbl,
                    is_correct=corr,
                    position=idx,
                )
            )
        session.add(
            QuestionProvenance(
                question_id=q2_1.id, question_revision_id=q2_1_rev.id, source_type="MANUAL"
            )
        )

        q2_2 = Question(
            course_id=c2.id,
            lesson_id=les_2_2.id,
            creator_user_id=inst2.id,
            difficulty="APPLY",
            learning_objective="Heap properties",
            status="ACTIVE",
        )
        session.add(q2_2)
        session.flush()
        q2_2_rev = QuestionRevision(
            question_id=q2_2.id,
            revision_no=1,
            is_current=True,
            created_by_user_id=inst2.id,
            content="Để xây dựng một Binary Heap từ một mảng n phần tử cho trước, thời gian tối ưu đạt được là bao nhiêu?",
            question_type="SINGLE_CHOICE",
            explanation="Thuật toán Build-Heap từ dưới lên (bottom-up heapify) chỉ mất thời gian O(n).",
            change_type="INITIAL",
            approved_at=now,
        )
        session.add(q2_2_rev)
        session.flush()
        for idx, (lbl, corr) in enumerate(
            [("O(n)", True), ("O(n log n)", False), ("O(n^2)", False), ("O(1)", False)], 1
        ):
            session.add(
                QuestionRevisionChoice(
                    question_revision_id=q2_2_rev.id,
                    choice_key=uuid.uuid4(),
                    content=lbl,
                    is_correct=corr,
                    position=idx,
                )
            )
        session.add(
            QuestionProvenance(
                question_id=q2_2.id, question_revision_id=q2_2_rev.id, source_type="MANUAL"
            )
        )

        session.add(
            AssessmentQuestionAssignment(
                assessment_id=asm2.id,
                question_id=q2_1.id,
                section_id=sec2.id,
                points=decimal.Decimal("50.00"),
                position=1,
            )
        )
        session.add(
            AssessmentQuestionAssignment(
                assessment_id=asm2.id,
                question_id=q2_2.id,
                section_id=sec2.id,
                points=decimal.Decimal("50.00"),
                position=2,
            )
        )

        # =========================================================================
        # COURSE 3: OPS401
        # =========================================================================
        logger.info("Seeding Course 3: OPS401...")
        c3_slo = [
            {
                "title": "SLO-1: Đóng gói Container & Quản trị Image",
                "description": "Thiết kế Dockerfile đa tầng (Multi-stage build), tối ưu layer cache và bảo mật container non-root.",
                "weight": "30%",
            },
            {
                "title": "SLO-2: Tự động hóa CI/CD với GitHub Actions",
                "description": "Xây dựng pipeline tự động kiểm thử tự động, linting, build docker image và deploy lên staging server.",
                "weight": "40%",
            },
            {
                "title": "SLO-3: Điều phối Dịch vụ & Giám sát Hệ thống",
                "description": "Quản lý multi-container với Docker Compose, healthchecks, cấu hình reverse proxy Nginx và giám sát telemetry.",
                "weight": "30%",
            },
        ]
        c3_target = [
            "Lập trình viên Backend muốn làm chủ hạ tầng và quy trình vận hành phần mềm hiện đại",
            "Kỹ sư hệ thống muốn chuyển dịch sang văn hóa DevOps và công nghệ Container hóa",
            "Trưởng nhóm kỹ thuật cần chuẩn hóa pipeline kiểm thử và tự động hóa release cho dự án doanh nghiệp",
        ]
        c3_completion = {
            "minimum_grade_score": 80.0,
            "allow_certificate": True,
            "completion_grace_days": 14,
            "require_all_lessons": True,
        }

        c3 = Course(
            course_code="OPS401",
            course_code_normalized="OPS401",
            title="DevOps, CI/CD Pipeline & Hạ Tầng Điện Toán Đám Mây",
            title_normalized="devops, ci/cd pipeline & hạ tầng điện toán đám mây",
            description=(
                "Lộ trình thực chiến từ đóng gói container với Docker, điều phối dịch vụ với Docker Compose, "
                "xây dựng quy trình tự động hóa CI/CD với GitHub Actions, giám sát hạ tầng và triển khai ứng dụng "
                "an toàn trên đám mây."
            ),
            learning_objectives=json.dumps(c3_slo, ensure_ascii=False),
            target_audience=json.dumps(c3_target, ensure_ascii=False),
            completion_requirements=json.dumps(c3_completion, ensure_ascii=False),
            category="Hạ tầng & Điện toán Đám mây",
            difficulty="ADVANCED",
            owner_instructor_id=inst1.id,
            status="PUBLISHED",
            capacity=45,
            published_at=now - timedelta(days=7),
            approved_at=now - timedelta(days=7),
            approved_by_user_id=admin.id,
        )
        session.add(c3)
        session.flush()

        c3_img_bytes = generate_course_cover_png("OPS401", ((16, 24, 40), (28, 40, 60)))
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
                require_required_assessments=True,
                minimum_progress_percent=decimal.Decimal("80.00"),
                updated_by_user_id=inst1.id,
            )
        )

        # Chapter 1 of OPS401
        u3_1 = LearningUnit(
            course_id=c3.id,
            title="Chương 1: Đóng gói Container với Docker & Tối ưu Image",
            position=1,
            created_at=now - timedelta(days=6),
        )
        session.add(u3_1)
        session.flush()

        quiz_3_1 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Kỹ thuật Multi-Stage Build trong Dockerfile mang lại lợi ích nổi bật nhất nào?",
                "options": [
                    "Tự động cấu hình firewall cho server",
                    "Tách biệt môi trường build cồng kềnh khỏi runtime image cuối cùng, giúp giảm kích thước image từ hàng GB xuống vài chục MB",
                    "Ngăn cấm người dùng chạy container",
                    "Tự động tăng tốc độ đường truyền Internet",
                ],
                "choices": [
                    "Tự động cấu hình firewall cho server",
                    "Tách biệt môi trường build cồng kềnh khỏi runtime image cuối cùng, giúp giảm kích thước image từ hàng GB xuống vài chục MB",
                    "Ngăn cấm người dùng chạy container",
                    "Tự động tăng tốc độ đường truyền Internet",
                ],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "Multi-stage builds cho phép sử dụng image chứa công cụ build (SDK, compilers) ở stage đầu, sau đó chỉ copy artifact đã compile sang stage runtime tối giản (Alpine/Slim).",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Trong môi trường Production, luôn luôn nên chạy container dưới quyền user 'root' mặc định để tránh các lỗi phân quyền file.",
                "correct_answer": False,
                "explanation": "Sai. Đây là lỗi bảo mật nghiêm trọng. Container trong Production bắt buộc phải chạy dưới non-root user (như nobody hoặc appuser) để hạn chế thiệt hại khi xảy ra tấn công container breakout.",
            },
        ]

        md_3_1 = f"""<!-- video_urls: ["https://www.youtube.com/watch?v=kqtD5dpn9C8"] -->
# Đóng Gói Ứng Dụng Backend Đa Tầng với Dockerfile

Khám phá nguyên lý container hóa và các tiêu chuẩn bảo mật cho Docker Image.

## 1. Mẫu Dockerfile Multi-Stage Build Chuẩn
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
            revision_no=1,
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

        # Lesson 3.2
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
            revision_no=1,
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
            revision_no=1,
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

        # Formal Assessment for Course 3
        logger.info("Seeding formal assessment for Course 3...")
        asm3 = Assessment(
            course_id=c3.id,
            title="Kiểm tra Giữa kỳ: Hạ tầng DevOps & Tự động hóa CI/CD",
            description="Bài thi kiểm tra kiến thức đóng gói container Docker, cấu hình docker-compose và viết workflow GitHub Actions.",
            assessment_type="MIDTERM",
            status="PUBLISHED",
            time_limit_minutes=45,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("60.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=3),
        )
        session.add(asm3)
        session.flush()

        sec3 = AssessmentSection(
            assessment_id=asm3.id,
            title="Phần 1: Trắc nghiệm Kiến trúc Container & CI/CD",
            position=1,
            instructions="Đọc kỹ câu hỏi và chọn đáp án chính xác.",
        )
        session.add(sec3)
        session.flush()

        q3_1 = Question(
            course_id=c3.id,
            lesson_id=les_3_1.id,
            creator_user_id=inst1.id,
            difficulty="UNDERSTAND",
            learning_objective="Docker caching",
            status="ACTIVE",
        )
        session.add(q3_1)
        session.flush()
        q3_1_rev = QuestionRevision(
            question_id=q3_1.id,
            revision_no=1,
            is_current=True,
            created_by_user_id=inst1.id,
            content="Thứ tự nào sau đây trong Dockerfile giúp tối ưu hóa Docker Layer Cache tốt nhất khi build ứng dụng Python?",
            question_type="SINGLE_CHOICE",
            explanation="Copy file dependencies trước (requirements/pyproject) giúp tận dụng cache tầng cài đặt thư viện.",
            change_type="INITIAL",
            approved_at=now,
        )
        session.add(q3_1_rev)
        session.flush()
        for idx, (lbl, corr) in enumerate(
            [
                ("Copy pyproject.toml -> Run pip install -> Copy src/", True),
                ("Copy src/ -> Copy pyproject.toml -> Run pip install", False),
                ("Run pip install -> Copy src/ -> Copy pyproject.toml", False),
                ("Không cần quan tâm thứ tự các dòng lệnh", False),
            ],
            1,
        ):
            session.add(
                QuestionRevisionChoice(
                    question_revision_id=q3_1_rev.id,
                    choice_key=uuid.uuid4(),
                    content=lbl,
                    is_correct=corr,
                    position=idx,
                )
            )
        session.add(
            QuestionProvenance(
                question_id=q3_1.id, question_revision_id=q3_1_rev.id, source_type="MANUAL"
            )
        )

        q3_2 = Question(
            course_id=c3.id,
            lesson_id=les_3_3.id,
            creator_user_id=inst1.id,
            difficulty="APPLY",
            learning_objective="CI/CD Pipelines",
            status="ACTIVE",
        )
        session.add(q3_2)
        session.flush()
        q3_2_rev = QuestionRevision(
            question_id=q3_2.id,
            revision_no=1,
            is_current=True,
            created_by_user_id=inst1.id,
            content="Sự kiện (Event trigger) nào thường được cấu hình trong GitHub Actions để kích hoạt pipeline kiểm thử tự động mỗi khi thành viên gửi code mới?",
            question_type="SINGLE_CHOICE",
            explanation="Sự kiện push và pull_request là hai trigger cốt lõi cho CI pipeline.",
            change_type="INITIAL",
            approved_at=now,
        )
        session.add(q3_2_rev)
        session.flush()
        for idx, (lbl, corr) in enumerate(
            [
                ("push và pull_request", True),
                ("schedule hàng năm", False),
                ("watch repository", False),
                ("delete branch", False),
            ],
            1,
        ):
            session.add(
                QuestionRevisionChoice(
                    question_revision_id=q3_2_rev.id,
                    choice_key=uuid.uuid4(),
                    content=lbl,
                    is_correct=corr,
                    position=idx,
                )
            )
        session.add(
            QuestionProvenance(
                question_id=q3_2.id, question_revision_id=q3_2_rev.id, source_type="MANUAL"
            )
        )

        session.add(
            AssessmentQuestionAssignment(
                assessment_id=asm3.id,
                question_id=q3_1.id,
                section_id=sec3.id,
                points=decimal.Decimal("50.00"),
                position=1,
            )
        )
        session.add(
            AssessmentQuestionAssignment(
                assessment_id=asm3.id,
                question_id=q3_2.id,
                section_id=sec3.id,
                points=decimal.Decimal("50.00"),
                position=2,
            )
        )

        # =========================================================================
        # ENROLLMENTS, DEMO PROGRESS & ATTEMPT RESULTS
        # =========================================================================
        logger.info("Setting up enrollments, progress, and assessment attempt...")
        from pwd301.services.enrollment_service import enroll_student

        e1 = enroll_student(actor=student1, course_id=c1.id, session=session)
        enroll_student(actor=student1, course_id=c2.id, session=session)
        enroll_student(actor=student2, course_id=c1.id, session=session)
        enroll_student(actor=student3, course_id=c3.id, session=session)
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
                    acknowledged_revision_no=1,
                    completion_rule_snapshot_json=json.dumps(
                        {
                            "personal_notes": "Đã ghi nhớ các chuẩn HTTP methods và quy ước status codes.",
                            "mini_quiz_completed_at": (now - timedelta(days=3)).isoformat(),
                            "mini_quiz_question_count": 4,
                        }
                    ),
                )
            )
            session.add(
                LessonProgress(
                    enrollment_period_id=e1.current_period_id,
                    lesson_id=les_1_2.id,
                    seconds_spent=420,
                    max_view_fraction=decimal.Decimal("0.9500"),
                    completed_at=now - timedelta(days=2),
                    acknowledged_revision_no=1,
                    completion_rule_snapshot_json=json.dumps(
                        {
                            "personal_notes": "Đã hoàn thành video hướng dẫn Application Factory Pattern.",
                            "mini_quiz_completed_at": (now - timedelta(days=2)).isoformat(),
                            "mini_quiz_question_count": 2,
                        }
                    ),
                )
            )

        # student1 completed Attempt on Course 1 Assessment (score 100.00)
        attempt1 = AssessmentAttempt(
            assessment_id=asm1.id,
            enrollment_period_id=e1.current_period_id,
            student_user_id=student1.id,
            attempt_number=1,
            status="GRADED",
            started_at=now - timedelta(hours=3),
            deadline_at=now - timedelta(hours=2, minutes=15),
            submitted_at=now - timedelta(hours=2, minutes=20),
            graded_at=now - timedelta(hours=2, minutes=19),
            finalized_at=now - timedelta(hours=2, minutes=19),
        )
        session.add(attempt1)
        session.flush()

        aq1 = AttemptQuestion(
            attempt_id=attempt1.id,
            source_question_id=q1_1.id,
            source_question_revision_id=q1_1_rev.id,
            position=1,
            question_type_snapshot=q1_1_rev.question_type,
            content_snapshot=q1_1_rev.content,
            points_assigned=decimal.Decimal("50.0000"),
        )
        session.add(aq1)
        session.flush()

        for c_pos, choice in enumerate(q1_1_rev.choices, start=1):
            acs = AttemptChoiceSnapshot(
                attempt_question_id=aq1.id,
                source_choice_id=choice.id,
                choice_key_snapshot=choice.choice_key,
                content_snapshot=choice.content,
                position=c_pos,
            )
            session.add(acs)

        aq2 = AttemptQuestion(
            attempt_id=attempt1.id,
            source_question_id=q1_2.id,
            source_question_revision_id=q1_2_rev.id,
            position=2,
            question_type_snapshot=q1_2_rev.question_type,
            content_snapshot=q1_2_rev.content,
            points_assigned=decimal.Decimal("50.0000"),
        )
        session.add(aq2)
        session.flush()

        for c_pos, choice in enumerate(q1_2_rev.choices, start=1):
            acs = AttemptChoiceSnapshot(
                attempt_question_id=aq2.id,
                source_choice_id=choice.id,
                choice_key_snapshot=choice.choice_key,
                content_snapshot=choice.content,
                position=c_pos,
            )
            session.add(acs)

        ans1 = AttemptAnswer(
            attempt_question_id=aq1.id,
            saved_at=now - timedelta(hours=2, minutes=25),
        )
        session.add(ans1)

        session.add(
            AttemptQuestionGrade(
                attempt_question_id=aq1.id,
                awarded_points=decimal.Decimal("50.0000"),
                grading_status="AUTO_GRADED",
                grading_rule="ORIGINAL",
                graded_by_user_id=inst1.id,
                graded_at=now - timedelta(hours=2, minutes=19),
            )
        )

        ans2 = AttemptAnswer(
            attempt_question_id=aq2.id,
            saved_at=now - timedelta(hours=2, minutes=22),
        )
        session.add(ans2)

        session.add(
            AttemptQuestionGrade(
                attempt_question_id=aq2.id,
                awarded_points=decimal.Decimal("50.0000"),
                grading_status="AUTO_GRADED",
                grading_rule="ORIGINAL",
                graded_by_user_id=inst1.id,
                graded_at=now - timedelta(hours=2, minutes=19),
            )
        )

        session.add(
            AssessmentResult(
                attempt_id=attempt1.id,
                raw_score=decimal.Decimal("100.0000"),
                max_score=decimal.Decimal("100.0000"),
                percent_score=decimal.Decimal("100.0000"),
                passed=True,
                status="RELEASED",
                released_at=now - timedelta(hours=2, minutes=19),
                graded_at=now - timedelta(hours=2, minutes=19),
            )
        )

        session.commit()
        logger.info(
            "Done! Successfully seeded 3 rich courses with full multimedia, PDFs, quizzes, and assessments!"
        )


if __name__ == "__main__":
    seed_courses()
