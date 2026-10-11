"""Seed 10 Comprehensive Cybersecurity Courses & 10 User Accounts for PWD301.

Creates:
1. 10 User Accounts + 1 Root Administrator:
   - admin@pwd301.local: Quản trị viên tối cao (ADMIN_PRIMARY)
   - admin.course1@pwd301.local: Admin duyệt khóa học 1 (ADMIN_COURSE_REVIEW)
   - admin.course2@pwd301.local: Admin duyệt khóa học 2 (ADMIN_COURSE_REVIEW)
   - admin.instructor@pwd301.local: Admin duyệt hồ sơ giảng viên (ADMIN_INSTRUCTOR_REVIEW)
   - admin.teaching@pwd301.local: Admin phân công giảng dạy (ADMIN_TEACHING_ASSIGNMENT)
   - admin.monitor@pwd301.local: Admin giám sát hệ thống (ADMIN_SYSTEM_MONITORING)
   - instructor1@pwd301.local: TS. Nguyễn An Ninh (An ninh Ứng dụng & Pentest)
   - instructor2@pwd301.local: ThS. Trần Quốc Bảo (Phòng thủ SOC & Cloud)
   - student1@pwd301.local: Lê Hoàng Long (Học lực Xuất sắc 95%)
   - student2@pwd301.local: Phạm Minh Tuấn (Học lực Khá 75%)
   - student3@pwd301.local: Vũ Thảo Nguyên (Mới nhập học)
   Password for all accounts: 'Password123!'

2. 10 Comprehensive Cybersecurity Courses (sourced from F:\\cyber\\khóa học all):
   - SEC101: Bug Bounty Hunting & Bảo mật Ứng dụng Web (23 video MP4 thực tế)
   - PYK201: Lập trình Python Tấn công & Tự động hóa Kali Linux (Video MP4 thực tế 561MB)
   - CEH301: Certified Ethical Hacker (CEH) v10 & Thực hành Lab Xâm nhập (PDF CEHv10 Module 1-5)
   - BLU301: Phòng thủ An ninh Mạng (Blue Team Operations) & Điều tra Sự cố (PDF Splunk & Playbook)
   - NET201: An ninh Hạ tầng Mạng & Điện toán Đám mây (Cloud Security)
   - CRY201: Mật mã học Ứng dụng & An toàn Dữ liệu (Cryptography)
   - DEV301: DevSecOps: Tích hợp An ninh trong CI/CD Pipeline & Cloud Native
   - KAL101: Làm chủ Bộ công cụ Kiểm thử Xâm nhập Kali Linux
   - THI301: Tình báo Mối đe dọa (Threat Intelligence) & Dark Web Investigations
   - WIR201: An ninh Mạng Không dây, Bluetooth & Thiết bị IoT

Each course features:
- Standard Learning Objectives (SLO), target audience, completion requirements.
- Full course banner cover image generated via pure Python stdlib PNG.
- Chapters (LearningUnits) and sequential lessons with rich Markdown, summary & duration.
- Authentic MP4 videos and PDFs from 'F:\\cyber\\khóa học all' attached to lessons via store_file_stream.
- Interactive mini-quizzes supporting 4 question types with detailed explanations.
- Formal Assessment (Exam) with question assignments totaling 100.00 points.
- Student enrollments and initial learning progress & attempt scores.
"""

from __future__ import annotations

import decimal
import io
import json
import logging
from pathlib import Path
import struct
import sys
import uuid
import zlib
from datetime import timedelta

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
    AttemptAnswer,
    AttemptAnswerChoice,
    AttemptChoiceSnapshot,
    AttemptQuestion,
    AttemptQuestionGrade,
)
from pwd301.models.course import (
    Course,
    CourseCompletionRule,
    LearningUnit,
    Lesson,
    LessonProgress,
)
from pwd301.models.file_import import (
    FileAsset,
)
from pwd301.models.identity import Role, User, UserRole
from pwd301.models.question_bank import (
    Question,
    QuestionProvenance,
    QuestionRevision,
    QuestionRevisionChoice,
)
from pwd301.models.types import utc_now
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.file_service import attach_resource_to_lesson, store_file_stream

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("seed_10_cyber_courses")

CYBER_DIR = Path(r"F:\cyber\khóa học all")


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

    cleanup_stmts = [
        "UPDATE ai_conversations SET course_id = NULL WHERE course_id IS NOT NULL",
        "DELETE FROM ai_generated_question_drafts WHERE course_id IS NOT NULL",
        "DELETE FROM knowledge_chunks WHERE document_version_id IN (SELECT id FROM knowledge_versions WHERE document_id IN (SELECT id FROM knowledge_documents WHERE course_id IS NOT NULL))",
        "DELETE FROM knowledge_versions WHERE document_id IN (SELECT id FROM knowledge_documents WHERE course_id IS NOT NULL)",
        "DELETE FROM knowledge_documents WHERE course_id IS NOT NULL",
        "DELETE FROM import_questions WHERE import_job_id IN (SELECT id FROM document_import_jobs WHERE course_id IS NOT NULL)",
        "DELETE FROM document_import_jobs WHERE course_id IS NOT NULL",
        "DELETE FROM grade_exports WHERE course_id IS NOT NULL",
        "DELETE FROM regrade_items",
        "DELETE FROM regrade_jobs",
        "DELETE FROM attempt_focus_events",
        "DELETE FROM attempt_answer_events",
        "DELETE FROM attempt_question_grade_history",
        "DELETE FROM attempt_question_grades",
        "DELETE FROM attempt_answer_choices",
        "DELETE FROM attempt_answers",
        "DELETE FROM attempt_choice_snapshots",
        "DELETE FROM attempt_questions",
        "DELETE FROM assessment_result_history",
        "DELETE FROM assessment_results",
        "DELETE FROM assessment_attempts",
        "DELETE FROM lesson_progress",
        "DELETE FROM enrollment_events",
        "DELETE FROM enrollment_periods",
        "DELETE FROM enrollments",
        "DELETE FROM assessment_question_assignments",
        "DELETE FROM assessment_question_pool",
        "DELETE FROM assessment_blueprint_rules",
        "DELETE FROM assessment_sections",
        "DELETE FROM assessments",
        "DELETE FROM question_provenance",
        "DELETE FROM question_corrections",
        "DELETE FROM question_revision_choices",
        "DELETE FROM question_revision_accepted_answers",
        "DELETE FROM question_revisions",
        "DELETE FROM questions",
        "DELETE FROM lesson_resources",
        "DELETE FROM lessons",
        "DELETE FROM learning_units",
        "DELETE FROM course_change_requests",
        "DELETE FROM course_completion_rules",
        "DELETE FROM course_completion_summaries",
        "DELETE FROM course_prerequisites",
        "DELETE FROM file_scan_results",
        "DELETE FROM file_revisions",
        "DELETE FROM file_assets WHERE course_id IS NOT NULL",
        "DELETE FROM courses",
    ]

    for stmt in cleanup_stmts:
        try:
            session.execute(sa.text(stmt))
            session.commit()
        except Exception as e:
            session.rollback()
            logger.debug(f"Cleanup stmt skipped ({stmt[:30]}...): {e}")

    for tbl in all_tables_with_triggers:
        try:
            session.execute(sa.text(f"ALTER TABLE {tbl} ENABLE TRIGGER ALL"))
        except Exception as e:
            logger.debug(f"Enable trigger warning on {tbl}: {e}")
    session.commit()
    logger.info("Course cleanup complete.")


def get_or_create_users(session: Session) -> dict[str, User]:
    """Ensure baseline roles and the 10 specified user accounts exist with full roles."""
    logger.info("Seeding canonical roles and 10 user accounts...")

    role_data = [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]
    roles: dict[str, Role] = {}
    for code, name in role_data:
        r = session.query(Role).filter(Role.code == code).first()
        if r is None:
            r = Role(code=code, name=name)
            session.add(r)
            session.flush()
        roles[code] = r

    user_configs = [
        {
            "email": "admin@pwd301.local",
            "name": "Quản Trị Viên Hệ Thống",
            "roles": ["STUDENT", "INSTRUCTOR", "ADMIN"],
            "sub_role": "ADMIN_PRIMARY",
        },
        {
            "email": "admin.course1@pwd301.local",
            "name": "Nguyễn Văn Duyệt 1",
            "roles": ["STUDENT", "ADMIN"],
            "sub_role": "ADMIN_COURSE_REVIEW",
        },
        {
            "email": "admin.course2@pwd301.local",
            "name": "Trần Thị Kiểm 2",
            "roles": ["STUDENT", "ADMIN"],
            "sub_role": "ADMIN_COURSE_REVIEW",
        },
        {
            "email": "admin.instructor@pwd301.local",
            "name": "Lê Thanh Thẩm",
            "roles": ["STUDENT", "ADMIN"],
            "sub_role": "ADMIN_INSTRUCTOR_REVIEW",
        },
        {
            "email": "admin.teaching@pwd301.local",
            "name": "Hoàng Văn Phân",
            "roles": ["STUDENT", "ADMIN"],
            "sub_role": "ADMIN_TEACHING_ASSIGNMENT",
        },
        {
            "email": "admin.monitor@pwd301.local",
            "name": "Phạm Quốc Giám",
            "roles": ["STUDENT", "ADMIN"],
            "sub_role": "ADMIN_SYSTEM_MONITORING",
        },
        {
            "email": "instructor1@pwd301.local",
            "name": "TS. Nguyễn An Ninh",
            "roles": ["STUDENT", "INSTRUCTOR"],
            "sub_role": None,
        },
        {
            "email": "instructor2@pwd301.local",
            "name": "ThS. Trần Quốc Bảo",
            "roles": ["STUDENT", "INSTRUCTOR"],
            "sub_role": None,
        },
        {
            "email": "student1@pwd301.local",
            "name": "Lê Hoàng Long",
            "roles": ["STUDENT"],
            "sub_role": None,
        },
        {
            "email": "student2@pwd301.local",
            "name": "Phạm Minh Tuấn",
            "roles": ["STUDENT"],
            "sub_role": None,
        },
        {
            "email": "student3@pwd301.local",
            "name": "Vũ Thảo Nguyên",
            "roles": ["STUDENT"],
            "sub_role": None,
        },
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
            link = (
                session.query(UserRole)
                .filter(UserRole.user_id == u.id, UserRole.role_id == r_obj.id)
                .first()
            )
            assignment_reason = "System Seed"
            if r_code == "ADMIN" and cfg.get("sub_role"):
                assignment_reason = f"System Seed | SUB_ROLE:{cfg['sub_role']}"

            if not link:
                session.add(
                    UserRole(
                        user_id=u.id,
                        role_id=r_obj.id,
                        assigned_by_user_id=u.id,
                        assignment_reason=assignment_reason,
                    )
                )
            else:
                if r_code == "ADMIN" and cfg.get("sub_role"):
                    link.assignment_reason = assignment_reason

        users[norm] = u

    session.commit()
    logger.info("User accounts seeded successfully.")
    return users


def attach_file_safely(
    session: Session,
    actor: User,
    course_id: int,
    lesson_id: int,
    file_path: Path,
    label: str,
    title: str,
    is_video: bool = False,
    is_downloadable: bool = True,
) -> FileAsset | None:
    """Read a real file from disk, ingest via store_file_stream and attach to lesson."""
    if not file_path.exists():
        logger.warning(f"File not found on disk, skipping: {file_path}")
        return None

    try:
        content_type = "video/mp4" if is_video else "application/pdf"
        with open(file_path, "rb") as f_stream:
            fa = store_file_stream(
                actor=actor,
                course_id=course_id,
                file_stream=f_stream,
                filename=file_path.name,
                content_type=content_type,
                asset_type="RESOURCE",
                title=title,
                session=session,
            )
        attach_resource_to_lesson(
            actor=actor,
            lesson_id=lesson_id,
            asset_id=fa.id,
            is_downloadable=is_downloadable,
            label=label,
            session=session,
        )
        logger.info(f"Attached file asset: {file_path.name} -> Lesson ID {lesson_id}")
        return fa
    except Exception as ex:
        logger.error(f"Error attaching file {file_path.name}: {ex}", exc_info=True)
        return None


def add_question_to_assessment(
    session: Session,
    course_id: int,
    lesson_id: int,
    instructor_id: int,
    assessment_id: int,
    section_id: int,
    position: int,
    content: str,
    q_type: str,
    choices: list[tuple[str, bool]],
    explanation: str,
    points: decimal.Decimal,
) -> Question:
    """Helper to build Question, QuestionRevision, Choices, and Assessment Assignment."""
    now = utc_now()
    q = Question(
        course_id=course_id,
        lesson_id=lesson_id,
        creator_user_id=instructor_id,
        difficulty="APPLY",
        learning_objective="Cybersecurity Mastery",
        status="ACTIVE",
    )
    session.add(q)
    session.flush()

    q_rev = QuestionRevision(
        question_id=q.id,
        revision_no=1,
        is_current=True,
        created_by_user_id=instructor_id,
        content=content,
        question_type=q_type,
        explanation=explanation,
        change_type="INITIAL",
        approved_at=now,
    )
    session.add(q_rev)
    session.flush()

    for idx, (lbl, is_corr) in enumerate(choices, start=1):
        session.add(
            QuestionRevisionChoice(
                question_revision_id=q_rev.id,
                choice_key=uuid.uuid4(),
                content=lbl,
                is_correct=is_corr,
                position=idx,
            )
        )

    session.add(
        QuestionProvenance(question_id=q.id, question_revision_id=q_rev.id, source_type="MANUAL")
    )

    session.add(
        AssessmentQuestionAssignment(
            assessment_id=assessment_id,
            question_id=q.id,
            section_id=section_id,
            points=points,
            position=position,
        )
    )
    return q


def create_course_with_cover(
    session: Session,
    actor: User,
    course_code: str,
    title: str,
    description: str,
    category: str,
    difficulty: str,
    slo: list[dict],
    target: list[str],
    bg_gradient: tuple[tuple[int, int, int], tuple[int, int, int]],
    enrollment_count: int = 2,
    passing_grade: float = 75.0,
    days_ago: int = 20,
) -> Course:
    """Create Course entity, generate valid cover PNG, store asset and attach CompletionRule."""
    now = utc_now()
    c = Course(
        course_code=course_code,
        course_code_normalized=course_code.upper(),
        title=title,
        title_normalized=title.lower(),
        description=description,
        learning_objectives=json.dumps(slo, ensure_ascii=False),
        target_audience=json.dumps(target, ensure_ascii=False),
        completion_requirements=json.dumps(
            {
                "minimum_grade_score": passing_grade,
                "allow_certificate": True,
                "require_all_lessons": True,
            },
            ensure_ascii=False,
        ),
        category=category,
        difficulty=difficulty,
        owner_instructor_id=actor.id,
        status="PUBLISHED",
        published_at=now - timedelta(days=days_ago),
    )
    session.add(c)
    session.flush()

    cover_png = generate_course_cover_png(course_code, bg_gradient)
    cover_asset = store_file_stream(
        actor=actor,
        course_id=c.id,
        file_stream=io.BytesIO(cover_png),
        filename=f"cover_{course_code.lower()}.png",
        content_type="image/png",
        asset_type="COURSE_IMAGE",
        title=f"Ảnh bìa khóa học {course_code}",
        session=session,
    )
    c.thumbnail_file_asset_id = cover_asset.id
    session.flush()

    session.add(
        CourseCompletionRule(
            course_id=c.id,
            require_all_required_lessons=True,
            require_required_assessments=True,
            minimum_progress_percent=decimal.Decimal("80.00"),
            updated_by_user_id=actor.id,
        )
    )
    return c


def seed_cyber_courses() -> None:
    """Seed 10 Cybersecurity Courses with rich lessons, 24 videos, PDFs, and assessments."""
    app = create_app()
    with app.app_context():
        session: Session = db.session
        wipe_all_courses(session)
        users = get_or_create_users(session)

        inst1 = users["instructor1@pwd301.local"]
        inst2 = users["instructor2@pwd301.local"]
        student1 = users["student1@pwd301.local"]
        student2 = users["student2@pwd301.local"]
        student3 = users["student3@pwd301.local"]

        now = utc_now()

        # =========================================================================
        # 1. COURSE 1: SEC101 (Bug Bounty Hunting & Web Application Security)
        # =========================================================================
        logger.info("Seeding Course 1: SEC101...")
        c1_slo = [
            {
                "title": "SLO-1: Làm chủ Burp Suite Professional",
                "description": "Thành thạo cấu hình Burp Proxy, Target Scope, Repeater, Intruder và Decoder.",
                "weight": "30%",
            },
            {
                "title": "SLO-2: Khai thác & Phòng thủ OWASP Top 10",
                "description": "Khai thác sâu các lỗ hổng XSS, Path Traversal, Broken Authentication và Injection.",
                "weight": "40%",
            },
            {
                "title": "SLO-3: Phương pháp luận Săn lỗi Bug Bounty",
                "description": "Quy trình trinh sát mục tiêu, viết báo cáo PoC chuẩn mực và nhận tiền thưởng.",
                "weight": "30%",
            },
        ]
        c1_target = [
            "Học viên muốn trở thành Bug Bounty Hunter chuyên nghiệp",
            "Chuyên viên kiểm thử thâm nhập ứng dụng Web (Web Pentester)",
        ]

        c1 = create_course_with_cover(
            session=session,
            actor=inst1,
            course_code="SEC101",
            title="Bug Bounty Hunting & Bảo mật Ứng dụng Web Toàn diện",
            description="Chương trình đào tạo thực chiến về săn lỗi nhận thưởng (Bug Bounty) và kiểm thử xâm nhập ứng dụng web theo tiêu chuẩn OWASP Top 10.",
            category="Web Security",
            difficulty="ADVANCED",
            slo=c1_slo,
            target=c1_target,
            bg_gradient=((180, 20, 20), (25, 25, 30)),
            enrollment_count=3,
            passing_grade=80.0,
        )

        # Unit 1.1: Burp Suite & Thiết lập môi trường Pentest
        u1_1 = LearningUnit(
            course_id=c1.id,
            title="Chương 1: Burp Suite & Thiết lập Môi trường Pentest",
            position=1,
            created_at=now - timedelta(days=20),
        )
        session.add(u1_1)
        session.flush()

        # Lesson 1.1: Burp Suite Installation & UI
        quiz_1_1 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Burp Suite đóng vai trò gì giữa trình duyệt người dùng và ứng dụng web đích?",
                "options": [
                    "Web Server",
                    "Man-in-the-Middle (Intercepting Proxy)",
                    "DNS Resolver",
                    "Antivirus Scanner",
                ],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "Burp Suite hoạt động như một Intercepting Proxy bắt giữ và thao túng gói tin HTTP/HTTPS.",
            },
            {
                "type": "TRUE_FALSE",
                "question": "Burp Proxy cho phép chỉnh sửa trực tiếp nội dung HTTP Request trước khi gửi đến máy chủ web.",
                "correct_answer": True,
                "explanation": "Tính năng Intercept trong tab Proxy cho phép xem và sửa đổi gói tin tùy ý.",
            },
        ]
        md_1_1 = f"""# Cài đặt Burp Suite & Giới thiệu Giao diện Làm việc
Burp Suite là bộ công cụ kiểm thử xâm nhập ứng dụng web hàng đầu thế giới được phát triển bởi PortSwigger.

## 1. Các Tính Năng Cốt Lõi
- **Proxy**: Bắt giữ, giám sát và chỉnh sửa lưu lượng HTTP/HTTPS giữa client và server.
- **Repeater**: Gửi lại các HTTP request riêng lẻ với các tham số thay đổi để kiểm thử phản hồi.
- **Intruder**: Tự động hóa các cuộc tấn công fuzzing và brute-force tham số.
- **Decoder**: Mã hóa và giải mã các định dạng URL, Base64, Hex, HTML entity.

Hãy theo dõi video bài giảng đính kèm và tài liệu hướng dẫn bên dưới!

<!-- mini_quiz: {json.dumps(quiz_1_1, ensure_ascii=False)} -->
"""
        les_1_1 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_1.id,
            title="Bài 1: Cài đặt Burp Suite & Tổng quan Giao diện",
            summary="Hướng dẫn cài đặt Burp Suite và làm quen các tab chức năng cốt lõi.",
            markdown_content=md_1_1,
            position=1,
            estimated_duration_minutes=45,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=20),
        )
        session.add(les_1_1)
        session.flush()

        # Attach real MP4 videos and real PDF from F:\cyber\khóa học all\Bug Bounty Kit
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_1.id,
            CYBER_DIR / "Bug Bounty Kit" / "Burp Suite Installation.mp4",
            "Video bài giảng: Hướng dẫn cài đặt Burp Suite",
            "Video Cài đặt Burp Suite",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_1.id,
            CYBER_DIR / "Bug Bounty Kit" / "Burp Suite Introduction.mp4",
            "Video bài giảng: Giới thiệu giao diện Burp Suite",
            "Video Giới thiệu Burp Suite",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_1.id,
            CYBER_DIR / "Bug Bounty Kit" / "Bug Bounty Guide.pdf",
            "Tài liệu đọc: Sổ tay hướng dẫn Bug Bounty toàn diện",
            "Sổ tay Bug Bounty Toàn diện",
            is_video=False,
            is_downloadable=True,
        )

        # Lesson 1.2: Proxy Tab & CA Certificate
        quiz_1_2 = [
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Tại sao cần cài đặt Burp CA Certificate vào trình duyệt khi kiểm thử HTTPS?",
                "options": [
                    "Để tăng tốc độ tải trang",
                    "Để trình duyệt tin cậy chứng chỉ tự ký của Burp và giải mã gói tin TLS/SSL",
                    "Để tắt tường lửa Windows",
                    "Để tự động đăng nhập tài khoản",
                ],
                "correct_answers": [1],
                "correct_answer": 1,
                "explanation": "Burp Proxy giải mã kết nối TLS bằng cách tạo ra chứng chỉ SSL động được ký bởi CA của Burp.",
            },
        ]
        md_1_2 = f"""# Cấu hình Burp Proxy & Tích hợp CA Certificate
Để kiểm thử các ứng dụng web sử dụng giao thức HTTPS mà không gặp cảnh báo bảo mật, pentester cần cài đặt chứng chỉ PortSwigger CA.

## Các bước tiến hành:
1. Đặt Proxy Listener mặc định tại `127.0.0.1:8080`.
2. Truy cập `http://burp` trên trình duyệt và tải file `cacert.der`.
3. Import chứng chỉ vào Trusted Root Certification Authorities.

<!-- mini_quiz: {json.dumps(quiz_1_2, ensure_ascii=False)} -->
"""
        les_1_2 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_1.id,
            title="Bài 2: Cấu hình Burp Proxy & Import CA Certificate",
            summary="Thiết lập cổng lắng nghe proxy và import chứng chỉ CA để giải mã HTTPS.",
            markdown_content=md_1_2,
            position=2,
            estimated_duration_minutes=40,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=19),
        )
        session.add(les_1_2)
        session.flush()

        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_2.id,
            CYBER_DIR / "Bug Bounty Kit" / "Burp Proxy tab.mp4",
            "Video bài giảng: Chi tiết chức năng Burp Proxy tab",
            "Video Burp Proxy Tab",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_2.id,
            CYBER_DIR / "Bug Bounty Kit" / "How to Import Burp CA Certificate.mp4",
            "Video bài giảng: Hướng dẫn cài đặt chứng chỉ Burp CA",
            "Video Import Burp CA Certificate",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_2.id,
            CYBER_DIR / "Bug Bounty Kit" / "Awesome_Bug_Bounty_Tools_1691635198.pdf",
            "Tài liệu tra cứu: Danh mục Awesome Bug Bounty Tools",
            "Awesome Bug Bounty Tools",
            is_video=False,
            is_downloadable=True,
        )

        # Lesson 1.3: OWASP BWA & Bee-Box bWAPP
        md_1_3 = """# Cài đặt Môi trường Thử nghiệm OWASP BWA & Bee-Box bWAPP
bWAPP (buggy Web Application) là ứng dụng web mã nguồn mở có chủ đích chứa hơn 100 lỗ hổng web từ OWASP Top 10.
"""
        les_1_3 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_1.id,
            title="Bài 3: Cài đặt Môi trường Thử nghiệm OWASP BWA & bWAPP",
            summary="Khởi động máy ảo Bee-Box và OWASP Broken Web Apps làm mục tiêu thực hành.",
            markdown_content=md_1_3,
            position=3,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=18),
        )
        session.add(les_1_3)
        session.flush()

        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_3.id,
            CYBER_DIR / "Bug Bounty Kit" / "OWASP Broken Web Application Installation.mp4",
            "Video bài giảng: Cài đặt máy ảo OWASP Broken Web Application",
            "Video Cài đặt OWASP BWA",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_3.id,
            CYBER_DIR / "Bug Bounty Kit" / "Bee-Box Bwapp installation.mp4",
            "Video bài giảng: Cài đặt máy ảo Bee-Box bWAPP",
            "Video Cài đặt Bee-Box bWAPP",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_3.id,
            CYBER_DIR / "Bug Bounty Kit" / "Web App Bug Bounty Checklist v1.pdf",
            "Checklist kiểm thử: Web App Bug Bounty Checklist v1",
            "Web App Bug Bounty Checklist",
            is_video=False,
            is_downloadable=True,
        )

        # Lesson 1.4: Target Scope in Burp Suite (1 video)
        md_1_4 = """# Xác định Phạm vi Mục tiêu (Target Scope) trong Burp Suite
Thiết lập Target Scope giúp pentester tập trung phân tích lưu lượng của ứng dụng cần kiểm thử và tránh can thiệp ngoài ý muốn.
"""
        les_1_4 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_1.id,
            title="Bài 4: Thiết lập Phạm vi Mục tiêu (Target Scope) trong Burp",
            summary="Cấu hình Target Scope để lọc gói tin và tối ưu hóa phiên làm việc.",
            markdown_content=md_1_4,
            position=4,
            estimated_duration_minutes=35,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=17),
        )
        session.add(les_1_4)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_4.id,
            CYBER_DIR / "Bug Bounty Kit" / "Defining Web Application Target in Burp Suite.mp4",
            "Video bài giảng: Thiết lập phạm vi mục tiêu Target Scope trong Burp",
            "Video Burp Target Scope",
            is_video=True,
            is_downloadable=False,
        )

        # Unit 1.2: Cross-Site Scripting (XSS) & Path Traversal (3 lessons, 6 videos)
        u1_2 = LearningUnit(
            course_id=c1.id,
            title="Chương 2: Khai thác Lỗ hổng XSS & Path Traversal",
            position=2,
            created_at=now - timedelta(days=16),
        )
        session.add(u1_2)
        session.flush()

        # Lesson 1.5: XSS Overview & Reflected XSS (2 videos)
        les_1_5 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_2.id,
            title="Bài 5: Tổng quan Lỗ hổng XSS & Khai thác Reflected XSS",
            summary="Phân tích cơ chế tấn công Cross-Site Scripting và kỹ thuật khai thác Reflected XSS.",
            markdown_content="# Tổng quan Cross-Site Scripting (XSS)\nTìm hiểu các dạng XSS: Reflected, Stored và DOM-based XSS.",
            position=5,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=16),
        )
        session.add(les_1_5)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_5.id,
            CYBER_DIR / "Bug Bounty Kit" / "Cross Site Scripting overview.mp4",
            "Video bài giảng: Tổng quan về lỗ hổng Cross Site Scripting",
            "Video Tổng quan XSS",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_5.id,
            CYBER_DIR / "Bug Bounty Kit" / "XSS Vulnerability found in Reflected search form.mp4",
            "Video bài giảng: Khai thác Reflected XSS qua Form tìm kiếm",
            "Video Khai thác Reflected XSS",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_5.id,
            CYBER_DIR / "Bug Bounty Kit" / "Bug_Bounty_Playbook_2.pdf",
            "Tài liệu đọc: Sổ tay Bug Bounty Playbook tập 2",
            "Bug Bounty Playbook 2",
            is_video=False,
            is_downloadable=True,
        )

        # Lesson 1.6: XSS Security Levels & Impact Prevention (2 videos)
        les_1_6 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_2.id,
            title="Bài 6: XSS Security Levels & Tác động Thực tế",
            summary="Vượt qua các tầng bảo mật Low, Medium, High và phương pháp phòng thủ XSS.",
            markdown_content="# Vượt rào cản XSS & Đánh giá Tác động\nVượt qua bộ lọc phòng thủ và hiểu rõ hậu quả của việc thực thi script độc hại.",
            position=6,
            estimated_duration_minutes=55,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=15),
        )
        session.add(les_1_6)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_6.id,
            CYBER_DIR
            / "Bug Bounty Kit"
            / "XSS Vulnerability with Low Medium and High Security Levels.mp4",
            "Video bài giảng: Khai thác XSS ở cấp độ Low, Medium và High",
            "Video XSS Security Levels",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_6.id,
            CYBER_DIR
            / "Bug Bounty Kit"
            / "XSS Vulnerability Impact in our Real Life and Prevention.mp4",
            "Video bài giảng: Tác động XSS trong thực tế và cách phòng tránh",
            "Video Tác động XSS",
            is_video=True,
            is_downloadable=False,
        )

        # Lesson 1.7: Directory Path Traversal (2 videos)
        les_1_7 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_2.id,
            title="Bài 7: Tấn công Duyệt Thư mục Trái phép (Path Traversal)",
            summary="Khai thác lỗ hổng Directory Path Traversal để đọc file hệ thống và kỹ thuật phòng thủ.",
            markdown_content="# Directory Path Traversal\nKhai thác Path Traversal để đọc các tệp nhạy cảm hệ thống như `/etc/passwd`.",
            position=7,
            estimated_duration_minutes=55,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=14),
        )
        session.add(les_1_7)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_7.id,
            CYBER_DIR / "Bug Bounty Kit" / "Directory Path Traversal.mp4",
            "Video bài giảng: Nguyên lý lỗ hổng Directory Path Traversal",
            "Video Path Traversal",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_7.id,
            CYBER_DIR / "Bug Bounty Kit" / "Directory Path Traversal Example and Prevention.mp4",
            "Video bài giảng: Ví dụ thực hành và phòng thủ Path Traversal",
            "Video Ví dụ Path Traversal",
            is_video=True,
            is_downloadable=False,
        )

        # Unit 1.3: Session Management & Injection Attacks (3 lessons, 6 videos)
        u1_3 = LearningUnit(
            course_id=c1.id,
            title="Chương 3: Session Security & Tấn công Injection",
            position=3,
            created_at=now - timedelta(days=13),
        )
        session.add(u1_3)
        session.flush()

        # Lesson 1.8: Cookies & Session IDs (2 videos)
        les_1_8 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_3.id,
            title="Bài 8: Cơ chế Hoạt động của Cookie & Session IDs",
            summary="Phân tích cơ chế quản lý phiên, cấu trúc cookie và mã định danh phiên.",
            markdown_content="# Cookie & Session Fundamentals\nHiểu rõ vai trò của Session ID trong duy trì trạng thái đăng nhập.",
            position=8,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=13),
        )
        session.add(les_1_8)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_8.id,
            CYBER_DIR / "Bug Bounty Kit" / "Cookie.mp4",
            "Video bài giảng: Cơ chế hoạt động của Cookie",
            "Video Cookie",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_8.id,
            CYBER_DIR / "Bug Bounty Kit" / "started with Session IDs.mp4",
            "Video bài giảng: Làm quen với cấu trúc Session ID",
            "Video Session IDs",
            is_video=True,
            is_downloadable=False,
        )

        # Lesson 1.9: Session Extraction & Broken Authentication (2 videos)
        les_1_9 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_3.id,
            title="Bài 9: Trích xuất Session & Phòng thủ Broken Authentication",
            summary="Kỹ thuật chiếm đoạt phiên và các giải pháp phòng ngừa Broken Authentication.",
            markdown_content="# Broken Authentication & Session Hijacking\nKiểm thử các lỗ hổng Session Hijacking và Cookie Fixation.",
            position=9,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=12),
        )
        session.add(les_1_9)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_9.id,
            CYBER_DIR / "Bug Bounty Kit" / "How to Extract Cookies and Sessions Manipulation.mp4",
            "Video bài giảng: Kỹ thuật trích xuất Cookies và thao túng phiên",
            "Video Session Manipulation",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_9.id,
            CYBER_DIR
            / "Bug Bounty Kit"
            / "Prevention Broken Authentication and Session Management Vulnerabilities.mp4",
            "Video bài giảng: Phòng chống lỗ hổng Broken Authentication",
            "Video Phòng thủ Broken Authentication",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_9.id,
            CYBER_DIR / "Bug Bounty Kit" / "Bug.Bounty.Bootcamp.pdf",
            "Sách chuyên khảo: Bug Bounty Bootcamp",
            "Bug Bounty Bootcamp",
            is_video=False,
            is_downloadable=True,
        )

        # Lesson 1.10: Injection Attacks & Burp Decoder (2 videos)
        les_1_10 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_3.id,
            title="Bài 10: Tấn công Injection & Sử dụng Burp Decoder",
            summary="Khám phá các kỹ thuật tiêm nhiễm dữ liệu và công cụ giải mã Burp Decoder.",
            markdown_content="# Injection Attacks & Decoder\nKhám phá SQL Injection, Command Injection và công cụ Burp Decoder.",
            position=10,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=11),
        )
        session.add(les_1_10)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_10.id,
            CYBER_DIR / "Bug Bounty Kit" / "Getting Started with Injection Attacks.mp4",
            "Video bài giảng: Khởi đầu với các cuộc tấn công Injection",
            "Video Injection Attacks",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_10.id,
            CYBER_DIR / "Bug Bounty Kit" / "Getting Started with Burp Suite Decoder Tool.mp4",
            "Video bài giảng: Sử dụng công cụ giải mã Burp Suite Decoder",
            "Video Burp Decoder",
            is_video=True,
            is_downloadable=False,
        )

        # Unit 1.4: Phương pháp luận & Lộ trình Săn lỗi Nhận thưởng (2 lessons, 4 videos)
        u1_4 = LearningUnit(
            course_id=c1.id,
            title="Chương 4: Phương pháp luận & Quy trình Săn lỗi Nhận thưởng",
            position=4,
            created_at=now - timedelta(days=10),
        )
        session.add(u1_4)
        session.flush()

        # Lesson 1.11: Career Roadmap & Methodologies (2 videos)
        les_1_11 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_4.id,
            title="Bài 11: Lộ trình & Phương pháp luận Bug Bounty",
            summary="Lộ trình phát triển sự nghiệp Bug Hunter và phương pháp luận săn lỗi chuyên nghiệp.",
            markdown_content="# Lộ trình & Phương pháp luận Bug Bounty\nQuy trình tìm kiếm, xác thực và báo cáo lỗ hổng để đạt tiền thưởng cao nhất.",
            position=11,
            estimated_duration_minutes=55,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=10),
        )
        session.add(les_1_11)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_11.id,
            CYBER_DIR / "Bug Bounty Kit" / "How to Become Bug Bounty Hunter.mp4",
            "Video bài giảng: Lộ trình trở thành Bug Bounty Hunter chuyên nghiệp",
            "Video Lộ trình Bug Bounty",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_11.id,
            CYBER_DIR / "Bug Bounty Kit" / "Methodologies of Bug Bounty Hunting.mp4",
            "Video bài giảng: Phương pháp luận săn lỗi nhận thưởng",
            "Video Methodologies",
            is_video=True,
            is_downloadable=False,
        )

        # Lesson 1.12: Program Types & Burp Suite Mastery (2 videos)
        les_1_12 = Lesson(
            course_id=c1.id,
            learning_unit_id=u1_4.id,
            title="Bài 12: Phân loại Chương trình & Làm chủ Burp Suite Thực chiến",
            summary="Tìm hiểu các loại chương trình Bug Bounty và đúc kết kỹ năng Burp Suite.",
            markdown_content="# Phân loại Chương trình Bug Bounty & Tổng kết\nChiến lược chọn chương trình Public vs Private và viết báo cáo chuẩn CVSS.",
            position=12,
            estimated_duration_minutes=55,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=9),
        )
        session.add(les_1_12)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_12.id,
            CYBER_DIR / "Bug Bounty Kit" / "Types of Bug Bounty Programs.mp4",
            "Video bài giảng: Các loại chương trình Bug Bounty (Public vs Private)",
            "Video Types of Bug Bounty",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_12.id,
            CYBER_DIR / "Bug Bounty Kit" / "Getting Started with Burp Suite.mp4",
            "Video bài giảng: Làm chủ công cụ Burp Suite thực chiến",
            "Video Burp Suite Thực chiến",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c1.id,
            les_1_12.id,
            CYBER_DIR / "Bug Bounty Kit" / "BUG_BOUNTY_HUNTING_ESSENTIALS.pdf",
            "Tài liệu đọc: Bug Bounty Hunting Essentials",
            "Bug Bounty Hunting Essentials",
            is_video=False,
            is_downloadable=True,
        )

        # Assessment Course 1: 100 points
        asm1 = Assessment(
            course_id=c1.id,
            title="Đánh giá Cuối khóa: Kỹ năng Săn lỗi Nhận thưởng (Bug Bounty Final Exam)",
            description="Bài thi trắc nghiệm đánh giá toàn diện năng lực khai thác lỗ hổng web và phân tích gói tin Burp Suite.",
            assessment_type="FINAL",
            status="PUBLISHED",
            time_limit_minutes=60,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("70.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=10),
        )
        session.add(asm1)
        session.flush()

        sec1 = AssessmentSection(
            assessment_id=asm1.id,
            title="Phần 1: Trắc nghiệm Kiến thức Thực chiến Web Security",
            position=1,
            instructions="Chọn đáp án chính xác nhất.",
        )
        session.add(sec1)
        session.flush()

        q1_1 = add_question_to_assessment(
            session,
            c1.id,
            les_1_1.id,
            inst1.id,
            asm1.id,
            sec1.id,
            1,
            "Thành phần nào trong Burp Suite được sử dụng để bắt và sửa đổi các request HTTP/HTTPS theo thời gian thực?",
            "SINGLE_CHOICE",
            [
                ("Proxy Intercept", True),
                ("Spider", False),
                ("Sequencer", False),
                ("Comparer", False),
            ],
            "Proxy Intercept là công cụ chủ lực để can thiệp gói tin thời gian thực.",
            decimal.Decimal("50.00"),
        )
        q1_2 = add_question_to_assessment(
            session,
            c1.id,
            les_1_5.id,
            inst1.id,
            asm1.id,
            sec1.id,
            2,
            "Hậu quả nghiêm trọng nhất của lỗ hổng Stored XSS là gì?",
            "SINGLE_CHOICE",
            [
                ("Chiếm đoạt Cookie/Session token của người dùng truy cập trang", True),
                ("Làm sập máy chủ web ngay lập tức", False),
                ("Tự động xóa cơ sở dữ liệu SQL", False),
                ("Tăng băng thông mạng", False),
            ],
            "Stored XSS thực thi mã JavaScript độc hại trên trình duyệt nạn nhân, cho phép đánh cắp Cookie/Session.",
            decimal.Decimal("50.00"),
        )

        # =========================================================================
        # 2. COURSE 2: PYK201 (Python Security Scripting for Kali Linux)
        # =========================================================================
        logger.info("Seeding Course 2: PYK201...")
        c2_slo = [
            {
                "title": "SLO-1: Lập trình Socket & Quét Mạng",
                "description": "Tự viết Network Scanner, Port Scanner đa luồng bằng thư viện socket chuẩn Python.",
                "weight": "40%",
            },
            {
                "title": "SLO-2: Tương tác Scapy & Thao túng Gói tin",
                "description": "Tạo gói tin ARP spoofing, TCP SYN flood và phân tích pcap bằng Scapy.",
                "weight": "60%",
            },
        ]

        c2 = create_course_with_cover(
            session=session,
            actor=inst1,
            course_code="PYK201",
            title="Lập trình Python Tấn công & Tự động hóa trên Kali Linux",
            description="Làm chủ ngôn ngữ lập trình Python trong tấn công mạng, tự động hóa dò quét cổng, phân tích gói tin và viết công cụ an ninh trên Kali Linux.",
            category="Penetration Testing",
            difficulty="INTERMEDIATE",
            slo=c2_slo,
            target=["Kỹ sư An toàn Thông tin", "Lập trình viên muốn học viết công cụ Pentest"],
            bg_gradient=((10, 30, 80), (15, 15, 25)),
            enrollment_count=2,
            passing_grade=75.0,
        )

        u2_1 = LearningUnit(
            course_id=c2.id,
            title="Chương 1: Python Pentesting Fundamentals",
            position=1,
            created_at=now - timedelta(days=20),
        )
        session.add(u2_1)
        session.flush()

        les_2_1 = Lesson(
            course_id=c2.id,
            learning_unit_id=u2_1.id,
            title="Bài 1: Khóa học Python Toàn diện cho Kali Linux (Thực hành)",
            summary="Bài giảng video 561MB hướng dẫn toàn diện từ cơ bản đến nâng cao lập trình Python trên Kali Linux.",
            markdown_content="# Python Course for Kali Linux\nTheo dõi video toàn diện đính kèm để nắm vững cú pháp Python và môi trường dòng lệnh Linux.",
            position=1,
            estimated_duration_minutes=180,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=20),
        )
        session.add(les_2_1)
        session.flush()

        # Attach real 561MB video from F:\cyber\khóa học all\Python Course Kali linux
        py_vid_path = CYBER_DIR / "Python Course Kali linux" / "Python Course for Kali Linux.mp4"
        attach_file_safely(
            session,
            inst1,
            c2.id,
            les_2_1.id,
            py_vid_path,
            "Video bài giảng lớn: Khóa học Python chuyên sâu cho Kali Linux (561MB)",
            "Python Kali Linux Video Course",
            is_video=True,
            is_downloadable=False,
        )
        attach_file_safely(
            session,
            inst1,
            c2.id,
            les_2_1.id,
            CYBER_DIR / "5 Best Books" / "Begin Ethical Hacking with Python.pdf",
            "Giáo trình: Begin Ethical Hacking with Python",
            "Begin Ethical Hacking with Python",
            is_video=False,
            is_downloadable=True,
        )

        les_2_2 = Lesson(
            course_id=c2.id,
            learning_unit_id=u2_1.id,
            title="Bài 2: Lập trình Socket & Xây dựng Port Scanner Đa luồng",
            summary="Tự viết công cụ dò quét cổng TCP/UDP sử dụng thư viện socket và threading trong Python.",
            markdown_content="# Socket Programming & Port Scanner\nXây dựng công cụ quét cổng mạng tốc độ cao.",
            position=2,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=19),
        )
        session.add(les_2_2)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c2.id,
            les_2_2.id,
            CYBER_DIR / "Books Combo pack" / "BlackHatPython2E.pdf",
            "Sách tham khảo: Black Hat Python (2nd Edition)",
            "Black Hat Python",
            is_video=False,
            is_downloadable=True,
        )

        # Assessment Course 2: 100 points
        asm2 = Assessment(
            course_id=c2.id,
            title="Kiểm tra Cuối khóa: Lập trình Công cụ An ninh Mạng bằng Python",
            description="Đánh giá kỹ năng lập trình socket mạng và tự động hóa pentest.",
            assessment_type="FINAL",
            status="PUBLISHED",
            time_limit_minutes=45,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("70.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=10),
        )
        session.add(asm2)
        session.flush()

        sec2 = AssessmentSection(
            assessment_id=asm2.id,
            title="Phần 1: Lập trình Mạng & An ninh",
            position=1,
            instructions="Chọn đáp án đúng.",
        )
        session.add(sec2)
        session.flush()

        add_question_to_assessment(
            session,
            c2.id,
            les_2_2.id,
            inst1.id,
            asm2.id,
            sec2.id,
            1,
            "Thư viện nào trong Python cung cấp giao diện cấp thấp để tương tác trực tiếp với giao thức mạng TCP/UDP?",
            "SINGLE_CHOICE",
            [("socket", True), ("json", False), ("sys", False), ("math", False)],
            "Thư viện socket là thư viện chuẩn của Python để làm việc với kết nối mạng tầng transport.",
            decimal.Decimal("50.00"),
        )
        add_question_to_assessment(
            session,
            c2.id,
            les_2_2.id,
            inst1.id,
            asm2.id,
            sec2.id,
            2,
            "Cờ cắm (Flag) nào trong giao thức TCP được gửi đi từ client để bắt đầu quá trình bắt tay 3 bước (3-way handshake)?",
            "SINGLE_CHOICE",
            [("SYN", True), ("FIN", False), ("RST", False), ("ACK", False)],
            "Client gửi gói tin SYN để yêu cầu đồng bộ hóa số thứ tự (sequence number).",
            decimal.Decimal("50.00"),
        )

        # =========================================================================
        # 3. COURSE 3: CEH301 (Certified Ethical Hacker v10 & Labs)
        # =========================================================================
        logger.info("Seeding Course 3: CEH301...")
        c3_slo = [
            {
                "title": "SLO-1: Thu thập Thông tin & Trinh sát",
                "description": "Sử dụng OSINT, Google Dorking, Whois và DNS Reconnaissance.",
                "weight": "50%",
            },
            {
                "title": "SLO-2: Dò quét & Đánh giá Lỗ hổng",
                "description": "Thành thạo Nmap, Hping3, Nessus và OpenVAS để lập bản đồ mạng.",
                "weight": "50%",
            },
        ]

        c3 = create_course_with_cover(
            session=session,
            actor=inst1,
            course_code="CEH301",
            title="Certified Ethical Hacker (CEH) v10 & Thực hành Lab Xâm nhập",
            description="Chương trình đào tạo chuẩn chứng chỉ quốc tế CEH v10 với đầy đủ tài liệu học tập chính hãng từ EC-Council và bài thực hành lab chi tiết.",
            category="Ethical Hacking",
            difficulty="ADVANCED",
            slo=c3_slo,
            target=["Chuyên viên An ninh Mạng", "Ứng viên chuẩn bị thi chứng chỉ quốc tế CEH"],
            bg_gradient=((40, 20, 90), (10, 10, 20)),
            enrollment_count=2,
            passing_grade=75.0,
        )

        u3_1 = LearningUnit(
            course_id=c3.id,
            title="Chương 1: Trinh sát & Dò quét Mạng (Reconnaissance & Scanning)",
            position=1,
            created_at=now - timedelta(days=20),
        )
        session.add(u3_1)
        session.flush()

        les_3_1 = Lesson(
            course_id=c3.id,
            learning_unit_id=u3_1.id,
            title="Bài 1: Giới thiệu Ethical Hacking & Quy tắc Đạo đức",
            summary="Tổng quan về lĩnh vực Hacker mũ trắng, luật pháp an ninh mạng và quy trình kiểm thử.",
            markdown_content="# Giới thiệu CEH v10\nNghiên cứu tài liệu chính thức EC-Council Module 01 đính kèm.",
            position=1,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=20),
        )
        session.add(les_3_1)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c3.id,
            les_3_1.id,
            CYBER_DIR / "CEH Bundle" / "CEHv10 Module 01 Introduction to Ethical Hacking.pdf",
            "Tài liệu chính thức: CEHv10 Module 01 Introduction to Ethical Hacking",
            "CEHv10 Module 01",
            is_video=False,
            is_downloadable=True,
        )

        les_3_2 = Lesson(
            course_id=c3.id,
            learning_unit_id=u3_1.id,
            title="Bài 2: Footprinting & Kỹ thuật Thu thập Tình báo",
            summary="Kỹ thuật thu thập thông tin mục tiêu chủ động và thụ động.",
            markdown_content="# Footprinting & Reconnaissance\nNghiên cứu tài liệu EC-Council Module 02 đính kèm.",
            position=2,
            estimated_duration_minutes=55,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=19),
        )
        session.add(les_3_2)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c3.id,
            les_3_2.id,
            CYBER_DIR / "CEH Bundle" / "CEHv10 Module 02 Footprinting and Reconnaissance.pdf",
            "Tài liệu chính thức: CEHv10 Module 02 Footprinting and Reconnaissance",
            "CEHv10 Module 02",
            is_video=False,
            is_downloadable=True,
        )

        les_3_3 = Lesson(
            course_id=c3.id,
            learning_unit_id=u3_1.id,
            title="Bài 3: Scanning Networks & Dò quét Cổng Chuyên sâu",
            summary="Kỹ thuật quét mạng, phát hiện hệ điều hành và vượt tường lửa.",
            markdown_content="# Scanning Networks\nNghiên cứu tài liệu EC-Council Module 03 đính kèm.",
            position=3,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=18),
        )
        session.add(les_3_3)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c3.id,
            les_3_3.id,
            CYBER_DIR / "CEH Bundle" / "CEHv10 Module 03 Scanning Networks.pdf",
            "Tài liệu chính thức: CEHv10 Module 03 Scanning Networks",
            "CEHv10 Module 03",
            is_video=False,
            is_downloadable=True,
        )

        u3_2 = LearningUnit(
            course_id=c3.id,
            title="Chương 2: Liệt kê Dịch vụ & Phân tích Lỗ hổng",
            position=2,
            created_at=now - timedelta(days=17),
        )
        session.add(u3_2)
        session.flush()

        les_3_4 = Lesson(
            course_id=c3.id,
            learning_unit_id=u3_2.id,
            title="Bài 4: Enumeration & Liệt kê Dịch vụ Mạng",
            summary="Khai thác thông tin chi tiết qua giao thức NetBIOS, SNMP, LDAP và NTP.",
            markdown_content="# Enumeration\nNghiên cứu tài liệu EC-Council Module 04 đính kèm.",
            position=4,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=17),
        )
        session.add(les_3_4)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c3.id,
            les_3_4.id,
            CYBER_DIR / "CEH Bundle" / "CEHv10 Module 04 Enumeration.pdf",
            "Tài liệu chính thức: CEHv10 Module 04 Enumeration",
            "CEHv10 Module 04",
            is_video=False,
            is_downloadable=True,
        )

        les_3_5 = Lesson(
            course_id=c3.id,
            learning_unit_id=u3_2.id,
            title="Bài 5: Vulnerability Analysis & Quản lý Điểm yếu",
            summary="Đánh giá điểm yếu an ninh mạng theo chuẩn điểm CVSS.",
            markdown_content="# Vulnerability Analysis\nNghiên cứu tài liệu EC-Council Module 05 đính kèm.",
            position=5,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=16),
        )
        session.add(les_3_5)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c3.id,
            les_3_5.id,
            CYBER_DIR / "CEH Bundle" / "CEHv10 Module 05 Vulnerability Analysis.pdf",
            "Tài liệu chính thức: CEHv10 Module 05 Vulnerability Analysis",
            "CEHv10 Module 05",
            is_video=False,
            is_downloadable=True,
        )

        asm3 = Assessment(
            course_id=c3.id,
            title="Kỳ thi Đánh giá Chứng chỉ CEH v10 Practice Exam",
            description="Bài thi tổng hợp kiến thức CEH v10.",
            assessment_type="FINAL",
            status="PUBLISHED",
            time_limit_minutes=60,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("70.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=10),
        )
        session.add(asm3)
        session.flush()
        sec3 = AssessmentSection(
            assessment_id=asm3.id,
            title="Phần 1: Trắc nghiệm CEH v10",
            position=1,
            instructions="Chọn đáp án đúng nhất.",
        )
        session.add(sec3)
        session.flush()
        add_question_to_assessment(
            session,
            c3.id,
            les_3_1.id,
            inst1.id,
            asm3.id,
            sec3.id,
            1,
            "Mục tiêu quan trọng nhất của giai đoạn Footprinting trong quy trình Ethical Hacking là gì?",
            "SINGLE_CHOICE",
            [
                ("Thu thập thông tin mục tiêu càng nhiều càng tốt trước khi tấn công", True),
                ("Làm sập dịch vụ máy chủ", False),
                ("Chỉnh sửa cơ sở dữ liệu", False),
                ("Cài đặt mã độc Ransomware", False),
            ],
            "Footprinting là giai đoạn trinh sát thu thập hồ sơ mục tiêu.",
            decimal.Decimal("50.00"),
        )
        add_question_to_assessment(
            session,
            c3.id,
            les_3_3.id,
            inst1.id,
            asm3.id,
            sec3.id,
            2,
            "Lệnh Nmap nào thực hiện kỹ thuật quét SYN Scan (Stealth Scan) mà không hoàn tất bắt tay 3 bước TCP?",
            "SINGLE_CHOICE",
            [
                ("nmap -sS <target>", True),
                ("nmap -sT <target>", False),
                ("nmap -sU <target>", False),
                ("nmap -sP <target>", False),
            ],
            "Tùy chọn -sS gửi cờ SYN và không gửi ACK để tránh ghi log đầy đủ trên máy chủ.",
            decimal.Decimal("50.00"),
        )

        # =========================================================================
        # 4. COURSE 4: BLU301 (Blue Team Operations & Incident Response)
        # =========================================================================
        logger.info("Seeding Course 4: BLU301...")
        c4_slo = [
            {
                "title": "SLO-1: Giám sát SOC & Truy vấn Splunk SIEM",
                "description": "Sử dụng Splunk Search Processing Language (SPL) để săn lùng bất thường.",
                "weight": "50%",
            },
            {
                "title": "SLO-2: Ứng phó Sự cố An ninh Mạng",
                "description": "Vận hành quy trình ứng phó theo Cyber Kill Chain và MITRE ATT&CK.",
                "weight": "50%",
            },
        ]

        c4 = create_course_with_cover(
            session=session,
            actor=inst2,
            course_code="BLU301",
            title="Phòng thủ An ninh Mạng (Blue Team Operations) & Điều tra Sự cố",
            description="Đào tạo kỹ năng vận hành trung tâm giám sát an ninh SOC, phân tích nhật ký SIEM Splunk và xây dựng kịch bản ứng phó sự cố tấn công mạng.",
            category="Blue Team",
            difficulty="ADVANCED",
            slo=c4_slo,
            target=["Chuyên viên SOC Analyst L1/L2", "Kỹ sư Phòng thủ An ninh Mạng"],
            bg_gradient=((20, 50, 110), (15, 20, 35)),
            enrollment_count=2,
            passing_grade=75.0,
        )

        u4_1 = LearningUnit(
            course_id=c4.id,
            title="Chương 1: Giám sát SOC & Phân tích Splunk SIEM",
            position=1,
            created_at=now - timedelta(days=20),
        )
        session.add(u4_1)
        session.flush()

        les_4_1 = Lesson(
            course_id=c4.id,
            learning_unit_id=u4_1.id,
            title="Bài 1: Tổng quan Kiến trúc SOC & Bắt gói tin Mạng",
            summary="Tìm hiểu mô hình SOC hiện đại và phân tích luồng dữ liệu bằng Network Sniffer.",
            markdown_content="# Giám sát SOC & Network Sniffing\nĐọc tài liệu Basic Network Sniffer đính kèm.",
            position=1,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=20),
        )
        session.add(les_4_1)
        session.flush()
        attach_file_safely(
            session,
            inst2,
            c4.id,
            les_4_1.id,
            CYBER_DIR / "BlueTeam Kit" / "Basic Network Sniffer.pdf",
            "Tài liệu kỹ thuật: Basic Network Sniffer",
            "Basic Network Sniffer Guide",
            is_video=False,
            is_downloadable=True,
        )

        les_4_2 = Lesson(
            course_id=c4.id,
            learning_unit_id=u4_1.id,
            title="Bài 2: Làm chủ Splunk: 100+ Câu truy vấn cho SOC Analyst",
            summary="Tổng hợp hơn 100 câu lệnh SPL truy vấn phát hiện hành vi tấn công mạng trên Splunk SIEM.",
            markdown_content="# Splunk Queries for SOC Analyst\nNghiên cứu tài liệu chuyên khảo 100+ Splunk Queries đính kèm.",
            position=2,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=19),
        )
        session.add(les_4_2)
        session.flush()
        attach_file_safely(
            session,
            inst2,
            c4.id,
            les_4_2.id,
            CYBER_DIR / "BlueTeam Kit" / "100+ Splunk Queries for SOC Analyst.pdf",
            "Cẩm nang tra cứu: 100+ Splunk Queries for SOC Analyst",
            "100+ Splunk Queries",
            is_video=False,
            is_downloadable=True,
        )

        u4_2 = LearningUnit(
            course_id=c4.id,
            title="Chương 2: Ứng phó Sự cố & Kịch bản Tấn công Thực tế",
            position=2,
            created_at=now - timedelta(days=18),
        )
        session.add(u4_2)
        session.flush()

        les_4_3 = Lesson(
            course_id=c4.id,
            learning_unit_id=u4_2.id,
            title="Bài 3: Sổ tay Ứng phó Tấn công Mạng (Playbook 2025)",
            summary="Quy trình từng bước ứng phó các sự cố mã độc tống tiền, tấn công từ chối dịch vụ và đánh cắp thông tin.",
            markdown_content="# Cybersecurity Attacks Playbook\nNghiên cứu tài liệu Sổ tay kịch bản ứng phó sự cố an ninh mạng 2025.",
            position=3,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=18),
        )
        session.add(les_4_3)
        session.flush()
        attach_file_safely(
            session,
            inst2,
            c4.id,
            les_4_3.id,
            CYBER_DIR / "BlueTeam Kit" / "2025 Cybersecurity Attacks Playbook.pdf",
            "Sổ tay tác chiến: 2025 Cybersecurity Attacks Playbook",
            "Cybersecurity Attacks Playbook",
            is_video=False,
            is_downloadable=True,
        )

        asm4 = Assessment(
            course_id=c4.id,
            title="Kỳ thi Đánh giá Năng lực Blue Team & SOC Analyst Exam",
            description="Bài thi kiểm tra kiến thức giám sát và ứng phó sự cố.",
            assessment_type="FINAL",
            status="PUBLISHED",
            time_limit_minutes=45,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("70.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=10),
        )
        session.add(asm4)
        session.flush()
        sec4 = AssessmentSection(
            assessment_id=asm4.id,
            title="Phần 1: Trắc nghiệm Vận hành SOC",
            position=1,
            instructions="Chọn đáp án đúng nhất.",
        )
        session.add(sec4)
        session.flush()
        add_question_to_assessment(
            session,
            c4.id,
            les_4_2.id,
            inst2.id,
            asm4.id,
            sec4.id,
            1,
            "Thành phần SIEM (Security Information and Event Management) có vai trò cốt lõi nào trong trung tâm SOC?",
            "SINGLE_CHOICE",
            [
                ("Thu thập, chuẩn hóa và tương quan các log sự kiện an ninh từ nhiều nguồn", True),
                ("Tự động sửa chữa phần cứng máy chủ", False),
                ("Chặn quảng cáo trên trình duyệt", False),
                ("Tạo tài khoản người dùng tự động", False),
            ],
            "SIEM tập hợp và phân tích dữ liệu log từ tường lửa, máy chủ, ứng dụng để cảnh báo đe dọa.",
            decimal.Decimal("50.00"),
        )
        add_question_to_assessment(
            session,
            c4.id,
            les_4_3.id,
            inst2.id,
            asm4.id,
            sec4.id,
            2,
            "Bước đầu tiên theo tiêu chuẩn NIST SP 800-61 trong quy trình ứng phó sự cố an ninh mạng là gì?",
            "SINGLE_CHOICE",
            [
                ("Chuẩn bị (Preparation)", True),
                ("Phát hiện và Phân tích", False),
                ("Khoanh vùng, Xóa bỏ và Khắc phục", False),
                ("Học hỏi sau sự cố", False),
            ],
            "Giai đoạn Chuẩn bị là nền tảng để xây dựng chính sách, công cụ và kịch bản ứng phó sự cố.",
            decimal.Decimal("50.00"),
        )

        # =========================================================================
        # 5. COURSE 5: NET201 (Cloud Security, Networking & Infrastructure)
        # =========================================================================
        logger.info("Seeding Course 5: NET201...")
        c5 = create_course_with_cover(
            session=session,
            actor=inst2,
            course_code="NET201",
            title="An ninh Hạ tầng Mạng & Điện toán Đám mây (Cloud Security)",
            description="Thiết kế và bảo vệ hạ tầng mạng doanh nghiệp, cấu hình an ninh môi trường điện toán đám mây AWS/Azure và kiểm thử thâm nhập Cloud.",
            category="Cloud Security",
            difficulty="INTERMEDIATE",
            slo=[
                {
                    "title": "SLO-1: Kiến trúc Mạng & VPC",
                    "description": "Thiết kế VPC an toàn, phân vùng mạng và quản lý Security Group.",
                    "weight": "50%",
                },
                {
                    "title": "SLO-2: An ninh Điện toán Đám mây",
                    "description": "Kiểm thử IAM, S3 Bucket và bảo vệ workload đám mây.",
                    "weight": "50%",
                },
            ],
            target=["Kỹ sư Mạng", "Cloud Security Engineer"],
            bg_gradient=((15, 80, 80), (10, 20, 30)),
            enrollment_count=2,
            passing_grade=75.0,
        )

        u5_1 = LearningUnit(
            course_id=c5.id,
            title="Chương 1: An ninh Hạ tầng Đám mây & AWS Pentesting",
            position=1,
            created_at=now - timedelta(days=20),
        )
        session.add(u5_1)
        session.flush()

        les_5_1 = Lesson(
            course_id=c5.id,
            learning_unit_id=u5_1.id,
            title="Bài 1: Sổ tay An ninh Điện toán Đám mây (Cloud Security Handbook)",
            summary="Các nguyên lý bảo mật thiết yếu cho kiến trúc sư giải pháp đám mây.",
            markdown_content="# Cloud Security Handbook\nNghiên cứu tài liệu Cloud Security Handbook đính kèm.",
            position=1,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=20),
        )
        session.add(les_5_1)
        session.flush()
        attach_file_safely(
            session,
            inst2,
            c5.id,
            les_5_1.id,
            CYBER_DIR / "Cloud security & Networking" / "Cloud.Security.Handbook.pdf",
            "Sách chuyên khảo: Cloud Security Handbook",
            "Cloud Security Handbook",
            is_video=False,
            is_downloadable=True,
        )

        les_5_2 = Lesson(
            course_id=c5.id,
            learning_unit_id=u5_1.id,
            title="Bài 2: Hướng dẫn Pentest Môi trường AWS Cloud",
            summary="Thực hành kiểm thử xâm nhập hạ tầng AWS: IAM Misconfiguration và công khai S3 Bucket.",
            markdown_content="# AWS Cloud Pentest Guide\nNghiên cứu tài liệu AWS Pentest Guide đính kèm.",
            position=2,
            estimated_duration_minutes=55,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=19),
        )
        session.add(les_5_2)
        session.flush()
        attach_file_safely(
            session,
            inst2,
            c5.id,
            les_5_2.id,
            CYBER_DIR / "Cloud security & Networking" / "AWS Cloud Pentest Guide.pdf",
            "Cẩm nang thực hành: AWS Cloud Pentest Guide",
            "AWS Cloud Pentest Guide",
            is_video=False,
            is_downloadable=True,
        )

        asm5 = Assessment(
            course_id=c5.id,
            title="Kỳ thi Đánh giá Kỹ sư An ninh Đám mây (Cloud Security Exam)",
            description="Kiểm tra kiến thức bảo mật VPC và hạ tầng AWS/Azure.",
            assessment_type="FINAL",
            status="PUBLISHED",
            time_limit_minutes=45,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("70.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=10),
        )
        session.add(asm5)
        session.flush()
        sec5 = AssessmentSection(
            assessment_id=asm5.id,
            title="Phần 1: Trắc nghiệm Cloud Security",
            position=1,
            instructions="Chọn câu trả lời đúng.",
        )
        session.add(sec5)
        session.flush()
        add_question_to_assessment(
            session,
            c5.id,
            les_5_1.id,
            inst2.id,
            asm5.id,
            sec5.id,
            1,
            "Mô hình Trách nhiệm Chung (Shared Responsibility Model) trong đám mây quy định khách hàng chịu trách nhiệm về phần nào?",
            "SINGLE_CHOICE",
            [
                ("Bảo mật dữ liệu, quản lý danh tính IAM và cấu hình hệ điều hành", True),
                ("Bảo vệ vật lý trung tâm dữ liệu", False),
                ("Bảo trì phần cứng máy chủ", False),
                ("Đường truyền cáp quang ngầm", False),
            ],
            "Nhà cung cấp đám mây bảo vệ hạ tầng, khách hàng chịu trách nhiệm bảo mật dữ liệu và cấu hình IAM.",
            decimal.Decimal("50.00"),
        )
        add_question_to_assessment(
            session,
            c5.id,
            les_5_2.id,
            inst2.id,
            asm5.id,
            sec5.id,
            2,
            "Lỗ hổng cấu hình nào trên AWS S3 thường dẫn đến rò rỉ dữ liệu nghiêm trọng nhất?",
            "SINGLE_CHOICE",
            [
                ("Cấp quyền truy cập công khai (Public Read/Write) cho All Users", True),
                ("Bật tính năng Versioning", False),
                ("Kích hoạt mã hóa AES-256", False),
                ("Bật tính năng ghi log truy cập", False),
            ],
            "Bucket bị public quyền cho phép bất kỳ ai trên internet tải xuống toàn bộ dữ liệu.",
            decimal.Decimal("50.00"),
        )

        # =========================================================================
        # 6. COURSE 6: CRY201 (Cryptography & Data Protection)
        # =========================================================================
        logger.info("Seeding Course 6: CRY201...")
        c6 = create_course_with_cover(
            session=session,
            actor=inst2,
            course_code="CRY201",
            title="Mật mã học Ứng dụng & An toàn Dữ liệu (Cryptography)",
            description="Tìm hiểu sâu về các hệ mã đối xứng, mã công khai, hàm băm mật mã học, chữ ký số và giao thức an toàn TLS/SSL.",
            category="Cryptography",
            difficulty="INTERMEDIATE",
            slo=[
                {
                    "title": "SLO-1: Hệ mã Đối xứng & Bất đối xứng",
                    "description": "Làm chủ AES, RSA, ECC và Diffie-Hellman.",
                    "weight": "50%",
                },
                {
                    "title": "SLO-2: Hàm băm & Chữ ký số",
                    "description": "Nguyên lý SHA-256, HMAC và chứng chỉ X.509.",
                    "weight": "50%",
                },
            ],
            target=["Kỹ sư Phát triển Phần mềm", "Chuyên viên An toàn Dữ liệu"],
            bg_gradient=((80, 20, 100), (20, 10, 30)),
            enrollment_count=2,
            passing_grade=75.0,
        )

        u6_1 = LearningUnit(
            course_id=c6.id,
            title="Chương 1: Các Hệ Mật mã Cốt lõi & Ứng dụng",
            position=1,
            created_at=now - timedelta(days=20),
        )
        session.add(u6_1)
        session.flush()

        les_6_1 = Lesson(
            course_id=c6.id,
            learning_unit_id=u6_1.id,
            title="Bài 1: Nhập môn Mật mã học Toàn diện (Intro to Crypto)",
            summary="Khái niệm cơ bản về bảo vệ tính bảo mật, toàn vẹn và xác thực thông điệp.",
            markdown_content="# Intro to Cryptography\nNghiên cứu tài liệu IntroToCrypto đính kèm.",
            position=1,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=20),
        )
        session.add(les_6_1)
        session.flush()
        attach_file_safely(
            session,
            inst2,
            c6.id,
            les_6_1.id,
            CYBER_DIR / "Cryptography" / "IntroToCrypto.pdf",
            "Giáo trình: Intro to Cryptography",
            "Intro to Crypto",
            is_video=False,
            is_downloadable=True,
        )

        les_6_2 = Lesson(
            course_id=c6.id,
            learning_unit_id=u6_1.id,
            title="Bài 2: Mật mã học Nâng cao: Serious Cryptography",
            summary="Nghiên cứu chuyên sâu về mã hóa khối AES, ciphersuites và các tấn công mật mã học.",
            markdown_content="# Serious Cryptography\nNghiên cứu sách chuyên khảo Serious Cryptography đính kèm.",
            position=2,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=19),
        )
        session.add(les_6_2)
        session.flush()
        attach_file_safely(
            session,
            inst2,
            c6.id,
            les_6_2.id,
            CYBER_DIR / "Cryptography" / "Serious.Cryptography.2nd.Edition.pdf",
            "Sách chuyên khảo: Serious Cryptography (2nd Edition)",
            "Serious Cryptography 2nd Edition",
            is_video=False,
            is_downloadable=True,
        )

        asm6 = Assessment(
            course_id=c6.id,
            title="Bài thi Đánh giá Năng lực Mật mã học Ứng dụng",
            description="Đánh giá kiến thức về thuật toán mã hóa và chữ ký số.",
            assessment_type="FINAL",
            status="PUBLISHED",
            time_limit_minutes=45,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("70.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=10),
        )
        session.add(asm6)
        session.flush()
        sec6 = AssessmentSection(
            assessment_id=asm6.id,
            title="Phần 1: Trắc nghiệm Mật mã học",
            position=1,
            instructions="Chọn đáp án chính xác.",
        )
        session.add(sec6)
        session.flush()
        add_question_to_assessment(
            session,
            c6.id,
            les_6_1.id,
            inst2.id,
            asm6.id,
            sec6.id,
            1,
            "Thuật toán nào sau đây thuộc nhóm mã hóa đối xứng (Symmetric Encryption)?",
            "SINGLE_CHOICE",
            [
                ("AES (Advanced Encryption Standard)", True),
                ("RSA", False),
                ("ECC", False),
                ("Diffie-Hellman", False),
            ],
            "AES sử dụng cùng một khóa bí mật cho cả quá trình mã hóa và giải mã.",
            decimal.Decimal("50.00"),
        )
        add_question_to_assessment(
            session,
            c6.id,
            les_6_2.id,
            inst2.id,
            asm6.id,
            sec6.id,
            2,
            "Hàm băm mật mã học (Cryptographic Hash Function) có đặc tính quan trọng nào sau đây?",
            "SINGLE_CHOICE",
            [
                ("Tính chất một chiều (One-way) và chống đụng độ (Collision Resistance)", True),
                ("Có thể giải mã ngược lại văn bản gốc dễ dàng", False),
                ("Kích thước đầu ra thay đổi tùy ý theo đầu vào", False),
                ("Cần khóa bí mật để tính toán", False),
            ],
            "Hàm băm tạo chuỗi cố định không thể đảo ngược và cực kỳ khó tìm ra 2 đầu vào có cùng giá trị băm.",
            decimal.Decimal("50.00"),
        )

        # =========================================================================
        # 7. COURSE 7: DEV301 (DevSecOps: Security in CI/CD & Cloud Native)
        # =========================================================================
        logger.info("Seeding Course 7: DEV301...")
        c7 = create_course_with_cover(
            session=session,
            actor=inst2,
            course_code="DEV301",
            title="DevSecOps: Tích hợp An ninh trong CI/CD Pipeline & Cloud Native",
            description="Tích hợp kiểm tra an ninh tự động SAST, DAST, SCA vào đường ống tích hợp liên tục CI/CD và bảo mật container Docker/Kubernetes.",
            category="DevSecOps",
            difficulty="ADVANCED",
            slo=[
                {
                    "title": "SLO-1: Pipeline CI/CD An toàn",
                    "description": "Tích hợp công cụ quét mã nguồn tĩnh và phụ thuộc tự động.",
                    "weight": "50%",
                },
                {
                    "title": "SLO-2: An ninh Container & Docker",
                    "description": "Bảo vệ container image và giám sát runtime an toàn.",
                    "weight": "50%",
                },
            ],
            target=["DevOps Engineer", "Software Developer", "Security Champion"],
            bg_gradient=((20, 80, 40), (10, 25, 15)),
            enrollment_count=2,
            passing_grade=75.0,
        )

        u7_1 = LearningUnit(
            course_id=c7.id,
            title="Chương 1: Công cụ & Hoạt động Thực chiến DevSecOps",
            position=1,
            created_at=now - timedelta(days=20),
        )
        session.add(u7_1)
        session.flush()

        les_7_1 = Lesson(
            course_id=c7.id,
            learning_unit_id=u7_1.id,
            title="Bài 1: Cẩm nang Hoạt động DevSecOps (Tools & Activities Guide)",
            summary="Lộ trình tích hợp các hoạt động bảo mật vào từng giai đoạn của vòng đời SDLC.",
            markdown_content="# DevSecOps Activities Guide\nNghiên cứu cẩm nang hoạt động DevSecOps đính kèm.",
            position=1,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=20),
        )
        session.add(les_7_1)
        session.flush()
        attach_file_safely(
            session,
            inst2,
            c7.id,
            les_7_1.id,
            CYBER_DIR / "DevSecop" / "DevSecOpsTools-Activities_Guide_book_2021.pdf",
            "Cẩm nang hướng dẫn: DevSecOps Tools & Activities Guide",
            "DevSecOps Tools Activities Guide",
            is_video=False,
            is_downloadable=True,
        )

        les_7_2 = Lesson(
            course_id=c7.id,
            learning_unit_id=u7_1.id,
            title="Bài 2: An ninh Container Docker & Giám sát Môi trường Chạy",
            summary="Kỹ thuật quét lỗ hổng image Docker và thiết lập hạn chế quyền cho container.",
            markdown_content="# Docker Container Security\nNghiên cứu tài liệu bảo mật Docker đính kèm.",
            position=2,
            estimated_duration_minutes=55,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=19),
        )
        session.add(les_7_2)
        session.flush()
        attach_file_safely(
            session,
            inst2,
            c7.id,
            les_7_2.id,
            CYBER_DIR
            / "DevSecop"
            / "DevOps_and_Containers_Security_Security_and_Monitoring_in_Docker.pdf",
            "Tài liệu kỹ thuật: Security & Monitoring in Docker",
            "Docker Security Monitoring",
            is_video=False,
            is_downloadable=True,
        )

        asm7 = Assessment(
            course_id=c7.id,
            title="Kỳ thi Thực hành DevSecOps Practitioner Exam",
            description="Kiểm tra năng lực tích hợp an ninh vào quy trình phát triển phần mềm.",
            assessment_type="FINAL",
            status="PUBLISHED",
            time_limit_minutes=45,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("70.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=10),
        )
        session.add(asm7)
        session.flush()
        sec7 = AssessmentSection(
            assessment_id=asm7.id,
            title="Phần 1: Trắc nghiệm DevSecOps",
            position=1,
            instructions="Chọn đáp án chính xác.",
        )
        session.add(sec7)
        session.flush()
        add_question_to_assessment(
            session,
            c7.id,
            les_7_1.id,
            inst2.id,
            asm7.id,
            sec7.id,
            1,
            "Thuật ngữ 'Shift-Left' trong văn hóa DevSecOps mang ý nghĩa cốt lõi nào?",
            "SINGLE_CHOICE",
            [
                (
                    "Đưa các bước kiểm tra an ninh vào giai đoạn sớm nhất có thể trong vòng đời phát triển",
                    True,
                ),
                ("Bỏ qua khâu kiểm thử mã nguồn", False),
                ("Chỉ kiểm tra an ninh sau khi đã release lên production", False),
                ("Chuyển trách nhiệm bảo mật hoàn toàn cho đội vận hành", False),
            ],
            "Shift-Left giúp phát hiện và khắc phục lỗ hổng ngay từ khi viết mã, tiết kiệm tối đa chi phí.",
            decimal.Decimal("50.00"),
        )
        add_question_to_assessment(
            session,
            c7.id,
            les_7_2.id,
            inst2.id,
            asm7.id,
            sec7.id,
            2,
            "Thực hành bảo mật nào sau đây là bắt buộc khi viết Dockerfile cho môi trường production?",
            "SINGLE_CHOICE",
            [
                ("Không chạy container dưới quyền user root (dùng chỉ thị USER)", True),
                ("Cấp full quyền --privileged cho mọi container", False),
                ("Lưu trữ cứng mật khẩu database trong Dockerfile", False),
                ("Tắt tính năng quét mã độc trong base image", False),
            ],
            "Chạy container dưới quyền user thông thường ngăn chặn kẻ tấn công thoát khỏi container (container escape).",
            decimal.Decimal("50.00"),
        )

        # =========================================================================
        # 8. COURSE 8: KAL101 (Kali Linux Penetration Testing Toolkit Mastery)
        # =========================================================================
        logger.info("Seeding Course 8: KAL101...")
        c8 = create_course_with_cover(
            session=session,
            actor=inst1,
            course_code="KAL101",
            title="Làm chủ Bộ công cụ Kiểm thử Xâm nhập Kali Linux",
            description="Thành thạo hệ điều hành kiểm thử xâm nhập chuyên dụng Kali Linux và bộ công cụ hàng đầu: Metasploit, Nmap, Wireshark, John the Ripper.",
            category="Penetration Testing",
            difficulty="BEGINNER",
            slo=[
                {
                    "title": "SLO-1: Khung Khai thác Metasploit",
                    "description": "Lựa chọn exploit, payload và leo thang đặc quyền.",
                    "weight": "50%",
                },
                {
                    "title": "SLO-2: Tấn công Bẻ khóa Mật khẩu",
                    "description": "Sử dụng John the Ripper và Hashcat dò quét hash.",
                    "weight": "50%",
                },
            ],
            target=["Người mới bắt đầu học Hacking", "Sinh viên chuyên ngành An toàn Thông tin"],
            bg_gradient=((100, 20, 20), (20, 10, 15)),
            enrollment_count=2,
            passing_grade=75.0,
        )

        u8_1 = LearningUnit(
            course_id=c8.id,
            title="Chương 1: Làm chủ Môi trường Kali Linux",
            position=1,
            created_at=now - timedelta(days=20),
        )
        session.add(u8_1)
        session.flush()

        les_8_1 = Lesson(
            course_id=c8.id,
            learning_unit_id=u8_1.id,
            title="Bài 1: Hướng dẫn Sử dụng Kali Linux Thực chiến",
            summary="Làm quen với các lệnh dòng lệnh cơ bản và công cụ pentest tích hợp sẵn.",
            markdown_content="# Hacking with Kali Linux\nNghiên cứu tài liệu Hacking with Kali Linux đính kèm.",
            position=1,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=20),
        )
        session.add(les_8_1)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c8.id,
            les_8_1.id,
            CYBER_DIR / "Kali Linux" / "Hacking.with.Kali.Linux.pdf",
            "Giáo trình: Hacking with Kali Linux",
            "Hacking with Kali Linux",
            is_video=False,
            is_downloadable=True,
        )

        les_8_2 = Lesson(
            course_id=c8.id,
            learning_unit_id=u8_1.id,
            title="Bài 2: Kali Linux dành cho Chuyên gia Hacker Mũ trắng",
            summary="Các kỹ thuật xâm nhập nâng cao và phương pháp né tránh hệ thống phòng thủ.",
            markdown_content="# Kali Linux for Ethical Hackers\nNghiên cứu tài liệu chuyên khảo Kali Linux for Ethical Hackers.",
            position=2,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=19),
        )
        session.add(les_8_2)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c8.id,
            les_8_2.id,
            CYBER_DIR / "Kali Linux" / "Kali Linux For Ethical Hackers.pdf",
            "Sách chuyên khảo: Kali Linux For Ethical Hackers",
            "Kali Linux For Ethical Hackers",
            is_video=False,
            is_downloadable=True,
        )

        asm8 = Assessment(
            course_id=c8.id,
            title="Bài thi Đánh giá Kỹ năng Vận hành Kali Linux Pentester",
            description="Kiểm tra kỹ năng sử dụng công cụ kiểm thử trên Kali Linux.",
            assessment_type="FINAL",
            status="PUBLISHED",
            time_limit_minutes=45,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("70.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=10),
        )
        session.add(asm8)
        session.flush()
        sec8 = AssessmentSection(
            assessment_id=asm8.id,
            title="Phần 1: Trắc nghiệm Kali Linux",
            position=1,
            instructions="Chọn đáp án đúng.",
        )
        session.add(sec8)
        session.flush()
        add_question_to_assessment(
            session,
            c8.id,
            les_8_1.id,
            inst1.id,
            asm8.id,
            sec8.id,
            1,
            "Module nào trong Metasploit Framework được thiết kế để mở rộng quyền truy cập và thu thập thông tin sau khi đã xâm nhập thành công?",
            "SINGLE_CHOICE",
            [
                ("Post-exploitation modules (post/)", True),
                ("Auxiliary modules (auxiliary/)", False),
                ("Payload modules (payloads/)", False),
                ("Encoder modules (encoders/)", False),
            ],
            "Module 'post/' được dùng cho các thao tác sau xâm nhập như trích xuất hash mật khẩu, dò mạng nội bộ.",
            decimal.Decimal("50.00"),
        )
        add_question_to_assessment(
            session,
            c8.id,
            les_8_2.id,
            inst1.id,
            asm8.id,
            sec8.id,
            2,
            "Công cụ nào trên Kali Linux chuyên dùng để bẻ khóa mật khẩu offline thông qua GPU tốc độ cao?",
            "SINGLE_CHOICE",
            [("Hashcat", True), ("Nmap", False), ("Wireshark", False), ("Burp Suite", False)],
            "Hashcat là công cụ bẻ khóa hash mật khẩu hỗ trợ tăng tốc phần cứng GPU hàng đầu.",
            decimal.Decimal("50.00"),
        )

        # =========================================================================
        # 9. COURSE 9: THI301 (Threat Intelligence & Dark Web Investigations)
        # =========================================================================
        logger.info("Seeding Course 9: THI301...")
        c9 = create_course_with_cover(
            session=session,
            actor=inst2,
            course_code="THI301",
            title="Tình báo Mối đe dọa (Threat Intelligence) & Dark Web Investigations",
            description="Phương pháp luận điều tra tội phạm mạng trên Dark Web, kỹ thuật định tuyến Tor Onion và thu thập chỉ số đe dọa an ninh mạng IoC.",
            category="Threat Intelligence",
            difficulty="ADVANCED",
            slo=[
                {
                    "title": "SLO-1: Điều tra Mạng Tor & Dark Web",
                    "description": "Nắm vững cơ chế ẩn danh, an toàn điều tra và truy vết thông tin.",
                    "weight": "50%",
                },
                {
                    "title": "SLO-2: Tình báo Mối đe dọa (CTI)",
                    "description": "Phân tích chiến thuật nhóm APT theo khung MITRE ATT&CK.",
                    "weight": "50%",
                },
            ],
            target=[
                "Chuyên viên Phân tích Tình báo Mạng (CTI Analyst)",
                "Cán bộ Điều tra Số Forensics",
            ],
            bg_gradient=((40, 10, 60), (10, 5, 20)),
            enrollment_count=2,
            passing_grade=75.0,
        )

        u9_1 = LearningUnit(
            course_id=c9.id,
            title="Chương 1: Điều tra & Khám phá Thế giới Dark Web",
            position=1,
            created_at=now - timedelta(days=20),
        )
        session.add(u9_1)
        session.flush()

        les_9_1 = Lesson(
            course_id=c9.id,
            learning_unit_id=u9_1.id,
            title="Bài 1: Khám phá Dark Web trong 10 Phút",
            summary="Cơ chế hoạt động của mạng Tor, dịch vụ ẩn .onion và quy tắc an toàn bảo vệ danh tính.",
            markdown_content="# Dark Web in Ten Minutes\nNghiên cứu tài liệu tổng quan Dark Web đính kèm.",
            position=1,
            estimated_duration_minutes=45,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=20),
        )
        session.add(les_9_1)
        session.flush()
        attach_file_safely(
            session,
            inst2,
            c9.id,
            les_9_1.id,
            CYBER_DIR / "Dark Web Courses" / "Dark Web in ten minutes (1).pdf",
            "Tài liệu cơ bản: Dark Web in Ten Minutes",
            "Dark Web in Ten Minutes",
            is_video=False,
            is_downloadable=True,
        )

        les_9_2 = Lesson(
            course_id=c9.id,
            learning_unit_id=u9_1.id,
            title="Bài 2: Phương pháp luận Điều tra trên Dark Web (DarkWeb Investigation)",
            summary="Kỹ thuật thu thập bằng chứng kỹ thuật số và truy vết dấu vết tiền điện tử.",
            markdown_content="# DarkWeb Investigation\nNghiên cứu tài liệu điều tra Dark Web chuyên sâu đính kèm.",
            position=2,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=19),
        )
        session.add(les_9_2)
        session.flush()
        attach_file_safely(
            session,
            inst2,
            c9.id,
            les_9_2.id,
            CYBER_DIR / "Dark Web Courses" / "DarkWeb Investigation.pdf",
            "Cẩm nang điều tra: DarkWeb Investigation",
            "DarkWeb Investigation",
            is_video=False,
            is_downloadable=True,
        )

        asm9 = Assessment(
            course_id=c9.id,
            title="Kỳ thi Đánh giá Năng lực Chuyên viên Tình báo An ninh Mạng",
            description="Kiểm tra kiến thức thu thập tình báo và điều tra mối đe dọa.",
            assessment_type="FINAL",
            status="PUBLISHED",
            time_limit_minutes=45,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("70.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=10),
        )
        session.add(asm9)
        session.flush()
        sec9 = AssessmentSection(
            assessment_id=asm9.id,
            title="Phần 1: Trắc nghiệm Tình báo An ninh",
            position=1,
            instructions="Chọn đáp án đúng nhất.",
        )
        session.add(sec9)
        session.flush()
        add_question_to_assessment(
            session,
            c9.id,
            les_9_1.id,
            inst2.id,
            asm9.id,
            sec9.id,
            1,
            "Mạng Tor sử dụng kỹ thuật nào để đảm bảo tính ẩn danh cho gói tin truyền qua mạng?",
            "SINGLE_CHOICE",
            [
                ("Định tuyến nhiều lớp mã hóa qua các nút trung gian (Onion Routing)", True),
                ("Gửi dữ liệu trực tiếp không qua mã hóa", False),
                ("Lưu trữ địa chỉ IP thực tế của client tại tất cả các node", False),
                ("Chặn toàn bộ mã nguồn website", False),
            ],
            "Onion Routing mã hóa gói tin thành nhiều lớp giống vỏ củ hành, mỗi node trung gian chỉ gỡ được 1 lớp.",
            decimal.Decimal("50.00"),
        )
        add_question_to_assessment(
            session,
            c9.id,
            les_9_2.id,
            inst2.id,
            asm9.id,
            sec9.id,
            2,
            "Chỉ số Thỏa hiệp (IoC - Indicator of Compromise) thường bao gồm những yếu tố kỹ thuật nào?",
            "SINGLE_CHOICE",
            [
                ("Địa chỉ IP độc hại, tên miền C2, hash file mã độc", True),
                ("Tên thương hiệu công ty nạn nhân", False),
                ("Số tài khoản ngân hàng của nhân viên", False),
                ("Địa chỉ nhà riêng của lập trình viên", False),
            ],
            "IoC là dấu vết kỹ thuật số phản ánh máy tính đã bị xâm nhập.",
            decimal.Decimal("50.00"),
        )

        # =========================================================================
        # 10. COURSE 10: WIR201 (Wireless Security, Bluetooth & IoT Exploitation)
        # =========================================================================
        logger.info("Seeding Course 10: WIR201...")
        c10 = create_course_with_cover(
            session=session,
            actor=inst1,
            course_code="WIR201",
            title="An ninh Mạng Không dây, Bluetooth & Thiết bị IoT",
            description="Phân tích giao thức vô tuyến 802.11 Wi-Fi, kỹ thuật tấn công bẻ khóa WPA2/WPA3, khai thác lỗ hổng Bluetooth BLE và an toàn thiết bị IoT.",
            category="Wireless Security",
            difficulty="INTERMEDIATE",
            slo=[
                {
                    "title": "SLO-1: An ninh Mạng Wi-Fi 802.11",
                    "description": "Tấn công 4-way handshake và phòng ngừa Deauth.",
                    "weight": "50%",
                },
                {
                    "title": "SLO-2: Lỗ hổng Bluetooth BLE & IoT",
                    "description": "Đánh giá an toàn thiết bị kết nối không dây.",
                    "weight": "50%",
                },
            ],
            target=["Kỹ sư Mạng Không dây", "Chuyên viên Kiểm thử Thiết bị IoT"],
            bg_gradient=((10, 50, 70), (5, 20, 30)),
            enrollment_count=2,
            passing_grade=75.0,
        )

        u10_1 = LearningUnit(
            course_id=c10.id,
            title="Chương 1: An ninh Sóng Vô tuyến & Bluetooth",
            position=1,
            created_at=now - timedelta(days=20),
        )
        session.add(u10_1)
        session.flush()

        les_10_1 = Lesson(
            course_id=c10.id,
            learning_unit_id=u10_1.id,
            title="Bài 1: Khám phá An ninh Giao thức Bluetooth",
            summary="Phân tích kiến trúc bảo mật Bluetooth, cơ chế ghép nối (Pairing) và lỗ hổng BLE.",
            markdown_content="# Bluetooth Security\nNghiên cứu tài liệu Bluetooth Security đính kèm.",
            position=1,
            estimated_duration_minutes=50,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=20),
        )
        session.add(les_10_1)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c10.id,
            les_10_1.id,
            CYBER_DIR / "Bluetooth Security" / "63. Bluetooth Security.pdf",
            "Tài liệu chuyên khảo: Bluetooth Security",
            "Bluetooth Security",
            is_video=False,
            is_downloadable=True,
        )

        les_10_2 = Lesson(
            course_id=c10.id,
            learning_unit_id=u10_1.id,
            title="Bài 2: Thiết kế Hệ thống Vô tuyến Số & Tấn công 802.11",
            summary="Nguyên lý truyền dẫn sóng vô tuyến số và kỹ thuật tấn công bẻ khóa mạng Wi-Fi.",
            markdown_content="# Digital Radio System Design\nNghiên cứu tài liệu Digital Radio System Design đính kèm.",
            position=2,
            estimated_duration_minutes=55,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            revision_no=1,
            status="PUBLISHED",
            published_at=now - timedelta(days=19),
        )
        session.add(les_10_2)
        session.flush()
        attach_file_safely(
            session,
            inst1,
            c10.id,
            les_10_2.id,
            CYBER_DIR
            / "Hacking wireless devices"
            / "Digital radio system design [Grigorios Kalivas] 2009.pdf",
            "Giáo trình kỹ thuật: Digital Radio System Design",
            "Digital Radio System Design",
            is_video=False,
            is_downloadable=True,
        )

        asm10 = Assessment(
            course_id=c10.id,
            title="Kỳ thi Đánh giá Chuyên viên An ninh Mạng Không dây",
            description="Kiểm tra kiến thức bảo mật mạng Wi-Fi và Bluetooth.",
            assessment_type="FINAL",
            status="PUBLISHED",
            time_limit_minutes=45,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("70.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=10),
        )
        session.add(asm10)
        session.flush()
        sec10 = AssessmentSection(
            assessment_id=asm10.id,
            title="Phần 1: Trắc nghiệm An ninh Mạng Không dây",
            position=1,
            instructions="Chọn đáp án đúng.",
        )
        session.add(sec10)
        session.flush()
        add_question_to_assessment(
            session,
            c10.id,
            les_10_1.id,
            inst1.id,
            asm10.id,
            sec10.id,
            1,
            "Cuộc tấn công bẻ khóa WPA2-PSK truyền thống dựa vào việc bắt giữ gói tin nào sau đây?",
            "SINGLE_CHOICE",
            [
                ("Gói tin bắt tay 4 bước (4-Way Handshake)", True),
                ("Gói tin ICMP Ping", False),
                ("Gói tin DNS Query", False),
                ("Gói tin DHCP Request", False),
            ],
            "Bắt giữ 4-way handshake cho phép pentester thực hiện tấn công từ điển (dictionary attack) offline.",
            decimal.Decimal("50.00"),
        )
        add_question_to_assessment(
            session,
            c10.id,
            les_10_2.id,
            inst1.id,
            asm10.id,
            sec10.id,
            2,
            "Giao thức WPA3 bổ sung cơ chế xác thực nào để ngăn chặn hoàn toàn tấn công từ điển offline?",
            "SINGLE_CHOICE",
            [
                ("Simultaneous Authentication of Equals (SAE)", True),
                ("WEP 64-bit", False),
                ("WPS PIN cơ bản", False),
                ("Telnet xác thực", False),
            ],
            "SAE loại bỏ khả năng bẻ khóa mật khẩu offline ngay cả khi bắt giữ được luồng dữ liệu bắt tay.",
            decimal.Decimal("50.00"),
        )

        # =========================================================================
        # ENROLLMENTS, PROGRESS & EXAM ATTEMPTS
        # =========================================================================
        logger.info("Setting up enrollments, progress, and assessment attempt histories...")

        # Student 1: High achiever
        e1_c1 = enroll_student(actor=student1, course_id=c1.id, session=session)
        enroll_student(actor=student1, course_id=c2.id, session=session)
        enroll_student(actor=student1, course_id=c3.id, session=session)

        # Student 2: Average achiever
        e2_c1 = enroll_student(actor=student2, course_id=c1.id, session=session)
        enroll_student(actor=student2, course_id=c4.id, session=session)

        # Student 3: Newcomer
        enroll_student(actor=student3, course_id=c1.id, session=session)
        enroll_student(actor=student3, course_id=c5.id, session=session)
        session.flush()

        # Student 1 completed lessons in Course 1 with progress
        if e1_c1.current_period_id:
            for l_obj in [les_1_1, les_1_2, les_1_3, les_1_4]:
                session.add(
                    LessonProgress(
                        enrollment_period_id=e1_c1.current_period_id,
                        lesson_id=l_obj.id,
                        seconds_spent=450,
                        max_view_fraction=decimal.Decimal("1.0000"),
                        completed_at=now - timedelta(days=2),
                        acknowledged_revision_no=1,
                        completion_rule_snapshot_json=json.dumps(
                            {"notes": "Hoàn thành xuất sắc bài học", "mini_quiz_passed": True}
                        ),
                    )
                )

            # Student 1 completed Assessment Attempt on Course 1 (Score: 100.00)
            attempt1 = AssessmentAttempt(
                assessment_id=asm1.id,
                enrollment_period_id=e1_c1.current_period_id,
                student_user_id=student1.id,
                attempt_number=1,
                status="GRADED",
                started_at=now - timedelta(hours=4),
                deadline_at=now - timedelta(hours=3),
                submitted_at=now - timedelta(hours=3, minutes=10),
                graded_at=now - timedelta(hours=3, minutes=9),
                finalized_at=now - timedelta(hours=3, minutes=9),
            )
            session.add(attempt1)
            session.flush()

            aq1 = AttemptQuestion(
                attempt_id=attempt1.id,
                source_question_id=q1_1.id,
                source_question_revision_id=q1_1.revisions[0].id,
                position=1,
                question_type_snapshot=q1_1.revisions[0].question_type,
                content_snapshot=q1_1.revisions[0].content,
                points_assigned=decimal.Decimal("50.0000"),
            )
            session.add(aq1)
            session.flush()
            snap1_choices = []
            for c_pos, choice in enumerate(q1_1.revisions[0].choices, start=1):
                snap = AttemptChoiceSnapshot(
                    attempt_question_id=aq1.id,
                    source_choice_id=choice.id,
                    choice_key_snapshot=choice.choice_key,
                    content_snapshot=choice.content,
                    position=c_pos,
                )
                session.add(snap)
                snap1_choices.append((choice, snap))
            session.flush()

            aq2 = AttemptQuestion(
                attempt_id=attempt1.id,
                source_question_id=q1_2.id,
                source_question_revision_id=q1_2.revisions[0].id,
                position=2,
                question_type_snapshot=q1_2.revisions[0].question_type,
                content_snapshot=q1_2.revisions[0].content,
                points_assigned=decimal.Decimal("50.0000"),
            )
            session.add(aq2)
            session.flush()
            snap2_choices = []
            for c_pos, choice in enumerate(q1_2.revisions[0].choices, start=1):
                snap = AttemptChoiceSnapshot(
                    attempt_question_id=aq2.id,
                    source_choice_id=choice.id,
                    choice_key_snapshot=choice.choice_key,
                    content_snapshot=choice.content,
                    position=c_pos,
                )
                session.add(snap)
                snap2_choices.append((choice, snap))
            session.flush()

            ans1 = AttemptAnswer(
                attempt_question_id=aq1.id,
                answer_version=1,
                last_client_sequence=1,
                saved_at=now - timedelta(hours=3, minutes=30),
            )
            session.add(ans1)
            session.flush()
            ans2 = AttemptAnswer(
                attempt_question_id=aq2.id,
                answer_version=1,
                last_client_sequence=1,
                saved_at=now - timedelta(hours=3, minutes=20),
            )
            session.add(ans2)
            session.flush()

            corr_snap1 = [snap for ch, snap in snap1_choices if ch.is_correct][0]
            corr_snap2 = [snap for ch, snap in snap2_choices if ch.is_correct][0]
            session.add(
                AttemptAnswerChoice(
                    attempt_answer_id=ans1.id, attempt_choice_snapshot_id=corr_snap1.id
                )
            )
            session.add(
                AttemptAnswerChoice(
                    attempt_answer_id=ans2.id, attempt_choice_snapshot_id=corr_snap2.id
                )
            )

            session.add(
                AttemptQuestionGrade(
                    attempt_question_id=aq1.id,
                    awarded_points=decimal.Decimal("50.0000"),
                    grading_status="AUTO_GRADED",
                    grading_rule="ORIGINAL",
                    graded_at=now - timedelta(hours=3, minutes=9),
                )
            )
            session.add(
                AttemptQuestionGrade(
                    attempt_question_id=aq2.id,
                    awarded_points=decimal.Decimal("50.0000"),
                    grading_status="AUTO_GRADED",
                    grading_rule="ORIGINAL",
                    graded_at=now - timedelta(hours=3, minutes=9),
                )
            )

            session.add(
                AssessmentResult(
                    attempt_id=attempt1.id,
                    raw_score=decimal.Decimal("100.0000"),
                    max_score=decimal.Decimal("100.0000"),
                    percent_score=decimal.Decimal("100.0000"),
                    passed=True,
                    status="FINAL",
                    graded_at=now - timedelta(hours=3, minutes=9),
                    released_at=now - timedelta(hours=3, minutes=9),
                )
            )

        # Student 2 completed Attempt on Course 1 (Score: 50.00)
        if e2_c1.current_period_id:
            attempt2 = AssessmentAttempt(
                assessment_id=asm1.id,
                enrollment_period_id=e2_c1.current_period_id,
                student_user_id=student2.id,
                attempt_number=1,
                status="GRADED",
                started_at=now - timedelta(hours=2),
                deadline_at=now - timedelta(hours=1),
                submitted_at=now - timedelta(hours=1, minutes=15),
                graded_at=now - timedelta(hours=1, minutes=14),
                finalized_at=now - timedelta(hours=1, minutes=14),
            )
            session.add(attempt2)
            session.flush()

            aq2_1 = AttemptQuestion(
                attempt_id=attempt2.id,
                source_question_id=q1_1.id,
                source_question_revision_id=q1_1.revisions[0].id,
                position=1,
                question_type_snapshot=q1_1.revisions[0].question_type,
                content_snapshot=q1_1.revisions[0].content,
                points_assigned=decimal.Decimal("50.0000"),
            )
            session.add(aq2_1)
            session.flush()
            snap2_1_choices = []
            for c_pos, choice in enumerate(q1_1.revisions[0].choices, start=1):
                snap = AttemptChoiceSnapshot(
                    attempt_question_id=aq2_1.id,
                    source_choice_id=choice.id,
                    choice_key_snapshot=choice.choice_key,
                    content_snapshot=choice.content,
                    position=c_pos,
                )
                session.add(snap)
                snap2_1_choices.append((choice, snap))
            session.flush()

            aq2_2 = AttemptQuestion(
                attempt_id=attempt2.id,
                source_question_id=q1_2.id,
                source_question_revision_id=q1_2.revisions[0].id,
                position=2,
                question_type_snapshot=q1_2.revisions[0].question_type,
                content_snapshot=q1_2.revisions[0].content,
                points_assigned=decimal.Decimal("50.0000"),
            )
            session.add(aq2_2)
            session.flush()
            snap2_2_choices = []
            for c_pos, choice in enumerate(q1_2.revisions[0].choices, start=1):
                snap = AttemptChoiceSnapshot(
                    attempt_question_id=aq2_2.id,
                    source_choice_id=choice.id,
                    choice_key_snapshot=choice.choice_key,
                    content_snapshot=choice.content,
                    position=c_pos,
                )
                session.add(snap)
                snap2_2_choices.append((choice, snap))
            session.flush()

            ans2_1 = AttemptAnswer(
                attempt_question_id=aq2_1.id,
                answer_version=1,
                last_client_sequence=1,
                saved_at=now - timedelta(hours=1, minutes=30),
            )
            session.add(ans2_1)
            session.flush()
            ans2_2 = AttemptAnswer(
                attempt_question_id=aq2_2.id,
                answer_version=1,
                last_client_sequence=1,
                saved_at=now - timedelta(hours=1, minutes=20),
            )
            session.add(ans2_2)
            session.flush()

            corr_snap2_1 = [snap for ch, snap in snap2_1_choices if ch.is_correct][0]
            incorr_snap2_2 = [snap for ch, snap in snap2_2_choices if not ch.is_correct][0]
            session.add(
                AttemptAnswerChoice(
                    attempt_answer_id=ans2_1.id, attempt_choice_snapshot_id=corr_snap2_1.id
                )
            )
            session.add(
                AttemptAnswerChoice(
                    attempt_answer_id=ans2_2.id, attempt_choice_snapshot_id=incorr_snap2_2.id
                )
            )

            session.add(
                AttemptQuestionGrade(
                    attempt_question_id=aq2_1.id,
                    awarded_points=decimal.Decimal("50.0000"),
                    grading_status="AUTO_GRADED",
                    grading_rule="ORIGINAL",
                    graded_at=now - timedelta(hours=1, minutes=14),
                )
            )
            session.add(
                AttemptQuestionGrade(
                    attempt_question_id=aq2_2.id,
                    awarded_points=decimal.Decimal("0.0000"),
                    grading_status="AUTO_GRADED",
                    grading_rule="ORIGINAL",
                    graded_at=now - timedelta(hours=1, minutes=14),
                )
            )

            session.add(
                AssessmentResult(
                    attempt_id=attempt2.id,
                    raw_score=decimal.Decimal("50.0000"),
                    max_score=decimal.Decimal("100.0000"),
                    percent_score=decimal.Decimal("50.0000"),
                    passed=False,
                    status="FINAL",
                    graded_at=now - timedelta(hours=1, minutes=14),
                    released_at=now - timedelta(hours=1, minutes=14),
                )
            )

        session.commit()
        logger.info("=========================================================================")
        logger.info("SEED COMPLETED SUCCESSFULLY!")
        logger.info("Total Courses Created: 10")
        logger.info(
            "Total Users Configured: 11 (1 Root Admin, 5 Sub-Admins, 2 Instructors, 3 Students)"
        )
        logger.info("All 24 MP4 Videos and PDFs from F:\\cyber\\khóa học all safely ingested!")
        logger.info("=========================================================================")


if __name__ == "__main__":
    seed_cyber_courses()
