Changelog of threedi-schema
===================================================

0.216.2 (2023-03-24)
--------------------

- Remove groundwater columns from beta columns for 1d boundary conditions.
- Check on vegetation drag settings id in global settings instead of vegetation drag id for beta columns.


0.216.1 (2023-03-23)
--------------------

- Add beta_features.py to contain a list of spatialite columns and values for columns still in beta status.


0.216.0 (2023-03-15)
--------------------

- Add v2_vegation_drag table.
- Add 1D2D groundwater attributes to Pipes, Channels and Manholes


0.214.6 (2023-03-13)
--------------------

- Make timeseries non-nullable for BoundaryCondition1D and BoundaryConditions2D.


0.214.5 (2023-02-16)
--------------------

- Add SQLAlchemy 2.0 support and drop 1.3 support.


0.214.4 (2023-01-31)
--------------------

- Properly cleanup geo-tables in migration 214.


0.214.3 (2023-01-19)
--------------------

- Adapted versioning: prefix existing versions with 0.

- Fixed deprecation warnings of Geoalchemy2 0.13.0


0.214.2 (2023-01-17)
--------------------

- Fixed packaging (also include migrations).


0.214.1 (2023-01-17)
--------------------

- Fixed packaging.


0.214.0 (2023-01-17)
--------------------

- Initial project structure created with cookiecutter and
  https://github.com/nens/cookiecutter-python-template

- Ported code from threedi-modelchecker, rearranged into
  'domain', 'application', 'infrastructure', 'migrations'.
