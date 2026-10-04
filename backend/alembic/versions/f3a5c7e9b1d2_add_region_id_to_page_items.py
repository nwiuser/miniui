"""Link page items to their containing region

Revision ID: f3a5c7e9b1d2
Revises: c9d0e1f2a3b4

The visual Page Builder lets users drop page items inside regions, but
``apex_page_items`` had no ``region_id`` column, so every saved item came back
as a page-level (unassigned) item and the canvas could never show items nested
in their regions.

This migration adds a nullable ``region_id`` foreign key (``ON DELETE SET
NULL`` so deleting a region orphans its items instead of failing) plus a
lookup index, matching ``Base.metadata``.

Existing rows keep ``region_id = NULL`` and behave exactly as before: form
regions render unassigned items alongside their own.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a5c7e9b1d2'
down_revision: Union[str, None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "apex_page_items",
        sa.Column("region_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_apex_page_items_region_id",
        "apex_page_items",
        "apex_regions",
        ["region_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_apex_page_items_region_id", "apex_page_items", ["region_id"])


def downgrade() -> None:
    op.drop_index("ix_apex_page_items_region_id", table_name="apex_page_items")
    op.drop_constraint("fk_apex_page_items_region_id", "apex_page_items", type_="foreignkey")
    op.drop_column("apex_page_items", "region_id")
