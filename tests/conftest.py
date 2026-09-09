"""Pytest configuration and shared fixtures for PWD301 test suite."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner

from pwd301 import create_app
from pwd301.extensions import db


@pytest.fixture
def app() -> Generator[Flask, None, None]:
    """Create and configure a clean Flask application instance for testing."""
    test_app = create_app("testing")

    with test_app.app_context():
        db.create_all()
        yield test_app
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
