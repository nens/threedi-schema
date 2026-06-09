class MigrationMissingError(Exception):
    """Raised when 3Di model is missing migrations."""

    pass


class UpgradeFailedError(Exception):
    """Raised when an upgrade() fails"""


class InvalidSRIDException(Exception):
    def __init__(self, epsg_code, issue=None):
        msg = f"Cannot migrate schematisation with model_settings.epsg_code={epsg_code}"
        if issue is not None:
            msg += f"; {issue}"
        super().__init__(msg)


class SchemaStructureError(Exception):
    """Raised when expected tables or columns are missing from the database.

    Attributes:
        missing_tables: List of table names that are missing from the database.
        missing_columns: Dict mapping table name to list of missing column names.
    """

    def __init__(self, missing_tables=None, missing_columns=None):
        parts = ["Database schema structure is incomplete."]

        if missing_tables:
            parts.append(f"\nMissing tables ({len(missing_tables)}):")
            for table in sorted(missing_tables):
                parts.append(f"\n  - {table}")

        if missing_columns:
            parts.append(f"\nMissing columns in {len(missing_columns)} table(s):")
            for table in sorted(missing_columns.keys()):
                cols = sorted(missing_columns[table])
                parts.append(f"\n  - {table}: {', '.join(cols)}")

        parts.append("\nThe database may need to be upgraded or repaired.")

        super().__init__("".join(parts))
