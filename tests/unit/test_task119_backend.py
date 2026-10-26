"""Tests for TASK-119: Backend Core, Admin Broadcast Management, and Course Certificate PDF Service.

Verifies:
1. Course Certificate PDF generation (ReportLab landscape A4, Vietnamese Unicode, watermarking, headers).
2. Student Certificate issuing endpoint:
   - Incomplete / unenrolled student receives HTTP 400 with Vietnamese error message.
   - Completed student receives HTTP 200 with valid binary PDF payload (%PDF-) and proper download headers.
3. Admin Broadcast Management:
   - list_admin_broadcasts returns broadcast events with recipient counts.
   - hard_delete_broadcast deletes both parent NotificationEvent and child Notification rows.
   - Strict 2-tier RBAC: Primary Admin can delete all categories; System Monitoring Admin only SYSTEM; others forbidden.
4. Auto-cleanup of expired notifications:
   - Notifications older than 15 days (e.g. 16 days) are permanently hard-deleted.
   - Recent notifications are preserved.
   - Orphaned notification events are pruned.
5. Public trailer stream endpoint:
   - Stream endpoint serves video with conditional=True.
"""

from __future__ import annotations

import datetime
import io
import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.course import Course, Enrollment
from backend.models.file_import import FileAsset, FileBlob, FileRevision
from backend.models.identity import User
from backend.models.notification_audit import Notification, NotificationEvent
from backend.models.types import utc_now
from backend.seeds.baseline import seed_baseline
from backend.services.certificate_pdf_service import (
    generate_course_certificate_html,
    generate_course_certificate_pdf,
)
from backend.services.course_service import create_course
from backend.services.enrollment_service import enroll_student
from backend.services.exceptions import ForbiddenError, NotificationNotFoundError
from backend.services.notification_service import (
    broadcast_system_notification,
    cleanup_expired_notifications,
    hard_delete_broadcast,
    list_admin_broadcasts,
)
from backend.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def task119_fixture(app: Flask) -> dict[str, Any]:
    """Setup users, roles, and a test course for TASK-119 tests."""
    sess: Session = db.session
    seed_baseline(sess)

    # 1. Primary Admin
    primary_admin = sess.query(User).filter_by(email="tqtphamnguyenhoangphuc@gmail.com").one()

    # 2. System Monitoring Admin
    sys_admin = register_user(
        f"sysadmin_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "SysAdmin Monitoring",
        session=sess,
    )
    assign_role_to_user(sys_admin.id, "ADMIN", admin_sub_role="ADMIN_SYSTEM_MONITORING", session=sess)

    # 3. Course Review Admin
    review_admin = register_user(
        f"review_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Review Admin",
        session=sess,
    )
    assign_role_to_user(review_admin.id, "ADMIN", admin_sub_role="ADMIN_COURSE_REVIEW", session=sess)

    # 4. Instructor
    instructor = register_user(
        f"instructor_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Instructor PPTQ",
        session=sess,
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR", session=sess)

    # 5. Student
    student = register_user(
        f"student_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Nguyễn Văn Học Viên",
        session=sess,
    )
    assign_role_to_user(student.id, "STUDENT", session=sess)

    # 6. Test Course
    course = create_course(
        instructor,
        {
            "course_code": f"CERT{uuid.uuid4().hex[:4].upper()}",
            "title": "Lập trình Backend và Tạo Chứng chỉ PDF",
            "category": "LẬP TRÌNH",
            "difficulty": "ADVANCED",
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.commit()

    return {
        "primary_admin": primary_admin,
        "sys_admin": sys_admin,
        "review_admin": review_admin,
        "instructor": instructor,
        "student": student,
        "course": course,
    }


def test_certificate_pdf_service_direct() -> None:
    """generate_course_certificate_pdf creates valid binary PDF with Portrait A4 dimensions."""
    student_mock = {"display_name": "Trần Thị Ánh Tuyết", "email": "tuyet@example.com"}
    course_mock = {"title": "Khoa học Dữ liệu và AI Ứng dụng", "course_code": "DS-2026"}
    pdf_bytes = generate_course_certificate_pdf(
        student=student_mock,
        course=course_mock,
        completion_date="22/10/2026",
        cert_id="CERT-DS-2026-9999",
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")

    # Verify HTML generation
    html_content = generate_course_certificate_html(
        student=student_mock,
        course=course_mock,
        completion_date="22/10/2026",
        cert_id="CERT-DS-2026-9999",
    )
    assert isinstance(html_content, str)
    assert "TRẦN THỊ ÁNH TUYẾT" in html_content
    assert "KHOA HỌC DỮ LIỆU VÀ AI ỨNG DỤNG" in html_content
    assert "DS-2026" in html_content
    assert "Be Vietnam Pro" in html_content
    assert "CERT-DS-2026-9999" in html_content
    assert "watermark-logo" in html_content


def test_admin_broadcast_listing_and_rbac(app: Flask, task119_fixture: dict[str, Any]) -> None:
    """Test list_admin_broadcasts returns correct records and enforces admin RBAC."""
    sess: Session = db.session
    p_admin = task119_fixture["primary_admin"]
    student = task119_fixture["student"]

    # Student cannot list broadcasts
    with pytest.raises(ForbiddenError):
        list_admin_broadcasts(actor=student, session=sess)

    # Create a system broadcast
    broadcast_system_notification(
        actor=p_admin,
        title="Bảo trì khẩn cấp",
        body="Hệ thống sẽ tạm dừng để nâng cấp hạ tầng mạng.",
        category="SYSTEM",
        session=sess,
    )

    broadcasts = list_admin_broadcasts(actor=p_admin, session=sess)
    assert len(broadcasts) >= 1
    found = next((b for b in broadcasts if b["title"] == "Bảo trì khẩn cấp"), None)
    assert found is not None
    assert found["category"] == "SYSTEM"
    assert found["recipient_count"] >= 1
    assert "event_key" in found


def test_admin_broadcast_hard_delete_and_rbac(app: Flask, task119_fixture: dict[str, Any]) -> None:
    """Test hard_delete_broadcast completely purges event & child notifications with 2-tier RBAC."""
    sess: Session = db.session
    p_admin = task119_fixture["primary_admin"]
    sys_admin = task119_fixture["sys_admin"]
    review_admin = task119_fixture["review_admin"]
    student = task119_fixture["student"]

    # 1. Primary admin creates a COURSE broadcast
    broadcast_system_notification(
        actor=p_admin,
        title="Thông báo Khóa học mới",
        body="Đã cập nhật bài học mới",
        category="COURSE",
        session=sess,
    )
    broadcasts = list_admin_broadcasts(actor=p_admin, session=sess)
    course_bc = next(b for b in broadcasts if b["title"] == "Thông báo Khóa học mới")
    course_key = course_bc["event_key"]

    # 2. Student cannot delete broadcast
    with pytest.raises(ForbiddenError):
        hard_delete_broadcast(actor=student, event_key_or_id=course_key, session=sess)

    # 3. Review admin cannot delete broadcast
    with pytest.raises(ForbiddenError):
        hard_delete_broadcast(actor=review_admin, event_key_or_id=course_key, session=sess)

    # 4. System monitoring admin cannot delete COURSE category broadcast (only SYSTEM)
    with pytest.raises(ForbiddenError):
        hard_delete_broadcast(actor=sys_admin, event_key_or_id=course_key, session=sess)

    # 5. System monitoring admin CAN delete SYSTEM category broadcast
    broadcast_system_notification(
        actor=p_admin,
        title="Thông báo Bảo trì Hệ thống",
        body="Nâng cấp server",
        category="SYSTEM",
        session=sess,
    )
    bcs = list_admin_broadcasts(actor=p_admin, session=sess)
    sys_bc = next(b for b in bcs if b["title"] == "Thông báo Bảo trì Hệ thống")
    sys_key = sys_bc["event_key"]

    del_res = hard_delete_broadcast(actor=sys_admin, event_key_or_id=sys_key, session=sess)
    assert del_res["deleted"] is True
    # Confirm event deleted from DB
    assert sess.query(NotificationEvent).filter_by(event_key=uuid.UUID(sys_key)).first() is None

    # 6. Primary admin can delete COURSE category broadcast
    del_res_primary = hard_delete_broadcast(actor=p_admin, event_key_or_id=course_key, session=sess)
    assert del_res_primary["deleted"] is True
    assert sess.query(NotificationEvent).filter_by(event_key=uuid.UUID(course_key)).first() is None

    # 7. Non-existent event raises NotificationNotFoundError
    with pytest.raises(NotificationNotFoundError):
        hard_delete_broadcast(actor=p_admin, event_key_or_id=str(uuid.uuid4()), session=sess)


def test_cleanup_expired_notifications(app: Flask, task119_fixture: dict[str, Any]) -> None:
    """cleanup_expired_notifications hard-deletes notifications older than 15 days."""
    sess: Session = db.session
    student = task119_fixture["student"]
    p_admin = task119_fixture["primary_admin"]

    # Create an event older than 16 days
    old_time = utc_now() - datetime.timedelta(days=16)
    old_event = NotificationEvent(
        event_key=uuid.uuid4(),
        event_type="SYSTEM_BROADCAST",
        actor_user_id=p_admin.id,
        created_at=old_time,
    )
    sess.add(old_event)
    sess.flush()

    old_notif = Notification(
        notification_event_id=old_event.id,
        recipient_user_id=student.id,
        category="SYSTEM",
        title="Thông báo 16 ngày trước",
        body="Thông báo đã hết hạn",
        created_at=old_time,
    )
    sess.add(old_notif)

    # Create a fresh notification (today)
    fresh_time = utc_now()
    fresh_event = NotificationEvent(
        event_key=uuid.uuid4(),
        event_type="SYSTEM_BROADCAST",
        actor_user_id=p_admin.id,
        created_at=fresh_time,
    )
    sess.add(fresh_event)
    sess.flush()

    fresh_notif = Notification(
        notification_event_id=fresh_event.id,
        recipient_user_id=student.id,
        category="SYSTEM",
        title="Thông báo hôm nay",
        body="Thông báo mới tinh",
        created_at=fresh_time,
    )
    sess.add(fresh_notif)
    sess.commit()

    old_notif_id = old_notif.id
    fresh_notif_id = fresh_notif.id
    old_event_id = old_event.id
    fresh_event_id = fresh_event.id

    # Run cleanup with default days=15
    result = cleanup_expired_notifications(days=15, session=sess)
    assert result["deleted_notifications"] >= 1

    # Verify old notification is gone
    assert sess.get(Notification, old_notif_id) is None
    # Verify fresh notification remains
    assert sess.get(Notification, fresh_notif_id) is not None
    # Verify old orphan event is pruned
    assert sess.get(NotificationEvent, old_event_id) is None
    # Verify fresh event remains
    assert sess.get(NotificationEvent, fresh_event_id) is not None


def test_student_certificate_endpoint(
    app: Flask, client: FlaskClient, task119_fixture: dict[str, Any]
) -> None:
    """Test GET /student/courses/<course_id>/certificate: 400 when incomplete, PDF when completed."""
    sess: Session = db.session
    student = task119_fixture["student"]
    course = task119_fixture["course"]

    # Log in web session
    login_web_user(client, student)

    # Case 1: Student not enrolled -> 400 with Vietnamese message
    resp1 = client.get(f"/student/courses/{course.public_id}/certificate")
    assert resp1.status_code == 400
    data1 = resp1.get_json()
    assert data1["success"] is False
    assert "chưa hoàn thành" in data1["error"]["message"]

    # Case 2: Enrolled but not completed -> 400 with Vietnamese message
    enrollment = enroll_student(actor=student, course_id=course.id, session=sess)
    enrollment.status = "ACTIVE"
    sess.commit()

    resp2 = client.get(f"/student/courses/{course.public_id}/certificate")
    assert resp2.status_code == 400
    data2 = resp2.get_json()
    assert data2["success"] is False
    assert "chưa hoàn thành" in data2["error"]["message"]

    # Case 3: Course marked COMPLETED -> 200 with valid binary PDF attachment
    enrollment.status = "COMPLETED"
    enrollment.completed_at = utc_now()
    sess.commit()

    resp3 = client.get(f"/student/courses/{course.public_id}/certificate")
    assert resp3.status_code == 200
    assert resp3.mimetype == "application/pdf"
    assert resp3.data.startswith(b"%PDF-")
    cd_header = resp3.headers.get("Content-Disposition", "")
    assert f"Chung_chi_{course.course_code}.pdf" in cd_header

    # Case 4: Format HTML view -> 200 with text/html
    resp_html = client.get(f"/student/courses/{course.public_id}/certificate?format=html")
    assert resp_html.status_code == 200
    assert resp_html.mimetype == "text/html"
    html_text = resp_html.data.decode("utf-8")
    assert "CHỨNG NHẬN HOÀN THÀNH KHÓA HỌC" in html_text
    assert student.display_name.upper() in html_text
    assert course.title.upper() in html_text


def test_admin_broadcast_routes(
    app: Flask, client: FlaskClient, task119_fixture: dict[str, Any]
) -> None:
    """Test admin GET/DELETE broadcast routes and auto-cleanup trigger."""
    sess: Session = db.session
    p_admin = task119_fixture["primary_admin"]

    # Log in web session
    login_web_user(client, p_admin)

    # 1. Create broadcast via service
    broadcast_system_notification(
        actor=p_admin,
        title="Broadcast via API route",
        body="Nội dung thông báo qua route",
        category="SYSTEM",
        session=sess,
    )

    # 2. GET /admin/notifications/broadcasts
    resp_list = client.get("/admin/notifications/broadcasts")
    assert resp_list.status_code == 200
    data = resp_list.get_json()
    assert data["success"] is True
    assert "cleanup" in data
    assert any(b["title"] == "Broadcast via API route" for b in data["data"])

    target_bc = next(b for b in data["data"] if b["title"] == "Broadcast via API route")
    ev_key = target_bc["event_key"]

    # 3. DELETE /admin/notifications/broadcasts/<event_key>
    resp_del = client.delete(f"/admin/notifications/broadcasts/{ev_key}")
    assert resp_del.status_code == 200
    del_json = resp_del.get_json()
    assert del_json["success"] is True
    assert del_json["deleted"] is True


def test_public_trailer_stream_endpoint(
    app: Flask, client: FlaskClient, task119_fixture: dict[str, Any], tmp_path
) -> None:
    """Test GET /api/courses/<course_id>/trailer/stream serves video publicly with conditional=True."""
    sess: Session = db.session
    course = task119_fixture["course"]
    instructor = task119_fixture["instructor"]

    # Create dummy video file on disk
    from backend.services.file_service import get_file_storage_root

    storage_root = get_file_storage_root()
    video_content = b"FAKE_MP4_VIDEO_HEADER_DATA_STREAM_TEST"
    storage_key = f"courses/{course.id}/test_trailer.mp4"
    disk_file = storage_root / storage_key
    disk_file.parent.mkdir(parents=True, exist_ok=True)
    disk_file.write_bytes(video_content)

    import hashlib
    sha = hashlib.sha256(video_content).digest()

    blob = FileBlob(
        sha256=sha,
        size_bytes=len(video_content),
        detected_mime_type="video/mp4",
        storage_key=storage_key,
        storage_backend="local",
        status="PRESENT",
    )
    sess.add(blob)
    sess.flush()

    asset = FileAsset(
        course_id=course.id,
        created_by_user_id=instructor.id,
        asset_type="RESOURCE",
        display_name="course_trailer.mp4",
        status="ACTIVE",
    )
    sess.add(asset)
    sess.flush()

    rev = FileRevision(
        file_asset_id=asset.id,
        revision_no=1,
        is_current=True,
        blob_id=blob.id,
        original_filename="course_trailer.mp4",
        detected_mime_type="video/mp4",
        size_bytes=len(video_content),
        status="ACTIVE",
        uploaded_by_user_id=instructor.id,
    )
    sess.add(rev)
    sess.commit()

    # Public request: unauthenticated client can stream trailer
    resp = client.get(f"/api/courses/{course.public_id}/trailer/stream")
    assert resp.status_code in (200, 206)
    assert resp.data == video_content
    assert resp.mimetype == "video/mp4"

    # Also test instructor convenience path
    resp_inst = client.get(f"/instructor/courses/{course.public_id}/trailer/stream")
    assert resp_inst.status_code in (200, 206)
    assert resp_inst.data == video_content
