# this import is a test in itself; if these variables aren't defined, the modelchecker will fail
from threedi_schema.beta_features import BETA_COLUMNS, BETA_VALUES
from sqlalchemy.orm.attributes import InstrumentedAttribute

def test_beta_columns_structure():
    assert isinstance(BETA_COLUMNS, list)
    for column in BETA_COLUMNS:
        assert isinstance(column, InstrumentedAttribute)
