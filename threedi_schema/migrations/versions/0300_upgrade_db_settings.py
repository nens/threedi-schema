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
    ["v2_aggregation_settings", "aggregation_settings"],
    ["v2_groundwater", "groundwater"],
    ["v2_interflow", "interflow"],
    ["v2_numerical_settings", "numerical_settings"],
    ["v2_simple_infiltration", "simple_infiltration"],
    ["v2_vegetation_drag", "vegetation_drag"],
]

RENAME_COLUMNS = {"aggregation_settings":
                     [
                         ("timestep", "interval")
                     ],
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
                     ],
                 "simple_infiltration":
                     [
                         ("max_infiltration_capacity", "max_infiltration_volume"),
                         ("max_infiltration_capacity_file", "max_infiltration_volume_file"),
                     ]
                 }

ADD_TABLES = ["initial_conditions"]

ADD_COLUMNS = [
    ["numerical_settings", sa.Column("flooding_threshold", sa.Float())],
    ["initial_conditions", sa.Column("initial_groundwater_level", sa.Float())]
]

MOVE_COLUMNS = [
    ["v2_global_settings", "flooding_threshold", "numerical_settings", "flooding_threshold"],
    ["v2_global_settings", "initial_groundwater_level", "initial_conditions", "initial_groundwater_level"]
]


def upgrade():
    # Rename tables
    for old_name, new_name in RENAME_TABLES:
        op.rename_table(old_name, new_name)

    # Rename columns
    for table, columns in RENAME_COLUMNS.items():
        with op.batch_alter_table(table) as batch_op:
            for old_name, new_name in columns:
                batch_op.alter_column(old_name, new_column_name=new_name)

    # Add tables
    for table_name in ADD_TABLES:
        op.create_table(table_name, sa.Column("id", sa.Integer(), primary_key=True))

    # Add columns
    for dst_table, col in ADD_COLUMNS:
        op.add_column(dst_table, col)

    # Move columns
    for src_table, src_col, dst_table, dst_col in MOVE_COLUMNS:
        op.execute(sa.text(f'INSERT INTO {dst_table} ({dst_col}) SELECT {src_col} FROM {src_table}'))
        # TODO: maybe drop copied column from source

def downgrade():
    for table, columns in RENAME_COLUMNS.items():
        with op.batch_alter_table(table) as batch_op:
            for old_name, new_name in columns:
                batch_op.alter_column(new_name, new_column_name=old_name)
    for old_name, new_name in RENAME_TABLES:
        op.rename_table(new_name, old_name)
