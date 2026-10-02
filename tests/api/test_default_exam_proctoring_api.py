import uuid
from typing import Any

from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.services.assessment_service import create_assessment
from tests.api.test_student_exam_backend_remediation import login_client

# Ensure fixtures from test_student_exam_backend_remediation are registered
pytest_plugins = ["tests.api.test_student_exam_backend_remediation"]


def test_create_assessment_defaults_monitoring_enabled_to_true(
    app: Any, exam_env: dict[str, Any]
) -> None:
    """Verify that create_assessment defaults monitoring_enabled and request_fullscreen to True."""
    inst_user = exam_env["instructor"]
    course = exam_env["course"]

    asm = create_assessment(
        actor=inst_user,
        course_id=course.id,
        payload={
            "title": "Exam Auto Proctoring Enabled",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 45,
            "scoring_policy": "HIGHEST",
        },
        session=db.session,
    )
    assert asm.monitoring_enabled is True
    assert asm.request_fullscreen is True


def test_default_proctoring_lifecycle_and_focus_events(
    client: FlaskClient, exam_env: dict[str, Any]
) -> None:
    """Verify focus events record duration and instructor gets total_away_seconds."""
    assessment = exam_env["assessment"]
    # Ensure monitoring_enabled is active
    assessment.monitoring_enabled = True
    assessment.request_fullscreen = True
    db.session.commit()

    csrf = login_client(client, "student_exam@pwd301.local")

    # Start attempt
    start_res = client.post(
        f"/student/assessments/{assessment.public_id}/start",
        headers={"X-CSRFToken": csrf},
    )
    assert start_res.status_code in (200, 201)
    attempt_id = start_res.get_json()["attempt_id"]

    # Delivery API must return monitoring_enabled: True and request_fullscreen: True
    delivery_res = client.get(
        f"/student/attempt/{attempt_id}",
        headers={"X-CSRFToken": csrf},
    )
    assert delivery_res.status_code == 200
    delivery = delivery_res.get_json()
    assert delivery["monitoring_enabled"] is True
    assert delivery["request_fullscreen"] is True

    # Record TAB_HIDDEN START and END
    event_id = str(uuid.uuid4())
    route = f"/student/attempt/{attempt_id}/focus-events"

    start_ev = client.post(
        route,
        json={"event_id": event_id, "event_type": "TAB_HIDDEN", "phase": "START"},
        headers={"X-CSRFToken": csrf},
    )
    assert start_ev.status_code == 200
    assert start_ev.get_json()["event_count"] >= 1

    end_ev = client.post(
        route,
        json={"event_id": event_id, "event_type": "TAB_HIDDEN", "phase": "END"},
        headers={"X-CSRFToken": csrf},
    )
    assert end_ev.status_code == 200

    # Record FULLSCREEN_EXIT START and END
    fs_event_id = str(uuid.uuid4())
    client.post(
        route,
        json={"event_id": fs_event_id, "event_type": "FULLSCREEN_EXIT", "phase": "START"},
        headers={"X-CSRFToken": csrf},
    )
    client.post(
        route,
        json={"event_id": fs_event_id, "event_type": "FULLSCREEN_EXIT", "phase": "END"},
        headers={"X-CSRFToken": csrf},
    )

    # Logout student and login instructor to review
    client.post("/auth/logout", headers={"X-CSRFToken": csrf})
    inst_csrf = login_client(client, "instructor_exam@pwd301.local")

    review_res = client.get(
        f"/instructor/attempts/{attempt_id}/focus-events",
        headers={"X-CSRFToken": inst_csrf},
    )
    assert review_res.status_code == 200
    review_data = review_res.get_json()
    assert review_data["event_count"] >= 2
    assert "total_away_seconds" in review_data
    assert isinstance(review_data["total_away_seconds"], (int, float))
    assert len(review_data["events"]) >= 2
