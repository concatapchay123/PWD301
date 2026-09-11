"""Asynchronous Background Job & Queue Worker Engine for PWD301.

Implements:
- Transactional Outbox / Job Queue pattern utilizing canonical 'background_jobs' table.
- Non-blocking asynchronous dispatch via ThreadPoolExecutor so HTTP request threads never timeout.
- Worker dispatch for heavy tasks:
  - REGRADE: Asynchronous attempt regrading (regrade_worker.py)
  - FILE_SCAN: Multi-engine malware scanning / quarantine inspection
  - IMPORT: DOCX/PDF assessment import parsing & duplicate reconciliation
  - EMAIL: Asynchronous email outbox delivery and retry
- Concurrency-safe job claiming with leasing and retry limits.
- Standalone worker loop runner for production worker daemon (systemd/Docker/Gunicorn worker).
- ADR-002 Zero internal PK leakage: public UUIDv4/v5 job_key representation.
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import threading
import time
import uuid
from typing import Any

import sqlalchemy as sa
from flask import current_app
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.operations import BackgroundJob
from pwd301.models.types import utc_now
from pwd301.services.exceptions import ServiceError

logger = logging.getLogger(__name__)

# Dedicated asynchronous worker thread pool
_WORKER_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="pwd301-worker",
)
_WORKER_SHUTDOWN_LOCK = threading.Lock()


class BackgroundJobError(ServiceError):
    """Base exception for background job errors."""


class BackgroundJobNotFoundError(BackgroundJobError):
    """Raised when a specified background job cannot be located."""


def _resolve_session(
    session: Session | scoped_session[Any] | None = None,
) -> Session | scoped_session[Any]:
    return session if session is not None else db.session


def enqueue_background_job(
    job_type: str,
    payload: dict[str, Any] | None = None,
    priority: int = 100,
    dedupe_key: str | None = None,
    max_attempts: int = 5,
    run_async: bool = True,
    session: Session | scoped_session[Any] | None = None,
) -> BackgroundJob:
    """Enqueue a new task into background_jobs queue and optionally dispatch async."""
    sess = _resolve_session(session)

    valid_types = {
        "FILE_SCAN",
        "IMPORT",
        "REGRADE",
        "KNOWLEDGE_INDEX",
        "EMAIL",
        "CLEANUP",
        "ANALYTICS",
        "BACKUP",
        "EXPORT",
    }
    if job_type not in valid_types:
        raise BackgroundJobError(f"Invalid job_type '{job_type}'. Must be one of {valid_types}.")

    now = utc_now()
    payload_str = json.dumps(payload or {})

    # Check deduplication if dedupe_key provided
    if dedupe_key:
        existing = (
            sess.query(BackgroundJob)
            .filter(
                BackgroundJob.job_type == job_type,
                BackgroundJob.dedupe_key == dedupe_key,
                BackgroundJob.status.in_(["QUEUED", "RUNNING"]),
            )
            .first()
        )
        if existing is not None:
            logger.info(
                "Reusing existing active job %s for dedupe_key %s",
                existing.job_key,
                dedupe_key,
            )
            return existing

    job = BackgroundJob(
        job_key=uuid.uuid4(),
        job_type=job_type,
        dedupe_key=dedupe_key,
        status="QUEUED",
        priority=max(0, priority),
        attempt_count=0,
        max_attempts=max(1, max_attempts),
        available_at=now,
        payload_json=payload_str,
        created_at=now,
    )
    sess.add(job)
    sess.flush()

    job_id = job.id
    job_key_str = str(job.job_key)

    if run_async:
        # Capture current Flask app instance for the worker thread context
        try:
            app_obj = current_app._get_current_object()  # type: ignore[attr-defined]
        except RuntimeError:
            app_obj = None

        def _async_task() -> None:
            if app_obj is not None:
                with app_obj.app_context():
                    _run_job_safely(job_id)
            else:
                _run_job_safely(job_id)

        _WORKER_EXECUTOR.submit(_async_task)
        logger.info("Enqueued and dispatched job %s (%s)", job_key_str, job_type)
    else:
        logger.info("Enqueued job %s (%s) for sync/external execution", job_key_str, job_type)

    return job


def claim_next_background_job(
    lease_seconds: int = 300,
    session: Session | scoped_session[Any] | None = None,
) -> BackgroundJob | None:
    """Atomically claim the next eligible queued background job."""
    sess = _resolve_session(session)
    now = utc_now()
    # Query highest priority available job: either freshly QUEUED,
    # or stalled RUNNING whose lease expired
    q = (
        sess.query(BackgroundJob)
        .filter(
            sa.or_(
                sa.and_(
                    BackgroundJob.status == "QUEUED",
                    BackgroundJob.available_at <= now,
                ),
                sa.and_(
                    BackgroundJob.status == "RUNNING",
                    BackgroundJob.lease_expires_at.is_not(None),
                    BackgroundJob.lease_expires_at <= now,
                ),
            )
        )
        .order_by(BackgroundJob.priority.asc(), BackgroundJob.available_at.asc())
    )
    bind = sess.bind
    if (
        bind is not None
        and getattr(bind, "dialect", None) is not None
        and getattr(bind.dialect, "name", "") != "sqlite"
    ):
        q = q.with_for_update()
    job = q.first()

    if job is None:
        return None

    import datetime

    job.status = "RUNNING"
    job.claimed_at = now
    job.lease_expires_at = now + datetime.timedelta(seconds=lease_seconds)
    job.attempt_count += 1
    sess.flush()
    return job


def execute_background_job(
    job_id: int | BackgroundJob,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Execute a claimed background job, dispatching to the appropriate domain service."""
    sess = _resolve_session(session)
    job = job_id if isinstance(job_id, BackgroundJob) else sess.get(BackgroundJob, job_id)

    if job is None:
        raise BackgroundJobNotFoundError(f"BackgroundJob {job_id} not found.")

    payload: dict[str, Any] = {}
    if job.payload_json:
        try:
            payload = json.loads(job.payload_json)
        except Exception:
            payload = {}

    now = utc_now()
    try:
        if job.job_type == "REGRADE":
            from pwd301.services.regrade_worker import process_regrade_job

            regrade_job_id = payload.get("regrade_job_id") or payload.get("job_id")
            if regrade_job_id:
                process_regrade_job(regrade_job_id, session=sess)

        elif job.job_type == "EMAIL":
            from pwd301.services.email_service import process_email_queue

            batch_size = payload.get("batch_size", 50)
            process_email_queue(batch_size=batch_size, session=sess)

        elif job.job_type == "IMPORT":
            from pwd301.models.file_import import DocumentImportJob

            import_job_id = payload.get("import_job_id") or payload.get("job_id")
            if import_job_id:
                imp_job = sess.get(DocumentImportJob, import_job_id)
                if imp_job and imp_job.status in ("PARSING", "UPLOADED"):
                    imp_job.status = "REVIEW"
                    sess.flush()

        elif job.job_type == "FILE_SCAN":
            from pwd301.services.file_service import rescan_file_asset

            asset_id = payload.get("asset_id")
            user_id = payload.get("user_id")
            if asset_id and user_id:
                from pwd301.models.identity import User

                actor = sess.get(User, user_id)
                if actor:
                    rescan_file_asset(actor=actor, asset_id=asset_id, session=sess)

        # Mark succeeded
        job.status = "SUCCEEDED"
        job.completed_at = now
        job.last_error = None
        sess.commit()
        logger.info("BackgroundJob %s (%s) succeeded", job.job_key, job.job_type)
        return True

    except Exception as exc:
        sess.rollback()
        logger.error(
            "BackgroundJob %s (%s) failed: %s",
            job.job_key,
            job.job_type,
            exc,
            exc_info=True,
        )
        job.last_error = str(exc)[:2000]
        if job.attempt_count >= job.max_attempts:
            job.status = "FAILED"
        else:
            job.status = "QUEUED"
            import datetime

            # Exponential backoff
            delay = 2 ** min(job.attempt_count, 6) * 10
            job.available_at = now + datetime.timedelta(seconds=delay)
        sess.commit()
        return False


def _run_job_safely(job_id: int) -> None:
    """Safely invoke execute_background_job in a new database session."""
    try:
        execute_background_job(job_id, session=db.session)
    except Exception as exc:
        logger.error("Error running background job %s: %s", job_id, exc)


def run_worker_once(session: Session | scoped_session[Any] | None = None) -> bool:
    """Claim and execute a single background job. Returns True if a job was processed."""
    sess = _resolve_session(session)
    job = claim_next_background_job(session=sess)
    if job is None:
        return False
    sess.commit()
    return execute_background_job(job, session=sess)


def run_worker_loop(poll_interval_seconds: float = 2.0, max_iterations: int | None = None) -> None:
    """Run worker daemon polling loop until interrupted or max_iterations reached."""
    iterations = 0
    logger.info("Starting PWD301 Background Worker daemon loop...")
    while max_iterations is None or iterations < max_iterations:
        processed = run_worker_once()
        iterations += 1
        if not processed:
            time.sleep(poll_interval_seconds)
