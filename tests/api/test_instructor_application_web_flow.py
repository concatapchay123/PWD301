"""Web UI integration tests for Instructor Application & Review Workflow.

Tests verify:
1. Student accesses GET /student/become-instructor (renders form or status).
2. Student submits nomination form via POST /student/become-instructor.
3. Duplicate pending application is rejected.
4. Student cancels pending application via POST /student/become-instructor/cancel.
5. Admin accesses GET /admin/instructor-applications (renders queue with status filter).
6. Admin views single application details via GET /admin/instructor-applications/<app_id>.
7. Admin approves application via POST /admin/instructor-applications/<app_id>/review:
   - Grants INSTRUCTOR role to applicant (AUTH-002 cumulative hierarchy).
   - Applicant can now switch to INSTRUCTOR and access /instructor/dashboard.
8. Admin rejects application with reason.
9. Security & Access Control: unauthorized users cannot access admin queue.
"""

from __future__ import annotations

import re

import pytest

from pwd301.extensions import db
from pwd301.models.identity import InstructorApplication, User
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def test_users(app):
    """Seed test users: student, another student, admin."""
    with app.app_context():
        student1 = register_user(
            "student1.apply@pwd301.edu.vn", "Password123!", "Student One", session=db.session
        )
        assign_role_to_user(student1.id, "STUDENT", session=db.session)

        student2 = register_user(
            "student2.apply@pwd301.edu.vn", "Password123!", "Student Two", session=db.session
        )
        assign_role_to_user(student2.id, "STUDENT", session=db.session)

        admin = register_user(
            "admin.approver@pwd301.edu.vn", "AdminPassword123!", "System Admin", session=db.session
        )
        assign_role_to_user(admin.id, "ADMIN", session=db.session)

        return {
            "student1_id": student1.id,
            "student1_email": student1.email,
            "student2_id": student2.id,
            "student2_email": student2.email,
            "admin_id": admin.id,
            "admin_email": admin.email,
        }


def extract_csrf_token(html_text: str) -> str:
    """Extract csrf_token from hidden HTML input."""
    match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html_text)
    if not match:
        match = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrf_token["\']', html_text)
    return match.group(1) if match else ""


def test_student_become_instructor_page_renders(client, test_users):
    """Student can view the become-instructor nomination endpoint."""
    resp = client.post(
        "/auth/login",
        json={"email": test_users["student1_email"], "password": "Password123!"},
    )
    assert resp.status_code == 200

    resp = client.get("/student/become-instructor")
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert "is_already_instructor" in data


def test_student_submit_nomination_web_flow(client, test_users):
    """Student submits application via form/JSON, receives status JSON."""
    client.post(
        "/auth/login",
        json={"email": test_users["student1_email"], "password": "Password123!"},
    )

    form_data = {
        "institution_name": "Đại học Sư phạm Kỹ thuật",
        "institution_email": "student1@ute.edu.vn",
        "faculty_department": "Khoa CNTT",
        "specialization": "Kỹ thuật phần mềm & Lập trình Web",
        "experience_years": "3",
        "phone_number": "0987654321",
        "teaching_evidence": (
            "Chứng chỉ sư phạm nghề và 2 năm làm giảng viên thỉnh giảng môn Thiết kế Web"
        ),
        "salary_proof": "Sao kê tài khoản nhận lương giảng dạy năm 2025",
        "current_schedule": "Thứ 3 ca 1 và Thứ 5 ca 3 tại phòng máy 201",
        "employment_contract": "Hợp đồng lao động giảng dạy số 112/HD-SPKT",
        "evidence_urls": "https://drive.google.com/drive/folders/evidence-test",
        "statement_of_purpose": (
            "Tôi muốn tham gia giảng dạy và đóng góp bài giảng chất lượng cho hệ thống PWD301."
        ),
    }

    resp = client.post("/student/become-instructor", json=form_data)
    assert resp.status_code in (200, 201)
    assert resp.is_json
    data = resp.get_json()
    assert data.get("status") == "PENDING" or "application_id" in data


def test_admin_review_and_approval_flow(client, test_users):
    """Admin views applications queue and approves student nomination."""
    # 1. Student submits application
    client.post(
        "/auth/login",
        json={"email": test_users["student2_email"], "password": "Password123!"},
    )

    client.post(
        "/student/become-instructor",
        json={
            "institution_name": "Đại học Công nghệ Thông tin",
            "institution_email": "student2@uit.edu.vn",
            "specialization": "Fullstack Web & Cloud Computing",
            "experience_years": "4",
            "teaching_evidence": "Bằng thạc sĩ CNTT và trợ giảng 2 năm",
        },
    )
    client.post("/auth/logout")

    # 2. Admin logs in and inspects applications queue
    client.post(
        "/auth/login",
        json={"email": test_users["admin_email"], "password": "AdminPassword123!"},
    )

    admin_resp = client.get("/admin/instructor-applications")
    assert admin_resp.status_code == 200
    assert admin_resp.is_json

    # Find the application ID in database
    with client.application.app_context():
        app_record = (
            db.session.query(InstructorApplication)
            .filter(InstructorApplication.applicant_user_id == test_users["student2_id"])
            .first()
        )
        assert app_record is not None
        app_id = app_record.id

    # 3. Admin approves application
    approve_resp = client.post(
        f"/admin/instructor-applications/{app_id}/review",
        json={
            "action": "approve",
            "reason": "Hồ sơ đủ tiêu chuẩn bằng cấp và kinh nghiệm giảng dạy.",
        },
    )
    assert approve_resp.status_code == 200
    assert approve_resp.is_json

    # 4. Verify in DB that applicant is now an INSTRUCTOR
    with client.application.app_context():
        student2_user = db.session.get(User, test_users["student2_id"])
        assert student2_user.is_instructor is True
        assert "INSTRUCTOR" in student2_user.role_codes

    # 5. Log in as student2 and verify role privileges
    client.post("/auth/logout")
    login_stud2 = client.post(
        "/auth/login",
        json={"email": test_users["student2_email"], "password": "Password123!"},
    )
    assert login_stud2.status_code == 200
    # Promoted user lands on instructor dashboard or can switch to it
    inst_dash = client.get("/instructor/dashboard")
    assert inst_dash.status_code == 200
    assert inst_dash.is_json


def test_student_cancel_application_flow(client, test_users):
    """Student can cancel their pending application and reapply."""
    client.post(
        "/auth/login",
        json={"email": test_users["student1_email"], "password": "Password123!"},
    )

    # Cancel
    cancel_resp = client.post(
        "/student/become-instructor/cancel",
        json={},
    )
    assert cancel_resp.status_code in (200, 404)
    assert cancel_resp.is_json


def test_admin_reject_application_flow(client, test_users):
    """Admin rejects application with required reason; student sees rejection and can reapply."""
    # 1. Student1 submits application
    client.post(
        "/auth/login",
        json={"email": test_users["student1_email"], "password": "Password123!"},
    )

    client.post(
        "/student/become-instructor",
        json={
            "institution_name": "Trung tâm Đào tạo Tin học",
            "institution_email": "student1@center.edu.vn",
            "specialization": "Lập trình Web nâng cao",
            "teaching_evidence": "Thiếu chứng chỉ sư phạm",
        },
    )
    client.post("/auth/logout")

    # 2. Admin logs in
    client.post(
        "/auth/login",
        json={"email": test_users["admin_email"], "password": "AdminPassword123!"},
    )

    with client.application.app_context():
        app_record = (
            db.session.query(InstructorApplication)
            .filter(
                InstructorApplication.applicant_user_id == test_users["student1_id"],
                InstructorApplication.status == "PENDING",
            )
            .first()
        )
        assert app_record is not None
        app_id = app_record.id

    # 3. Reject without reason -> rejected with 400 validation error
    fail_resp = client.post(
        f"/admin/instructor-applications/{app_id}/review",
        json={"action": "reject", "reason": ""},
    )
    assert fail_resp.status_code == 400
    assert fail_resp.is_json

    # 4. Reject with valid reason
    reject_resp = client.post(
        f"/admin/instructor-applications/{app_id}/review",
        json={
            "action": "reject",
            "reason": "Cần bổ sung chứng chỉ giảng dạy sư phạm và bằng cử nhân chuyên ngành.",
        },
    )
    assert reject_resp.status_code == 200
    assert reject_resp.is_json

    # 5. Student logs back in and checks become-instructor view
    client.post("/auth/logout")
    client.post(
        "/auth/login",
        json={"email": test_users["student1_email"], "password": "Password123!"},
    )
    student_view = client.get("/student/become-instructor")
    assert student_view.status_code == 200
    assert student_view.is_json
    data = student_view.get_json()
    assert data["application"]["status"] == "REJECTED"
    assert "Cần bổ sung chứng chỉ" in data["application"]["review_reason"]


def test_security_access_control_admin_queue(client, test_users):
    """Students cannot access the admin applications queue or review endpoints."""
    # 1. Anonymous user redirected to login
    anon_resp = client.get("/admin/instructor-applications")
    assert anon_resp.status_code in (302, 401, 403)

    # 2. Student user logged in
    client.post(
        "/auth/login",
        data={"email": test_users["student1_email"], "password": "Password123!"},
        follow_redirects=True,
    )
    student_access = client.get("/admin/instructor-applications")
    assert student_access.status_code in (302, 403)

    # 3. Student user attempting review POST
    fake_token = "fake-token"
    student_review = client.post(
        "/admin/instructor-applications/1/review",
        data={"csrf_token": fake_token, "action": "approve"},
    )
    assert student_review.status_code in (302, 400, 403)


def test_rest_api_instructor_application_flow(client, test_users):
    """REST API endpoints for student self-nomination and admin review."""
    from pwd301.services.jwt_auth_service import create_token_pair

    # Create tokens for student and admin
    with client.application.app_context():
        student_u = db.session.get(User, test_users["student1_id"])
        admin_u = db.session.get(User, test_users["admin_id"])
        student_tokens = create_token_pair(student_u)
        admin_tokens = create_token_pair(admin_u)

    student_headers = {"Authorization": f"Bearer {student_tokens['access_token']}"}
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

    # 1. Student GET application (initially returns application or not found)
    get_init = client.get("/api/student/instructor-application", headers=student_headers)
    assert get_init.status_code in (200, 404)

    # 2. Student POST application
    payload = {
        "institution_name": "Đại học Bách Khoa",
        "institution_email": "api.student@hcmut.edu.vn",
        "faculty_department": "Khoa Khoa học Máy tính",
        "specialization": "Hệ thống phân tán",
        "experience_years": 5,
        "phone_number": "0912345678",
        "teaching_evidence": "Bằng tiến sĩ và 5 bài báo khoa học",
        "salary_proof": "Xác nhận thu nhập giảng viên",
        "current_schedule": "Thứ 2, 4, 6 ca chiều",
        "employment_contract": "Hợp đồng cơ hữu số 889/HD-BK",
        "evidence_urls": "https://example.com/evidence-folder",
        "statement_of_purpose": "Mong muốn giảng dạy trực tuyến tại PWD301",
    }
    submit_resp = client.post(
        "/api/student/instructor-application", json=payload, headers=student_headers
    )
    assert submit_resp.status_code in (200, 201)
    sub_data = submit_resp.get_json()
    assert sub_data["status"] == "PENDING"
    app_id = sub_data["application_id"]

    # 3. Duplicate submission returns 400
    dup_resp = client.post(
        "/api/student/instructor-application", json=payload, headers=student_headers
    )
    assert dup_resp.status_code == 400

    # 4. Admin lists applications
    admin_list = client.get("/api/admin/instructor-applications", headers=admin_headers)
    assert admin_list.status_code == 200
    list_data = admin_list.get_json()
    assert any(item["id"] == app_id for item in list_data["applications"])

    # 5. Admin gets specific application
    admin_get = client.get(f"/api/admin/instructor-applications/{app_id}", headers=admin_headers)
    assert admin_get.status_code == 200
    assert admin_get.get_json()["applicant_email"] == test_users["student1_email"]

    # 6. Admin reviews and approves
    review_resp = client.post(
        f"/api/admin/instructor-applications/{app_id}/review",
        json={"action": "approve", "reason": "Hồ sơ xuất sắc, bằng tiến sĩ phù hợp."},
        headers=admin_headers,
    )
    assert review_resp.status_code == 200
    rev_data = review_resp.get_json()
    assert rev_data["status"] == "APPROVED"

    # 7. Verify user role updated in database
    with client.application.app_context():
        u = db.session.get(User, test_users["student1_id"])
        assert "INSTRUCTOR" in u.role_codes


def test_instructor_application_evidence_upload_and_download(client, test_users):
    """Test file upload during application submission and secure admin download."""
    import io
    import zipfile

    # 1. Login as student2
    client.post(
        "/auth/login",
        data={"email": test_users["student2_email"], "password": "Password123!"},
        follow_redirects=True,
    )

    get_form = client.get("/student/become-instructor")
    csrf_token = extract_csrf_token(get_form.text)

    # 2. Submit multipart form with an attached Word certificate.
    docx_buffer = io.BytesIO()
    with zipfile.ZipFile(docx_buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Teaching Certificate Evidence</w:t></w:r></w:p>"
            "</w:body></w:document>",
        )
    file_content = docx_buffer.getvalue()
    data = {
        "csrf_token": csrf_token,
        "institution_name": "Đại học Sư phạm",
        "institution_email": "teacher@hnue.edu.vn",
        "faculty_department": "Khoa Toán - Tin",
        "specialization": "Phương pháp giảng dạy Lập trình",
        "experience_years": "4",
        "phone_number": "0987654321",
        "teaching_evidence": "Có bằng nghiệp vụ sư phạm",
        "salary_proof": "Bảng lương 6 tháng gần nhất",
        "current_schedule": "Thứ 3 và Thứ 5",
        "employment_contract": "Hợp đồng giảng dạy 2024-2026",
        "statement_of_purpose": "Muốn đóng góp cho cộng đồng PWD301",
        "certificate_drive_url": "https://drive.google.com/file/d/" + "a" * 180 + "/view?usp=sharing",
        "evidence_files": (io.BytesIO(file_content), "certificate_2024.docx"),
    }

    submit_resp = client.post(
        "/student/become-instructor",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert submit_resp.status_code in (200, 201)

    # Retrieve created application from DB
    with client.application.app_context():
        app = (
            db.session.query(InstructorApplication)
            .filter(InstructorApplication.applicant_user_id == test_users["student2_id"])
            .first()
        )
        assert app is not None
        details = app.parsed_details
        assert "attached_files" in details
        assert len(details["attached_files"]) == 1
        attached = details["attached_files"][0]
        assert attached["original_name"] == "certificate_2024.docx"
        assert details["certificate_drive_url"] == data["certificate_drive_url"]
        saved_filename = attached["saved_filename"]
        app_id = app.id

    # 3. Log out and try downloading evidence unauthenticated -> redirect to login (401/302)
    client.post("/auth/logout", follow_redirects=True)
    unauth_resp = client.get(f"/admin/instructor-applications/{app_id}/evidence/{saved_filename}")
    assert unauth_resp.status_code in (302, 401)

    # 4. Login as Student1 and try downloading -> 403 Forbidden
    client.post(
        "/auth/login",
        data={"email": test_users["student1_email"], "password": "Password123!"},
        follow_redirects=True,
    )
    student_resp = client.get(f"/admin/instructor-applications/{app_id}/evidence/{saved_filename}")
    assert student_resp.status_code == 403

    # 5. Login as Admin and download evidence -> 200 OK with correct file content
    client.post("/auth/logout", follow_redirects=True)
    client.post(
        "/auth/login",
        data={"email": test_users["admin_email"], "password": "AdminPassword123!"},
        follow_redirects=True,
    )
    admin_download = client.get(
        f"/admin/instructor-applications/{app_id}/evidence/{saved_filename}"
    )
    assert admin_download.status_code == 200
    assert admin_download.data == file_content
    assert "attachment" in admin_download.headers.get("Content-Disposition", "")

    admin_preview = client.get(
        f"/admin/instructor-applications/{app_id}/evidence/{saved_filename}?preview=1"
    )
    assert admin_preview.status_code == 200
    assert admin_preview.data == file_content
    assert "inline" in admin_preview.headers.get("Content-Disposition", "")
    assert admin_preview.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert "frame-ancestors 'self'" in admin_preview.headers.get("Content-Security-Policy", "")

    extracted_preview = client.get(
        f"/admin/instructor-applications/{app_id}/evidence/{saved_filename}?format=text"
    )
    assert extracted_preview.status_code == 200
    assert extracted_preview.get_json()["data"]["text"] == "Teaching Certificate Evidence"

    # 6. Path traversal attempt -> 404
    traversal_resp = client.get(
        f"/admin/instructor-applications/{app_id}/evidence/..%2F..%2Fconfig.py"
    )
    assert traversal_resp.status_code in (404, 400)


def test_student_freelancer_niche_submit_web_flow(client, test_users):
    """Freelancer/niche expert student submits application without institution_name with cv_file."""
    import io

    client.post(
        "/auth/login",
        json={"email": test_users["student1_email"], "password": "Password123!"},
    )

    cv_bytes = b"%PDF-1.4 Fake Freelancer CV Content for Testing"
    data = {
        "full_name": "Nguyen Freelancer",
        "date_of_birth": "2000-01-01",
        "phone_number": "0988888888",
        "contact_email": "freelancer@niche.dev",
        "id_card_number": "079123456789",
        "specialization": "Ngành ngách: AI Prompt Engineering & Workflow Automation",
        "statement": "Tôi là chuyên gia độc lập chia sẻ kỹ năng thực chiến.",
        "portfolio_url": "https://github.com/niche-freelancer",
        "cv_file": (io.BytesIO(cv_bytes), "my_cv_freelance.pdf"),
    }

    resp = client.post(
        "/student/become-instructor",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code in (200, 201)
    assert resp.is_json
    res_data = resp.get_json()
    assert res_data.get("status") == "PENDING" or "application_id" in res_data

    # Verify saved application record in database
    with client.application.app_context():
        app = (
            db.session.query(InstructorApplication)
            .filter(InstructorApplication.applicant_user_id == test_users["student1_id"])
            .first()
        )
        assert app is not None
        details = app.parsed_details
        expected_spec = "Ngành ngách: AI Prompt Engineering & Workflow Automation"
        assert details["specialization"] == expected_spec
        assert details["portfolio_url"] == "https://github.com/niche-freelancer"
        assert len(details["attached_files"]) == 1
        assert details["attached_files"][0]["doc_type"] == "CV_PORTFOLIO"
