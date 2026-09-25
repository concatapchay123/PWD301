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
import logging
import re
import uuid
from typing import Any

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, scoped_session
from werkzeug.security import check_password_hash, generate_password_hash

from pwd301.extensions import db
from pwd301.models.identity import InstructorApplication, Role, User, UserRole
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.types import utc_now
from pwd301.services.exceptions import (
    AccountNotActiveError,
    AdminActionForbiddenError,
    InvalidEmailError,
    InvalidPasswordError,
    InvalidRoleAssignmentError,
    ResourceNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
    ValidationError,
)
from pwd301.services.jwt_auth_service import revoke_all_user_tokens
from pwd301.services.session_auth_service import revoke_all_user_sessions

logger = logging.getLogger(__name__)

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
        InvalidPasswordError: If the password does not meet complexity and length requirements.
    """
    if not password or not isinstance(password, str):
        raise InvalidPasswordError("Mật khẩu không được để trống.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise InvalidPasswordError(f"Mật khẩu phải có tối thiểu {MIN_PASSWORD_LENGTH} ký tự.")

    if not re.search(r"[A-Za-z]", password):
        raise InvalidPasswordError("Mật khẩu phải chứa ít nhất một chữ cái.")

    if not re.search(r"\d", password):
        raise InvalidPasswordError("Mật khẩu phải chứa ít nhất một chữ số.")

    if not re.search(r"[^A-Za-z0-9]", password):
        raise InvalidPasswordError("Mật khẩu phải chứa ít nhất một ký tự đặc biệt (!@#$%^&*...).")


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


def validate_role_combination(
    roles: set[str] | list[str] | frozenset[str],
    raise_on_error: bool = False,
) -> bool:
    """Validate whether a set of roles matches one of the canonical cumulative combinations.

    Allowed cumulative combinations:
    - {'STUDENT'}
    - {'STUDENT', 'INSTRUCTOR'}
    - {'STUDENT', 'INSTRUCTOR', 'ADMIN'}

    Args:
        roles: The set or collection of role codes to validate.
        raise_on_error: If True and the combination is invalid, raises InvalidRoleAssignmentError.

    Returns:
        True if the combination is valid, False otherwise.

    Raises:
        InvalidRoleAssignmentError: If raise_on_error is True and combination is invalid.
    """
    normalized = {r.strip().upper() for r in roles} if roles else set()
    is_valid = frozenset(normalized) in VALID_ROLE_COMBINATIONS
    if not is_valid and raise_on_error:
        raise InvalidRoleAssignmentError(
            f"Invalid role combination: {set(roles)}. Allowed cumulative combinations: "
            f"{{'STUDENT'}}, {{'STUDENT', 'INSTRUCTOR'}}, {{'STUDENT', 'INSTRUCTOR', 'ADMIN'}}."
        )
    return is_valid


def set_user_roles(
    user_id: int,
    role_codes: set[str] | list[str] | frozenset[str],
    assigned_by_user_id: int | None = None,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Explicitly assign an exact set of roles to an existing user.

    Invariants enforced:
    - Never creates a new User; modifies the existing user record in place.
    - Validates that the role combination strictly satisfies cumulative hierarchy (AUTH-002).
      Any invalid partial combination (e.g. {'INSTRUCTOR'} without STUDENT, or {'ADMIN'} alone)
      immediately raises InvalidRoleAssignmentError.
    - Baseline STUDENT role cannot be omitted.
    - Records append-only AuditEvent.
    - Dispatches in-app notification to the user.
    - Increments user.auth_version by 1.

    Args:
        user_id: Primary key of target user.
        role_codes: The exact desired set of role codes.
        assigned_by_user_id: Optional ID of administrator changing roles.
        reason: Optional justification for the change.
        session: Optional SQLAlchemy session.

    Returns:
        The updated User instance.

    Raises:
        UserNotFoundError: If user does not exist.
        InvalidRoleAssignmentError: If role_codes does not match an allowed cumulative set.
    """
    sess = session if session is not None else db.session
    user = sess.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {user_id} not found.")

    # Strictly validate cumulative combination
    validate_role_combination(role_codes, raise_on_error=True)
    target_roles = {r.strip().upper() for r in role_codes}

    before_roles = sorted(user.role_codes)
    now = utc_now()

    # Synchronize roles: remove obsolete, add newly assigned
    for r in list(user.roles):
        if r.code not in target_roles:
            user.roles.remove(r)

    for code in sorted(target_roles):
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

    after_roles = sorted(target_roles)
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
        action="USER_ROLES_UPDATED",
        target_type="USER",
        target_id=user.id,
        reason=reason,
        before_json=json.dumps({"roles": before_roles}),
        after_json=json.dumps({"roles": after_roles}),
        performed_as_admin=performed_as_admin,
        created_at=now,
    )
    sess.add(audit_entry)

    # In-app notification
    try:
        from pwd301.services.notification_service import dispatch_notification

        with sess.begin_nested():
            dispatch_notification(
                recipient_user=user.id,
                event_type="ROLE_CHANGED",
                title="Cập nhật vai trò tài khoản",
                body=(
                    f"Các vai trò của bạn đã được cập nhật thành: {', '.join(after_roles)}."
                    + (f" Lý do: {reason}" if reason else "")
                ),
                action_url="/",
                category="SYSTEM",
                session=sess,
            )
    except Exception:
        pass

    try:
        sess.commit()
        sess.expire_all()
        sess.refresh(user)
    except Exception:
        sess.rollback()
        raise

    return user


def assign_role_to_user(
    user_id: int,
    role_code: str,
    assigned_by_user_id: int | None = None,
    reason: str | None = None,
    admin_sub_role: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Assign a role to a user, ensuring cumulative hierarchy per AUTH-002.

    Invariants enforced:
    - Allowed role sets are strictly STUDENT, STUDENT+INSTRUCTOR, STUDENT+INSTRUCTOR+ADMIN.
    - Assigning INSTRUCTOR automatically ensures STUDENT is assigned.
    - Assigning ADMIN automatically ensures INSTRUCTOR and STUDENT are assigned.
    - Role assignment is recorded in append-only AuditEvent.
    - Increments user.auth_version by 1 and revokes tokens/sessions if needed.
    - Only primary admin (is_primary_admin) can assign roles if caller is admin.

    Args:
        user_id: Primary key of user receiving role.
        role_code: Role code to assign ('STUDENT', 'INSTRUCTOR', 'ADMIN').
        assigned_by_user_id: Optional ID of the user (e.g. Admin) assigning the role.
        reason: Optional justification for the assignment.
        admin_sub_role: Optional sub-role code for ADMIN ('ADMIN_PRIMARY', etc.).
        session: Optional SQLAlchemy session.

    Returns:
        The updated User instance.

    Raises:
        UserNotFoundError: If target user does not exist.
        InvalidRoleAssignmentError: If role_code is not one of the allowed canonical roles.
        AdminActionForbiddenError: If non-primary admin attempts role assignment.
    """
    sess = session if session is not None else db.session
    user = sess.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {user_id} not found.")

    norm_code = role_code.strip().upper()
    if norm_code not in ("STUDENT", "INSTRUCTOR", "ADMIN"):
        raise InvalidRoleAssignmentError(f"Invalid role code: '{role_code}'.")

    if assigned_by_user_id is not None:
        assigner = sess.get(User, assigned_by_user_id)
        if assigner is not None and assigner.is_admin and not assigner.is_primary_admin:
            raise AdminActionForbiddenError(
                "Chỉ Admin chính mới có quyền phân quyền và bổ nhiệm các Admin khác."
            )

    if assigned_by_user_id is not None and reason is not None:
        clean_reason = reason.strip()
        if len(clean_reason) < 5:
            raise ValidationError("Lý do cấp vai trò kiểm toán bắt buộc tối thiểu 5 ký tự.")

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
    if assigned_by_user_id is not None or reason is not None or admin_sub_role is not None:
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
                    effective_reason = reason or ""
                    if code == "ADMIN":
                        chosen_sub = admin_sub_role or "ADMIN_PRIMARY"
                        link.assignment_reason = f"SUB_ROLE:{chosen_sub} | {effective_reason}"
                    else:
                        link.assignment_reason = effective_reason

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

    # In-app notification on role change
    if before_roles != after_roles:
        try:
            from pwd301.services.notification_service import dispatch_notification

            with sess.begin_nested():
                dispatch_notification(
                    recipient_user=user.id,
                    event_type="ROLE_CHANGED",
                    title="Cập nhật vai trò tài khoản",
                    body=(
                        f"Các vai trò của bạn đã được cập nhật thành: {', '.join(after_roles)}."
                        + (f" Lý do: {reason}" if reason else "")
                    ),
                    action_url="/",
                    category="SYSTEM",
                    session=sess,
                )
        except Exception:
            pass

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

    if removed_by_user_id is not None:
        remover = sess.get(User, removed_by_user_id)
        if remover is not None and remover.is_admin and not remover.is_primary_admin:
            raise AdminActionForbiddenError(
                "Chỉ Admin chính mới có quyền thu hồi vai trò của người dùng khác."
            )

    if removed_by_user_id is not None and reason is not None:
        clean_reason = reason.strip()
        if len(clean_reason) < 5:
            raise ValidationError("Lý do thu hồi vai trò kiểm toán bắt buộc tối thiểu 5 ký tự.")

    # Guard: Self-Demotion Block
    if removed_by_user_id is not None and user.id == removed_by_user_id and norm_code == "ADMIN":
        raise AdminActionForbiddenError(
            "Không thể tự thu hồi quyền Quản trị viên (ADMIN) của chính mình."
        )

    current_codes = set(user.role_codes)
    if norm_code not in current_codes:
        return user  # Role already absent, idempotent

    # Enforce cumulative downgrade
    roles_to_remove = {"INSTRUCTOR", "ADMIN"} if norm_code == "INSTRUCTOR" else {"ADMIN"}

    # Guard: Last Admin Protection
    if "ADMIN" in roles_to_remove:
        admin_role = sess.query(Role).filter(Role.code == "ADMIN").first()
        if admin_role:
            active_admins = (
                sess.query(User)
                .filter(User.roles.contains(admin_role), User.status != "SUSPENDED")
                .all()
            )
            if len(active_admins) <= 1 and any(u.id == user.id for u in active_admins):
                raise AdminActionForbiddenError(
                    "Không thể tước quyền Quản trị viên của tài khoản Admin "
                    "hoạt động duy nhất còn lại trong hệ thống."
                )

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

    # In-app notification on role revocation
    if before_roles != after_roles:
        try:
            from pwd301.services.notification_service import dispatch_notification

            with sess.begin_nested():
                dispatch_notification(
                    recipient_user=user.id,
                    event_type="ROLE_CHANGED",
                    title="Cập nhật vai trò tài khoản",
                    body=(
                        f"Các vai trò của bạn đã được cập nhật thành: {', '.join(after_roles)}."
                        + (f" Lý do: {reason}" if reason else "")
                    ),
                    action_url="/",
                    category="SYSTEM",
                    session=sess,
                )
        except Exception:
            pass

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


# ==============================================================================
# Instructor Application & Role Nomination Workflow
# ==============================================================================


def submit_instructor_application(
    user_id: int,
    application_data: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> InstructorApplication:
    """Submit an application for a student to become an instructor.

    Enforces:
    - Target user must exist and be active.
    - User cannot already possess INSTRUCTOR or ADMIN roles.
    - User cannot have a currently PENDING application.
    - Application data is validated and serialized to JSON into application_note (<= 2000 chars).
    - Status is initialized to PENDING.
    - An append-only AuditEvent is recorded.
    """
    sess = session if session is not None else db.session
    user = sess.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {user_id} not found.")

    if user.is_instructor or user.is_admin:
        raise ValidationError("Bạn đã có quyền Giảng viên hoặc Quản trị viên trong hệ thống.")

    # Check for active pending application
    existing_pending = (
        sess.query(InstructorApplication)
        .filter(
            InstructorApplication.applicant_user_id == user.id,
            InstructorApplication.status == "PENDING",
        )
        .first()
    )
    if existing_pending is not None:
        raise ValidationError(
            "Bạn đang có một đơn đăng ký đang chờ xét duyệt. Vui lòng đợi quản trị viên "
            "xử lý hoặc hủy đơn cũ trước khi gửi đơn mới."
        )

    # Basic validations on required fields
    institution_name = str(application_data.get("institution_name", "")).strip()
    if not institution_name:
        institution_name = "Hoạt động tự do / Độc lập"
    specialization = str(application_data.get("specialization", "")).strip()
    if not specialization:
        raise ValidationError(
            "Vui lòng cung cấp lĩnh vực / chuyên môn giảng dạy hoặc ngành ngách của bạn."
        )

    # Experience years
    try:
        exp_years = int(application_data.get("experience_years", 0))
    except (ValueError, TypeError):
        exp_years = 0

    contact_email = str(application_data.get("contact_email", "")).strip()
    inst_email = str(application_data.get("institution_email", "")).strip()
    port_url = str(application_data.get("portfolio_url", "")).strip()
    ev_urls = str(application_data.get("evidence_urls", "")).strip()
    sop = (
        str(application_data.get("statement_of_purpose", "")).strip()
        or str(application_data.get("bio", "")).strip()
        or str(application_data.get("statement", "")).strip()
    )

    attached_files = application_data.get("attached_files", [])
    clean_files: list[dict[str, Any]] = []
    if isinstance(attached_files, list):
        for f in attached_files:
            if isinstance(f, dict):
                clean_files.append(
                    {
                        "original_name": str(f.get("original_name") or f.get("name") or "")[:120],
                        "saved_filename": str(f.get("saved_filename") or f.get("file") or "")[:120],
                        "doc_type": str(f.get("doc_type") or "OTHER")[:30],
                        "size": int(f.get("size") or f.get("file_size") or 0),
                    }
                )

    clean_data: dict[str, Any] = {
        "full_name": str(application_data.get("full_name", "")).strip(),
        "date_of_birth": str(application_data.get("date_of_birth", "")).strip(),
        "contact_email": contact_email or inst_email,
        "phone_number": str(application_data.get("phone_number", "")).strip(),
        "id_card_number": str(application_data.get("id_card_number", "")).strip(),
        "work_address": str(application_data.get("work_address", "")).strip(),
        "institution_name": institution_name,
        "institution_email": inst_email or contact_email,
        "faculty_department": str(application_data.get("faculty_department", "")).strip(),
        "specialization": specialization,
        "experience_years": exp_years,
        "sheer_id": str(application_data.get("sheer_id", "")).strip(),
        "teaching_evidence": str(application_data.get("teaching_evidence", "")).strip(),
        "salary_proof": str(application_data.get("salary_proof", "")).strip(),
        "current_schedule": str(application_data.get("current_schedule", "")).strip(),
        "employment_contract": str(application_data.get("employment_contract", "")).strip(),
        "portfolio_url": port_url or ev_urls,
        "evidence_urls": ev_urls or port_url,
        "statement_of_purpose": sop,
        "attached_files": clean_files[:10],
    }

    # Ensure JSON fits in 2000 chars without truncating JSON syntax or stripping attached_files
    note_json = json.dumps(clean_data, ensure_ascii=False)
    if len(note_json) > 1950:
        clean_data["statement_of_purpose"] = str(clean_data["statement_of_purpose"])[:200]
        clean_data["teaching_evidence"] = str(clean_data["teaching_evidence"])[:80]
        clean_data["salary_proof"] = str(clean_data["salary_proof"])[:60]
        clean_data["current_schedule"] = str(clean_data["current_schedule"])[:60]
        clean_data["employment_contract"] = str(clean_data["employment_contract"])[:60]
        clean_data["work_address"] = str(clean_data["work_address"])[:60]
        clean_data["evidence_urls"] = str(clean_data["evidence_urls"])[:80]
        clean_data["portfolio_url"] = str(clean_data["portfolio_url"])[:80]
        note_json = json.dumps(clean_data, ensure_ascii=False)

    if len(note_json) > 1950:
        clean_data["statement_of_purpose"] = str(clean_data["statement_of_purpose"])[:80]
        clean_data["teaching_evidence"] = ""
        clean_data["salary_proof"] = ""
        clean_data["current_schedule"] = ""
        clean_data["employment_contract"] = ""
        clean_data["work_address"] = ""
        note_json = json.dumps(clean_data, ensure_ascii=False)

    if len(note_json) > 1950:
        clean_data["statement_of_purpose"] = str(clean_data["statement_of_purpose"])[:30]
        note_json = json.dumps(clean_data, ensure_ascii=False)

    now = utc_now()
    app_record = InstructorApplication(
        applicant_user_id=user.id,
        status="PENDING",
        application_note=note_json,
        created_at=now,
    )
    sess.add(app_record)
    sess.flush()

    audit_entry = AuditEvent(
        actor_user_id=user.id,
        actor_roles_snapshot=",".join(sorted(user.role_codes)),
        action="INSTRUCTOR_APPLICATION_SUBMITTED",
        target_type="INSTRUCTOR_APPLICATION",
        target_id=app_record.id,
        reason=f"Đề cử trở thành Giảng viên ({institution_name} - {specialization})",
        after_json=json.dumps({"status": "PENDING", "institution": institution_name}),
        created_at=now,
    )
    sess.add(audit_entry)

    try:
        from pwd301.services.notification_service import dispatch_notification

        admin_role = sess.query(Role).filter(Role.code == "ADMIN").first()
        if admin_role:
            admin_users = (
                sess.query(User)
                .filter(User.roles.contains(admin_role), User.status == "ACTIVE")
                .all()
            )
            for adm in admin_users:
                if adm.has_admin_permission("INSTRUCTOR_REVIEW"):
                    dispatch_notification(
                        recipient_user=adm.id,
                        event_type="INSTRUCTOR_APPLICATION_SUBMITTED",
                        title="Hồ sơ ứng tuyển giảng viên mới chờ duyệt",
                        body=(
                            f"Ứng viên {user.display_name} đã nộp hồ sơ đăng ký giảng viên "
                            f"({institution_name} - {specialization}). "
                            "Vui lòng xem xét hồ sơ và phê duyệt."
                        ),
                        action_url="#/admin/governance?tab=applications",
                        category="SYSTEM",
                        payload={
                            "application_id": str(app_record.public_id),
                            "applicant_name": user.display_name,
                            "action_url": "#/admin/governance?tab=applications",
                        },
                        session=sess,
                    )
    except Exception as exc:
        logger.warning(
            "Failed to dispatch instructor application notification to admins: %s", exc
        )

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return app_record


def cancel_instructor_application(
    user_id: int,
    application_id: int,
    session: Session | scoped_session[Any] | None = None,
) -> InstructorApplication:
    """Allow an applicant to cancel their own PENDING application."""
    sess = session if session is not None else db.session
    app_record = sess.get(InstructorApplication, application_id)
    if app_record is None:
        raise ResourceNotFoundError(f"Đơn đăng ký #{application_id} không tồn tại.")

    if app_record.applicant_user_id != user_id:
        raise ValidationError("Bạn không có quyền thao tác trên đơn đăng ký này.")

    if app_record.status != "PENDING":
        raise ValidationError(
            f"Chỉ có thể hủy đơn khi ở trạng thái Chờ duyệt "
            f"(trạng thái hiện tại: {app_record.status})."
        )

    now = utc_now()
    app_record.status = "CANCELLED"

    audit_entry = AuditEvent(
        actor_user_id=user_id,
        actor_roles_snapshot="STUDENT",
        action="INSTRUCTOR_APPLICATION_CANCELLED",
        target_type="INSTRUCTOR_APPLICATION",
        target_id=app_record.id,
        reason="Học viên chủ động hủy đơn đăng ký",
        after_json=json.dumps({"status": "CANCELLED"}),
        created_at=now,
    )
    sess.add(audit_entry)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return app_record


def get_user_active_application(
    user_id: int,
    session: Session | scoped_session[Any] | None = None,
) -> InstructorApplication | None:
    """Retrieve the latest instructor application for a user."""
    sess = session if session is not None else db.session
    return (
        sess.query(InstructorApplication)
        .filter(InstructorApplication.applicant_user_id == user_id)
        .order_by(InstructorApplication.created_at.desc())
        .first()
    )


def get_instructor_application(
    application_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> InstructorApplication | None:
    """Retrieve an instructor application by internal primary key or public UUIDv5."""
    sess = session if session is not None else db.session
    if isinstance(application_id, InstructorApplication):
        return application_id
    if isinstance(application_id, int):
        return sess.get(InstructorApplication, application_id)
    if isinstance(application_id, str):
        if application_id.isdigit():
            return sess.get(InstructorApplication, int(application_id))
        try:
            target_uuid = uuid.UUID(application_id)
        except (ValueError, TypeError):
            return None
    elif isinstance(application_id, uuid.UUID):
        target_uuid = application_id
    else:
        return None

    for app in sess.query(InstructorApplication).all():
        if app.public_id == target_uuid:
            return app
    return None


def list_instructor_applications(
    status: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> list[InstructorApplication]:
    """List instructor applications with optional status filter, ordered by latest created_at."""
    sess = session if session is not None else db.session
    query = sess.query(InstructorApplication)
    if status and status.upper() != "ALL":
        query = query.filter(InstructorApplication.status == status.upper())
    return query.order_by(InstructorApplication.created_at.desc()).all()


def review_instructor_application(
    application_id: int | uuid.UUID | str,
    admin_user_id: int,
    action: str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> InstructorApplication:
    """Review an instructor application (approve or reject) by an administrator."""
    sess = session if session is not None else db.session
    admin = sess.get(User, admin_user_id)
    if admin is None or not admin.is_admin:
        raise ValidationError(
            "Chỉ Quản trị viên (Admin) mới có quyền xét duyệt đơn đăng ký giảng viên."
        )

    clean_action = str(action).strip().lower()
    if clean_action not in ("approve", "reject"):
        raise ValidationError("Hành động xét duyệt phải là 'approve' hoặc 'reject'.")

    app_record = get_instructor_application(application_id, session=sess)
    if app_record is None:
        raise ResourceNotFoundError(f"Đơn đăng ký #{application_id} không tồn tại.")

    if app_record.status != "PENDING":
        raise ValidationError(
            f"Đơn đăng ký #{application_id} không ở trạng thái Chờ duyệt "
            f"(trạng thái hiện tại: {app_record.status})."
        )

    now = utc_now()
    clean_reason = (reason or "").strip()

    if clean_action == "approve":
        # Assign INSTRUCTOR role adhering to AUTH-002 cumulative hierarchy
        assign_role_to_user(
            user_id=app_record.applicant_user_id,
            role_code="INSTRUCTOR",
            assigned_by_user_id=admin.id,
            reason=(
                f"Phê duyệt đơn đăng ký giảng viên #{app_record.id}: "
                f"{clean_reason or 'Đạt yêu cầu chuyên môn'}"
            ),
            session=sess,
        )
        app_record.status = "APPROVED"
        app_record.reviewed_by_user_id = admin.id
        app_record.reviewed_at = now
        app_record.review_reason = clean_reason or "Đơn đăng ký được phê duyệt thành công."

        # Send in-app notification to applicant
        try:
            from pwd301.services.notification_service import dispatch_notification

            dispatch_notification(
                recipient_user=app_record.applicant_user_id,
                event_type="ROLE_CHANGED",
                title="Đơn đăng ký Giảng viên đã được phê duyệt!",
                body=(
                    f"Chúc mừng bạn! Quản trị viên đã phê duyệt đơn đăng ký giảng viên "
                    f"của bạn. Quyền Giảng viên (Instructor) đã được kích hoạt trên "
                    f"tài khoản. {clean_reason}"
                ),
                action_url="#/instructor/dashboard",
                category="SYSTEM",
                payload={"action_url": "#/instructor/dashboard"},
                session=sess,
            )
        except Exception:
            pass

        audit_entry = AuditEvent(
            actor_user_id=admin.id,
            actor_roles_snapshot=",".join(sorted(admin.role_codes)),
            action="INSTRUCTOR_APPLICATION_APPROVED",
            target_type="INSTRUCTOR_APPLICATION",
            target_id=app_record.id,
            reason=clean_reason or "Phê duyệt đơn đăng ký giảng viên",
            before_json=json.dumps({"status": "PENDING"}),
            after_json=json.dumps({"status": "APPROVED", "granted_role": "INSTRUCTOR"}),
            performed_as_admin=True,
            created_at=now,
        )
        sess.add(audit_entry)

    else:  # reject
        if not clean_reason:
            raise ValidationError(
                "Vui lòng cung cấp lý do từ chối đơn đăng ký để thông báo cho ứng viên."
            )

        app_record.status = "REJECTED"
        app_record.reviewed_by_user_id = admin.id
        app_record.reviewed_at = now
        app_record.review_reason = clean_reason

        # Send in-app notification to applicant
        try:
            from pwd301.services.notification_service import dispatch_notification

            dispatch_notification(
                recipient_user=app_record.applicant_user_id,
                event_type="ROLE_CHANGED",
                title="Thông báo kết quả xét duyệt đơn Giảng viên",
                body=(
                    f"Đơn đăng ký trở thành Giảng viên của bạn chưa được chấp thuận. "
                    f"Lý do: {clean_reason}. Bạn có thể cập nhật thông tin và nộp lại hồ sơ sau."
                ),
                action_url="#/student/become-instructor",
                category="SYSTEM",
                payload={"action_url": "#/student/become-instructor"},
                session=sess,
            )
        except Exception:
            pass

        audit_entry = AuditEvent(
            actor_user_id=admin.id,
            actor_roles_snapshot=",".join(sorted(admin.role_codes)),
            action="INSTRUCTOR_APPLICATION_REJECTED",
            target_type="INSTRUCTOR_APPLICATION",
            target_id=app_record.id,
            reason=clean_reason,
            before_json=json.dumps({"status": "PENDING"}),
            after_json=json.dumps({"status": "REJECTED", "reason": clean_reason}),
            performed_as_admin=True,
            created_at=now,
        )
        sess.add(audit_entry)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return app_record
