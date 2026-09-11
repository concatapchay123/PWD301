"""Sliding-window rate limiting and abuse defense engine for PWD301.

Implements:
- Brute-force login lockout: max 5 consecutive failed attempts per 60 seconds per IP or email.
- Multi-worker coordination via shared filesystem sliding window in INSTANCE_PATH/rate_limits.
- Loopback/proxy protection (_TRUSTED_PROXIES) preventing platform-wide DoS on innocent users.
- AI chat request rate limiting: per-user quota protection against Gemini exhaustion.
- Email dispatch rate limiting: per-recipient flood protection for background deliveries.
- Thread-safe concurrency using threading.Lock.
- Zero external dependencies (no Redis/Celery).
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from pwd301.services.exceptions import (
    AIQuotaExceededError,
    EmailRateLimitExceededError,
)

_lock = threading.Lock()

# Sliding window storage: key -> list of float timestamps (time.time())
_login_failed_attempts: dict[str, list[float]] = defaultdict(list)
_ai_request_timestamps: dict[str, list[float]] = defaultdict(list)
_email_dispatch_timestamps: dict[str, list[float]] = defaultdict(list)

# Trusted loopback and proxy IP addresses exempt from whole-IP global lockout
_TRUSTED_PROXIES: set[str] = {"127.0.0.1", "::1", "localhost", "testclient"}


def _get_rate_limit_dir() -> Path:
    """Return directory for cross-worker rate-limit coordination."""
    from flask import current_app

    try:
        if current_app and current_app.instance_path:
            base = Path(current_app.instance_path) / "rate_limits"
            base.mkdir(parents=True, exist_ok=True)
            return base
    except Exception:
        pass

    base = Path(__file__).resolve().parent.parent.parent / "instance" / "rate_limits"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _key_to_path(key: str) -> Path:
    """Generate deterministic file path for a rate-limit tracking key."""
    key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
    return _get_rate_limit_dir() / f"{key_hash}.timestamps"


def _read_file_timestamps(key: str, window_seconds: int, now: float) -> list[float]:
    """Read unexpired timestamps for a key from shared filesystem."""
    path = _key_to_path(key)
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        cutoff = now - window_seconds
        timestamps = [float(line.strip()) for line in lines if line.strip()]
        return [t for t in timestamps if t > cutoff]
    except Exception:
        return []


def _record_file_timestamp(key: str, now: float, window_seconds: int = 300) -> None:
    """Append a timestamp to the shared filesystem file for multi-worker sync."""
    path = _key_to_path(key)
    try:
        timestamps = _read_file_timestamps(key, window_seconds, now)
        timestamps.append(now)
        cutoff = now - window_seconds
        timestamps = [t for t in timestamps if t > cutoff]
        temp_path = path.with_suffix(".tmp")
        temp_path.write_text("\n".join(str(t) for t in timestamps), encoding="utf-8")
        temp_path.replace(path)
    except Exception:
        pass


def _clear_file_timestamps(key: str) -> None:
    """Clear shared filesystem tracking file for a key."""
    path = _key_to_path(key)
    try:
        if path.is_file():
            path.unlink(missing_ok=True)
    except Exception:
        pass


def _clean_window(timestamps: list[float], window_seconds: int, now: float) -> list[float]:
    """Prune timestamps older than window_seconds."""
    cutoff = now - window_seconds
    return [t for t in timestamps if t > cutoff]


def record_failed_login(
    ip: str,
    email: str | None = None,
    session: Any = None,
) -> None:
    """Record a failed login attempt for an IP address and optional email.

    Persists to both in-process memory and shared filesystem sliding window
    for multi-worker Gunicorn coordination.
    """
    now = time.time()
    with _lock:
        if ip:
            clean_ip = ip.strip()
            _login_failed_attempts[f"ip:{clean_ip}"].append(now)
            _record_file_timestamp(f"ip:{clean_ip}", now)
        if email:
            clean_email = email.strip().lower()
            _login_failed_attempts[f"email:{clean_email}"].append(now)
            _record_file_timestamp(f"email:{clean_email}", now)


def is_login_locked(
    ip: str,
    email: str | None = None,
    max_attempts: int = 5,
    window_seconds: int = 60,
    session: Any = None,
) -> tuple[bool, int]:
    """Check whether login is locked for given IP address or email.

    Defensive rules:
    - Account lockout (5 attempts) applies to the targeted email account.
    - IP-level lockout applies to untrusted external client IPs.
    - Trusted local/proxy addresses (127.0.0.1, ::1) are never globally locked,
      preventing reverse-proxy denial-of-service against innocent users.
    - Checks both in-process memory and shared filesystem sliding window.

    Returns:
        tuple (is_locked, retry_after_seconds)
    """
    now = time.time()
    with _lock:
        keys_to_check: list[str] = []
        if email:
            keys_to_check.append(f"email:{email.strip().lower()}")
        if ip:
            clean_ip = ip.strip()
            # Do not lock out shared loopback/reverse-proxy IPs across all users
            if clean_ip not in _TRUSTED_PROXIES:
                keys_to_check.append(f"ip:{clean_ip}")

        max_retry_after = 0
        is_locked = False

        for k in keys_to_check:
            mem_timestamps = _clean_window(_login_failed_attempts[k], window_seconds, now)
            _login_failed_attempts[k] = mem_timestamps
            file_timestamps = _read_file_timestamps(k, window_seconds, now)
            all_timestamps = sorted(set(mem_timestamps + file_timestamps))
            if len(all_timestamps) >= max_attempts:
                is_locked = True
                oldest_in_window = all_timestamps[-max_attempts]
                remaining = int(window_seconds - (now - oldest_in_window)) + 1
                max_retry_after = max(max_retry_after, max(1, remaining))

        if is_locked:
            return True, max_retry_after

    return False, 0


def clear_login_attempts(
    ip: str,
    email: str | None = None,
    session: Any = None,
) -> None:
    """Clear failed login attempts upon successful authentication across all workers."""
    with _lock:
        if ip:
            clean_ip = ip.strip()
            _login_failed_attempts.pop(f"ip:{clean_ip}", None)
            _clear_file_timestamps(f"ip:{clean_ip}")
        if email:
            clean_email = email.strip().lower()
            _login_failed_attempts.pop(f"email:{clean_email}", None)
            _clear_file_timestamps(f"email:{clean_email}")


def check_ai_rate_limit(
    user_id: int | str,
    limit: int = 20,
    window_seconds: int = 60,
) -> None:
    """Check AI chat request rate limit for an authenticated user across all workers.

    Raises:
        AIQuotaExceededError: If user exceeds allowed requests within window.
    """
    now = time.time()
    key = f"user:{user_id}"
    with _lock:
        mem_timestamps = _clean_window(_ai_request_timestamps[key], window_seconds, now)
        _ai_request_timestamps[key] = mem_timestamps
        file_timestamps = _read_file_timestamps(key, window_seconds, now)
        all_timestamps = sorted(set(mem_timestamps + file_timestamps))
        if len(all_timestamps) >= limit:
            raise AIQuotaExceededError(
                "Rate limit exceeded for AI requests. "
                "Please wait a moment before sending another message."
            )
        _ai_request_timestamps[key].append(now)
        _record_file_timestamp(key, now, window_seconds=window_seconds)


def check_email_rate_limit(
    recipient_email: str,
    limit: int = 30,
    window_seconds: int = 60,
) -> None:
    """Check email dispatch rate limit for a recipient address across all workers.

    Raises:
        EmailRateLimitExceededError: If outbound email count exceeds allowed threshold.
    """
    now = time.time()
    key = f"recipient:{recipient_email.strip().lower()}"
    with _lock:
        mem_timestamps = _clean_window(_email_dispatch_timestamps[key], window_seconds, now)
        _email_dispatch_timestamps[key] = mem_timestamps
        file_timestamps = _read_file_timestamps(key, window_seconds, now)
        all_timestamps = sorted(set(mem_timestamps + file_timestamps))
        if len(all_timestamps) >= limit:
            raise EmailRateLimitExceededError(
                f"Outbound email rate limit exceeded for recipient '{recipient_email}'."
            )
        _email_dispatch_timestamps[key].append(now)
        _record_file_timestamp(key, now, window_seconds=window_seconds)


def reset_all_rate_limits() -> None:
    """Reset all in-memory and shared file rate limiting state."""
    with _lock:
        _login_failed_attempts.clear()
        _ai_request_timestamps.clear()
        _email_dispatch_timestamps.clear()
    for dir_path in [
        _get_rate_limit_dir(),
        Path(__file__).resolve().parent.parent.parent / "instance" / "rate_limits",
        Path(".rate_limits"),
    ]:
        try:
            if dir_path.is_dir():
                for f in dir_path.glob("*.timestamps*"):
                    f.unlink(missing_ok=True)
        except Exception:
            pass
