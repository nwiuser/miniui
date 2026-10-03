"""Widen apex_page_processes.execution_point to fit its default value

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6

The column was declared VARCHAR(20) but its default, "ON_SUBMIT_BEFORE_COMPUTATION",
is 30 characters. SQLite does not enforce the length, so the mismatch only
surfaced on PostgreSQL, where any insert relying on the default raised
StringDataRightTruncation.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('apex_page_processes', schema=None) as batch_op:
        batch_op.alter_column('execution_point',
                   existing_type=sa.VARCHAR(length=20),
                   type_=sa.VARCHAR(length=50),
                   existing_nullable=True)


def downgrade() -> None:
    # Any row already holding the default cannot fit back into VARCHAR(20), so
    # truncate first to keep the downgrade from failing on data it created.
    op.execute(
        "UPDATE apex_page_processes "
        "SET execution_point = 'ON_SUBMIT_BEFORE' "
        "WHERE execution_point = 'ON_SUBMIT_BEFORE_COMPUTATION'"
    )
    with op.batch_alter_table('apex_page_processes', schema=None) as batch_op:
        batch_op.alter_column('execution_point',
                   existing_type=sa.VARCHAR(length=50),
                   type_=sa.VARCHAR(length=20),
                   existing_nullable=True)
