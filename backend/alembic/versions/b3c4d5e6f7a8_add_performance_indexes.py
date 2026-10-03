"""Add lookup indexes for the runtime and builder hot paths

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7

PostgreSQL does not index foreign key columns automatically. Every runtime page
request resolves a page by (application_id, page_number) and then loads its
regions, items, processes, computations and validations by page_id; the same
page_id lookups run on submit for validations. Without these indexes each of
those is a sequential scan.

The model declarations were updated in the same commit; this migration brings
existing databases in line with ``Base.metadata``. The ``apex_sessions``
application index is already created by the session migration, so it is not
repeated here.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_INDEXES = [
    ("ix_apex_pages_application_id_page_number", "apex_pages", ["application_id", "page_number"]),
    ("ix_apex_regions_page_id", "apex_regions", ["page_id"]),
    ("ix_apex_page_items_page_id", "apex_page_items", ["page_id"]),
    ("ix_apex_page_processes_page_id", "apex_page_processes", ["page_id"]),
    ("ix_apex_computations_page_id", "apex_computations", ["page_id"]),
    ("ix_apex_validations_page_id", "apex_validations", ["page_id"]),
]


def upgrade() -> None:
    for name, table, columns in _INDEXES:
        op.create_index(name, table, columns)


def downgrade() -> None:
    for name, table, _columns in reversed(_INDEXES):
        op.drop_index(name, table_name=table)