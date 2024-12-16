import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest

from threedi_schema import models, ModelSchema, ThreediDatabase
from threedi_schema.migrations.exceptions import InvalidSRIDException

data_dir = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sqlite_path():
    return data_dir.joinpath("test_crs_migation_28992.sqlite")


@pytest.fixture()
def db(tmp_path_factory, sqlite_path):
    tmp_sqlite = tmp_path_factory.mktemp("custom_dir").joinpath(sqlite_path.name)
    shutil.copy(sqlite_path, tmp_sqlite)
    return ThreediDatabase(tmp_sqlite)


@pytest.mark.parametrize("epsg_code", [
    999999, # non-existing
    2227, # projected / US survey foot
    4979, # not project
])
def test_check_valid_crs(db, epsg_code):
    session = db.get_session()
    # Update the epsg_code in ModelSettings
    model_settings_to_update = session.query(models.ModelSettings).filter_by(id=0).first()
    model_settings_to_update.epsg_code = epsg_code
    session.commit()
    with pytest.raises(InvalidSRIDException) as exc_info:
        db.schema.upgrade(backup=False)


def test_migration(tmp_path_factory):
    # Ensure all geometries are transformed
    sqlite_path = data_dir.joinpath("v2_bergermeer_221.sqlite")
    tmp_sqlite = tmp_path_factory.mktemp("custom_dir").joinpath(sqlite_path.name)
    shutil.copy(sqlite_path, tmp_sqlite)
    schema = ModelSchema(ThreediDatabase(tmp_sqlite))
    schema.upgrade(backup=False)
    cursor = sqlite3.connect(schema.db.path).cursor()
    query = cursor.execute("SELECT srid FROM geometry_columns where f_table_name = 'geom'")
    epsg_matches = [int(item[0])==28992 for item in query.fetchall()]
    assert all(epsg_matches)


