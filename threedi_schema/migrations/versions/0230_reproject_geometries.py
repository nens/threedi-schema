"""Reproject geometries to model CRS

Revision ID: 0230
Revises:
Create Date: 2024-11-12 12:30

"""
import sqlite3
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm.attributes import InstrumentedAttribute

from threedi_schema import models
from threedi_schema.migrations.exceptions import InvalidSRIDException

# revision identifiers, used by Alembic.
revision = "0230"
down_revision = "0229"
branch_labels = None
depends_on = None


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
    srid_str = conn.execute(sa.text("SELECT epsg_code FROM model_settings LIMIT 1")).fetchone()
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
        raise InvalidSRIDException(srid, "the CRS must be in meters")
    if not is_projected:
        raise InvalidSRIDException(srid, "the CRS must be in projected")
    return srid


def get_cols_for_model(model, skip_cols=None):
    if skip_cols is None:
        skip_cols = []
    return [getattr(model, item) for item in model.__dict__
            if item not in skip_cols
            and isinstance(getattr(model, item), InstrumentedAttribute)]


def create_sqlite_table_from_model(model, table_name, add_geom=True):
    cols = get_cols_for_model(model, skip_cols = ["id", "geom"])
    query = f"""
        CREATE TABLE {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
        {','.join(f"{col.name} {col.type}" for col in cols)}
    """
    if add_geom:
        query += f', geom {model.geom.type.geometry_type} NOT NULL'
    query += ');'
    op.execute(sa.text(query))


def fix_geometry_column(model, srid):
    arg_str = f"'{model.__tablename__}', 'geom'"
    conn = op.get_bind()
    op.execute(sa.text(f"SELECT RecoverGeometryColumn('{model.__tablename__}', "
                       f"'geom', {srid}, '{model.geom.type.geometry_type}', 'XY')"))
    if conn.execute(sa.text(f"SELECT CheckSpatialIndex({arg_str})")).scalar() == 1:
        op.execute(sa.text(f"SELECT DisableSpatialIndex({arg_str})"))
    op.execute(sa.text(f"SELECT CreateSpatialIndex({arg_str})"))
    op.execute(sa.text(f"SELECT RecoverSpatialIndex({arg_str})"))



def transform_column(model, srid):
    table_name = model.__tablename__
    temp_table_name = f'_temp_230_{table_name}'
    create_sqlite_table_from_model(model, temp_table_name)
    col_names = ",".join([col.name for col in get_cols_for_model(model, skip_cols = ["geom"])])
    # Copy transformed geometry and other columns to temp table
    op.execute(sa.text(f"""
        INSERT INTO `{temp_table_name}` ({col_names}, `geom`) 
        SELECT {col_names}, ST_Transform(`geom`, {srid}) AS `geom` FROM `{table_name}`
        """))
    # Discard geometry column in old table
    op.execute(sa.text(f"SELECT DiscardGeometryColumn('{table_name}', 'geom')"))
    # Remove old table
    op.execute(sa.text(f"DROP TABLE `{table_name}`"))
    # Rename temp table
    op.execute(sa.text(f"ALTER TABLE `{temp_table_name}` RENAME TO `{table_name}`;"))
    fix_geometry_column(model, srid)


def prep_spatialite(srid: int):
    conn = op.get_bind()
    has_srid = conn.execute(sa.text(f'SELECT COUNT(*) FROM spatial_ref_sys WHERE srid = {srid};')).fetchone()[0] > 0
    if not has_srid:
        conn.execute(sa.text(f"InsertEpsgSrid({srid})"))


def has_geom():
    connection = op.get_bind()
    geom_tables = [model.__tablename__ for model in models.DECLARED_MODELS if hasattr(model, "geom")]
    has_data = [connection.execute(sa.text(f'SELECT COUNT(*) FROM {table}')).fetchone()[0] > 0 for table in geom_tables]
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
    for model in models.DECLARED_MODELS:
        if hasattr(model, "geom"):
            transform_column(model, srid)
    # remove crs from model_settings
    # with op.batch_alter_table('model_settings') as batch_op:
    #     batch_op.drop_column('epsg_code')


def downgrade():
    # Not implemented on purpose
    raise NotImplementedError("Downgrade back from 0.3xx is not supported")
