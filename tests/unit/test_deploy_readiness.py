"""Deployment safety regression checks; never connect to a database."""

import pytest

from scripts.test_database_guard import require_disposable_database


def test_memory_sqlite_is_disposable(monkeypatch):
    monkeypatch.delenv("PWD301_TEST_DB_DISPOSABLE", raising=False)
    require_disposable_database("sqlite:///:memory:")


@pytest.mark.parametrize(
    "target",
    [
        "mssql+pyodbc://localhost/PWD301",
        "mssql+pyodbc://localhost/pwd301_test_staging",
        "sqlite:///instance/pwd301_dev.db",
    ],
)
def test_unconfirmed_database_is_rejected(monkeypatch, target):
    monkeypatch.delenv("PWD301_TEST_DB_DISPOSABLE", raising=False)
    with pytest.raises(RuntimeError, match="No database was modified"):
        require_disposable_database(target)


def test_confirmation_does_not_authorize_live_database(monkeypatch):
    monkeypatch.setenv("PWD301_TEST_DB_DISPOSABLE", "1")
    with pytest.raises(RuntimeError):
        require_disposable_database("mssql+pyodbc://localhost/PWD301")


def test_named_confirmed_database_is_allowed(monkeypatch):
    monkeypatch.setenv("PWD301_TEST_DB_DISPOSABLE", "1")
    require_disposable_database("mssql+pyodbc://localhost/pwd301_test_release")


def test_production_rejects_insecure_session_cookie(monkeypatch):
    from pwd301.config import ProductionConfig

    monkeypatch.setenv("SECRET_KEY", "a-secure-runtime-secret-value-32-chars-minimum")
    monkeypatch.setenv("JWT_SECRET_KEY", "another-secure-runtime-secret-32-chars-minimum")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    with pytest.raises(ValueError, match="SESSION_COOKIE_SECURE"):
        ProductionConfig()


def test_production_compose_has_private_services():
    from pathlib import Path

    import yaml

    services = yaml.safe_load(Path("deploy/compose.production.yml").read_text())["services"]
    for name in ("db", "clamav", "web", "worker"):
        assert "ports" not in services[name]
    assert services["db"]["environment"]["MSSQL_PID"] == "Express"
    assert services["web"]["environment"]["SEED_DEMO_DATA"] == "false"
    assert services["web"]["environment"]["SESSION_COOKIE_SECURE"] == "true"
    assert not any("./src" in str(v) for v in services["web"].get("volumes", []))


def test_production_baseline_requires_admin_secret(app, monkeypatch):
    from pwd301.extensions import db
    from pwd301.seeds.baseline import seed_baseline

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    with app.app_context(), pytest.raises(ValueError, match="ADMIN_PASSWORD"):
        seed_baseline(db.session)


def test_degraded_required_dependency_is_not_ready(client, monkeypatch):
    monkeypatch.setattr(
        "pwd301.services.operations_service.check_system_health",
        lambda **kwargs: {"status": "DEGRADED", "services": {}},
    )
    assert client.get("/health/deep").status_code == 503


def test_public_readiness_does_not_expose_dependency_paths_or_errors(client, monkeypatch):
    monkeypatch.setattr(
        "pwd301.services.operations_service.check_system_health",
        lambda **kwargs: {
            "status": "HEALTHY",
            "services": {
                "storage_minio": {
                    "status": "HEALTHY",
                    "directories": {"root": {"path": "/private/server/storage"}},
                },
                "mssql": {"status": "HEALTHY", "error": "private database diagnostics"},
            },
        },
    )
    response = client.get("/health/deep")
    assert response.status_code == 200
    assert "/private/server" not in response.text
    assert "private database diagnostics" not in response.text
    assert response.json["services"]["mssql"]["status"] == "HEALTHY"


def test_production_requires_clamav(monkeypatch):
    from pwd301.config import ProductionConfig

    monkeypatch.setenv("SECRET_KEY", "a-secure-runtime-secret-value-32-chars-minimum")
    monkeypatch.setenv("JWT_SECRET_KEY", "another-secure-runtime-secret-32-chars-minimum")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("CLAMAV_ENABLED", "false")
    with pytest.raises(ValueError, match="CLAMAV_ENABLED"):
        ProductionConfig()


def test_missing_worker_heartbeat_is_not_healthy(app, monkeypatch, tmp_path):
    from pwd301.extensions import db
    from pwd301.services.operations_service import _check_workers_health

    monkeypatch.setenv("WORKER_HEARTBEAT_PATH", str(tmp_path / "heartbeat.json"))
    with app.app_context():
        assert _check_workers_health(db.session)["status"] != "HEALTHY"


def test_production_without_worker_probe_is_not_ready(app, monkeypatch):
    from pwd301.extensions import db
    from pwd301.services.operations_service import _check_workers_health

    monkeypatch.delenv("WORKER_HEARTBEAT_PATH", raising=False)
    with app.app_context():
        app.config["APP_ENV"] = "production"
        assert _check_workers_health(db.session)["status"] == "DOWN"


def test_cloud_probe_fails_closed(app, monkeypatch):
    from pwd301.services.exceptions import FileStorageError
    from pwd301.services.operations_service import _check_cloud_storage_health

    def unavailable():
        raise FileStorageError("credentials missing")

    monkeypatch.setattr("pwd301.services.storage_adapter.get_s3_client", unavailable)
    with app.app_context():
        app.config["STORAGE_BACKEND"] = "s3"
        assert _check_cloud_storage_health()["status"] == "DOWN"


def test_real_health_aggregation_rejects_missing_worker(app, monkeypatch):
    from pwd301.services import operations_service as operations

    monkeypatch.setattr(
        operations, "_check_db_health", lambda sess: {"status": "HEALTHY", "latency_ms": 1}
    )
    monkeypatch.setattr(operations, "_check_storage_health", lambda: {"status": "HEALTHY"})
    monkeypatch.setattr(operations, "_check_cloud_storage_health", lambda: {"status": "HEALTHY"})
    monkeypatch.setattr(operations, "_check_clamav_health", lambda: {"status": "HEALTHY"})
    monkeypatch.setattr(operations, "_check_workers_health", lambda sess: {"status": "DOWN"})
    monkeypatch.setattr(operations, "_check_mail_queue_health", lambda sess: {"status": "HEALTHY"})
    with app.app_context():
        assert operations.check_system_health()["status"] != "HEALTHY"


def test_production_telemetry_ignores_development_host_overrides(app, monkeypatch):
    from pathlib import Path

    import psutil

    from pwd301.services.operations_service import get_real_system_telemetry

    monkeypatch.setenv("CONTAINER", "true")
    monkeypatch.setenv("HOST_TOTAL_RAM_GB", "9999")
    monkeypatch.setenv("HOST_NAME", "invented-development-host")
    monkeypatch.setenv("HOST_OS", "invented-development-os")
    monkeypatch.setattr(psutil, "cpu_freq", lambda: None)
    monkeypatch.setattr(psutil, "cpu_percent", lambda **kwargs: 5.0)
    monkeypatch.setattr(Path, "is_file", lambda self: False)
    with app.app_context():
        app.config["APP_ENV"] = "production"
        report = get_real_system_telemetry()
    assert report["memory"]["total_gb"] == round(psutil.virtual_memory().total / 1024**3, 1)
    assert report["hostname"] != "invented-development-host"
    assert report["os"] != "invented-development-os"


@pytest.mark.parametrize(
    "field,value",
    [
        ("DB_NAME", "live"),
        ("DATABASE_URL", "mssql+pyodbc://pwd301_app:x@other/live"),
        ("MIGRATION_DATABASE_URL", "mssql+pyodbc://sa:x@db/pwd301_test_release"),
    ],
)
def test_release_rejects_mismatched_database_targets(field, value):
    from scripts.deployment_urls import validate_database_targets

    settings = {
        "DB_NAME": "pwd301_test_release",
        "DATABASE_URL": "mssql+pyodbc://pwd301_app:x@db/pwd301_test_release",
        "MIGRATION_DATABASE_URL": "mssql+pyodbc://pwd301_migrator:x@db/pwd301_test_release",
    }
    settings[field] = value
    with pytest.raises(ValueError, match="declared DB_NAME"):
        validate_database_targets(settings)


def test_production_auth_runtime_never_enables_demo(app, client):
    app.config.update(APP_ENV="production", SEED_DEMO_DATA=True)
    response = client.get("/auth/runtime-config")
    assert response.status_code == 200
    assert response.json["data"] == {"environment": "production", "demo_accounts_enabled": False}


def test_demo_runtime_requires_explicit_nonproduction_seed(app, client):
    app.config["SEED_DEMO_DATA"] = True
    assert client.get("/auth/runtime-config").json["data"] == {
        "environment": "testing",
        "demo_accounts_enabled": True,
    }


def test_admin_backup_list_reads_manifest_metadata(app, tmp_path):
    import json
    from datetime import datetime
    from unittest.mock import Mock

    from pwd301.services import operations_service as operations

    artifact = tmp_path / "sample.bak"
    artifact.write_bytes(b"staging-proof")
    artifact.with_name("sample.bak.manifest.json").write_text(
        json.dumps(
            {
                "format": "PWD301_SQLSERVER_BACKUP_MANIFEST",
                "database_backup_name": "sample.bak",
                "file_size": 13,
                "sha256": "a" * 64,
            }
        )
    )
    backup = Mock(
        storage_location=str(artifact),
        verified_at=datetime.now(),
        to_dict=lambda: {"started_at": "2026-10-09", "verified_at": "2026-10-09"},
    )
    session = Mock()
    session.query.return_value.order_by.return_value.all.return_value = [backup]
    actor = Mock()
    actor.has_role.return_value = True
    with app.app_context():
        app.config["FILE_BACKUP_ROOT"] = str(tmp_path)
        result = operations.list_backups(actor, session=session)
    assert result[0]["file_size_bytes"] == 13
    assert result[0]["checksum_sha256"] == "a" * 64
