"""Durable maintenance across processes and fail-closed real HTTP mutations."""

import json
import subprocess
import sys

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.notification_audit import NotificationPreference
from backend.services import operations_service
from tests.conftest import login_web_user
from tests.integration.test_sqlserver_import_atomic_retry import http_request
from tests.integration.test_sqlserver_import_atomic_retry import http_server as http_server
from tests.integration.test_sqlserver_password_reset_atomic import SecretString
from tests.unit.test_operations_service import admin_user as admin_user
from tests.unit.test_operations_service import setup_roles as setup_roles
from tests.unit.test_operations_service import student_user as student_user


@pytest.fixture(autouse=True)
def sqlserver_only(app):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires a guarded disposable SQL Server database")


@pytest.fixture
def student_headers(app, student_user):
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    login_web_user(client, student_user)
    csrf = client.get("/auth/login").json["csrf_token"]
    cookie = client.get_cookie(app.config["SESSION_COOKIE_NAME"])
    return {
        "Cookie": SecretString(f"{cookie.key}={cookie.value}"),
        "X-CSRFToken": SecretString(csrf),
    }


def preferences(engine, user_id):
    with Session(engine) as observer:
        return sorted(
            (row.category, row.email_enabled)
            for row in observer.query(NotificationPreference).filter_by(user_id=user_id)
        )


def test_http_maintenance_query_failure_blocks_write_then_retry_recovers(
    app, student_user, student_headers, http_server
):
    user_id, engine = student_user.id, db.engine
    response = http_request(student_headers, "GET", f"{http_server}/auth/preferences")
    assert response.status_code == 200
    before = preferences(engine, user_id)

    def fail_authority(conn, cursor, statement, parameters, context, executemany):
        if "from system_alerts" in statement.lower():
            raise sa.exc.OperationalError(statement, {}, RuntimeError("Authority read unavailable"))

    sa.event.listen(engine, "before_cursor_execute", fail_authority)
    try:
        denied = http_request(
            student_headers,
            "PATCH",
            f"{http_server}/auth/preferences",
            {"email_course": False},
        )
        assert denied.status_code == 503
        assert denied.json()["error"]["code"] == "MAINTENANCE_STATUS_UNAVAILABLE"
        assert preferences(engine, user_id) == before
    finally:
        sa.event.remove(engine, "before_cursor_execute", fail_authority)
    retry = http_request(
        student_headers, "PATCH", f"{http_server}/auth/preferences", {"email_course": False}
    )
    assert retry.status_code == 200
    assert dict(preferences(engine, user_id))["COURSE"] is False


WORKER_READ_SCRIPT = """
import json, os, sys
from backend import create_app
from backend.extensions import db
from backend.services.operations_service import is_maintenance_active_cached
app = create_app('testing')
for command in sys.stdin:
    with app.app_context():
        active, window = is_maintenance_active_cached(session=db.session)
        print('STATE ' + json.dumps({'pid':os.getpid(), 'active':active,
            'window':str(window.public_id) if window else None}), flush=True)
"""


def test_persistent_processes_observe_committed_maintenance_without_cache_ttl(
    app, admin_user, student_headers, http_server
):
    workers = [
        subprocess.Popen(
            [sys.executable, "-u", "-c", WORKER_READ_SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        for _ in range(2)
    ]

    def read(worker):
        assert worker.stdin is not None and worker.stdout is not None
        worker.stdin.write("read\n")
        worker.stdin.flush()
        while line := worker.stdout.readline():
            if line.startswith("STATE "):
                return json.loads(line[6:])
        raise AssertionError("Maintenance observer exited before reporting state")

    try:
        initial = [read(worker) for worker in workers]
        assert initial[0]["pid"] != initial[1]["pid"]
        assert all(not state["active"] for state in initial)
        window = operations_service.start_maintenance_window(
            admin_user, "Verified durable window", 2
        )
        window_id = str(window.public_id)
        during = [read(worker) for worker in workers]
        assert [state["pid"] for state in during] == [state["pid"] for state in initial]
        assert all(state["active"] and state["window"] == window_id for state in during)
        blocked = http_request(
            student_headers, "PATCH", f"{http_server}/auth/preferences", {"email_course": False}
        )
        assert blocked.status_code == 503
        assert blocked.json()["error"]["code"] == "MAINTENANCE_MODE_ACTIVE"
        assert http_request({}, "GET", f"{http_server}/auth/login").status_code == 200
        operations_service.end_maintenance_window(admin_user, window_id)
        after = [read(worker) for worker in workers]
        assert [state["pid"] for state in after] == [state["pid"] for state in initial]
        assert all(not state["active"] for state in after)
        resumed = http_request(
            student_headers, "PATCH", f"{http_server}/auth/preferences", {"email_course": False}
        )
        assert resumed.status_code == 200
    finally:
        for worker in workers:
            if worker.stdin is not None:
                worker.stdin.close()
            try:
                worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                worker.terminate()
                worker.wait(timeout=10)
