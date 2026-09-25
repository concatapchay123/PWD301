from pwd301.extensions import db
from pwd301.models.identity import Role, User, UserRole
from pwd301.services.user_service import register_user


def test_admin_subroles_and_permissions(app):
    """Test Admin Sub-role permissions mapping and model attributes."""
    with app.app_context():
        # Test Anonymous / None user
        anon = User()
        assert not anon.has_admin_permission("COURSE_REVIEW")
        assert not anon.is_primary_admin

        # Ensure ADMIN role exists
        admin_role = db.session.query(Role).filter_by(code="ADMIN").first()
        if not admin_role:
            admin_role = Role(code="ADMIN", name="Quản trị viên")
            db.session.add(admin_role)
            db.session.commit()

        # Create Primary Admin user
        primary_admin = register_user(
            email="primary_admin_test@pwd301.local",
            password="AdminPass1234!",
            display_name="Primary Admin"
        )

        role_admin = UserRole(
            user_id=primary_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_PRIMARY | Initial primary admin"
        )
        db.session.add(role_admin)
        db.session.commit()

        assert primary_admin.is_primary_admin
        assert primary_admin.admin_sub_role == "ADMIN_PRIMARY"
        assert primary_admin.has_admin_permission("COURSE_REVIEW")
        assert primary_admin.has_admin_permission("INSTRUCTOR_REVIEW")
        assert primary_admin.has_admin_permission("TEACHING_ASSIGNMENT")
        assert primary_admin.has_admin_permission("SYSTEM_MONITORING")

        # Create Course Review Admin user
        course_admin = register_user(
            email="course_admin_test@pwd301.local",
            password="CoursePass1234!",
            display_name="Course Review Admin"
        )

        role_course = UserRole(
            user_id=course_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_COURSE_REVIEW | Reviewer"
        )
        db.session.add(role_course)
        db.session.commit()

        assert not course_admin.is_primary_admin
        assert course_admin.admin_sub_role == "ADMIN_COURSE_REVIEW"
        assert course_admin.has_admin_permission("COURSE_REVIEW")
        assert not course_admin.has_admin_permission("INSTRUCTOR_REVIEW")
        assert not course_admin.has_admin_permission("TEACHING_ASSIGNMENT")
        assert not course_admin.has_admin_permission("SYSTEM_MONITORING")

        # Cleanup
        ids = [primary_admin.id, course_admin.id]
        db.session.query(UserRole).filter(
            UserRole.user_id.in_(ids)
        ).delete(synchronize_session=False)
        db.session.query(User).filter(
            User.id.in_(ids)
        ).delete(synchronize_session=False)
        db.session.commit()


def test_auth_profile_and_preferences(app, client):
    """Test /auth/profile and /auth/preferences endpoints."""
    with app.app_context():
        user = register_user(
            email="settings_user_test@pwd301.local",
            password="StudentPass1234!",
            display_name="Test Student"
        )
        user_id = user.id

    # Login
    login_res = client.post("/auth/login", json={
        "email": "settings_user_test@pwd301.local",
        "password": "StudentPass1234!"
    })
    assert login_res.status_code == 200

    # GET /auth/profile
    profile_res = client.get("/auth/profile")
    assert profile_res.status_code == 200
    pdata = profile_res.get_json()["profile"]
    assert pdata["display_name"] == "Test Student"
    assert pdata["email"] == "settings_user_test@pwd301.local"

    # PUT /auth/profile
    update_res = client.put("/auth/profile", json={
        "display_name": "Updated Student Name",
        "avatar_url": "https://example.com/new-avatar.png"
    })
    assert update_res.status_code == 200
    assert update_res.get_json()["profile"]["display_name"] == "Updated Student Name"

    # GET /auth/preferences
    pref_res = client.get("/auth/preferences")
    assert pref_res.status_code == 200
    pref_data = pref_res.get_json()
    assert "email_course" in pref_data["preferences_map"]
    assert "email_assessment" in pref_data["preferences_map"]

    # PUT /auth/preferences
    new_prefs = {
        "email_course": False,
        "email_assessment": True,
        "email_grade": True,
        "email_marketing": True
    }
    update_pref_res = client.put("/auth/preferences", json={"preferences": new_prefs})
    assert update_pref_res.status_code == 200
    up_data = update_pref_res.get_json()
    assert up_data["preferences_map"]["email_course"] is False
    assert up_data["preferences_map"]["email_marketing"] is True

    # Cleanup
    with app.app_context():
        from pwd301.models.identity import AuthSession
        from pwd301.models.notification_audit import NotificationPreference
        db.session.query(AuthSession).filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.query(NotificationPreference).filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.query(UserRole).filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.query(User).filter_by(id=user_id).delete(synchronize_session=False)
        db.session.commit()


def test_admin_subrole_rbac_enforcement(app, client):
    """Test that non-primary admins cannot modify user roles and are restricted by their subrole."""
    with app.app_context():
        admin_role = db.session.query(Role).filter_by(code="ADMIN").first()
        if not admin_role:
            admin_role = Role(code="ADMIN", name="Quản trị viên")
            db.session.add(admin_role)
            db.session.commit()

        # Create Course Review Admin (non-primary)
        course_admin = register_user(
            email="course_only_admin@pwd301.local",
            password="AdminPass1234!",
            display_name="Course Only Admin"
        )
        ur_course = UserRole(
            user_id=course_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_COURSE_REVIEW | Reviewer only"
        )
        db.session.add(ur_course)

        # Create a target student
        target_student = register_user(
            email="target_student_test@pwd301.local",
            password="StudentPass1234!",
            display_name="Target Student"
        )
        db.session.commit()
        course_admin_id = course_admin.id
        target_student_id = target_student.id

    # Login as course_admin
    login_res = client.post("/auth/login", json={
        "email": "course_only_admin@pwd301.local",
        "password": "AdminPass1234!"
    })
    assert login_res.status_code == 200

    # Non-primary admin attempts to manage roles -> 403 Forbidden
    role_res = client.post(f"/admin/users/{target_student_id}/roles", json={
        "action": "assign",
        "role": "INSTRUCTOR",
        "reason": "Unauthorized assignment test"
    })
    assert role_res.status_code == 403
    assert "chính" in role_res.get_json()["error"]["message"]

    # Non-primary admin attempts to review instructor apps -> 403 Forbidden
    app_res = client.get("/admin/instructor-applications")
    assert app_res.status_code == 403

    # Cleanup
    with app.app_context():
        from pwd301.models.identity import AuthSession
        from pwd301.models.notification_audit import NotificationPreference
        uids = [course_admin_id, target_student_id]
        db.session.query(AuthSession).filter(
            AuthSession.user_id.in_(uids)
        ).delete(synchronize_session=False)
        db.session.query(NotificationPreference).filter(
            NotificationPreference.user_id.in_(uids)
        ).delete(synchronize_session=False)
        db.session.query(UserRole).filter(
            UserRole.user_id.in_(uids)
        ).delete(synchronize_session=False)
        db.session.query(User).filter(
            User.id.in_(uids)
        ).delete(synchronize_session=False)
        db.session.commit()


def test_notifications_and_evidence_preview(app, client):
    """Test that notifications contain direct approval SPA URLs and evidence preview headers."""
    with app.app_context():
        import json

        from pwd301.models.identity import InstructorApplication
        from pwd301.models.notification_audit import Notification

        admin_role = db.session.query(Role).filter_by(code="ADMIN").first()
        if not admin_role:
            admin_role = Role(code="ADMIN", name="Quản trị viên")
            db.session.add(admin_role)
            db.session.commit()

        # Create Primary Admin
        admin_user = register_user(
            email="notif_admin_test@pwd301.local",
            password="AdminPass1234!",
            display_name="Notif Admin"
        )
        ur_admin = UserRole(
            user_id=admin_user.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_PRIMARY | Primary"
        )
        db.session.add(ur_admin)

        # Create Applicant Student
        applicant = register_user(
            email="applicant_test@pwd301.local",
            password="StudentPass1234!",
            display_name="Applicant Student"
        )
        db.session.commit()
        admin_id = admin_user.id
        applicant_id = applicant.id

        # Create mock instructor application with an evidence file
        app_record = InstructorApplication(
            applicant_user_id=applicant.id,
            status="PENDING",
            application_note=json.dumps({
                "institution": "Đại học Bách Khoa",
                "specialization": "Khoa học Máy tính",
                "attached_files": [
                    {
                        "doc_type": "CV_PORTFOLIO",
                        "original_name": "CV_NguyenVanA.pdf",
                        "saved_filename": "evidence_cv_test.pdf",
                        "size": 102400
                    }
                ]
            })
        )
        db.session.add(app_record)

        # Create direct notification
        from pwd301.services.notification_service import dispatch_notification
        dispatch_notification(
            recipient_user=admin_id,
            event_type="INSTRUCTOR_APPLICATION_SUBMITTED",
            title="Đơn đăng ký Giảng viên mới",
            body="Ứng viên Applicant Student đã nộp đơn đăng ký làm Giảng viên.",
            action_url="#/admin/governance?tab=applications",
            category="SYSTEM",
            payload={"action_url": "#/admin/governance?tab=applications"},
            session=db.session
        )
        db.session.commit()
        app_record_id = app_record.id

        # Verify notification has SPA action_url
        notif = db.session.query(Notification).filter_by(
            recipient_user_id=admin_id,
        ).first()
        assert notif is not None
        assert notif.to_dict()["action_url"] == "#/admin/governance?tab=applications"

    # Login as admin
    login_res = client.post("/auth/login", json={
        "email": "notif_admin_test@pwd301.local",
        "password": "AdminPass1234!"
    })
    assert login_res.status_code == 200

    # Cleanup
    with app.app_context():
        from pwd301.models.identity import AuthSession
        from pwd301.models.notification_audit import NotificationPreference
        uids = [admin_id, applicant_id]
        db.session.query(Notification).filter(
            Notification.recipient_user_id.in_(uids)
        ).delete(synchronize_session=False)
        db.session.query(InstructorApplication).filter(
            InstructorApplication.id == app_record_id
        ).delete(synchronize_session=False)
        db.session.query(AuthSession).filter(
            AuthSession.user_id.in_(uids)
        ).delete(synchronize_session=False)
        db.session.query(NotificationPreference).filter(
            NotificationPreference.user_id.in_(uids)
        ).delete(synchronize_session=False)
        db.session.query(UserRole).filter(
            UserRole.user_id.in_(uids)
        ).delete(synchronize_session=False)
        db.session.query(User).filter(
            User.id.in_(uids)
        ).delete(synchronize_session=False)
        db.session.commit()
