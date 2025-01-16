import warnings
from pathlib import Path

# This import is needed for alembic to recognize the geopackage dialect
import geoalchemy2.alembic_helpers  # noqa: F401
from alembic import command as alembic_command
from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from osgeo import gdal
from sqlalchemy import Column, Integer, MetaData, Table, text
from sqlalchemy.exc import IntegrityError

from ..domain import constants, models
from ..infrastructure.spatial_index import ensure_spatial_indexes
from ..infrastructure.spatialite_versions import copy_models, get_spatialite_version
from .errors import MigrationMissingError, UpgradeFailedError
from .upgrade_utils import setup_logging

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


def _upgrade_database(db, revision="head", unsafe=True, progress_func=None):
    """Upgrade ThreediDatabase instance"""
    engine = db.engine
    config = get_alembic_config(engine, unsafe=unsafe)
    if progress_func is not None:
        setup_logging(db.schema, revision, config, progress_func)
    alembic_command.upgrade(config, revision)


class GdalErrorHandler:
    def __call__(self, err_level, err_no, err_msg):
        self.err_level = err_level
        self.err_no = err_no
        self.err_msg = err_msg


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
        upgrade_spatialite_version=False,
        convert_to_geopackage=False,
        progress_func=None,
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

        Specify 'upgrade_spatialite_version=True' to also upgrade the
        spatialite file version after the upgrade.

        Specify 'convert_to_geopackage=True' to also convert from spatialite
        to geopackage file version after the upgrade.

        Specify a 'progress_func' to handle progress updates. `progress_func` should
        expect a single argument representing the fraction of progress
        """
        try:
            rev_nr = get_schema_version() if revision == "head" else int(revision)
        except ValueError:
            raise ValueError(
                f"Incorrect version format: {revision}. Expected 'head' or a numeric value."
            )
        if convert_to_geopackage and rev_nr < 300:
            raise UpgradeFailedError(
                f"Cannot convert to geopackage for {revision=} because geopackage support is "
                "enabled from revision 300",
            )
        v = self.get_version()
        if v is not None and v < constants.LATEST_SOUTH_MIGRATION_ID:
            raise MigrationMissingError(
                f"This tool cannot update versions below "
                f"{constants.LATEST_SOUTH_MIGRATION_ID}. Please consult the "
                f"3Di documentation on how to update legacy databases."
            )
        if backup:
            with self.db.file_transaction() as work_db:
                _upgrade_database(
                    work_db, revision=revision, unsafe=True, progress_func=progress_func
                )
        else:
            _upgrade_database(
                self.db, revision=revision, unsafe=False, progress_func=progress_func
            )
        if upgrade_spatialite_version:
            self.upgrade_spatialite_version()
        elif convert_to_geopackage:
            self.convert_to_geopackage()

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
                try:
                    copy_models(self.db, work_db, self.declared_models)
                except IntegrityError as e:
                    raise UpgradeFailedError(e.orig.args[0])

    def convert_to_geopackage(self):
        """
        Convert spatialite to geopackage using gdal.VectorTranslate.

        Does nothing if the current database is already a geopackage.

        Raises UpgradeFailedError if the conversion of spatialite to geopackage with VectorTranslate fails.
        """

        handler = GdalErrorHandler()
        gdal.PushErrorHandler(handler)
        gdal.UseExceptions()

        warnings_list = []

        if self.db.get_engine().dialect.name == "geopackage":
            return

        # Ensure database is upgraded and views are recreated
        self.upgrade()
        self.validate_schema()
        # Make necessary modifications for conversion on temporary database
        with self.db.file_transaction(start_empty=False, copy_results=False) as work_db:
            # remove spatialite specific tables that break conversion
            with work_db.get_session() as session:
                session.execute(text("DROP TABLE IF EXISTS spatialite_history;"))
                session.execute(text("DROP TABLE IF EXISTS views_geometry_columns;"))

                all_tablenames = [model.__tablename__ for model in self.declared_models]
                geometry_tablenames = (
                    session.execute(text("SELECT f_table_name FROM geometry_columns;"))
                    .scalars()
                    .all()
                )
                non_geometry_tablenames = list(
                    set(all_tablenames) - set(geometry_tablenames)
                )

                if (
                    session.execute(
                        text(
                            "SELECT count(*) FROM sqlite_master WHERE name='schema_version';"
                        )
                    ).scalar()
                    > 0
                ):
                    non_geometry_tablenames.append("schema_version")

            infile = str(work_db.path)
            outfile = str(Path(self.db.path).with_suffix(".gpkg"))

            conversion_list = []
            conversion_list.append(
                gdal.VectorTranslateOptions(
                    format="gpkg",
                    skipFailures=True,
                )
            )
            for table in non_geometry_tablenames:
                conversion_list.append(
                    gdal.VectorTranslateOptions(
                        format="gpkg",
                        accessMode="update",
                        SQLStatement=f"SELECT * FROM {table}",
                        layerName=table,
                    )
                )
            for conversion_options in conversion_list:
                try:
                    ds = gdal.VectorTranslate(
                        destNameOrDestDS=outfile,
                        srcDS=infile,
                        options=conversion_options,
                    )
                    # dereference dataset before writing additional layers to ensure the data is written
                    del ds
                except RuntimeError as err:
                    raise UpgradeFailedError from err
                else:
                    if (
                        hasattr(handler, "err_level")
                        and handler.err_level >= gdal.CE_Warning
                    ):
                        warnings_list.append(handler.err_msg)

            if len(warnings_list) > 0:
                warning_string = "\n".join(
                    ["GeoPackage conversion didn't finish as expected:"] + warnings
                )
                warnings.warn(warning_string)

        # Correct path of current database
        self.db.path = Path(self.db.path).with_suffix(".gpkg")
        # Reset engine so new path is used on the next call of get_engine()
        self.db._engine = None
        # Recreate views_geometry_columns so set_views works as expected
        with self.db.get_session() as session:
            session.execute(
                text(
                    "CREATE TABLE views_geometry_columns(view_name TEXT, view_geometry TEXT, view_rowid TEXT, f_table_name VARCHAR(256), f_geometry_column VARCHAR(256))"
                )
            )
