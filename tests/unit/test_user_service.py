"""Unit tests for user service and security token service.

Verifies:
- Email normalization and validation.
- User registration with password hashing, student role assignment, and duplicate rejection.
- Password verification, password change with auth_version increment, and admin set_password.
- Profile update and email verification marking.
- Security token generation, SHA-256 binary hash storage, and expiry management.
- Token consumption, rejection of expired or reused tokens, and purpose mismatch enforcement.
- Workflows: verify_email_with_token, reset_password_with_token, and apply_email_change_with_token.
"""

from __future__ import annotations

import datetime
import hashlib
import uuid

import pytest

from pwd301.extensions import db
from pwd301.models.identity import Role
from pwd301.models.types import utc_now
from pwd301.services.auth_token_service import (
    SecurityTokenPurpose,
    apply_email_change_with_token,
    consume_security_token,
    create_security_token,
    reset_password_with_token,
    verify_email_with_token,
    verify_security_token,
)
from pwd301.services.exceptions import (
    AccountNotActiveError,
    InvalidEmailError,
    InvalidPasswordError,
    InvalidTokenError,
    TokenAlreadyConsumedError,
    TokenExpiredError,
    TokenPurposeMismatchError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from pwd301.services.user_service import (
    change_password,
    get_user_by_email,
    get_user_by_id,
    get_user_by_public_id,
    mark_email_verified,
    normalize_email,
    register_user,
    set_password,
    update_profile,
    validate_password,
    verify_password,
)

# ---------------------------------------------------------------------------
# Email Normalization & Validation Tests
# ---------------------------------------------------------------------------


def test_normalize_email_valid():
    """Verify email normalization strips spaces and converts to lowercase."""
    assert normalize_email("  Student@Example.COM  ") == "student@example.com"
    assert normalize_email("JOHN.DOE+tag@SUB.DOMAIN.ORG") == "john.doe+tag@sub.domain.org"


@pytest.mark.parametrize(
    "invalid_input",
    [
        "",
        "   ",
        "plainaddress",
        "@missinglocal.com",
        "missingdomain@",
        "missingdot@domain",
        "double@@domain.com",
        "spaces in@domain.com",
        "a" * 315 + "@example.com",  # exceeds 320 chars
    ],
)
def test_normalize_email_invalid(invalid_input: str):
    """Verify InvalidEmailError is raised for malformed email inputs."""
    with pytest.raises(InvalidEmailError):
        normalize_email(invalid_input)


# ---------------------------------------------------------------------------
# Password Validation Tests
# ---------------------------------------------------------------------------


def test_validate_password():
    """Verify password validation enforces minimum length."""
    with pytest.raises(InvalidPasswordError):
        validate_password("")

    with pytest.raises(InvalidPasswordError):
        validate_password("short")

    # 8 chars or more should pass
    validate_password("12345678")
    validate_password("SecurePassword@2026")


# ---------------------------------------------------------------------------
# User Registration & Management Tests
# ---------------------------------------------------------------------------


def test_register_user_success(app):
    """Verify successful user registration with hashing, defaults, and STUDENT role."""
    with app.app_context():
        # Ensure STUDENT role exists in DB
        student_role = Role(code="STUDENT", name="Student")
        db.session.add(student_role)
        db.session.commit()

        user = register_user(
            email="  NEW_STUDENT@pwd301.local ",
            password="StrongPassword@123",
            display_name="New Student",
        )

        assert user.id is not None
        assert user.public_id is not None
        assert isinstance(user.public_id, uuid.UUID)
        assert user.email == "new_student@pwd301.local"
        assert user.display_name == "New Student"
        assert user.status == "ACTIVE"
        assert user.auth_version == 1
        assert user.email_verified_at is None
        assert user.created_at is not None

        # Invariant: Raw password must NEVER be persisted
        assert user.password_hash != "StrongPassword@123"
        assert verify_password(user, "StrongPassword@123") is True
        assert verify_password(user, "WrongPassword") is False

        # Invariant: Default STUDENT role assigned
        assert len(user.roles) == 1
        assert user.roles[0].code == "STUDENT"


def test_register_user_duplicate_email_rejected(app):
    """Verify duplicate email registration is rejected with UserAlreadyExistsError."""
    with app.app_context():
        register_user(
            email="duplicate@pwd301.local",
            password="Password@123",
            display_name="User One",
        )

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            register_user(
                email="  DUPLICATE@pwd301.local  ",
                password="AnotherPassword@123",
                display_name="User Two",
            )
        assert "duplicate@pwd301.local" in str(exc_info.value)


def test_register_user_invalid_inputs(app):
    """Verify registration rejects invalid display name or invalid email."""
    with app.app_context():
        with pytest.raises(InvalidEmailError):
            register_user("invalid-email", "Password@123", "Valid Name")

        with pytest.raises(InvalidPasswordError):
            register_user("valid@pwd301.local", "short", "Valid Name")

        with pytest.raises(ValueError):
            register_user("valid@pwd301.local", "Password@123", "   ")


def test_get_user_helpers(app):
    """Verify user lookup by primary key, public UUID, and normalized email."""
    with app.app_context():
        user = register_user("lookup@pwd301.local", "Password@123", "Lookup User")

        # Lookup by ID
        by_id = get_user_by_id(user.id)
        assert by_id is not None
        assert by_id.id == user.id
        assert get_user_by_id(999999) is None

        # Lookup by public_id
        by_uuid = get_user_by_public_id(user.public_id)
        assert by_uuid is not None
        assert by_uuid.id == user.id

        by_uuid_str = get_user_by_public_id(str(user.public_id))
        assert by_uuid_str is not None
        assert by_uuid_str.id == user.id

        assert get_user_by_public_id(uuid.uuid4()) is None
        assert get_user_by_public_id("invalid-uuid-string") is None

        # Lookup by email
        by_email = get_user_by_email("  LOOKUP@pwd301.local  ")
        assert by_email is not None
        assert by_email.id == user.id
        assert get_user_by_email("nonexistent@pwd301.local") is None
        assert get_user_by_email("malformed_email") is None


def test_change_password_increments_auth_version(app):
    """Verify password change verifies current password and increments auth_version."""
    with app.app_context():
        user = register_user("pwdchange@pwd301.local", "OldPassword@123", "Pwd User")
        assert user.auth_version == 1

        # Failure: Wrong current password
        with pytest.raises(InvalidPasswordError):
            change_password(user.id, "WrongOldPassword", "NewPassword@123")
        assert user.auth_version == 1

        # Failure: Same new password
        with pytest.raises(InvalidPasswordError):
            change_password(user.id, "OldPassword@123", "OldPassword@123")

        # Success
        updated = change_password(user.id, "OldPassword@123", "NewPassword@123")
        assert updated.auth_version == 2
        assert verify_password(updated, "OldPassword@123") is False
        assert verify_password(updated, "NewPassword@123") is True

        # Subsequent change increments again
        updated2 = change_password(user.id, "NewPassword@123", "ThirdPassword@123")
        assert updated2.auth_version == 3


def test_change_password_inactive_user_rejected(app):
    """Verify inactive/suspended users cannot change their password."""
    with app.app_context():
        user = register_user("suspended@pwd301.local", "OldPassword@123", "Suspended")
        user.status = "SUSPENDED"
        user.suspended_at = utc_now()
        db.session.commit()

        with pytest.raises(AccountNotActiveError):
            change_password(user.id, "OldPassword@123", "NewPassword@123")


def test_set_password_admin_or_reset(app):
    """Verify set_password directly sets password and increments auth_version."""
    with app.app_context():
        user = register_user("directpwd@pwd301.local", "InitialPass@123", "Direct Pwd")
        assert user.auth_version == 1

        updated = set_password(user.id, "DirectNewPass@123")
        assert updated.auth_version == 2
        assert verify_password(updated, "DirectNewPass@123") is True


def test_update_profile(app):
    """Verify profile updating of display_name and avatar."""
    with app.app_context():
        user = register_user("profile@pwd301.local", "Password@123", "Old Name")
        assert user.display_name == "Old Name"
        assert user.avatar_file_asset_id is None

        updated = update_profile(user.id, display_name="Updated Name")
        assert updated.display_name == "Updated Name"

        with pytest.raises(ValueError):
            update_profile(user.id, display_name="   ")

        with pytest.raises(UserNotFoundError):
            update_profile(999999, display_name="Ghost")


def test_mark_email_verified(app):
    """Verify marking email verified sets timestamp."""
    with app.app_context():
        user = register_user("unverified@pwd301.local", "Password@123", "Unverified")
        assert user.email_verified_at is None

        updated = mark_email_verified(user.id)
        assert updated.email_verified_at is not None
        assert isinstance(updated.email_verified_at, datetime.datetime)


# ---------------------------------------------------------------------------
# Security Token Lifecycle Tests
# ---------------------------------------------------------------------------


def test_create_security_token_storage(app):
    """Verify security token generation, SHA-256 storage, and raw token return."""
    with app.app_context():
        user = register_user("tokenuser@pwd301.local", "Password@123", "Token User")

        token_record, raw_token = create_security_token(
            user_id=user.id,
            purpose=SecurityTokenPurpose.EMAIL_VERIFY,
        )

        assert token_record.id is not None
        assert token_record.user_id == user.id
        assert token_record.purpose == "EMAIL_VERIFY"
        assert token_record.consumed_at is None
        assert token_record.expires_at > token_record.created_at

        # Invariant: Raw token is NOT stored in DB
        assert isinstance(raw_token, str)
        assert len(raw_token) >= 32
        expected_hash = hashlib.sha256(raw_token.encode("utf-8")).digest()
        assert token_record.token_hash == expected_hash
        assert len(token_record.token_hash) == 32


def test_create_security_token_invalidates_prior_unconsumed(app):
    """Verify creating a new token of same purpose invalidates older pending tokens."""
    with app.app_context():
        user = register_user("tokensupersede@pwd301.local", "Password@123", "Supersede")

        tok1, raw1 = create_security_token(user.id, SecurityTokenPurpose.EMAIL_VERIFY)
        assert tok1.consumed_at is None

        tok2, raw2 = create_security_token(user.id, SecurityTokenPurpose.EMAIL_VERIFY)

        # tok1 should now be consumed/invalidated
        db.session.refresh(tok1)
        assert tok1.consumed_at is not None
        assert tok2.consumed_at is None

        # Attempting to verify or consume raw1 should fail as already consumed
        with pytest.raises(TokenAlreadyConsumedError):
            verify_security_token(raw1, SecurityTokenPurpose.EMAIL_VERIFY)

        # raw2 should verify cleanly
        valid = verify_security_token(raw2, SecurityTokenPurpose.EMAIL_VERIFY)
        assert valid.id == tok2.id


def test_verify_and_consume_security_token(app):
    """Verify token validation and atomic consumption."""
    with app.app_context():
        user = register_user("consume@pwd301.local", "Password@123", "Consumer")

        tok, raw = create_security_token(user.id, SecurityTokenPurpose.PASSWORD_RESET)

        # Verification without consumption does not set consumed_at
        verified = verify_security_token(raw, SecurityTokenPurpose.PASSWORD_RESET)
        assert verified.id == tok.id
        assert verified.consumed_at is None

        # Purpose mismatch
        with pytest.raises(TokenPurposeMismatchError):
            verify_security_token(raw, SecurityTokenPurpose.EMAIL_VERIFY)

        # Unknown token
        with pytest.raises(InvalidTokenError):
            verify_security_token(
                "completely-invalid-raw-token", SecurityTokenPurpose.PASSWORD_RESET
            )

        # Consume token
        consumed = consume_security_token(raw, SecurityTokenPurpose.PASSWORD_RESET)
        assert consumed.consumed_at is not None

        # Second consumption fails
        with pytest.raises(TokenAlreadyConsumedError):
            consume_security_token(raw, SecurityTokenPurpose.PASSWORD_RESET)


def test_verify_security_token_expired(app):
    """Verify expired security token is rejected with TokenExpiredError."""
    with app.app_context():
        user = register_user("expired@pwd301.local", "Password@123", "Expired")

        # Issue token with expires_in_seconds=1
        tok, raw = create_security_token(
            user.id,
            SecurityTokenPurpose.EMAIL_VERIFY,
            expires_in_seconds=1,
        )

        # Manually backdate created_at and expires_at to simulate expiration
        tok.created_at = utc_now() - datetime.timedelta(hours=2)
        tok.expires_at = utc_now() - datetime.timedelta(hours=1)
        db.session.commit()

        with pytest.raises(TokenExpiredError):
            verify_security_token(raw, SecurityTokenPurpose.EMAIL_VERIFY)


# ---------------------------------------------------------------------------
# Convenience Workflow Tests
# ---------------------------------------------------------------------------


def test_verify_email_with_token(app):
    """Verify email verification workflow via token."""
    with app.app_context():
        user = register_user("verifyflow@pwd301.local", "Password@123", "Verify Flow")
        assert user.email_verified_at is None

        _, raw_token = create_security_token(user.id, SecurityTokenPurpose.EMAIL_VERIFY)

        updated_user = verify_email_with_token(raw_token)
        assert updated_user.id == user.id
        assert updated_user.email_verified_at is not None

        # Token is single-use; reuse fails
        with pytest.raises(TokenAlreadyConsumedError):
            verify_email_with_token(raw_token)


def test_reset_password_with_token(app):
    """Verify password reset workflow via token."""
    with app.app_context():
        user = register_user("resetflow@pwd301.local", "InitialPass@123", "Reset Flow")
        assert user.auth_version == 1

        _, raw_token = create_security_token(user.id, SecurityTokenPurpose.PASSWORD_RESET)

        updated_user = reset_password_with_token(raw_token, "NewResetPass@456")
        assert updated_user.id == user.id
        assert updated_user.auth_version == 2
        assert verify_password(updated_user, "InitialPass@123") is False
        assert verify_password(updated_user, "NewResetPass@456") is True

        # Token is single-use
        with pytest.raises(TokenAlreadyConsumedError):
            reset_password_with_token(raw_token, "AnotherPass@789")


def test_apply_email_change_with_token(app):
    """Verify email change workflow via token."""
    with app.app_context():
        user = register_user("old_address@pwd301.local", "Password@123", "Email Changer")
        assert user.auth_version == 1

        _, raw_token = create_security_token(
            user.id,
            SecurityTokenPurpose.EMAIL_CHANGE,
            pending_email="  NEW_ADDRESS@pwd301.local  ",
        )

        updated_user = apply_email_change_with_token(raw_token)
        assert updated_user.id == user.id
        assert updated_user.email == "new_address@pwd301.local"
        assert updated_user.email_verified_at is not None
        assert updated_user.auth_version == 2

        # Invariant: Looking up old email now yields None; new email yields user
        assert get_user_by_email("old_address@pwd301.local") is None
        assert get_user_by_email("new_address@pwd301.local") is not None


def test_apply_email_change_conflict_rejected(app):
    """Verify email change fails if target email is taken before token consumption."""
    with app.app_context():
        user1 = register_user("user1@pwd301.local", "Password@123", "User 1")
        _user2 = register_user("taken@pwd301.local", "Password@123", "User 2")

        # user1 requests change to taken@pwd301.local
        # Note: at creation time, suppose taken wasn't checked or was registered right after
        _, raw_token = create_security_token(
            user1.id,
            SecurityTokenPurpose.EMAIL_CHANGE,
            pending_email="taken@pwd301.local",
        )

        with pytest.raises(UserAlreadyExistsError):
            apply_email_change_with_token(raw_token)
