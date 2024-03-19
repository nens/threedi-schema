import csv
import shutil
import sqlite3
from pathlib import Path

import pytest
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
def schema_300(tmp_path_factory):
    sqlite_path = data_dir.joinpath("v2_bergermeer_220.gpkg")
    tmp_sqlite = tmp_path_factory.mktemp("custom_dir").joinpath(sqlite_path.name)
    shutil.copy(sqlite_path, tmp_sqlite)
    schema = ModelSchema(ThreediDatabase(tmp_sqlite))
    schema.upgrade(backup=False)
    return schema


@pytest.fixture(scope="session")
def schema_220(tmp_path_factory):
    sqlite_path = data_dir.joinpath("v2_bergermeer_220.gpkg")
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
    return {c['name']: (str(c['type']), c['nullable']) for c in columns}


def get_columns_from_sqlite(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return {c[1]: (c[2], not c[3]) for c in columns}


def get_values_from_sqlite(cursor, table_name, column_name):
    cursor.execute(f"SELECT {column_name} FROM {table_name}")
    return cursor.fetchall()


class TestMigration300:
    pytestmark = pytest.mark.migration_300

    with open(data_dir.joinpath('migration_300.csv'), 'r') as file:
        # src_table, src_column, dst_table, dst_column
        migration_map = [[row[0], row[1], row[2], row[3]] for row in csv.reader(file)]
    removed_tables = list(set([row[0] for row in migration_map]))
    added_tables = list(set([row[2] for row in migration_map]))
    bool_settings = [
        ("use_groundwater_storage", "groundwater_settings_id", "groundwater"),
        ("use_interflow", "interflow_settings_id", "interflow"),
        ("use_structure_control", "control_group_id", "v2_control_group"),
        ("use_simple_infiltration", "simple_infiltration_settings_id", "simple_infiltration"),
        ("use_vegetation_drag_2d", "vegetation_drag_settings_id", "vegetation_drag_2d")
    ]

    def test_tables(self, schema_220, schema_300):
        # Test whether renaming removed the correct columns,
        # and whether adding/renaming added the correct columns.
        tables_220 = set(get_sql_tables(get_cursor_for_schema(schema_220)))
        tables_300 = set(get_sql_tables(get_cursor_for_schema(schema_300)))
        assert sorted(self.removed_tables) == sorted(list(tables_220 - tables_300))
        assert sorted(self.added_tables) == sorted(list(tables_300 - tables_220))

    def test_columns_added_tables(self, schema_300):
        # Note that only the added tables are touched.
        # So this check covers both added and removed columns.
        cursor = get_cursor_for_schema(schema_300)
        for table in self.added_tables:
            cols_sqlite = get_columns_from_sqlite(cursor, table)
            cols_schema = get_columns_from_schema(schema_300, table)
            assert cols_sqlite == cols_schema

    def test_copied_values(self, schema_220, schema_300):
        cursor_220 = get_cursor_for_schema(schema_220)
        cursor_300 = get_cursor_for_schema(schema_300)
        for src_tbl, src_col, dst_tbl, dst_col in self.migration_map:
            # use settings are tested seperately
            if f'use_{dst_tbl}' in get_columns_from_schema(schema_300, 'model_settings'):
                continue
            values_220 = get_values_from_sqlite(cursor_220, src_tbl, src_col)
            values_300 = get_values_from_sqlite(cursor_300, dst_tbl, dst_col)
            # dem_file should be different
            if src_col == 'dem_file':
                path_220 = Path(values_220[0][0])
                assert str(path_220.name) == values_300[0][0]
            else:
                assert values_220 == values_300

    def test_boolean_setting(self, schema_220, schema_300):
        cursor_220 = get_cursor_for_schema(schema_220)
        cursor_300 = get_cursor_for_schema(schema_300)
        for col, id, table in self.bool_settings:
            id_val = get_values_from_sqlite(cursor_220, 'v2_global_settings', id)[0][0]
            use_val = get_values_from_sqlite(cursor_300, 'model_settings', col)[0][0]
            settings = get_values_from_sqlite(cursor_300, table, 'id')
            # check if `use_` columns are set properly
            if id_val is None:
                assert (use_val is None or use_val == 0)
            if id_val == 1:
                assert use_val == 1
            # check if matching settings tables consist of 1 (use = True) or 0 (use = False) rows
            if use_val == 0 or use_val is None:
                print(col, id, table)
                print(use_val, id_val)
                assert settings == []
            if use_val == 1:
                assert len(settings) == 1


