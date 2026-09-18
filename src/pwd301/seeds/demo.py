"""Comprehensive Demonstration Dataset Seeding Engine for PWD301.

Creates realistic, fully relational demonstration data for platform showcase:
- 7 Accounts: 1 Admin, 2 Instructors, 4 Students (standard password: Password123!)
- 3 Courses:
    * CS101 (PUBLISHED): Active enrollments, lessons with rich Markdown & clean attachments.
    * CS201 (DRAFT): Authoring state, prerequisite linked to CS101 (no cycle).
    * CS301 (SUBMITTED_FOR_REVIEW): Pending administrator review.
- Question Bank: 5 question types (SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE,
  SHORT_ANSWER, ESSAY) tagged with Bloom taxonomy.
- Assessment: Midterm exam (PUBLISHED) with sections and assigned questions.
- Attempts & Grading:
    * student1: 100% completed & graded (auto-graded + instructor essay feedback).
    * student2: Submitted awaiting manual essay grading (demonstrates grading UI).
    * student3: Enrolled in progress.
    * student4: Unenrolled (clean account for live registration/enrollment demo).
- Sample in-app notifications and append-only audit events.
- 100% idempotent: Safe to execute repeatedly without duplicating records or failing.
"""

from __future__ import annotations

import decimal
import io
import json
import uuid
from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session, scoped_session
from werkzeug.security import generate_password_hash

from pwd301.models.assessment import (
    Assessment,
    AssessmentQuestionAssignment,
    AssessmentSection,
)
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AssessmentResult,
    AttemptAnswer,
    AttemptChoiceSnapshot,
    AttemptQuestion,
    AttemptQuestionGrade,
)
from pwd301.models.course import (
    Course,
    CourseCompletionRule,
    CourseCompletionSummary,
    CoursePrerequisite,
    Enrollment,
    EnrollmentPeriod,
    Lesson,
    LessonProgress,
)
from pwd301.models.file_import import LessonResource
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
from pwd301.seeds.baseline import seed_baseline

DEMO_PASSWORD: str = "Password123!"

DEMO_USERS_CONFIG: list[dict[str, Any]] = [
    {
        "email": "admin@pwd301.local",
        "display_name": "Quản trị viên Hệ thống",
        "roles": ["STUDENT", "INSTRUCTOR", "ADMIN"],
    },
    {
        "email": "instructor1@pwd301.local",
        "display_name": "TS. Nguyễn Văn A",
        "roles": ["STUDENT", "INSTRUCTOR"],
    },
    {
        "email": "instructor2@pwd301.local",
        "display_name": "ThS. Trần Thị B",
        "roles": ["STUDENT", "INSTRUCTOR"],
    },
    {
        "email": "student1@pwd301.local",
        "display_name": "Lê Hoàng Long",
        "roles": ["STUDENT"],
    },
    {
        "email": "student2@pwd301.local",
        "display_name": "Phạm Minh Tuấn",
        "roles": ["STUDENT"],
    },
    {
        "email": "student3@pwd301.local",
        "display_name": "Vũ Thảo Nguyên",
        "roles": ["STUDENT"],
    },
    {
        "email": "student4@pwd301.local",
        "display_name": "Đặng Gia Huy",
        "roles": ["STUDENT"],
    },
]


def seed_demo(session: Session | scoped_session[Any]) -> dict[str, Any]:
    """Execute complete demonstration data seeding."""
    summary: dict[str, Any] = {
        "users_created": [],
        "users_existing": [],
        "courses_created": [],
        "courses_existing": [],
        "lessons_created": [],
        "questions_created": [],
        "assessments_created": [],
        "enrollments_created": [],
        "attempts_created": [],
        "notifications_created": 0,
        "audit_events_created": 0,
    }

    # 1. Baseline initialization (Roles & Root Admin)
    seed_baseline(session)

    # Cache roles
    roles_by_code: dict[str, Role] = {r.code: r for r in session.query(Role).all()}

    # 2. Seed Demo Users
    users_by_email: dict[str, User] = {}
    hashed_pwd = generate_password_hash(DEMO_PASSWORD)
    now = utc_now()

    for u_cfg in DEMO_USERS_CONFIG:
        norm_email = u_cfg["email"].lower().strip()
        user = session.query(User).filter(User.email_normalized == norm_email).first()
        if user is None:
            user = User(
                email=norm_email,
                password_hash=hashed_pwd,
                display_name=u_cfg["display_name"],
                status="ACTIVE",
                auth_version=1,
                email_verified_at=now,
            )
            session.add(user)
            session.flush()
            summary["users_created"].append(norm_email)
        else:
            # Ensure password and verification are set for existing demo accounts
            user.password_hash = hashed_pwd
            user.email_verified_at = user.email_verified_at or now
            summary["users_existing"].append(norm_email)

        # Ensure role assignments
        for r_code in u_cfg["roles"]:
            r_obj = roles_by_code.get(r_code)
            if r_obj:
                existing_link = (
                    session.query(UserRole)
                    .filter(UserRole.user_id == user.id, UserRole.role_id == r_obj.id)
                    .first()
                )
                if not existing_link:
                    session.add(
                        UserRole(
                            user_id=user.id,
                            role_id=r_obj.id,
                            assigned_by_user_id=user.id,
                            assignment_reason="Demo environment initialization",
                        )
                    )

        users_by_email[norm_email] = user

    admin_user = users_by_email["admin@pwd301.local"]
    instructor1 = users_by_email["instructor1@pwd301.local"]
    instructor2 = users_by_email["instructor2@pwd301.local"]
    student1 = users_by_email["student1@pwd301.local"]
    student2 = users_by_email["student2@pwd301.local"]
    student3 = users_by_email["student3@pwd301.local"]
    student4 = users_by_email["student4@pwd301.local"]
    # student4 left unenrolled for live enrollment demo

    session.flush()

    # 3. Seed Demo Courses
    # Course 1: CS101 (PUBLISHED)
    course1 = session.query(Course).filter(Course.course_code == "CS101").first()
    if course1 is None:
        course1 = Course(
            course_code="CS101",
            course_code_normalized="CS101",
            title="CS101: Lập trình Python & Flask Web Nâng Cao",
            title_normalized="cs101: lập trình python & flask web nâng cao",
            description=(
                "Khóa học toàn diện về lập trình Python hiện đại, kiến trúc Flask REST API, "
                "kết nối cơ sở dữ liệu Microsoft SQL Server với SQLAlchemy ORM, bảo mật xác thực "
                "JWT và phân quyền đa cấp RBAC."
            ),
            category="Khoa học Máy tính",
            difficulty="INTERMEDIATE",
            owner_instructor_id=instructor1.id,
            status="PUBLISHED",
            capacity=50,
            published_at=now - timedelta(days=14),
            approved_at=now - timedelta(days=14),
            approved_by_user_id=admin_user.id,
        )
        session.add(course1)
        session.flush()
        summary["courses_created"].append("CS101")
    else:
        summary["courses_existing"].append("CS101")

    # Course 2: CS201 (DRAFT)
    course2 = session.query(Course).filter(Course.course_code == "CS201").first()
    if course2 is None:
        course2 = Course(
            course_code="CS201",
            course_code_normalized="CS201",
            title="CS201: Cấu trúc Dữ liệu, Giải thuật & Thiết kế Hệ thống",
            title_normalized="cs201: cấu trúc dữ liệu, giải thuật & thiết kế hệ thống",
            description=(
                "Nghiên cứu chuyên sâu về cấu trúc dữ liệu nâng cao, thuật toán tối ưu, "
                "mẫu thiết kế kiến trúc vi dịch vụ và xử lý tương tranh cao."
            ),
            category="Khoa học Máy tính",
            difficulty="ADVANCED",
            owner_instructor_id=instructor1.id,
            status="DRAFT",
            capacity=30,
        )
        session.add(course2)
        session.flush()
        summary["courses_created"].append("CS201")
    else:
        summary["courses_existing"].append("CS201")

    # Course 3: CS301 (SUBMITTED_FOR_REVIEW)
    course3 = session.query(Course).filter(Course.course_code == "CS301").first()
    if course3 is None:
        course3 = Course(
            course_code="CS301",
            course_code_normalized="CS301",
            title="CS301: Trí tuệ Nhân tạo & Xử lý Ngôn ngữ Tự nhiên RAG",
            title_normalized="cs301: trí tuệ nhân tạo & xử lý ngôn ngữ tự nhiên rag",
            description=(
                "Ứng dụng thực tiễn của Large Language Models (LLM), Vector Embeddings, "
                "và kiến trúc Retrieval-Augmented Generation (RAG) tích hợp Google Gemini API."
            ),
            category="Trí tuệ Nhân tạo",
            difficulty="ADVANCED",
            owner_instructor_id=instructor2.id,
            status="SUBMITTED_FOR_REVIEW",
            capacity=40,
        )
        session.add(course3)
        session.flush()
        summary["courses_created"].append("CS301")
    else:
        summary["courses_existing"].append("CS301")

    # 4. Prerequisite: CS201 requires CS101 (no cycle)
    prereq_link = (
        session.query(CoursePrerequisite)
        .filter(
            CoursePrerequisite.course_id == course2.id,
            CoursePrerequisite.prerequisite_course_id == course1.id,
        )
        .first()
    )
    if not prereq_link:
        session.add(
            CoursePrerequisite(
                course_id=course2.id,
                prerequisite_course_id=course1.id,
                created_by_user_id=instructor1.id,
            )
        )

    # 5. Course Completion Rules for CS101
    rule1 = (
        session.query(CourseCompletionRule)
        .filter(CourseCompletionRule.course_id == course1.id)
        .first()
    )
    if not rule1:
        session.add(
            CourseCompletionRule(
                course_id=course1.id,
                require_all_required_lessons=True,
                require_required_assessments=True,
                minimum_progress_percent=decimal.Decimal("80.00"),
                updated_by_user_id=instructor1.id,
            )
        )

    # 6. Lessons for CS101
    lesson1 = (
        session.query(Lesson).filter(Lesson.course_id == course1.id, Lesson.position == 1).first()
    )
    if not lesson1:
        lesson1 = Lesson(
            course_id=course1.id,
            title="Bài 1: Tổng quan về Kiến trúc Web & HTTP Protocol",
            summary=("Tìm hiểu nguyên lý Client-Server, HTTP methods, status codes và REST API."),
            position=1,
            estimated_duration_minutes=45,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=14),
            markdown_content="""# Kiến trúc Web Hiện Đại & Giao Thức HTTP

Chào mừng bạn đến với khóa học **CS101: Lập trình Python & Flask Web Nâng Cao**.

## 1. Mô hình Client-Server & Vòng đời Request-Response

Mọi ứng dụng web hiện đại đều vận hành trên nền tảng kiến trúc **Client-Server**:
1. **Client** (Trình duyệt, ứng dụng di động, API consumer) khởi tạo HTTP Request qua mạng Internet.
2. **Reverse Proxy** (Nginx / Cloudflare) tiếp nhận kết nối, hỗ trợ TLS termination và cân bằng tải.
3. **WSGI / Application Server** (Gunicorn) chuyển request vào ứng dụng Flask.
4. **Application Logic** xử lý nghiệp vụ, truy vấn CSDL và trả về HTTP Response.

## 2. Các HTTP Methods Tiêu Chuẩn (RFC 7231)

| HTTP Method | Mục đích | Safe? | Idempotent? |
|-------------|----------|-------|-------------|
| `GET`       | Đọc tài nguyên | Có | Có |
| `POST`      | Tạo mới tài nguyên | Không | Không |
| `PUT`       | Cập nhật toàn bộ tài nguyên | Không | Có |
| `PATCH`     | Cập nhật một phần tài nguyên | Không | Không |
| `DELETE`    | Xóa tài nguyên | Không | Có |

## 3. Mã trạng thái HTTP (HTTP Status Codes)
- **200 OK**: Request thành công.
- **201 Created**: Tạo mới tài nguyên thành công.
- **400 Bad Request**: Dữ liệu gửi lên không hợp lệ.
- **401 Unauthorized**: Chưa xác thực (thiếu JWT hoặc session token).
- **403 Forbidden**: Không đủ quyền truy cập tài nguyên (IDOR / RBAC).
- **404 Not Found**: Tài nguyên không tồn tại.
- **500 Internal Server Error**: Lỗi máy chủ nội bộ.
""",
        )
        session.add(lesson1)
        session.flush()
        summary["lessons_created"].append(lesson1.title)

    lesson2 = (
        session.query(Lesson).filter(Lesson.course_id == course1.id, Lesson.position == 2).first()
    )
    if not lesson2:
        lesson2 = Lesson(
            course_id=course1.id,
            title="Bài 2: Xây dựng REST API Chuẩn với Flask & SQLAlchemy",
            summary=("Thiết kế RESTful endpoints, Application Factory Pattern và SQLAlchemy ORM."),
            position=2,
            estimated_duration_minutes=60,
            minimum_completion_seconds=30,
            viewed_fraction_required=decimal.Decimal("0.8000"),
            status="PUBLISHED",
            published_at=now - timedelta(days=12),
            markdown_content="""# Xây Dựng REST API Chuẩn với Flask & SQLAlchemy

Trong bài học này, chúng ta sẽ tìm hiểu cách kiến trúc dự án Flask chuẩn doanh nghiệp.

## 1. Application Factory Pattern

Application Factory Pattern cho phép bạn khởi tạo ứng dụng Flask với nhiều
cấu hình môi trường khác nhau (`development`, `testing`, `production`):

```python
from flask import Flask
from pwd301.extensions import db, migrate

def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    # Nạp cấu hình theo môi trường
    ...
    # Khởi tạo extensions
    db.init_app(app)
    migrate.init_app(app, db)
    return app
```

## 2. SQLAlchemy ORM & Connection Pooling

Khi kết nối tới Microsoft SQL Server, SQLAlchemy tự động quản lý **Connection Pool**:
- Tái sử dụng socket connection, giảm thiểu độ trễ kết nối TCP/TLS.
- Ngăn chặn tình trạng cạn kiệt connection bằng giới hạn `pool_size` và `max_overflow`.
- Phải luôn đóng hoặc trả session về pool bằng `session.close()` hoặc sử dụng context manager.
""",
        )
        session.add(lesson2)
        session.flush()
        summary["lessons_created"].append(lesson2.title)

    # Lessons for CS201 (DRAFT)
    lesson_cs201 = (
        session.query(Lesson).filter(Lesson.course_id == course2.id, Lesson.position == 1).first()
    )
    if not lesson_cs201:
        lesson_cs201 = Lesson(
            course_id=course2.id,
            title="Bài 1: Phân tích Độ phức tạp Thuật toán Big-O",
            summary="Tổng quan về không gian và thời gian thực thi thuật toán.",
            position=1,
            estimated_duration_minutes=50,
            status="DRAFT",
            markdown_content=(
                "# Phân Tích Độ Phức Tạp Thuật Toán\n\nNội dung bài học đang được biên soạn..."
            ),
        )
        session.add(lesson_cs201)
        session.flush()
        summary["lessons_created"].append(lesson_cs201.title)

    # Lessons for CS301 (SUBMITTED_FOR_REVIEW)
    lesson_cs301 = (
        session.query(Lesson).filter(Lesson.course_id == course3.id, Lesson.position == 1).first()
    )
    if not lesson_cs301:
        lesson_cs301 = Lesson(
            course_id=course3.id,
            title="Bài 1: Nguyên lý LLM & Vector Database",
            summary="Khám phá cơ chế Attention, Transformers và biểu diễn vector không gian.",
            position=1,
            estimated_duration_minutes=40,
            status="PUBLISHED",
            published_at=now - timedelta(days=2),
            markdown_content=(
                "# Nguyên Lý LLM & Vector Database\n\nTổng quan về kiến trúc Transformer..."
            ),
        )
        session.add(lesson_cs301)
        session.flush()
        summary["lessons_created"].append(lesson_cs301.title)

    # 7. Safe clean PDF file attachment to Lesson 1 (if file_service is operational)
    existing_resource = (
        session.query(LessonResource).filter(LessonResource.lesson_id == lesson1.id).first()
    )
    if not existing_resource:
        try:
            from pwd301.services.file_service import attach_resource_to_lesson, store_file_stream

            clean_pdf_bytes = (
                b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
                b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
                b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n"
                b"0000000102 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
            )
            stream = io.BytesIO(clean_pdf_bytes)
            file_asset = store_file_stream(
                actor=instructor1,
                course_id=course1.id,
                file_stream=stream,
                filename="tai_lieu_kien_truc_web.pdf",
                content_type="application/pdf",
                asset_type="RESOURCE",
                title="Tài liệu tham khảo: Tổng quan Kiến trúc Web & HTTP",
                session=session,
            )
            attach_resource_to_lesson(
                actor=instructor1,
                lesson_id=lesson1.id,
                asset_id=file_asset.id,
                is_downloadable=True,
                label="Tài liệu tham khảo: Tổng quan Kiến trúc Web & HTTP",
                session=session,
            )
        except Exception:
            # Graceful fallback: continue seeding if storage engine is mocked in non-container env
            pass

    # 8. Question Bank for Course 1 (5 Question Types)
    existing_questions = (
        session.query(Question)
        .filter(Question.course_id == course1.id)
        .order_by(Question.id.asc())
        .all()
    )
    questions_map: dict[str, Question] = {}

    if not existing_questions:
        # Q1: SINGLE_CHOICE
        q1 = Question(
            course_id=course1.id,
            lesson_id=lesson1.id,
            creator_user_id=instructor1.id,
            difficulty="REMEMBER",
            learning_objective="Nhận diện decorator định tuyến URL trong Flask.",
            status="ACTIVE",
        )
        session.add(q1)
        session.flush()
        q1_rev = QuestionRevision(
            question_id=q1.id,
            revision_no=1,
            is_current=True,
            created_by_user_id=instructor1.id,
            content=(
                "Trong Flask, decorator nào được sử dụng phổ biến nhất để ánh xạ một đường dẫn "
                "URL tới hàm xử lý view function?"
            ),
            question_type="SINGLE_CHOICE",
            explanation="`@app.route()` là decorator chuẩn trong Flask để đăng ký URL routing.",
            change_type="INITIAL",
            approved_at=now,
        )
        session.add(q1_rev)
        session.flush()

        choices_q1 = [
            ("@app.route()", True, 1),
            ("@app.url()", False, 2),
            ("@app.endpoint()", False, 3),
            ("@app.path()", False, 4),
        ]
        for text, correct, pos in choices_q1:
            session.add(
                QuestionRevisionChoice(
                    question_revision_id=q1_rev.id,
                    choice_key=uuid.uuid4(),
                    content=text,
                    is_correct=correct,
                    position=pos,
                )
            )
        session.add(
            QuestionProvenance(
                question_id=q1.id,
                question_revision_id=q1_rev.id,
                source_type="MANUAL",
            )
        )
        questions_map["Q1"] = q1
        summary["questions_created"].append("Q1: SINGLE_CHOICE")

        # Q2: MULTIPLE_CHOICE
        q2 = Question(
            course_id=course1.id,
            lesson_id=lesson1.id,
            creator_user_id=instructor1.id,
            difficulty="UNDERSTAND",
            learning_objective="Phân biệt tính lũy đẳng (Idempotent) của các HTTP methods.",
            status="ACTIVE",
        )
        session.add(q2)
        session.flush()
        q2_rev = QuestionRevision(
            question_id=q2.id,
            revision_no=1,
            is_current=True,
            created_by_user_id=instructor1.id,
            content=(
                "Theo chuẩn RFC 7231, những HTTP methods nào sau đây có tính chất "
                "Idempotent (Lũy đẳng)?"
            ),
            question_type="MULTIPLE_CHOICE",
            explanation=(
                "GET, PUT, và DELETE là idempotent vì thực thi nhiều lần cho cùng một kết quả."
            ),
            change_type="INITIAL",
            approved_at=now,
        )
        session.add(q2_rev)
        session.flush()

        choices_q2 = [
            ("GET", True, 1),
            ("PUT", True, 2),
            ("DELETE", True, 3),
            ("POST", False, 4),
        ]
        for text, correct, pos in choices_q2:
            session.add(
                QuestionRevisionChoice(
                    question_revision_id=q2_rev.id,
                    choice_key=uuid.uuid4(),
                    content=text,
                    is_correct=correct,
                    position=pos,
                )
            )
        session.add(
            QuestionProvenance(
                question_id=q2.id,
                question_revision_id=q2_rev.id,
                source_type="MANUAL",
            )
        )
        questions_map["Q2"] = q2
        summary["questions_created"].append("Q2: MULTIPLE_CHOICE")

        # Q3: TRUE_FALSE
        q3 = Question(
            course_id=course1.id,
            lesson_id=lesson2.id,
            creator_user_id=instructor1.id,
            difficulty="REMEMBER",
            learning_objective="Hiểu về cơ chế signed cookie session mặc định của Flask.",
            status="ACTIVE",
        )
        session.add(q3)
        session.flush()
        q3_rev = QuestionRevision(
            question_id=q3.id,
            revision_no=1,
            is_current=True,
            created_by_user_id=instructor1.id,
            content=(
                "Trong Flask session mặc định, dữ liệu session được lưu trữ ở phía client "
                "dưới dạng cookie có chữ ký mật mã (cryptographically signed cookie)."
            ),
            question_type="TRUE_FALSE",
            explanation=(
                "Chính xác! Flask lưu session data trên client cookie và ký bằng SECRET_KEY."
            ),
            change_type="INITIAL",
            approved_at=now,
        )
        session.add(q3_rev)
        session.flush()

        choices_q3 = [
            ("Đúng", True, 1),
            ("Sai", False, 2),
        ]
        for text, correct, pos in choices_q3:
            session.add(
                QuestionRevisionChoice(
                    question_revision_id=q3_rev.id,
                    choice_key=uuid.uuid4(),
                    content=text,
                    is_correct=correct,
                    position=pos,
                )
            )
        session.add(
            QuestionProvenance(
                question_id=q3.id,
                question_revision_id=q3_rev.id,
                source_type="MANUAL",
            )
        )
        questions_map["Q3"] = q3
        summary["questions_created"].append("Q3: TRUE_FALSE")

        # Q4: SHORT_ANSWER
        q4 = Question(
            course_id=course1.id,
            lesson_id=lesson2.id,
            creator_user_id=instructor1.id,
            difficulty="APPLY",
            learning_objective="Ghi nhớ công cụ migration chuẩn được tích hợp trong Flask-Migrate.",
            status="ACTIVE",
        )
        session.add(q4)
        session.flush()
        q4_rev = QuestionRevision(
            question_id=q4.id,
            revision_no=1,
            is_current=True,
            created_by_user_id=instructor1.id,
            content=(
                "Tên của công cụ migration cơ sở dữ liệu mặc định được tích hợp "
                "cùng Flask-SQLAlchemy và Flask-Migrate là gì?"
            ),
            question_type="SHORT_ANSWER",
            explanation="Alembic là thư viện migration nền tảng của SQLAlchemy.",
            short_answer_match_mode="NORMALIZED",
            change_type="INITIAL",
            approved_at=now,
        )
        session.add(q4_rev)
        session.flush()

        session.add(
            QuestionRevisionAcceptedAnswer(
                question_revision_id=q4_rev.id,
                answer_text="Alembic",
                answer_normalized="alembic",
                position=1,
            )
        )
        session.add(
            QuestionProvenance(
                question_id=q4.id,
                question_revision_id=q4_rev.id,
                source_type="MANUAL",
            )
        )
        questions_map["Q4"] = q4
        summary["questions_created"].append("Q4: SHORT_ANSWER")

        # Q5: ESSAY
        q5 = Question(
            course_id=course1.id,
            lesson_id=lesson2.id,
            creator_user_id=instructor1.id,
            difficulty="APPLY",
            learning_objective="Phân tích vai trò và rủi ro của Connection Pooling trong CSDL.",
            status="ACTIVE",
        )
        session.add(q5)
        session.flush()
        q5_rev = QuestionRevision(
            question_id=q5.id,
            revision_no=1,
            is_current=True,
            created_by_user_id=instructor1.id,
            content=(
                "Hãy phân tích vai trò và rủi ro của Connection Pooling "
                "trong kiến trúc ứng dụng web đa luồng."
            ),
            question_type="ESSAY",
            explanation=(
                "Connection Pooling giúp giảm overhead kết nối nhưng có nguy cơ "
                "rò rỉ kết nối nếu không được giải phóng."
            ),
            change_type="INITIAL",
            approved_at=now,
        )
        session.add(q5_rev)
        session.flush()
        session.add(QuestionProvenance(question_id=q5.id, source_type="MANUAL"))
        questions_map["Q5"] = q5
        summary["questions_created"].append("Q5: ESSAY")
    else:
        for idx, q in enumerate(existing_questions, start=1):
            questions_map[f"Q{idx}"] = q

    # 9. Assessment for CS101 (PUBLISHED)
    assessment1 = session.query(Assessment).filter(Assessment.course_id == course1.id).first()
    if not assessment1:
        assessment1 = Assessment(
            course_id=course1.id,
            title="Kiểm tra Giữa kỳ: Kiến thức Web & Flask Core",
            description=(
                "Bài đánh giá năng lực lập trình web, giao thức HTTP, "
                "kiến trúc REST API và SQLAlchemy ORM."
            ),
            assessment_type="MIDTERM",
            status="PUBLISHED",
            time_limit_minutes=30,
            attempt_limit=3,
            scoring_policy="HIGHEST",
            passing_percent=decimal.Decimal("60.00"),
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="IMMEDIATE",
            published_at=now - timedelta(days=7),
            first_attempt_started_at=None,
        )
        session.add(assessment1)
        session.flush()
        summary["assessments_created"].append(assessment1.title)

        # Section 1: Trắc nghiệm khách quan
        sec1 = AssessmentSection(
            assessment_id=assessment1.id,
            title="Phần 1: Trắc nghiệm Khách quan",
            instructions="Chọn câu trả lời chính xác nhất hoặc điền từ khóa phù hợp.",
            position=1,
        )
        session.add(sec1)
        session.flush()

        # Section 2: Tự luận kiến trúc
        sec2 = AssessmentSection(
            assessment_id=assessment1.id,
            title="Phần 2: Tự luận Vận dụng Kiến trúc",
            instructions="Trả lời ngắn gọn và súc tích câu hỏi tự luận phân tích hệ thống.",
            position=2,
        )
        session.add(sec2)
        session.flush()

        # Assign Questions: Q1..Q4 in Section 1, Q5 in Section 2
        for pos, q_key in enumerate(["Q1", "Q2", "Q3", "Q4"], start=1):
            if q_key in questions_map:
                session.add(
                    AssessmentQuestionAssignment(
                        assessment_id=assessment1.id,
                        section_id=sec1.id,
                        question_id=questions_map[q_key].id,
                        position=pos,
                        points=decimal.Decimal("4.0000"),
                        is_mandatory=True,
                    )
                )

        if "Q5" in questions_map:
            session.add(
                AssessmentQuestionAssignment(
                    assessment_id=assessment1.id,
                    section_id=sec2.id,
                    question_id=questions_map["Q5"].id,
                    position=1,
                    points=decimal.Decimal("4.0000"),
                    is_mandatory=True,
                )
            )
        session.flush()

        # Lock structure by recording first_attempt_started_at once sections & questions are linked
        assessment1.first_attempt_started_at = now - timedelta(days=5)
        session.flush()
    else:
        if assessment1.first_attempt_started_at is None:
            assessment1.first_attempt_started_at = now - timedelta(days=5)
            session.flush()

    # 10. Enrollments & Progress for Students
    def get_or_create_enrollment(
        student: User, course: Course
    ) -> tuple[Enrollment, EnrollmentPeriod]:
        enr = (
            session.query(Enrollment)
            .filter(
                Enrollment.student_user_id == student.id,
                Enrollment.course_id == course.id,
            )
            .first()
        )
        if not enr:
            enr = Enrollment(
                student_user_id=student.id,
                course_id=course.id,
                status="ACTIVE",
                enrolled_at=now - timedelta(days=10),
            )
            session.add(enr)
            session.flush()

            period = EnrollmentPeriod(
                enrollment_id=enr.id,
                period_no=1,
                status="ACTIVE",
                started_at=now - timedelta(days=10),
            )
            session.add(period)
            session.flush()

            enr.current_period_id = period.id
            session.flush()
            summary["enrollments_created"].append(f"{student.email} -> {course.course_code}")
        else:
            period_opt = (
                session.get(EnrollmentPeriod, enr.current_period_id)
                if enr.current_period_id
                else None
            )
            if period_opt is None:
                period_opt = EnrollmentPeriod(
                    enrollment_id=enr.id,
                    period_no=1,
                    status="ACTIVE",
                    started_at=now - timedelta(days=10),
                )
                session.add(period_opt)
                session.flush()
                enr.current_period_id = period_opt.id
                session.flush()
            period = period_opt
        return enr, period

    # Student 1: Enrolled in CS101, 100% Progress, Completed
    enr1, period1 = get_or_create_enrollment(student1, course1)
    enr1.current_progress_percent = decimal.Decimal("100.00")
    enr1.completed_at = now - timedelta(days=3)

    # Progress on lessons
    for les in [lesson1, lesson2]:
        lp = (
            session.query(LessonProgress)
            .filter(
                LessonProgress.enrollment_period_id == period1.id,
                LessonProgress.lesson_id == les.id,
            )
            .first()
        )
        if not lp:
            session.add(
                LessonProgress(
                    enrollment_period_id=period1.id,
                    lesson_id=les.id,
                    seconds_spent=120,
                    max_view_fraction=decimal.Decimal("1.0000"),
                    completed_at=now - timedelta(days=5),
                    last_activity_at=now - timedelta(days=5),
                )
            )

    # Student 2: Enrolled in CS101, 70% Progress
    enr2, period2 = get_or_create_enrollment(student2, course1)
    enr2.current_progress_percent = decimal.Decimal("70.00")

    lp2_1 = (
        session.query(LessonProgress)
        .filter(
            LessonProgress.enrollment_period_id == period2.id,
            LessonProgress.lesson_id == lesson1.id,
        )
        .first()
    )
    if not lp2_1:
        session.add(
            LessonProgress(
                enrollment_period_id=period2.id,
                lesson_id=lesson1.id,
                seconds_spent=95,
                max_view_fraction=decimal.Decimal("1.0000"),
                completed_at=now - timedelta(days=4),
                last_activity_at=now - timedelta(days=4),
            )
        )

    # Student 3: Enrolled in CS101, 15% Progress
    enr3, period3 = get_or_create_enrollment(student3, course1)
    enr3.current_progress_percent = decimal.Decimal("15.00")

    session.flush()

    # 11. Attempts for Assessment 1
    # Attempt 1 (student1): Fully GRADED (20.0 / 20.0)
    attempt1 = (
        session.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.assessment_id == assessment1.id,
            AssessmentAttempt.student_user_id == student1.id,
            AssessmentAttempt.attempt_number == 1,
        )
        .first()
    )
    if not attempt1 and "Q1" in questions_map and "Q5" in questions_map:
        attempt1 = AssessmentAttempt(
            assessment_id=assessment1.id,
            enrollment_period_id=period1.id,
            student_user_id=student1.id,
            attempt_number=1,
            status="GRADED",
            started_at=now - timedelta(days=4, hours=2),
            deadline_at=now - timedelta(days=4, hours=1, minutes=30),
            submitted_at=now - timedelta(days=4, hours=1, minutes=40),
            graded_at=now - timedelta(days=4, hours=1),
            finalized_at=now - timedelta(days=4, hours=1),
        )
        session.add(attempt1)
        session.flush()
        summary["attempts_created"].append(f"{student1.email}: GRADED")

        # Snapshot and grade questions for student1
        for pos, q_key in enumerate(["Q1", "Q2", "Q3", "Q4", "Q5"], start=1):
            q_entity = questions_map[q_key]
            q_rev = q_entity.current_revision
            aq = AttemptQuestion(
                attempt_id=attempt1.id,
                source_question_id=q_entity.id,
                source_question_revision_id=q_rev.id,
                position=pos,
                question_type_snapshot=q_rev.question_type,
                content_snapshot=q_rev.content,
                points_assigned=decimal.Decimal("4.0000"),
            )
            session.add(aq)
            session.flush()

            # Snapshot choices if present
            selected_choice_snapshots = []
            for c_pos, choice in enumerate(q_rev.choices, start=1):
                acs = AttemptChoiceSnapshot(
                    attempt_question_id=aq.id,
                    source_choice_id=choice.id,
                    choice_key_snapshot=choice.choice_key,
                    content_snapshot=choice.content,
                    position=c_pos,
                )
                session.add(acs)
                session.flush()
                if choice.is_correct:
                    selected_choice_snapshots.append(acs)

            # Answer
            ans = AttemptAnswer(
                attempt_question_id=aq.id,
                saved_at=now - timedelta(days=4, hours=1, minutes=42),
                answer_text=(
                    "Alembic"
                    if q_key == "Q4"
                    else (
                        "Connection pooling giúp tái sử dụng socket kết nối, "
                        "giảm độ trễ TCP handshake nhưng cần quản lý timeout chặt chẽ."
                        if q_key == "Q5"
                        else None
                    )
                ),
            )
            if selected_choice_snapshots:
                ans.selected_choices = selected_choice_snapshots
            session.add(ans)
            session.flush()

            # Grade: 4.0 for all (Q5 is MANUAL_GRADED)
            if q_key == "Q5":
                session.add(
                    AttemptQuestionGrade(
                        attempt_question_id=aq.id,
                        awarded_points=decimal.Decimal("4.0000"),
                        grading_status="MANUAL_GRADED",
                        grading_rule="ORIGINAL",
                        graded_against_revision_id=q_rev.id,
                        manual_reason=(
                            "Phân tích chi tiết, chính xác vai trò và rủi ro của connection pool."
                        ),
                        graded_by_user_id=instructor1.id,
                        graded_at=now - timedelta(days=4, hours=1),
                    )
                )
            else:
                session.add(
                    AttemptQuestionGrade(
                        attempt_question_id=aq.id,
                        awarded_points=decimal.Decimal("4.0000"),
                        grading_status="AUTO_GRADED",
                        grading_rule="ORIGINAL",
                        graded_against_revision_id=q_rev.id,
                        graded_at=now - timedelta(days=4, hours=1),
                    )
                )

        # Assessment Result for student1
        session.add(
            AssessmentResult(
                attempt_id=attempt1.id,
                raw_score=decimal.Decimal("20.0000"),
                max_score=decimal.Decimal("20.0000"),
                percent_score=decimal.Decimal("100.0000"),
                passed=True,
                status="RELEASED",
                released_at=now - timedelta(days=4, hours=1),
                graded_at=now - timedelta(days=4, hours=1),
            )
        )

        # CourseCompletionSummary for student1
        summary_rec = (
            session.query(CourseCompletionSummary)
            .filter(
                CourseCompletionSummary.student_user_id == student1.id,
                CourseCompletionSummary.course_id == course1.id,
            )
            .first()
        )
        if not summary_rec:
            session.add(
                CourseCompletionSummary(
                    student_user_id=student1.id,
                    course_id=course1.id,
                    ever_completed=True,
                    prerequisite_eligible=True,
                    first_completed_at=now - timedelta(days=3),
                    latest_completed_at=now - timedelta(days=3),
                    final_aggregate_score=decimal.Decimal("100.0000"),
                    source_period_id=period1.id,
                )
            )

    # Attempt 2 (student2): SUBMITTED awaiting manual grading for Q5
    attempt2 = (
        session.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.assessment_id == assessment1.id,
            AssessmentAttempt.student_user_id == student2.id,
            AssessmentAttempt.attempt_number == 1,
        )
        .first()
    )
    if not attempt2 and "Q1" in questions_map and "Q5" in questions_map:
        attempt2 = AssessmentAttempt(
            assessment_id=assessment1.id,
            enrollment_period_id=period2.id,
            student_user_id=student2.id,
            attempt_number=1,
            status="SUBMITTED",
            started_at=now - timedelta(hours=3),
            deadline_at=now - timedelta(hours=2, minutes=30),
            submitted_at=now - timedelta(hours=2, minutes=40),
        )
        session.add(attempt2)
        session.flush()
        summary["attempts_created"].append(f"{student2.email}: SUBMITTED (pending essay)")

        for pos, q_key in enumerate(["Q1", "Q2", "Q3", "Q4", "Q5"], start=1):
            q_entity = questions_map[q_key]
            q_rev = q_entity.current_revision
            aq = AttemptQuestion(
                attempt_id=attempt2.id,
                source_question_id=q_entity.id,
                source_question_revision_id=q_rev.id,
                position=pos,
                question_type_snapshot=q_rev.question_type,
                content_snapshot=q_rev.content,
                points_assigned=decimal.Decimal("4.0000"),
            )
            session.add(aq)
            session.flush()

            # Snapshot choices if present
            selected_choice_snapshots = []
            for c_pos, choice in enumerate(q_rev.choices, start=1):
                acs = AttemptChoiceSnapshot(
                    attempt_question_id=aq.id,
                    source_choice_id=choice.id,
                    choice_key_snapshot=choice.choice_key,
                    content_snapshot=choice.content,
                    position=c_pos,
                )
                session.add(acs)
                session.flush()
                if q_key in ("Q1", "Q2", "Q3") and choice.is_correct:
                    selected_choice_snapshots.append(acs)

            ans = AttemptAnswer(
                attempt_question_id=aq.id,
                saved_at=now - timedelta(hours=2, minutes=45),
                answer_text=(
                    "Flask-Migrate"
                    if q_key == "Q4"
                    else ("TCP Connection" if q_key == "Q5" else None)
                ),
            )
            if selected_choice_snapshots:
                ans.selected_choices = selected_choice_snapshots
            session.add(ans)
            session.flush()

            # Auto-graded: Q1-Q3 correct (12 pts), Q4 incorrect (0 pts), Q5 pending essay
            if q_key == "Q5":
                session.add(
                    AttemptQuestionGrade(
                        attempt_question_id=aq.id,
                        awarded_points=decimal.Decimal("0.0000"),
                        grading_status="PENDING",
                        grading_rule="ORIGINAL",
                        graded_against_revision_id=q_rev.id,
                        graded_at=now - timedelta(hours=2, minutes=40),
                    )
                )
            else:
                pts = (
                    decimal.Decimal("4.0000")
                    if q_key in ("Q1", "Q2", "Q3")
                    else decimal.Decimal("0.0000")
                )
                session.add(
                    AttemptQuestionGrade(
                        attempt_question_id=aq.id,
                        awarded_points=pts,
                        grading_status="AUTO_GRADED",
                        grading_rule="ORIGINAL",
                        graded_against_revision_id=q_rev.id,
                        graded_at=now - timedelta(hours=2, minutes=40),
                    )
                )

        session.add(
            AssessmentResult(
                attempt_id=attempt2.id,
                raw_score=decimal.Decimal("12.0000"),
                max_score=decimal.Decimal("20.0000"),
                percent_score=decimal.Decimal("60.0000"),
                passed=True,
                status="RELEASED",
            )
        )

    # 12. Sample In-App Notifications (Enriched & Personalized per User & Role)
    demo_notification_configs = [
        # Admin User (admin@pwd301.local)
        (
            admin_user,
            instructor1.id,
            "SYSTEM_SECURITY_ALERT",
            "SECURITY",
            "Cảnh báo bảo mật: Phiên đăng nhập mới",
            (
                "Phát hiện phiên đăng nhập quản trị từ IP lạ (192.168.1.105). "
                "Vui lòng kiểm tra nhật ký kiểm toán."
            ),
            {
                "target_url": "#/admin/governance?tab=security",
                "action_url": "#/admin/governance?tab=security",
            },
            False,
        ),
        (
            admin_user,
            instructor2.id,
            "COURSE_APPROVAL_REQUEST",
            "COURSE",
            "Yêu cầu xét duyệt khóa học: CS301",
            (
                "Giảng viên ThS. Trần Thị B đã gửi yêu cầu xuất bản khóa học CS301. "
                "Đang chờ bạn phê duyệt."
            ),
            {
                "target_url": "#/admin/governance?tab=courses",
                "action_url": "#/admin/governance?tab=courses",
            },
            False,
        ),
        (
            admin_user,
            admin_user.id,
            "SYSTEM_BACKUP_COMPLETED",
            "SYSTEM",
            "Sao lưu cơ sở dữ liệu định kỳ hoàn tất",
            (
                "Bản sao lưu tự động lúc 00:00 UTC đã được lưu trữ an toàn "
                "(Dung lượng 142 MB, toàn vẹn 100%)."
            ),
            {"target_url": "#/admin/operations", "action_url": "#/admin/operations"},
            True,
        ),
        (
            admin_user,
            instructor1.id,
            "ASSESSMENT_MONITORING",
            "ASSESSMENT",
            "Báo cáo kết thúc kỳ thi CS101 Midterm",
            (
                "Kỳ thi giữa kỳ CS101 đã kết thúc thời gian làm bài. "
                "2 học viên đã nộp bài, 0 trường hợp vi phạm."
            ),
            {"target_url": "#/admin/operations", "action_url": "#/admin/operations"},
            True,
        ),
        # Instructor 1 (instructor1@pwd301.local)
        (
            instructor1,
            student2.id,
            "ASSESSMENT_SUBMITTED",
            "ASSESSMENT",
            "Có bài thi tự luận mới cần chấm",
            (
                "Sinh viên Phạm Minh Tuấn đã nộp bài thi MIDTERM môn CS101. "
                "Vui lòng chấm điểm câu hỏi tự luận."
            ),
            {"target_url": "#/instructor/grading", "action_url": "#/instructor/grading"},
            False,
        ),
        (
            instructor1,
            admin_user.id,
            "COURSE_PUBLISHED",
            "COURSE",
            "Khóa học CS101 đã được phê duyệt xuất bản",
            (
                "Quản trị viên đã phê duyệt khóa học CS101: Lập trình Python & "
                "Flask Web Nâng Cao lên cổng công khai."
            ),
            {"target_url": "#/instructor/courses", "action_url": "#/instructor/courses"},
            False,
        ),
        (
            instructor1,
            instructor1.id,
            "GRADE_REPORT",
            "GRADE",
            "Báo cáo phổ điểm giữa kỳ môn CS101",
            (
                "Thống kê sơ bộ: Điểm trung bình đạt 18.5/20.0 (92.5%). "
                "Có 1 học viên đạt điểm tối đa 20.0."
            ),
            {"target_url": "#/instructor/analytics", "action_url": "#/instructor/analytics"},
            True,
        ),
        (
            instructor1,
            admin_user.id,
            "SYSTEM_ANNOUNCEMENT",
            "SYSTEM",
            "Lịch bảo trì máy chủ khảo thí cuối tuần",
            (
                "Hệ thống thi trắc nghiệm sẽ bảo trì định kỳ từ 02:00 đến 03:00 "
                "Chủ nhật. Giảng viên vui lòng lưu ý."
            ),
            {"target_url": "#/instructor/dashboard", "action_url": "#/instructor/dashboard"},
            True,
        ),
        # Instructor 2 (instructor2@pwd301.local)
        (
            instructor2,
            admin_user.id,
            "COURSE_STATUS_UPDATE",
            "COURSE",
            "Hồ sơ xét duyệt CS301 đang được thụ lý",
            (
                "Đề cương chi tiết và ngân hàng bài giảng CS301 đã được chuyển "
                "đến ban khảo thí xem xét."
            ),
            {"target_url": "#/instructor/courses", "action_url": "#/instructor/courses"},
            False,
        ),
        (
            instructor2,
            instructor2.id,
            "QUESTION_BANK_READY",
            "ASSESSMENT",
            "Ngân hàng câu hỏi CS301 đã sẵn sàng",
            (
                "Đã đồng bộ 25 câu hỏi trắc nghiệm chuẩn Azota vào ngân hàng "
                "câu hỏi khảo thí học phần CS301."
            ),
            {"target_url": "#/instructor/questions", "action_url": "#/instructor/questions"},
            False,
        ),
        # Student 1 (student1@pwd301.local - Lê Hoàng Long)
        (
            student1,
            instructor1.id,
            "ASSESSMENT_GRADED",
            "ASSESSMENT",
            "Chúc mừng bạn đạt 20.0/20.0 điểm bài thi giữa kỳ!",
            (
                "Bạn đã đạt điểm số tối đa trong bài kiểm tra giữa kỳ môn CS101. "
                "Kết quả đã lưu vào hồ sơ học vụ."
            ),
            {"target_url": "#/student/assessments", "action_url": "#/student/assessments"},
            False,
        ),
        (
            student1,
            instructor1.id,
            "LESSON_UNLOCKED",
            "COURSE",
            "Bài giảng mới đã mở: Lesson 04 - SQLAlchemy ORM",
            (
                "Nội dung bài giảng mới đã sẵn sàng. "
                "Hoàn thành bài kiểm tra nhanh để mở khóa bài tiếp theo."
            ),
            {"target_url": "#/student/courses", "action_url": "#/student/courses"},
            False,
        ),
        (
            student1,
            instructor1.id,
            "GRADE_ANNOUNCEMENT",
            "GRADE",
            "Bảng điểm thành phần đợt 1 đã công bố",
            "Giảng viên ThS. Nguyễn Văn A đã công bố điểm danh và điểm bài tập Lab 01, Lab 02.",
            {"target_url": "#/student/courses", "action_url": "#/student/courses"},
            True,
        ),
        # Student 2 (student2@pwd301.local - Phạm Minh Tuấn)
        (
            student2,
            instructor1.id,
            "ASSESSMENT_SUBMITTED_CONFIRM",
            "ASSESSMENT",
            "Bài thi giữa kỳ CS101 nộp thành công",
            (
                "Bài làm của bạn đã được ghi nhận vào lúc 10:30 UTC. "
                "Câu hỏi tự luận đang chờ Giảng viên chấm điểm."
            ),
            {"target_url": "#/student/assessments", "action_url": "#/student/assessments"},
            False,
        ),
        (
            student2,
            instructor1.id,
            "ASSIGNMENT_DUE_REMINDER",
            "COURSE",
            "Nhắc nhở: Hạn nộp bài tập lớn Lab 03",
            (
                "Hạn chót nộp bài tập lớn môn CS101 còn 2 ngày (23:59 Chủ nhật). "
                "Hãy rà soát mã nguồn trước khi nộp."
            ),
            {"target_url": "#/student/courses", "action_url": "#/student/courses"},
            False,
        ),
        # Student 3 (student3@pwd301.local - Vũ Thảo Nguyên)
        (
            student3,
            admin_user.id,
            "COURSE_ENROLLMENT_CONFIRM",
            "COURSE",
            "Đăng ký học phần CS101 thành công",
            (
                "Chào mừng bạn đến với khóa học CS101. "
                "Bạn có thể bắt đầu học bài giảng mở đầu ngay bây giờ."
            ),
            {"target_url": "#/student/courses", "action_url": "#/student/courses"},
            False,
        ),
        (
            student3,
            instructor1.id,
            "ASSESSMENT_SCHEDULED",
            "ASSESSMENT",
            "Lịch khảo sát năng lực đầu vào",
            (
                "Bài kiểm tra khảo sát kiến thức nền tảng sẽ mở trong 24 giờ "
                "tới tại Phòng chờ Khảo thí."
            ),
            {"target_url": "#/student/assessments", "action_url": "#/student/assessments"},
            True,
        ),
        # Student 4 (student4@pwd301.local - Đặng Gia Huy)
        (
            student4,
            admin_user.id,
            "WELCOME_ONBOARDING",
            "SYSTEM",
            "Chào mừng bạn gia nhập Cổng Học thuật PWD301",
            (
                "Tài khoản học viên của bạn đã kích hoạt hoàn tất. "
                "Hãy khám phá danh mục khóa học để bắt đầu."
            ),
            {"target_url": "#/student/catalog", "action_url": "#/student/catalog"},
            False,
        ),
        (
            student4,
            admin_user.id,
            "PROFILE_UPDATE_PROMPT",
            "SYSTEM",
            "Cập nhật hồ sơ học viên của bạn",
            (
                "Vui lòng cập nhật hình đại diện và thông tin liên hệ "
                "để nhận các chứng chỉ học thuật hợp lệ."
            ),
            {"target_url": "#/student/profile", "action_url": "#/student/profile"},
            True,
        ),
    ]

    for (
        recipient_usr,
        actor_uid,
        ev_type,
        cat_code,
        title_txt,
        body_txt,
        payload_dict,
        is_read_flag,
    ) in demo_notification_configs:
        existing_ev = (
            session.query(NotificationEvent)
            .filter(
                NotificationEvent.actor_user_id == actor_uid,
                NotificationEvent.event_type == ev_type,
            )
            .first()
        )
        if not existing_ev:
            existing_ev = NotificationEvent(
                event_type=ev_type,
                actor_user_id=actor_uid,
                target_type="USER",
                target_id=recipient_usr.id,
                payload_json=json.dumps(payload_dict),
                created_at=now,
            )
            session.add(existing_ev)
            session.flush()
        else:
            existing_ev.payload_json = json.dumps(payload_dict)

        existing_notif = (
            session.query(Notification)
            .filter(
                Notification.notification_event_id == existing_ev.id,
                Notification.recipient_user_id == recipient_usr.id,
            )
            .first()
        )
        if not existing_notif:
            session.add(
                Notification(
                    notification_event_id=existing_ev.id,
                    recipient_user_id=recipient_usr.id,
                    category=cat_code,
                    title=title_txt,
                    body=body_txt,
                    read_at=now - timedelta(hours=2) if is_read_flag else None,
                    created_at=now - timedelta(minutes=15),
                )
            )
            summary["notifications_created"] += 1

    # 13. Sample Audit Events
    audit_samples = [
        (
            "COURSE_PUBLISHED",
            "COURSE",
            course1.id,
            admin_user,
            "Admin approved and published course CS101",
        ),
        (
            "ASSESSMENT_PUBLISHED",
            "ASSESSMENT",
            assessment1.id,
            instructor1,
            "Instructor published midterm exam",
        ),
        (
            "ROLE_ASSIGNED",
            "USER",
            instructor1.id,
            admin_user,
            "Assigned INSTRUCTOR role to instructor1",
        ),
    ]
    for action, t_type, t_id, actor_u, reason_txt in audit_samples:
        existing_audit = (
            session.query(AuditEvent)
            .filter(
                AuditEvent.action == action,
                AuditEvent.target_type == t_type,
                AuditEvent.target_id == t_id,
            )
            .first()
        )
        if not existing_audit:
            session.add(
                AuditEvent(
                    actor_user_id=actor_u.id,
                    actor_roles_snapshot=",".join(sorted(actor_u.role_codes)) or "SYSTEM",
                    action=action,
                    target_type=t_type,
                    target_id=t_id,
                    reason=reason_txt,
                    performed_as_admin=(actor_u.id == admin_user.id),
                    created_at=now - timedelta(days=7),
                )
            )
            summary["audit_events_created"] += 1

    try:
        session.commit()
    except Exception:
        session.rollback()
        raise

    return summary
