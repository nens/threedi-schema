"""Add GFRP and Relined pipes to material table

Revision ID: 0302
Revises: 0301
Create Date: 2026-04-10

"""
import csv
from pathlib import Path

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = "0302"
down_revision = "0301"
branch_labels = None
depends_on = None

def upgrade():
    datafile = Path(__file__).parent / "data" / "0302_materials.csv"
    conn = op.get_bind()
    session = Session(bind=conn)
    with open(datafile) as file:
        reader = csv.DictReader(file)
        rows = list(reader)
    # Insert if not present (idempotent)
    for row in rows:
        exists = conn.execute(sa.text("SELECT 1 FROM material WHERE id = :id"), {"id": row["id"]}).fetchone()
        if not exists:
            conn.execute(sa.text(
                """
                INSERT INTO material (id, description, friction_type, friction_coefficient)
                VALUES (:id, :description, :friction_type, :friction_coefficient)
                """
            ), row)
    session.commit()

def downgrade():
    conn = op.get_bind()
    ids = [11, 12]  # IDs used in the migration
    for id in ids:
        conn.execute(sa.text("DELETE FROM material WHERE id = :id"), {"id": id})
