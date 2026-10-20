# -*- coding: utf-8 -*-
"""Seed script for Black Hat Cybersecurity Course (BHE501).
Builds a production-ready course in Microsoft SQL Server based on 5 PDF eBooks:
- 5 Chapters (LearningUnits)
- 60 Lessons (each >= 600 words, with YouTube 16:9 video, miniquiz, attached PDF file asset)
- 5 Chapter Quizzes (10 questions each = 50 questions)
- 1 Final Comprehensive Exam (20 questions)
- Total 70 assessment questions in question bank
- Student enrollments and completion rules
"""

import io
import os
import sys
import uuid
from decimal import Decimal
from datetime import timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Force UTF-8 stdout for Windows consoles
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pwd301 import create_app, db
from pwd301.models.identity import User, Role
from pwd301.models.course import (
    Course,
    LearningUnit,
    Lesson,
    CourseChangeRequest,
    CourseCompletionRule,
    Enrollment,
    EnrollmentPeriod,
    EnrollmentEvent,
)
from pwd301.models.file_import import LessonResource, FileAsset, FileRevision
from pwd301.models.assessment import (
    Assessment,
    AssessmentSection,
    AssessmentQuestionAssignment,
)
from pwd301.models.question_bank import (
    Question,
    QuestionRevision,
    QuestionRevisionChoice,
)
from pwd301.models.types import utc_now
from pwd301.services.file_service import store_file_stream, attach_resource_to_lesson
from pwd301.services.enrollment_service import enroll_student

from scripts.course_data.builder_ch1 import get_chapter_1_lessons
from scripts.course_data.builder_ch2 import get_chapter_2_lessons
from scripts.course_data.builder_ch3 import get_chapter_3_lessons
from scripts.course_data.builder_ch4 import get_chapter_4_lessons
from scripts.course_data.builder_ch5 import get_chapter_5_lessons
from scripts.course_data.builder_assessments import (
    get_chapter_1_quiz_data,
    get_chapter_2_quiz_data,
    get_chapter_3_quiz_data,
    get_chapter_4_quiz_data,
    get_chapter_5_quiz_data,
    get_final_exam_data,
)
from scripts.course_data.common import count_vietnamese_words

# PDF source directory: check local repository first, fallback to external path
LOCAL_EBOOKS_DIR = Path(__file__).resolve().parent / "course_data" / "ebooks"
EXTERNAL_EBOOKS_DIR = Path(r"F:\cyber\khóa học all\Blackhat EBooks")
PDF_DIR = LOCAL_EBOOKS_DIR if LOCAL_EBOOKS_DIR.exists() and any(LOCAL_EBOOKS_DIR.glob("*.pdf")) else EXTERNAL_EBOOKS_DIR

PDF_FILES = {
    1: PDF_DIR / "TOR.pdf",
    2: PDF_DIR / "Tor_and_The_Dark_Net_Remain_Anonymous_and_Evade_NSA_Spying_by_Ja.pdf",
    3: PDF_DIR / "Dissecting the Dark Web.pdf",
    4: PDF_DIR / "Black_Hat_Rust.pdf",
    5: PDF_DIR / "BlackHat GraphQL.pdf",
}



def ensure_users():
    """Ensure baseline admin, instructor, and student users exist."""
    print("[1/8] Đảm bảo tài khoản người dùng hệ thống...")
    from werkzeug.security import generate_password_hash

    admin_role = db.session.query(Role).filter_by(name="System Administrator").first()
    instructor_role = db.session.query(Role).filter_by(name="Instructor").first()
    student_role = db.session.query(Role).filter_by(name="Student").first()

    # Admin
    admin = db.session.query(User).filter_by(email="admin@pwd301.local").first()
    if not admin:
        admin = User(
            email="admin@pwd301.local",
            password_hash=generate_password_hash("Password123!"),
            display_name="System Administrator",
            status="ACTIVE",
        )
        admin.roles = [admin_role, instructor_role, student_role]
        db.session.add(admin)
        db.session.flush()

    # Instructor
    instructor = db.session.query(User).filter_by(email="instructor1@pwd301.local").first()
    if not instructor:
        instructor = User(
            email="instructor1@pwd301.local",
            password_hash=generate_password_hash("Password123!"),
            display_name="TS. Nguyễn Văn An - Giảng Viên An Ninh Mạng",
            status="ACTIVE",
        )
        instructor.roles = [instructor_role, student_role]
        db.session.add(instructor)
        db.session.flush()

    # Students
    student1 = db.session.query(User).filter_by(email="student1@pwd301.local").first()
    if not student1:
        student1 = User(
            email="student1@pwd301.local",
            password_hash=generate_password_hash("Password123!"),
            display_name="Học Viên Trần Minh Quân",
            status="ACTIVE",
        )
        student1.roles = [student_role]
        db.session.add(student1)
        db.session.flush()

    student2 = db.session.query(User).filter_by(email="student2@pwd301.local").first()
    if not student2:
        student2 = User(
            email="student2@pwd301.local",
            password_hash=generate_password_hash("Password123!"),
            display_name="Học Viên Lê Hoàng Nam",
            status="ACTIVE",
        )
        student2.roles = [student_role]
        db.session.add(student2)
        db.session.flush()

    db.session.commit()
    print(f"  ✓ Admin: {admin.email}")
    print(f"  ✓ Instructor: {instructor.email}")
    print(f"  ✓ Students: {student1.email}, {student2.email}")
    return admin, instructor, student1, student2


def cleanup_existing_course(course_code="BHE501"):
    """Safely cleanup any previous instance of the course using raw SQL for strict FK order."""
    import sqlalchemy as sa
    existing = db.session.query(Course).filter_by(course_code=course_code).first()
    if not existing:
        return
    print(f"  Dọn dẹp phiên bản cũ của khóa học {course_code} (ID: {existing.id})...")
    
    db.session.execute(sa.text("""
        DECLARE @cid BIGINT = (SELECT id FROM courses WHERE course_code = :code);
        IF @cid IS NOT NULL
        BEGIN
            UPDATE courses SET thumbnail_file_asset_id = NULL WHERE id = @cid;
            DELETE FROM lesson_resources WHERE lesson_id IN (SELECT id FROM lessons WHERE course_id = @cid);
            DELETE FROM lessons WHERE course_id = @cid;
            DELETE FROM learning_units WHERE course_id = @cid;
            DELETE FROM assessment_question_assignments WHERE assessment_id IN (SELECT id FROM assessments WHERE course_id = @cid);
            DELETE FROM assessment_sections WHERE assessment_id IN (SELECT id FROM assessments WHERE course_id = @cid);
            DELETE FROM assessments WHERE course_id = @cid;
            DELETE FROM question_revision_choices WHERE question_revision_id IN (
                SELECT qr.id FROM question_revisions qr JOIN questions q ON qr.question_id = q.id WHERE q.course_id = @cid
            );
            DELETE FROM question_revisions WHERE question_id IN (SELECT id FROM questions WHERE course_id = @cid);
            DELETE FROM questions WHERE course_id = @cid;
            DELETE FROM enrollment_events WHERE enrollment_id IN (SELECT id FROM enrollments WHERE course_id = @cid);
            DELETE FROM enrollment_periods WHERE enrollment_id IN (SELECT id FROM enrollments WHERE course_id = @cid);
            DELETE FROM enrollments WHERE course_id = @cid;
            DELETE FROM course_change_requests WHERE course_id = @cid;
            DELETE FROM course_completion_rules WHERE course_id = @cid;
            DELETE FROM file_scan_results WHERE file_revision_id IN (
                SELECT fr.id FROM file_revisions fr JOIN file_assets fa ON fr.file_asset_id = fa.id WHERE fa.course_id = @cid
            );
            DELETE FROM file_revisions WHERE file_asset_id IN (SELECT id FROM file_assets WHERE course_id = @cid);
            DELETE FROM file_assets WHERE course_id = @cid;
            DELETE FROM courses WHERE id = @cid;
        END
    """), {"code": course_code})
    db.session.commit()
    print("  ✓ Đã dọn dẹp sạch phiên bản cũ.")


def create_course_thumbnail():
    """Generate high-resolution 16:9 banner PNG (1280x720) for the course."""
    img = Image.new("RGB", (1280, 720), color=(15, 23, 42))  # Slate 900
    draw = ImageDraw.Draw(img)

    # Accent decorative bars
    draw.rectangle([0, 0, 1280, 12], fill=(16, 185, 129))  # Emerald 500
    draw.rectangle([0, 708, 1280, 720], fill=(16, 185, 129))
    draw.rectangle([60, 60, 1220, 660], outline=(30, 41, 59), width=3)

    # Title & Text
    draw.text((100, 180), "BLACK HAT CYBERSECURITY MASTERCLASS", fill=(16, 185, 129))
    draw.text((100, 240), "AN NINH MẠNG MŨ ĐEN CHUYÊN SÂU", fill=(248, 250, 252))
    draw.text((100, 310), "Tor Network • Amnesic OPSEC • Dark Web Malware • Rust Exploits • GraphQL", fill=(148, 163, 184))
    draw.text((100, 480), "Khóa học 60 bài giảng chuyên sâu + 5 bài kiểm tra chương + Bài thi tốt nghiệp 20 câu", fill=(203, 213, 225))
    draw.text((100, 540), "Mã môn: BHE501 | Tác giả: Chuyên gia An ninh Mạng", fill=(100, 116, 139))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def seed_course(admin, instructor):
    """Create Course BHE501."""
    print("[2/8] Khởi tạo Khóa học BHE501...")
    cleanup_existing_course("BHE501")

    now = utc_now()
    course = Course(
        course_code="BHE501",
        title="Kỹ Thuật An Ninh Mạng Mũ Đen: Tor, Dark Web, Lập Trình Khai Thác Rust & Pentest GraphQL",
        learning_objectives="Làm chủ kiến trúc Tor, kỹ thuật OPSEC, mã độc C2 Darknet, lập trình khai thác bằng Rust và kiểm thử bảo mật GraphQL.",
        target_audience="Chuyên gia an ninh mạng, kỹ sư bảo mật Red Team/Blue Team, lập trình viên hệ thống.",
        completion_requirements="Hoàn thành 100% bài học, vượt qua 5 bài kiểm tra chương và đạt điểm tối thiểu 75% trong bài thi tốt nghiệp.",
        description="""# Khóa Học Kỹ Thuật An Ninh Mạng Mũ Đen Chuyên Sâu (BHE501)

Chào mừng bạn đến với chương trình đào tạo an ninh mạng thực chiến cấp cao. Khóa học được thiết kế chuẩn mực 5 chương với 60 bài học chi tiết, tích hợp đầy đủ:
- **Tài liệu gốc đính kèm**: Toàn văn 5 cuốn sách chuyên khảo an ninh mạng nổi tiếng thế giới.
- **Video bài giảng chuẩn 16:9**: Các bài giảng minh họa thực tế từ các chuyên gia hàng đầu.
- **Nội dung lý thuyết và thực hành chuẩn mực**: Mỗi bài học có dung lượng trên 600 từ, đầy đủ kiến trúc, mã nguồn khai thác và khuyến nghị phòng thủ.
- **Miniquiz củng cố từng bài**: Kiểm tra ngay sau bài học với 4 loại câu hỏi (Trắc nghiệm, Đúng/Sai, Điền từ, Nối cặp).
- **Hệ thống đánh giá năng lực**: 5 bài kiểm tra chương (10 câu/bài) và 1 bài thi tốt nghiệp toàn diện (20 câu).

### Cấu trúc 5 Chương học:
1. **Chương 1**: Kiến Trúc Mạng Tor & Định Tuyến Củ Hành (12 bài học + Quiz 1)
2. **Chương 2**: Kỹ Thuật Ẩn Danh, OPSEC & Phòng Thủ Trinh Sát (11 bài học + Quiz 2)
3. **Chương 3**: Phân Tích Mã Độc, Botnet & Thế Giới Ngầm Dark Web (13 bài học + Quiz 3)
4. **Chương 4**: Lập Trình Khai Thác Mũ Đen & Tối Ưu Bộ Nhớ Với Rust (12 bài học + Quiz 4)
5. **Chương 5**: Đánh Giá An Ninh & Tấn Công Khai Thác Hệ Thống GraphQL (12 bài học + Quiz 5)
""",
        category="An toàn thông tin",
        difficulty="ADVANCED",
        owner_instructor_id=instructor.id,
        status="PUBLISHED",
        capacity=200,
        storage_quota_bytes=10 * 1024 * 1024 * 1024,  # 10 GB
        published_at=now,
        approved_at=now,
        approved_by_user_id=admin.id,
    )
    db.session.add(course)
    db.session.flush()

    # Rule completion
    rule = CourseCompletionRule(
        course_id=course.id,
        require_all_required_lessons=True,
        require_required_assessments=True,
        minimum_progress_percent=Decimal("80.00"),
        updated_by_user_id=admin.id,
    )
    db.session.add(rule)
    db.session.flush()

    # Thumbnail
    thumb_buf = create_course_thumbnail()
    thumb_asset = store_file_stream(
        actor=instructor,
        course_id=course.id,
        file_stream=thumb_buf,
        filename="bhe501_course_cover.png",
        content_type="image/png",
        asset_type="RESOURCE",
        title="Bìa Khóa Học BHE501",
    )
    course.thumbnail_file_asset_id = thumb_asset.id
    db.session.flush()

    print(f"  ✓ Đã tạo khóa học: {course.title} (ID: {course.id})")
    return course


def ingest_ebook_assets(instructor, course):
    """Store 5 PDF eBooks as FileAssets."""
    print("[3/8] Tải lên và đăng ký 5 tập tin PDF chuyên khảo chính thức...")
    assets = {}
    titles = {
        1: "Giáo trình Tor Network Architecture & Onion Routing (TOR.pdf)",
        2: "Giáo trình Remain Anonymous & Evade NSA Spying",
        3: "Giáo trình Dissecting the Dark Web & Cybercrime Underground",
        4: "Giáo trình Black Hat Rust: Offensive Exploit Development",
        5: "Giáo trình Black Hat GraphQL: Attack & Defense",
    }

    for ch_idx, file_path in PDF_FILES.items():
        if not file_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file PDF: {file_path}")
        
        file_size = file_path.stat().st_size
        print(f"  - Chương {ch_idx}: {file_path.name} ({file_size / (1024*1024):.2f} MB)")
        with open(file_path, "rb") as f:
            asset = store_file_stream(
                actor=instructor,
                course_id=course.id,
                file_stream=f,
                filename=file_path.name,
                content_type="application/pdf",
                asset_type="RESOURCE",
                title=titles[ch_idx],
            )
            assets[ch_idx] = asset
            print(f"    ✓ FileAsset ID {asset.id} - {asset.display_name}")

    db.session.commit()
    return assets


def seed_learning_units(course):
    """Create 5 LearningUnits."""
    print("[4/8] Khởi tạo 5 Chương học (Learning Units)...")
    units = {}
    unit_titles = {
        1: "Chương 1: Kiến Trúc Mạng Tor & Định Tuyến Củ Hành (The Onion Router Fundamentals)",
        2: "Chương 2: Kỹ Thuật Ẩn Danh, OPSEC & Phòng Thủ Trinh Sát (Anonymity & Surveillance Defense)",
        3: "Chương 3: Phân Tích Mã Độc, Botnet & Thế Giới Ngầm Dark Web (Dissecting the Dark Web)",
        4: "Chương 4: Lập Trình Khai Thác Mũ Đen & Tối Ưu Bộ Nhớ Với Rust (Black Hat Rust Exploit Development)",
        5: "Chương 5: Đánh Giá An Ninh & Tấn Công Khai Thác Hệ Thống GraphQL (Black Hat GraphQL Pentesting)",
    }

    for pos, title in unit_titles.items():
        unit = LearningUnit(
            course_id=course.id,
            title=title,
            position=pos,
        )
        db.session.add(unit)
        db.session.flush()
        units[pos] = unit
        print(f"  ✓ Unit {pos}: {unit.title} (ID: {unit.id})")

    db.session.commit()
    return units


def seed_lessons(instructor, course, units, assets):
    """Seed 60 lessons across 5 chapters and attach resources."""
    print("[5/8] Khởi tạo 60 bài học chi tiết (mỗi bài >= 600 từ, có video, quiz, PDF)...")
    builders = {
        1: get_chapter_1_lessons(),
        2: get_chapter_2_lessons(),
        3: get_chapter_3_lessons(),
        4: get_chapter_4_lessons(),
        5: get_chapter_5_lessons(),
    }

    global_pos = 1
    total_words = 0
    now = utc_now()

    for ch_idx in range(1, 6):
        lessons_data = builders[ch_idx]
        unit = units[ch_idx]
        asset = assets[ch_idx]
        print(f"\n  -- Chương {ch_idx}: {unit.title[:60]}... ({len(lessons_data)} bài) --")

        for l_data in lessons_data:
            wc = count_vietnamese_words(l_data["markdown_content"])
            total_words += wc
            if wc < 600:
                raise ValueError(f"Bài học '{l_data['title']}' không đủ 600 từ ({wc} từ)!")

            lesson = Lesson(
                course_id=course.id,
                learning_unit_id=unit.id,
                title=l_data["title"],
                summary=l_data["summary"],
                markdown_content=l_data["markdown_content"],
                position=global_pos,
                estimated_duration_minutes=45,
                minimum_completion_seconds=30,
                viewed_fraction_required=Decimal("0.8000"),
                status="PUBLISHED",
                published_at=now,
            )
            db.session.add(lesson)
            db.session.flush()

            # Attach chapter eBook PDF resource
            resource = LessonResource(
                lesson_id=lesson.id,
                file_asset_id=asset.id,
                position=1,
                label=f"Tài liệu bài học: {asset.display_name}",
                is_required=False,
            )
            db.session.add(resource)

            print(f"    [{global_pos:02d}/60] {lesson.title[:45]}... | {wc} từ | PDF ID {asset.id}")
            global_pos += 1

        db.session.commit()

    print(f"\n  ✓ Đã tạo thành công {global_pos - 1} bài học. Tổng số từ: {total_words:,} từ (trung bình {total_words // 60} từ/bài).")


def seed_chapter_quizzes(instructor, course):
    """Seed 5 chapter quizzes (10 questions each = 50 questions)."""
    print("[6/8] Khởi tạo 5 Bài kiểm tra đánh giá năng lực theo chương (50 câu hỏi)...")
    quiz_funcs = [
        get_chapter_1_quiz_data,
        get_chapter_2_quiz_data,
        get_chapter_3_quiz_data,
        get_chapter_4_quiz_data,
        get_chapter_5_quiz_data,
    ]

    now = utc_now()

    for ch_idx, fn in enumerate(quiz_funcs, 1):
        qdata = fn()
        assessment = Assessment(
            course_id=course.id,
            creator_user_id=instructor.id,
            title=qdata["title"],
            description=qdata["description"],
            assessment_type=qdata["assessment_type"],
            status="PUBLISHED",
            open_at=now - timedelta(days=1),
            close_at=now + timedelta(days=365),
            time_limit_minutes=qdata["time_limit_minutes"],
            attempt_limit=qdata["attempt_limit"],
            scoring_policy="HIGHEST",
            passing_percent=qdata["passing_percent"],
            is_required_for_completion=True,
            score_release_policy="IMMEDIATE",
            answer_visibility_policy="AFTER_CLOSE",
            exam_layout="STANDARD",
            allow_student_view_results=True,
            monitoring_enabled=True,
            request_fullscreen=False,
            published_at=now,
        )
        db.session.add(assessment)
        db.session.flush()

        section = AssessmentSection(
            assessment_id=assessment.id,
            title="Phần 1: Trắc nghiệm đánh giá kiến thức chuyên môn",
            position=1,
            instructions="Đọc kỹ câu hỏi và chọn đáp án chính xác nhất.",
        )
        db.session.add(section)
        db.session.flush()

        for q_pos, q_info in enumerate(qdata["questions"], 1):
            # Create Question in Bank
            question = Question(
                course_id=course.id,
                creator_user_id=instructor.id,
                difficulty=q_info["difficulty"],
                learning_objective=q_info["learning_objective"],
                status="ACTIVE",
            )
            db.session.add(question)
            db.session.flush()

            # Create QuestionRevision
            rev = QuestionRevision(
                question_id=question.id,
                revision_no=1,
                is_current=True,
                question_type=q_info["question_type"],
                content=q_info["content"],
                explanation=q_info["explanation"],
                change_type="INITIAL",
            )
            db.session.add(rev)
            db.session.flush()

            # Choices
            for c_info in q_info["choices"]:
                choice = QuestionRevisionChoice(
                    question_revision_id=rev.id,
                    choice_key=uuid.uuid4(),
                    content=c_info["content"],
                    is_correct=c_info["is_correct"],
                    position=c_info["position"],
                )
                db.session.add(choice)

            # Assignment to Assessment
            assign = AssessmentQuestionAssignment(
                assessment_id=assessment.id,
                section_id=section.id,
                question_id=question.id,
                position=q_pos,
                points=qdata["points_per_question"],
                is_mandatory=True,
                source_type="BANK",
            )
            db.session.add(assign)

        db.session.commit()
        print(f"  ✓ Bài kiểm tra Chương {ch_idx}: {assessment.title[:50]}... (10 câu, 100 điểm)")


def seed_final_exam(instructor, course):
    """Seed Final Comprehensive Exam (20 questions = 100 points)."""
    print("[7/8] Khởi tạo Bài thi tốt nghiệp toàn diện 20 câu hỏi (Final Exam)...")
    fdata = get_final_exam_data()
    now = utc_now()

    assessment = Assessment(
        course_id=course.id,
        creator_user_id=instructor.id,
        title=fdata["title"],
        description=fdata["description"],
        assessment_type=fdata["assessment_type"],
        status="PUBLISHED",
        open_at=now - timedelta(days=1),
        close_at=now + timedelta(days=365),
        time_limit_minutes=fdata["time_limit_minutes"],
        attempt_limit=fdata["attempt_limit"],
        scoring_policy="HIGHEST",
        passing_percent=fdata["passing_percent"],
        is_required_for_completion=True,
        score_release_policy="IMMEDIATE",
        answer_visibility_policy="AFTER_CLOSE",
        exam_layout="STANDARD",
        allow_student_view_results=True,
        monitoring_enabled=True,
        request_fullscreen=True,
        published_at=now,
    )
    db.session.add(assessment)
    db.session.flush()

    section = AssessmentSection(
        assessment_id=assessment.id,
        title="Phần 1: Bài thi trắc nghiệm tốt nghiệp 20 câu hỏi tổng hợp",
        position=1,
        instructions="Bài thi bao quát kiến thức từ Chương 1 đến Chương 5. Mỗi câu hỏi đúng được tính 5.00 điểm. Tổng điểm tối đa 100.00 điểm.",
    )
    db.session.add(section)
    db.session.flush()

    for q_pos, q_info in enumerate(fdata["questions"], 1):
        # Create Question in Bank
        question = Question(
            course_id=course.id,
            creator_user_id=instructor.id,
            difficulty=q_info["difficulty"],
            learning_objective=q_info["learning_objective"],
            status="ACTIVE",
        )
        db.session.add(question)
        db.session.flush()

        # Create QuestionRevision
        rev = QuestionRevision(
            question_id=question.id,
            revision_no=1,
            is_current=True,
            question_type=q_info["question_type"],
            content=q_info["content"],
            explanation=q_info["explanation"],
            change_type="INITIAL",
        )
        db.session.add(rev)
        db.session.flush()

        # Choices
        for c_info in q_info["choices"]:
            choice = QuestionRevisionChoice(
                question_revision_id=rev.id,
                choice_key=uuid.uuid4(),
                content=c_info["content"],
                is_correct=c_info["is_correct"],
                position=c_info["position"],
            )
            db.session.add(choice)

        # Assignment to Assessment (5.00 points each)
        assign = AssessmentQuestionAssignment(
            assessment_id=assessment.id,
            section_id=section.id,
            question_id=question.id,
            position=q_pos,
            points=fdata["points_per_question"],
            is_mandatory=True,
            source_type="BANK",
        )
        db.session.add(assign)

    db.session.commit()
    print(f"  ✓ Bài thi tốt nghiệp: {assessment.title} (20 câu hỏi, 100 điểm)")


def seed_enrollments(admin, course, student1, student2):
    """Enroll students into the course."""
    print("[8/8] Ghi danh sinh viên vào khóa học BHE501...")
    e1 = enroll_student(actor=admin, course_id=course.id, student_id=student1.id)
    e2 = enroll_student(actor=admin, course_id=course.id, student_id=student2.id)
    print(f"  ✓ Đã ghi danh {student1.display_name} (Enrollment ID: {e1.id})")
    print(f"  ✓ Đã ghi danh {student2.display_name} (Enrollment ID: {e2.id})")
    db.session.commit()


def main():
    print("=" * 80)
    print("BẮT ĐẦU QUY TRÌNH KHỞI TẠO KHÓA HỌC AN NINH MẠNG MŨ ĐEN (BHE501)")
    print("Dựa trên 5 eBook tại F:\\cyber\\khóa học all\\Blackhat EBooks")
    print("=" * 80)

    app = create_app()
    with app.app_context():
        # 1. Users
        admin, instructor, student1, student2 = ensure_users()

        # 2. Course
        course = seed_course(admin, instructor)

        # 3. eBooks FileAssets
        assets = ingest_ebook_assets(instructor, course)

        # 4. Learning Units
        units = seed_learning_units(course)

        # 5. Lessons with videos, quizzes, PDF attachments
        seed_lessons(instructor, course, units, assets)

        # 6. Chapter Quizzes
        seed_chapter_quizzes(instructor, course)

        # 7. Final Exam (20 questions)
        seed_final_exam(instructor, course)

        # 8. Enrollments
        seed_enrollments(admin, course, student1, student2)

    print("\n" + "=" * 80)
    print("HOÀN TẤT THÀNH CÔNG 100% QUY TRÌNH KHỞI TẠO KHÓA HỌC BHE501!")
    print("=" * 80)


if __name__ == "__main__":
    main()
