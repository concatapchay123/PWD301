"""Real SQL Server coverage for revision activation and immutable children."""

from __future__ import annotations

import os
import uuid

import pytest
import sqlalchemy as sa
from flask_migrate import upgrade

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.identity import Role
from pwd301.models.types import utc_now
from pwd301.services.course_service import create_course
from pwd301.services.question_bank_service import create_question, create_question_revision
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.mark.integration
@pytest.mark.parametrize("question_type", ["SINGLE_CHOICE", "SHORT_ANSWER"])
def test_sqlserver_revision_activation_preserves_immutable_children(monkeypatch, question_type):
    database_url = os.environ.get("SQLSERVER_MIGRATION_URL")
    if not database_url:
        pytest.skip("SQLSERVER_MIGRATION_URL is required for disposable SQL Server coverage")
    monkeypatch.setenv("DATABASE_URL", database_url)
    app = create_app("development")
    with app.app_context():
        assert db.engine.dialect.name == "mssql"
        upgrade(directory="migrations")
        try:
            for code in ("STUDENT", "INSTRUCTOR"):
                if db.session.query(Role).filter_by(code=code).first() is None:
                    db.session.add(Role(code=code, name=code.title()))
            db.session.commit()
            suffix = uuid.uuid4().hex[:12]
            instructor = register_user(
                f"revision-{suffix}@example.com", "Password@123", "Revision Test Instructor"
            )
            assign_role_to_user(instructor.id, "INSTRUCTOR")
            course = create_course(
                instructor,
                {
                    "course_code": f"REV-{suffix}",
                    "title": f"Revision trigger test {suffix}",
                },
            )
            payload = {
                "question_type": question_type,
                "difficulty": "REMEMBER",
                "content": "Original stem",
            }
            if question_type == "SINGLE_CHOICE":
                payload["choices"] = [
                    {"content": "A", "is_correct": True, "position": 1},
                    {"content": "B", "is_correct": False, "position": 2},
                ]
                table_name, text_column, error_number = (
                    "question_revision_choices",
                    "content",
                    "51007",
                )
            else:
                payload["accepted_answers"] = ["Accepted answer"]
                table_name, text_column, error_number = (
                    "question_revision_accepted_answers",
                    "answer_text",
                    "51008",
                )
            question = create_question(instructor, course.id, payload)
            question.first_used_at = utc_now()
            question.first_answered_at = utc_now()
            original = question.current_revision
            original.was_student_exposed = True
            original_id, question_id = original.id, question.id
            db.session.commit()
            revised, correction = create_question_revision(
                instructor,
                question_id,
                {
                    "change_type": "TYPO_FIX",
                    "change_reason": "Correct wording without changing answers",
                    "content": "Corrected stem",
                },
            )
            assert revised.is_current and correction is not None
            assert original.content == "Original stem" and original.is_current is False
            assert db.session.execute(
                sa.text(
                    f"SELECT COUNT(*) FROM {table_name} WHERE question_revision_id = :revision"
                ),
                {"revision": revised.id},
            ).scalar_one() == (2 if question_type == "SINGLE_CHOICE" else 1)
            with db.engine.connect() as connection:
                with pytest.raises(sa.exc.DBAPIError) as failure:
                    connection.execute(
                        sa.text(
                            f"UPDATE {table_name} SET {text_column} = 'Forbidden rewrite' "
                            "WHERE question_revision_id = :revision"
                        ),
                        {"revision": original_id},
                    )
                assert error_number in str(failure.value)
                connection.rollback()
            assert (
                db.session.execute(
                    sa.text(
                        f"SELECT COUNT(*) FROM {table_name} WHERE question_revision_id = :revision "
                        f"AND {text_column} = 'Forbidden rewrite'"
                    ),
                    {"revision": original_id},
                ).scalar_one()
                == 0
            )
        finally:
            db.session.remove()
            db.engine.dispose()
