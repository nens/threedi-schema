Changelog of threedi-schema
===================================================


0.300.29 (unreleased)
---------------------

- Nothing changed yet.


0.300.28 (2025-07-25)
---------------------

- Add fix to migration 300 to fix setting of use_0d_inflow > 1 in migration 223 (#234)


0.300.27 (2025-05-20)
---------------------

- Fix migration (223) for schematisations where id 101-115 is already present in v2_surface_parameters (#229)


0.300.26 (2025-04-10)
---------------------

- Fix pyproject.toml.


0.300.25 (2025-04-10)
---------------------

- Fix mistake in pattern matching for old index tables to be deleted.


0.300.24 (2025-04-09)
---------------------

- Delete spatialite after conversion to geopackage


0.300.23 (2025-04-03)
---------------------

- set SewerageType to be Integer instead of IntegerEnum


0.300.22 (2025-03-27)
---------------------


- Fix upgrade progress tracking


0.300.21 (2025-03-26)
---------------------

- Add migration step description to upgrade progress tracking


0.300.20 (2025-03-25)
---------------------

- Fix progress tracking for upgrade to be continuous


0.300.19 (2025-03-17)
---------------------

- Add display_name to CrossSectionLocation
- Add display_name and code to Windshielding1D


0.300.18 (2025-03-12)
---------------------

- Read EPSG code for geopackage schematisations using gdal ogr (this also works on empy schematisations)


0.300.17 (2025-03-11)
---------------------

- Fix progress handler for upgrades with 0 steps


0.300.16 (2025-03-11)
---------------------

- Move InvalidSRIDException to application.errors


0.300.15 (2025-03-11)
---------------------

- Fix incorrect geometry in measure_location table in migration 0224
- Correct names of several migrations
- Convert ModelSchema.db.path to pathlib.Path in ModelSchema._get_dem_epsg()


0.300.14 (2025-03-05)
---------------------

- Ensure linestrings are valid (length > 0) after crs transformation


0.300.13 (2025-03-05)
---------------------

- Add ModelSchema._get_dem_epsg() to fetch EPSG from DEM.


0.300.12 (2025-02-27)
---------------------

- Delete temporary model settings row after it is set for the EPSG code


0.300.11 (2025-02-20)
---------------------

- Fix EPSG code setting on empty databases


0.300.10 (2025-02-18)
---------------------

- schema.epsg_code returns None if EPSG code could not be determined from database


0.300.9 (2025-02-18)
--------------------

- Make schema.epsg_code work for all migration versions.
  Raises threedi_schema.migrations.exceptions.InvalidSRIDException if the epsg_code is unusable or not set.

0.300.8 (2025-02-11)
--------------------

- Preserve ID column in non-geometry tables


0.300.7 (2025-02-11)
--------------------

- Add total discharge boundary types (TOTAL_DISCHARGE_2D, GROUNDWATER_TOTAL_DISCHARGE_2D)


0.300.6 (2025-01-31)
--------------------

- Add spatial_ref_sys view to geopackage so ST_Transform can be used


0.300.5 (2025-01-30)
--------------------

- Fix bug in upgrading logic that causes upgrading with gpkg to fail


0.300.4 (2025-01-30)
--------------------

- Fix migration starting from geopackage
- Set autoincrement for primary keys in models


0.300.3 (2025-01-28)
--------------------

- Fix setting surface_parameters_id


0.300.2 (2025-01-27)
--------------------

- Fix typo in warning handling on convert to geopackge
- Set default visualisation of connection_node to -1
- Fix geom for pump in migration 228


0.300.1 (2025-01-24)
--------------------

- Fix incorrect naming of table Tags as tag instead of tags in migration 223


0.300.0 (2025-01-24)
--------------------

- Convert spatialite to geopackage during upgrade


0.230.3 (2025-01-23)
--------------------

- Fix invalid setting of geometry types for lateral_2d and boundary_condition_2d


0.230.2 (2025-01-23)
--------------------

- Modify model names such that sqlite table names match to model names


0.230.1 (2025-01-21)
--------------------

- Fix invalid geometry types for measure_map, memory_control and table_control


0.230.0 (2025-01-16)
--------------------

- Reproject all geometries to the srid in model_settings.epsg_code
- Remove model_settings.epsg_code


0.229.2 (2025-01-16)
--------------------

- Rewrite geopackage conversion to use gdal.VectorTranslate instead of ogr2ogr


0.229.1 (2025-01-15)
--------------------

- Fix setting of geometry columns for revision 223 and 228
- Fix incorrect creation of geometry for dry weather flow and surface during migration


0.229.0 (2025-01-08)
--------------------

- Rename sqlite table "tags" to "tag"
- Remove indices referring to removed tables in previous migrations
- Make model_settings.use_2d_rain and model_settings.friction_averaging booleans
- Remove columns referencing v2 in geometry_column
- Ensure correct use_* values when matching tables have no data
- Use custom types for comma separated and table text fields to strip extra white space
- Correct direction of dwf and surface map
- Remove v2 related views from sqlite


0.228.4 (2025-01-10)
--------------------

- Fix incorrectly setting of geometry for pipe, weir and orifice in migration
- Fix issue where invalid geometries broke migration 228 for culverts


0.228.3 (2024-12-10)
--------------------

- Fix issue with incorrect types of migrated cross_section_width and height that broke the spatialite upgrade


0.228.2 (2024-12-04)
--------------------

- Significantly speed up migration to schema 228 for schematisations with many 1D components
- Remove support for python 3.8 and require python 3.9 as minimal version
- Add tags column to cross_section_location and windshielding_1d


0.228.1 (2024-11-26)
--------------------

- Add `progress_func` argument to schema.upgrade


0.228.0 (2024-11-25)
--------------------

- Implement changes for schema version 300 concerning 1D
- Remove v2 prefix from table names v2_channel, v2_windshielding, v2_cross_section_location, v2_pipe, v2_culvert` v2_orifice and v2_weir
- Move data from v2_cross_section_definition to linked tables (cross_section_location, pipe, culvert, orifice and weir)
- Move data from v2_manhole to connection_nodes and remove v2_manhole table
- Rename v2_pumpstation to pump and add table pump_map that maps the end nodes to pumps
- Remove tables v2_floodfill and v2_cross_section_definition


0.227.3 (2024-11-04)
--------------------

- Extend list of file paths that are replaced with the file name with the files in vegetation_drag_2d"


0.227.2 (2024-10-23)
--------------------

- Fix setting of model_settings.use_interception in migration to 0.222


0.227.1 (2024-10-21)
--------------------

- Propagate changes from 0.226.7


0.227.0 (2024-10-14)
--------------------

- Remove measure_variable column from tables memory_control and table_control
- Rename control_measure_map to measure_map and control_measure_location to measure_location


0.226.7 (2024-10-21)
--------------------

- Add several models that where missing in DECLARED_MODELS


0.226.6 (2024-10-03)
--------------------

- Copy id column when renaming tables.


0.226.5 (2024-09-30)
--------------------

- Prevent migrations 225 and 226 from failing when any of the new table names already exists
- Propagate changes from 0.225.6.


0.226.4 (2024-09-25)
--------------------

- Propagate fixes from 224.


0.226.3 (2024-09-24)
--------------------

- Propagate fixes from 224.5


0.226.2 (2024-09-23)
--------------------

- Release including fixes for 0.224.4 and 0.225.3


0.226.1 (2024-09-12)
--------------------

- Set type of dry_weather_flow.dry_weather_flow_distribution_id to integer (https://github.com/nens/threedi-schema/pull/90)


0.226.0 (2024-09-10)
--------------------

- Implement changes for schema version 300 concerning 2d and 1d2d
- Renamed v2_dem_average_area to dem_average_area, v2_exchange_line to echange_line,
  v2_grid_refinement to grid_refinement_line, v2_grid_refinement_area to grid_refinement_area,
  v2_obstacle to obstacle and v2_potential_breach to potential_breach
- Ensure that all these tables have a geom, code, display_name and tags column
- Ensure that all columns except for geom are nullable
- Rename refinement_level to grid_level in grid_refinement_line and grid_refinement_area
- Rename potential_breach.exchange_level to initial_exchange_level
- Remove potential_breach.maximum_breach_depth and set maximum_breach_depth.final_exchange_level to exchange_level - maximum_breach_depth


0.225.6 (2024-09-30)
--------------------

- Fix incorrect left join in migration 0.225.0


0.225.5 (2024-09-25)
--------------------

- Propagate fixes from 224.6


0.225.4 (2024-09-24)
--------------------

- Propagate fixes from 224.5


0.225.3 (2024-09-23)
--------------------

- Use unique name for temp tables in migrations


0.225.2 (2024-09-12)
--------------------

- Set type of dry_weather_flow.dry_weather_flow_distribution_id to integer (https://github.com/nens/threedi-schema/pull/90)


0.225.1 (2024-09-09)
--------------------

- Create enum for 1d_advection_type and use use that for PhysicalSettings.use_advection_1d


0.225.0 (2024-09-09)
--------------------

- Rename v2_1d_boundary_conditions and v2_2d_boundary_conditions to boundary_condition_1d and boundary_condition_2d.

- Rename v2_1d_laterals and v2_2d_laterals to lateral_1d and lateral_2d.

- Rename the_geom to geom in boundary_condition_2d and lateral_2d, and add geom columns to boundary_condition_1d and lateral_1d.

- Drop all constraints on boundary condition and lateral tables, except NOT NULL constrains on id and geom.


0.224.7 (2024-09-30)
--------------------

- Prevent migration 222 to 224 from failing when any of the new table names already exists
- Swap start and end of control_measure_map geometries
- Modify geometry of controls associated with pumpstation to the pumpstation start node
- Ensure control_measure_map.geom is a valid line


0.224.6 (2024-09-25)
--------------------

- Ensure dry_weather_flow_map.geom and surface_map.geom are valid lines


0.224.5 (2024-09-24)
--------------------

- Do not migrate controls that refer to non-existing nodes


0.224.4 (2024-09-23)
--------------------

- Use unique name for temp tables in migrations


0.224.3 (2024-09-12)
--------------------

- Set type of dry_weather_flow.dry_weather_flow_distribution_id to integer


0.224.2 (2024-09-05)
--------------------

- Change names of aggregation_settings.flow_variable to match threedigrid
- Make renaming raster paths more resilient
- Fix setting default values in dry_weather_flow and surface
- Actually set geom columns in dry_weather_flow_map and surface_map


0.224.1 (2024-09-02)
--------------------

- Fix creating control_measure_map.geom in 224 migration
- Handle created Null geometries when migrating surface / impervious_surface
- Revert removing on customized load_spatialite function
- Remove unused columns from several settings tables
- Rename groundwater.equilibrium_infiltration_rate_type to equilibrium_infiltration_rate_aggregation
- Rename control_measure_location.object_id to connection_node_id
- Replace paths to raster files with the file name


0.224.0 (2024-08-16)
--------------------

- Implement changes for schema version 300 concerning structure control.
- Simplify schema to four tables (`control_measure_location`, `control_measure_map`, `memory_control` and `table_control`) and removing tables `v2_control`, `v2_control_delta`, `v2_control_measure_group`, `v2_control_measure_map` and `v2_control_pid`.
- Removed time control and corresponding table (`v2_control_timed`).
- Add geometries to all four tables (with optional display name and tags).
- A full overview can be obtained from the migration code (`threedi_schema/migrations/versions/0224_db_upgrade_structure_control.py`)


0.223 (2024-08-01)
------------------

- Implement changes for schema version 300 concerning inflow
- Replace v2_surface and v2_impervious_surface (and maps) with surface and dry_weather_flow tables
- Redistribute data from v2_surface or v2_impervious_surface, depending on simulation_template_settings.use_0d_inflow, over suface and dry_weather_flow tables
- Populate surface_parameters and dry_weather_flow_distribution tables with default data
- A full overview can be obtained from the migration code (`threedi_schema/migrations/versions/0223_upgrade_db_inflow.py`)


0.222.2 (2024-06-13)
--------------------

- Skip testing convert to geopackage


0.222.1 (2024-06-13)
--------------------

- Disable `convert_to_geopackage` in `schema.upgrade` for schema version before 300
- Ensure `revision` format in `schema.upgrade` is correctly formatted


0.222.0 (2024-05-22)
--------------------

- Implement changes for schema version 300 concerning simulation settings
- Reduce all settings tables to a single row. Multiple settings per schematisation are no longer allowed.
- A full overview can most easily be obtained from the migration code (`threedi_schema/migrations/versions/0222_upgrade_db_settings.py`); to summarize:
    - Rename settings tables from "v2_foo" to "foo"
    - Rename several columns in settings tables
    - Move settings to context specific tables instead of a single generic table


0.221 (2024-04-08)
------------------

- Remove column vegetation_drag_coeficients from v2_cross_section_location (sqlite only) that was added in migration 218

0.220 (2024-02-29)
------------------

- Add support for geopackage
- Remove `the_geom_linestring` from `v2_connection_nodes` because geopackage does not support multiple geometry objects in one table


0.219.3 (2024-04-16)
--------------------

- Fix not setting views when using upgrade with upgrade_spatialite_version=True on up to date spatialite


0.219.2 (2024-04-04)
--------------------

- Update v2_cross_section_location_view with vegetation columns


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
