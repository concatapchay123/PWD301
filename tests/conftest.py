"""Pytest configuration and shared fixtures for PWD301 test suite."""

from __future__ import annotations

import contextlib
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner

from pwd301 import create_app
from pwd301.extensions import db
from scripts.test_database_guard import require_disposable_database


def _clean_mssql_database() -> None:
    """Fast teardown cleanup for SQL Server preserving migrated schema and triggers."""
    require_disposable_database(db.engine.url.render_as_string(hide_password=True))
    with contextlib.suppress(Exception):
        db.session.rollback()
    db.session.remove()
    db.engine.dispose()
    with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(sa.text("SET LOCK_TIMEOUT 5000"))
        with contextlib.suppress(Exception):
            res = conn.execute(
                sa.text(
                    "SELECT session_id FROM sys.dm_exec_sessions "
                    "WHERE database_id = DB_ID() AND session_id <> @@SPID"
                )
            )
            for row in list(res):
                with contextlib.suppress(Exception):
                    conn.execute(sa.text(f"KILL {row[0]}"))

        conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT all'"))
        conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? DISABLE TRIGGER all'"))
        res = conn.execute(
            sa.text("SELECT t.name FROM sys.tables t WHERE t.name <> 'alembic_version'")
        )
        tables = [row[0] for row in res]
        for t in tables:
            conn.execute(sa.text(f"DELETE FROM [{t}]"))
        conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? ENABLE TRIGGER all'"))
        conn.execute(
            sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT all'")
        )


@pytest.fixture
def app(tmp_path: Path) -> Generator[Flask, None, None]:
    """Create and configure a clean Flask application instance for testing."""
    config_override: dict[str, Any] = {
        "FILE_STORAGE_ROOT": tmp_path / "storage",
        "FILE_QUARANTINE_ROOT": tmp_path / "quarantine",
        "FILE_BACKUP_ROOT": tmp_path / "backups",
        "STORAGE_DIR": tmp_path / "hls",
    }
    db_url = os.environ.get("TEST_DATABASE_URL", "")
    if "mssql" in db_url:
        config_override["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": sa.pool.NullPool}

    require_disposable_database(db_url or "sqlite:///:memory:")
    test_app = create_app("testing", config_override=config_override)

    with test_app.app_context():
        dialect_name = db.engine.dialect.name
        require_disposable_database(db.engine.url.render_as_string(hide_password=True))
        if dialect_name == "mssql":
            _clean_mssql_database()
            try:
                yield test_app
            finally:
                _clean_mssql_database()
        else:
            db.create_all()
            try:
                yield test_app
            finally:
                db.session.remove()
                db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """A test client for making HTTP requests against the test application."""
    return app.test_client()


@pytest.fixture
def runner(app: Flask) -> FlaskCliRunner:
    """A test CLI runner for invoking Flask CLI commands."""
    return app.test_cli_runner()


def login_web_user(client: FlaskClient, user: Any) -> str:
    """Helper for testing Web UI routes: establishes a valid authenticated Flask session."""
    from pwd301.services.session_auth_service import create_auth_session

    _, raw_key = create_auth_session(user, session=db.session)
    db.session.commit()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["auth_session_key"] = raw_key
        sess["auth_version"] = user.auth_version
        sess["auth_source"] = "SESSION"
    return raw_key


def require_disposable_sqlserver_target(database_url: str) -> None:
    """Opt-in tests that create their own apps must satisfy the same DB safety gate."""
    target = sa.engine.make_url(database_url)
    if (
        not target.drivername.startswith("mssql")
        or not (target.database or "").startswith("pwd301_test_")
        or os.environ.get("PWD301_TEST_DB_DISPOSABLE") != "1"
    ):
        raise RuntimeError(
            "SQL Server tests require an acknowledged disposable pwd301_test_* database."
        )


@pytest.fixture(autouse=True)
def _reset_rate_limits_between_tests() -> Generator[None, None, None]:
    """Reset rate limit counters before and after each test for clean test isolation."""
    from pwd301.services.rate_limit_service import reset_all_rate_limits

    reset_all_rate_limits()
    yield
    reset_all_rate_limits()


@pytest.fixture(autouse=True)
def _reset_maintenance_cache_between_tests():
    """Disposable app databases must not share another test's maintenance lease."""
    from pwd301.services.operations_service import invalidate_maintenance_cache

    invalidate_maintenance_cache()
    yield
    invalidate_maintenance_cache()


@pytest.fixture
def playback_watch(monkeypatch):
    """Drive real pacing logic with only provider metadata and UTC clock controlled."""
    from datetime import timedelta

    from pwd301.models.types import utc_now
    from pwd301.services import playback_service

    monkeypatch.setattr(
        playback_service,
        "get_youtube_metadata",
        lambda *_: {
            "valid": True,
            "embeddable": True,
            "duration_seconds": 100,
        },
    )
    clock = [utc_now()]

    def watch(actor, lesson, fraction=1.0):
        media_id = playback_service.lesson_media_ids(lesson)[0]
        at = clock[0]
        start = playback_service.start_playback_session(actor, lesson.public_id, media_id, now=at)
        position = start["frontier"]
        payload = {
            "playback_session_id": start["session_id"],
            "media_id": media_id,
            "position_seconds": position,
            "playback_rate": 1,
            "state": "playing",
            "sequence": 1,
        }
        result = playback_service.record_playback_heartbeat(
            actor, lesson.public_id, payload, now=at
        )
        target = start["duration"] * fraction
        while position < target:
            step = min(10, target - position)
            at += timedelta(seconds=step)
            position += step
            payload.update(sequence=result["next_sequence"], position_seconds=position)
            result = playback_service.record_playback_heartbeat(
                actor, lesson.public_id, payload, now=at
            )
        clock[0] = at
        return result

    return watch


@pytest.fixture
def physical_backup_engine(app, monkeypatch, tmp_path):
    """Mock only the SQL Server command boundary, never claim a real restore drill."""
    import re
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    app.config["FILE_BACKUP_ROOT"] = tmp_path
    app.config["SQLSERVER_BACKUP_ROOT"] = "/engine/backups"
    original_get_bind = db.session.get_bind
    engine = MagicMock()
    engine.engine = engine
    engine.dialect.name = "mssql"
    engine.url = SimpleNamespace(database="isolated_unit_test")
    connection = engine.connect.return_value.execution_options.return_value.__enter__.return_value
    statements = []

    def execute(statement):
        sql = str(statement)
        statements.append(sql)
        if sql.startswith("BACKUP DATABASE"):
            filename = re.search(r"TO DISK = N'([^']+)'", sql).group(1).split("/")[-1]
            (tmp_path / filename).write_bytes(b"unit fixture physical artifact bytes")
        elif not sql.startswith("RESTORE VERIFYONLY"):
            raise AssertionError("Unit inspection must never restore a database")

    connection.execute.side_effect = execute
    monkeypatch.setattr(db.session, "get_bind", lambda: engine)
    return original_get_bind, statements
