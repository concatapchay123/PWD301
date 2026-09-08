"""JWT authentication service for PWD301 REST API.

Provides RFC 7519 compliant JSON Web Token lifecycle management:
- Generates access/refresh token pairs backed by persisted 'jwt_token_grants'.
- Enforces session family tracking and token rotation.
- Detects refresh token replay/reuse and automatically revokes token families.
- Enforces instant token invalidation upon auth_version change or account suspension.
- Provides the @jwt_required decorator for protecting REST API endpoints.
"""

from __future__ import annotations

import datetime
from functools import wraps
from typing import Any, Callable
import uuid

from flask import current_app, g, jsonify, request
import jwt
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.identity import JwtTokenGrant, User
from pwd301.models.types import utc_now
from pwd301.services.exceptions import (
    AccountNotActiveError,
    AuthVersionMismatchError,
    JwtTokenExpiredError,
    JwtTokenInvalidError,
    JwtTokenRevokedError,
)

# Standard token lifetimes
ACCESS_TOKEN_LIFETIME = datetime.timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = datetime.timedelta(days=7)
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "pwd301"


def _ensure_utc(dt: datetime.datetime) -> datetime.datetime:
    """Ensure datetime is UTC timezone-aware for dialect-safe comparisons."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.UTC)
    return dt


def _get_jwt_secret_key() -> str:
    """Retrieve the configured JWT secret key from the active Flask application."""
    if current_app:
        secret = current_app.config.get("JWT_SECRET_KEY")
        if secret:
            return str(secret)
    return "dev-insecure-jwt-secret-change-in-production"


def create_token_pair(
    user: User,
    session_family_id: uuid.UUID | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Generate and persist an Access Token and Refresh Token pair for a user.

    Invariants enforced:
    - User account must be active.
    - Grants are recorded in 'jwt_token_grants' before returning tokens.
    - Claims include opaque public_id as subject, jti, user_id, auth_version, and family_id.
    - Signed exclusively with JWT_SECRET_KEY via HS256.

    Args:
        user: The User instance for whom tokens are generated.
        session_family_id: Optional existing session family UUID (for token rotation).
        session: Optional SQLAlchemy session.

    Returns:
        Dict containing access_token, refresh_token, token_type, and expires_in (seconds).

    Raises:
        AccountNotActiveError: If the user is suspended or not active.
    """
    sess = session if session is not None else db.session

    if not user.is_active:
        raise AccountNotActiveError(f"Cannot issue tokens for inactive/suspended user {user.id}.")

    family_id = session_family_id or uuid.uuid4()
    access_jti = uuid.uuid4()
    refresh_jti = uuid.uuid4()

    now = utc_now()
    access_exp = now + ACCESS_TOKEN_LIFETIME
    refresh_exp = now + REFRESH_TOKEN_LIFETIME

    secret = _get_jwt_secret_key()

    # Access token payload
    access_payload = {
        "iss": JWT_ISSUER,
        "sub": str(user.public_id),
        "user_id": user.id,
        "jti": str(access_jti),
        "token_type": "ACCESS",
        "auth_version": user.auth_version,
        "session_family_id": str(family_id),
        "iat": int(now.timestamp()),
        "exp": int(access_exp.timestamp()),
    }

    # Refresh token payload
    refresh_payload = {
        "iss": JWT_ISSUER,
        "sub": str(user.public_id),
        "user_id": user.id,
        "jti": str(refresh_jti),
        "token_type": "REFRESH",
        "auth_version": user.auth_version,
        "session_family_id": str(family_id),
        "iat": int(now.timestamp()),
        "exp": int(refresh_exp.timestamp()),
    }

    access_token_str = jwt.encode(access_payload, secret, algorithm=JWT_ALGORITHM)
    refresh_token_str = jwt.encode(refresh_payload, secret, algorithm=JWT_ALGORITHM)

    access_grant = JwtTokenGrant(
        jti=access_jti,
        user_id=user.id,
        session_family_id=family_id,
        auth_version=user.auth_version,
        token_type="ACCESS",
        issued_at=now,
        expires_at=access_exp,
        revoked_at=None,
    )

    refresh_grant = JwtTokenGrant(
        jti=refresh_jti,
        user_id=user.id,
        session_family_id=family_id,
        auth_version=user.auth_version,
        token_type="REFRESH",
        issued_at=now,
        expires_at=refresh_exp,
        revoked_at=None,
    )

    sess.add(access_grant)
    sess.add(refresh_grant)
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return {
        "access_token": access_token_str,
        "refresh_token": refresh_token_str,
        "token_type": "Bearer",
        "expires_in": int(ACCESS_TOKEN_LIFETIME.total_seconds()),
    }


def refresh_tokens(
    raw_refresh_token: str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Rotate a refresh token and issue a new token pair.

    Invariants enforced:
    - Verifies token signature and token_type == 'REFRESH'.
    - Replay detection: If a refresh token is used after already being revoked,
      the entire token family is immediately revoked to prevent token hijacking.
    - The old refresh grant is marked revoked and linked to the new grant via replaced_by_jti.
    - auth_version must match the user's current auth_version.

    Args:
        raw_refresh_token: The plaintext refresh JWT string.
        session: Optional SQLAlchemy session.

    Returns:
        Dict containing the new access_token, refresh_token, token_type, and expires_in.

    Raises:
        JwtTokenInvalidError: If token is malformed, invalid, or wrong type.
        JwtTokenRevokedError: If token is revoked or reuse/replay is detected.
        JwtTokenExpiredError: If token is expired.
        AccountNotActiveError: If user is inactive or suspended.
        AuthVersionMismatchError: If user auth_version has incremented.
    """
    if not raw_refresh_token:
        raise JwtTokenInvalidError("Refresh token is missing.")

    secret = _get_jwt_secret_key()
    try:
        payload = jwt.decode(
            raw_refresh_token,
            secret,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
        )
    except jwt.ExpiredSignatureError as exc:
        raise JwtTokenExpiredError("Refresh token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise JwtTokenInvalidError(f"Invalid refresh token: {exc}") from exc

    if payload.get("token_type") != "REFRESH":
        raise JwtTokenInvalidError("Provided token is not a refresh token.")

    try:
        token_jti = uuid.UUID(payload.get("jti", ""))
        family_id = uuid.UUID(payload.get("session_family_id", ""))
    except (ValueError, TypeError) as exc:
        raise JwtTokenInvalidError("Token contains invalid identifiers.") from exc

    sess = session if session is not None else db.session
    grant = sess.query(JwtTokenGrant).filter(JwtTokenGrant.jti == token_jti).first()

    if grant is None:
        raise JwtTokenInvalidError("Token grant not found.")

    now = utc_now()

    # Replay detection: if token is already revoked, revoke whole family
    if grant.revoked_at is not None:
        active_in_family = (
            sess.query(JwtTokenGrant)
            .filter(
                JwtTokenGrant.session_family_id == family_id,
                JwtTokenGrant.revoked_at.is_(None),
            )
            .all()
        )
        for g_item in active_in_family:
            g_item.revoked_at = now
        try:
            sess.commit()
        except Exception:
            sess.rollback()
        raise JwtTokenRevokedError(
            "Refresh token has already been revoked or replayed. Token family invalidated."
        )

    if _ensure_utc(grant.expires_at) <= now:
        raise JwtTokenExpiredError("Refresh token has expired.")

    user = sess.get(User, grant.user_id)
    if user is None or not user.is_active:
        raise AccountNotActiveError("User account is inactive or suspended.")

    if user.auth_version != grant.auth_version or user.auth_version != payload.get("auth_version"):
        raise AuthVersionMismatchError("Token invalidated due to user credential change.")

    # Create new pair within the same family
    new_access_jti = uuid.uuid4()
    new_refresh_jti = uuid.uuid4()
    access_exp = now + ACCESS_TOKEN_LIFETIME
    refresh_exp = now + REFRESH_TOKEN_LIFETIME

    # Mark old refresh grant as revoked and replaced
    grant.revoked_at = now
    grant.replaced_by_jti = new_refresh_jti

    new_access_payload = {
        "iss": JWT_ISSUER,
        "sub": str(user.public_id),
        "user_id": user.id,
        "jti": str(new_access_jti),
        "token_type": "ACCESS",
        "auth_version": user.auth_version,
        "session_family_id": str(family_id),
        "iat": int(now.timestamp()),
        "exp": int(access_exp.timestamp()),
    }

    new_refresh_payload = {
        "iss": JWT_ISSUER,
        "sub": str(user.public_id),
        "user_id": user.id,
        "jti": str(new_refresh_jti),
        "token_type": "REFRESH",
        "auth_version": user.auth_version,
        "session_family_id": str(family_id),
        "iat": int(now.timestamp()),
        "exp": int(refresh_exp.timestamp()),
    }

    new_access_str = jwt.encode(new_access_payload, secret, algorithm=JWT_ALGORITHM)
    new_refresh_str = jwt.encode(new_refresh_payload, secret, algorithm=JWT_ALGORITHM)

    new_access_grant = JwtTokenGrant(
        jti=new_access_jti,
        user_id=user.id,
        session_family_id=family_id,
        auth_version=user.auth_version,
        token_type="ACCESS",
        issued_at=now,
        expires_at=access_exp,
        revoked_at=None,
    )

    new_refresh_grant = JwtTokenGrant(
        jti=new_refresh_jti,
        user_id=user.id,
        session_family_id=family_id,
        auth_version=user.auth_version,
        token_type="REFRESH",
        issued_at=now,
        expires_at=refresh_exp,
        revoked_at=None,
    )

    sess.add(new_access_grant)
    sess.add(new_refresh_grant)
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return {
        "access_token": new_access_str,
        "refresh_token": new_refresh_str,
        "token_type": "Bearer",
        "expires_in": int(ACCESS_TOKEN_LIFETIME.total_seconds()),
    }


def verify_access_token(
    raw_token: str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[User, dict[str, Any]]:
    """Verify an access token and return the associated User and claims payload.

    Invariants enforced:
    - Signature validity using JWT_SECRET_KEY and HS256.
    - Token must not be expired.
    - token_type must be 'ACCESS'.
    - Grant must exist in 'jwt_token_grants' and revoked_at must be NULL.
    - Grant must not be expired in the database.
    - Associated User must exist and be ACTIVE.
    - auth_version must match between claims, DB grant, and User record.

    Args:
        raw_token: The raw access JWT string.
        session: Optional SQLAlchemy session.

    Returns:
        Tuple of (User instance, decoded claims payload dict).

    Raises:
        JwtTokenInvalidError: If token is malformed, has invalid signature, or wrong type.
        JwtTokenExpiredError: If token is expired.
        JwtTokenRevokedError: If token grant is revoked.
        AccountNotActiveError: If user is inactive or suspended.
        AuthVersionMismatchError: If user auth_version has incremented.
    """
    if not raw_token:
        raise JwtTokenInvalidError("Token is missing.")

    secret = _get_jwt_secret_key()
    try:
        payload = jwt.decode(
            raw_token,
            secret,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
        )
    except jwt.ExpiredSignatureError as exc:
        raise JwtTokenExpiredError("Access token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise JwtTokenInvalidError(f"Invalid access token: {exc}") from exc

    if payload.get("token_type") != "ACCESS":
        raise JwtTokenInvalidError("Token is not an access token.")

    try:
        token_jti = uuid.UUID(payload.get("jti", ""))
    except (ValueError, TypeError) as exc:
        raise JwtTokenInvalidError("Token contains invalid jti.") from exc

    sess = session if session is not None else db.session
    grant = sess.query(JwtTokenGrant).filter(JwtTokenGrant.jti == token_jti).first()

    if grant is None:
        raise JwtTokenInvalidError("Token grant not found.")

    if grant.revoked_at is not None:
        raise JwtTokenRevokedError("Access token has been revoked.")

    now = utc_now()
    if _ensure_utc(grant.expires_at) <= now:
        raise JwtTokenExpiredError("Access token has expired.")

    user = sess.get(User, grant.user_id)
    if user is None or not user.is_active:
        raise AccountNotActiveError("User account is inactive or suspended.")

    if user.auth_version != grant.auth_version or user.auth_version != payload.get("auth_version"):
        raise AuthVersionMismatchError("Token invalidated due to user credential change.")

    return user, payload


def revoke_token(
    raw_token_or_jti: str | uuid.UUID,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Revoke a token grant by raw JWT string or explicit JTI UUID.

    Args:
        raw_token_or_jti: The raw JWT string or UUID of the JTI.
        session: Optional SQLAlchemy session.

    Returns:
        True if the grant was found and newly marked revoked, False otherwise.
    """
    target_jti: uuid.UUID | None = None

    if isinstance(raw_token_or_jti, uuid.UUID):
        target_jti = raw_token_or_jti
    else:
        # Check if it's already a UUID string
        try:
            target_jti = uuid.UUID(raw_token_or_jti)
        except (ValueError, AttributeError):
            # Try to decode as JWT without verifying expiration
            try:
                secret = _get_jwt_secret_key()
                unverified = jwt.decode(
                    raw_token_or_jti,
                    secret,
                    algorithms=[JWT_ALGORITHM],
                    options={"verify_exp": False},
                )
                target_jti = uuid.UUID(unverified.get("jti", ""))
            except Exception:
                return False

    if target_jti is None:
        return False

    sess = session if session is not None else db.session
    grant = sess.query(JwtTokenGrant).filter(JwtTokenGrant.jti == target_jti).first()

    if grant is None or grant.revoked_at is not None:
        return False

    grant.revoked_at = utc_now()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return True


def revoke_all_user_tokens(
    user_id: int,
    session: Session | scoped_session[Any] | None = None,
) -> int:
    """Revoke all active JWT grants for a given user.

    Used when a user changes password, is suspended, or requests full API logout.

    Args:
        user_id: Primary key of the target user.
        session: Optional SQLAlchemy session.

    Returns:
        The number of grants that were revoked.
    """
    sess = session if session is not None else db.session

    now = utc_now()
    active_grants = (
        sess.query(JwtTokenGrant)
        .filter(
            JwtTokenGrant.user_id == user_id,
            JwtTokenGrant.revoked_at.is_(None),
        )
        .all()
    )

    count = 0
    for g_item in active_grants:
        g_item.revoked_at = now
        count += 1

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return count


def jwt_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator protecting REST API endpoints with Bearer JWT authentication.

    Pulls token from Authorization: Bearer <token>, verifies it, and attaches:
    - g.current_user: The authenticated User model instance.
    - g.jwt_claims: The verified JWT payload dictionary.

    Returns standard 401/403 JSON responses if authentication fails.
    """

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Missing Authorization header with Bearer token.",
                            "correlation_id": getattr(g, "correlation_id", ""),
                        }
                    }
                ),
                401,
            )

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return (
                jsonify(
                    {
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Authorization header must be Bearer <token>.",
                            "correlation_id": getattr(g, "correlation_id", ""),
                        }
                    }
                ),
                401,
            )

        token = parts[1]
        try:
            user, claims = verify_access_token(token)
        except JwtTokenExpiredError as exc:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "TOKEN_EXPIRED",
                            "message": str(exc),
                            "correlation_id": getattr(g, "correlation_id", ""),
                        }
                    }
                ),
                401,
            )
        except JwtTokenRevokedError as exc:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "TOKEN_REVOKED",
                            "message": str(exc),
                            "correlation_id": getattr(g, "correlation_id", ""),
                        }
                    }
                ),
                401,
            )
        except AuthVersionMismatchError as exc:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "AUTH_VERSION_MISMATCH",
                            "message": str(exc),
                            "correlation_id": getattr(g, "correlation_id", ""),
                        }
                    }
                ),
                401,
            )
        except AccountNotActiveError as exc:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "ACCOUNT_INACTIVE",
                            "message": str(exc),
                            "correlation_id": getattr(g, "correlation_id", ""),
                        }
                    }
                ),
                403,
            )
        except JwtTokenInvalidError as exc:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_TOKEN",
                            "message": str(exc),
                            "correlation_id": getattr(g, "correlation_id", ""),
                        }
                    }
                ),
                401,
            )
        except Exception as exc:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": f"Authentication failed: {exc}",
                            "correlation_id": getattr(g, "correlation_id", ""),
                        }
                    }
                ),
                401,
            )

        g.current_user = user
        g.jwt_claims = claims
        return f(*args, **kwargs)

    return decorated
