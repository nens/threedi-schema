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
RENAME_TABLES = [('control_measure_location', 'measure_location'),
                 ('control_measure_map', 'measure_map'), ]


def fix_geometries(tables):
    for table_name in tables:
        op.execute(sa.text(f"SELECT RecoverGeometryColumn('{table_name}', 'geom', 4326, 'POINT', 'XY')"))


def upgrade():
    # remove measure variable from memory_control and table_control
    for table_name in TABLES:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_column('measure_variable')
    # rename column
    with op.batch_alter_table('control_measure_map') as batch_op:
        batch_op.alter_column('control_measure_location_id', new_column_name='measure_location_id')
    # rename tables
    for old_table_name, new_table_name in RENAME_TABLES:
        op.rename_table(old_table_name, new_table_name)
    all_tables = set(list(TABLES) + [new_table_name for _, new_table_name in RENAME_TABLES])
    fix_geometries(all_tables)


def downgrade():
    # undo remove measure variable from memory_control and table_control
    for table_name in TABLES:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(sa.Column("measure_variable", sa.Text, server_default="water_level"))
    # undo rename columns
    with op.batch_alter_table('measure_map') as batch_op:
        batch_op.alter_column('measure_location_id', new_column_name='control_measure_location_id')
    # rename tables
    for old_table_name, new_table_name in RENAME_TABLES:
        op.rename_table(new_table_name, old_table_name)
    all_tables = set(list(TABLES) + [new_table_name for old_table_name, _ in RENAME_TABLES])
    fix_geometries(all_tables)
