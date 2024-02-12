def test_convert_to_geopackage(oldest_sqlite):
    # In case the fixture changes and refers to a geopackage,
    # convert_to_geopackage will be ignored because the db is already a geopackage
    assert oldest_sqlite.get_engine().dialect.name == "sqlite"
    oldest_sqlite.schema.upgrade(convert_to_geopackage=True)
    # Ensure that after the conversion the geopackage is used
    assert oldest_sqlite.path.suffix == ".gpkg"
    assert oldest_sqlite.get_engine().dialect.name == "geopackage"
    assert oldest_sqlite.schema.validate_schema()
