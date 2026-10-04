"""Repair databases that missed d1e2f3a4b5c6 and e2f3a4b5c6d7

Revision ID: c9d0e1f2a3b4
Revises: b3c4d5e6f7a8
Create Date: 2026-10-03 17:00:00.000000

Some databases were stamped at head while the d1e2 (is_public on pages) and
e2f3 (REST data sources) revisions were never applied to them, so the version
table claims they are done. Re-running those revisions is impossible; this
repair applies exactly their DDL, guarded by existence checks, so it is a
no-op on databases that already have them (including fresh databases built
through the normal chain).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    page_columns = {c['name'] for c in inspector.get_columns('apex_pages')}
    if 'is_public' not in page_columns:
        op.add_column('apex_pages', sa.Column('is_public', sa.Boolean(), nullable=True))
        op.execute("UPDATE apex_pages SET is_public = false WHERE is_public IS NULL")

    if not inspector.has_table('apex_rest_data_sources'):
        op.create_table(
            'apex_rest_data_sources',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('application_id', sa.Integer(), sa.ForeignKey('apex_applications.id'), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('url', sa.String(2000), nullable=False),
            sa.Column('method', sa.String(10), nullable=False, server_default='GET'),
            sa.Column('headers', sa.JSON(), nullable=True),
            sa.Column('query_params', sa.JSON(), nullable=True),
            sa.Column('request_body', sa.JSON(), nullable=True),
            sa.Column('response_mapping', sa.JSON(), nullable=True),
            sa.Column('timeout', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
        op.create_index('ix_apex_rest_data_sources_id', 'apex_rest_data_sources', ['id'])
        op.create_index(
            'ix_apex_rest_data_sources_application_id',
            'apex_rest_data_sources',
            ['application_id'],
        )


def downgrade() -> None:
    # Intentionally a no-op: this revision only backfills schema objects that
    # belong to earlier revisions. Dropping them here would break the chained
    # downgrades of d1e2f3a4b5c6/e2f3a4b5c6d7, which own those objects.
    pass
