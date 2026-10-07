"""Integration tests for database migrations.

Verifies Alembic / Flask-Migrate upgrade and downgrade cycles against an isolated database.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest
import sqlalchemy as sa
from flask_migrate import downgrade, upgrade

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.question_bank import Question, QuestionRevision


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
            # Existing domain tables plus focus observations and learning units.
            assert "attempt_focus_events" in tables
            assert "learning_units" in tables
            assert len(tables - {"alembic_version"}) == 73
            revision_constraint = next(
                constraint["sqltext"]
                for constraint in inspector.get_check_constraints("question_revisions")
                if constraint["name"] == "ck_question_revisions_4"
            )
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

            # Run downgrade to base
            downgrade(directory="migrations", revision="base")

            # Verify all domain tables dropped cleanly
            inspector_after = sa.inspect(db.engine)
            tables_after = set(inspector_after.get_table_names())
            assert "users" not in tables_after
            assert "roles" not in tables_after
            assert "courses" not in tables_after
            assert "assessments" not in tables_after
            assert len(tables_after - {"alembic_version"}) == 0

            # Verify round-trip re-upgrade to head works cleanly
            upgrade(directory="migrations")
            inspector_re = sa.inspect(db.engine)
            tables_re = set(inspector_re.get_table_names())
            assert tables_re == tables

            # Explicitly dispose engine to release SQLite file lock on Windows
            db.engine.dispose()


def test_learning_unit_migration_backfills_without_replacing_lesson(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_url = f"sqlite:///{(Path(tmpdir) / 'backfill.db').as_posix()}"
        monkeypatch.setenv("TEST_DATABASE_URL", test_db_url)
        app = create_app("testing")
        with app.app_context():
            upgrade(directory="migrations", revision="c3d4e5f6a7b9")
            with db.engine.begin() as conn:
                conn.execute(
                    sa.text("""
                    INSERT INTO courses (
                        course_code, course_code_normalized, title, title_normalized
                    )
                    VALUES ('MIG-101', 'MIG-101', 'Migration course', 'MIGRATION COURSE')
                """)
                )
                course_id = conn.execute(
                    sa.text("SELECT id FROM courses WHERE course_code='MIG-101' ")
                ).scalar_one()
                conn.execute(
                    sa.text("""
                    INSERT INTO lessons (course_id, title, markdown_content, position)
                    VALUES (:course_id, 'Existing lesson', '# Saved content', 1)
                """),
                    {"course_id": course_id},
                )
                lesson_id = conn.execute(
                    sa.text("SELECT id FROM lessons WHERE course_id=:course_id"),
                    {"course_id": course_id},
                ).scalar_one()
            upgrade(directory="migrations")
            with db.engine.connect() as conn:
                row = conn.execute(
                    sa.text("""
                    SELECT l.id, l.markdown_content, u.title, u.course_id
                    FROM lessons l JOIN learning_units u ON u.id=l.learning_unit_id
                    WHERE l.id=:lesson_id
                """),
                    {"lesson_id": lesson_id},
                ).one()
                assert tuple(row) == (lesson_id, "# Saved content", "Existing lesson", course_id)
            db.engine.dispose()


def test_revision_type_downgrade_refuses_history_loss(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv(
            "TEST_DATABASE_URL", f"sqlite:///{(Path(tmpdir) / 'revision.db').as_posix()}"
        )
        app = create_app("testing")
        with app.app_context():
            try:
                upgrade(directory="migrations")
                course = Course(
                    course_code="MIG-REV",
                    course_code_normalized="MIG-REV",
                    title="Revision migration",
                    title_normalized="REVISION MIGRATION",
                )
                question = Question(course=course, difficulty="REMEMBER")
                revision = QuestionRevision(
                    question=question,
                    revision_no=1,
                    is_current=True,
                    question_type="SINGLE_CHOICE",
                    content="Retained historical content",
                    change_type="ANSWER_CHANGE",
                )
                db.session.add(revision)
                db.session.commit()
                with pytest.raises(SystemExit) as failure:
                    downgrade(directory="migrations", revision="b3c4d5e6f7a9")
                assert failure.value.code == 1
                assert db.session.get(QuestionRevision, revision.id).change_type == "ANSWER_CHANGE"
                assert (
                    db.session.execute(
                        sa.text("SELECT version_num FROM alembic_version")
                    ).scalar_one()
                    == "c4d5e6f7a8b0"
                )
            finally:
                db.session.remove()
                db.engine.dispose()
