"""Add computations table for page computations

Revision ID: f1a2b3c4d5e6
Revises: e2f3a4b5c6d7
Create Date: 2026-09-29 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The Computation model and its endpoints shipped in phase 5, but no
    # migration ever created apex_computations: a database built from
    # migration history was missing the table entirely.
    op.create_table(
        'apex_computations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('page_id', sa.Integer(), sa.ForeignKey('apex_pages.id'), nullable=False),
        sa.Column('computation_point', sa.String(20), nullable=False),
        sa.Column('computation_type', sa.String(20), nullable=False),
        sa.Column('computation_item', sa.String(255), nullable=False),
        sa.Column('computation_value', sa.Text(), nullable=True),
        sa.Column('computation_condition_type', sa.String(255), nullable=True),
        sa.Column('computation_condition_expression', sa.Text(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_apex_computations_id', 'apex_computations', ['id'])


def downgrade() -> None:
    op.drop_index('ix_apex_computations_id', table_name='apex_computations')
    op.drop_table('apex_computations')
