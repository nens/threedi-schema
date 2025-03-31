from pathlib import Path

import pytest
from sqlalchemy import text

from threedi_schema.domain import constants


@pytest.mark.parametrize(
    "upgrade_spatialite, delete_spatialite", [[True, True], [False, False]]
)
def test_convert_to_geopackage(oldest_sqlite, upgrade_spatialite, delete_spatialite):
    # if upgrade_spatialite:
    oldest_sqlite.schema.upgrade(
        upgrade_spatialite_version=upgrade_spatialite,
        revision=f"{constants.LAST_SPTL_SCHEMA_VERSION:04d}",
    )
    old_path = Path(oldest_sqlite.path)
    oldest_sqlite.schema.convert_to_geopackage(delete_spatialite=delete_spatialite)
    # Ensure that after the conversion the geopackage is used
    assert oldest_sqlite.path.suffix == ".gpkg"
    if delete_spatialite:
        assert not old_path.exists()
    assert not oldest_sqlite.schema.is_spatialite
    assert oldest_sqlite.schema.is_geopackage

    with oldest_sqlite.get_session() as session:
        assert (
            session.execute(
                text(
                    "SELECT count(*) FROM sqlite_master WHERE type='view' AND name='spatial_ref_sys'"
                )
            ).scalar()
            == 1
        )
