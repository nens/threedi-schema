"""Migration the old friction_type 4 to 2 (MANNING)

Revision ID: 0300
Revises:
Create Date: 2024-03-04 10:06

"""
import sqlalchemy as sa
from sqlalchemy import Boolean, Column, Float, Integer, String
from sqlalchemy import inspect, text
from alembic import op

from sqlalchemy.orm import declarative_base, Session

from typing import Dict, List, Tuple

# revision identifiers, used by Alembic.
revision = "0300"
down_revision = "0220"
branch_labels = None
depends_on = None

Base = declarative_base()

# (source table, destination table)
RENAME_TABLES = [
    ("v2_aggregation_settings", "aggregation_settings"),
    ("v2_groundwater", "groundwater"),
    ("v2_interflow", "interflow"),
    ("v2_numerical_settings", "numerical_settings"),
    ("v2_simple_infiltration", "simple_infiltration"),
    ("v2_vegetation_drag", "vegetation_drag_2d"),
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
            ("infiltration_rate", "infiltration_rate")
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

# Columns set to True if a mapping between use_* and settings table exists
# (boolean column, setting id, setting table)
GLOBAL_SETTINGS_ID_TO_BOOL = [
    ("use_groundwater_storage", "groundwater_settings_id", "groundwater"),
    ("use_interflow", "interflow_settings_id", "interflow"),
    ("use_structure_control", "control_group_id", "v2_control_group"),
    ("use_simple_infiltration", "simple_infiltration_settings_id", "simple_infiltration"),
    ("use_vegetation_drag_2d", "vegetation_drag_settings_id", "vegetation_drag_2d")
]


def rename_tables(table_sets: List[Tuple[str, str]]):
    # no checks for existence are done, this will fail if a source table doesn't exist
    for src_name, dst_name in table_sets:
        op.rename_table(src_name, dst_name)


def rename_columns(table_name: str, columns: List[Tuple[str, str]]):
    # no checks for existence are done, this will fail if table or any source column doesn't exist
    with op.batch_alter_table(table_name) as batch_op:
        for src_name, dst_name in columns:
            batch_op.alter_column(src_name, new_column_name=dst_name)


def make_all_columns_nullable(table_name, id_name: str = 'id'):
    # no checks for existence are done, this will fail if table doesn't exist
    connection = op.get_bind()
    table = sa.Table(table_name, sa.MetaData(), autoload_with=connection)
    with op.batch_alter_table(table_name) as batch_op:
        for column in table.columns:
            if column.name == id_name:
                continue
            batch_op.alter_column(column_name=column.name, nullable=True)


def create_new_tables(table_names: List[str]):
    # no checks for existence are done, this will fail if any table already exists
    for table_name in table_names:
        op.create_table(table_name, sa.Column("id", sa.Integer(), primary_key=True))


def add_columns_to_tables(table_columns: List[Tuple[str, Column]]):
    # no checks for existence are done, this will fail if any column already exists
    for dst_table, col in table_columns:
        with op.batch_alter_table(dst_table) as batch_op:
            batch_op.add_column(col)


def move_values(src_table: str, dst_table: str, columns: List[str]):
    # move values from one table to another
    # no checks for existence are done, this will fail if any table or column doesn't exist
    dst_cols = ', '.join(dst for _, dst in columns)
    src_cols = ', '.join(src for src, _ in columns)
    op.execute(sa.text(f'INSERT INTO {dst_table} ({dst_cols}) SELECT {src_cols} FROM {src_table}'))
    remove_columns_from_table(src_table, [src for src, _ in columns])


def remove_columns_from_table(table_name: str, columns: List[str]):
    # no checks for existence are done, this will fail if any table or column doesn't exist
    with op.batch_alter_table(table_name) as batch_op:
        for column in columns:
            batch_op.drop_column(column)


def set_bool_settings():
    conn = op.get_bind()
    for settings_col, settings_id, settings_table in GLOBAL_SETTINGS_ID_TO_BOOL:
        # set boolean 'use_*' in model_settings if a relationship exists
        op.execute(f"UPDATE model_settings SET {settings_col} = TRUE WHERE {settings_id} IS NOT NULL;")
        op.execute(f"UPDATE model_settings SET {settings_col} = FALSE WHERE {settings_id} IS NULL;")
        # remove all settings rows, exact for the one matching
        op.execute(
            f"DELETE FROM {settings_table} WHERE id NOT IN (SELECT {settings_col} FROM model_settings WHERE {settings_col} IS NOT NULL);")
    with op.batch_alter_table('model_settings') as batch_op:
        for _, settings_id, _ in GLOBAL_SETTINGS_ID_TO_BOOL:
            batch_op.drop_column(settings_id)
    # set use_groundwater_flow
    sql = """
        UPDATE model_settings
        SET use_groundwater_flow = CASE
            WHEN (SELECT groundwater_hydraulic_conductivity FROM groundwater LIMIT 1) IS NOT NULL OR (SELECT groundwater_hydraulic_conductivity_file FROM groundwater LIMIT 1) IS NOT NULL THEN 1
            ELSE 0
        END;
        """
    op.execute(sql)


def correct_dem_paths():
    # remove path - this will not work with nested paths!
    op.execute(f"UPDATE model_settings SET dem_file = SUBSTR(dem_file, INSTR(dem_file, '/') + 1)")
    op.execute(f"UPDATE model_settings SET dem_file = SUBSTR(dem_file, INSTR(dem_file, '\') + 1)")


def upgrade():
    rename_tables(RENAME_TABLES)
    # rename columns in renamed tables
    for table_name, columns in RENAME_COLUMNS.items():
        rename_columns(table_name, columns)
    # make all columns in renamed tables, except id, nullable
    for _, table_name in RENAME_TABLES:
        make_all_columns_nullable(table_name)
    # create new tables
    create_new_tables(COPY_FROM_GLOBAL.keys())
    # add empty columns to tables
    add_columns_to_tables(ADD_COLUMNS)
    # copy data from model_settings to new tables and columns
    for dst_table, columns in COPY_FROM_GLOBAL.items():
        move_values("model_settings", dst_table, columns)

    set_bool_settings()
    correct_dem_paths()

    # TODO: organize this better
    src_tbl = 'model_settings'
    src_col = 'flooding_threshold'
    dst_tbl = 'numerical_settings'
    dst_col = 'flooding_threshold'
    op.execute(f'UPDATE {dst_tbl} SET {dst_col} = (SELECT {src_col} FROM {src_tbl} LIMIT 1)')


def downgrade():
    # Not implemented on purpose
    print("Downgrade back from 0.3xx is not supported")
