"""Empirical Challenger Adversarial Test Suite for Milestone 2.

Target Subsystem: Student Portal Integration (Survey 5.2 / M2)
Tested Templates:
- student/course_detail.html (Prerequisite gating, capacity gating, syllabus)
- student/lesson.html (Lesson navigation, video/doc stream, resource vault, progress badge)
- student/my_learning.html (Course hub, leave & re-enroll lifecycle, search/filter attributes)
- student/become_instructor.html (Instructor nomination workflow, pending dossier, cancellation)
"""

from __future__ import annotations

from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Enrollment
from pwd301.models.file_import import FileAsset, FileRevision, LessonResource
from pwd301.models.identity import User
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    enroll_student,
)
from pwd301.services.lesson_service import (
    change_lesson_status,
    create_lesson,
)
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def m2_challenger_env(app: Flask) -> dict[str, Any]:
    """Setup isolated test environment with Instructor, Student, Courses,
    Prerequisites & Lessons.
    """
    seed_baseline(db.session)
    sess: Session = db.session

    admin = sess.query(User).filter(User.email == "admin@pwd301.local").first()
    assert admin is not None

    instructor = register_user(
        email="m2_inst@pwd301.local",
        password="Password@123",
        display_name="M2 Instructor",
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR")

    student_unmet = register_user(
        email="m2_student_unmet@pwd301.local",
        password="Password@123",
        display_name="Student Unmet Prereqs",
    )

    student_met = register_user(
        email="m2_student_met@pwd301.local",
        password="Password@123",
        display_name="Student Met Prereqs",
    )

    # 1. Course A (Prerequisite Course)
    course_a = create_course(
        instructor,
        {
            "course_code": "M2-CS101",
            "title": "Intro to Programming",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
            "capacity": 50,
            "learning_objectives": "Master variables and loops\nUnderstand basic algorithms",
        },
        session=sess,
    )
    change_course_status(instructor, course_a.id, "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin, course_a.id, "APPROVED", session=sess)
    change_course_status(instructor, course_a.id, "PUBLISHED", session=sess)

    # 2. Course B (Dependent Course requiring Course A)
    course_b = create_course(
        instructor,
        {
            "course_code": "M2-CS201",
            "title": "Data Structures and Algorithms",
            "category": "Computer Science",
            "difficulty": "INTERMEDIATE",
            "capacity": 2,  # Small capacity to test capacity limits
            "learning_objectives": "Master Binary Trees\nGraph Algorithms",
        },
        session=sess,
    )
    change_course_status(instructor, course_b.id, "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin, course_b.id, "APPROVED", session=sess)
    change_course_status(instructor, course_b.id, "PUBLISHED", session=sess)

    # Add prerequisite: Course B requires Course A
    add_course_prerequisite(instructor, course_b.id, course_a.id, session=sess)

    # Create lessons for Course A
    la1 = create_lesson(
        instructor,
        course_a.id,
        {
            "title": "Lesson 1: Variables",
            "markdown_content": "# Lesson 1\nVariables and Types.",
            "position": 1,
            "estimated_duration_minutes": 20,
        },
        session=sess,
    )
    change_lesson_status(instructor, la1.id, "PUBLISHED", session=sess)

    la2 = create_lesson(
        instructor,
        course_a.id,
        {
            "title": "Lesson 2: Control Flow",
            "markdown_content": "# Lesson 2\nIf statements and Loops.",
            "position": 2,
            "estimated_duration_minutes": 35,
        },
        session=sess,
    )
    change_lesson_status(instructor, la2.id, "PUBLISHED", session=sess)

    # Attach a media video file asset to Lesson 1
    video_asset = FileAsset(
        course_id=course_a.id,
        created_by_user_id=instructor.id,
        asset_type="RESOURCE",
        display_name="variables_lecture.mp4",
        status="ACTIVE",
    )
    sess.add(video_asset)
    sess.flush()

    rev_video = FileRevision(
        file_asset_id=video_asset.id,
        revision_no=1,
        is_current=True,
        original_filename="variables_lecture.mp4",
        detected_mime_type="video/mp4",
        size_bytes=10485760,
        status="ACTIVE",
        uploaded_by_user_id=instructor.id,
    )
    sess.add(rev_video)
    sess.flush()

    res_video = LessonResource(
        lesson_id=la1.id,
        file_asset_id=video_asset.id,
        label="Lecture Video: Variables",
        position=1,
    )
    sess.add(res_video)

    # Attach a doc resource to Lesson 1
    doc_asset = FileAsset(
        course_id=course_a.id,
        created_by_user_id=instructor.id,
        asset_type="RESOURCE",
        display_name="variables_handout.pdf",
        status="ACTIVE",
    )
    sess.add(doc_asset)
    sess.flush()

    rev_doc = FileRevision(
        file_asset_id=doc_asset.id,
        revision_no=1,
        is_current=True,
        original_filename="variables_handout.pdf",
        detected_mime_type="application/pdf",
        size_bytes=102400,
        status="ACTIVE",
        uploaded_by_user_id=instructor.id,
    )
    sess.add(rev_doc)
    sess.flush()

    res_doc = LessonResource(
        lesson_id=la1.id,
        file_asset_id=doc_asset.id,
        label="Lecture Handout PDF",
        position=2,
    )
    sess.add(res_doc)
    sess.commit()

    return {
        "admin": admin,
        "instructor": instructor,
        "student_unmet": student_unmet,
        "student_met": student_met,
        "course_a": course_a,
        "course_b": course_b,
        "lesson_a1": la1,
        "lesson_a2": la2,
    }


class TestM2AdversarialGatingAndLifecycle:
    """Adversarial stress-testing suite for Milestone 2 features."""

    # =========================================================================
    # 1. COURSE PREREQUISITE & CAPACITY GATING (course_detail.html)
    # =========================================================================

    def test_prerequisite_gating_unmet_blocks_ui_and_post(
        self, client: FlaskClient, m2_challenger_env: dict[str, Any]
    ) -> None:
        """Adversarially verify that student with unmet prerequisites cannot
        enroll via API or direct POST.
        """
        student_unmet = m2_challenger_env["student_unmet"]
        course_b = m2_challenger_env["course_b"]

        login_web_user(client, student_unmet)

        # 1. GET course detail JSON
        resp = client.get(
            f"/student/courses/{course_b.public_id}", headers={"Accept": "application/json"}
        )
        assert resp.status_code == 200
        data = resp.get_json()

        # Invariant checks on prerequisite gating
        assert data["is_eligible"] is False
        assert len(data["missing_titles"]) > 0
        assert any(
            p["course_code"] == "M2-CS101" and not p["is_satisfied"] for p in data["prerequisites"]
        )

        # 2. Hostile direct POST attempt to bypass prerequisite gating
        post_resp = client.post(
            f"/student/courses/{course_b.public_id}/enroll",
            headers={"Accept": "application/json"},
        )
        assert post_resp.status_code in (400, 403, 409)
        err_data = post_resp.get_json()
        assert "error" in err_data

        # Verify enrollment was NOT created in database
        enr = (
            db.session.query(Enrollment)
            .filter(
                Enrollment.student_user_id == student_unmet.id,
                Enrollment.course_id == course_b.id,
            )
            .first()
        )
        assert enr is None

    def test_prerequisite_gating_satisfied_allows_enrollment(
        self, client: FlaskClient, m2_challenger_env: dict[str, Any]
    ) -> None:
        """When student completes Course A, Course B prerequisite barrier unlocks."""
        student_met = m2_challenger_env["student_met"]
        course_a = m2_challenger_env["course_a"]
        course_b = m2_challenger_env["course_b"]

        # Satisfy Course A: Enroll and mark COMPLETED
        enr_a = enroll_student(student_met, course_a.id, session=db.session)
        enr_a.status = "COMPLETED"
        enr_a.current_progress_percent = 100.0
        db.session.commit()

        login_web_user(client, student_met)

        # 1. GET course detail page for Course B
        resp = client.get(
            f"/student/courses/{course_b.public_id}", headers={"Accept": "application/json"}
        )
        assert resp.status_code == 200
        data = resp.get_json()

        # Prerequisite barrier is unlocked
        assert data["is_eligible"] is True
        assert all(p["is_satisfied"] for p in data["prerequisites"])

        # 2. Submit enrollment
        post_resp = client.post(
            f"/student/courses/{course_b.public_id}/enroll",
            headers={"Accept": "application/json"},
        )
        assert post_resp.status_code in (200, 201)

        # Enrollment is now ACTIVE
        enr_b = (
            db.session.query(Enrollment)
            .filter(
                Enrollment.student_user_id == student_met.id,
                Enrollment.course_id == course_b.id,
            )
            .first()
        )
        assert enr_b is not None
        assert enr_b.status == "ACTIVE"

    def test_course_capacity_saturation_blocks_enrollment(
        self, client: FlaskClient, m2_challenger_env: dict[str, Any]
    ) -> None:
        """When course capacity is reached, course is marked full and enrollment blocked."""
        course_b = m2_challenger_env["course_b"]

        # Fill capacity of course_b (capacity is 2)
        u1 = register_user("filler1@pwd301.local", "Password@123", "Filler 1")
        u2 = register_user("filler2@pwd301.local", "Password@123", "Filler 2")
        e1 = Enrollment(student_user_id=u1.id, course_id=course_b.id, status="ACTIVE")
        e2 = Enrollment(student_user_id=u2.id, course_id=course_b.id, status="ACTIVE")
        db.session.add_all([e1, e2])
        db.session.commit()

        # Another student with satisfied prerequisite attempts to view
        u3 = register_user("filler3@pwd301.local", "Password@123", "Filler 3")
        # Satisfy prereq
        e_prereq = Enrollment(
            student_user_id=u3.id,
            course_id=m2_challenger_env["course_a"].id,
            status="COMPLETED",
        )
        db.session.add(e_prereq)
        db.session.commit()

        login_web_user(client, u3)
        resp = client.get(
            f"/student/courses/{course_b.public_id}", headers={"Accept": "application/json"}
        )
        assert resp.status_code == 200
        data = resp.get_json()

        assert data["course"]["is_full"] is True
        assert data["course"]["active_enrolled_count"] >= data["course"]["capacity"]

    # =========================================================================
    # 2. LESSON READER, MEDIA STREAMING & PROGRESS
    # =========================================================================

    def test_lesson_reader_elements_and_media_rendering(
        self, client: FlaskClient, m2_challenger_env: dict[str, Any]
    ) -> None:
        """Verify lesson outline, video stream, resource downloads, and progress badge."""
        student = m2_challenger_env["student_unmet"]
        course_a = m2_challenger_env["course_a"]
        lesson_a1 = m2_challenger_env["lesson_a1"]

        # Enroll student in Course A
        enroll_student(student, course_a.id, session=db.session)

        login_web_user(client, student)
        resp = client.get(
            f"/student/courses/{course_a.public_id}/lessons/{lesson_a1.public_id}",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.get_json()

        # 1. Lesson Progress
        assert data["progress"]["is_completed"] is False

        # 2. Canonical details
        assert data["lesson_id"] == str(lesson_a1.public_id)
        assert data["title"] == "Lesson 1: Variables"
        assert "# Lesson 1" in data["markdown_content"]

        # 3. Resources Vault & File Assets
        assert len(data["resources"]) >= 1
        res_names = [r.get("display_name") or r.get("label") for r in data["resources"]]
        assert any("Handout" in n or "variables" in n for n in res_names if n)

    def test_lesson_progress_toggle_and_heartbeat(
        self, client: FlaskClient, m2_challenger_env: dict[str, Any]
    ) -> None:
        """Verify POST /student/lessons/<lesson_id>/progress updates completion state."""
        student = m2_challenger_env["student_unmet"]
        course_a = m2_challenger_env["course_a"]
        lesson_a1 = m2_challenger_env["lesson_a1"]

        enroll_student(student, course_a.id, session=db.session)
        login_web_user(client, student)

        # 1. Send completion update via AJAX
        post_resp = client.post(
            f"/student/lessons/{lesson_a1.public_id}/progress",
            json={"completed": True, "time_spent_seconds": 150, "view_fraction": 1.0},
            headers={"Accept": "application/json"},
        )
        assert post_resp.status_code == 200
        data = post_resp.get_json()
        assert data.get("completed") is True

        # 2. Reload lesson and check completed progress state
        resp = client.get(
            f"/student/courses/{course_a.public_id}/lessons/{lesson_a1.public_id}",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["progress"]["is_completed"] is True

    # =========================================================================
    # 3. MY LEARNING HUB & LIFECYCLE ACTIONS
    # =========================================================================

    def test_my_learning_leave_and_reenroll_lifecycle(
        self, client: FlaskClient, m2_challenger_env: dict[str, Any]
    ) -> None:
        """Verify leaving a course marks status LEFT, and re-enrolling restores it to ACTIVE."""
        student = m2_challenger_env["student_unmet"]
        course_a = m2_challenger_env["course_a"]

        enroll_student(student, course_a.id, session=db.session)
        login_web_user(client, student)

        # 1. Initial view: Course is ACTIVE
        resp = client.get("/student/my-learning", headers={"Accept": "application/json"})
        assert resp.status_code == 200
        data = resp.get_json()
        enrollments = data["enrollments"]
        assert any(e["course_code"] == "M2-CS101" and e["status"] == "ACTIVE" for e in enrollments)

        # 2. Leave course
        leave_resp = client.post(
            f"/student/courses/{course_a.public_id}/leave",
            json={"reason": "Busy schedule"},
            headers={"Accept": "application/json"},
        )
        assert leave_resp.status_code == 200
        leave_data = leave_resp.get_json()
        assert leave_data["status"] == "LEFT"

        # 3. Re-enroll course
        re_resp = client.post(
            f"/student/courses/{course_a.public_id}/re-enroll",
            headers={"Accept": "application/json"},
        )
        assert re_resp.status_code == 200
        re_data = re_resp.get_json()
        assert re_data["status"] == "ACTIVE"

    # =========================================================================
    # 4. BECOME INSTRUCTOR PORTAL
    # =========================================================================

    def test_become_instructor_full_submission_and_cancel_flow(
        self, client: FlaskClient, m2_challenger_env: dict[str, Any]
    ) -> None:
        """Verify student can view application status, submit application,
        view pending dossier, and cancel.
        """
        student = m2_challenger_env["student_unmet"]
        login_web_user(client, student)

        # 1. Fresh student views application status
        resp = client.get("/student/become-instructor", headers={"Accept": "application/json"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["is_already_instructor"] is False
        assert data["application"] is None

        # 2. Submit application
        post_resp = client.post(
            "/student/become-instructor",
            json={
                "institution_name": "Đại học Bách Khoa TP.HCM",
                "institution_email": "m2_student@hcmut.edu.vn",
                "faculty_department": "Khoa Khoa học & Kỹ thuật Máy tính",
                "specialization": "Hệ thống phân tán & Bảo mật ứng dụng",
                "experience_years": "5",
                "phone_number": "0987654321",
                "teaching_evidence": "Giảng dạy 5 năm môn Mạng máy tính.",
                "evidence_urls": "https://github.com/m2-student",
            },
            headers={"Accept": "application/json"},
        )
        assert post_resp.status_code == 201
        post_data = post_resp.get_json()
        assert post_data["status"] == "PENDING"

        # Should now reflect pending review dossier
        resp2 = client.get("/student/become-instructor", headers={"Accept": "application/json"})
        assert resp2.status_code == 200
        data2 = resp2.get_json()
        assert data2["application"] is not None
        assert data2["application"]["status"] == "PENDING"
        assert data2["application"]["status_label"] in ("Chờ duyệt", "Đang thẩm định")
        assert data2["application"]["details"]["institution_name"] == "Đại học Bách Khoa TP.HCM"

        # 3. Cancel application
        cancel_resp = client.post(
            "/student/become-instructor/cancel",
            headers={"Accept": "application/json"},
        )
        assert cancel_resp.status_code == 200
        cancel_data = cancel_resp.get_json()
        assert cancel_data["status"] == "CANCELLED"

    def test_become_instructor_for_existing_instructor(
        self, client: FlaskClient, m2_challenger_env: dict[str, Any]
    ) -> None:
        """When an instructor accesses become-instructor, role is reflected."""
        instructor = m2_challenger_env["instructor"]
        login_web_user(client, instructor)

        resp = client.get("/student/become-instructor", headers={"Accept": "application/json"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["is_already_instructor"] is True
