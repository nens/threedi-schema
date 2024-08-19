"""Migrate 1d and 2d lateral and boundary condition tables to new schema

Revision ID: 0225
Revises:
Create Date: 2024-08-05 11:22

"""
from pathlib import Path
from typing import Dict, List, Tuple

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import load_spatialite
from sqlalchemy import Boolean, Column, Integer, Text
from sqlalchemy.event import listen
from sqlalchemy.orm import declarative_base

from threedi_schema.domain.custom_types import Geometry

# revision identifiers, used by Alembic.
revision = "0225"
down_revision = "0224"
branch_labels = None
depends_on = None

Base = declarative_base()

data_dir = Path(__file__).parent / "data"


# (source table, destination table)
RENAME_TABLES = [
    ("v2_1d_lateral", "lateral_1d"),
    ("v2_2d_lateral", "lateral_2d"),
    ("v2_1d_boundary_conditions", "boundary_condition_1d"),
    ("v2_2d_boundary_conditions", "boundary_condition_2d"),
]


ADD_COLUMNS = [
    ("lateral_1d", Column("code", Text)),
    ("lateral_1d", Column("display_name", Text)),
    ("lateral_1d", Column("tags", Text)),
    ("lateral_1d", Column("time_units", Text)),
    ("lateral_1d", Column("interpolate", Boolean)),
    ("lateral_1d", Column("offset", Integer)),
    ("lateral_1d", Column("units", Text)),

    ("lateral_2d", Column("code", Text)),
    ("lateral_2d", Column("display_name", Text)),
    ("lateral_2d", Column("tags", Text)),
    ("lateral_2d", Column("time_units", Text)),
    ("lateral_2d", Column("interpolate", Boolean)),
    ("lateral_2d", Column("offset", Integer)),
    ("lateral_2d", Column("units", Text)),

    ("boundary_condition_1d", Column("code", Text)),
    ("boundary_condition_1d", Column("display_name", Text)),
    ("boundary_condition_1d", Column("tags", Text)),
    ("boundary_condition_1d", Column("time_units", Text)),
    ("boundary_condition_1d", Column("interpolate", Boolean)),

    ("boundary_condition_2d", Column("code", Text)),
    # display_name was already added in migration 200
    ("boundary_condition_2d", Column("tags", Text)),
    ("boundary_condition_2d", Column("time_units", Text)),
    ("boundary_condition_2d", Column("interpolate", Boolean)),
]

# Geom columns need to be added using geoalchemy, so therefore that's a separate task
NEW_GEOM_COLUMNS = {
    ("lateral_1d", Column("geom", Geometry("POINT"), nullable=False)),
    ("boundary_condition_1d", Column("geom", Geometry("POINT"), nullable=False)),
}

# old name, new name
# the columns will be individually renamed
# this is because alembic has conniptions whenever you try to batch rename a geometry column
RENAME_GEOM_COLUMNS = {
    "lateral_2d":
        [
            ("the_geom", "geom"),
        ],
    "boundary_condition_2d":
        [
            ("the_geom", "geom"),
        ]
}


DEFAULT_VALUES = {
    "lateral_1d": {
        "time_units": "'minutes'",
        "interpolate": "0",  # false
        "offset": "NULL",
        "units": "'m3/s'"
    },
    "lateral_2d": {
        "time_units": "'minutes'",
        "interpolate": "0",  # false
        "offset": "NULL",
        "units": "'m3/s'"
    },
    "boundary_condition_1d": {
        "time_units": "'minutes'",
        "interpolate": "1",  # true
    },
    "boundary_condition_2d": {
        "time_units": "'minutes'",
        "interpolate": "1",  # true
    },
}


def rename_tables(table_sets: List[Tuple[str, str]]):
    # no checks for existence are done, this will fail if a source table doesn't exist
    for src_name, dst_name in table_sets:
        op.rename_table(src_name, dst_name)


def create_new_tables(new_tables: Dict[str, sa.Column]):
    # no checks for existence are done, this will fail if any table already exists
    for table_name, columns in new_tables.items():
        op.create_table(table_name, sa.Column("id", sa.Integer(), primary_key=True),
                        *columns)


def add_columns_to_tables(table_columns: List[Tuple[str, Column]]):
    # no checks for existence are done, this will fail if any column already exists
    for dst_table, col in table_columns:
        if isinstance(col.type, Geometry):
            add_geometry_column(dst_table, col)
        else:
            with op.batch_alter_table(dst_table) as batch_op:
                batch_op.add_column(col)


def add_geometry_column(table: str, geocol: Column):
    # Adding geometry columns via alembic doesn't work
    # https://postgis.net/docs/AddGeometryColumn.html
    geotype = geocol.type
    query = (
        f"SELECT AddGeometryColumn('{table}', '{geocol.name}', {geotype.srid}, '{geotype.geometry_type}', 'XY', 0);")
    op.execute(sa.text(query))


def rename_columns(table_name: str, columns: List[Tuple[str, str]]):
    # no checks for existence are done, this will fail if table or any source column doesn't exist
    for src_name, dst_name in columns:
        op.execute(sa.text(f"ALTER TABLE {table_name} RENAME COLUMN {src_name} TO {dst_name};"))



def copy_v2_geometries_from_connection_nodes_by_id(dest_table: str, dest_column: str):
    query = (
        f"""
        UPDATE {dest_table}
        SET {dest_column} = (
            SELECT the_geom
            FROM {dest_table}
            LEFT JOIN v2_connection_nodes
            WHERE {dest_table}.connection_node_id = v2_connection_nodes.id
        );
        """
    )
    op.execute(sa.text(query))


def populate_table(table: str, values: dict):
    """Populate SQL columns with values"""
    # convert {a: b, c: d} to "a=b, c=d" for the query
    sql_formatted_columns = ', '.join('{} = {}'.format(key, value) for key, value in values.items())
    # then insert it into the query
    query = f"""UPDATE {table} SET {sql_formatted_columns};"""
    op.execute(sa.text(query))


def upgrade():
    connection = op.get_bind()
    listen(connection.engine, "connect", load_spatialite)
    # rename existing tables
    rename_tables(RENAME_TABLES)
    # add new columns to existing tables
    add_columns_to_tables(ADD_COLUMNS)
    add_columns_to_tables(NEW_GEOM_COLUMNS)
    # rename columns in renamed tables
    for table_name, columns in RENAME_GEOM_COLUMNS.items():
        rename_columns(table_name, columns)
    # recover geometry columns
    for table, column in (
        ("lateral_1d", "geom"),
        ("boundary_condition_1d", "geom")
    ):
        copy_v2_geometries_from_connection_nodes_by_id(dest_table=table, dest_column=column)
    # populate new columns in tables
    for key, value in DEFAULT_VALUES.items():
        populate_table(table=key, values=value)


def downgrade():
    # Not implemented on purpose
    raise NotImplementedError("Downgrade back from 0.3xx is not supported")
