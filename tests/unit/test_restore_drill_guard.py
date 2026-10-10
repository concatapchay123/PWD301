import pytest


def test_restore_drill_rejects_live_target_before_connection(monkeypatch):
    from scripts.restore_drill import validate_drill_targets

    monkeypatch.setenv("PWD301_TEST_DB_DISPOSABLE", "1")
    with pytest.raises(ValueError, match="different disposable"):
        validate_drill_targets("pwd301_test_source", "PWD301")


def test_restore_drill_rejects_overwriting_source(monkeypatch):
    from scripts.restore_drill import validate_drill_targets

    monkeypatch.setenv("PWD301_TEST_DB_DISPOSABLE", "1")
    with pytest.raises(ValueError, match="different disposable"):
        validate_drill_targets("pwd301_test_source", "pwd301_test_source")
