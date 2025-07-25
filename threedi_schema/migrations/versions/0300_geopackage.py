"""Convert to geopackage

Revision ID: 0230
Revises:
Create Date: 2024-11-12 12:30

"""
import sqlite3
import uuid

import sqlalchemy as sa
from alembic import op

from threedi_schema.application.errors import InvalidSRIDException

# revision identifiers, used by Alembic.
revision = "0300"
down_revision = "0230"
branch_labels = None
depends_on = None


def fix_use_0d_inflow():
    # fix setting use_0d_inflow to be only 0 or 1 (also see migration 223)
    op.execute(sa.text("""UPDATE simulation_template_settings SET use_0d_inflow = 1 WHERE use_0d_inflow > 0 """))


def upgrade():
    fix_use_0d_inflow()


def downgrade():
    # Not implemented on purpose
    pass
