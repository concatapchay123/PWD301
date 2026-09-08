"""Unit tests for the application factory, extensions, and centralized error handling."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301 import create_app
from pwd301.extensions import login_manager


def test_create_app_testing() -> None:
    """Verify create_app creates an app with testing configuration."""
    app = create_app("testing")
    assert isinstance(app, Flask)
    assert app.testing is True
    assert app.config["ENV"] == "testing"


def test_create_app_invalid_environment() -> None:
    """Verify create_app raises ValueError when an unknown environment is requested."""
    with pytest.raises(ValueError, match="Unknown configuration 'invalid_env'"):
        create_app("invalid_env")


def test_extensions_are_initialized(app: Flask) -> None:
    """Verify core extensions are properly registered with the application."""
    assert "sqlalchemy" in app.extensions
    assert "migrate" in app.extensions
    assert "csrf" in app.extensions
    assert getattr(app, "login_manager", None) is login_manager


def test_correlation_id_in_response(client: FlaskClient) -> None:
    """Verify X-Correlation-ID header is generated and echoed on responses."""
    # Test without incoming correlation ID
    response = client.get("/health")
    assert "X-Correlation-ID" in response.headers
    generated_id = response.headers["X-Correlation-ID"]
    assert len(generated_id) > 0

    # Test with custom incoming correlation ID
    custom_id = "test-correlation-uuid-999"
    response2 = client.get("/health", headers={"X-Correlation-ID": custom_id})
    assert response2.headers.get("X-Correlation-ID") == custom_id


def test_404_error_handler_api_format(client: FlaskClient) -> None:
    """Verify 404 on an API route returns the standardized PWD301 JSON error payload."""
    response = client.get("/api/nonexistent-endpoint")
    assert response.status_code == 404
    assert response.is_json
    data = response.get_json()

    assert "error" in data
    error = data["error"]
    assert error["code"] == "RESOURCE_NOT_FOUND"
    assert "message" in error
    assert "field_errors" in error
    assert "correlation_id" in error


def test_404_error_handler_html_format(client: FlaskClient) -> None:
    """Verify 404 on a browser page route returns HTML with correct status code."""
    response = client.get(
        "/nonexistent-page",
        headers={"Accept": "text/html"},
    )
    assert response.status_code == 404
    assert "text/html" in response.content_type
    assert b"RESOURCE_NOT_FOUND" in response.data


def test_405_error_handler(client: FlaskClient) -> None:
    """Verify 405 Method Not Allowed returns standardized format on API routes."""
    # /health only allows GET, so POST should trigger 405
    response = client.post("/health", headers={"Accept": "application/json"})
    assert response.status_code == 405
    assert response.is_json
    data = response.get_json()
    assert data["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_500_error_handler(app: Flask) -> None:
    """Verify 500 error handler returns structured response without leaking internals."""

    @app.route("/api/test-server-error")
    def trigger_error() -> None:
        raise RuntimeError("Unexpected internal crash")

    test_client = app.test_client()
    response = test_client.get("/api/test-server-error")
    assert response.status_code == 500
    assert response.is_json
    data = response.get_json()
    assert data["error"]["code"] == "INTERNAL_ERROR"
    assert "Unexpected internal crash" not in data["error"]["message"]
    assert "correlation_id" in data["error"]


def test_create_app_default_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify create_app defaults to APP_ENV or development when config_name is None."""
    monkeypatch.setenv("APP_ENV", "testing")
    app = create_app()
    assert app.config["ENV"] == "testing"


def test_400_error_handler(app: Flask) -> None:
    """Verify 400 error handler returns VALIDATION_ERROR."""
    from werkzeug.exceptions import BadRequest

    @app.route("/api/test-bad-request")
    def trigger_bad_request() -> None:
        raise BadRequest("Invalid query parameters provided.")

    client = app.test_client()
    response = client.get("/api/test-bad-request")
    assert response.status_code == 400
    assert response.is_json
    data = response.get_json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "Invalid query parameters" in data["error"]["message"]


def test_csrf_error_handler(app: Flask) -> None:
    """Verify CSRF error handler handles CSRFError gracefully."""
    from flask_wtf.csrf import CSRFError

    @app.route("/api/test-csrf-trigger")
    def trigger_csrf() -> None:
        raise CSRFError("The CSRF token is missing.")

    client = app.test_client()
    response = client.get("/api/test-csrf-trigger")
    assert response.status_code == 400
    assert response.is_json
    data = response.get_json()
    assert data["error"]["code"] == "CSRF_ERROR"
