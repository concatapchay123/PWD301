"""Security token lifecycle management service for PWD301.

Provides business logic for single-use security tokens:
- Generation of cryptographically secure random tokens (URL-safe).
- Storing binary SHA-256 token digests (never raw tokens).
- Expiration and single-use consumption verification.
- Purpose-specific workflows: email verification, password reset, and email change.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import secrets
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, scoped_session
from werkzeug.security import generate_password_hash

from pwd301.extensions import db
from pwd301.models.identity import User, UserSecurityToken
from pwd301.models.types import utc_now
from pwd301.services.exceptions import (
    AccountNotActiveError,
    InvalidTokenError,
    TokenAlreadyConsumedError,
    TokenExpiredError,
    TokenPurposeMismatchError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from pwd301.services.user_service import normalize_email, validate_password


class SecurityTokenPurpose:
    """Canonical security token purposes adhering to CHECK constraint ck_user_security_tokens_1."""

    EMAIL_VERIFY = "EMAIL_VERIFY"
    EMAIL_CHANGE = "EMAIL_CHANGE"
    PASSWORD_RESET = "PASSWORD_RESET"


DEFAULT_EXPIRATION_SECONDS: dict[str, int] = {
    SecurityTokenPurpose.EMAIL_VERIFY: 24 * 3600,  # 24 hours
    SecurityTokenPurpose.EMAIL_CHANGE: 24 * 3600,  # 24 hours
    SecurityTokenPurpose.PASSWORD_RESET: 1 * 3600,  # 1 hour
}

# Constant-time dummy digest for side-channel timing attack mitigation
DUMMY_TOKEN_HASH = hashlib.sha256(b"pwd301-timing-defense-security-token").digest()


def _ensure_utc(dt: datetime.datetime) -> datetime.datetime:
    """Ensure datetime is UTC timezone-aware for dialect-safe comparisons."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.UTC)
    return dt


def hash_token(raw_token: str) -> bytes:
    """Compute the 32-byte SHA-256 digest of a raw token string."""
    return hashlib.sha256(raw_token.encode("utf-8")).digest()


def generate_raw_token() -> str:
    """Generate a cryptographically secure URL-safe random token string."""
    return secrets.token_urlsafe(32)


def create_security_token(
    user_id: int,
    purpose: str,
    pending_email: str | None = None,
    expires_in_seconds: int | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[UserSecurityToken, str]:
    """Generate and store a single-use security token for a user.

    Invariants enforced:
    - Raw token is never stored in the database; only its SHA-256 binary digest is saved.
    - Token purpose is validated against canonical allowed purposes.
    - User must exist and have an active status.
    - Pre-existing unconsumed tokens of the same purpose for this user are invalidated.
    - Expiration duration defaults to 24h for email verification/change and 1h for password reset.

    Args:
        user_id: Primary key of the target user.
        purpose: Security token purpose ('EMAIL_VERIFY', 'EMAIL_CHANGE', 'PASSWORD_RESET').
        pending_email: Optional pending email address (used for 'EMAIL_CHANGE').
        expires_in_seconds: Optional custom lifetime in seconds.
        session: Optional SQLAlchemy database session.

    Returns:
        tuple[UserSecurityToken, str]: Persisted token record and the raw token string.

    Raises:
        ValueError: If purpose is invalid or expiration duration is non-positive.
        UserNotFoundError: If user does not exist.
        AccountNotActiveError: If user account is not active.
    """
    if purpose not in DEFAULT_EXPIRATION_SECONDS:
        raise ValueError(f"Unsupported security token purpose: '{purpose}'.")

    duration = (
        expires_in_seconds
        if expires_in_seconds is not None
        else DEFAULT_EXPIRATION_SECONDS[purpose]
    )
    if duration <= 0:
        raise ValueError("Token expiration duration must be greater than zero.")

    sess = session if session is not None else db.session
    user = sess.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {user_id} not found.")

    if not user.is_active:
        raise AccountNotActiveError(f"Account for user {user_id} is not active.")

    norm_pending_email = normalize_email(pending_email) if pending_email is not None else None

    now = utc_now()

    # Invalidate older pending unconsumed tokens of the same purpose for this user
    older_tokens = (
        sess.query(UserSecurityToken)
        .filter(
            UserSecurityToken.user_id == user_id,
            UserSecurityToken.purpose == purpose,
            UserSecurityToken.consumed_at.is_(None),
        )
        .all()
    )
    for old_tok in older_tokens:
        old_tok.consumed_at = now

    raw_token = generate_raw_token()
    token_digest = hash_token(raw_token)
    expires_at = now + datetime.timedelta(seconds=duration)

    token_record = UserSecurityToken(
        user_id=user_id,
        purpose=purpose,
        token_hash=token_digest,
        pending_email=norm_pending_email,
        created_at=now,
        expires_at=expires_at,
        consumed_at=None,
    )

    sess.add(token_record)
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return token_record, raw_token


def verify_security_token(
    raw_token: str,
    purpose: str,
    session: Session | scoped_session[Any] | None = None,
) -> UserSecurityToken:
    """Verify a security token without marking it consumed.

    Args:
        raw_token: The raw token string supplied by the client.
        purpose: Expected purpose ('EMAIL_VERIFY', 'EMAIL_CHANGE', 'PASSWORD_RESET').
        session: Optional SQLAlchemy database session.

    Returns:
        The matching, valid UserSecurityToken instance.

    Raises:
        InvalidTokenError: If token does not exist or is malformed.
        TokenPurposeMismatchError: If the token was issued for a different purpose.
        TokenAlreadyConsumedError: If the token has already been used.
        TokenExpiredError: If the token expiration time has elapsed.
    """
    if not raw_token or not isinstance(raw_token, str):
        raise InvalidTokenError("Security token cannot be empty.")

    sess = session if session is not None else db.session
    token_digest = hash_token(raw_token)

    token_record = (
        sess.query(UserSecurityToken).filter(UserSecurityToken.token_hash == token_digest).first()
    )
    expected_hash = token_record.token_hash if token_record is not None else DUMMY_TOKEN_HASH
    digest_matches = hmac.compare_digest(expected_hash, token_digest)
    if token_record is None or not digest_matches:
        raise InvalidTokenError("Security token is invalid or does not exist.")

    if token_record.purpose != purpose:
        raise TokenPurposeMismatchError(
            f"Token purpose mismatch: expected '{purpose}', "
            f"but token is for '{token_record.purpose}'."
        )

    if token_record.consumed_at is not None:
        raise TokenAlreadyConsumedError("Security token has already been consumed.")

    if _ensure_utc(token_record.expires_at) < utc_now():
        raise TokenExpiredError("Security token has expired.")

    return token_record


def consume_security_token(
    raw_token: str,
    purpose: str,
    session: Session | scoped_session[Any] | None = None,
) -> UserSecurityToken:
    """Verify and atomically consume a single-use security token.

    Args:
        raw_token: The raw token string.
        purpose: Expected purpose.
        session: Optional SQLAlchemy database session.

    Returns:
        The consumed UserSecurityToken instance.
    """
    sess = session if session is not None else db.session
    token_record = verify_security_token(raw_token, purpose, session=sess)

    token_record.consumed_at = utc_now()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return token_record


def verify_email_with_token(
    raw_token: str,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Verify a user's email address using an EMAIL_VERIFY token.

    Consumes the token, marks user's email_verified_at, and commits.

    Args:
        raw_token: The raw verification token.
        session: Optional SQLAlchemy database session.

    Returns:
        The updated User instance.

    Raises:
        InvalidTokenError: If token is invalid.
        UserNotFoundError: If associated user record is missing.
    """
    sess = session if session is not None else db.session
    token_record = consume_security_token(
        raw_token,
        SecurityTokenPurpose.EMAIL_VERIFY,
        session=sess,
    )

    user = sess.get(User, token_record.user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {token_record.user_id} not found.")

    user.email_verified_at = utc_now()
    user.updated_at = utc_now()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return user


def reset_password_with_token(
    raw_token: str,
    new_password: str,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Reset a user's password using a PASSWORD_RESET token.

    Consumes the token, validates the new password, updates password hash,
    and increments auth_version by 1 to invalidate existing sessions.

    Args:
        raw_token: The raw password reset token.
        new_password: The desired new password.
        session: Optional SQLAlchemy database session.

    Returns:
        The updated User instance.

    Raises:
        InvalidTokenError: If token is invalid.
        InvalidPasswordError: If new password does not meet criteria.
        UserNotFoundError: If associated user record is missing.
    """
    validate_password(new_password)

    sess = session if session is not None else db.session
    token_record = consume_security_token(
        raw_token,
        SecurityTokenPurpose.PASSWORD_RESET,
        session=sess,
    )

    user = sess.get(User, token_record.user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {token_record.user_id} not found.")

    user.password_hash = generate_password_hash(new_password)
    user.auth_version += 1
    user.updated_at = utc_now()

    from pwd301.services.jwt_auth_service import revoke_all_user_tokens
    from pwd301.services.session_auth_service import revoke_all_user_sessions

    revoke_all_user_sessions(user.id, session=sess)
    revoke_all_user_tokens(user.id, session=sess)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return user


def apply_email_change_with_token(
    raw_token: str,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Verify and apply a pending email change using an EMAIL_CHANGE token.

    Invariants enforced:
    - Atomically consumes token.
    - Validates that the new email is not already taken by another user.
    - Updates user email and sets email_verified_at.
    - Increments auth_version by 1.

    Args:
        raw_token: The raw email change token.
        session: Optional SQLAlchemy database session.

    Returns:
        The updated User instance.

    Raises:
        InvalidTokenError: If token is invalid or lacks pending email.
        UserAlreadyExistsError: If new email is already registered.
        UserNotFoundError: If associated user record is missing.
    """
    sess = session if session is not None else db.session

    # Verify first before consuming
    token_record = verify_security_token(
        raw_token,
        SecurityTokenPurpose.EMAIL_CHANGE,
        session=sess,
    )

    if not token_record.pending_email:
        raise InvalidTokenError("Security token does not contain a pending email address.")

    norm_new_email = token_record.pending_email.lower()

    # Check for email conflict
    existing_user = sess.query(User).filter(User.email_normalized == norm_new_email).first()
    if existing_user is not None and existing_user.id != token_record.user_id:
        raise UserAlreadyExistsError(
            f"Email address '{norm_new_email}' is already registered to another user."
        )

    user = sess.get(User, token_record.user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {token_record.user_id} not found.")

    token_record.consumed_at = utc_now()
    user.email = norm_new_email
    user.email_verified_at = utc_now()
    user.auth_version += 1
    user.updated_at = utc_now()

    from pwd301.services.jwt_auth_service import revoke_all_user_tokens
    from pwd301.services.session_auth_service import revoke_all_user_sessions

    revoke_all_user_sessions(user.id, session=sess)
    revoke_all_user_tokens(user.id, session=sess)

    try:
        sess.commit()
    except IntegrityError as exc:
        sess.rollback()
        raise UserAlreadyExistsError(
            f"Email address '{norm_new_email}' is already registered to another user."
        ) from exc
    except Exception:
        sess.rollback()
        raise

    return user
