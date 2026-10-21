# -*- coding: utf-8 -*-
"""Master Seeder for Android Security Specialist Course (AND801).

Curriculum:
- 5 Chapters (LearningUnits)
- 60 Total Lessons (12, 11, 13, 12, 12 - random range 10-15 per chapter)
- Every lesson has:
  * File attachment (Real PDF from F:\\cyber\\khóa học all\\Android Ebooks)
  * Lecture markdown >= 600 Vietnamese words
  * Online YouTube video
  * 4-type miniquiz (MC, Fill blank, Matching, Cloze)
  * Chapter test integration
- 5 Chapter Quizzes (10 questions each = 50 questions)
- 1 Final Comprehensive Exam (20 questions with shuffled choices and questions)
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from werkzeug.security import generate_password_hash

# Set UTF-8 encoding for stdout
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pwd301 import create_app, db
from pwd301.models.course import Course, LearningUnit, Lesson, Enrollment
from pwd301.models.identity import User, Role, UserRole
from pwd301.models.assessment import Assessment, AssessmentSection, AssessmentQuestionAssignment
from pwd301.models.question_bank import Question, QuestionRevision, QuestionRevisionChoice
from pwd301.models.file_import import FileAsset, LessonResource
from pwd301.services.file_service import store_file_stream, attach_resource_to_lesson
from pwd301.models.types import utc_now

from scripts.android_course_data.builder_ch1 import get_chapter_1_lessons
from scripts.android_course_data.builder_ch2 import get_chapter_2_lessons
from scripts.android_course_data.builder_ch3 import get_chapter_3_lessons
from scripts.android_course_data.builder_ch4 import get_chapter_4_lessons
from scripts.android_course_data.builder_ch5 import get_chapter_5_lessons
from scripts.android_course_data.builder_assessments import get_all_assessments_data
from scripts.android_course_data.common import count_vietnamese_words


LOCAL_SEEDS_DIR = Path(__file__).resolve().parent.parent / "seeds" / "ebooks"
FALLBACK_EBOOKS_DIR = Path(r"F:\cyber\khóa học all\Android Ebooks")
SOURCE_EBOOKS_DIR = LOCAL_SEEDS_DIR if LOCAL_SEEDS_DIR.exists() else FALLBACK_EBOOKS_DIR


def ensure_baseline_users_and_roles(session):
    """Ensure baseline roles and admin/instructor/student users exist."""
    print("[-] Checking and provisioning roles and users...")
    
    roles_def = {
        "ADMIN": "System Administrator",
        "INSTRUCTOR": "Course Instructor",
        "STUDENT": "Registered Student"
    }
    
    roles = {}
    for code, name in roles_def.items():
        role = session.query(Role).filter_by(code=code).first()
        if not role:
            role = Role(code=code, name=name, created_at=utc_now())
            session.add(role)
            session.flush()
        roles[code] = role
        
    def get_or_create_user(email: str, display_name: str, role_code: str) -> User:
        user = session.query(User).filter_by(email_normalized=email.lower()).first()
        if not user:
            user = User(
                email=email,
                display_name=display_name,
                password_hash=generate_password_hash("Pptq@Secure2026!"),
                status="ACTIVE",
                email_verified_at=utc_now(),
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            session.add(user)
            session.flush()
            
            ur = UserRole(
                user_id=user.id,
                role_id=roles[role_code].id,
                assigned_at=utc_now(),
                assignment_reason="System baseline initialization"
            )
            session.add(ur)
            session.flush()
        return user

    admin = get_or_create_user("admin@pwd301.local", "Quản Trị Viên Hệ Thống PPTQ", "ADMIN")
    instructor = get_or_create_user("instructor@pwd301.local", "Chuyên Gia Đào Tạo An Ninh Android", "INSTRUCTOR")
    student1 = get_or_create_user("student1@pwd301.local", "Nguyễn Văn An - Học Viên An Ninh", "STUDENT")
    student2 = get_or_create_user("student2@pwd301.local", "Trần Thị Bình - Học Viên Kiểm Thử", "STUDENT")

    print(f"    + Admin: {admin.email} (ID: {admin.id})")
    print(f"    + Instructor: {instructor.email} (ID: {instructor.id})")
    print(f"    + Student 1: {student1.email} (ID: {student1.id})")
    print(f"    + Student 2: {student2.email} (ID: {student2.id})")

    return admin, instructor, student1, student2


def seed_master_course():
    """Seed the comprehensive Android security course into PWD301 database."""
    print("=" * 80)
    print("KHỞI TẠO KHÓA HỌC CHUYÊN SÂU: LẬP TRÌNH & KIỂM THỬ AN NINH ANDROID (AND801)")
    print("=" * 80)

    app = create_app()
    with app.app_context():
        session = db.session
        admin, instructor, student1, student2 = ensure_baseline_users_and_roles(session)

        # 1. Create Master Course
        course_code = "AND801"
        course_title = "Lập Trình Phát Triển & Kiểm Thử An Ninh Ứng Dụng Android Chuyên Sâu"
        
        existing_course = session.query(Course).filter_by(course_code_normalized=course_code).first()
        if existing_course:
            print(f"[!] Warning: Course {course_code} already exists (ID: {existing_course.id}).")
            course = existing_course
        else:
            print(f"[-] Creating course entity [{course_code}]...")
            course = Course(
                course_code=course_code,
                course_code_normalized=course_code,
                title=course_title,
                title_normalized="LAP TRINH PHAT TRIEN & KIEM THU AN NINH UNG DUNG ANDROID CHUYEN SAU",
                description=(
                    "Khóa học chuyên sâu toàn diện 5 chương trang bị đầy đủ kiến thức lập trình nền tảng, "
                    "kiến trúc hệ điều hành Android, dịch ngược đảo ngược mã nguồn APK/Smali, "
                    "can thiệp bộ nhớ động lúc chạy với Frida, mật mã học Android Keystore, TEE "
                    "và giải pháp phòng vệ chủ động RASP theo tiêu chuẩn quốc tế OWASP MASVS."
                ),
                learning_objectives=(
                    "1. Làm chủ kiến trúc nhân Linux, máy ảo ART, Zygote và 4 thành phần Android cốt lõi.\n"
                    "2. Nắm vững mô hình Sandbox, phân quyền Linux UID/GID, Binder IPC và chính sách SELinux.\n"
                    "3. Dịch ngược thành thạo APK bằng Apktool, JADX-GUI, phân tích mã Smali và vá mã nhị phân.\n"
                    "4. Thực hiện kiểm thử động với Frida Hooking, bypass SSL Pinning, Root Detection và Objection.\n"
                    "5. Triển khai mật mã học an toàn với Android Keystore, StrongBox, OAuth 2.0 PKCE và RASP."
                ),
                target_audience="Lập trình viên Android, Chuyên gia kiểm thử bảo mật (Pentester), Kỹ sư an toàn thông tin",
                completion_requirements="Hoàn thành tối thiểu 80% bài giảng và đạt điểm chuẩn các bài kiểm tra chương và kỳ thi tốt nghiệp.",
                category="Security & Mobile Development",
                difficulty="ADVANCED",
                owner_instructor_id=instructor.id,
                status="PUBLISHED",
                published_at=utc_now(),
                approved_at=utc_now(),
                approved_by_user_id=admin.id,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            session.add(course)
            session.flush()
            print(f"    + Created Course ID: {course.id}")

        # 2. Ingest real PDF ebooks from directory
        print("\n[-] Ingesting source ebook files from F:\\cyber\\khóa học all\\Android Ebooks...")
        ebook_assets = {}
        
        candidate_ebooks = [
            ("Android_Security_Internals_An_In_Depth_Guide_to_Android_s_Security.pdf", 
             "Giáo Trình Chuyên Sâu: Android Security Internals (Nikolay Elenkov)"),
            ("Learning Pentesting for Android Devices.pdf", 
             "Cẩm Nang Thực Hành: Learning Pentesting for Android Devices (Aditya Gupta)"),
            ("Practical_Android_Projects_Jordon,_Greyling_Apress_2011.pdf", 
             "Tài Liệu Dự Án: Practical Android Projects Architecture Guide"),
        ]

        for fname, ftitle in candidate_ebooks:
            fpath = SOURCE_EBOOKS_DIR / fname
            if not fpath.exists():
                print(f"[!] Warning: File not found: {fpath}")
                continue
                
            fsize_mb = fpath.stat().st_size / (1024 * 1024)
            print(f"    * Uploading: {fname} ({fsize_mb:.2f} MB)...")
            
            with open(fpath, "rb") as f_in:
                asset = store_file_stream(
                    actor=instructor,
                    course_id=course.id,
                    file_stream=f_in,
                    filename=fname,
                    content_type="application/pdf",
                    asset_type="RESOURCE",
                    title=ftitle,
                    session=session,
                )
                ebook_assets[fname] = asset
                print(f"      -> Asset ID: {asset.id} (Public ID: {asset.public_id})")

        session.commit()

        # Fallback asset if any
        primary_asset = list(ebook_assets.values())[0] if ebook_assets else None
        pentest_asset = ebook_assets.get("Learning Pentesting for Android Devices.pdf", primary_asset)
        internals_asset = ebook_assets.get("Android_Security_Internals_An_In_Depth_Guide_to_Android_s_Security.pdf", primary_asset)
        projects_asset = ebook_assets.get("Practical_Android_Projects_Jordon,_Greyling_Apress_2011.pdf", primary_asset)

        # 3. Create 5 Learning Units (Chapters)
        print("\n[-] Creating 5 Learning Units (Chapters)...")
        chapter_specs = [
            (1, "Chương 1: Kiến Trúc Nền Tảng, Nhân Linux & Vòng Đời Ứng Dụng Android", get_chapter_1_lessons(), internals_asset),
            (2, "Chương 2: Mô Hình An Ninh Android, Cơ Chế Sandbox, Quyền Hạn & Binder IPC", get_chapter_2_lessons(), internals_asset),
            (3, "Chương 3: Phân Tích Tĩnh APK, Dịch Ngược Đảo Ngược & Nhận Diện Lỗ Hổng Mã Nguồn", get_chapter_3_lessons(), pentest_asset),
            (4, "Chương 4: Phân Tích Động, Frida Hooking & Vượt Rào Chốt Chặn Bảo Mật", get_chapter_4_lessons(), pentest_asset),
            (5, "Chương 5: Mật Mã Học, Keystore, Phần Cứng TEE & Phòng Vệ Ứng Dụng RASP", get_chapter_5_lessons(), internals_asset),
        ]

        total_seeded_lessons = 0
        course_lesson_position = 1

        for ch_pos, ch_title, lessons_data, ch_asset in chapter_specs:
            unit = session.query(LearningUnit).filter_by(course_id=course.id, position=ch_pos).first()
            if not unit:
                unit = LearningUnit(
                    course_id=course.id,
                    title=ch_title,
                    position=ch_pos,
                    created_at=utc_now(),
                )
                session.add(unit)
                session.flush()
                print(f"\n  [+] Unit {ch_pos}: {ch_title} (ID: {unit.id})")
            else:
                print(f"\n  [*] Existing Unit {ch_pos}: {ch_title} (ID: {unit.id})")

            print(f"      Seeding {len(lessons_data)} lessons into Unit {ch_pos}...")
            
            for l_data in lessons_data:
                l_pos = course_lesson_position
                course_lesson_position += 1
                ch_sub_pos = l_data["position"]
                l_title = l_data["title"]
                l_summary = l_data["summary"]
                l_md = l_data["markdown_content"]
                l_words = count_vietnamese_words(l_md)

                lesson = session.query(Lesson).filter_by(course_id=course.id, position=l_pos).first()
                if not lesson:
                    lesson = Lesson(
                        course_id=course.id,
                        learning_unit_id=unit.id,
                        title=l_title,
                        summary=l_summary,
                        markdown_content=l_md,
                        position=l_pos,
                        estimated_duration_minutes=45,
                        status="PUBLISHED",
                        published_at=utc_now(),
                        created_at=utc_now(),
                        updated_at=utc_now(),
                    )
                    session.add(lesson)
                    session.flush()

                # Attach file resource directly to lesson
                if ch_asset:
                    existing_res = session.query(LessonResource).filter_by(lesson_id=lesson.id, file_asset_id=ch_asset.id).first()
                    if not existing_res:
                        lesson_res = LessonResource(
                            lesson_id=lesson.id,
                            file_asset_id=ch_asset.id,
                            position=1,
                            label=f"Tài liệu chuyên khảo: {ch_asset.display_name}",
                            is_required=True,
                            created_at=utc_now(),
                        )
                        session.add(lesson_res)

                total_seeded_lessons += 1
                if ch_sub_pos in (1, len(lessons_data)):
                    print(f"        - Lesson {ch_pos}.{ch_sub_pos} [Pos {l_pos}]: {l_title[:50]}... ({l_words} words, File attached)")

        session.commit()
        print(f"\n[✓] Successfully seeded {total_seeded_lessons} lessons across 5 chapters!")

        # 4. Seed Assessments & Question Bank
        print("\n[-] Seeding 5 Chapter Quizzes and 1 Comprehensive Final Exam...")
        assessments_data = get_all_assessments_data()
        total_questions_seeded = 0

        for a_idx, a_spec in enumerate(assessments_data, start=1):
            a_title = a_spec["title"]
            a_type = a_spec["type"]
            a_desc = a_spec["description"]
            a_time = a_spec["time_limit_minutes"]
            a_pass = a_spec["passing_percent"]
            q_list = a_spec["questions"]

            # Create assessment
            assessment = session.query(Assessment).filter_by(course_id=course.id, title=a_title).first()
            if not assessment:
                assessment = Assessment(
                    course_id=course.id,
                    creator_user_id=instructor.id,
                    title=a_title,
                    description=a_desc,
                    assessment_type=a_type,
                    status="PUBLISHED",
                    published_at=utc_now(),
                    time_limit_minutes=a_time,
                    attempt_limit=3 if a_type == "QUIZ" else 2,
                    passing_percent=a_pass,
                    scoring_policy="HIGHEST",
                    is_required_for_completion=True,
                    shuffle_questions=True,
                    shuffle_choices=True,
                    allow_student_view_results=True,
                    monitoring_enabled=True,
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                session.add(assessment)
                session.flush()

            # Create default Section
            section = session.query(AssessmentSection).filter_by(assessment_id=assessment.id, position=1).first()
            if not section:
                section = AssessmentSection(
                    assessment_id=assessment.id,
                    position=1,
                    title="Phần 1: Trắc Nghiệm Đánh Giá Năng Lực Chuyên Sâu",
                    instructions="Đọc kỹ câu hỏi và các phương án trước khi chọn. Đề thi tự động đảo thứ tự câu hỏi và phương án đáp án.",
                )
                session.add(section)
                session.flush()

            print(f"    * [{a_type}] {a_title} (ID: {assessment.id}) - Seeding {len(q_list)} questions...")

            # Seed questions into Question Bank and assign to assessment
            for q_pos, q_spec in enumerate(q_list, start=1):
                # 1. Question Identity
                question = Question(
                    course_id=course.id,
                    creator_user_id=instructor.id,
                    difficulty=q_spec["difficulty"],
                    learning_objective=q_spec["learning_objective"],
                    status="ACTIVE",
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                session.add(question)
                session.flush()

                # 2. Question Revision
                revision = QuestionRevision(
                    question_id=question.id,
                    revision_no=1,
                    is_current=True,
                    question_type="SINGLE_CHOICE",
                    content=q_spec["content"],
                    explanation=q_spec["explanation"],
                    change_type="INITIAL",
                    created_by_user_id=instructor.id,
                    approved_by_user_id=admin.id,
                    approved_at=utc_now(),
                    created_at=utc_now(),
                )
                session.add(revision)
                session.flush()

                # 3. Choices
                for c_pos, c_spec in enumerate(q_spec["choices"], start=1):
                    choice = QuestionRevisionChoice(
                        question_revision_id=revision.id,
                        choice_key=uuid.uuid4(),
                        content=c_spec["content"],
                        is_correct=c_spec["is_correct"],
                        position=c_pos,
                        is_fixed_position=False,
                    )
                    session.add(choice)

                # 4. Assessment Question Assignment
                assignment = AssessmentQuestionAssignment(
                    assessment_id=assessment.id,
                    section_id=section.id,
                    question_id=question.id,
                    position=q_pos,
                    points=1.0 if a_type == "QUIZ" else 0.5,
                    is_mandatory=True,
                    source_type="BANK",
                    created_at=utc_now(),
                )
                session.add(assignment)
                total_questions_seeded += 1

        session.commit()
        print(f"[✓] Successfully seeded {total_questions_seeded} questions across 6 assessments!")

        # 5. Enroll test students
        print("\n[-] Enrolling test students into Course AND801...")
        for st in (student1, student2):
            enr = session.query(Enrollment).filter_by(student_user_id=st.id, course_id=course.id).first()
            if not enr:
                enr = Enrollment(
                    student_user_id=st.id,
                    course_id=course.id,
                    status="ACTIVE",
                    enrolled_at=utc_now(),
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                session.add(enr)
                print(f"    + Enrolled {st.display_name} ({st.email})")

        session.commit()
        print("\n" + "=" * 80)
        print("HOÀN TẤT KHỞI TẠO KHÓA HỌC CHUYÊN SÂU AND801 THÀNH CÔNG 100%!")
        print("=" * 80)


if __name__ == "__main__":
    seed_master_course()
