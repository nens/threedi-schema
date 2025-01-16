import pytest


@pytest.mark.parametrize("upgrade_spatialite", [True, False])
def test_convert_to_geopackage(oldest_sqlite, upgrade_spatialite):
    if upgrade_spatialite:
        oldest_sqlite.schema.upgrade(upgrade_spatialite_version=True)

    oldest_sqlite.schema.convert_to_geopackage()
    # Ensure that after the conversion the geopackage is used
    assert oldest_sqlite.path.suffix == ".gpkg"
    assert not oldest_sqlite.schema.is_spatialite
    assert oldest_sqlite.schema.is_geopackage
    assert oldest_sqlite.schema.validate_schema()
