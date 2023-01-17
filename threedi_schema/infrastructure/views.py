__all__ = ["recreate_views"]


def recreate_views(db, file_version, all_views, views_to_delete):
    """Recreate predefined views in a ThreediDatabase instance"""
    engine = db.get_engine()

    with engine.begin() as connection:
        for (name, view) in all_views.items():
            connection.execute(f"DROP VIEW IF EXISTS {name}")
            connection.execute(
                f"DELETE FROM views_geometry_columns WHERE view_name = '{name}'"
            )
            connection.execute(f"CREATE VIEW {name} AS {view['definition']}")
            if file_version == 3:
                connection.execute(
                    f"INSERT INTO views_geometry_columns (view_name, view_geometry,view_rowid,f_table_name,f_geometry_column) VALUES('{name}', '{view['view_geometry']}', '{view['view_rowid']}', '{view['f_table_name']}', '{view['f_geometry_column']}')"
                )
            else:
                connection.execute(
                    f"INSERT INTO views_geometry_columns (view_name, view_geometry,view_rowid,f_table_name,f_geometry_column,read_only) VALUES('{name}', '{view['view_geometry']}', '{view['view_rowid']}', '{view['f_table_name']}', '{view['f_geometry_column']}', 0)"
                )
        for name in views_to_delete:
            connection.execute(f"DROP VIEW IF EXISTS {name}")
            connection.execute(
                f"DELETE FROM views_geometry_columns WHERE view_name = '{name}'"
            )
