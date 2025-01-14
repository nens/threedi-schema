import pytest
from sqlalchemy import text


@pytest.mark.parametrize("upgrade_spatialite", [True, False])
def test_convert_to_geopackage(oldest_sqlite, upgrade_spatialite):
    if upgrade_spatialite:
        oldest_sqlite.schema.upgrade(upgrade_spatialite_version=True)

    oldest_sqlite.schema.convert_to_geopackage()
    # Ensure that after the conversion the geopackage is used
    assert oldest_sqlite.path.suffix == ".gpkg"
    with oldest_sqlite.session_scope() as session:
        gpkg_table_exists = bool(
            session.execute(
                text(
                    "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='gpkg_contents';"
                )
            ).scalar()
        )
        spatialite_table_exists = bool(
            session.execute(
                text(
                    "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='spatial_ref_sys';"
                )
            ).scalar()
        )

    assert gpkg_table_exists
    assert not spatialite_table_exists
    assert oldest_sqlite.schema.validate_schema()
