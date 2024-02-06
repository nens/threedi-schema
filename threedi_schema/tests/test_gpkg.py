from threedi_schema.domain import models


def test_read_geopackage(gpkg_db):
    channel = gpkg_db.get_session().query(models.Culvert).first()
    assert channel.code == "40902275"
    assert channel.the_geom is not None  # this is what happens with GeoAlchemy2


def test_convert_to_geopackage(oldest_sqlite):
    # In case the fixture changes and refers to a geopackage,
    # convert_to_geopackage will be ignored because the db is already a geopackage
    assert oldest_sqlite.get_engine().dialect.name == "sqlite"
    oldest_sqlite.schema.upgrade(convert_to_geopackage=True)
    # Ensure that after the conversion the geopackage is used
    assert oldest_sqlite.path.suffix == ".gpkg"
    assert oldest_sqlite.get_engine().dialect.name == "geopackage"
