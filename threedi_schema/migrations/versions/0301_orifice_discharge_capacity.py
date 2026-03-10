"""add breach and exchange properties

Revision ID: 0301
Revises: 0300
Create Date: 2026-03-12

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0301"
down_revision = "0300"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("orifice") as batch_op:
        batch_op.add_column(sa.Column("discharge_capacity", sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table("orifice") as batch_op:
        batch_op.drop_column("discharge_capacity")

