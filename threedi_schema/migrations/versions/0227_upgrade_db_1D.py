"""Migrate 1D related settings to schema 300

Revision ID: 0227
Revises:
Create Date: 2024-09-09 15:44

"""
from copy import deepcopy
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
revision = "0226"
down_revision = "0225"
branch_labels = None
depends_on = None

Base = declarative_base()

data_dir = Path(__file__).parent / "data"


# (source table, destination table)
RENAME_TABLES = [
    ("v2_", "")
]


ADD_COLUMNS = [
    ("table", Column("col", Text)),
]

# Geom columns need to be added using geoalchemy, so therefore that's a separate task
NEW_GEOM_COLUMNS = {
    ("table", Column("geom", Geometry("POINT"), nullable=False)),
}


# old name, new name
# the columns will be renamed using raw sql
# this is because alembic has conniptions whenever you try to batch rename a geometry column
RENAME_COLUMNS = {
    "table": [
        ("old_col", "new_col"),
    ],
}


DEFAULT_VALUES = {
    "table": {
        "col": "val",
    },
}



def upgrade():
    # rename existing tables
    rename_tables(RENAME_TABLES)

    # add new columns to existing tables
    add_columns_to_tables(ADD_COLUMNS)

    # rename columns in renamed tables
    for table_name, columns in RENAME_COLUMNS.items():
        rename_columns(table_name, columns)

    # add geometry columns after renaming columns
    # to not needlessly trigger RecoverGeometryColumn
    add_columns_to_tables(NEW_GEOM_COLUMNS)

    # recover geometry column data from connection nodes
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
