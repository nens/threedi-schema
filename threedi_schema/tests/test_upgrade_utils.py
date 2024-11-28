import logging
from pathlib import Path
from unittest.mock import call, MagicMock

import pytest

from threedi_schema.application import upgrade_utils
from threedi_schema.application.schema import get_alembic_config
from threedi_schema.application.threedi_database import ThreediDatabase

data_dir = Path(__file__).parent / "data"


def test_progress_handler():
    progress_func = MagicMock()
    mock_record = MagicMock(levelno=logging.INFO, percent=40)
    expected_calls = [call(100 * i / 5) for i in range(5)]
    handler = upgrade_utils.ProgressHandler(progress_func, total_steps=5)
    for _ in range(5):
        handler.handle(mock_record)
    assert progress_func.call_args_list == expected_calls


@pytest.mark.parametrize(
    "target_revision, nsteps_expected", [("0226", 5), ("0200", 0), (None, 0)]
)
def test_get_upgrade_steps_count(target_revision, nsteps_expected):
    schema = ThreediDatabase(data_dir.joinpath("v2_bergermeer_221.sqlite")).schema
    nsteps = upgrade_utils.get_upgrade_steps_count(
        config=get_alembic_config(),
        current_revision=schema.get_version(),
        target_revision=target_revision,
    )
    assert nsteps == nsteps_expected


def test_get_upgrade_steps_count_pre_200(oldest_sqlite):
    schema = oldest_sqlite.schema
    nsteps = upgrade_utils.get_upgrade_steps_count(
        config=get_alembic_config(),
        current_revision=schema.get_version(),
        target_revision="0226",
    )
    assert nsteps == 27


def test_upgrade_with_progress_func(oldest_sqlite):
    schema = oldest_sqlite.schema
    progress_func = MagicMock()
    schema.upgrade(
        backup=False,
        upgrade_spatialite_version=False,
        progress_func=progress_func,
        revision="0201",
    )
    assert progress_func.call_args_list == [call(0.0), call(50.0)]