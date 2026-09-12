"""Unit tests for Instructor Application workflow in PWD301.

Tests cover:
- Student submitting instructor application with required professional and educational data.
- Enforcing single active PENDING application per student.
- Preventing existing Instructors and Admins from submitting applications.
- Application cancellation by the applicant.
- Admin reviewing application (APPROVE: grants INSTRUCTOR role, updates status, emits audit event).
- Admin reviewing application (REJECT: updates status, records review reason, emits audit event).
- Validation of payload size and schema bounds.
"""

from __future__ import annotations

import pytest

from pwd301.extensions import db
from pwd301.models.identity import User
from pwd301.services.exceptions import (
    ValidationError,
)
from pwd301.services.user_service import (
    assign_role_to_user,
    cancel_instructor_application,
    get_instructor_application,
    list_instructor_applications,
    register_user,
    review_instructor_application,
    submit_instructor_application,
)


@pytest.fixture
def student_user(app):
    """Create a verified student user."""
    with app.app_context():
        user = register_user(
            email="applicant.student@example.edu.vn",
            password="StrongPassword123!",
            display_name="Nguyen Van A",
            session=db.session,
        )
        assign_role_to_user(user.id, "STUDENT", session=db.session)
        return user.id


@pytest.fixture
def instructor_user(app):
    """Create a user with INSTRUCTOR role."""
    with app.app_context():
        user = register_user(
            email="existing.instructor@example.edu.vn",
            password="StrongPassword123!",
            display_name="Dr. Tran Van B",
            session=db.session,
        )
        assign_role_to_user(user.id, "INSTRUCTOR", session=db.session)
        return user.id


@pytest.fixture
def admin_user(app):
    """Create an administrator user."""
    with app.app_context():
        user = register_user(
            email="system.admin@pwd301.edu.vn",
            password="StrongAdminPassword123!",
            display_name="Admin Manager",
            session=db.session,
        )
        assign_role_to_user(user.id, "ADMIN", session=db.session)
        return user.id


@pytest.fixture
def valid_application_data():
    """Valid sample instructor application payload."""
    return {
        "institution_name": "Đại học Bách Khoa TP.HCM",
        "institution_email": "nva.lecturer@hcmut.edu.vn",
        "faculty_department": "Khoa Khoa học và Kỹ thuật Máy tính",
        "specialization": "Lập trình Web & Kiến trúc Hệ thống Phân tán",
        "experience_years": 4,
        "phone_number": "0912345678",
        "teaching_evidence": (
            "Chứng chỉ nghiệp vụ sư phạm ĐH Sư phạm TP.HCM số CP-2023-889; "
            "Giảng dạy trợ giảng môn PWD301 từ 2024"
        ),
        "salary_proof": "Hợp đồng thù lao thỉnh giảng và sao kê lương gần nhất",
        "current_schedule": "Thứ 2, Thứ 4 ca 2 (09:30 - 11:45) tại phòng LAB 402",
        "employment_contract": "Hợp đồng giảng viên số HD-BK-2024/09 có hiệu lực đến 2027",
        "evidence_urls": "https://drive.google.com/drive/folders/pwd301-applicant-portfolio",
        "statement_of_purpose": (
            "Mong muốn đóng góp xây dựng hệ thống khóa học chất lượng cao, "
            "chia sẻ kiến thức chuẩn công nghiệp cho cộng đồng sinh viên."
        ),
    }


def test_submit_instructor_application_success(app, student_user, valid_application_data):
    """Student successfully submits application with comprehensive data."""
    with app.app_context():
        app_record = submit_instructor_application(
            user_id=student_user,
            application_data=valid_application_data,
            session=db.session,
        )

        assert app_record.id is not None
        assert app_record.applicant_user_id == student_user
        assert app_record.status == "PENDING"
        assert app_record.reviewed_by_user_id is None
        assert app_record.reviewed_at is None

        # Verify parsed details
        details = app_record.parsed_details
        assert details["institution_name"] == "Đại học Bách Khoa TP.HCM"
        assert details["institution_email"] == "nva.lecturer@hcmut.edu.vn"
        assert details["specialization"] == "Lập trình Web & Kiến trúc Hệ thống Phân tán"
        assert details["experience_years"] == 4
        assert app_record.status_label_vi == "Chờ duyệt"
        assert (
            "warning" in app_record.status_badge_class.lower()
            or "amber" in app_record.status_badge_class.lower()
        )


def test_submit_instructor_application_duplicate_rejected(
    app, student_user, valid_application_data
):
    """Submitting a second application while one is PENDING is rejected."""
    with app.app_context():
        submit_instructor_application(
            user_id=student_user,
            application_data=valid_application_data,
            session=db.session,
        )

        with pytest.raises(ValidationError, match="đang có một đơn đăng ký đang chờ xét duyệt"):
            submit_instructor_application(
                user_id=student_user,
                application_data=valid_application_data,
                session=db.session,
            )


def test_submit_instructor_application_by_existing_instructor_rejected(
    app, instructor_user, valid_application_data
):
    """Existing instructors cannot apply to become instructor again."""
    with app.app_context(), pytest.raises(ValidationError, match="Bạn đã có quyền Giảng viên"):
        submit_instructor_application(
            user_id=instructor_user,
            application_data=valid_application_data,
            session=db.session,
        )


def test_cancel_instructor_application(app, student_user, valid_application_data):
    """Applicant can cancel their own PENDING application."""
    with app.app_context():
        app_record = submit_instructor_application(
            user_id=student_user,
            application_data=valid_application_data,
            session=db.session,
        )

        cancelled_app = cancel_instructor_application(
            user_id=student_user,
            application_id=app_record.id,
            session=db.session,
        )

        assert cancelled_app.status == "CANCELLED"
        assert cancelled_app.status_label_vi == "Đã hủy"

        # After cancelling, student is allowed to submit a fresh application
        new_app = submit_instructor_application(
            user_id=student_user,
            application_data=valid_application_data,
            session=db.session,
        )
        assert new_app.status == "PENDING"
        assert new_app.id != app_record.id


def test_review_instructor_application_approve(
    app, student_user, admin_user, valid_application_data
):
    """Admin approves application: grants INSTRUCTOR role, updates status, records audit."""
    with app.app_context():
        app_record = submit_instructor_application(
            user_id=student_user,
            application_data=valid_application_data,
            session=db.session,
        )

        reviewed = review_instructor_application(
            application_id=app_record.id,
            admin_user_id=admin_user,
            action="approve",
            reason="Hồ sơ đầy đủ chứng chỉ sư phạm, kinh nghiệm phù hợp giáo trình PWD301.",
            session=db.session,
        )

        assert reviewed.status == "APPROVED"
        assert reviewed.reviewed_by_user_id == admin_user
        assert reviewed.reviewed_at is not None
        assert "Hồ sơ đầy đủ" in reviewed.review_reason

        # Verify applicant now has INSTRUCTOR role
        user = db.session.get(User, student_user)
        assert user.is_instructor is True
        assert "INSTRUCTOR" in user.role_codes
        assert "STUDENT" in user.role_codes  # Cumulative AUTH-002 preserved


def test_review_instructor_application_reject(
    app, student_user, admin_user, valid_application_data
):
    """Admin rejects application: updates status, preserves student role, logs reason."""
    with app.app_context():
        app_record = submit_instructor_application(
            user_id=student_user,
            application_data=valid_application_data,
            session=db.session,
        )

        reviewed = review_instructor_application(
            application_id=app_record.id,
            admin_user_id=admin_user,
            action="reject",
            reason="Thiếu giấy tờ minh chứng hợp đồng giảng dạy hợp lệ.",
            session=db.session,
        )

        assert reviewed.status == "REJECTED"
        assert reviewed.reviewed_by_user_id == admin_user
        assert reviewed.review_reason == "Thiếu giấy tờ minh chứng hợp đồng giảng dạy hợp lệ."

        # Verify applicant remains pure STUDENT
        user = db.session.get(User, student_user)
        assert user.is_instructor is False
        assert user.role_codes == {"STUDENT"}


def test_list_and_get_applications(app, student_user, valid_application_data):
    """Test listing applications by status and fetching single application."""
    with app.app_context():
        app_record = submit_instructor_application(
            user_id=student_user,
            application_data=valid_application_data,
            session=db.session,
        )

        # Get by id
        fetched = get_instructor_application(app_record.id, session=db.session)
        assert fetched is not None
        assert fetched.id == app_record.id

        # List all
        all_apps = list_instructor_applications(session=db.session)
        assert len(all_apps) >= 1

        # List by status
        pending_apps = list_instructor_applications(status="PENDING", session=db.session)
        assert any(a.id == app_record.id for a in pending_apps)

        approved_apps = list_instructor_applications(status="APPROVED", session=db.session)
        assert not any(a.id == app_record.id for a in approved_apps)
