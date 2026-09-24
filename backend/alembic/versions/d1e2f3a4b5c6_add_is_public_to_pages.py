"""Add is_public flag to pages for public/protected visibility

Revision ID: d1e2f3a4b5c6
Revises: 9c8d7f012c3a
Create Date: 2026-09-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = '9c8d7f012c3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('apex_pages', sa.Column('is_public', sa.Boolean(), nullable=True))
    op.execute("UPDATE apex_pages SET is_public = false WHERE is_public IS NULL")


def downgrade() -> None:
    op.drop_column('apex_pages', 'is_public')