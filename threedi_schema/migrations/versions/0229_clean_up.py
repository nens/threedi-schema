"""

Revision ID: 022
9Revises:
Create Date: 2024-11-15 14:18

"""
import uuid
from typing import List

import sqlalchemy as sa
from alembic import op

from threedi_schema import models

# revision identifiers, used by Alembic.
revision = "0229"
down_revision = "0228"
branch_labels = None
depends_on = None


def find_model(table_name):
    for model in models.DECLARED_MODELS:
        if model.__tablename__ == table_name:
            return model
    # This can only go wrong if the migration or model is incorrect
    raise


def create_sqlite_table_from_model(model, table_name):
    cols = get_cols_for_model(model, skip_cols=["id"])
    op.execute(sa.text(f"""
        CREATE TABLE {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
        {','.join(f"{col.name} {col.type}" for col in cols)}
    );"""))


def get_cols_for_model(model, skip_cols=None):
    from sqlalchemy.orm.attributes import InstrumentedAttribute
    if skip_cols is None:
        skip_cols = []
    return [getattr(model, item) for item in model.__dict__
            if item not in skip_cols
            and isinstance(getattr(model, item), InstrumentedAttribute)]


def sync_orm_types_to_sqlite(table_name):
    temp_table_name = f'_temp_229_{uuid.uuid4().hex}'
    model = find_model(table_name)
    create_sqlite_table_from_model(model, temp_table_name)
    col_names = [col.name for col in get_cols_for_model(model)]
    # This may copy wrong type data because some types change!!
    op.execute(sa.text(f"INSERT INTO {temp_table_name} ({','.join(col_names)}) "
                       f"SELECT {','.join(col_names)} FROM {table_name}"))
    op.execute(sa.text(f"DROP TABLE {table_name}"))
    op.execute(sa.text(f"ALTER TABLE {temp_table_name} RENAME TO {table_name};"))


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


def clean_by_type(type: str):
    connection = op.get_bind()
    items = [item[0] for item in connection.execute(
        sa.text(f"SELECT tbl_name FROM sqlite_master WHERE type='{type}' AND tbl_name LIKE '%v2%';")).fetchall()]
    for item in items:
        op.execute(f"DROP {type} IF EXISTS {item};")


def update_use_settings():
    # Ensure that use_* settings are only True when there is actual data for them
    use_settings = [
        (models.ModelSettings.use_groundwater_storage, models.GroundWater),
        (models.ModelSettings.use_groundwater_flow, models.GroundWater),
        (models.ModelSettings.use_interflow, models.Interflow),
        (models.ModelSettings.use_simple_infiltration, models.SimpleInfiltration),
        (models.ModelSettings.use_vegetation_drag_2d, models.VegetationDrag),
        (models.ModelSettings.use_interception, models.Interception)
    ]
    connection = op.get_bind()  # Get the connection for raw SQL execution
    for setting, table in use_settings:
        use_row = connection.execute(
            sa.select(getattr(models.ModelSettings, setting.name))
        ).scalar()
        if not use_row:
            continue
        row = connection.execute(sa.select(table)).first()
        use_row = (row is not None)
        if use_row:
            use_row = not all(
                getattr(row, column.name) in (None, "")
                for column in table.__table__.columns
                if column.name != "id"
            )
        if not use_row:
            connection.execute(
                sa.update(models.ModelSettings)
                .values({setting.name: False})
            )

            
def upgrade():
    remove_old_tables()
    clean_geometry_columns()
    clean_by_type("trigger")
    clean_by_type("view")
    update_use_settings()
    # Apply changing use_2d_rain and friction_averaging type to bool
    sync_orm_types_to_sqlite('model_settings')


def downgrade():
    pass
