"""Add notification target_role, outbox subject/body, and SYSTEM preference category.

Revision ID: f6a7b8c0d1e2
Revises: e5f6a7b8c0d1
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision = "f6a7b8c0d1e2"
down_revision = "e5f6a7b8c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Update notifications table: add target_role and index
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "target_role",
                sa.String(length=20),
                nullable=True,
            )
        )
        batch_op.create_index(
            "ix_notifications_user_role_unread",
            ["recipient_user_id", "target_role", "read_at"],
            unique=False,
        )

    bind = op.get_bind()
    if bind.dialect.name == "mssql":
        op.execute(sa.text("""
            IF NOT EXISTS (
                SELECT 1 FROM sys.check_constraints 
                WHERE name = 'ck_notifications_target_role' 
                AND parent_object_id = OBJECT_ID('notifications')
            )
            BEGIN
                ALTER TABLE notifications ADD CONSTRAINT ck_notifications_target_role 
                CHECK (target_role IS NULL OR target_role IN ('STUDENT', 'INSTRUCTOR', 'ADMIN'));
            END
        """))
    elif bind.dialect.name != "sqlite":
        with op.batch_alter_table("notifications", schema=None) as batch_op:
            batch_op.create_check_constraint(
                "ck_notifications_target_role",
                "target_role IS NULL OR target_role IN ('STUDENT', 'INSTRUCTOR', 'ADMIN')",
            )

    # 2. Update email_deliveries table: add subject and body_text
    with op.batch_alter_table("email_deliveries", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "subject",
                sa.Unicode(length=250),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "body_text",
                sa.UnicodeText().with_variant(sa.NVARCHAR(), "mssql"),
                nullable=True,
            )
        )

    # 3. Update notification_preferences table: allow SYSTEM category
    if bind.dialect.name == "mssql":
        op.execute(sa.text("""
            IF EXISTS (
                SELECT 1 FROM sys.check_constraints 
                WHERE name = 'ck_notification_preferences_1' 
                AND parent_object_id = OBJECT_ID('notification_preferences')
            )
            BEGIN
                ALTER TABLE notification_preferences DROP CONSTRAINT ck_notification_preferences_1;
                ALTER TABLE notification_preferences ADD CONSTRAINT ck_notification_preferences_1 
                CHECK (category IN ('COURSE','ASSESSMENT','GRADE','MARKETING','SECURITY','SYSTEM'));
            END
        """))


def downgrade() -> None:
    bind = op.get_bind()

    # Revert notification_preferences constraint
    if bind.dialect.name == "mssql":
        op.execute(sa.text("""
            IF EXISTS (
                SELECT 1 FROM sys.check_constraints 
                WHERE name = 'ck_notification_preferences_1' 
                AND parent_object_id = OBJECT_ID('notification_preferences')
            )
            BEGIN
                ALTER TABLE notification_preferences DROP CONSTRAINT ck_notification_preferences_1;
                ALTER TABLE notification_preferences ADD CONSTRAINT ck_notification_preferences_1 
                CHECK (category IN ('COURSE','ASSESSMENT','GRADE','MARKETING','SECURITY'));
            END
        """))

    # Revert email_deliveries
    with op.batch_alter_table("email_deliveries", schema=None) as batch_op:
        batch_op.drop_column("body_text")
        batch_op.drop_column("subject")

    # Drop check constraint on notifications
    if bind.dialect.name == "mssql":
        op.execute(sa.text("""
            IF EXISTS (
                SELECT 1 FROM sys.check_constraints 
                WHERE name = 'ck_notifications_target_role' 
                AND parent_object_id = OBJECT_ID('notifications')
            )
            BEGIN
                ALTER TABLE notifications DROP CONSTRAINT ck_notifications_target_role;
            END
        """))

    # Revert notifications table
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.drop_index("ix_notifications_user_role_unread")
        batch_op.drop_column("target_role")
