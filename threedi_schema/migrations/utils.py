from typing import List

import sqlalchemy as sa


def drop_geo_table(op, table_name: str):
    """

    Safely drop table, taking into account geometry columns

    Parameters:
    op : object
        An object representing the database operation.
    table_name : str
        The name of the table to be dropped.
    """
    connection = op.get_bind()
    res = connection.execute(sa.text(f"SELECT DropGeoTable('{table_name}', 0);")).fetchall()[0][0]
    if res == 0:
        op.execute(f"DROP TABLE IF EXISTS {table_name}")
        has_geom_cols = connection.execute(sa.text(f"""
            SELECT COUNT(*) FROM geometry_columns WHERE f_table_name = '{table_name}'
        """)).fetchall()[0][0] > 0
        if has_geom_cols:
            op.execute(sa.text(f"""
                DELETE FROM geometry_columns WHERE f_table_name = '{table_name}';
            """))
        triggers = [item[0] for item in connection.execute(sa.text(f"""
            SELECT name FROM sqlite_master 
            WHERE type = 'trigger' AND (tbl_name = '{table_name}' OR sql LIKE '%{table_name}%');        
        """)).fetchall()]
        for trigger in triggers:
            op.execute(f"DROP TRIGGER IF EXISTS {trigger};")
    # op.execute(sa.text(f"SELECT DropTable(NULL, '{table_name}');"))


def drop_conflicting(op, new_tables: List[str]):
    """
    Drop tables from database that conflict with new tables

    Parameters:
    op: The SQLAlchemy operation context to interact with the database.
    new_tables: A list of new table names to be checked for conflicts with existing tables.
    """
    connection = op.get_bind()
    existing_tables = [item[0] for item in connection.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()]
    for table_name in set(existing_tables).intersection(new_tables):
        drop_geo_table(op, table_name)