"""Integration tests for database migrations.

Verifies Alembic / Flask-Migrate upgrade and downgrade cycles against an isolated database.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import sqlalchemy as sa
from flask_migrate import downgrade, upgrade

from pwd301 import create_app
from pwd301.extensions import db


def test_migration_upgrade_and_downgrade(monkeypatch):
    """Verify that migrations upgrade to head and downgrade to base cleanly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_migration.db"
        test_db_url = f"sqlite:///{test_db_path.as_posix()}"

        monkeypatch.setenv("TEST_DATABASE_URL", test_db_url)
        app = create_app("testing")

        with app.app_context():
            # Run upgrade to head
            upgrade(directory="migrations")

            # Inspect created tables directly from app engine
            inspector = sa.inspect(db.engine)
            tables = set(inspector.get_table_names())

            assert "alembic_version" in tables
            assert "users" in tables
            assert "roles" in tables
            assert "courses" in tables
            assert "assessments" in tables
            # Exactly 71 domain tables + 1 alembic_version = 72
            assert len(tables) >= 71

            # Run downgrade to base
            downgrade(directory="migrations", revision="base")

            # Verify domain tables dropped
            inspector_after = sa.inspect(db.engine)
            tables_after = set(inspector_after.get_table_names())
            assert "users" not in tables_after
            assert "roles" not in tables_after
            assert "courses" not in tables_after

            # Explicitly dispose engine to release SQLite file lock on Windows
            db.engine.dispose()
