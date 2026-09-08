"""Smoke tests for core foundation endpoints."""

from __future__ import annotations

from flask.testing import FlaskClient

import pwd301


def test_health_endpoint(client: FlaskClient) -> None:
    """Verify /health endpoint returns HTTP 200 and expected payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["status"] == "ok"
    assert data["env"] == "testing"
    assert data["version"] == pwd301.__version__


def test_root_endpoint_json(client: FlaskClient) -> None:
    """Verify / returns informative JSON by default or when requested."""
    response = client.get("/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["status"] == "running"
    assert "PWD301" in data["name"]
    assert data["version"] == pwd301.__version__


def test_root_endpoint_html(client: FlaskClient) -> None:
    """Verify / returns informative HTML when requested by a browser."""
    response = client.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.content_type
    assert b"PWD301 Online Course Management Platform" in response.data
    assert b"Platform bootstrap foundation is active" in response.data
