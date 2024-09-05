"""Upgrade settings in schema

Revision ID: 0225
Revises:
Create Date: 2024-08-30 07:52

"""
from typing import Dict, List, Tuple

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

from threedi_schema.domain.custom_types import Geometry

# revision identifiers, used by Alembic.
revision = "0225"
down_revision = "0224"
branch_labels = None
depends_on = None

def upgrade():
    pass


def downgrade():
    # Not implemented on purpose
    raise NotImplementedError("Downgrade back from 0.3xx is not supported")
