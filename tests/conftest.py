"""Pytest configuration and shared fixtures for PWD301 test suite."""

from __future__ import annotations

import contextlib
import os
from collections.abc import Generator
from typing import Any

import pytest
import sqlalchemy as sa
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner

from pwd301 import create_app
from pwd301.extensions import db


def _clean_mssql_database() -> None:
    """Fast teardown cleanup for SQL Server preserving migrated schema and triggers."""
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
def app() -> Generator[Flask, None, None]:
    """Create and configure a clean Flask application instance for testing."""
    config_override = {}
    db_url = os.environ.get("TEST_DATABASE_URL", "")
    if "mssql" in db_url:
        config_override["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": sa.pool.NullPool}

    test_app = create_app("testing", config_override=config_override if config_override else None)

    with test_app.app_context():
        dialect_name = db.engine.dialect.name
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


@pytest.fixture(autouse=True)
def _reset_rate_limits_between_tests() -> Generator[None, None, None]:
    """Reset rate limit counters before and after each test for clean test isolation."""
    from pwd301.services.rate_limit_service import reset_all_rate_limits

    reset_all_rate_limits()
    yield
    reset_all_rate_limits()
