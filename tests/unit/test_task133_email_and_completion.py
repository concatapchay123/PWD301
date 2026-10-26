"""Unit & Integration tests for TASK-133:
1. Role-aware enterprise email greetings (Student, Instructor, Admin - never grouping all 3).
2. Corporate email templates (Course Enrollment Success & Course Completion Certificate).
3. 100 Email/day Quota Filter (Only allowing the 2 critical learning transactions to enqueue/send email).
4. Course Completion Strict Gating (Rejecting completion if lessons incomplete or assessments not passed).
5. Certificate Endpoint Safety (400 when requirements not met, valid PDF when met).
"""

from __future__ import annotations

import datetime
from decimal import Decimal
import pytest
from flask import Flask

from backend import create_app
from backend.extensions import db
from backend.models.identity import User
from backend.models.course import Course, Enrollment, Lesson, LessonProgress, EnrollmentPeriod
from backend.models.assessment import Assessment
from backend.models.attempt_regrade import AssessmentAttempt, AssessmentResult
from backend.services.email_service import (
    get_role_aware_greeting,
    render_course_enrollment_email,
    render_course_completion_email,
    render_corporate_email_template,
)
from backend.services.notification_service import dispatch_notification
from backend.services.completion_service import (
    calculate_course_progress,
    evaluate_course_completion,
)


@pytest.fixture(scope="module")
def app():
    app = create_app("development")
    with app.app_context():
        yield app


def test_role_aware_greetings():
    """Verify that greetings address the exact recipient role and never group all three."""
    # Student
    g_student = get_role_aware_greeting("Nguyễn Văn A", "STUDENT")
    assert "Kính gửi <strong>Nguyễn Văn A</strong>," in g_student
    assert "Quý Thầy/Cô" not in g_student

    # Instructor
    g_instructor = get_role_aware_greeting("Trần Thị B", "INSTRUCTOR")
    assert "Kính gửi Thầy/Cô <strong>Trần Thị B</strong>," in g_instructor
    assert "Học viên" not in g_instructor

    # Admin
    g_admin = get_role_aware_greeting("Lê Văn C", "ADMIN")
    assert "Kính gửi Quản trị viên <strong>Lê Văn C</strong>," in g_admin
    assert "Quý Thầy/Cô" not in g_admin

    # Fallback when name is empty
    g_fallback = get_role_aware_greeting(None, "STUDENT")
    assert "Kính gửi <strong>Học viên</strong>," in g_fallback
    assert "Quý Thầy/Cô" not in g_fallback


def test_render_course_enrollment_email():
    """Verify official enterprise course enrollment email contains all required sections and branding."""
    html_output = render_course_enrollment_email(
        recipient_name="Hoàng Phúc",
        course_title="Lập Trình An Ninh Android Chuyên Sâu",
        course_code="AND801",
        enrolled_date="24/10/2026",
        action_url="https://pptq.id.vn/#/student/courses/detail?id=and801",
    )
    # Check title & greeting
    assert "ĐĂNG KÝ KHÓA HỌC THÀNH CÔNG" in html_output
    assert "Kính gửi Hoàng Phúc," in html_output
    assert "PPTQ EDUCATION" in html_output
    assert "Chúng tôi rất vui khi được đồng hành cùng bạn" in html_output

    # Check course details table
    assert "Lập Trình An Ninh Android Chuyên Sâu" in html_output
    assert "AND801" in html_output
    assert "24/10/2026" in html_output
    assert "Đăng ký thành công" in html_output

    # Check CTA button & support details
    assert "TRUY CẬP KHÓA HỌC" in html_output
    assert "https://pptq.id.vn/#/student/courses/detail?id=and801" in html_output
    assert "support@pptq.id.vn" in html_output
    assert "0908.667.141" in html_output
    assert "PPTQ-SECURE-MAIL" in html_output
    assert "*Đây là email được gửi tự động từ hệ thống. Vui lòng không trả lời trực tiếp email này.*" in html_output


def test_render_course_completion_email():
    """Verify official enterprise course completion email contains all required sections and branding."""
    html_output = render_course_completion_email(
        recipient_name="Hoàng Phúc",
        course_title="Lập Trình An Ninh Android Chuyên Sâu",
        course_code="AND801",
        completed_date="24/10/2026",
        result_url="https://pptq.id.vn/#/student/courses/detail?id=and801",
        certificate_url="https://pptq.id.vn/api/student/courses/and801/certificate",
        catalog_url="https://pptq.id.vn/#/student/courses/catalog",
    )
    # Check title & greeting
    assert "CHÚC MỪNG BẠN ĐÃ HOÀN THÀNH KHÓA HỌC!" in html_output
    assert "Kính gửi Hoàng Phúc," in html_output
    assert "PPTQ EDUCATION" in html_output
    assert "đã hoàn thành chương trình học tập của khóa học" in html_output

    # Check completion details
    assert "Lập Trình An Ninh Android Chuyên Sâu" in html_output
    assert "AND801" in html_output
    assert "100%" in html_output
    assert "Hoàn thành" in html_output

    # Check CTAs are completely removed per user request
    assert "XEM KẾT QUẢ HỌC TẬP" not in html_output
    assert "XEM CHỨNG CHỈ" not in html_output
    assert "KHÁM PHÁ KHÓA HỌC MỚI" not in html_output
    assert "support@pptq.id.vn" in html_output
    assert "PPTQ-SECURE-MAIL" in html_output
    assert "*Đây là email được gửi tự động từ hệ thống. Vui lòng không trả lời trực tiếp email này.*" in html_output


def test_email_quota_filter(app):
    """Verify that only the 2 learning events enqueue an outbound email, while other events only create in-app notifications."""
    with app.app_context():
        user = db.session.get(User, 3)
        assert user is not None, "User 3 must exist in DB"

        # 1. Non-essential event: e.g. LESSON_COMMENT or SYSTEM_ANNOUNCEMENT
        # Should create Notification (in-app) but NOT EmailDelivery
        notif1, delivery1 = dispatch_notification(
            recipient_user=user.id,
            event_type="LESSON_COMMENT",
            title="Bình luận mới trong bài giảng",
            body="Một học viên khác đã phản hồi câu hỏi của bạn.",
            target_role="STUDENT",
            session=db.session,
        )
        assert notif1 is not None
        assert delivery1 is None, "Non-essential event must NOT enqueue email to preserve 100 email/day quota"

        # 2. Instructor notification for STUDENT_ENROLLED
        # Instructor should get in-app notification only, not consume student email quota
        notif2, delivery2 = dispatch_notification(
            recipient_user=user.id,
            event_type="STUDENT_ENROLLED",
            title="Học viên mới tham gia",
            body="Học viên mới vừa tham gia khóa học.",
            target_role="INSTRUCTOR",
            session=db.session,
        )
        assert notif2 is not None
        assert delivery2 is None, "Instructor notification must NOT enqueue email"

        # 3. Essential learning milestone: STUDENT_ENROLLED for STUDENT
        notif3, delivery3 = dispatch_notification(
            recipient_user=user.id,
            event_type="STUDENT_ENROLLED",
            title="Đăng ký khóa học thành công",
            body="Bạn đã đăng ký thành công khóa học 'Test Course'. Bắt đầu học ngay hôm nay!",
            target_role="STUDENT",
            session=db.session,
        )
        assert notif3 is not None
        assert delivery3 is not None, "STUDENT_ENROLLED for student must enqueue email"

        # 4. Essential learning milestone: COURSE_COMPLETED for STUDENT
        notif4, delivery4 = dispatch_notification(
            recipient_user=user.id,
            event_type="COURSE_COMPLETED",
            title="Chúc mừng bạn đã hoàn thành khóa học!",
            body="Hệ thống PPTQ trân trọng thông báo bạn đã hoàn thành khóa học 'Test Course'.",
            target_role="STUDENT",
            session=db.session,
        )
        assert notif4 is not None
        assert delivery4 is not None, "COURSE_COMPLETED for student must enqueue email"


def test_completion_evaluation_strict_gating(app):
    """Verify that an enrollment with incomplete lessons or uncompleted assessments cannot be COMPLETED."""
    with app.app_context():
        from backend.models.course import LearningUnit
        c = db.session.query(Course).filter_by(course_code="AND801").first()
        if c is None:
            from backend.models.identity import User
            user = db.session.query(User).filter_by(id=3).first()
            if not user:
                user = User(id=3, email="test_student3@example.com", full_name="Hoàng Phúc", is_active=True)
                db.session.add(user)
                db.session.flush()
            c = Course(course_code="AND801", title="Android Development", status="PUBLISHED", price=0)
            db.session.add(c)
            db.session.flush()
            unit = LearningUnit(course_id=c.id, title="Unit 1", position=1)
            db.session.add(unit)
            db.session.flush()
            les = Lesson(course_id=c.id, learning_unit_id=unit.id, title="Lesson 1", status="PUBLISHED", position=1)
            db.session.add(les)
            db.session.flush()
            enr = Enrollment(student_user_id=user.id, course_id=c.id, status="ACTIVE", current_progress_percent=0.0)
            db.session.add(enr)
            db.session.commit()
        else:
            enr = db.session.query(Enrollment).filter_by(student_user_id=3, course_id=c.id).first()
            assert enr is not None, "User 3 enrollment in AND801 must exist"
            if enr.current_period_id:
                db.session.query(LessonProgress).filter_by(enrollment_period_id=enr.current_period_id).delete()
            enr.status = "ACTIVE"
            enr.completed_at = None
            enr.current_progress_percent = 0.0
            if enr.current_period:
                enr.current_period.status = "ACTIVE"
                enr.current_period.completed_at = None
            from backend.models.course import CourseCompletionSummary
            db.session.query(CourseCompletionSummary).filter_by(student_user_id=3, course_id=c.id).delete()
            db.session.commit()

        # Evaluate completion
        is_completed, summary = evaluate_course_completion(enr.id, session=db.session)
        assert is_completed is False, "Course with 0 completed lessons must NOT be marked COMPLETED"
        assert enr.status == "ACTIVE", "Enrollment status must remain ACTIVE"
        assert float(enr.current_progress_percent) < 100.0, "Progress must be less than 100%"


def test_certificate_api_safety(app):
    """Verify that attempting to fetch certificate for an incomplete course returns 400 CERTIFICATE_NOT_AVAILABLE."""
    with app.app_context():
        from backend.models.course import LearningUnit
        from backend.models.identity import Role, User
        from backend.services.user_service import generate_pptq_password_hash
        c = db.session.query(Course).filter_by(course_code="AND801").first()
        if c is None:
            c = Course(course_code="AND801", title="Android Development", status="PUBLISHED", price=0)
            db.session.add(c)
            db.session.flush()
            unit = LearningUnit(course_id=c.id, title="Unit 1", position=1)
            db.session.add(unit)
            db.session.flush()
            les = Lesson(course_id=c.id, learning_unit_id=unit.id, title="Lesson 1", status="PUBLISHED", position=1)
            db.session.add(les)
            db.session.flush()
            db.session.commit()

        email = "tqtphamnguyenhoangphuc@gmail.com"
        u = db.session.query(User).filter_by(email=email).first()
        if not u:
            u = User(email=email, full_name="Hoàng Phúc", is_active=True, password_hash=generate_pptq_password_hash("Password123!"))
            student_role = db.session.query(Role).filter_by(role_name="STUDENT").first()
            if student_role:
                u.roles.append(student_role)
            db.session.add(u)
            db.session.flush()
            enr = Enrollment(student_user_id=u.id, course_id=c.id, status="ACTIVE", current_progress_percent=0.0)
            db.session.add(enr)
            db.session.commit()
        else:
            u.password_hash = generate_pptq_password_hash("Password123!")
            enr = db.session.query(Enrollment).filter_by(student_user_id=u.id, course_id=c.id).first()
            if not enr:
                enr = Enrollment(student_user_id=u.id, course_id=c.id, status="ACTIVE", current_progress_percent=0.0)
                db.session.add(enr)
            else:
                if enr.current_period_id:
                    db.session.query(LessonProgress).filter_by(enrollment_period_id=enr.current_period_id).delete()
                enr.status = "ACTIVE"
                enr.completed_at = None
                enr.current_progress_percent = 0.0
                if enr.current_period:
                    enr.current_period.status = "ACTIVE"
                    enr.current_period.completed_at = None
                from backend.models.course import CourseCompletionSummary
                db.session.query(CourseCompletionSummary).filter_by(student_user_id=u.id, course_id=c.id).delete()
            db.session.commit()

        course_id = c.id

    with app.test_client() as client:
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "tqtphamnguyenhoangphuc@gmail.com", "password": "Password123!"},
        )
        assert login_resp.status_code == 200
        data = login_resp.json.get("data") or login_resp.json
        token = data.get("access_token")
        assert token

        cert_resp = client.get(
            f"/student/courses/{course_id}/certificate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert cert_resp.status_code == 400
        assert cert_resp.json["error"]["code"] == "CERTIFICATE_NOT_AVAILABLE"
        assert "chưa hoàn thành đủ bài học" in cert_resp.json["error"]["message"]
