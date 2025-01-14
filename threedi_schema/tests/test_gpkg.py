import pytest
from sqlalchemy import text

from threedi_schema.application.schema import get_schema_version
from threedi_schema.infrastructure.spatialite_versions import get_spatialite_version


@pytest.mark.parametrize("upgrade_spatialite", [True, False])
def test_convert_to_geopackage(oldest_sqlite, upgrade_spatialite):
    # if get_schema_version() < 300:
    #     pytest.skip("Gpkg not supported for schema < 300")
    # In case the fixture changes and refers to a geopackage,
    # convert_to_geopackage will be ignored because the db is already a geopackage

    # Ensure that before the conversion, spatialite is used
    with oldest_sqlite.session_scope() as session:
        spatialite_table_exists = bool(
            session.execute(
                text(
                    "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='spatial_ref_sys';"
                )
            ).scalar()
        )

    assert spatialite_table_exists

    if upgrade_spatialite:
        _, file_version = get_spatialite_version(oldest_sqlite)
        assert file_version == 3
        oldest_sqlite.schema.upgrade(revision="0229")
        oldest_sqlite.schema.upgrade_spatialite_version()
        _, file_version = get_spatialite_version(oldest_sqlite)
        assert file_version >= 4

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

    assert gpkg_table_exists and not spatialite_table_exists
    assert oldest_sqlite.schema.validate_schema()
