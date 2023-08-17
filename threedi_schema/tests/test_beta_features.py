# this import is a test in itself; if these variables aren't defined, the modelchecker will fail
from threedi_schema.beta_features import BETA_COLUMNS, BETA_VALUES
# comparing directly with SQLAlchemy Column type doesn't work
from sqlalchemy.orm.attributes import InstrumentedAttribute

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
