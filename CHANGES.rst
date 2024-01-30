Changelog of threedi-schema
===================================================

0.219.1 (2024-01-30)
--------------------

- Fix migration to nullable friction_value that resulted in string type for friction_value.
- Update action versions to use a new NodeJS.
- Make CrossSectionLocation.friction_value nullable


0.218.0 (2024-01-08)
--------------------

- Add parameters vegetation_stem_density, vegetation_stem_diameter, vegetation_height and vegetation_drag_coefficient to CrossSectionLocation
- Add parameters friction_values, vegetation_stem_densities, vegetation_stem_diameters, vegetation_heights and vegetation_drag_coefficients to CrossSectionDefinition


0.217.13 (2023-10-02)
---------------------

- Change set_gate_height to set_gate_level


0.217.12 (2023-10-02)
---------------------

- Add set_gate_height to control structure options.

- Set timed control column restrictions similar to table control.


0.217.11 (2023-09-19)
---------------------

- Fix conveyance values list.


0.217.10 (2023-09-19)
---------------------

- Unmark conveyance columns as beta.
- Move zest.releaser config to pyproject.toml.


0.217.9 (2023-08-16)
--------------------

- Fix incorrectly formatted beta_features.py.


0.217.8 (2023-08-15)
--------------------

- Mark friction types with conveyance as beta features.


0.217.7 (2023-07-28)
--------------------

- Don't set journal_mode to MEMORY since it causes the schema version
  field to not be updated, making migrations crash.


0.217.6 (2023-07-13)
--------------------

- Extend FrictionType enum with Chézy friction with conveyance and
  Manning friction with conveyance.


0.217.5 (2023-06-15)
--------------------

- Fixed set_views (spatialite metadata tables wwere not updated).


0.217.4 (2023-06-15)
--------------------

- Fix SQLAlchemy engine and connection usage.

- Do not pool connections (solving file permission denied issues on Windows).


0.217.3 (2023-06-12)
--------------------

- Added groundwater 1D2D columns to the views.


0.217.2 (2023-05-24)
--------------------

- Remove vegetation and groundwater settings from beta features, since they are going to be released.


0.217.1 (2023-05-17)
--------------------

- Rewrite release workflow to use a supported github action for github release.
- Build the threedi-schema release with the build package instead of setuptools.


0.217.0 (2023-05-08)
--------------------

- Rename vegetation columns to match raster options.


0.216.4 (2023-04-11)
--------------------

- Fixed libspatialite 4.3 incompatibility (introduced in 0.216.3).


0.216.3 (2023-04-04)
--------------------

- Fixed DROP TABLE in migration 214 (tables "v2_connected_pnt", "v2_calculation_point",
  "v2_levee" remained present). The DROP TABLE is emitted again in migration 216.


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
