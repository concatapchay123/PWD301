"""Opt-in SQL Server migration round-trip coverage.

The test requires ``SQLSERVER_MIGRATION_URL`` to point at a disposable empty
SQL Server database. It is intentionally opt-in so the normal SQLite suite
cannot masquerade as SQL Server DDL coverage.
"""

from __future__ import annotations

import os
import re

import pytest
import sqlalchemy as sa
from flask_migrate import downgrade, upgrade

from pwd301 import create_app
from pwd301.extensions import db


@pytest.mark.integration
def test_sqlserver_migrations_upgrade_downgrade_upgrade_roundtrip(monkeypatch):
    database_url = os.environ.get("SQLSERVER_MIGRATION_URL")
    if not database_url:
        pytest.skip("SQLSERVER_MIGRATION_URL is required for disposable SQL Server coverage")

    monkeypatch.setenv("DATABASE_URL", database_url)
    app = create_app("development")

    with app.app_context():
        upgrade(directory="migrations")
        inspector = sa.inspect(db.engine)
        assert "lessons" in inspector.get_table_names()
        assert "revision_no" in {column["name"] for column in inspector.get_columns("lessons")}
        with db.engine.connect() as connection:
            revision_constraint = connection.execute(
                sa.text(
                    "SELECT definition FROM sys.check_constraints "
                    "WHERE parent_object_id = OBJECT_ID('dbo.question_revisions') "
                    "AND name = 'ck_question_revisions_4'"
                )
            ).scalar_one()
        assert set(re.findall(r"'([^']+)'", revision_constraint)) == {
            "INITIAL",
            "EDIT",
            "ANSWER_ONLY",
            "CONTENT_OR_CHOICES",
            "TYPO_FIX",
            "ANSWER_CHANGE",
            "CONTENT_CHANGE",
            "REVOCATION",
        }

        downgrade(directory="migrations", revision="base")
        assert "users" not in sa.inspect(db.engine).get_table_names()

        upgrade(directory="migrations")
        with db.engine.connect() as connection:
            revision = connection.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar_one()
        assert revision == "c4d5e6f7a8b0"
        db.engine.dispose()
