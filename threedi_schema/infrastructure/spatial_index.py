from geoalchemy2.types import Geometry
from sqlalchemy import func, text

__all__ = ["ensure_spatial_indexes"]


def _ensure_spatial_index(connection, column):
    """Ensure presence of a spatial index for given geometry olumn"""
    if (
        connection.execute(
            func.RecoverSpatialIndex(column.table.name, column.name)
        ).scalar()
        is not None
    ):
        return False

    idx_name = f"{column.table.name}_{column.name}"
    connection.execute(text(f"DROP TABLE IF EXISTS idx_{idx_name}"))
    for prefix in {"gii_", "giu_", "gid_"}:
        connection.execute(text(f"DROP TRIGGER IF EXISTS {prefix}{idx_name}"))
    if (
        connection.execute(
            func.CreateSpatialIndex(column.table.name, column.name)
        ).scalar()
        != 1
    ):
        raise RuntimeError(f"Spatial index creation for {idx_name} failed")

    return True


def ensure_spatial_indexes(db, models):
    """Ensure presence of spatial indexes for all geometry columns"""
    created = False
    engine = db.engine

    with engine.connect() as connection:
        with connection.begin():
            for model in models:
                geom_columns = [
                    x for x in model.__table__.columns if isinstance(x.type, Geometry)
                ]
                if len(geom_columns) > 1:
                    # Pragmatic fix: spatialindex breaks on multiple geometry columns per table
                    geom_columns = [x for x in geom_columns if x.name == "the_geom"]
                if geom_columns:
                    created &= _ensure_spatial_index(connection, geom_columns[0])

            if created:
                connection.execute(text("VACUUM"))
