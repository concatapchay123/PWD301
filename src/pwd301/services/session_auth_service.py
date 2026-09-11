"""Session authentication service for PWD301.

Provides business logic and lifecycle management for Web UI / AJAX authentication sessions:
- Generates cryptographically secure session identifiers.
- Persists session key hashes and metadata into the canonical 'auth_sessions' table.
- Validates sessions against expiration, explicit revocation, and user auth_version.
- Supports individual and user-wide session revocation.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import secrets
from typing import Any

from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.identity import AuthSession, User
from pwd301.models.types import utc_now
from pwd301.services.exceptions import (
    AccountNotActiveError,
    AuthVersionMismatchError,
    InvalidCredentialsError,
    SessionExpiredError,
    SessionRevokedError,
)

# Default session duration: 7 days
DEFAULT_SESSION_LIFETIME = datetime.timedelta(days=7)

# Constant-time dummy digest for side-channel timing attack mitigation
DUMMY_SESSION_KEY_HASH = hashlib.sha256(b"pwd301-timing-defense-session-key").digest()


def _ensure_utc(dt: datetime.datetime) -> datetime.datetime:
    """Ensure datetime is UTC timezone-aware for dialect-safe comparisons."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.UTC)
    return dt


def hash_session_key(raw_session_key: str) -> bytes:
    """Compute the 32-byte SHA-256 digest of a raw session key.

    Args:
        raw_session_key: The plaintext session key string.

    Returns:
        32-byte binary digest mapping to Binary32.
    """
    return hashlib.sha256(raw_session_key.encode("utf-8")).digest()


def hash_user_agent(user_agent: str | None) -> bytes | None:
    """Compute the 32-byte SHA-256 digest of a client User-Agent string.

    Args:
        user_agent: The client User-Agent header value, if present.

    Returns:
        32-byte binary digest, or None if user_agent is empty.
    """
    if not user_agent:
        return None
    return hashlib.sha256(user_agent.encode("utf-8")).digest()


def create_auth_session(
    user: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
    session_duration: datetime.timedelta | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[AuthSession, str]:
    """Create and persist a new authentication session for a user.

    Invariants enforced:
    - Only active users can establish a session.
    - Raw session key is never stored; only SHA-256 digest is persisted.
    - Session captures user's current auth_version for instantaneous global invalidation.
    - Expiration is strictly greater than creation time.

    Args:
        user: The User instance for whom the session is created.
        ip_address: Optional client IP address string.
        user_agent: Optional client User-Agent string.
        session_duration: Optional session duration (defaults to 7 days).
        session: Optional SQLAlchemy session.

    Returns:
        A tuple of (persisted AuthSession instance, raw_session_key string).

    Raises:
        AccountNotActiveError: If the user is suspended or not active.
    """
    sess = session if session is not None else db.session

    if not user.is_active:
        raise AccountNotActiveError(f"Cannot create session for inactive/suspended user {user.id}.")

    raw_session_key = secrets.token_urlsafe(32)
    key_hash = hash_session_key(raw_session_key)
    agent_hash = hash_user_agent(user_agent)

    now = utc_now()
    duration = session_duration or DEFAULT_SESSION_LIFETIME
    expires_at = now + duration

    auth_session = AuthSession(
        session_key_hash=key_hash,
        user_id=user.id,
        auth_version=user.auth_version,
        created_at=now,
        last_seen_at=now,
        expires_at=expires_at,
        revoked_at=None,
        ip_address=ip_address[:45] if ip_address else None,
        user_agent_hash=agent_hash,
    )

    sess.add(auth_session)
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return auth_session, raw_session_key


def validate_auth_session(
    raw_session_key: str,
    update_last_seen: bool = True,
    session: Session | scoped_session[Any] | None = None,
) -> AuthSession | None:
    """Validate an authentication session by its raw session key.

    Invariants enforced:
    - Session key hash must exist in 'auth_sessions'.
    - Session must not be revoked (revoked_at is None).
    - Session must not be expired (expires_at > utc_now()).
    - User account must be active.
    - auth_session.auth_version must strictly match user.auth_version.

    Args:
        raw_session_key: The raw session key presented by the client.
        update_last_seen: If True, updates last_seen_at to utc_now().
        session: Optional SQLAlchemy session.

    Returns:
        The valid AuthSession instance, or None if validation fails.
    """
    if not raw_session_key:
        return None

    sess = session if session is not None else db.session
    key_hash = hash_session_key(raw_session_key)

    auth_session = sess.query(AuthSession).filter(AuthSession.session_key_hash == key_hash).first()
    expected_hash = (
        auth_session.session_key_hash if auth_session is not None else DUMMY_SESSION_KEY_HASH
    )
    digest_matches = hmac.compare_digest(expected_hash, key_hash)
    if auth_session is None or not digest_matches:
        return None

    if auth_session.revoked_at is not None:
        return None

    now = utc_now()
    if _ensure_utc(auth_session.expires_at) <= now:
        return None

    user = sess.get(User, auth_session.user_id)
    if user is None or not user.is_active:
        return None

    if auth_session.auth_version != user.auth_version:
        return None

    if update_last_seen:
        auth_session.last_seen_at = now
        try:
            sess.commit()
        except Exception:
            sess.rollback()

    return auth_session


def verify_auth_session_or_raise(
    raw_session_key: str,
    session: Session | scoped_session[Any] | None = None,
) -> AuthSession:
    """Validate an authentication session, raising domain exceptions on failure.

    Args:
        raw_session_key: The raw session key presented by the client.
        session: Optional SQLAlchemy session.

    Returns:
        The valid AuthSession instance.

    Raises:
        InvalidCredentialsError: If the session does not exist.
        SessionRevokedError: If the session has been revoked.
        SessionExpiredError: If the session has expired.
        AccountNotActiveError: If the associated user is suspended/inactive.
        AuthVersionMismatchError: If the auth_version does not match current user version.
    """
    if not raw_session_key:
        raise InvalidCredentialsError("Session key is missing.")

    sess = session if session is not None else db.session
    key_hash = hash_session_key(raw_session_key)

    auth_session = sess.query(AuthSession).filter(AuthSession.session_key_hash == key_hash).first()
    expected_hash = (
        auth_session.session_key_hash if auth_session is not None else DUMMY_SESSION_KEY_HASH
    )
    digest_matches = hmac.compare_digest(expected_hash, key_hash)
    if auth_session is None or not digest_matches:
        raise InvalidCredentialsError("Invalid or nonexistent session.")

    if auth_session.revoked_at is not None:
        raise SessionRevokedError("Session has been revoked.")

    now = utc_now()
    if _ensure_utc(auth_session.expires_at) <= now:
        raise SessionExpiredError("Session has expired.")

    user = sess.get(User, auth_session.user_id)
    if user is None or not user.is_active:
        raise AccountNotActiveError("User account is suspended or inactive.")

    if auth_session.auth_version != user.auth_version:
        raise AuthVersionMismatchError("Session is invalidated due to user credential change.")

    auth_session.last_seen_at = now
    try:
        sess.commit()
    except Exception:
        sess.rollback()

    return auth_session


def revoke_auth_session(
    raw_session_key: str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Revoke a specific authentication session.

    Args:
        raw_session_key: The raw session key to revoke.
        session: Optional SQLAlchemy session.

    Returns:
        True if the session was found and freshly revoked, False otherwise.
    """
    if not raw_session_key:
        return False

    sess = session if session is not None else db.session
    key_hash = hash_session_key(raw_session_key)

    auth_session = sess.query(AuthSession).filter(AuthSession.session_key_hash == key_hash).first()
    if auth_session is None or not hmac.compare_digest(auth_session.session_key_hash, key_hash):
        return False

    if auth_session.revoked_at is not None:
        return False

    auth_session.revoked_at = utc_now()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return True


def revoke_all_user_sessions(
    user_id: int,
    session: Session | scoped_session[Any] | None = None,
) -> int:
    """Revoke all active authentication sessions for a user.

    Used when a user changes password, is suspended, or requests global logout.

    Args:
        user_id: Primary key of the target user.
        session: Optional SQLAlchemy session.

    Returns:
        The number of active sessions that were revoked.
    """
    sess = session if session is not None else db.session

    now = utc_now()
    active_sessions = (
        sess.query(AuthSession)
        .filter(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
        )
        .all()
    )

    count = 0
    for s in active_sessions:
        s.revoked_at = now
        count += 1

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return count
