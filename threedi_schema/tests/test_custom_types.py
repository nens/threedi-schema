import pytest
from sqlalchemy import Column, create_engine, func, Integer
from sqlalchemy.event import listen
from sqlalchemy.orm import declarative_base, sessionmaker

from threedi_schema.application.threedi_database import load_spatialite
from threedi_schema.domain.custom_types import (
    clean_csv_string,
    clean_csv_table,
    Geometry,
)


@pytest.mark.parametrize(
    "value",
    [
        "1,2,3",
        "1, 2, 3 ",
        "1,\t2,3",
        "1,\r2,3 ",
        "1,\n2,3 ",
        "1,  2,3",
        "1,  2  ,3",
        " 1,2,3 ",
        "\n1,2,3",
        "\t1,2,3",
        "\r1,2,3",
        "1,2,3\t",
        "1,2,3\n",
        "1,2,3\r",
    ],
)
def test_clean_csv_string(value):
    assert clean_csv_string(value) == "1,2,3"


def test_clean_csv_string_with_whitespace():
    assert clean_csv_string("1,2 3,4") == "1,2 3,4"


@pytest.mark.parametrize(
    "value",
    [
        "1,2,3\n4,5,6",
        "1,2,3\r\n4,5,6",
        "\n1,2,3\n4,5,6",
        "1,2,3\n4,5,6\n",
    ],
)
def test_clean_csv_table(value):
    assert clean_csv_table(value) == "1,2,3\n4,5,6"


@pytest.mark.parametrize(
    "value", [" ", "0 1", "3;5", "foo", "1,2\n3,", ",2", ",2\n3,4"]
)
def test_clean_csv_table_no_fail(value):
    clean_csv_table(value)


@pytest.mark.parametrize("from_text", [None, "GeomFromEWKB"])
def test_geometry_type_from_text(from_text):
    # Esnure that the "from_text" values that are use to
    # create a Geometry do not break downstream
    Base = declarative_base()

    engine = create_engine("sqlite:///:memory:")
    listen(engine, "connect", load_spatialite)

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.execute(func.gpkgCreateBaseTables())

    class Location(Base):
        __tablename__ = "locations"
        id = Column(Integer, primary_key=True)
        geom = Column(Geometry("POINT", from_text=from_text))  # Invalid from_text

    Base.metadata.create_all(engine)

    try:
        # Create a test point using WKT format
        test_location = Location()
        session.add(test_location)
        session.commit()
    finally:
        session.close()
