"""Audit logging engine and sensitive admin action services for PWD301.

Implements canonical architecture and non-negotiable invariants:
- ADR-010: Append-only audit records. No UPDATE or DELETE mechanism exists.
- ADR-010: Fail-closed audit logging. Sensitive admin mutations roll back if audit log fails.
- ADR-002: Zero internal PK leakage. All exposed identifiers use Public UUIDs.
- Automatic recursive redaction of credentials, tokens, and secrets from audit payloads.
"""

from __future__ import annotations

import contextlib
import datetime
import json
import uuid
from typing import Any

from flask import g, has_request_context, request
from sqlalchemy import or_
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.course import Course
from pwd301.models.file_import import FileAsset
from pwd301.models.identity import AuthSession, JwtTokenGrant, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import Question
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import _resolve_user
from pwd301.services.exceptions import (
    AdminActionForbiddenError,
    AuditNotFoundError,
    AuditPersistenceError,
    ResourceNotFoundError,
    ValidationError,
)

REDACTED_TEXT = "[REDACTED]"
SENSITIVE_KEY_PATTERNS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "raw_key",
    "session_key",
    "cookie",
    "credential",
    "gemini",
    "bearer",
    "private_key",
    "authorization",
)


def redact_sensitive_data(val: Any, parent_key_is_sensitive: bool = False) -> Any:
    """Recursively redact sensitive key-values in dicts, lists, tuples, or sets.

    Ensures no passwords, API keys, tokens, session secrets, or raw hashes
    enter the audit log payload per ADR-010 and System Specification Section 15.
    """
    if isinstance(val, dict):
        cleaned: dict[str, Any] = {}
        for k, v in val.items():
            k_lower = str(k).lower()
            key_sensitive = any(p in k_lower for p in SENSITIVE_KEY_PATTERNS)
            if key_sensitive and not isinstance(v, (dict, list, tuple, set)):
                cleaned[k] = REDACTED_TEXT
            else:
                cleaned[k] = redact_sensitive_data(v, parent_key_is_sensitive=key_sensitive)
        return cleaned
    elif isinstance(val, (list, tuple)):
        items = []
        for item in val:
            if parent_key_is_sensitive and not isinstance(item, (dict, list, tuple, set)):
                items.append(REDACTED_TEXT)
            else:
                items.append(
                    redact_sensitive_data(item, parent_key_is_sensitive=parent_key_is_sensitive)
                )
        return type(val)(items) if isinstance(val, tuple) else items
    elif isinstance(val, set):
        return {
            REDACTED_TEXT
            if parent_key_is_sensitive and not isinstance(item, (dict, list, tuple, set))
            else redact_sensitive_data(item, parent_key_is_sensitive=parent_key_is_sensitive)
            for item in val
        }
    return val


def _resolve_correlation_uuid(correlation_id: str | uuid.UUID | None = None) -> uuid.UUID:
    """Resolve correlation UUID from explicit argument or Flask request context."""
    if correlation_id is not None:
        if isinstance(correlation_id, uuid.UUID):
            return correlation_id
        try:
            return uuid.UUID(str(correlation_id))
        except (ValueError, TypeError):
            return uuid.uuid4()

    if has_request_context():
        ctx_corr = getattr(g, "correlation_id", None)
        if ctx_corr:
            try:
                return uuid.UUID(str(ctx_corr))
            except (ValueError, TypeError):
                pass

    return uuid.uuid4()


def record_audit_event(
    actor: User | Any | None,
    action: str,
    target_type: str,
    target_id: int | str | uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
    reason: str | None = None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    correlation_id: str | uuid.UUID | None = None,
    performed_as_admin: bool | None = None,
    commit: bool = False,
    session: Session | scoped_session[Any] | None = None,
) -> AuditEvent:
    """Record an append-only audit event in 'audit_events'.

    Invariants enforced:
    - ADR-010: Immutable audit entry.
    - ADR-010: Fail-closed logging — raises AuditPersistenceError on failure.
    - ADR-002: Automatic redaction of credentials/secrets in before/after JSON.
    - Captures actor identity, roles snapshot, target context, and correlation ID.

    Args:
        actor: The actor User or identifier performing the action.
        action: Canonical action identifier (e.g. USER_SUSPEND, ROLE_ASSIGNED).
        target_type: Resource category (USER, COURSE, FILE_ASSET, ASSESSMENT, etc.).
        target_id: Internal BIGINT or Public UUID of target resource.
        details: Optional dict of operational details (mapped to after_state).
        reason: Justification string.
        before_state: State dictionary before mutation.
        after_state: State dictionary after mutation.
        ip_address: Client IP address (auto-resolved if in request context).
        user_agent: Client User-Agent string.
        correlation_id: Correlation GUID for distributed tracing.
        performed_as_admin: Explicit admin flag override.
        commit: If True, commits the transaction immediately.
        session: Optional SQLAlchemy session.

    Returns:
        The persisted AuditEvent instance.

    Raises:
        AuditPersistenceError: If flushing/persisting the audit record fails.
    """
    sess = session if session is not None else db.session

    # 1. Resolve actor metadata
    actor_user_id: int | None = None
    actor_roles = "SYSTEM"
    is_admin = False

    if actor is not None:
        if isinstance(actor, User):
            actor_user_id = actor.id
            actor_roles = ",".join(sorted(actor.role_codes)) if actor.role_codes else "USER"
            is_admin = actor.is_admin
        elif hasattr(actor, "id") and isinstance(actor.id, int):
            actor_user_id = actor.id
            if hasattr(actor, "role_codes"):
                actor_roles = ",".join(sorted(actor.role_codes))
            if hasattr(actor, "is_admin"):
                is_admin = bool(actor.is_admin)

    if performed_as_admin is not None:
        is_admin = performed_as_admin

    # 2. Resolve target ID for relational storage
    internal_target_id: int | None = None
    target_public_id_str: str | None = None

    if target_id is not None:
        if isinstance(target_id, int):
            internal_target_id = target_id
        else:
            target_str = str(target_id).strip()
            try:
                target_uuid = uuid.UUID(target_str)
                target_public_id_str = str(target_uuid)
                # Attempt lookup based on target_type
                upper_target_type = target_type.strip().upper()
                if upper_target_type == "USER":
                    u_row = sess.query(User.id).filter(User.public_id == target_uuid).first()
                    if u_row:
                        internal_target_id = u_row[0]
                elif upper_target_type == "COURSE":
                    c_row = sess.query(Course.id).filter(Course.public_id == target_uuid).first()
                    if c_row:
                        internal_target_id = c_row[0]
                elif upper_target_type in ("FILE", "FILE_ASSET"):
                    f_row = (
                        sess.query(FileAsset.id).filter(FileAsset.public_id == target_uuid).first()
                    )
                    if f_row:
                        internal_target_id = f_row[0]
                elif upper_target_type == "ASSESSMENT":
                    a_row = (
                        sess.query(Assessment.id)
                        .filter(Assessment.public_id == target_uuid)
                        .first()
                    )
                    if a_row:
                        internal_target_id = a_row[0]
                elif upper_target_type == "QUESTION":
                    q_row = (
                        sess.query(Question.id).filter(Question.public_id == target_uuid).first()
                    )
                    if q_row:
                        internal_target_id = q_row[0]
                elif upper_target_type in ("ATTEMPT", "ASSESSMENT_ATTEMPT"):
                    at_row = (
                        sess.query(AssessmentAttempt.id)
                        .filter(AssessmentAttempt.public_id == target_uuid)
                        .first()
                    )
                    if at_row:
                        internal_target_id = at_row[0]
            except ValueError:
                with contextlib.suppress(ValueError):
                    internal_target_id = int(target_str)

    # 3. Process states & apply redaction
    if details and after_state is None:
        after_state = dict(details)

    before_json: str | None = None
    if before_state is not None:
        clean_before = redact_sensitive_data(before_state)
        before_json = json.dumps(clean_before)

    after_json: str | None = None
    if after_state is not None:
        clean_after = redact_sensitive_data(dict(after_state))
        if target_public_id_str and "target_public_id" not in clean_after:
            clean_after["target_public_id"] = target_public_id_str
        after_json = json.dumps(clean_after)

    # 4. Resolve request context & network metadata
    request_uuid = _resolve_correlation_uuid(correlation_id)

    client_ip = ip_address
    if client_ip is None and has_request_context():
        # Do not trust raw client-supplied X-Forwarded-For headers;
        # when running behind a trusted reverse proxy, ProxyFix safely sets request.remote_addr.
        client_ip = request.remote_addr

    # 5. Build AuditEvent
    audit_entry = AuditEvent(
        event_id=uuid.uuid4(),
        actor_user_id=actor_user_id,
        actor_roles_snapshot=actor_roles,
        action=action.strip().upper(),
        target_type=target_type.strip().upper(),
        target_id=internal_target_id,
        reason=reason[:1000] if reason else None,
        before_json=before_json,
        after_json=after_json,
        request_id=request_uuid,
        ip_address=client_ip[:45] if client_ip else None,
        performed_as_admin=is_admin,
        created_at=utc_now(),
    )

    sess.add(audit_entry)

    # 6. Fail-closed guarantee
    try:
        sess.flush()
        if commit:
            sess.commit()
    except Exception as exc:
        sess.rollback()
        raise AuditPersistenceError(
            f"Failed to persist mandatory audit log for action '{action}': {exc}"
        ) from exc

    return audit_entry


def query_audit_logs(
    actor: User,
    filters: dict[str, Any] | None = None,
    page: int = 1,
    per_page: int = 20,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[list[dict[str, Any]], int, int, int, int]:
    """Query and filter audit log history with pagination.

    Enforces strict access control: only ADMIN accounts can read audit logs.
    Guarantees ADR-002 Zero Internal PK Leakage in all serialized outputs.

    Args:
        actor: Authenticated caller User (must have ADMIN role).
        filters: Optional dictionary containing query filter parameters:
                 - action (str): Action identifier filter.
                 - actor_id (str/UUID): Public UUID of actor user.
                 - target_type (str): Target resource category.
                 - target_id (str/UUID): Public UUID of target resource.
                 - date_from (str/datetime): Start of UTC creation range.
                 - date_to (str/datetime): End of UTC creation range.
                 - correlation_id (str/UUID): Correlation request identifier.
        page: 1-indexed page number (default: 1).
        per_page: Number of items per page (default: 20, max: 100).
        session: Optional SQLAlchemy session.

    Returns:
        A tuple of (items_list, total_count, page, per_page, total_pages).

    Raises:
        AdminActionForbiddenError: If caller is not an administrator.
    """
    if not actor or not actor.is_admin:
        raise AdminActionForbiddenError("Only administrators are permitted to query audit logs.")

    sess = session if session is not None else db.session
    query = sess.query(AuditEvent)

    active_filters = filters or {}

    # 1. Filter: Action
    action_val = active_filters.get("action")
    if action_val:
        query = query.filter(AuditEvent.action == str(action_val).strip().upper())

    # 2. Filter: Target Type
    target_type_val = active_filters.get("target_type")
    if target_type_val:
        query = query.filter(AuditEvent.target_type == str(target_type_val).strip().upper())

    # 3. Filter: Actor ID (Public UUID)
    actor_id_val = active_filters.get("actor_id")
    if actor_id_val:
        try:
            actor_uuid = uuid.UUID(str(actor_id_val).strip())
            actor_user_row = sess.query(User.id).filter(User.public_id == actor_uuid).first()
            if actor_user_row:
                query = query.filter(AuditEvent.actor_user_id == actor_user_row[0])
            else:
                return [], 0, page, per_page, 0
        except ValueError:
            return [], 0, page, per_page, 0

    # 4. Filter: Target ID (Public UUID)
    target_id_val = active_filters.get("target_id")
    if target_id_val:
        try:
            target_uuid = uuid.UUID(str(target_id_val).strip())
            # Search across User, Course, FileAsset to resolve internal ID
            resolved_ids = []
            u_row = sess.query(User.id).filter(User.public_id == target_uuid).first()
            if u_row:
                resolved_ids.append((u_row[0], "USER"))
            c_row = sess.query(Course.id).filter(Course.public_id == target_uuid).first()
            if c_row:
                resolved_ids.append((c_row[0], "COURSE"))
            f_row = sess.query(FileAsset.id).filter(FileAsset.public_id == target_uuid).first()
            if f_row:
                resolved_ids.append((f_row[0], "FILE_ASSET"))
                resolved_ids.append((f_row[0], "FILE"))
            a_row = sess.query(Assessment.id).filter(Assessment.public_id == target_uuid).first()
            if a_row:
                resolved_ids.append((a_row[0], "ASSESSMENT"))
            q_row = sess.query(Question.id).filter(Question.public_id == target_uuid).first()
            if q_row:
                resolved_ids.append((q_row[0], "QUESTION"))
            at_row = (
                sess.query(AssessmentAttempt.id)
                .filter(AssessmentAttempt.public_id == target_uuid)
                .first()
            )
            if at_row:
                resolved_ids.append((at_row[0], "ATTEMPT"))
                resolved_ids.append((at_row[0], "ASSESSMENT_ATTEMPT"))

            target_conditions = []
            for tid, ttype in resolved_ids:
                target_conditions.append(
                    (AuditEvent.target_id == tid) & (AuditEvent.target_type == ttype)
                )

            # Also match if target public UUID is directly mentioned in after_json
            target_conditions.append(AuditEvent.after_json.contains(str(target_uuid)))

            query = query.filter(or_(*target_conditions))
        except ValueError:
            return [], 0, page, per_page, 0

    # 5. Filter: Date range
    date_from_val = active_filters.get("date_from")
    if date_from_val:
        if isinstance(date_from_val, str):
            try:
                date_from_val = datetime.datetime.fromisoformat(date_from_val)
            except ValueError:
                date_from_val = None
        if date_from_val:
            if date_from_val.tzinfo is None:
                date_from_val = date_from_val.replace(tzinfo=datetime.UTC)
            query = query.filter(AuditEvent.created_at >= date_from_val)

    date_to_val = active_filters.get("date_to")
    if date_to_val:
        if isinstance(date_to_val, str):
            try:
                date_to_val = datetime.datetime.fromisoformat(date_to_val)
            except ValueError:
                date_to_val = None
        if date_to_val:
            if date_to_val.tzinfo is None:
                date_to_val = date_to_val.replace(tzinfo=datetime.UTC)
            query = query.filter(AuditEvent.created_at <= date_to_val)

    # 6. Filter: Correlation ID
    correlation_id_val = active_filters.get("correlation_id")
    if correlation_id_val:
        try:
            corr_uuid = uuid.UUID(str(correlation_id_val).strip())
            query = query.filter(AuditEvent.request_id == corr_uuid)
        except ValueError:
            return [], 0, page, per_page, 0

    # 7. Count & Pagination
    total = query.count()
    p = max(1, int(page))
    pp = max(1, min(100, int(per_page)))
    total_pages = max(1, (total + pp - 1) // pp) if total > 0 else 0

    events = (
        query.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .offset((p - 1) * pp)
        .limit(pp)
        .all()
    )

    # 8. Batch resolve target public UUIDs to eliminate N+1 queries
    user_target_ids = {
        e.target_id for e in events if e.target_type == "USER" and e.target_id is not None
    }
    course_target_ids = {
        e.target_id for e in events if e.target_type == "COURSE" and e.target_id is not None
    }
    file_target_ids = {
        e.target_id
        for e in events
        if e.target_type in ("FILE", "FILE_ASSET") and e.target_id is not None
    }
    assessment_target_ids = {
        e.target_id for e in events if e.target_type == "ASSESSMENT" and e.target_id is not None
    }
    question_target_ids = {
        e.target_id for e in events if e.target_type == "QUESTION" and e.target_id is not None
    }
    attempt_target_ids = {
        e.target_id
        for e in events
        if e.target_type in ("ATTEMPT", "ASSESSMENT_ATTEMPT") and e.target_id is not None
    }

    target_uuid_map: dict[tuple[str, int], str] = {}
    if user_target_ids:
        for uid, upub in sess.query(User.id, User.public_id).filter(User.id.in_(user_target_ids)):
            target_uuid_map[("USER", uid)] = str(upub)
    if course_target_ids:
        for cid, cpub in sess.query(Course.id, Course.public_id).filter(
            Course.id.in_(course_target_ids)
        ):
            target_uuid_map[("COURSE", cid)] = str(cpub)
    if file_target_ids:
        for fid, fpub in sess.query(FileAsset.id, FileAsset.public_id).filter(
            FileAsset.id.in_(file_target_ids)
        ):
            target_uuid_map[("FILE", fid)] = str(fpub)
            target_uuid_map[("FILE_ASSET", fid)] = str(fpub)
    if assessment_target_ids:
        for aid, apub in sess.query(Assessment.id, Assessment.public_id).filter(
            Assessment.id.in_(assessment_target_ids)
        ):
            target_uuid_map[("ASSESSMENT", aid)] = str(apub)
    if question_target_ids:
        for qid, qpub in sess.query(Question.id, Question.public_id).filter(
            Question.id.in_(question_target_ids)
        ):
            target_uuid_map[("QUESTION", qid)] = str(qpub)
    if attempt_target_ids:
        for atid, atpub in sess.query(AssessmentAttempt.id, AssessmentAttempt.public_id).filter(
            AssessmentAttempt.id.in_(attempt_target_ids)
        ):
            target_uuid_map[("ATTEMPT", atid)] = str(atpub)
            target_uuid_map[("ASSESSMENT_ATTEMPT", atid)] = str(atpub)

    items = []
    for e in events:
        resolved_uuid: str | None = None
        if e.target_id:
            resolved_uuid = target_uuid_map.get((e.target_type, e.target_id))
        items.append(e.to_dict(target_public_id=resolved_uuid))

    return items, total, p, pp, total_pages


def get_audit_log_detail(
    actor: User,
    audit_id: str | uuid.UUID,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Retrieve detailed single audit log entry by Public UUID event_id.

    Args:
        actor: Authenticated caller User (must be Admin).
        audit_id: Public UUID event_id of the audit record.
        session: Optional SQLAlchemy session.

    Returns:
        Serialized dictionary strictly compliant with ADR-002 Zero PK Leakage.

    Raises:
        AdminActionForbiddenError: If caller is not Admin.
        AuditNotFoundError: If record is not found.
    """
    if not actor or not actor.is_admin:
        raise AdminActionForbiddenError("Only administrators are permitted to view audit details.")

    try:
        audit_uuid = uuid.UUID(str(audit_id).strip())
    except (ValueError, TypeError) as exc:
        raise AuditNotFoundError(f"Audit log '{audit_id}' not found.") from exc

    sess = session if session is not None else db.session
    event = sess.query(AuditEvent).filter(AuditEvent.event_id == audit_uuid).first()
    if event is None:
        raise AuditNotFoundError(f"Audit log '{audit_id}' not found.")

    target_pub_id: str | None = None
    if event.target_id:
        if event.target_type == "USER":
            u_row = sess.query(User.public_id).filter(User.id == event.target_id).first()
            if u_row:
                target_pub_id = str(u_row[0])
        elif event.target_type == "COURSE":
            c_row = sess.query(Course.public_id).filter(Course.id == event.target_id).first()
            if c_row:
                target_pub_id = str(c_row[0])
        elif event.target_type in ("FILE", "FILE_ASSET"):
            f_row = sess.query(FileAsset.public_id).filter(FileAsset.id == event.target_id).first()
            if f_row:
                target_pub_id = str(f_row[0])
        elif event.target_type == "ASSESSMENT":
            a_row = (
                sess.query(Assessment.public_id).filter(Assessment.id == event.target_id).first()
            )
            if a_row:
                target_pub_id = str(a_row[0])
        elif event.target_type == "QUESTION":
            q_row = sess.query(Question.public_id).filter(Question.id == event.target_id).first()
            if q_row:
                target_pub_id = str(q_row[0])
        elif event.target_type in ("ATTEMPT", "ASSESSMENT_ATTEMPT"):
            at_row = (
                sess.query(AssessmentAttempt.public_id)
                .filter(AssessmentAttempt.id == event.target_id)
                .first()
            )
            if at_row:
                target_pub_id = str(at_row[0])

    return event.to_dict(target_public_id=target_pub_id)


# ==============================================================================
# Administrative Sensitive Action Workflows with Fail-Closed Audit Logging
# ==============================================================================


def suspend_user_account(
    admin_actor: User,
    target_user_id: str | int | uuid.UUID,
    reason: str,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Suspend user account with mandatory fail-closed audit log and instant session revocation.

    Invariants enforced:
    - Actor must be an active Administrator.
    - Reason is mandatory.
    - Administrators cannot suspend their own account.
    - User status changes to 'SUSPENDED'.
    - user.auth_version is incremented to instantly invalidate all JWT tokens.
    - All active auth_sessions and jwt_token_grants are revoked.
    - Audit log (USER_SUSPEND) is written in the SAME database transaction.
    - If audit log or transaction commit fails, everything is rolled back (Fail-Closed).

    Args:
        admin_actor: The administrator executing the suspension.
        target_user_id: Target user public ID or primary key.
        reason: Justification reason for account suspension.
        session: Optional SQLAlchemy session.

    Returns:
        The updated User instance.

    Raises:
        AdminActionForbiddenError: If actor is not Admin.
        ValidationError: If reason is empty or self-suspension is attempted.
        ResourceNotFoundError: If target user does not exist.
        AuditPersistenceError: If audit log cannot be committed (Fail-Closed).
    """
    if not admin_actor or not admin_actor.is_admin:
        raise AdminActionForbiddenError("Only administrators can suspend accounts.")

    clean_reason = (reason or "").strip()
    if not clean_reason:
        raise ValidationError("Reason is required to suspend a user account.")

    sess = session if session is not None else db.session
    target_user = _resolve_user(target_user_id, session=sess)
    if target_user is None:
        raise ResourceNotFoundError(f"User '{target_user_id}' not found.")

    if target_user.id == admin_actor.id:
        raise ValidationError("Administrators cannot suspend their own account.")

    now = utc_now()
    before_state = {
        "status": target_user.status,
        "auth_version": target_user.auth_version,
        "suspended_at": (
            target_user.suspended_at.isoformat() if target_user.suspended_at else None
        ),
        "suspension_reason": target_user.suspension_reason,
    }

    try:
        # 1. Update user state
        target_user.status = "SUSPENDED"
        target_user.suspended_at = now
        target_user.suspension_reason = clean_reason
        target_user.auth_version += 1
        target_user.updated_at = now

        # 2. Invalidate active sessions and tokens directly in this transaction
        active_sessions = (
            sess.query(AuthSession)
            .filter(
                AuthSession.user_id == target_user.id,
                AuthSession.revoked_at.is_(None),
            )
            .all()
        )
        for s in active_sessions:
            s.revoked_at = now

        active_grants = (
            sess.query(JwtTokenGrant)
            .filter(
                JwtTokenGrant.user_id == target_user.id,
                JwtTokenGrant.revoked_at.is_(None),
            )
            .all()
        )
        for g_item in active_grants:
            g_item.revoked_at = now

        after_state = {
            "status": target_user.status,
            "auth_version": target_user.auth_version,
            "suspended_at": now.isoformat(),
            "suspension_reason": clean_reason,
            "revoked_sessions_count": len(active_sessions),
            "revoked_grants_count": len(active_grants),
            "target_public_id": str(target_user.public_id),
        }

        # 3. Mandatory audit log in the same transaction
        record_audit_event(
            actor=admin_actor,
            action="USER_SUSPEND",
            target_type="USER",
            target_id=target_user.id,
            reason=clean_reason,
            before_state=before_state,
            after_state=after_state,
            session=sess,
        )

        sess.commit()
    except Exception as exc:
        sess.rollback()
        raise AuditPersistenceError(
            f"Failed to persist audit trail for account suspension: {exc}"
        ) from exc

    return target_user


def unsuspend_user_account(
    admin_actor: User,
    target_user_id: str | int | uuid.UUID,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Reactivate a suspended user account with mandatory fail-closed audit log.

    Args:
        admin_actor: The administrator executing the unsuspension.
        target_user_id: Target user public ID or primary key.
        reason: Optional justification reason.
        session: Optional SQLAlchemy session.

    Returns:
        The updated User instance.

    Raises:
        AdminActionForbiddenError: If actor is not Admin.
        ResourceNotFoundError: If target user does not exist.
        AuditPersistenceError: If audit log cannot be committed (Fail-Closed).
    """
    if not admin_actor or not admin_actor.is_admin:
        raise AdminActionForbiddenError("Only administrators can unsuspend accounts.")

    sess = session if session is not None else db.session
    target_user = _resolve_user(target_user_id, session=sess)
    if target_user is None:
        raise ResourceNotFoundError(f"User '{target_user_id}' not found.")

    now = utc_now()
    clean_reason = (reason or "").strip() or None

    before_state = {
        "status": target_user.status,
        "auth_version": target_user.auth_version,
        "suspended_at": (
            target_user.suspended_at.isoformat() if target_user.suspended_at else None
        ),
        "suspension_reason": target_user.suspension_reason,
    }

    try:
        # 1. Update user state
        target_user.status = "ACTIVE"
        target_user.suspended_at = None
        target_user.suspension_reason = None
        target_user.auth_version += 1
        target_user.updated_at = now

        after_state = {
            "status": target_user.status,
            "auth_version": target_user.auth_version,
            "suspended_at": None,
            "reason": clean_reason,
            "target_public_id": str(target_user.public_id),
        }

        # 2. Mandatory audit log in the same transaction
        record_audit_event(
            actor=admin_actor,
            action="USER_UNSUSPEND",
            target_type="USER",
            target_id=target_user.id,
            reason=clean_reason,
            before_state=before_state,
            after_state=after_state,
            session=sess,
        )

        sess.commit()
    except Exception as exc:
        sess.rollback()
        raise AuditPersistenceError(
            f"Failed to persist audit trail for account unsuspension: {exc}"
        ) from exc

    return target_user


def force_revoke_user_sessions(
    admin_actor: User,
    target_user_id: str | int | uuid.UUID,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> User:
    """Force revocation of all active sessions and tokens for a user with audit logging.

    Args:
        admin_actor: The administrator executing the revocation.
        target_user_id: Target user public ID or primary key.
        reason: Optional justification reason.
        session: Optional SQLAlchemy session.

    Returns:
        The updated User instance.

    Raises:
        AdminActionForbiddenError: If actor is not Admin.
        ResourceNotFoundError: If target user does not exist.
        AuditPersistenceError: If audit log cannot be committed (Fail-Closed).
    """
    if not admin_actor or not admin_actor.is_admin:
        raise AdminActionForbiddenError("Only administrators can force revoke user sessions.")

    sess = session if session is not None else db.session
    target_user = _resolve_user(target_user_id, session=sess)
    if target_user is None:
        raise ResourceNotFoundError(f"User '{target_user_id}' not found.")

    clean_reason = (reason or "").strip() or None
    before_state = {
        "auth_version": target_user.auth_version,
    }

    try:
        # 1. Increment auth_version to invalidate tokens
        now = utc_now()
        target_user.auth_version += 1
        target_user.updated_at = now

        # 2. Revoke active sessions & token grants directly in this transaction
        active_sessions = (
            sess.query(AuthSession)
            .filter(
                AuthSession.user_id == target_user.id,
                AuthSession.revoked_at.is_(None),
            )
            .all()
        )
        for s in active_sessions:
            s.revoked_at = now

        active_grants = (
            sess.query(JwtTokenGrant)
            .filter(
                JwtTokenGrant.user_id == target_user.id,
                JwtTokenGrant.revoked_at.is_(None),
            )
            .all()
        )
        for g_item in active_grants:
            g_item.revoked_at = now

        after_state = {
            "auth_version": target_user.auth_version,
            "revoked_sessions_count": len(active_sessions),
            "revoked_grants_count": len(active_grants),
            "reason": clean_reason,
            "target_public_id": str(target_user.public_id),
        }

        # 3. Mandatory audit log in the same transaction
        record_audit_event(
            actor=admin_actor,
            action="USER_REVOKE_SESSIONS",
            target_type="USER",
            target_id=target_user.id,
            reason=clean_reason,
            before_state=before_state,
            after_state=after_state,
            session=sess,
        )

        sess.commit()
    except Exception as exc:
        sess.rollback()
        raise AuditPersistenceError(
            f"Failed to persist audit trail for session revocation: {exc}"
        ) from exc

    return target_user
