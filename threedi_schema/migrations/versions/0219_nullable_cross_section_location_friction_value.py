"""rename vegetation columns

Revision ID: 0218
Revises: 0217
Create Date: 2023-12-22 08:33

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0219'
down_revision = '0218'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("v2_cross_section_location") as batch_op:
        batch_op.alter_column("friction_value", nullable=True, type_=sa.TEXT)
