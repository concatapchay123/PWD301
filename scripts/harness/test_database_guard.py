"""Reject destructive test cleanup against an unconfirmed database target."""

from __future__ import annotations

import os

from sqlalchemy.engine import make_url


def require_disposable_database(database_url: str) -> None:
    """Allow memory SQLite or explicitly confirmed, recognizably named test databases."""
    target = make_url(database_url)
    if target.get_backend_name() == "sqlite" and target.database in (None, "", ":memory:"):
        return
    name = target.database or ""
    if (
        os.environ.get("PWD301_TEST_DB_DISPOSABLE") != "1"
        or not name.lower().startswith("pwd301_test_")
        or target.get_backend_name() not in {"mssql", "sqlite"}
    ):
        raise RuntimeError(
            "Destructive tests require memory SQLite or PWD301_TEST_DB_DISPOSABLE=1 "
            "and a database named pwd301_test_*. No database was modified."
        )
