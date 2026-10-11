import pytest

from scripts.storage_maintenance import validate_target


def test_storage_cli_rejects_live_name_containing_staging(monkeypatch):
    monkeypatch.setenv("PWD301_TEST_DB_DISPOSABLE", "1")
    with pytest.raises(RuntimeError):
        validate_target("mssql+pyodbc://localhost/staging_live", confirmed=True)
