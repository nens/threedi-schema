"""Upgrade settings in schema

Revision ID: 0225
Revises:
Create Date: 2024-09-10 09:00

"""
import csv
from pathlib import Path
from typing import Dict, List, Tuple

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base, Session

from threedi_schema.domain import constants, models
from threedi_schema.domain.custom_types import Geometry, IntegerEnum

Base = declarative_base()

data_dir = Path(__file__).parent / "data"


# revision identifiers, used by Alembic.
revision = "0227"
down_revision = "0226"
branch_labels = None
depends_on = None

RENAME_TABLES = [
    ("v2_channel", "channel"),
    ("v2_windshielding", "windshielding_1d"),
    ("v2_cross_section_location", "cross_section_location"),
    ("v2_pipe", "pipe"),
    ("v2_culvert", "culvert"),
    ("v2_weir", "weir"),
    ("v2_orifice", "orifice"),
    ("v2_pumpstation", "pump")
]

DELETE_TABLES = ["v2_cross_section_definition",
                 "v2_floodfill",
                 "v2_connection_nodes"]

RENAME_COLUMNS = {
    "culvert": {"calculation_type": "exchange_type",
                "dist_calc_points": "calculation_point_distance"},
    "pipe": {"calculation_type": "exchange_type",
             "dist_calc_points": "calculation_point_distance",
             "material": "material_id"},
    "channel": {"calculation_type": "exchange_type",
             "dist_calc_points": "calculation_point_distance"},
    "weir": {"calculation_type": "exchange_type",
                "dist_calc_points": "calculation_point_distance"},
    "orifice": {"calculation_type": "exchange_type",
                "dist_calc_points": "calculation_point_distance"},
    "pump": {"connection_node_start_id": "connection_node_id"}
}

REMOVE_COLUMNS = {
    "channel": ["zoom_category",],
    "cross_section_location": ["definition_id", "vegetation_drag_coeficients"],
    "culvert": ["zoom_category", "cross_section_definition_id"],
    "pipe": ["zoom_category", "original_length", "cross_section_definition_id", "profile_num"],
    "orifice": ["zoom_category", "cross_section_definition_id"],
    "weir": ["zoom_category", "cross_section_definition_id"],
    "pump": ["connection_node_end_id", "zoom_category", "classification"]
}

RETYPE_COLUMNS = {}


class Schema227UpgradeException(Exception):
    pass


def add_columns_to_tables(table_columns: List[Tuple[str, Column]]):
    # no checks for existence are done, this will fail if any column already exists
    for dst_table, col in table_columns:
        with op.batch_alter_table(dst_table) as batch_op:
            batch_op.add_column(col)


def remove_tables(tables: List[str]):
    for table in tables:
        op.drop_table(table)


def modify_table(old_table_name, new_table_name):
    # Create a new table named `new_table_name` using the declared models
    # Use the columns from `old_table_name`, with the following exceptions:
    # * columns in `RENAME_COLUMNS[new_table_name]` are renamed
    # * `the_geom` is renamed to `geom` and NOT NULL is enforced
    # create new table
    create_sqlite_table_from_model(find_model(new_table_name))
    # copy data from old to new table
    connection = op.get_bind()
    # get all column names and types
    col_names = [col[1] for col in connection.execute(sa.text(f"PRAGMA table_info('{old_table_name}')")).fetchall()]
    # create list of old and new columns
    skip_cols = ['id', 'the_geom'] + REMOVE_COLUMNS.get(new_table_name, [])
    rename_cols = {**RENAME_COLUMNS.get(new_table_name, {}), "the_geom": "geom"}
    old_col_names = [cname for cname in col_names if cname not in skip_cols]
    new_col_names = [rename_cols.get(cname, cname) for cname in col_names if cname not in skip_cols]
    # Copy data
    op.execute(sa.text(f"INSERT INTO {new_table_name} ({','.join(new_col_names)}) "
                       f"SELECT {','.join(old_col_names)} FROM {old_table_name}"))


def find_model(table_name):
    for model in models.DECLARED_MODELS:
        if model.__tablename__ == table_name:
            return model
    # This can only go wrong if the migration or model is incorrect
    raise

def fix_geometry_columns():
    GEO_COL_INFO = [
        ('dem_average_area', 'geom', 'POLYGON'),
        ('exchange_line', 'geom', 'LINESTRING'),
        ('grid_refinement_line', 'geom', 'LINESTRING'),
        ('grid_refinement_area', 'geom', 'POLYGON'),
        ('obstacle', 'geom', 'LINESTRING'),
        ('potential_breach', 'geom', 'LINESTRING'),
    ]
    for table, column, geotype in GEO_COL_INFO:
        migration_query = f"SELECT RecoverGeometryColumn('{table}', '{column}', {4326}, '{geotype}', 'XY')"
        op.execute(sa.text(migration_query))


class Temp(Base):
    __tablename__ = 'temp'

    id = Column(Integer, primary_key=True)
    cross_section_table = Column(String)
    cross_section_friction_values = Column(String)
    cross_section_vegetation_table = Column(String)
    cross_section_shape = Column(IntegerEnum(constants.CrossSectionShape))


class Material(Base):
    # todo: move to models
    __tablename__ = 'material'

    id = Column(Integer, primary_key=True)
    description = Column(String)
    friction_type = Column(Integer)
    friction_coefficient = Column(Float)


def extend_cross_section_definition_table():
    conn = op.get_bind()
    session = Session(bind=op.get_bind())
    # create temporary table
    # TODO use create_sqlite_table_from_model
    op.execute(sa.text(
        """CREATE TABLE temp 
            (id INTEGER PRIMARY KEY, 
             cross_section_table TEXT,
             cross_section_shape INT,
             cross_section_width REAL,
             cross_section_height REAL,
             cross_section_friction_values TEXT,
             cross_section_vegetation_table TEXT)
        """))
    # copy id's from v2_cross_section_definition
    # TODO copy more ?
    op.execute(sa.text(
        """INSERT INTO temp (id, cross_section_shape, cross_section_width, cross_section_height) 
           SELECT id, shape, width, height 
           FROM v2_cross_section_definition"""
    ))
    # add_cross_section_table_to_temp(session)
    def make_table(*args):
        split_args = [arg.split() for arg in args]
        if not all(len(args) == len(split_args[0]) for args in split_args):
            return
        return '\n'.join([','.join(row) for row in zip(*split_args)])
    # Create cross_section_table for tabulated
    res = conn.execute(sa.text(f"""
        SELECT id, height, width FROM v2_cross_section_definition 
        WHERE v2_cross_section_definition.shape IN (5,6,7)   
        AND height IS NOT NULL AND width IS NOT NULL
    """)).fetchall()
    for id, h, w in res:
        temp_row = session.query(Temp).filter_by(id=id).first()
        temp_row.cross_section_table = make_table(h,w)
        session.commit()
    # add cross_section_friction_table to cross_section_definition
    res = conn.execute(sa.text("""
    SELECT id, friction_values FROM v2_cross_section_definition 
    WHERE friction_values IS NOT NULL
    AND v2_cross_section_definition.shape = 7 
    """)).fetchall()
    for id, friction_values in res:
        temp_row = session.query(Temp).filter_by(id=id).first()
        temp_row.cross_section_friction_values = friction_values.replace(' ',',')
        session.commit()
    # add cross_section_vegetation_table to cross_section_definition
    res = conn.execute(sa.text("""
    SELECT id, vegetation_stem_densities, vegetation_stem_diameters, vegetation_heights, vegetation_drag_coefficients
    FROM v2_cross_section_definition 
    WHERE vegetation_stem_densities IS NOT NULL
    AND vegetation_stem_diameters IS NOT NULL
    AND vegetation_heights IS NOT NULL
    AND vegetation_drag_coefficients IS NOT NULL
    AND v2_cross_section_definition.shape = 7 
    """)).fetchall()
    for id, dens, diam, h, c in res:
        temp_row = session.query(Temp).filter_by(id=id).first()
        temp_row.cross_section_vegetation_table = make_table(dens, diam, h, c)
        session.commit()


def migrate_cross_section_definition_from_temp(target_table: str,
                                               cols: List[Tuple[str, str]],
                                               def_id_col: str):
    for cname, ctype in cols:
        op.execute(sa.text(f'ALTER TABLE {target_table} ADD COLUMN {cname} {ctype}'))

    set_query = ','.join(
        f'{cname} = (SELECT {cname} FROM temp WHERE temp.id = {target_table}.{def_id_col})' for cname, _ in
        cols)
    op.execute(sa.text(f"""
        UPDATE {target_table}
        SET {set_query}
        WHERE EXISTS (SELECT 1 FROM temp WHERE temp.id = {target_table}.{def_id_col});
    """))

def migrate_cross_section_definition_to_location():
    cols = [('cross_section_table', 'TEXT'),
            ('cross_section_friction_values', 'TEXT'),
            ('cross_section_vegetation_table', 'TEXT'),
            ('cross_section_shape', 'INT'),
            ('cross_section_width', 'REAL'),
            ('cross_section_height', 'REAL')]
    migrate_cross_section_definition_from_temp(target_table='v2_cross_section_location',
                                               cols=cols,
                                               def_id_col='definition_id')

def migrate_cross_section_definition_to_object(table_name: str):
    cols = [('cross_section_table', 'TEXT'),
            ('cross_section_shape', 'INT'),
            ('cross_section_width', 'REAL'),
            ('cross_section_height', 'REAL')]
    migrate_cross_section_definition_from_temp(target_table=table_name,
                                               cols=cols,
                                               def_id_col='cross_section_definition_id')


def set_geom_for_object(table_name: str, col_name: str = 'the_geom'):
    # line from connection_node_start_id to connection_node_end_id
    # SELECT load_extension('mod_spatialite');
    op.execute(sa.text(f"SELECT AddGeometryColumn('{table_name}', '{col_name}', 4326, 'LINESTRING', 'XY', 0);"))
    q = f"""
        UPDATE
            {table_name}
        SET the_geom = (
            SELECT MakeLine(start_node.the_geom, end_node.the_geom) FROM {table_name} AS object 
            JOIN v2_connection_nodes AS start_node ON object.connection_node_start_id = start_node.id
            JOIN v2_connection_nodes AS end_node ON object.connection_node_end_id = end_node.id
        )         
    """
    op.execute(sa.text(q))


def set_geom_for_v2_pumpstation():
    op.execute(sa.text(f"SELECT AddGeometryColumn('v2_pumpstation', 'the_geom', 4326, 'POINT', 'XY', 0);"))
    q = f"""
        UPDATE
            v2_pumpstation
        SET the_geom = (
            SELECT node.the_geom FROM v2_pumpstation AS object 
            JOIN v2_connection_nodes AS node ON object.connection_node_start_id = node.id
        )         
    """
    op.execute(sa.text(q))


def create_sqlite_table_from_model(model):
    from sqlalchemy.orm.attributes import InstrumentedAttribute
    skip_cols = ["id", "geom"]
    cols = [getattr(model, item) for item in model.__dict__
            if item not in skip_cols
            and isinstance(getattr(model, item), InstrumentedAttribute)]
    op.execute(sa.text(f"""
        CREATE TABLE {model.__tablename__} (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
        {','.join(f"{col.name} {col.type}" for col in cols)}
    );"""))
    op.execute(sa.text(f"SELECT AddGeometryColumn('{model.__tablename__}', 'geom', "
                       f"4326, '{model.geom.type.geometry_type}', 'XY', 0);"))



def create_pump_map():
    # Create table
    create_sqlite_table_from_model(models.PumpMap)

    # Copy data from v2_pumpstation
    new_col_names = ["pump_id", "connection_node_end_id", "code", "display_name"]
    old_col_names = ["id", "connection_node_end_id", "code", "display_name"]
    op.execute(sa.text(f"""
    INSERT INTO pump_map ({','.join(new_col_names)}) 
    SELECT {','.join(old_col_names)} FROM v2_pumpstation
    WHERE v2_pumpstation.connection_node_end_id IS NOT NULL
    AND v2_pumpstation.connection_node_start_id IS NOT NULL
    """))
    # Create geometry
    op.execute(sa.text("""
    UPDATE pump_map
    SET geom = (
        SELECT MakeLine(start_node.the_geom, end_node.the_geom)
        FROM v2_pumpstation AS object
        JOIN v2_connection_nodes AS start_node ON object.connection_node_start_id = start_node.id
        JOIN v2_connection_nodes AS end_node ON object.connection_node_end_id = end_node.id
        WHERE pump_map.pump_id = object.id
    )
    WHERE EXISTS (
        SELECT 1
        FROM v2_pumpstation AS object
        JOIN v2_connection_nodes AS start_node ON object.connection_node_start_id = start_node.id
        JOIN v2_connection_nodes AS end_node ON object.connection_node_end_id = end_node.id
        WHERE pump_map.pump_id = object.id
    );
    """))




def create_connection_node():
    create_sqlite_table_from_model(models.ConnectionNode)
    # copy from v2_connection_nodes
    old_col_names = ["id", "initial_waterlevel", "storage_area", "the_geom", "code"]
    rename_map = {"initial_waterlevel": "initial_water_level", "the_geom": "geom"}
    new_col_names = [rename_map.get(old_name, old_name) for old_name in old_col_names]
    op.execute(sa.text(f"""
    INSERT INTO connection_node ({','.join(new_col_names)}) 
    SELECT {','.join(old_col_names)} FROM v2_connection_nodes
    """))
    # conditional copy from v2_manhole
    old_col_names = ["display_name", "code", "manhole_indicator",
                     "surface_level", "bottom_level", "drain_level",
                     "calculation_type", "exchange_thickness",
                     "hydraulic_conductivity_in", "hydraulic_conductivity_out"]
    rename_map = {"surface_level": "manhole_surface_level",
                  "bottom_level": "manhole_bottom_level",
                  "drain_level": "exchange_level",
                  "calculation_type": "exchange_type",}
    set_items = ',\n'.join(f"""{rename_map.get(col_name, col_name)} = (
        SELECT v2_manhole.{col_name} FROM v2_manhole
        WHERE v2_manhole.connection_node_id = connection_node.id)""" for col_name in old_col_names)
    op.execute(sa.text(f"""
    UPDATE connection_node
    SET {set_items}
    WHERE EXISTS (
        SELECT 1
        FROM v2_manhole
        WHERE v2_manhole.connection_node_id = connection_node.id
    );
    """))


def create_material():
    op.execute(sa.text("""
    CREATE TABLE material (
    id INTEGER PRIMARY KEY NOT NULL,
    description TEXT,
    friction_type INT,
    friction_coefficient REAL);
    """))
    session = Session(bind=op.get_bind())
    with open(data_dir.joinpath('0227_materials.csv')) as file:
        reader = csv.DictReader(file)
        session.bulk_save_objects([Material(**row) for row in reader])
        session.commit()



def modify_obstacle():
    op.execute(sa.text(f'ALTER TABLE obstacle ADD COLUMN affects_2d BOOLEAN DEFAULT TRUE;'))
    op.execute(sa.text(f'ALTER TABLE obstacle ADD COLUMN affects_1d2d_open_water BOOLEAN DEFAULT TRUE;'))
    op.execute(sa.text(f'ALTER TABLE obstacle ADD COLUMN affects_1d2d_closed BOOLEAN DEFAULT FALSE;'))


def modify_control_target_type():
    for table_name in ['table_control', 'memory_control']:
        op.execute(sa.text(f"""
        UPDATE {table_name}
        SET target_type = REPLACE(target_type, 'v2_', '')
        WHERE target_type LIKE 'v2_%';
        """))


def modify_model_settings():
    op.execute(sa.text(f'ALTER TABLE model_settings ADD COLUMN node_open_water_detection INTEGER DEFAULT 1;'))


def check_for_null_geoms():
    tables = ["v2_connection_nodes", "v2_cross_section_location", "v2_culvert", "v2_channel", "v2_windshielding"]
    conn = op.get_bind()
    for table in tables:
        nof_null = conn.execute(sa.text(f"SELECT COUNT(*) FROM {table} WHERE the_geom IS NULL;")).fetchone()[0]
        if nof_null > 0:
            raise Schema227UpgradeException("Cannot migrate because of empty geometries in table {table}")



def upgrade():
    # Known issues (maybe solve)
    # - empty or non-existing connection node id (start or end) in Orifice, Pipe, Pumpstation or Weir creates a NULL geometry
    check_for_null_geoms()
    # Extent cross section definition table (actually stored in temp)
    extend_cross_section_definition_table()
    # Migrate data from cross_section_definition to cross_section_location
    migrate_cross_section_definition_to_location()
    # Prepare object tables for renaming by copying cross section data and setting the_geom
    for table_name in ['v2_culvert', 'v2_weir', 'v2_pipe', 'v2_orifice']:
        migrate_cross_section_definition_to_object(table_name)
        if table_name != 'v2_culvert':
            set_geom_for_object(table_name)
    set_geom_for_v2_pumpstation()
    for old_table_name, new_table_name in RENAME_TABLES:
        modify_table(old_table_name, new_table_name)
    # Create new tables
    create_pump_map()
    create_material()
    create_connection_node()
    # Modify exsiting tables
    modify_model_settings()
    modify_obstacle()
    modify_control_target_type()
    fix_geometry_columns()
    remove_tables([old for old, _ in RENAME_TABLES]+DELETE_TABLES)


def downgrade():
    # Not implemented on purpose
    raise NotImplementedError("Downgrade back from 0.3xx is not supported")
