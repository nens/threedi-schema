import subprocess
import warnings

# This import is needed for alembic to recognize the geopackage dialect
import geoalchemy2.alembic_helpers  # noqa: F401
from alembic import command as alembic_command
from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Column, Integer, MetaData, Table, text
from sqlalchemy.exc import IntegrityError

from ..domain import constants, models, views
from ..infrastructure.spatial_index import ensure_spatial_indexes
from ..infrastructure.spatialite_versions import copy_models, get_spatialite_version
from ..infrastructure.views import recreate_views
from .errors import MigrationMissingError, UpgradeFailedError

__all__ = ["ModelSchema"]


def get_alembic_config(engine=None, unsafe=False):
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "threedi_schema:migrations")
    alembic_cfg.set_main_option("version_table", constants.VERSION_TABLE_NAME)
    if engine is not None:
        alembic_cfg.attributes["engine"] = engine
    alembic_cfg.attributes["unsafe"] = unsafe
    return alembic_cfg


def get_schema_version():
    """Returns the version of the schema in this library"""
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)
    with EnvironmentContext(config=config, script=script) as env:
        return int(env.get_head_revision())


def _upgrade_database(db, revision="head", unsafe=True):
    """Upgrade ThreediDatabase instance"""
    engine = db.engine

    config = get_alembic_config(engine, unsafe=unsafe)
    alembic_command.upgrade(config, revision)


class ModelSchema:
    def __init__(self, threedi_db, declared_models=models.DECLARED_MODELS):
        self.db = threedi_db
        self.declared_models = declared_models

    def _get_version_old(self):
        """The version of the database using the old 'south' versioning."""
        south_migrationhistory = Table(
            "south_migrationhistory", MetaData(), Column("id", Integer)
        )
        engine = self.db.engine
        if not self.db.has_table("south_migrationhistory"):
            return
        with engine.connect() as connection:
            query = south_migrationhistory.select().order_by(
                south_migrationhistory.columns["id"].desc()
            )
            versions = list(connection.execute(query.limit(1)))
            if len(versions) == 1:
                return versions[0][0]
            else:
                return None

    def get_version(self):
        """Returns the id (integer) of the latest migration"""
        with self.db.engine.connect() as connection:
            context = MigrationContext.configure(
                connection, opts={"version_table": constants.VERSION_TABLE_NAME}
            )
            version = context.get_current_revision()
        if version is not None:
            return int(version)
        else:
            return self._get_version_old()

    def upgrade(
        self,
        revision="head",
        backup=True,
        set_views=True,
        upgrade_spatialite_version=False,
        convert_to_geopackage=False,
    ):
        """Upgrade the database to the latest version.

        This requires either a completely empty database or a database with its
        current schema version at least 174 (the latest migration of the old
        model databank).

        The upgrade is done using database transactions. However, for SQLite,
        database transactions are only partially supported. To ensure that the
        database file does not become corrupt, enable the "backup" parameter.
        If the database is temporary already (or if it is PostGIS), disable
        it.

        Specify 'set_views=True' to also (re)create views after the upgrade.
        This is not compatible when upgrading to a different version than the
        latest version.

        Specify 'upgrade_spatialite_version=True' to also upgrade the
        spatialite file version after the upgrade.

        Specify 'convert_to_geopackage=True' to also convert from spatialite
        to geopackage file version after the upgrade.
        """
        if (upgrade_spatialite_version or convert_to_geopackage) and not set_views:
            raise ValueError(
                "Cannot upgrade the spatialite version without setting the views."
            )
        v = self.get_version()
        if v is not None and v < constants.LATEST_SOUTH_MIGRATION_ID:
            raise MigrationMissingError(
                f"This tool cannot update versions below "
                f"{constants.LATEST_SOUTH_MIGRATION_ID}. Please consult the "
                f"3Di documentation on how to update legacy databases."
            )
        if set_views and revision not in ("head", get_schema_version()):
            raise ValueError(f"Cannot set views when upgrading to version '{revision}'")
        if backup:
            with self.db.file_transaction() as work_db:
                _upgrade_database(work_db, revision=revision, unsafe=True)
        else:
            _upgrade_database(self.db, revision=revision, unsafe=False)
        if upgrade_spatialite_version:
            self.upgrade_spatialite_version()
        elif convert_to_geopackage:
            self.convert_to_geopackage()
        elif set_views:
            self.set_views()

    def validate_schema(self):
        """Very basic validation of 3Di schema.

        Check that the database has the latest migration applied. If the
        latest migrations is applied, we assume the database also contains all
        tables and columns defined in threedi_model.models.py.

        :return: True if the threedi_db schema is valid, raises an error otherwise.
        :raise MigrationMissingError, MigrationTooHighError
        """
        version = self.get_version()
        schema_version = get_schema_version()
        if version is None or version < schema_version:
            raise MigrationMissingError(
                f"This tool requires at least schema version "
                f"{schema_version}. Current version: {version}."
            )

        if version > schema_version:
            warnings.warn(
                f"The database version is higher than the threedi-schema version "
                f"({version} > {schema_version}). This may lead to unexpected "
                f"results. "
            )
        return True

    def set_views(self):
        """(Re)create views in the spatialite according to the latest definitions."""
        version = self.get_version()
        schema_version = get_schema_version()
        if version != schema_version:
            raise MigrationMissingError(
                f"Setting views requires schema version "
                f"{schema_version}. Current version: {version}."
            )

        _, file_version = get_spatialite_version(self.db)

        recreate_views(self.db, file_version, views.ALL_VIEWS, views.VIEWS_TO_DELETE)

    def set_spatial_indexes(self):
        """(Re)create spatial indexes in the spatialite according to the latest definitions."""
        version = self.get_version()
        schema_version = get_schema_version()
        if version != schema_version:
            raise MigrationMissingError(
                f"Setting views requires schema version "
                f"{schema_version}. Current version: {version}."
            )

        ensure_spatial_indexes(self.db, models.DECLARED_MODELS)

    def upgrade_spatialite_version(self):
        """Upgrade the version of the spatialite file to the version of the
        current spatialite library.

        Does nothing if the current file version > 3 or if the current library
        version is not 4 or 5.

        Raises UpgradeFailedError if there are any SQL constraints violated.
        """
        lib_version, file_version = get_spatialite_version(self.db)
        if file_version == 3 and lib_version in (4, 5):
            self.validate_schema()

            with self.db.file_transaction(start_empty=True) as work_db:
                _upgrade_database(work_db, revision="head", unsafe=True)
                recreate_views(
                    work_db,
                    file_version=4,
                    all_views=views.ALL_VIEWS,
                    views_to_delete=views.VIEWS_TO_DELETE,
                )

                try:
                    copy_models(self.db, work_db, self.declared_models)
                except IntegrityError as e:
                    raise UpgradeFailedError(e.orig.args[0])

    def convert_to_geopackage(self):
        """
        Convert spatialite to geopackage

        Does nothing if the current database is already a geopackage

        """
        # TODO: work with temp db!
        if self.db.get_engine().dialect.name == "geopackage":
            return
        # Ensure database is upgraded and views are recreated
        # check: do these views work and do we want to keep them
        self.upgrade()
        self.validate_schema()
        # remove spatialite specific tables that break conversion
        with self.db.get_session() as session:
            session.execute(text("DROP TABLE IF EXISTS spatialite_history;"))
            session.execute(text("DROP TABLE IF EXISTS views_geometry_columns;"))
        cmd = [
            "ogr2ogr",
            "-f",
            "gpkg",
            str(self.db.path.with_suffix(".gpkg")),
            str(self.db.path),
            "-oo",
            "LIST_ALL_TABLES=YES",
        ]
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1
        )
        _, err = p.communicate()
        # ogr2ogr raises an error while the conversion is fine
        # so to catch any real issues we compare the produced error with the expected error
        expected_error = b'ERROR 1: sqlite3_exec(CREATE TABLE "sqlite_sequence" ( "rowid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "name" TEXT, "seq" TEXT)) failed: object name reserved for internal use: sqlite_sequence\n'
        if err != expected_error:
            raise RuntimeError(f"ogr2ogr didn't finish as expected:\n{err}")
        # correct database path
        self.db.path = self.db.path.with_suffix(".gpkg")
        # reset engine so new path is used on the next call of get_engine()
        self.db._engine = None
        # recreate views_geometry_columns so set_views works as expected
        with self.db.get_session() as session:
            session.execute(
                text(
                    "CREATE TABLE views_geometry_columns(view_name TEXT, view_geometry TEXT, view_rowid TEXT, f_table_name VARCHAR(256), f_geometry_column VARCHAR(256))"
                )
            )
        self.set_views()
