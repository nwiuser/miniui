"""Add REST data sources table for external API integration

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-09-25 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    op.create_index('ix_apex_rest_data_sources_application_id', 'apex_rest_data_sources', ['application_id'])


def downgrade() -> None:
    op.drop_index('ix_apex_rest_data_sources_application_id', table_name='apex_rest_data_sources')
    op.drop_index('ix_apex_rest_data_sources_id', table_name='apex_rest_data_sources')
    op.drop_table('apex_rest_data_sources')