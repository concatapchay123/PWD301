"""0002_fix_critical_integrity_defects

Revision ID: e8f9a1b2c3d4
Revises: c1d237fd6bf9
Create Date: 2026-09-09 16:15:00.000000

Fixes 6 critical integrity and concurrency defects:
1. Break circular FKs by removing current_revision_id / current_version_id and adding is_current with filtered unique index.
2. Add lease_epoch, is_detail_purged, and detail_purged_at to assessment_attempts for autosave fencing and skeleton tombstone purging.
3. Relax lesson unique position constraint to active/published status only and add change_request_id foreign key for relational staging.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = 'e8f9a1b2c3d4'
down_revision = 'c1d237fd6bf9'
branch_labels = None
depends_on = None


def upgrade():
    # 1. questions: drop circular FK and current_revision_id column
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_questions_current_revision_id', type_='foreignkey')
        batch_op.drop_column('current_revision_id')

    # 2. question_revisions: add is_current column and filtered unique index
    with op.batch_alter_table('question_revisions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_current', sa.Boolean(), server_default=sa.text('0'), nullable=False))
        batch_op.create_index(
            'uq_question_revisions_current',
            ['question_id'],
            unique=True,
            mssql_where=sa.text('is_current = 1'),
            sqlite_where=sa.text('is_current = 1'),
        )

    # 3. file_assets: drop check constraint, circular FK, and current_revision_id column
    with op.batch_alter_table('file_assets', schema=None) as batch_op:
        batch_op.drop_constraint('ck_file_assets_3', type_='check')
        batch_op.drop_constraint('fk_file_assets_current_revision_id', type_='foreignkey')
        batch_op.drop_column('current_revision_id')

    # 4. file_revisions: add is_current column and filtered unique index
    with op.batch_alter_table('file_revisions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_current', sa.Boolean(), server_default=sa.text('0'), nullable=False))
        batch_op.create_index(
            'uq_file_revisions_current',
            ['file_asset_id'],
            unique=True,
            mssql_where=sa.text('is_current = 1'),
            sqlite_where=sa.text('is_current = 1'),
        )

    # 5. knowledge_documents: drop circular FK and current_version_id column
    with op.batch_alter_table('knowledge_documents', schema=None) as batch_op:
        batch_op.drop_constraint('fk_knowledge_documents_current_version_id', type_='foreignkey')
        batch_op.drop_column('current_version_id')

    # 6. knowledge_versions: add is_current column and filtered unique index
    with op.batch_alter_table('knowledge_versions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_current', sa.Boolean(), server_default=sa.text('0'), nullable=False))
        batch_op.create_index(
            'uq_knowledge_versions_current',
            ['knowledge_document_id'],
            unique=True,
            mssql_where=sa.text('is_current = 1'),
            sqlite_where=sa.text('is_current = 1'),
        )

    # 7. assessment_attempts: add lease_epoch, is_detail_purged, detail_purged_at
    with op.batch_alter_table('assessment_attempts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lease_epoch', sa.Integer(), server_default=sa.text('1'), nullable=False))
        batch_op.add_column(sa.Column('is_detail_purged', sa.Boolean(), server_default=sa.text('0'), nullable=False))
        batch_op.add_column(sa.Column('detail_purged_at', sa.DateTime().with_variant(mssql.DATETIME2(precision=3), 'mssql'), nullable=True))

    # 8. lessons: add change_request_id, relax unique position to active/published, update ck_lessons_5
    with op.batch_alter_table('lessons', schema=None) as batch_op:
        batch_op.add_column(sa.Column('change_request_id', sa.BigInteger(), nullable=True))
        batch_op.create_foreign_key('fk_lessons_change_request_id', 'course_change_requests', ['change_request_id'], ['id'], ondelete='SET NULL')
        batch_op.drop_constraint('uq_lessons_course_id_position_2', type_='unique')
        batch_op.create_index(
            'uq_lessons_course_position_active',
            ['course_id', 'position'],
            unique=True,
            mssql_where=sa.text("status IN ('ACTIVE','PUBLISHED')"),
            sqlite_where=sa.text("status IN ('ACTIVE','PUBLISHED')"),
        )
        batch_op.drop_constraint('ck_lessons_5', type_='check')
        batch_op.create_check_constraint('ck_lessons_5', "status IN ('DRAFT','ACTIVE','PUBLISHED','PENDING_APPROVAL','ARCHIVED','HIDDEN','TRASH','HISTORICAL')")


def downgrade():
    # 8. lessons: restore ck_lessons_5, restore unique constraint, drop index, drop FK and column
    with op.batch_alter_table('lessons', schema=None) as batch_op:
        batch_op.drop_constraint('ck_lessons_5', type_='check')
        batch_op.create_check_constraint('ck_lessons_5', "status IN ('DRAFT','PUBLISHED','HIDDEN','TRASH','HISTORICAL')")
        batch_op.drop_index('uq_lessons_course_position_active')
        batch_op.create_unique_constraint('uq_lessons_course_id_position_2', ['course_id', 'position'])
        batch_op.drop_constraint('fk_lessons_change_request_id', type_='foreignkey')
        batch_op.drop_column('change_request_id')

    # 7. assessment_attempts: drop added columns
    with op.batch_alter_table('assessment_attempts', schema=None) as batch_op:
        batch_op.drop_column('detail_purged_at')
        batch_op.drop_column('is_detail_purged')
        batch_op.drop_column('lease_epoch')

    # 6. knowledge_versions: drop index and is_current
    with op.batch_alter_table('knowledge_versions', schema=None) as batch_op:
        batch_op.drop_index('uq_knowledge_versions_current')
        batch_op.drop_column('is_current')

    # 5. knowledge_documents: restore current_version_id and FK
    with op.batch_alter_table('knowledge_documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_version_id', sa.BigInteger(), nullable=True))
        batch_op.create_foreign_key('fk_knowledge_documents_current_version_id', 'knowledge_versions', ['current_version_id'], ['id'], ondelete='SET NULL')

    # 4. file_revisions: drop index and is_current
    with op.batch_alter_table('file_revisions', schema=None) as batch_op:
        batch_op.drop_index('uq_file_revisions_current')
        batch_op.drop_column('is_current')

    # 3. file_assets: restore current_revision_id, FK, and check constraint
    with op.batch_alter_table('file_assets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_revision_id', sa.BigInteger(), nullable=True))
        batch_op.create_foreign_key('fk_file_assets_current_revision_id', 'file_revisions', ['current_revision_id'], ['id'], ondelete='SET NULL')
        batch_op.create_check_constraint('ck_file_assets_3', "status <> 'ACTIVE' OR current_revision_id IS NOT NULL")

    # 2. question_revisions: drop index and is_current
    with op.batch_alter_table('question_revisions', schema=None) as batch_op:
        batch_op.drop_index('uq_question_revisions_current')
        batch_op.drop_column('is_current')

    # 1. questions: restore current_revision_id and FK
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_revision_id', sa.BigInteger(), nullable=True))
        batch_op.create_foreign_key('fk_questions_current_revision_id', 'question_revisions', ['current_revision_id'], ['id'], ondelete='SET NULL')
