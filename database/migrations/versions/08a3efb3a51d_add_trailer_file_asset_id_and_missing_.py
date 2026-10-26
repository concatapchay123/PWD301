"""add_trailer_file_asset_id_and_missing_columns

Revision ID: 08a3efb3a51d
Revises: 146415b3568e
Create Date: 2026-10-26 21:18:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql
from backend.models.types import EncryptedUnicode

# revision identifiers, used by Alembic.
revision = '08a3efb3a51d'
down_revision = '146415b3568e'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create assessment_appeals table if not exists
    op.create_table('assessment_appeals',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
        sa.Column('public_id', sa.Uuid().with_variant(mssql.UNIQUEIDENTIFIER(), 'mssql'), server_default=sa.text('NEWSEQUENTIALID()'), nullable=False),
        sa.Column('assessment_attempt_id', sa.BigInteger(), nullable=False),
        sa.Column('student_user_id', sa.BigInteger(), nullable=False),
        sa.Column('course_id', sa.BigInteger(), nullable=False),
        sa.Column('reason', sa.Unicode(length=255), nullable=False),
        sa.Column('student_note', sa.UnicodeText().with_variant(sa.NVARCHAR(), 'mssql'), nullable=True),
        sa.Column('status', sa.String(length=20), server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column('original_score', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('final_score', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('instructor_feedback', sa.UnicodeText().with_variant(sa.NVARCHAR(), 'mssql'), nullable=True),
        sa.Column('evidence_filename', sa.Unicode(length=255), nullable=True),
        sa.Column('evidence_url', sa.Unicode(length=500), nullable=True),
        sa.Column('reviewed_by_user_id', sa.BigInteger(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime().with_variant(mssql.DATETIME2(precision=3), 'mssql'), nullable=True),
        sa.Column('created_at', sa.DateTime().with_variant(mssql.DATETIME2(precision=3), 'mssql'), server_default=sa.text('SYSUTCDATETIME()'), nullable=False),
        sa.Column('updated_at', sa.DateTime().with_variant(mssql.DATETIME2(precision=3), 'mssql'), server_default=sa.text('SYSUTCDATETIME()'), nullable=False),
        sa.Column('row_version', sa.LargeBinary(length=8).with_variant(mssql.ROWVERSION(), 'mssql'), nullable=True),
        sa.CheckConstraint("status IN ('PENDING','RESOLVED','REJECTED')", name='ck_assessment_appeals_status'),
        sa.ForeignKeyConstraint(['assessment_attempt_id'], ['assessment_attempts.id'], name='fk_assessment_appeals_attempt_id'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_assessment_appeals_course_id'),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id'], name='fk_assessment_appeals_reviewed_by_user_id'),
        sa.ForeignKeyConstraint(['student_user_id'], ['users.id'], name='fk_assessment_appeals_student_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id')
    )
    with op.batch_alter_table('assessment_appeals', schema=None) as batch_op:
        batch_op.create_index('ix_assessment_appeals_attempt', ['assessment_attempt_id'], unique=False)
        batch_op.create_index('ix_assessment_appeals_course_status', ['course_id', 'status'], unique=False)
        batch_op.create_index('ix_assessment_appeals_student', ['student_user_id'], unique=False)

    # 2. Add trailer_file_asset_id to courses
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('trailer_file_asset_id', sa.BigInteger(), nullable=True))
        batch_op.create_foreign_key('fk_courses_trailer_file_asset_id', 'file_assets', ['trailer_file_asset_id'], ['id'])

    # 3. Expand display_name on users to NVARCHAR(300) for EncryptedUnicode support
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('display_name',
               existing_type=sa.Unicode(length=150),
               type_=sa.Unicode(length=300),
               existing_nullable=False)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('display_name',
               existing_type=sa.Unicode(length=300),
               type_=sa.Unicode(length=150),
               existing_nullable=False)

    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.drop_constraint('fk_courses_trailer_file_asset_id', type_='foreignkey')
        batch_op.drop_column('trailer_file_asset_id')

    with op.batch_alter_table('assessment_appeals', schema=None) as batch_op:
        batch_op.drop_index('ix_assessment_appeals_student')
        batch_op.drop_index('ix_assessment_appeals_course_status')
        batch_op.drop_index('ix_assessment_appeals_attempt')

    op.drop_table('assessment_appeals')
