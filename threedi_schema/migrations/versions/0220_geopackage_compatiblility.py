"""rename vegetation columns

Revision ID: 0220
Revises: 0219
Create Date: 2024-02-02 12:53

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0220'
down_revision = '0219'
branch_labels = None
depends_on = None

def upgrade():
    #TODO: replace sql?
    op.execute(sa.text("DROP VIEW IF EXISTS v2_manhole_view;"))
    with op.batch_alter_table("v2_connection_nodes") as batch_op:
        batch_op.drop_column("the_geom_linestring")
    # the_geom has become a GEOM instead of POINT
    # Unfortunately, this doesn't seem to fix it
    op.execute(sa.text("SELECT RecoverGeometryColumn('v2_connection_nodes', 'the_geom', 4326, 'POINT', 'XY')"))
    # remove the_geom_linestring from v2_manhole_view


def downgrade():
    #TODO: test
    with op.batch_alter_table("v2_connection_nodes") as batch_op:
        batch_op.add_column(sa.Column("the_geom_linestring", None))
    # add the_geom_linestring to v2_manhole_view
    # "v2_manhole_view": {
    #     "definition": "SELECT manh.rowid AS rowid, manh.id AS manh_id, manh.display_name AS manh_display_name, manh.code AS manh_code, manh.connection_node_id AS manh_connection_node_id, manh.shape AS manh_shape, manh.width AS manh_width, manh.length AS manh_length, manh.manhole_indicator AS manh_manhole_indicator, manh.calculation_type AS manh_calculation_type, manh.bottom_level AS manh_bottom_level, manh.surface_level AS manh_surface_level, manh.drain_level AS manh_drain_level, manh.sediment_level AS manh_sediment_level, manh.zoom_category AS manh_zoom_category, manh.exchange_thickness AS manh_exchange_thickness, manh.hydraulic_conductivity_in AS manh_hydraulic_conductivity_in, manh.hydraulic_conductivity_out AS manh_hydraulic_conductivity_out, node.id AS node_id, node.storage_area AS node_storage_area, node.initial_waterlevel AS node_initial_waterlevel, node.code AS node_code, node.the_geom AS the_geom, node.the_geom_linestring AS node_the_geom_linestring FROM v2_manhole AS manh , v2_connection_nodes AS node WHERE manh.connection_node_id = node.id",
    #     "view_geometry": "the_geom",
    #     "view_rowid": "rowid",
    #     "f_table_name": "v2_connection_nodes",
    #     "f_geometry_column": "the_geom",
    # },