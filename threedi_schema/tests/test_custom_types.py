import pytest

from threedi_schema.domain.custom_types import clean_csv_string, clean_csv_table


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
