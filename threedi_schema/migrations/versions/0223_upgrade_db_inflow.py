"""Upgrade settings in schema

Revision ID: 0223
Revises:
Create Date: 2024-05-27 10:35

"""
import json
from pathlib import Path
from typing import Dict, List, Tuple

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import load_spatialite
from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.event import listen
from sqlalchemy.orm import declarative_base

from threedi_schema.domain.custom_types import Geometry

# revision identifiers, used by Alembic.
revision = "0223"
down_revision = "0222"
branch_labels = None
depends_on = None

Base = declarative_base()

data_dir = Path(__file__).parent / "data"

# (source table, destination table)
RENAME_TABLES = [
    ("v2_surface_parameters", "surface_parameters"),
]

ADD_COLUMNS = [
    ("surface_parameters", Column("description", Text)),
    ("surface_parameters", Column("tags", Text)),
]

ADD_TABLES = {
    "surface": [
        Column("area", Float),
        Column("surface_parameters_id", Integer, server_default=1),
        Column("tags", Text),
        Column("code", String(100)),
        Column("display_name", String(255)),
    ],
    "dry_weather_flow": [
        Column("multiplier", Float),
        Column("dry_weather_flow_distribution_id", Integer, server_default=1),
        Column("daily_total", Float),
        Column("interpolate", Boolean, server_default=False),
        Column("tags", Text),
        Column("code", String(100)),
        Column("display_name", String(255)),
    ],
    "surface_map": [
        Column("connection_node_id", Integer),
        Column("surface_id", Integer),
        Column("percentage", Float),
        Column("tags", Text),
        Column("code", String(100)),
        Column("display_name", String(255)),
    ],
    "dry_weather_flow_map": [
        Column("connection_node_id", Integer),
        Column("dry_weather_flow_id", Integer),
        Column("percentage", Float),
        Column("tags", Text),
        Column("code", String(100)),
        Column("display_name", String(255)),
    ],
    "dry_weather_flow_distribution": [
        Column("description", Text),
        Column("tags", Text),
        Column("distribution", Text)
    ],
    "tags": [
        Column("description", Text)
    ]
}

# Geom columns need to be added using geoalchemy, so therefore that's a seperate task
NEW_GEOM_COLUMNS = {
    ("surface", Column("geom", Geometry("POLYGON"), nullable=False)),
    ("dry_weather_flow", Column("geom", Geometry("POLYGON"), nullable=False)),
    ("surface_map", Column("geom", Geometry("LINESTRING"), nullable=False)),
    ("dry_weather_flow_map", Column("geom", Geometry("LINESTRING"), nullable=False))
}

REMOVE_TABLES = [
    "v2_impervious_surface",
    "v2_impervious_surface_map",
    "v2_surface",
    "v2_surface_map"
]


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


def remove_tables(tables: List[str]):
    for table in tables:
        op.drop_table(table)


def copy_values_to_new_table(src_table: str, src_columns: List[str], dst_table: str, dst_columns: List[str]):
    query = f'INSERT INTO {dst_table} ({", ".join(dst_columns)}) SELECT {", ".join(src_columns)} FROM {src_table}'
    op.execute(sa.text(query))


def copy_v2_data_to_surface(src_table: str):
    src_columns = ["id", "code", "display_name", "sur_geom", "area"]
    dst_columns = ["id", "code", "display_name", "geom", "area"]
    if src_table == "v2_surface":
        src_columns += ["surface_parameters_id"]
        dst_columns += ["surface_parameters_id"]
    copy_values_to_new_table(src_table, src_columns, "surface", dst_columns)
    op.execute(sa.text("DELETE FROM surface WHERE area = 0 OR area IS NULL;"))


def copy_v2_data_to_dry_weather_flow(src_table: str):
    src_columns = ["id", "code", "display_name", "dwf_geom", "nr_of_inhabitants", "dry_weather_flow"]
    dst_columns = ["id", "code", "display_name", "geom", "multiplier", "daily_total"]
    copy_values_to_new_table(src_table, src_columns, "dry_weather_flow", dst_columns)
    op.execute(sa.text("DELETE FROM dry_weather_flow "
                       "WHERE multiplier = 0 OR daily_total = 0 OR multiplier IS NULL OR daily_total IS NULL;"))


def remove_orphans_from_map(basename: str):
    query = f"DELETE FROM {basename}_map WHERE {basename}_id NOT IN (SELECT id FROM {basename});"
    op.execute(sa.text(query))


def copy_v2_data_to_dry_weather_flow_map(src_table: str):
    src_columns = ["connection_node_id", "percentage", src_table.strip('v2_').replace('_map', '_id')]
    dst_columns = ["connection_node_id", "percentage", "dry_weather_flow_id"]
    copy_values_to_new_table(src_table, src_columns, "dry_weather_flow_map", dst_columns)


def copy_v2_data_to_surface_map(src_table: str):
    src_columns = ["connection_node_id", "percentage", src_table.strip('v2_').replace('_map', '_id')]
    dst_columns = ["connection_node_id", "percentage", "surface_id"]
    copy_values_to_new_table(src_table, src_columns, "surface_map", dst_columns)


def add_map_geometries(src_table: str):
    # Add geometries to a map table that connects the connection node and the surface / dry_weather_flow
    query = f"""
    UPDATE {src_table}_map 
    SET geom = (
    SELECT MakeLine(c.the_geom, ClosestPoint(s.geom, c.the_geom))
    FROM v2_connection_nodes c
    JOIN {src_table}_map m ON c.id = m.connection_node_id
    JOIN {src_table} s ON s.id = m.{src_table}_id);
    """
    op.execute(sa.text(query))


def get_global_srid():
    conn = op.get_bind()
    use_0d_inflow = conn.execute(sa.text("SELECT use_0d_inflow FROM simulation_template_settings LIMIT 1")).fetchone()
    if use_0d_inflow is not None:
        srid = conn.execute(sa.text("SELECT epsg_code FROM model_settings LIMIT 1")).fetchone()
        if (srid is not None) and (srid[0] is not None):
            return srid[0]
    return 28992


def get_area_str(geom_str) -> str:
    # Get SQLite statement to compute area for a given geometry
    return f'ST_Area(ST_Transform({geom_str},{get_global_srid()}))'


def copy_polygons(src_table: str, tmp_geom: str):
    # Copy existing polygons in src_table to a new column (tmp_geom):
    # - directly copy polygons
    # - copy the first item of all multipolygons
    # - add new rows for each extra polygon inside a multipolygon
    conn = op.get_bind()
    # Copy polygons directly
    op.execute(sa.text(f"UPDATE {src_table} SET {tmp_geom} = the_geom WHERE GeometryType(the_geom) = 'POLYGON';"))
    # Copy first polygon of each multipolygon and correct the area
    op.execute(sa.text(f"""
    UPDATE {src_table} 
    SET {tmp_geom} = ST_GeometryN(the_geom,1), area = {get_area_str('ST_GeometryN(the_geom,1)')}
    WHERE GeometryType(the_geom) = 'MULTIPOLYGON' 
    AND GeometryType(ST_GeometryN(the_geom,1))  = 'POLYGON';
    """))
    # Copy the remaining polygons for multipolygons with more than one polygon
    # select column names that we will copy directly
    col_names = [col_info[1] for col_info in
                 conn.execute(sa.text(f"PRAGMA table_info({src_table})")).fetchall()]
    col_str = ', '.join(list(set(col_names) - {'id', 'the_geom', 'tmp_geom', 'area'}))
    conn = op.get_bind()
    rows = conn.execute(sa.text(f"""
        SELECT id, {col_str}, NumGeometries(the_geom) FROM {src_table}
        WHERE GeometryType(the_geom) = 'MULTIPOLYGON'
        AND GeometryType(ST_GeometryN(the_geom,1))  = 'POLYGON'
        AND NumGeometries(the_geom) > 1;""")).fetchall()
    id_next = conn.execute(sa.text(f"SELECT MAX(id) FROM {src_table}")).fetchall()[0][0]
    surf_id = f"{src_table.strip('v2_')}_id"
    for row in rows:
        id = row[0]
        nof_polygons = row[-1]
        # Retrieve data from map table
        conn_node_id, percentage = conn.execute(sa.text(f"""
            SELECT connection_node_id, percentage FROM {src_table}_map
            WHERE {surf_id} = {id}""")).fetchall()[0]
        for i in range(2, nof_polygons + 1):
            id_next += 1
            # Copy polygon to new row
            op.execute(sa.text(f"""
                INSERT INTO {src_table} (id, the_geom, {tmp_geom}, area, {col_str})
                SELECT {id_next}, the_geom, ST_GeometryN(the_geom, {i}),
                {get_area_str(f'ST_GeometryN(the_geom,{i})')}, {col_str}
                FROM {src_table} WHERE id = {id} LIMIT 1
            """))
            # Add new row to the map
            op.execute(sa.text(f"""
                INSERT INTO {src_table}_map ({surf_id}, connection_node_id, percentage)
                VALUES ({id_next}, {conn_node_id}, {percentage})
            """))


def create_buffer_polygons(src_table: str, tmp_geom: str):
    # create circular polygon of area 1 around the connection node
    surf_id = f"{src_table.strip('v2_')}_id"
    op.execute(sa.text(f"""
    UPDATE {src_table} 
    SET {tmp_geom} = (
        SELECT ST_Buffer(v2_connection_nodes.the_geom, 1)
        FROM v2_connection_nodes 
        JOIN {src_table}_map 
        ON v2_connection_nodes.id = {src_table}_map.connection_node_id
        WHERE {src_table}.id = {src_table}_map.{surf_id}
    )
    WHERE {tmp_geom} IS NULL
    AND id IN (
        SELECT {src_table}_map.{surf_id}
        FROM v2_connection_nodes 
        JOIN {src_table}_map 
        ON v2_connection_nodes.id = {src_table}_map.connection_node_id
    );
    """))


def create_square_polygons(src_table: str, tmp_geom: str):
    # create square polygon with area area around the connection node
    side_expr = f'sqrt({src_table}.area)'
    surf_id = f"{src_table.strip('v2_')}_id"
    # When no geometry is defined, a square with area matching the area column
    # with the center at the connection node is added
    srid = get_global_srid()
    query_str = f"""
        WITH center AS (
          SELECT {src_table}.id AS item_id,
                    ST_Centroid(ST_Collect(
                        ST_Transform(v2_connection_nodes.the_geom, {srid}))) AS geom
          FROM {src_table}_map
          JOIN v2_connection_nodes ON {src_table}_map.connection_node_id = v2_connection_nodes.id
          JOIN {src_table} ON {src_table}_map.{surf_id} = {src_table}.id    
          WHERE {src_table}_map.{surf_id} = {src_table}.id
          GROUP BY {src_table}.id
        ),
        side_length AS (
          SELECT {side_expr} AS side
        )
        UPDATE {src_table}
        SET {tmp_geom} = (
            SELECT ST_Transform(
                    SetSRID(
                        ST_GeomFromText('POLYGON((' ||
                            (ST_X(center.geom) - side_length.side / 2) || ' ' || (ST_Y(center.geom) - side_length.side / 2) || ',' ||
                            (ST_X(center.geom) + side_length.side / 2) || ' ' || (ST_Y(center.geom) - side_length.side / 2) || ',' ||
                            (ST_X(center.geom) + side_length.side / 2) || ' ' || (ST_Y(center.geom) + side_length.side / 2) || ',' ||
                            (ST_X(center.geom) - side_length.side / 2) || ' ' || (ST_Y(center.geom) + side_length.side / 2) || ',' ||
                            (ST_X(center.geom) - side_length.side / 2) || ' ' || (ST_Y(center.geom) - side_length.side / 2) ||
                            '))'),
                        {srid}),
                4326
            ) AS transformed_geom
            FROM center, side_length
            WHERE center.item_id = {src_table}.id
        )
        WHERE {tmp_geom} IS NULL;
        """
    op.execute(sa.text(query_str))


def fix_src_geometry(src_table: str, tmp_geom: str, create_polygons):
    conn = op.get_bind()
    # create columns to store the derived geometries to
    op.execute(sa.text(f"SELECT AddGeometryColumn('{src_table}', '{tmp_geom}', 4326, 'POLYGON', 'XY', 0);"))
    # Copy existing polygons
    copy_polygons(src_table, tmp_geom)
    # Check if any existing geometries where not copied
    not_copied = conn.execute(sa.text(f'SELECT id FROM {src_table} '
                                      f'WHERE {tmp_geom} IS NULL '
                                      f'AND the_geom IS NOT NULL')).fetchall()
    if len(not_copied) > 0:
        raise BaseException(f'Found {len(not_copied)} geometries in {src_table} that could not'
                            f'be converted to a POLYGON geometry: {not_copied}')
    # Create polygons for rows where no geometry was defined
    create_polygons(src_table, tmp_geom)


def populate_surface_and_dry_weather_flow():
    conn = op.get_bind()
    use_0d_inflow = conn.execute(sa.text("SELECT use_0d_inflow FROM simulation_template_settings LIMIT 1")).fetchone()
    if (use_0d_inflow is None) or (len(use_0d_inflow) == 0) or (use_0d_inflow[0] not in [1, 2]):
        return
    use_0d_inflow = use_0d_inflow[0]
    # Use use_0d_inflow setting to determine wether to copy any data and if so from what table
    src_table = "v2_impervious_surface" if use_0d_inflow == 1 else "v2_surface"
    # Remove rows with insufficient data
    op.execute(sa.text(f"DELETE FROM {src_table} WHERE area = 0 "
                       "AND (nr_of_inhabitants = 0 OR dry_weather_flow = 0);"))
    # Create geometries for non-specified ones
    # Add geometries for surfaces and dwf by adding extra columns
    # This has to be done in advance because NULL geometries cannot be copied
    # And this had to be done seperately because the geometries for surfaces and
    # DWF are not by definition the same
    fix_src_geometry(src_table, 'sur_geom', create_square_polygons)
    fix_src_geometry(src_table, 'dwf_geom', create_buffer_polygons)
    # Copy data to new tables
    copy_v2_data_to_surface(src_table)
    copy_v2_data_to_dry_weather_flow(src_table)
    copy_v2_data_to_surface_map(f"{src_table}_map")
    copy_v2_data_to_dry_weather_flow_map(f"{src_table}_map")
    # Remove rows in maps that refer to non-existing objects
    remove_orphans_from_map(basename="surface")
    remove_orphans_from_map(basename="dry_weather_flow")
    # Create geometries in new maps
    add_map_geometries("surface")
    add_map_geometries("dry_weather_flow")
    # Set surface parameter id
    if use_0d_inflow == 1:
        set_surface_parameters_id()
    # Populate tables with default values
    populate_dry_weather_flow_distribution()
    populate_surface_parameters()


def set_surface_parameters_id():
    # Make sure not to call this on an empty database
    with open(data_dir.joinpath('0223_surface_parameters_map.json'), 'r') as f:
        parameter_map = json.load(f)
    conn = op.get_bind()
    surface_class, surface_inclination = conn.execute(
        sa.text("SELECT surface_class, surface_inclination FROM v2_impervious_surface")).fetchone()
    parameter_id = parameter_map[f'{surface_class} - {surface_inclination}']
    op.execute(f'UPDATE surface SET surface_parameters_id = {parameter_id}')


def populate_surface_parameters():
    # Make sure not to call this on an empty database
    with open(data_dir.joinpath('0223_surface_parameters_contents.json'), 'r') as f:
        data_to_insert = json.load(f)
    keys_str = "(" + ",".join(data_to_insert[0].keys()) + ")"
    for row in data_to_insert:
        val_str = "(" + ",".join([repr(item) for item in row.values()]) + ")"
        sql_query = f"INSERT INTO surface_parameters {keys_str} VALUES {val_str}"
        op.execute(sa.text(sql_query))


def populate_dry_weather_flow_distribution():
    with open(data_dir.joinpath('0223_dry_weather_flow_distribution.csv'), 'r') as f:
        distr = f.read().strip()
    description = "Kennisbank Stichting Rioned - https://www.riool.net/huishoudelijk-afvalwater"
    sql_query = f"INSERT INTO dry_weather_flow_distribution (description, distribution) VALUES ('{description}', '{distr}')"
    op.execute(sa.text(sql_query))


def fix_geometry_columns():
    GEO_COL_INFO = [
        ('dry_weather_flow', 'geom', 'POLYGON'),
        ('dry_weather_flow_map', 'geom', 'LINESTRING'),
        ('surface', 'geom', 'POLYGON'),
        ('surface_map', 'geom', 'LINESTRING'),
    ]
    for table, column, geotype in GEO_COL_INFO:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(column_name=column, nullable=False)
        migration_query = f"SELECT RecoverGeometryColumn('{table}', '{column}', {4326}, '{geotype}', 'XY')"
        op.execute(sa.text(migration_query))


def upgrade():
    connection = op.get_bind()
    listen(connection.engine, "connect", load_spatialite)
    # create new tables and rename existing tables
    create_new_tables(ADD_TABLES)
    rename_tables(RENAME_TABLES)
    # add new columns to existing tables
    add_columns_to_tables(ADD_COLUMNS)
    add_columns_to_tables(NEW_GEOM_COLUMNS)
    # migrate values from old tables to new tables
    populate_surface_and_dry_weather_flow()
    # recover geometry columns
    fix_geometry_columns()
    # remove old tables
    remove_tables(REMOVE_TABLES)


def downgrade():
    # Not implemented on purpose
    raise NotImplementedError("Downgrade back from 0.3xx is not supported")
