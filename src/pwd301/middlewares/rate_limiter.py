"""Rate Limiter Middleware for PWD301.

Implements a thread-safe sliding-window token-bucket rate limiter stored in-memory
with time-to-live (TTL) eviction.

Configuration tiers:
- Global: 120 requests/minute/IP
- Sensitive authentication: 10 requests/minute/IP (/auth/login, /auth/register, etc.)
- Heavy operations: 20 requests/minute/IP (/api/ai/*, /files/upload, etc.)

Exempt paths:
- /static/*
- /frontend/*
- /favicon.ico
- /admin/health, /health, /health/deep
- Disabled when app.config["RATELIMIT_ENABLED"] is False
"""

from __future__ import annotations

import math
import threading
import time
from typing import Any

from flask import Flask, Response, current_app, jsonify, request


class TokenBucket:
    """Thread-safe sliding-window Token Bucket structure for a single rate-limit identity."""

    __slots__ = ("capacity", "refill_rate", "tokens", "last_updated")

    def __init__(self, capacity: float, refill_rate: float, initial_tokens: float | None = None) -> None:
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.tokens = float(initial_tokens if initial_tokens is not None else capacity)
        self.last_updated = time.time()

    def consume(self, now: float, tokens_to_consume: float = 1.0) -> tuple[bool, int]:
        """Attempt to consume tokens.

        Args:
            now: Current timestamp in seconds.
            tokens_to_consume: Number of tokens requested.

        Returns:
            Tuple of (is_allowed, retry_after_seconds).
        """
        elapsed = max(0.0, now - self.last_updated)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_updated = now

        if self.tokens >= tokens_to_consume:
            self.tokens -= tokens_to_consume
            return True, 0

        deficit = tokens_to_consume - self.tokens
        retry_after = max(1, math.ceil(deficit / self.refill_rate))
        return False, retry_after


class RateLimiter:
    """In-memory thread-safe rate limiter supporting multiple endpoint tiers and TTL eviction."""

    AUTH_SENSITIVE_PATHS = {
        "/auth/login",
        "/api/auth/login",
        "/api/v1/auth/login",
        "/auth/register",
        "/api/auth/register",
        "/api/v1/auth/register",
        "/auth/forgot-password",
        "/api/auth/forgot-password",
        "/api/v1/auth/forgot-password",
        "/auth/reset-password",
        "/api/auth/reset-password",
        "/api/v1/auth/reset-password",
    }

    HEAVY_TASK_PREFIXES = (
        "/api/ai/",
        "/api/v1/ai/",
        "/api/ai",
        "/files/upload",
        "/api/files/upload",
        "/api/v1/files/upload",
    )

    EXEMPT_PREFIXES = (
        "/static/",
        "/frontend/",
        "/admin/health",
        "/health",
        "/favicon.ico",
    )

    def __init__(
        self,
        app: Flask | None = None,
        global_limit: int = 120,
        auth_limit: int = 60,
        heavy_limit: int = 20,
        window_seconds: float = 60.0,
        ttl_seconds: float = 120.0,
        eviction_interval_seconds: float = 60.0,
    ) -> None:
        self.global_limit = global_limit
        self.auth_limit = auth_limit
        self.heavy_limit = heavy_limit
        self.window_seconds = window_seconds
        self.ttl_seconds = ttl_seconds
        self.eviction_interval_seconds = eviction_interval_seconds

        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()
        self._last_eviction = time.time()

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Register the rate limiter with a Flask application instance."""
        app.extensions["rate_limiter"] = self
        app.before_request(self._flask_before_request_hook)

    def reset(self) -> None:
        """Clear all in-memory buckets (useful for test isolation)."""
        with self._lock:
            self._buckets.clear()
            self._last_eviction = time.time()

    def _evict_stale_buckets_locked(self, now: float) -> None:
        """Evict idle buckets that have been completely refilled and untouched beyond TTL."""
        if now - self._last_eviction < self.eviction_interval_seconds:
            return

        stale_keys: list[str] = []
        for key, bucket in self._buckets.items():
            if (now - bucket.last_updated) >= self.ttl_seconds and bucket.tokens >= (bucket.capacity - 0.001):
                stale_keys.append(key)

        for key in stale_keys:
            self._buckets.pop(key, None)

        self._last_eviction = now

    def _get_client_ip(self) -> str:
        """Extract reliable client IP from headers or remote_addr."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # First IP in comma-separated list is the client origin
            return forwarded_for.split(",")[0].strip()
        return request.remote_addr or "127.0.0.1"

    def is_exempt(self, path: str, method: str) -> bool:
        """Determine if a request is exempt from rate limiting."""
        if method == "OPTIONS":
            return True

        if current_app:
            if current_app.config.get("RATELIMIT_ENABLED") is False:
                return True

        for prefix in self.EXEMPT_PREFIXES:
            if path == prefix or path.startswith(prefix):
                return True

        return False

    def _classify_tier(self, path: str) -> tuple[str, int]:
        """Classify request path into rate limit tier name and capacity limit.

        Returns:
            Tuple of (tier_name, limit_per_minute).
        """
        # Exact or normalized match for authentication sensitive endpoints (only state-changing requests consume auth bucket)
        norm_path = path.rstrip("/")
        if norm_path in self.AUTH_SENSITIVE_PATHS or path in self.AUTH_SENSITIVE_PATHS:
            if request.method in ("POST", "PUT", "PATCH", "DELETE"):
                limit = current_app.config.get("RATELIMIT_AUTH_LIMIT", self.auth_limit) if current_app else self.auth_limit
                return "auth", limit
            # GET requests (CSRF token fetching / session verification) fall back to global tier
            limit = current_app.config.get("RATELIMIT_GLOBAL_LIMIT", self.global_limit) if current_app else self.global_limit
            return "global", limit

        # Heavy tasks (AI and uploads)
        for prefix in self.HEAVY_TASK_PREFIXES:
            if path == prefix or path.startswith(prefix):
                limit = current_app.config.get("RATELIMIT_HEAVY_LIMIT", self.heavy_limit) if current_app else self.heavy_limit
                return "heavy", limit

        # Global fallback
        limit = current_app.config.get("RATELIMIT_GLOBAL_LIMIT", self.global_limit) if current_app else self.global_limit
        return "global", limit

    def check_request(self) -> Response | None:
        """Evaluate the incoming Flask request against token bucket rules.

        Returns:
            Flask 429 Response if limit is exceeded, otherwise None to allow pass-through.
        """
        path = request.path
        method = request.method

        if self.is_exempt(path, method):
            return None

        client_ip = self._get_client_ip()
        now = time.time()
        tier_name, tier_capacity = self._classify_tier(path)
        global_capacity = (
            current_app.config.get("RATELIMIT_GLOBAL_LIMIT", self.global_limit)
            if current_app
            else self.global_limit
        )

        with self._lock:
            self._evict_stale_buckets_locked(now)

            # 1. Tier-specific check (auth or heavy)
            if tier_name != "global":
                tier_key = f"{tier_name}:{client_ip}"
                if tier_key not in self._buckets:
                    refill_rate = float(tier_capacity) / self.window_seconds
                    self._buckets[tier_key] = TokenBucket(tier_capacity, refill_rate)

                allowed, retry_after = self._buckets[tier_key].consume(now)
                if not allowed:
                    return self._create_429_response(retry_after)

            # 2. Global tier check (applies to all non-exempt requests)
            global_key = f"global:{client_ip}"
            if global_key not in self._buckets:
                global_refill_rate = float(global_capacity) / self.window_seconds
                self._buckets[global_key] = TokenBucket(global_capacity, global_refill_rate)

            allowed, retry_after = self._buckets[global_key].consume(now)
            if not allowed:
                return self._create_429_response(retry_after)

        return None

    def _create_429_response(self, retry_after: int) -> Response:
        """Format standard HTTP 429 Too Many Requests response with retry headers."""
        payload = {
            "success": False,
            "error": "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau ít phút.",
            "retry_after": int(retry_after),
        }
        resp = jsonify(payload)
        resp.status_code = 429
        resp.headers["Retry-After"] = str(int(retry_after))
        return resp

    def _flask_before_request_hook(self) -> Response | None:
        """Internal Flask before_request callback."""
        return self.check_request()


# Module-level singleton instance for convenient import and access
rate_limiter = RateLimiter()


def init_rate_limiter(app: Flask) -> RateLimiter:
    """Initialize rate limiter on the target Flask app."""
    rate_limiter.init_app(app)
    return rate_limiter


def get_rate_limiter() -> RateLimiter:
    """Retrieve the active rate limiter instance."""
    return rate_limiter
