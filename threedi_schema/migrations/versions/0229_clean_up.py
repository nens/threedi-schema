"""

Revision ID: 022
9Revises:
Create Date: 2024-11-15 14:18

"""
from typing import List

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0229"
down_revision = "0228"
branch_labels = None
depends_on = None


def remove_tables(tables: List[str]):
    for table in tables:
        op.drop_table(table)


def find_tables_by_pattern(pattern: str) -> List[str]:
    connection = op.get_bind()
    query = connection.execute(
        sa.text(f"select name from sqlite_master where type = 'table' and name like '{pattern}'"))
    return [item[0] for item in query.fetchall()]


def remove_old_tables():
    remaining_v2_idx_tables = find_tables_by_pattern('idx_v2_%_the_geom')
    remaining_alembic = find_tables_by_pattern('%_alembic_%_the_geom')
    remove_tables(remaining_v2_idx_tables + remaining_alembic)


def clean_geometry_columns():
    """ Remove columns referencing v2 in geometry_columns """
    op.execute(sa.text("""
            DELETE FROM geometry_columns WHERE f_table_name IN (
                SELECT g.f_table_name FROM geometry_columns g
                LEFT JOIN sqlite_master m ON g.f_table_name = m.name
                WHERE m.name IS NULL AND g.f_table_name like "%v2%"
            );
        """))


def clean_triggers():
    """ Remove triggers referencing v2 tables """
    connection = op.get_bind()
    triggers = [item[0] for item in connection.execute(
        sa.text("SELECT tbl_name FROM sqlite_master WHERE type='trigger' AND tbl_name LIKE '%v2%';")).fetchall()]
    for trigger in triggers:
        op.execute(f"DROP TRIGGER IF EXISTS {trigger};")


def upgrade():
    remove_old_tables()
    clean_geometry_columns()
    clean_triggers()


def downgrade():
    pass
