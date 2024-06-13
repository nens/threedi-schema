import re
import subprocess

import pytest

from threedi_schema.application.schema import get_schema_version


def test_convert_to_geopackage(oldest_sqlite):
    if get_schema_version() < 300:
        pytest.skip("Gpkg not supported for schema < 300")
    # In case the fixture changes and refers to a geopackage,
    # convert_to_geopackage will be ignored because the db is already a geopackage
    assert oldest_sqlite.get_engine().dialect.name == "sqlite"
    # check if ogr2ogr is installed and has the right version:
    result = subprocess.run(
        "ogr2ogr --version",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    expect_success = False
    if result.returncode == 0:
        # get version
        version = re.findall(r"\b(\d+\.\d+\.\d+)\b", result.stdout)[0]
        # trim patch version and convert to float
        float_version = float(version[0 : version.rfind(".")])
        if float_version >= 3.4:
            expect_success = True
    if expect_success:
        oldest_sqlite.schema.convert_to_geopackage()
        # Ensure that after the conversion the geopackage is used
        assert oldest_sqlite.path.suffix == ".gpkg"
        assert oldest_sqlite.get_engine().dialect.name == "geopackage"
        assert oldest_sqlite.schema.validate_schema()
    else:
        # Upgrade is not performed in convert_to_geopackage when ogr2ogr doesn't run
        # because no operation should be performed in that case.
        # However, this wil result in an invalid schema, so here we will run upgrade manually.
        # Because convert_to_geopackage() is only used via upgrade; this is not an issue.
        with pytest.warns():
            oldest_sqlite.schema.convert_to_geopackage()
            oldest_sqlite.schema.upgrade()
            assert oldest_sqlite.path.suffix == ".sqlite"
            assert oldest_sqlite.get_engine().dialect.name == "sqlite"
            assert oldest_sqlite.schema.validate_schema()
