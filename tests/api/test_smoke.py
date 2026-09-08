"""Smoke tests for core foundation endpoints."""

from __future__ import annotations

from flask import Flask
from flask.testing import FlaskClient

import pwd301
from pwd301.extensions import db
from pwd301.models.course import Course


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
    """Verify / returns canonical course catalog HTML when requested by a browser."""
    response = client.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.content_type
    html_text = response.get_data(as_text=True)
    assert "PWD301 LMS" in html_text
    assert "Khám phá Khóa học" in html_text
    assert "Chưa có khóa học nào được công khai" in html_text


def test_root_endpoint_html_with_published_course(app: Flask, client: FlaskClient) -> None:
    """Verify / displays course cards when published courses exist."""
    with app.app_context():
        course = Course(
            course_code="PWD301",
            title="Lập trình Web với Python Flask",
            description="Khóa học thực chiến toàn diện",
            category="Phát triển Web",
            status="PUBLISHED",
        )
        db.session.add(course)
        db.session.commit()

    response = client.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    html_text = response.get_data(as_text=True)
    assert "PWD301" in html_text
    assert "Lập trình Web với Python Flask" in html_text
    assert "Phát triển Web" in html_text
