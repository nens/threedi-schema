import pytest

from threedi_schema.domain import constants


@pytest.mark.parametrize("upgrade_spatialite", [True, False])
def test_convert_to_geopackage(oldest_sqlite, upgrade_spatialite):
    # if upgrade_spatialite:
    oldest_sqlite.schema.upgrade(
        upgrade_spatialite_version=upgrade_spatialite,
        revision=f"{constants.LAST_SPTL_SCHEMA_VERSION:04d}",
    )

    oldest_sqlite.schema.convert_to_geopackage()
    # Ensure that after the conversion the geopackage is used
    assert oldest_sqlite.path.suffix == ".gpkg"
    assert not oldest_sqlite.schema.is_spatialite
    assert oldest_sqlite.schema.is_geopackage
