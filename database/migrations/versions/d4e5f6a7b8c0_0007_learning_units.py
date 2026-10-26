"""Group existing lessons under parent learning units without changing lesson IDs.

Revision ID: d4e5f6a7b8c0
Revises: c3d4e5f6a7b9
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision = "d4e5f6a7b8c0"
down_revision = "c3d4e5f6a7b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_units",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "public_id",
            sa.Uuid(as_uuid=True).with_variant(mssql.UNIQUEIDENTIFIER, "mssql"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            sa.BigInteger(),
            sa.ForeignKey("courses.id", name="fk_learning_units_course_id"),
            nullable=False,
        ),
        sa.Column("title", sa.Unicode(200), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime().with_variant(mssql.DATETIME2(3), "mssql"), nullable=False
        ),
        sa.Column(
            "deleted_at", sa.DateTime().with_variant(mssql.DATETIME2(3), "mssql"), nullable=True
        ),
        sa.CheckConstraint("position > 0", name="ck_learning_units_position"),
        sa.UniqueConstraint("public_id", name="uq_learning_units_public_id"),
    )
    op.create_index(
        "ix_learning_units_course_position", "learning_units", ["course_id", "position"]
    )
    with op.batch_alter_table("lessons") as batch_op:
        batch_op.add_column(sa.Column("learning_unit_id", sa.BigInteger(), nullable=True))
        batch_op.create_foreign_key(
            "fk_lessons_learning_unit_id", "learning_units", ["learning_unit_id"], ["id"]
        )

    conn = op.get_bind()
    units = sa.table(
        "learning_units",
        sa.column("id", sa.BigInteger()),
        sa.column("public_id", sa.Uuid(as_uuid=True).with_variant(mssql.UNIQUEIDENTIFIER, "mssql")),
        sa.column("course_id", sa.BigInteger()),
        sa.column("title", sa.Unicode(200)),
        sa.column("position", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
    )
    lessons = sa.table(
        "lessons",
        sa.column("id", sa.BigInteger()),
        sa.column("course_id", sa.BigInteger()),
        sa.column("title", sa.Unicode(200)),
        sa.column("position", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
        sa.column("learning_unit_id", sa.BigInteger()),
    )
    existing_lessons = conn.execute(
        sa.select(
            lessons.c.id,
            lessons.c.course_id,
            lessons.c.title,
            lessons.c.position,
            lessons.c.created_at,
        ).order_by(lessons.c.course_id, lessons.c.position, lessons.c.id)
    ).all()
    for row in existing_lessons:
        public_id = uuid.uuid4()
        conn.execute(
            sa.insert(units).values(
                public_id=public_id,
                course_id=row.course_id,
                title=row.title,
                position=row.position,
                created_at=row.created_at,
            )
        )
        unit_id = conn.execute(
            sa.select(units.c.id).where(units.c.public_id == public_id)
        ).scalar_one()
        conn.execute(
            sa.update(lessons).where(lessons.c.id == row.id).values(learning_unit_id=unit_id)
        )
    with op.batch_alter_table("lessons") as batch_op:
        batch_op.alter_column("learning_unit_id", existing_type=sa.BigInteger(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("lessons") as batch_op:
        batch_op.drop_constraint("fk_lessons_learning_unit_id", type_="foreignkey")
        batch_op.drop_column("learning_unit_id")
    op.drop_index("ix_learning_units_course_position", table_name="learning_units")
    op.drop_table("learning_units")
