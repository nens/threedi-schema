"""Reproject geometries to model CRS

Revision ID: 0230
Revises:
Create Date: 2024-11-12 12:30

"""
import sqlite3
import uuid

import sqlalchemy as sa
from alembic import op

from threedi_schema.migrations.exceptions import InvalidSRIDException

# revision identifiers, used by Alembic.
revision = "0230"
down_revision = "0229"
branch_labels = None
depends_on = None

GEOM_TABLES = ['boundary_condition_1d', 'boundary_condition_2d', 'channel', 'connection_node', 'measure_location',
               'measure_map', 'memory_control', 'table_control', 'cross_section_location', 'culvert',
               'dem_average_area', 'dry_weather_flow', 'dry_weather_flow_map', 'exchange_line', 'grid_refinement_line',
               'grid_refinement_area', 'lateral_1d', 'lateral_2d', 'obstacle', 'orifice', 'pipe', 'potential_breach',
               'pump', 'pump_map', 'surface', 'surface_map', 'weir', 'windshielding_1d']


def get_crs_info(srid):
    # Create temporary spatialite to find crs unit and projection
    conn = sqlite3.connect(":memory:")
    conn.enable_load_extension(True)
    conn.load_extension("mod_spatialite")
    # Initialite spatialite without any meta data
    conn.execute("SELECT InitSpatialMetaData(1, 'NONE');")
    # Add CRS
    success = conn.execute(f"SELECT InsertEpsgSrid({srid})").fetchone()[0]
    if not success:
        raise InvalidSRIDException(srid, "the supplied epsg_code is invalid")
    # retrieve units and is_projected
    unit = conn.execute(f'SELECT SridGetUnit({srid})').fetchone()[0]
    is_projected = conn.execute(f'SELECT SridIsProjected({srid})').fetchone()[0]
    return unit, is_projected


def get_model_srid() -> int:
    # Note: this will not work for models which are allowed to have no CRS (no geometries)
    conn = op.get_bind()
    srid_str = conn.execute(sa.text("SELECT epsg_code FROM model_settings")).fetchone()
    if srid_str is None or srid_str[0] is None:
        if not has_geom():
            return None
        raise InvalidSRIDException(None, "no epsg_code is defined")
    try:
        srid = int(srid_str[0])
    except TypeError:
        raise InvalidSRIDException(srid_str[0], "the epsg_code must be an integer")
    unit, is_projected = get_crs_info(srid)
    if unit != "metre":
        raise InvalidSRIDException(srid, f"the CRS must be in meters, not {unit}")
    if not is_projected:
        raise InvalidSRIDException(srid, "the CRS must be in projected")
    return srid


def get_geom_type(table_name, geo_col_name):
    connection = op.get_bind()
    columns = connection.execute(sa.text(f"PRAGMA table_info('{table_name}')")).fetchall()
    for col in columns:
        if col[1] == geo_col_name:
            return col[2]


def add_geometry_column(table: str, name: str, srid: int, geometry_type: str):
    # Adding geometry columns via alembic doesn't work
    query = (
        f"SELECT AddGeometryColumn('{table}', '{name}', {srid}, '{geometry_type}', 'XY', 1);")
    op.execute(sa.text(query))


def transform_column(table_name, srid):
    connection = op.get_bind()
    columns = connection.execute(sa.text(f"PRAGMA table_info('{table_name}')")).fetchall()
    # get all column names and types
    skip_cols = ['id', 'geom']
    col_names = [col[1] for col in columns if col[1] not in skip_cols]
    col_types = [col[2] for col in columns if col[1] not in skip_cols]
    # Create temporary table
    temp_table_name = f'_temp_230_{table_name}_{uuid.uuid4().hex}'
    # Create new table, insert data, drop original and rename temp to table_name
    col_str = ','.join(['id INTEGER PRIMARY KEY NOT NULL'] + [f'{cname} {ctype}' for cname, ctype in
                                                              zip(col_names, col_types)])
    query = f"CREATE TABLE {temp_table_name} ({col_str});"
    op.execute(sa.text(query))
    # Add geometry column with new srid!
    geom_type = get_geom_type(table_name, 'geom')
    add_geometry_column(temp_table_name, 'geom', srid, geom_type)
    # Copy transformed geometry and other columns to temp table
    col_str = ','.join(['id'] + col_names)
    query = f"""
        INSERT INTO {temp_table_name} ({col_str}, geom) 
        SELECT {col_str}, ST_Transform(geom, {srid}) AS geom FROM {table_name}
        """
    op.execute(sa.text(query))
    # Discard geometry column in old table
    op.execute(sa.text(f"SELECT DiscardGeometryColumn('{table_name}', 'geom')"))
    op.execute(sa.text(f"SELECT DiscardGeometryColumn('{temp_table_name}', 'geom')"))
    # Remove old table
    op.execute(sa.text(f"DROP TABLE '{table_name}'"))
    # Rename temp table
    op.execute(sa.text(f"ALTER TABLE '{temp_table_name}' RENAME TO '{table_name}';"))
    # Recover geometry stuff
    op.execute(sa.text(f"SELECT RecoverGeometryColumn('{table_name}', "
                       f"'geom', {srid}, '{geom_type}', 'XY')"))
    op.execute(sa.text(f"SELECT CreateSpatialIndex('{table_name}', 'geom')"))
    op.execute(sa.text(f"SELECT RecoverSpatialIndex('{table_name}', 'geom')"))


def prep_spatialite(srid: int):
    conn = op.get_bind()
    has_srid = conn.execute(sa.text(f'SELECT COUNT(*) FROM spatial_ref_sys WHERE srid = {srid};')).fetchone()[0] > 0
    if not has_srid:
        conn.execute(sa.text(f"InsertEpsgSrid({srid})"))


def has_geom():
    connection = op.get_bind()
    has_data = [connection.execute(sa.text(f'SELECT COUNT(*) FROM {table}')).fetchone()[0] > 0 for table in GEOM_TABLES]
    return any(has_data)


def upgrade():
    # retrieve srid from model settings
    # raise exception if there is no srid, or if the srid is not valid
    srid = get_model_srid()
    if srid is None:
        print('Model without geometries and epsg code, we need to think about this')
        return
    # prepare spatialite databases
    prep_spatialite(srid)
    # transform all geometries
    for table_name in GEOM_TABLES:
        transform_column(table_name, srid)
    # remove crs from model_settings
    with op.batch_alter_table('model_settings') as batch_op:
        batch_op.drop_column('epsg_code')


def downgrade():
    # Not implemented on purpose
    raise NotImplementedError("Downgrade back from 0.3xx is not supported")
