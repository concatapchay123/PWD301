"""Unit tests for background_job_service.py."""

from __future__ import annotations

import pytest
from flask import Flask

from pwd301.extensions import db
from pwd301.services.background_job_service import (
    BackgroundJobError,
    claim_next_background_job,
    enqueue_background_job,
    execute_background_job,
    run_worker_once,
)


def test_enqueue_valid_job(app: Flask) -> None:
    with app.app_context():
        job = enqueue_background_job(
            job_type="EMAIL",
            payload={"batch_size": 10},
            priority=50,
            run_async=False,
            session=db.session,
        )
        assert job.id is not None
        assert job.status == "QUEUED"
        assert job.priority == 50
        assert job.job_key is not None


def test_enqueue_invalid_job_type(app: Flask) -> None:
    with app.app_context(), pytest.raises(BackgroundJobError, match="Invalid job_type"):
        enqueue_background_job(
            job_type="INVALID_TYPE",
            run_async=False,
            session=db.session,
        )


def test_enqueue_dedupe_job(app: Flask) -> None:
    with app.app_context():
        job1 = enqueue_background_job(
            job_type="CLEANUP",
            dedupe_key="daily-cleanup",
            run_async=False,
            session=db.session,
        )
        job2 = enqueue_background_job(
            job_type="CLEANUP",
            dedupe_key="daily-cleanup",
            run_async=False,
            session=db.session,
        )
        assert job1.id == job2.id


def test_claim_and_execute_job(app: Flask) -> None:
    with app.app_context():
        job = enqueue_background_job(
            job_type="CLEANUP",
            payload={"action": "purge_stale"},
            priority=10,
            run_async=False,
            session=db.session,
        )
        db.session.commit()

        claimed = claim_next_background_job(session=db.session)
        assert claimed is not None
        assert claimed.id == job.id
        assert claimed.status == "RUNNING"
        assert claimed.attempt_count == 1
        db.session.commit()

        success = execute_background_job(claimed.id, session=db.session)
        assert success is True
        assert claimed.status == "SUCCEEDED"
        assert claimed.completed_at is not None


def test_run_worker_once(app: Flask) -> None:
    with app.app_context():
        enqueue_background_job(
            job_type="CLEANUP",
            payload={"task": "temp_cleanup"},
            run_async=False,
            session=db.session,
        )
        db.session.commit()

        processed = run_worker_once(session=db.session)
        assert processed is True

        # When no more jobs, run_worker_once returns False
        assert run_worker_once(session=db.session) is False
