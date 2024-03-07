"""Migration the old friction_type 4 to 2 (MANNING)

Revision ID: 0300
Revises:
Create Date: 2024-03-04 10:06

"""
import sqlalchemy as sa
from sqlalchemy import Boolean, Column, Float, Integer, String
from alembic import op

from sqlalchemy.orm import declarative_base, Session

# revision identifiers, used by Alembic.
revision = "0300"
down_revision = "0220"
branch_labels = None
depends_on = None

Base = declarative_base()


RENAME_TABLES = [
    ("v2_aggregation_settings", "aggregation_settings"),
    ("v2_groundwater", "groundwater"),
    ("v2_interflow", "interflow"),
    ("v2_numerical_settings", "numerical_settings"),
    ("v2_simple_infiltration", "simple_infiltration"),
    ("v2_vegetation_drag", "vegetation_drag"),
    ("v2_global_settings", "model_settings")
]

# (old name, new name)
RENAME_COLUMNS = {
    "aggregation_settings":
        [
            ("timestep", "interval"),
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
        ],
    "model_settings":
        [
            ("dist_calc_points", "calculation_point_distance_1d"),
            ("frict_avg", "friction_averaging"),
            ("frict_coef", "friction_coefficient"),
            ("frict_coef_file", "friction_coefficient_file"),
            ("frict_type", "friction_type"),
            ("manhole_storage_area", "manhole_aboveground_storage_area"),
            ("grid_space", "minimum_cell_size"),
            ("kmax", "nr_grid_levels"),
            ("table_step_size", "minimum_table_step_size"),
        ],
}

FORCE_NOT_NULLABLE = {
    "aggregation_settings": "all",
    "groundwater": "all",
    "interflow": "all",
    "numerical_settings": "all",
    "simple_infiltration": "all",
    "vegetation_drag": "all",
    "model_settings": "all",
}

ADD_COLUMNS = [
    ("numerical_settings", Column("flooding_threshold", Float)),
    ("initial_conditions", Column("initial_groundwater_level", Float)),
    ("initial_conditions", Column("initial_groundwater_level_aggregation", Integer)),
    ("initial_conditions", Column("initial_groundwater_level_file", String)),
    ("initial_conditions", Column("initial_water_level", Float)),
    ("initial_conditions", Column("initial_water_level_aggregation", Integer)),
    ("initial_conditions", Column("initial_water_level_file", String)),
    ("interception", Column("interception", Float)),
    ("interception", Column("interception_file", String)),
    ("physical_settings", Column("use_advection_1d", Integer)),
    ("physical_settings", Column("use_advection_2d", Integer)),
    ("simulation_template_settings", Column("name", String)),
    ("time_step_settings", Column("max_time_step", Float)),
    ("time_step_settings", Column("min_time_step", Float)),
    ("time_step_settings", Column("output_time_step", Float)),
    ("time_step_settings", Column("time_step", Float)),
    ("time_step_settings", Column("use_time_step_stretch", Boolean)),
    ("model_settings", Column("use_groundwater_flow", Boolean)),
    ("model_settings", Column("use_groundwater_storage", Boolean)),
    ("model_settings", Column("use_structure_control", Boolean)),
    ("model_settings", Column("use_simple_infiltration", Boolean)),
    ("model_settings", Column("use_vegetation_drag_2d", Boolean)),
    ("model_settings", Column("use_interflow", Boolean)),
]

COPY_FROM_GLOBAL = {
    "simulation_template_settings": [
        ("name", "name"),
    ],
    "time_step_settings": [
        ("maximum_sim_time_step", "max_time_step"),
        ("minimum_sim_time_step", "min_time_step"),
        ("output_time_step", "output_time_step"),
        ("sim_time_step", "time_step"),
        ("timestep_plus", "use_time_step_stretch"),
    ],
    "initial_conditions": [
        ("initial_groundwater_level", "initial_groundwater_level"),
        ("initial_groundwater_level_type", "initial_groundwater_level_aggregation"),
        ("initial_groundwater_level_file", "initial_groundwater_level_file"),
        ("initial_waterlevel", "initial_water_level"),
        ("water_level_ini_type", "initial_water_level_aggregation"),
        ("initial_waterlevel_file", "initial_water_level_file"),
    ],
    "physical_settings": [
        ("advection_1d", "use_advection_1d"),
        ("advection_2d", "use_advection_2d"),
    ],
    "interception": [
        ("interception_global", "interception"),
        ("interception_file", "interception_file"),
    ],
}

GLOBAL_SETTINGS_ID_TO_BOOL = [
    ("use_groundwater_storage", "groundwater"),
    ("use_interflow", "interflow"),
    ("use_structure_control", "v2_control_group"),
    ("use_simple_infiltration", "simple_infiltration"),
    ("use_vegetation_drag_2d", "vegetation_drag")
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
    for table_name in COPY_FROM_GLOBAL.keys():
        op.create_table(table_name, sa.Column("id", sa.Integer(), primary_key=True))

    # Add columns
    for dst_table, col in ADD_COLUMNS:
        op.add_column(dst_table, col)

    # Move columns
    src_table = "model_settings"
    for dst_table, columns in COPY_FROM_GLOBAL.items():
        dst_cols = ', '.join(dst for _, dst in columns)
        src_cols = ', '.join(src for src, _ in columns)
        op.execute(sa.text(f'INSERT INTO {dst_table} ({dst_cols}) SELECT {src_cols} FROM {src_table}'))
        # Remove columns specified in src_columns from src_table
        # for src, _ in columns:
        #     op.execute(sa.text(f'ALTER TABLE {src_table} DROP COLUMN {src};'))


    # TODO use_groundwater_flow: True if either groundwater.hydro_connectivity or groundwater.hydro_connectivity_file is NOT NULL
    session = Session(bind=op.get_bind())
    for settings_col, settings_table in GLOBAL_SETTINGS_ID_TO_BOOL:
        op.execute(f"UPDATE model_settings SET {settings_col} = 1 WHERE groundwater_settings_id IS NOT NULL;")
        op.execute(
            f"DELETE FROM {settings_table} WHERE id NOT IN (SELECT {settings_col} FROM model_settings WHERE {settings_col} IS NOT NULL);")
        # TODO: drop columns
        # op.execute(sa.text(f'ALTER TABLE model_settings DROP COLUMN {settings_col};'))

    # Make columns of the renamed tables, except for id, nullable
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    for table_name, columns in FORCE_NOT_NULLABLE.items():
        if columns == "all":
            _columns = [column['name'] for column in inspector.get_columns(table_name) if column['name'] == 'id']
        else:
            _columns = columns
        with op.batch_alter_table(table) as batch_op:
            for column in _columns:
                batch_op.alter_column(column_name=column, nullable=True)


def downgrade():
    # TODO: implement
    # Do all steps in the reverse order as upgrade
    # Revert move columns: move columns back to source table
    # Revert add columns: drop columns
    # Revert add tables: drop tables
    # Revert rename columns: restore original name
    for table, columns in RENAME_COLUMNS.items():
        with op.batch_alter_table(table) as batch_op:
            for old_name, new_name in columns:
                batch_op.alter_column(new_name, new_column_name=old_name)

    # Revert rename tables: restore original name
    for old_name, new_name in RENAME_TABLES:
        op.rename_table(new_name, old_name)
