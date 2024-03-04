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
    ("v2_groundwater", "groundwater"),
    ("v2_interflow", "interflow"),
    ("v2_numerical_settings", "numerical_settings")
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
                     ],
                 "numerical_settings":
                     [
                         ("frict_shallow_water_correction", "friction_shallow_water_depth_correction"),
                         ("thin_water_layer_definition", "limiter_slope_thin_water_layer"),
                         ("limiter_grad_1d", "limiter_waterlevel_gradient_1d"),
                         ("limiter_grad_2d", "limiter_waterlevel_gradient_2d"),
                         ("max_degree", "max_degree_gauss_seidel"),
                         ("max_nonlin_iterations", "max_non_linear_newton_iterations"),
                         ("minimum_friction_velocity", "min_friction_velocity"),
                         ("minimum_surface_area", "min_surface_area"),
                         ("integration_method", "time_integration_method"),
                         ("use_of_nested_newton", "use_nested_newton"),
                         ("precon_cg", "use_preconditioner_cg"),
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
