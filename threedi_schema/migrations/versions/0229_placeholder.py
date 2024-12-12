"""Placeholder

Revision ID: 0229
Revises:
Create Date: 2024-11-12 12:30

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0229"
down_revision = "0228"
branch_labels = None
depends_on = None

def clean_by_type(type: str):
    connection = op.get_bind()
    items = [item[0] for item in connection.execute(
        sa.text(f"SELECT tbl_name FROM sqlite_master WHERE type='{type}' AND tbl_name LIKE '%v2%';")).fetchall()]
    for item in items:
        op.execute(f"DROP {type} IF EXISTS {item};")


def upgrade():
    clean_by_type("trigger")

def downgrade():
    pass