"""Migration the old friction_type 4 to 2 (MANNING)

Revision ID: 0300
Revises:
Create Date: 2024-03-04 10:06

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0300"
down_revision = "0220"
branch_labels = None
depends_on = None

RENAME_TABLES = [
    ("v2_aggregation_settings", "aggregation_settings"),
    ('v2_groundwater', 'groundwater'),
]

RENAME_FIELDS = {"aggregation_settings":
                     [("timestep", "interval")],
                 "groundwater":
                     [
                         ("groundwater_hydro_connectivity", "groundwater_hydraulic_conductivity"),
                         ("groundwater_hydro_connectivity_file", "groundwater_hydraulic_conductivity_file"),
                         ("groundwater_hydro_connectivity_type", "groundwater_hydraulic_conductivity_aggregation"),
                         ("groundwater_impervious_layer_level_type", "groundwater_impervious_layer_level_aggregation"),
                         ("infiltration_decay_period_type", "infiltration_decay_period_aggregation"),
                         ("initial_infiltration_rate_type", "initial_infiltration_rate_aggregation"),
                         ("phreatic_storage_capacity_type", "phreatic_storage_capacity_aggregation"),
                     ]
                 }




def upgrade():
    for old_name, new_name in RENAME_TABLES:
        op.rename_table(old_name, new_name)
    for table, fields in RENAME_FIELDS.items():
        with op.batch_alter_table(table) as batch_op:
            for old_name, new_name in fields:
                batch_op.alter_column(old_name, new_column_name=new_name)


def downgrade():
    for table, fields in RENAME_FIELDS.items():
        with op.batch_alter_table(table) as batch_op:
            for old_name, new_name in fields:
                batch_op.alter_column(new_name, new_column_name=old_name)
    for old_name, new_name in RENAME_TABLES:
        op.rename_table(new_name, old_name)
