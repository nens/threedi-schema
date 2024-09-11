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

from threedi_schema.domain import constants
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

DELETE_TABLES = ["v2_cross_section_definition"]

NEW_COLUMNS = {
    "channel": [("tags", "TEXT"),],
    "windshielding_1d": [("tags", "TEXT"), ("code", "TEXT"), ("display_name", "TEXT")],
    "cross_section_location": [("tags", "TEXT"), ],
    "culvert": [("tags", "TEXT"),("material_id", "INT")],
    "orifice": [("tags", "TEXT"), ("material_id", "INT")],
    "weir": [("tags", "TEXT"), ("material_id", "INT")],
    "pump": [("tags", "TEXT")]
}

RENAME_COLUMNS = {
    "culvert": {"calculation_type": "exchange_type",
                "dist_calc_points": "calculation_point_distance"},
    "pipe": {"calculation_type": "exchange_type",
             "dist_calc_points": "calculation_point_distance",
             "material_id": "material"},
    "pump": {"connection_node_start_id": "connection_node_id"}
}

REMOVE_COLUMNS = {
    "channel": ["zoom_category",],
    "cross_section_location": ["definition_id", "vegetation_drag_coeficients"],
    "culvert": ["zoom_category", "cross_section_definition_id"],
    "pipe": ["zoom_category", "original_length", "cross_section_definition_id"],
    "orifice": ["zoom_category", "cross_section_definition_id"],
    "wier": ["zoom_category", "cross_section_definition_id"],
    "pump": ["connection_node_end_id", "zoom_category", "classification"]
}

RETYPE_COLUMNS = {}

def add_columns_to_tables(table_columns: List[Tuple[str, Column]]):
    # no checks for existence are done, this will fail if any column already exists
    for dst_table, col in table_columns:
        with op.batch_alter_table(dst_table) as batch_op:
            batch_op.add_column(col)


def remove_tables(tables: List[str]):
    for table in tables:
        op.drop_table(table)


def modify_table(old_table_name, new_table_name):
    # Create a new table named `new_table_name` by copying the
    # data from `old_table_name`.
    # Use the columns from `old_table_name`, with the following exceptions:
    # * columns in `REMOVE_COLUMNS[new_table_name]` are skipped
    # * columns in `RENAME_COLUMNS[new_table_name]` are renamed
    # * columns in `RETYPE_COLUMNS[new_table_name]` change type
    # * `the_geom` is renamed to `geom` and NOT NULL is enforced
    connection = op.get_bind()
    columns = connection.execute(sa.text(f"PRAGMA table_info('{old_table_name}')")).fetchall()
    # get all column names and types
    col_names = [col[1] for col in columns]
    col_types = [col[2] for col in columns]
    # get type of the geometry column
    geom_type = None
    for col in columns:
        if col[1] == 'the_geom':
            geom_type = col[2]
            break
    # create list of new columns and types for creating the new table
    # create list of old columns to copy to new table
    skip_cols = ['id', 'the_geom']
    if new_table_name in REMOVE_COLUMNS:
        skip_cols += REMOVE_COLUMNS[new_table_name]
    old_col_names = []
    new_col_names = []
    new_col_types = []
    for cname, ctype in zip(col_names, col_types):
        if cname in skip_cols:
            continue
        old_col_names.append(cname)
        if new_table_name in RENAME_COLUMNS and cname in RENAME_COLUMNS[new_table_name]:
            new_col_names.append(RENAME_COLUMNS[new_table_name][cname])
        else:
            new_col_names.append(cname)
        if new_table_name in RETYPE_COLUMNS and cname in RETYPE_COLUMNS[new_table_name]:
            new_col_types.append(RETYPE_COLUMNS[new_table_name][cname])
        else:
            new_col_types.append(ctype)
    # add to the end manually
    if 'the_geom' in col_names:
        old_col_names.append('the_geom')
        new_col_names.append('geom')
        new_col_types.append(f'{geom_type} NOT NULL')
    # Create new table (temp), insert data, drop original and rename temp to table_name
    new_col_str = ','.join(['id INTEGER PRIMARY KEY NOT NULL'] + [f'{cname} {ctype}' for cname, ctype in
                                                                  zip(new_col_names, new_col_types)])
    if new_table_name in NEW_COLUMNS:
        new_col_str += ','+','.join([f'{cname} {ctype}' for cname, ctype in NEW_COLUMNS[new_table_name]])
    op.execute(sa.text(f"CREATE TABLE {new_table_name} ({new_col_str});"))
    # Copy data
    op.execute(sa.text(f"INSERT INTO {new_table_name} ({','.join(new_col_names)}) "
                       f"SELECT {','.join(old_col_names)} FROM {old_table_name}"))


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


def create_pump_map():
    # Create table
    # TODO: use sql-alchemy to make this?
    op.execute(sa.text("""
    CREATE TABLE pump_map (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pump_id INTEGER,
        connection_node_end_id INTEGER,
        code TEXT,
        display_name TEXT,
        tags TEXT
    );"""))
    # Copy data from v2_pumpstation
    new_col_names = ["pump_id", "connection_node_end_id", "code", "display_name"]
    old_col_names = ["id", "connection_node_end_id", "code", "display_name"]
    op.execute(sa.text(f"""
    INSERT INTO pump_map ({','.join(new_col_names)}) 
    SELECT {','.join(old_col_names)} FROM v2_pumpstation
    WHERE v2_pumpstation.connection_node_end_id IS NOT NULL
    AND v2_pumpstation.connection_node_start_id IS NOT NULL
    """))
    q))
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
    pass


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


def upgrade():

    # v2_cross_section_location -> cross_section_location
    # - [x] add cross_section_table to cross_section_definition
    # - [x] add cross_section_friction_table to cross_section_definition
    # - [x] add cross_section_vegetation_table to cross_section_definition
    # Add cross_section_definition to
    # - [x] v2_cross_section_location
    # - [x] v2_culvert
    # - [x] v2_pipe
    # - [x] v2_weir
    # - [x] v2_orifice
    # set geom
    # - [x] v2_weir
    # - [x] v2_orifice
    # - [x] v2_pipe
    # - [x] v2_pumpstation
    # simple copy:
    # - [x] v2_channel -> channel
    # - [x] v2_windshielding -> windshielding
    # - [x] v2_cross_section_location -> cross_section_location
    # - [x] v2_cross_section_location
    # - [x] v2_culvert -> culvert
    # - [x] v2_pipe -> pipe
    # - [x] v2_weir -> weir
    # - [x] v2_orifice -> orifice
    # - [x] v2_pumpstation -> pump
    # Modify existing
    # - [x] obstacle
    # - [x] table_control
    # - [x] memory_control
    # - [x] model_settings
    # Material
    # - [x] Material table
    # - [ ] Check / set material
    # pump_map
    # - [x] copy columns from v2_pumpstation
    # - [x] set geometry
    # connection_nodes:
    # - [ ] : create manually
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
    create_pump_map()
    # rename tables
    rem_tables = []
    for old_table_name, new_table_name in RENAME_TABLES:
        modify_table(old_table_name, new_table_name)
        rem_tables.append(old_table_name)
    create_material()
    # for table in ['v2_culvert', 'v2_pipe', 'v2_orifice', 'v2_weir']:
        # include_cross_section_definition(table)
    # set_potential_breach_final_exchange_level()
    # fix_geometry_columns()
    # remove_tables(rem_tables+DELETE_TABLES)
    modify_model_settings()
    modify_obstacle()
    modify_control_target_type()


def downgrade():
    # Not implemented on purpose
    raise NotImplementedError("Downgrade back from 0.3xx is not supported")
