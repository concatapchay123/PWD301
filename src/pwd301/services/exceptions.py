"""Domain and service exceptions for PWD301.

Provides domain-specific exceptions for business logic, user management,
and security token verification.
"""

from __future__ import annotations


class ServiceError(Exception):
    """Base exception for all service-layer domain errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UserAlreadyExistsError(ServiceError):
    """Raised when an email is already registered to another user."""


class UserNotFoundError(ServiceError):
    """Raised when a requested user cannot be found."""


class InvalidEmailError(ServiceError):
    """Raised when an email address does not conform to valid structure."""


class InvalidPasswordError(ServiceError):
    """Raised when a provided password fails verification or complexity criteria."""


class AccountNotActiveError(ServiceError):
    """Raised when an operation is attempted on a suspended or inactive user."""


class InvalidTokenError(ServiceError):
    """Raised when a security token is invalid or does not exist."""


class TokenExpiredError(InvalidTokenError):
    """Raised when a security token has expired."""


class TokenAlreadyConsumedError(InvalidTokenError):
    """Raised when a single-use security token has already been consumed."""


class TokenPurposeMismatchError(InvalidTokenError):
    """Raised when a token purpose does not match the expected purpose."""


class AuthenticationError(ServiceError):
    """Base exception for all authentication errors."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when provided login credentials (email or password) are incorrect."""


class SessionExpiredError(AuthenticationError):
    """Raised when an auth session has passed its expiration time."""


class SessionRevokedError(AuthenticationError):
    """Raised when an auth session has been explicitly revoked."""


class JwtTokenInvalidError(AuthenticationError):
    """Raised when a JWT is malformed, has invalid signature, or wrong claims."""


class JwtTokenExpiredError(AuthenticationError):
    """Raised when a JWT has expired according to exp claim or grant record."""


class JwtTokenRevokedError(AuthenticationError):
    """Raised when a JWT grant has been revoked or replayed."""


class AuthVersionMismatchError(AuthenticationError):
    """Raised when a token or session auth_version does not match current user auth_version."""

