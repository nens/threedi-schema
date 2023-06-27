import os
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .schema import ModelSchema

__all__ = ["ThreediDatabase"]


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Switch on legacy_alter_table setting to fix our migrations.

    Why?
    1) SQLite does not support "DROP COLUMN ...". You have to create a new table,
       copy the data, drop the old table, then rename. Luckily Alembic supports this pattern.
       They call it a "batch operation". See https://alembic.sqlalchemy.org/en/latest/batch.html.
    2) Newer SQLite drivers do a lot of fancy checks on a RENAME command. This made our
       "batch operations" fail in case a view referred to the table that is getting a "batch operation".
       The solution was a PRAGMA command. See https://www.sqlite.org/pragma.html#pragma_legacy_alter_table.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA legacy_alter_table=ON")
    # Some additional pragmas recommended in https://www.sqlite.org/security.html, paragraph 1.2
    cursor.execute("PRAGMA cell_size_check=ON")
    cursor.execute("PRAGMA mmap_size=0")
    cursor.close()


def load_spatialite(dbapi_conn, connection_record):
    """Load SpatiaLite extension in SQLite DB.

    The path to the SpatiaLite module should be set in the `SPATIALITE_LIBRARY_PATH` environment
    variable.
    """

    spatialite_library_path = os.environ.get(
        "SPATIALITE_LIBRARY_PATH", "mod_spatialite"
    )
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.load_extension(spatialite_library_path)
    dbapi_conn.enable_load_extension(False)
    try:
        databases = [
            i[-1].endswith(".gpkg")
            for i in dbapi_conn.execute("PRAGMA database_list;").fetchall()
        ]
        is_gpkg = any(databases)
    except Exception:
        is_gpkg = False
    if is_gpkg:
        dbapi_conn.execute("SELECT AutoGpkgStart();")
        dbapi_conn.execute("SELECT EnableGpkgAmphibiousMode();")


class ThreediDatabase:
    def __init__(self, path, echo=False):
        self.path = path
        self.echo = echo

        self._engine = None
        self._base_metadata = None

    @property
    def schema(self):
        return ModelSchema(self)

    @property
    def engine(self):
        return self.get_engine()

    @property
    def base_path(self):
        return Path(self.path).absolute().parent

    def get_engine(self, get_seperate_engine=False):
        if self._engine is None or get_seperate_engine:
            if self.path == "":
                # Special case in-memory SQLite:
                # https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#threading-pooling-behavior
                poolclass = None
            else:
                poolclass = NullPool
            engine = create_engine(
                "sqlite:///{0}".format(self.path), echo=self.echo, poolclass=poolclass
            )
            listen(engine, "connect", load_spatialite)
            if get_seperate_engine:
                return engine
            else:
                self._engine = engine

        return self._engine

    def get_session(self, **kwargs):
        """Get a SQLAlchemy session for optimal control.

        It is probably necessary to call ``session.commit``, ``session.rollback``
        and/or ``session.close``.

        See also:
          https://docs.sqlalchemy.org/en/13/orm/session_basics.html
        """
        return sessionmaker(bind=self.engine)(**kwargs)

    @contextmanager
    def session_scope(self, **kwargs):
        """Get a session to execute a single transaction in a "with as" block."""
        session = self.get_session(**kwargs)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def file_transaction(self, start_empty=False):
        """Copy the complete database into a tmpdir and work on that one.

        On contextmanager exit, the database is copied back and the real
        database is overwritten. On error, nothing happens.
        """
        if self._engine is not None:
            self._engine.dispose()
        with tempfile.TemporaryDirectory() as tempdir:
            work_file = Path(tempdir) / f"work-{uuid.uuid4()}{Path(self.path).suffix}"
            # copy the database to the temporary directory
            if not start_empty:
                shutil.copy(self.path, str(work_file))
            # yield a new ThreediDatabase refering to the backup
            try:
                yield self.__class__(str(work_file), echo=self.echo)
            except Exception as e:
                raise e
            else:
                shutil.copy(str(work_file), self.path)

    def check_connection(self):
        """Check if there a connection can be started with the database

        :return: True if a connection can be established, otherwise raises an
            appropriate error.
        """
        session = self.get_session()
        r = session.execute(text("select 1"))
        return r.fetchone()

    def check_integrity(self):
        """Should be called before doing anything with an untrusted sqlite file."""
        with self.session_scope() as session:
            session.execute(text("PRAGMA integrity_check"))

    def has_table(self, name):
        engine = self.get_engine()
        try:
            # SQLAlchemy >= 1.4
            return inspect(engine).has_table(name)
        except AttributeError:  # SQLAlchemy < 1.4
            return engine.has_table(name)
