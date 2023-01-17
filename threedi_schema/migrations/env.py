import os

from alembic import context

import threedi_schema.domain.models  # NOQA needed for autogenerate
from threedi_schema import ThreediDatabase
from threedi_schema.domain import constants
from threedi_schema.domain.models import Base

target_metadata = Base.metadata
config = context.config


def get_url():
    db_url = os.environ.get("DB_URL")
    if not db_url:
        raise RuntimeError(
            "Database URL must be specified using the environment variable DB_URL"
        )
    return db_url


def run_migrations_online():
    """Run migrations in 'online' mode.

    Note: SQLite does not (completely) support transactions, so, backup the
    SQLite before running migrations.
    """
    connectable = config.attributes.get("connection")
    if connectable is None:
        connectable = ThreediDatabase(get_url()).get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=constants.VERSION_TABLE_NAME,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise ValueError("Offline mode is not supported")
else:
    run_migrations_online()
