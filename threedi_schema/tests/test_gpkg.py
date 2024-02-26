import pytest
import re
import subprocess
def test_convert_to_geopackage(oldest_sqlite):
    # In case the fixture changes and refers to a geopackage,
    # convert_to_geopackage will be ignored because the db is already a geopackage
    assert oldest_sqlite.get_engine().dialect.name == "sqlite"
    oldest_sqlite.schema.upgrade(convert_to_geopackage=True)
    # check if ogr2ogr is installed and has the right version:
    result = subprocess.run('ogr2ogr --version', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result)
    expect_success = False
    if result.returncode == 0:
        # get version
        version = re.findall(r'\b(\d+\.\d+\.\d+)\b', result.stdout)[0]
        # trim patch version and convert to float
        float_version = float(version[0:version.rfind('.')])
        if float_version >= 3.4:
            expect_success = True
    if expect_success:
        # Ensure that after the conversion the geopackage is used
        assert oldest_sqlite.path.suffix == ".gpkg"
        assert oldest_sqlite.get_engine().dialect.name == "geopackage"
        assert oldest_sqlite.schema.validate_schema()
    else:
        with pytest.warns(None):
            assert oldest_sqlite.path.suffix == ".sqlite"
            assert oldest_sqlite.get_engine().dialect.name == "sqlite"
            assert oldest_sqlite.schema.validate_schema()



