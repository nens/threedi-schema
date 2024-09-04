import csv
import shutil
import sqlite3
from pathlib import Path

import pytest
from geoalchemy2 import Geometry
from sqlalchemy import inspect

from threedi_schema import ModelSchema, ThreediDatabase

# All these tests are marked with the marker `migrations`.
# Individual tests and test classes are additionally marked with a marker relating
# to the specific migration that is being tested, e.g. `migration_300`.
# To run tests for all migrations: pytest -m migrations
# To run tests for a specific migration: pytest -m migration_xyz
# To exclude migration tests: pytest -m "no migrations"

pytestmark = pytest.mark.migrations

data_dir = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sqlite_path():
    return data_dir.joinpath("v2_bergermeer_221.sqlite")


@pytest.fixture(scope="session")
def schema_upgraded(tmp_path_factory, sqlite_path):
    tmp_sqlite = tmp_path_factory.mktemp("custom_dir").joinpath(sqlite_path.name)
    shutil.copy(sqlite_path, tmp_sqlite)
    schema = ModelSchema(ThreediDatabase(tmp_sqlite))
    schema.upgrade(backup=False)
    return schema


@pytest.fixture(scope="session")
def schema_ref(tmp_path_factory, sqlite_path):
    # Last pre-upgrade version
    tmp_sqlite = tmp_path_factory.mktemp("custom_dir").joinpath(sqlite_path.name)
    shutil.copy(sqlite_path, tmp_sqlite)
    return ModelSchema(ThreediDatabase(tmp_sqlite))


def get_sql_tables(cursor):
    return [item[0] for item in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]


def get_cursor_for_schema(schema):
    return sqlite3.connect(schema.db.path).cursor()


def get_columns_from_schema(schema, table_name):
    inspector = inspect(schema.db.get_engine())
    columns = inspector.get_columns(table_name)
    return {column['name']: (str(column['type']).lower(), column['nullable']) for column in columns
            if not 'geom' in column['name']}


def get_columns_from_sqlite(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    col_map = {}
    for c in cursor.fetchall():
        if 'geom' in c[1]:
            continue
        type_str = c[2].lower() if c[2] != 'bool' else 'boolean'
        col_map[c[1]] = (type_str, not c[3])
    return col_map


def get_values_from_sqlite(cursor, table_name, column_name):
    cursor.execute(f"SELECT {column_name} FROM {table_name}")
    return cursor.fetchall()


@pytest.mark.parametrize("sqlite_file",
                         ["v2_bergermeer_221.sqlite",
                          "staging-test-0d1d2d-simple-infiltration.sqlite",
                          "staging-test-0d1d2d-simple-infiltration_surface.sqlite"])
def test_upgrade_success(sqlite_file, tmp_path_factory):
    tmp_sqlite = tmp_path_factory.mktemp("custom_dir").joinpath(sqlite_file)
    shutil.copy(data_dir.joinpath(sqlite_file), tmp_sqlite)
    schema = ModelSchema(ThreediDatabase(tmp_sqlite))
    # Test if running upgrade doesn't run into any exceptions
    try:
        schema.upgrade(backup=False)
    except Exception:
        pytest.fail(f"Failed to upgrade {sqlite_file}")


class TestMigration224:
    pytestmark = pytest.mark.migration_224
    removed_tables = set(['v2_control', 'v2_control_delta', 'v2_control_group',
                          'v2_control_measure_group', 'v2_control_measure_map',
                          'v2_control_pid', 'v2_control_timed',
                          'v2_control_memory', 'v2_control_table'])
    added_tables = set(['memory_control', 'table_control', 'control_measure_location', 'control_measure_map'])

    def test_tables(self, schema_ref, schema_upgraded):
        # Test whether the added tables are present
        # and whether the removed tables are not present*
        tables_new = set(get_sql_tables(get_cursor_for_schema(schema_upgraded)))
        assert self.added_tables.issubset(tables_new)
        assert self.removed_tables.isdisjoint(tables_new)

    def test_columns_added_tables(self, schema_upgraded):
        # Note that only the added tables are touched.
        # So this check covers both added and removed columns.
        cursor = get_cursor_for_schema(schema_upgraded)
        for table in self.added_tables:
            cols_sqlite = get_columns_from_sqlite(cursor, table)
            cols_schema = get_columns_from_schema(schema_upgraded, table)
            assert cols_sqlite == cols_schema


class TestMigration223:
    pytestmark = pytest.mark.migration_223
    removed_tables = set(['v2_surface', 'v2_surface_parameters', 'v2_surface_map',
                          'v2_impervious_surface', 'v2_impervious_surface_map'])
    added_tables = set(['surface', 'surface_map', 'surface_parameters', 'tags',
                        'dry_weather_flow', 'dry_weather_flow_map', 'dry_weather_flow_distribution'])

    def test_tables(self, schema_ref, schema_upgraded):
        # Test whether the added tables are present
        # and whether the removed tables are not present*
        tables_new = set(get_sql_tables(get_cursor_for_schema(schema_upgraded)))
        assert self.added_tables.issubset(tables_new)
        assert self.removed_tables.isdisjoint(tables_new)

    def test_columns_added_tables(self, schema_upgraded):
        # Note that only the added tables are touched.
        # So this check covers both added and removed columns.
        cursor = get_cursor_for_schema(schema_upgraded)
        for table in self.added_tables:
            cols_sqlite = get_columns_from_sqlite(cursor, table)
            cols_schema = get_columns_from_schema(schema_upgraded, table)
            assert cols_sqlite == cols_schema


class TestMigration222:
    pytestmark = pytest.mark.migration_222

    with open(data_dir.joinpath('migration_222.csv'), 'r') as file:
        # src_table, src_column, dst_table, dst_column
        migration_map = [[row[0], row[1], row[2], row[3]] for row in csv.reader(file)]
    removed_tables = set([row[0] for row in migration_map])
    added_tables = set([row[2] for row in migration_map])
    bool_settings_id = [
        ("use_groundwater_storage", "groundwater_settings_id", "groundwater"),
        ("use_interflow", "interflow_settings_id", "interflow"),
        ("use_structure_control", "control_group_id", "v2_control_group"),
        ("use_simple_infiltration", "simple_infiltration_settings_id", "simple_infiltration"),
        ("use_vegetation_drag_2d", "vegetation_drag_settings_id", "vegetation_drag_2d")
    ]
    bool_settings_exist = [
        ("use_interception", "interception")
    ]
    single_row_tables = ["model_settings",
                         "simulation_template_settings",
                         "time_step_settings",
                         "numerical_settings",
                         "physical_settings",
                         "initial_conditions",
                         "interception"]

    def test_tables(self, schema_ref, schema_upgraded):
        # Test whether the added tables are present
        # and whether the removed tables are not present*
        tables_new = set(get_sql_tables(get_cursor_for_schema(schema_upgraded)))
        assert self.added_tables.issubset(tables_new)
        assert self.removed_tables.isdisjoint(tables_new)

    def test_columns_added_tables(self, schema_upgraded):
        # Note that only the added tables are touched.
        # So this check covers both added and removed columns.
        cursor = get_cursor_for_schema(schema_upgraded)
        for table in self.added_tables:
            cols_sqlite = get_columns_from_sqlite(cursor, table)
            cols_schema = get_columns_from_schema(schema_upgraded, table)
            assert cols_sqlite == cols_schema

    def test_copied_values(self, schema_ref, schema_upgraded):
        cursor_ref = get_cursor_for_schema(schema_ref)
        cursor_new = get_cursor_for_schema(schema_upgraded)
        for src_tbl, src_col, dst_tbl, dst_col in self.migration_map:
            # use settings are tested seperately
            if f'use_{dst_tbl}' in get_columns_from_schema(schema_upgraded, 'model_settings'):
                continue
            if dst_col.startswith('use_'):
                continue
            values_ref = get_values_from_sqlite(cursor_ref, src_tbl, src_col)
            values_new = get_values_from_sqlite(cursor_new, dst_tbl, dst_col)
            # dem_file should be different
            if src_col == 'dem_file':
                path_ref = Path(values_ref[0][0])
                assert str(path_ref.name) == values_new[0][0]
            # flow_variable should be different
            elif src_col == 'flow_variable':
                continue
            else:
                assert values_ref == values_new

    @pytest.mark.skip(reason="This test is broken by upgrade to 224")
    def test_boolean_setting_id(self, schema_ref, schema_upgraded):
        cursor_ref = get_cursor_for_schema(schema_ref)
        cursor_new = get_cursor_for_schema(schema_upgraded)
        for col, id, table in self.bool_settings_id:
            id_val = get_values_from_sqlite(cursor_ref, 'v2_global_settings', id)[0][0]
            use_val = get_values_from_sqlite(cursor_new, 'model_settings', col)[0][0]
            settings = get_values_from_sqlite(cursor_new, table, 'id')
            # check if `use_` columns are set properly
            if id_val is None:
                assert (use_val is None or use_val == 0)
            else:
                assert use_val == 1
            # check if matching settings tables consist of 1 (use = True) or 0 (use = False) rows
            if use_val == 0 or use_val is None:
                assert settings == []
            if use_val == 1:
                assert len(settings) == 1

    def test_boolean_setting_exist(self, schema_upgraded):
        cursor_new = get_cursor_for_schema(schema_upgraded)
        for col, table in self.bool_settings_exist:
            use_val = get_values_from_sqlite(cursor_new, 'model_settings', col)[0][0]
            settings = get_values_from_sqlite(cursor_new, table, 'id')
            if use_val == 0 or use_val is None:
                assert settings == []
            if use_val == 1:
                assert len(settings) == 1

    def test_column_length(self, schema_upgraded):
        cursor_new = get_cursor_for_schema(schema_upgraded)
        for table in self.single_row_tables:
            settings = get_values_from_sqlite(cursor_new, table, 'id')
            assert len(settings) == 1
