"""In-memory sliding-window rate limiting and abuse defense engine for PWD301.

Implements:
- Brute-force login lockout: max 5 consecutive failed attempts per 60 seconds per IP or email.
- AI chat request rate limiting: per-user quota protection against Gemini exhaustion.
- Email dispatch rate limiting: per-recipient flood protection for background deliveries.
- Thread-safe concurrency using threading.Lock.
- Self-cleaning sliding window mechanics with zero external dependencies (no Redis/Celery).
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict

from pwd301.services.exceptions import (
    AIQuotaExceededError,
    EmailRateLimitExceededError,
)

_lock = threading.Lock()

# Sliding window storage: key -> list of float timestamps (time.time())
_login_failed_attempts: dict[str, list[float]] = defaultdict(list)
_ai_request_timestamps: dict[str, list[float]] = defaultdict(list)
_email_dispatch_timestamps: dict[str, list[float]] = defaultdict(list)


def _clean_window(timestamps: list[float], window_seconds: int, now: float) -> list[float]:
    """Prune timestamps older than window_seconds."""
    cutoff = now - window_seconds
    return [t for t in timestamps if t > cutoff]


def record_failed_login(ip: str, email: str | None = None) -> None:
    """Record a failed login attempt for an IP address and optional email."""
    now = time.time()
    with _lock:
        if ip:
            clean_ip = ip.strip()
            _login_failed_attempts[f"ip:{clean_ip}"].append(now)
        if email:
            clean_email = email.strip().lower()
            _login_failed_attempts[f"email:{clean_email}"].append(now)


def is_login_locked(
    ip: str,
    email: str | None = None,
    max_attempts: int = 5,
    window_seconds: int = 60,
) -> tuple[bool, int]:
    """Check whether login is locked for given IP address or email.

    Args:
        ip: Remote client IP address.
        email: Optional login email address.
        max_attempts: Maximum allowed failed attempts within the window (default 5).
        window_seconds: Duration of sliding window in seconds (default 60).

    Returns:
        tuple (is_locked, retry_after_seconds)
    """
    now = time.time()
    with _lock:
        keys_to_check: list[str] = []
        if ip:
            keys_to_check.append(f"ip:{ip.strip()}")
        if email:
            keys_to_check.append(f"email:{email.strip().lower()}")

        max_retry_after = 0
        is_locked = False

        for k in keys_to_check:
            timestamps = _clean_window(_login_failed_attempts[k], window_seconds, now)
            _login_failed_attempts[k] = timestamps
            if len(timestamps) >= max_attempts:
                is_locked = True
                oldest_in_window = timestamps[0]
                remaining = int(window_seconds - (now - oldest_in_window)) + 1
                max_retry_after = max(max_retry_after, max(1, remaining))

        return is_locked, max_retry_after


def clear_login_attempts(ip: str, email: str | None = None) -> None:
    """Clear failed login attempts upon successful authentication."""
    with _lock:
        if ip:
            _login_failed_attempts.pop(f"ip:{ip.strip()}", None)
        if email:
            _login_failed_attempts.pop(f"email:{email.strip().lower()}", None)


def check_ai_rate_limit(
    user_id: int | str,
    limit: int = 20,
    window_seconds: int = 60,
) -> None:
    """Check AI chat request rate limit for an authenticated user.

    Raises:
        AIQuotaExceededError: If user exceeds allowed requests within window.
    """
    now = time.time()
    key = f"user:{user_id}"
    with _lock:
        timestamps = _clean_window(_ai_request_timestamps[key], window_seconds, now)
        if len(timestamps) >= limit:
            raise AIQuotaExceededError(
                "Rate limit exceeded for AI requests. "
                "Please wait a moment before sending another message."
            )
        timestamps.append(now)
        _ai_request_timestamps[key] = timestamps


def check_email_rate_limit(
    recipient_email: str,
    limit: int = 30,
    window_seconds: int = 60,
) -> None:
    """Check email dispatch rate limit for a recipient address.

    Raises:
        EmailRateLimitExceededError: If outbound email count exceeds allowed threshold.
    """
    now = time.time()
    key = f"recipient:{recipient_email.strip().lower()}"
    with _lock:
        timestamps = _clean_window(_email_dispatch_timestamps[key], window_seconds, now)
        if len(timestamps) >= limit:
            raise EmailRateLimitExceededError(
                f"Outbound email rate limit exceeded for recipient '{recipient_email}'."
            )
        timestamps.append(now)
        _email_dispatch_timestamps[key] = timestamps


def reset_all_rate_limits() -> None:
    """Reset all in-memory rate limiting and lockout state (primarily for test isolation)."""
    with _lock:
        _login_failed_attempts.clear()
        _ai_request_timestamps.clear()
        _email_dispatch_timestamps.clear()
