"""Upgrade settings in schema

Revision ID: 0227
Revises:
Create Date: 2024-09-24 15:10

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0227"
down_revision = "0226"
branch_labels = None
depends_on = None

TABLES = ['memory_control', 'table_control']


def upgrade():
    for table_name in TABLES:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_column('measure_variable')
        op.execute(sa.text(f"SELECT RecoverGeometryColumn('{table_name}', 'geom', 4326, 'POINT', 'XY')"))

def downgrade():
    for table_name in TABLES:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(sa.Column("measure_variable", sa.Text, server_default="water_level"))
        op.execute(sa.text(f"SELECT RecoverGeometryColumn('{table_name}', 'geom', 4326, 'POINT', 'XY')"))
