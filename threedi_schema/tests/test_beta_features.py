# comparing directly with SQLAlchemy Column type doesn't work so we use InstrumentedAttribute
from sqlalchemy.orm.attributes import InstrumentedAttribute

# this import is a test in itself; if the beta variables aren't defined, the modelchecker will fail
from threedi_schema.beta_features import BETA_COLUMNS, BETA_VALUES


def test_beta_columns_structure():
    assert isinstance(BETA_COLUMNS, list)
    for column in BETA_COLUMNS:
        assert isinstance(column, InstrumentedAttribute)


def test_beta_values_structure():
    assert isinstance(BETA_VALUES, list)
    for entry in BETA_VALUES:
        assert set(entry) == {"columns", "values"}  # check the keys
        assert isinstance(entry["columns"], list)
        assert isinstance(entry["values"], list)
        for column in entry["columns"]:
            assert isinstance(column, InstrumentedAttribute)
