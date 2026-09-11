"""User lifecycle and management service for PWD301.

Provides business logic for:
- User registration with normalized email, password hashing, and role assignment.
- User profile updates and password changes (with auth_version incrementation).
- User retrieval by primary key, public UUID, or normalized email.
- Password verification using Werkzeug adaptive hashing.
"""

from __future__ import annotations

import datetime
import json
import uuid
from typing import Any

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, scoped_session
from werkzeug.security import check_password_hash, generate_password_hash

from pwd301.extensions import db
from pwd301.models.identity import Role, User, UserRole
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.types import utc_now
from pwd301.services.exceptions import (
    AccountNotActiveError,
    InvalidEmailError,
    InvalidPasswordError,
    InvalidRoleAssignmentError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from pwd301.services.jwt_auth_service import revoke_all_user_tokens
from pwd301.services.session_auth_service import revoke_all_user_sessions

MIN_PASSWORD_LENGTH = 8
MAX_EMAIL_LENGTH = 320


def normalize_email(email: str) -> str:
    """Normalize and validate an email address.

    Trims leading and trailing whitespace and converts to lowercase.
    Ensures email contains an '@' separator and a valid domain format.

    Args:
        email: The raw email address string.

    Returns:
        The normalized lowercase email string.

    Raises:
        InvalidEmailError: If the email is empty, malformed, or exceeds 320 characters.
    """
    if not email or not isinstance(email, str):
        raise InvalidEmailError("Email address cannot be empty.")

    normalized = email.strip().lower()
    if len(normalized) > MAX_EMAIL_LENGTH:
        raise InvalidEmailError(
            f"Email address exceeds maximum allowed length of {MAX_EMAIL_LENGTH} characters."
        )

    if " " in normalized:
        raise InvalidEmailError("Invalid email format: email cannot contain whitespace.")

    if normalized.count("@") != 1:
        raise InvalidEmailError("Invalid email format: email must contain exactly one '@'.")

    local_part, domain_part = normalized.split("@")
    if (
        not local_part
        or not domain_part
        or "." not in domain_part
        or domain_part.startswith(".")
        or domain_part.endswith(".")
    ):
        raise InvalidEmailError("Invalid email format: invalid domain structure.")

    return normalized


def validate_password(password: str) -> None:
    """Validate password criteria before hashing.

    Args:
        password: Raw password to validate.

    Raises:
        InvalidPasswordError: If the password is empty or does not meet minimum length.
    """
    if not password or not isinstance(password, str):
        raise InvalidPasswordError("Password cannot be empty.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise InvalidPasswordError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )


def register_user(
    email: str,
    password: str,
    display_name: str,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Register a new user in the system.

    Invariants enforced:
    - Email is normalized (stripped, lowercased) and unique.
    - Password is hashed using Werkzeug adaptive hash; raw password is never stored.
    - User account defaults to ACTIVE status and auth_version = 1.
    - Email verification is initially None.
    - Assigns canonical STUDENT role by default if available.
    - Concurrency and duplicate email errors are handled safely via transaction rollback.

    Args:
        email: The user's registration email.
        password: The user's desired raw password.
        display_name: The user's public display name.
        session: Optional SQLAlchemy database session (defaults to db.session).

    Returns:
        The newly created and persisted User instance.

    Raises:
        InvalidEmailError: If email address is malformed.
        InvalidPasswordError: If password does not meet criteria.
        UserAlreadyExistsError: If a user with the same email already exists.
        ValueError: If display_name is empty.
    """
    sess = session if session is not None else db.session

    norm_email = normalize_email(email)
    validate_password(password)

    cleaned_display_name = display_name.strip() if display_name else ""
    if not cleaned_display_name:
        raise ValueError("Display name cannot be empty.")

    # Check for existing user before insertion
    existing = sess.query(User).filter(User.email_normalized == norm_email).first()
    if existing is not None:
        raise UserAlreadyExistsError(f"User with email '{norm_email}' already exists.")

    password_hash = generate_password_hash(password)

    user = User(
        email=norm_email,
        password_hash=password_hash,
        display_name=cleaned_display_name,
        status="ACTIVE",
        auth_version=1,
        email_verified_at=None,
    )

    # Assign default STUDENT role if it exists in the database
    student_role = sess.query(Role).filter(Role.code == "STUDENT").first()
    if student_role is not None:
        user.roles.append(student_role)

    sess.add(user)
    try:
        sess.commit()
    except IntegrityError as exc:
        sess.rollback()
        raise UserAlreadyExistsError(f"User with email '{norm_email}' already exists.") from exc
    except Exception:
        sess.rollback()
        raise

    return user


def get_user_by_id(
    user_id: int,
    session: Session | scoped_session[Any] | None = None,
) -> User | None:
    """Retrieve a user by primary key ID."""
    sess = session if session is not None else db.session
    return sess.get(User, user_id)


def get_user_by_public_id(
    public_id: uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> User | None:
    """Retrieve a user by public UUID."""
    sess = session if session is not None else db.session
    if isinstance(public_id, str):
        try:
            target_uuid = uuid.UUID(public_id)
        except ValueError:
            return None
    else:
        target_uuid = public_id

    return sess.query(User).filter(User.public_id == target_uuid).first()


def get_user_by_email(
    email: str,
    session: Session | scoped_session[Any] | None = None,
) -> User | None:
    """Retrieve a user by email address after normalization."""
    sess = session if session is not None else db.session
    try:
        norm_email = normalize_email(email)
    except InvalidEmailError:
        return None

    return sess.query(User).filter(User.email_normalized == norm_email).first()


# Constant-time dummy password hash for side-channel & timing-attack mitigation
DUMMY_PASSWORD_HASH = generate_password_hash("pwd301-timing-defense-sentinel")


def verify_password(user: User | None, password: str) -> bool:
    """Verify a raw password against user's stored password hash in constant time.

    Mitigates side-channel timing leaks and email enumeration:
    If user is None or user.password_hash is empty, executes check_password_hash
    against a precomputed dummy hash, ensuring response time parity regardless
    of whether the user account exists.
    """
    if user is None or not user.password_hash:
        check_password_hash(DUMMY_PASSWORD_HASH, password or "")
        return False
    if not password:
        check_password_hash(DUMMY_PASSWORD_HASH, "")
        return False
    return check_password_hash(user.password_hash, password)


def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Change a user's password after verifying the current password.

    Invariants enforced:
    - Current password must be verified before accepting the new password.
    - New password must meet complexity requirements and differ from current password.
    - Password change increments auth_version by 1, revoking active sessions.

    Args:
        user_id: Primary key of the user.
        current_password: The user's current raw password.
        new_password: The user's desired new raw password.
        session: Optional SQLAlchemy database session.

    Returns:
        The updated User instance.

    Raises:
        UserNotFoundError: If user does not exist.
        AccountNotActiveError: If user account is suspended or inactive.
        InvalidPasswordError: If current password is wrong or new password is invalid.
    """
    sess = session if session is not None else db.session
    user = sess.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {user_id} not found.")

    if not user.is_active:
        raise AccountNotActiveError(f"Account for user {user_id} is not active.")

    if not verify_password(user, current_password):
        raise InvalidPasswordError("Current password is incorrect.")

    validate_password(new_password)
    if current_password == new_password:
        raise InvalidPasswordError("New password must be different from current password.")

    user.password_hash = generate_password_hash(new_password)
    user.auth_version += 1
    user.updated_at = utc_now()

    revoke_all_user_sessions(user.id, session=sess)
    revoke_all_user_tokens(user.id, session=sess)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return user


def set_password(
    user_id: int,
    new_password: str,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Directly set a new password for a user (e.g. password reset or admin action).

    Increments auth_version by 1 and revokes all active sessions and tokens.

    Args:
        user_id: Primary key of the user.
        new_password: The user's new raw password.
        session: Optional SQLAlchemy database session.

    Returns:
        The updated User instance.

    Raises:
        UserNotFoundError: If user does not exist.
        InvalidPasswordError: If new password is invalid.
    """
    sess = session if session is not None else db.session
    user = sess.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {user_id} not found.")

    validate_password(new_password)
    user.password_hash = generate_password_hash(new_password)
    user.auth_version += 1
    user.updated_at = utc_now()

    revoke_all_user_sessions(user.id, session=sess)
    revoke_all_user_tokens(user.id, session=sess)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return user


def suspend_user(
    user_id: int,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Suspend a user account and immediately revoke all active sessions and tokens.

    Invariants enforced:
    - User status is set to 'SUSPENDED'.
    - suspended_at timestamp is set to UTC now.
    - auth_version is incremented by 1.
    - All active AuthSession records are revoked.
    - All active JwtTokenGrant records are revoked.
    - Performed in a single atomic transaction.

    Args:
        user_id: Primary key of the user to suspend.
        reason: Optional suspension reason explanation.
        session: Optional SQLAlchemy database session.

    Returns:
        The updated User instance.

    Raises:
        UserNotFoundError: If user does not exist.
    """
    sess = session if session is not None else db.session
    user = sess.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {user_id} not found.")

    now = utc_now()
    user.status = "SUSPENDED"
    user.suspended_at = now
    user.suspension_reason = reason
    user.auth_version += 1
    user.updated_at = now

    revoke_all_user_sessions(user.id, session=sess)
    revoke_all_user_tokens(user.id, session=sess)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return user


def update_profile(
    user_id: int,
    display_name: str | None = None,
    avatar_file_asset_id: int | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Update basic profile information for a user.

    Args:
        user_id: Primary key of the user.
        display_name: Optional new display name.
        avatar_file_asset_id: Optional avatar FileAsset ID.
        session: Optional SQLAlchemy database session.

    Returns:
        The updated User instance.

    Raises:
        UserNotFoundError: If user does not exist.
        ValueError: If display_name is provided but empty.
    """
    sess = session if session is not None else db.session
    user = sess.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {user_id} not found.")

    if display_name is not None:
        cleaned_name = display_name.strip()
        if not cleaned_name:
            raise ValueError("Display name cannot be empty.")
        user.display_name = cleaned_name

    if avatar_file_asset_id is not None:
        user.avatar_file_asset_id = avatar_file_asset_id

    user.updated_at = utc_now()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return user


def mark_email_verified(
    user_id: int,
    verified_at: datetime.datetime | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Mark a user's email as verified.

    Args:
        user_id: Primary key of the user.
        verified_at: Verification timestamp (defaults to current UTC time).
        session: Optional SQLAlchemy database session.

    Returns:
        The updated User instance.

    Raises:
        UserNotFoundError: If user does not exist.
    """
    sess = session if session is not None else db.session
    user = sess.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {user_id} not found.")

    user.email_verified_at = verified_at or utc_now()
    user.updated_at = utc_now()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return user


# Allowed role sets per AUTH-002: STUDENT; STUDENT+INSTRUCTOR; STUDENT+INSTRUCTOR+ADMIN
VALID_ROLE_COMBINATIONS: tuple[frozenset[str], ...] = (
    frozenset({"STUDENT"}),
    frozenset({"STUDENT", "INSTRUCTOR"}),
    frozenset({"STUDENT", "INSTRUCTOR", "ADMIN"}),
)


def validate_role_combination(roles: set[str] | list[str] | frozenset[str]) -> bool:
    """Validate whether a set of roles matches one of the canonical cumulative combinations."""
    return frozenset(roles) in VALID_ROLE_COMBINATIONS


def assign_role_to_user(
    user_id: int,
    role_code: str,
    assigned_by_user_id: int | None = None,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Assign a role to a user, ensuring cumulative hierarchy per AUTH-002.

    Invariants enforced:
    - Allowed role sets are strictly STUDENT, STUDENT+INSTRUCTOR, STUDENT+INSTRUCTOR+ADMIN.
    - Assigning INSTRUCTOR automatically ensures STUDENT is assigned.
    - Assigning ADMIN automatically ensures INSTRUCTOR and STUDENT are assigned.
    - Role assignment is recorded in append-only AuditEvent.
    - Increments user.auth_version by 1 and revokes tokens/sessions if needed.

    Args:
        user_id: Primary key of user receiving role.
        role_code: Role code to assign ('STUDENT', 'INSTRUCTOR', 'ADMIN').
        assigned_by_user_id: Optional ID of the user (e.g. Admin) assigning the role.
        reason: Optional justification for the assignment.
        session: Optional SQLAlchemy session.

    Returns:
        The updated User instance.

    Raises:
        UserNotFoundError: If target user does not exist.
        InvalidRoleAssignmentError: If role_code is not one of the allowed canonical roles.
    """
    sess = session if session is not None else db.session
    user = sess.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {user_id} not found.")

    norm_code = role_code.strip().upper()
    if norm_code not in ("STUDENT", "INSTRUCTOR", "ADMIN"):
        raise InvalidRoleAssignmentError(f"Invalid role code: '{role_code}'.")

    # Determine required cumulative closure
    if norm_code == "STUDENT":
        target_roles = {"STUDENT"}
    elif norm_code == "INSTRUCTOR":
        target_roles = {"STUDENT", "INSTRUCTOR"}
    else:  # ADMIN
        target_roles = {"STUDENT", "INSTRUCTOR", "ADMIN"}

    # Include existing roles
    new_role_codes = user.role_codes | target_roles
    if not validate_role_combination(new_role_codes):
        raise InvalidRoleAssignmentError(
            f"Resulting role set {new_role_codes} is not an allowed cumulative combination."
        )

    before_roles = sorted(user.role_codes)
    now = utc_now()

    for code in sorted(new_role_codes):
        if code not in user.role_codes:
            role_obj = sess.query(Role).filter(Role.code == code).first()
            if role_obj is None:
                role_obj = Role(code=code, name=code.capitalize())
                sess.add(role_obj)
                sess.flush()
            user.roles.append(role_obj)

    sess.flush()
    if assigned_by_user_id is not None or reason is not None:
        for code in target_roles:
            role_obj = sess.query(Role).filter(Role.code == code).first()
            if role_obj is not None:
                link = (
                    sess.query(UserRole)
                    .filter(UserRole.user_id == user.id, UserRole.role_id == role_obj.id)
                    .first()
                )
                if link is not None:
                    link.assigned_by_user_id = assigned_by_user_id
                    link.assignment_reason = reason

    after_roles = sorted(new_role_codes)
    user.auth_version += 1
    user.updated_at = now

    # Audit event
    actor_roles = "SYSTEM"
    performed_as_admin = False
    if assigned_by_user_id is not None:
        assigner = sess.get(User, assigned_by_user_id)
        if assigner is not None:
            actor_roles = ",".join(sorted(assigner.role_codes))
            performed_as_admin = assigner.is_admin

    audit_entry = AuditEvent(
        actor_user_id=assigned_by_user_id,
        actor_roles_snapshot=actor_roles,
        action="USER_ROLE_ASSIGNED",
        target_type="USER",
        target_id=user.id,
        reason=reason,
        before_json=json.dumps({"roles": before_roles}),
        after_json=json.dumps({"roles": after_roles}),
        performed_as_admin=performed_as_admin,
        created_at=now,
    )
    sess.add(audit_entry)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return user


def remove_role_from_user(
    user_id: int,
    role_code: str,
    removed_by_user_id: int | None = None,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Remove a role from a user, maintaining cumulative closure per AUTH-002.

    Invariants enforced:
    - The baseline STUDENT role cannot be removed from active accounts.
    - Removing INSTRUCTOR also removes ADMIN to maintain valid closure.
    - Role revocation is recorded in append-only AuditEvent.
    - Increments user.auth_version by 1 and revokes tokens/sessions.

    Args:
        user_id: Primary key of target user.
        role_code: Role code to remove.
        removed_by_user_id: Optional ID of the administrator removing the role.
        reason: Optional justification.
        session: Optional SQLAlchemy session.

    Returns:
        The updated User instance.

    Raises:
        UserNotFoundError: If user does not exist.
        InvalidRoleAssignmentError: If attempting to remove STUDENT or invalid role code.
    """
    sess = session if session is not None else db.session
    user = sess.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {user_id} not found.")

    norm_code = role_code.strip().upper()
    if norm_code == "STUDENT":
        raise InvalidRoleAssignmentError("Cannot remove baseline STUDENT role from user.")
    if norm_code not in ("INSTRUCTOR", "ADMIN"):
        raise InvalidRoleAssignmentError(f"Invalid role code: '{role_code}'.")

    current_codes = set(user.role_codes)
    if norm_code not in current_codes:
        return user  # Role already absent, idempotent

    # Enforce cumulative downgrade
    roles_to_remove = {"INSTRUCTOR", "ADMIN"} if norm_code == "INSTRUCTOR" else {"ADMIN"}

    new_role_codes = current_codes - roles_to_remove
    if not validate_role_combination(new_role_codes):
        raise InvalidRoleAssignmentError(
            f"Resulting role set {new_role_codes} is not an allowed cumulative combination."
        )

    before_roles = sorted(current_codes)
    now = utc_now()

    # Remove UserRole records via relationship
    for code in roles_to_remove:
        matching = [r for r in user.roles if r.code == code]
        for r in matching:
            user.roles.remove(r)

    after_roles = sorted(new_role_codes)
    user.auth_version += 1
    user.updated_at = now

    actor_roles = "SYSTEM"
    performed_as_admin = False
    if removed_by_user_id is not None:
        remover = sess.get(User, removed_by_user_id)
        if remover is not None:
            actor_roles = ",".join(sorted(remover.role_codes))
            performed_as_admin = remover.is_admin

    audit_entry = AuditEvent(
        actor_user_id=removed_by_user_id,
        actor_roles_snapshot=actor_roles,
        action="USER_ROLE_REVOKED",
        target_type="USER",
        target_id=user.id,
        reason=reason,
        before_json=json.dumps({"roles": before_roles}),
        after_json=json.dumps({"roles": after_roles}),
        performed_as_admin=performed_as_admin,
        created_at=now,
    )
    sess.add(audit_entry)

    try:
        sess.commit()
        sess.expire_all()
        sess.refresh(user)
    except Exception:
        sess.rollback()
        raise

    return user


def _get_token_serializer(salt: str) -> URLSafeTimedSerializer:
    """Resolve timed serializer using application secret key."""
    try:
        secret = current_app.config.get("SECRET_KEY", "pwd301-fallback-secret-key")
    except RuntimeError:
        secret = "pwd301-fallback-secret-key"
    return URLSafeTimedSerializer(secret, salt=salt)


def generate_email_verification_token(user_id: int) -> str:
    """Generate a single-use database-backed email verification token valid for 24 hours."""
    from pwd301.services.auth_token_service import SecurityTokenPurpose, create_security_token

    _, raw_token = create_security_token(user_id, SecurityTokenPurpose.EMAIL_VERIFY)
    return raw_token


def verify_email_verification_token(token: str, max_age: int = 86400) -> int | None:
    """Verify an email verification token and extract user_id if valid."""
    from pwd301.services.auth_token_service import SecurityTokenPurpose, verify_security_token
    from pwd301.services.exceptions import InvalidTokenError, ServiceError

    try:
        token_record = verify_security_token(token, SecurityTokenPurpose.EMAIL_VERIFY)
        return int(token_record.user_id)
    except (InvalidTokenError, ServiceError):
        pass

    if "." in token:
        serializer = _get_token_serializer(salt="email-verification")
        try:
            user_id = serializer.loads(token, max_age=max_age)
            return int(user_id) if user_id is not None else None
        except (BadSignature, SignatureExpired, Exception):
            return None
    return None


def generate_password_reset_token(user_id: int) -> str:
    """Generate a single-use database-backed password reset token valid for 1 hour."""
    from pwd301.services.auth_token_service import SecurityTokenPurpose, create_security_token

    _, raw_token = create_security_token(user_id, SecurityTokenPurpose.PASSWORD_RESET)
    return raw_token


def verify_password_reset_token(token: str, max_age: int = 3600) -> int | None:
    """Verify a password reset token and extract user_id if valid."""
    from pwd301.services.auth_token_service import SecurityTokenPurpose, verify_security_token
    from pwd301.services.exceptions import InvalidTokenError, ServiceError

    try:
        token_record = verify_security_token(token, SecurityTokenPurpose.PASSWORD_RESET)
        return int(token_record.user_id)
    except (InvalidTokenError, ServiceError):
        pass

    if "." in token:
        serializer = _get_token_serializer(salt="password-reset")
        try:
            user_id = serializer.loads(token, max_age=max_age)
            return int(user_id) if user_id is not None else None
        except (BadSignature, SignatureExpired, Exception):
            return None
    return None
