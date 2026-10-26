"""Server-Sent Events (SSE) Realtime Infrastructure for PWD301.

Provides thread-safe connection subscriptions, role/user-targeted event broadcasting,
heartbeat ping keep-alive every 15 seconds, and safe domain event emission.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, Response, jsonify, request, session

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SSESubscription:
    """Thread-safe SSE client connection subscription metadata."""

    queue: queue.Queue[str]
    user_id: int | str | None = None
    role: str | None = None
    roles: frozenset[str] = field(default_factory=frozenset)


class SSEManager:
    """Manages active SSE client subscriptions, role/user event routing, and pings."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscriptions: set[SSESubscription] = set()

    def subscribe(
        self,
        user_id: int | str | None = None,
        role: str | None = None,
        roles: list[str] | set[str] | None = None,
        max_queue_size: int = 500,
    ) -> queue.Queue[str]:
        """Register a new client connection subscription."""
        client_queue: queue.Queue[str] = queue.Queue(maxsize=max_queue_size)
        norm_role = role.strip().upper() if isinstance(role, str) and role else None
        role_set: set[str] = set()
        if norm_role:
            role_set.add(norm_role)
        if roles:
            for r in roles:
                if isinstance(r, str) and r:
                    role_set.add(r.strip().upper())

        sub = SSESubscription(
            queue=client_queue,
            user_id=str(user_id) if user_id is not None else None,
            role=norm_role,
            roles=frozenset(role_set),
        )
        with self._lock:
            self._subscriptions.add(sub)
        logger.debug(
            "SSE client subscribed: user_id=%s, role=%s, total_subscribers=%d",
            user_id,
            norm_role,
            len(self._subscriptions),
        )
        return client_queue

    def unsubscribe(self, client_queue: queue.Queue[str]) -> None:
        """Unregister a client connection subscription."""
        with self._lock:
            to_remove = [s for s in self._subscriptions if s.queue is client_queue]
            for s in to_remove:
                self._subscriptions.discard(s)
        logger.debug(
            "SSE client unsubscribed; remaining_subscribers=%d",
            len(self._subscriptions),
        )

    def publish_event(
        self,
        event_type: str,
        data: dict[str, Any] | Any = None,
        target_roles: list[str] | set[str] | str | None = None,
        target_user_ids: list[int | str] | set[int | str] | int | str | None = None,
        **kwargs: Any,
    ) -> int:
        """Deliver an event to targeted or all active SSE subscribers."""
        payload_data = data if isinstance(data, dict) else ({"payload": data} if data is not None else {})
        formatted_json = json.dumps(payload_data, default=str, ensure_ascii=False)
        sse_frame = f"event: {event_type}\ndata: {formatted_json}\n\n"

        if isinstance(target_roles, str):
            target_roles = [target_roles]
        if isinstance(target_user_ids, (int, str)):
            target_user_ids = [target_user_ids]

        norm_target_roles = (
            {str(r).strip().upper() for r in target_roles if r} if target_roles else None
        )
        norm_target_users = (
            {str(u) for u in target_user_ids if u is not None} if target_user_ids else None
        )

        with self._lock:
            current_subs = list(self._subscriptions)

        delivered_count = 0
        for sub in current_subs:
            if norm_target_roles is None and norm_target_users is None:
                matches = True
            else:
                matches_role = bool(
                    norm_target_roles and (sub.roles & norm_target_roles or sub.role in norm_target_roles)
                )
                matches_user = bool(
                    norm_target_users and (sub.user_id is not None and sub.user_id in norm_target_users)
                )
                matches = matches_role or matches_user

            if matches:
                try:
                    sub.queue.put_nowait(sse_frame)
                    delivered_count += 1
                except queue.Full:
                    try:
                        sub.queue.get_nowait()
                        sub.queue.put_nowait(sse_frame)
                        delivered_count += 1
                    except Exception:
                        pass

        return delivered_count

    def broadcast(
        self,
        event_name: str,
        data: dict[str, Any] | None = None,
        target_role: str | None = None,
        target_user_id: int | str | None = None,
        target_roles: list[str] | set[str] | None = None,
        target_user_ids: list[int | str] | set[int | str] | None = None,
        **kwargs: Any,
    ) -> int:
        """Compatibility broadcast method."""
        roles = list(target_roles) if target_roles else ([target_role] if target_role else None)
        users = list(target_user_ids) if target_user_ids else ([target_user_id] if target_user_id is not None else None)
        return self.publish_event(
            event_type=event_name,
            data=data,
            target_roles=roles,
            target_user_ids=users,
            **kwargs,
        )

    def active_subscribers_count(self) -> int:
        """Return the current number of active subscriber connections."""
        with self._lock:
            return len(self._subscriptions)

    def stream_events(
        self,
        user_id: int | str | None = None,
        role: str | None = None,
        roles: list[str] | set[str] | None = None,
        timeout: float = 15.0,
    ) -> Generator[str, None, None]:
        """Generator function yielding SSE frames and 15s heartbeat pings."""
        client_queue = self.subscribe(user_id=user_id, role=role, roles=roles)
        try:
            connected_json = json.dumps(
                {
                    "status": "connected",
                    "user_id": user_id,
                    "role": role,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                default=str,
            )
            yield f"event: connected\ndata: {connected_json}\n\n"

            while True:
                try:
                    msg = client_queue.get(timeout=timeout)
                    yield msg
                except queue.Empty:
                    ping_json = json.dumps({"time": datetime.now(timezone.utc).isoformat()})
                    yield f"event: ping\ndata: {ping_json}\n\n"
        except GeneratorExit:
            pass
        finally:
            self.unsubscribe(client_queue)


# Global singleton instance
sse_manager = SSEManager()


def get_sse_manager() -> SSEManager:
    """Retrieve the global SSE manager instance."""
    return sse_manager


def stream_events(
    user_id: int | str | None = None,
    role: str | None = None,
    roles: list[str] | set[str] | None = None,
    timeout: float = 15.0,
) -> Generator[str, None, None]:
    """Module-level generator function for streaming SSE events."""
    return sse_manager.stream_events(user_id=user_id, role=role, roles=roles, timeout=timeout)


def emit_domain_event(
    event_type: str,
    payload: dict[str, Any] | Any = None,
    target_roles: list[str] | set[str] | str | None = None,
    target_user_ids: list[int | str] | set[int | str] | int | str | None = None,
    **kwargs: Any,
) -> int:
    """Safely emit a domain event across SSE subscriptions without failing DB mutations."""
    try:
        return sse_manager.publish_event(
            event_type=event_type,
            data=payload,
            target_roles=target_roles,
            target_user_ids=target_user_ids,
            **kwargs,
        )
    except Exception as exc:
        logger.warning(
            "Failed to publish domain event %s: %s",
            event_type,
            exc,
            exc_info=True,
        )
        return 0


def broadcast_event(
    event_name: str,
    data: dict[str, Any] | None = None,
    target_role: str | None = None,
    target_user_id: int | str | None = None,
    target_roles: list[str] | set[str] | None = None,
    target_user_ids: list[int | str] | set[int | str] | None = None,
    **kwargs: Any,
) -> int:
    """Compatibility function."""
    return sse_manager.broadcast(
        event_name=event_name,
        data=data,
        target_role=target_role,
        target_user_id=target_user_id,
        target_roles=target_roles,
        target_user_ids=target_user_ids,
        **kwargs,
    )


def build_sse_stream_response() -> tuple[Response, int] | Response:
    """Authenticate incoming connection and construct text/event-stream Response."""
    from backend.services.authorization_service import get_authenticated_actor

    actor = get_authenticated_actor()
    if actor is None or not getattr(actor, "is_active", False):
        return (
            jsonify(
                {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required to connect to the realtime event stream.",
                    },
                }
            ),
            401,
        )

    active_role = session.get("active_role") or getattr(actor, "primary_role", None)
    role_codes = list(getattr(actor, "role_codes", []))
    if active_role and active_role not in role_codes:
        role_codes.append(active_role)

    stream_gen = stream_events(
        user_id=actor.id,
        role=active_role,
        roles=role_codes,
        timeout=15.0,
    )
    resp = Response(stream_gen, mimetype="text/event-stream")
    resp.headers["Content-Type"] = "text/event-stream; charset=utf-8"
    resp.headers["Cache-Control"] = "no-cache, no-transform"
    resp.headers["X-Accel-Buffering"] = "no"
    resp.headers["Connection"] = "keep-alive"
    return resp


events_bp = Blueprint("events", __name__)


@events_bp.route("/api/events/stream", methods=["GET"])
@events_bp.route("/auth/events/stream", methods=["GET"])
@events_bp.route("/events/stream", methods=["GET"])
@events_bp.route("/api/notifications/events/stream", methods=["GET"])
def events_stream_route() -> tuple[Response, int] | Response:
    """Universal SSE stream endpoint for Web UI and REST API clients."""
    return build_sse_stream_response()
