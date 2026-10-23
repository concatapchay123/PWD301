"""Unit tests for TASK-120: PayOS payment integration, digital wallet, course purchase, and ADMIN_FINANCIAL governance."""

import json
import pytest

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment
from pwd301.models.identity import User
from pwd301.models.wallet import UserBalance, WalletTransaction
from pwd301.services.payos_service import (
    create_payos_payment_link,
    create_signature,
    generate_12char_transfer_code,
    verify_webhook_signature,
)
from pwd301.services.wallet_service import (
    create_direct_course_qr,
    deposit_via_payos,
    get_cashflow_stats,
    get_or_create_balance,
    handle_payos_webhook,
    purchase_course_with_wallet,
    revoke_transaction,
    verify_deposit_manually,
)
from pwd301.services.exceptions import ValidationError, ForbiddenError


def test_12char_transfer_code_format(app):
    """Verify that generated transfer description is strictly 12 characters."""
    with app.app_context():
        user = User(email="student@test.com", password_hash="hash", display_name="Student Test")
        db.session.add(user)
        db.session.commit()

        code = generate_12char_transfer_code(user.id)
        assert len(code) == 12
        assert code.startswith("PPTQ")
        assert code.isalnum()
        assert code.isupper()


def test_payos_hmac_signature_and_verification():
    """Verify HMAC-SHA256 signature calculation and webhook verification."""
    data = {
        "amount": 100000,
        "cancelUrl": "http://test/cancel",
        "description": "PPTQU001A9B1",
        "orderCode": 12345678,
        "returnUrl": "http://test/return",
    }
    sig = create_signature(data, checksum_key="test_key_123")
    assert isinstance(sig, str)
    assert len(sig) == 64

    # Webhook payload verification
    payload = {
        "code": "00",
        "desc": "success",
        "data": data,
        "signature": sig,
    }
    assert verify_webhook_signature(payload, checksum_key="test_key_123") is True

    # Tampered data should fail
    tampered_payload = {
        "code": "00",
        "desc": "success",
        "data": {**data, "amount": 200000},
        "signature": sig,
    }
    assert verify_webhook_signature(tampered_payload, checksum_key="test_key_123") is False


def test_deposit_and_webhook_credit(app):
    """Verify PayOS deposit link creation and subsequent webhook credit to student balance."""
    with app.app_context():
        user = User(email="student_wallet@test.com", password_hash="hash", display_name="Student Wallet")
        db.session.add(user)
        db.session.commit()

        # 1. Create deposit request
        res = deposit_via_payos(user=user, amount=500000, session=db.session)
        assert res["status"] == "PENDING"
        assert res["amount"] == 500000
        assert len(res["transfer_code_12"]) == 12

        tx = db.session.query(WalletTransaction).filter(WalletTransaction.id == res["transaction_id"]).first()
        assert tx is not None
        assert tx.status == "PENDING"

        # 2. Simulate valid PayOS Webhook
        from pwd301.services.payos_service import PAYOS_CHECKSUM_KEY

        webhook_data = {
            "orderCode": tx.order_code,
            "amount": 500000,
            "description": tx.transfer_code_12,
        }
        sig = create_signature(webhook_data, checksum_key=PAYOS_CHECKSUM_KEY)
        webhook_payload = {
            "code": "00",
            "desc": "success",
            "data": webhook_data,
            "signature": sig,
        }

        wh_res = handle_payos_webhook(webhook_payload, session=db.session)
        assert wh_res["success"] is True

        # Verify balance
        bal = get_or_create_balance(user.id, session=db.session)
        assert bal.balance == 500000

        tx_updated = db.session.query(WalletTransaction).filter(WalletTransaction.id == tx.id).first()
        assert tx_updated.status == "COMPLETED"
        assert tx_updated.balance_after == 500000

        # 3. Idempotency test: Re-sending webhook should not double-credit
        wh_res2 = handle_payos_webhook(webhook_payload, session=db.session)
        assert wh_res2["success"] is True
        bal_after = get_or_create_balance(user.id, session=db.session)
        assert bal_after.balance == 500000  # Still 500,000


def test_purchase_course_with_wallet(app):
    """Verify purchasing a course using wallet balance and auto enrollment."""
    with app.app_context():
        user = User(email="buyer@test.com", password_hash="hash", display_name="Buyer Student")
        course = Course(
            course_code="CS101",
            course_code_normalized="cs101",
            title="Intro to CS",
            title_normalized="intro to cs",
            status="PUBLISHED",
            price=200000,
        )
        db.session.add_all([user, course])
        db.session.commit()

        # Give user 300,000 balance
        user_bal = get_or_create_balance(user.id, session=db.session)
        user_bal.balance = 300000
        db.session.commit()

        # Purchase course
        res = purchase_course_with_wallet(user=user, course_id=course.id, session=db_session if 'db_session' in locals() else db.session)
        assert res["success"] is True
        assert res["enrolled"] is True
        assert res["balance"] == 100000

        # Verify enrollment created
        enr = db.session.query(Enrollment).filter(
            Enrollment.student_user_id == user.id,
            Enrollment.course_id == course.id,
        ).first()
        assert enr is not None
        assert enr.status == "ACTIVE"


def test_purchase_course_insufficient_balance(app):
    """Verify that purchase fails cleanly if wallet balance is insufficient."""
    with app.app_context():
        user = User(email="poor@test.com", password_hash="hash", display_name="Poor Student")
        course = Course(
            course_code="CS202",
            course_code_normalized="cs202",
            title="Advanced CS",
            title_normalized="advanced cs",
            status="PUBLISHED",
            price=500000,
        )
        db.session.add_all([user, course])
        db.session.commit()

        # User has 100,000 balance (< 500,000)
        user_bal = get_or_create_balance(user.id, session=db.session)
        user_bal.balance = 100000
        db.session.commit()

        with pytest.raises(ValidationError) as exc:
            purchase_course_with_wallet(user=user, course_id=course.id, session=db.session)
        assert "Số dư tài khoản không đủ" in str(exc.value)


def test_revoke_deposit_and_cancel_enrollment(app):
    """Verify that admin revoking abnormal deposit deducts balance and revokes enrolled courses."""
    with app.app_context():
        admin = User(email="admin@test.com", password_hash="hash", display_name="Super Admin", status="ACTIVE")
        student = User(email="bad_student@test.com", password_hash="hash", display_name="Bad Student", status="ACTIVE")
        course = Course(
            course_code="SEC101",
            course_code_normalized="sec101",
            title="Security Course",
            title_normalized="security course",
            status="PUBLISHED",
            price=400000,
        )
        db.session.add_all([admin, student, course])
        db.session.commit()

        # Set admin role
        from pwd301.models.identity import Role, UserRole
        role_admin = Role(code="ADMIN", name="Administrator")
        db.session.add(role_admin)
        db.session.flush()
        db.session.add(UserRole(user_id=admin.id, role_id=role_admin.id))
        db.session.commit()

        # Deposit 400,000
        deposit_res = deposit_via_payos(user=student, amount=400000, session=db.session)
        tx = db.session.query(WalletTransaction).filter(WalletTransaction.id == deposit_res["transaction_id"]).first()
        tx.status = "COMPLETED"
        student_bal = get_or_create_balance(student.id, session=db.session)
        student_bal.balance = 400000
        db.session.commit()

        # Student purchases course
        purchase_res = purchase_course_with_wallet(user=student, course_id=course.id, session=db.session)
        assert purchase_res["enrolled"] is True
        assert student_bal.balance == 0

        # Admin revokes the 400,000 deposit transaction
        revoke_res = revoke_transaction(
            admin_user=admin,
            tx_id=tx.id,
            reason="Dấu hiệu chuyển khoản giả mạo",
            session=db.session,
        )
        assert revoke_res["success"] is True
        assert revoke_res["revoked_amount"] == 400000
        assert len(revoke_res["cancelled_courses"]) >= 1

        # Verify course enrollment cancelled
        enr = db.session.query(Enrollment).filter(
            Enrollment.student_user_id == student.id,
            Enrollment.course_id == course.id,
        ).first()
        assert enr.status == "LEFT"  # Un-enrolled!


def test_admin_financial_rbac(app, client):
    """Verify that Primary Admin and ADMIN_FINANCIAL have cashflow access, while other roles are rejected with 403."""
    with app.app_context():
        from pwd301.models.identity import Role, UserRole
        from tests.conftest import login_web_user

        role_admin = db.session.query(Role).filter_by(code="ADMIN").first()
        if not role_admin:
            role_admin = Role(code="ADMIN", name="Administrator")
            db.session.add(role_admin)
            db.session.flush()

        role_student = db.session.query(Role).filter_by(code="STUDENT").first()
        if not role_student:
            role_student = Role(code="STUDENT", name="Student")
            db.session.add(role_student)
            db.session.flush()

        primary_admin = User(email="super_admin@test.com", password_hash="hash", display_name="Super Admin", status="ACTIVE")
        financial_admin = User(email="financial_admin@test.com", password_hash="hash", display_name="Finance Admin", status="ACTIVE")
        course_admin = User(email="course_admin@test.com", password_hash="hash", display_name="Course Review Admin", status="ACTIVE")
        student_user = User(email="plain_student@test.com", password_hash="hash", display_name="Student User", status="ACTIVE")

        db.session.add_all([primary_admin, financial_admin, course_admin, student_user])
        db.session.flush()

        db.session.add_all([
            UserRole(user_id=primary_admin.id, role_id=role_admin.id, assignment_reason="SUB_ROLE:ADMIN_PRIMARY"),
            UserRole(user_id=financial_admin.id, role_id=role_admin.id, assignment_reason="SUB_ROLE:ADMIN_FINANCIAL"),
            UserRole(user_id=course_admin.id, role_id=role_admin.id, assignment_reason="SUB_ROLE:ADMIN_COURSE_REVIEW"),
            UserRole(user_id=student_user.id, role_id=role_student.id),
        ])
        db.session.commit()

        # 1. Primary Admin -> 200 OK
        login_web_user(client, primary_admin)
        res = client.get("/admin/cashflow/dashboard")
        assert res.status_code == 200
        assert res.json.get("success") is True

        # 2. Financial Admin -> 200 OK
        login_web_user(client, financial_admin)
        res_fin = client.get("/admin/cashflow/dashboard")
        assert res_fin.status_code == 200
        assert res_fin.json.get("success") is True

        # 3. Course Review Admin -> 403 Forbidden
        login_web_user(client, course_admin)
        res_course = client.get("/admin/cashflow/dashboard")
        assert res_course.status_code == 403

        # 4. Student User -> 403 Forbidden
        login_web_user(client, student_user)
        res_stu = client.get("/admin/cashflow/dashboard")
        assert res_stu.status_code == 403


def test_payos_authentic_bank_credentials(app):
    """Verify that PayOS payment link and QR generation strictly output authentic MBBank merchant details."""
    with app.app_context():
        user = User(email="bank_test_student@test.com", password_hash="hash", display_name="Bank Student")
        db.session.add(user)
        db.session.commit()

        deposit_res = deposit_via_payos(user=user, amount=100000, session=db.session)
        assert deposit_res["bin"] == "970422"
        assert "MB" in deposit_res["bank_name"]
        assert "account_name" in deposit_res
        assert "account_number" in deposit_res
        assert len(deposit_res["qr_code"]) > 0


