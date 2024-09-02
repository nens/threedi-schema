from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

from . import constants
from .custom_types import Geometry, IntegerEnum, VarcharEnum

Base = declarative_base()  # automap_base()


class Lateral2D(Base):
    __tablename__ = "v2_2d_lateral"
    id = Column(Integer, primary_key=True)

    type = Column(IntegerEnum(constants.Later2dType), nullable=False)
    the_geom = Column(Geometry("POINT"), nullable=False)
    timeseries = Column(Text, nullable=False)


class BoundaryConditions2D(Base):
    __tablename__ = "v2_2d_boundary_conditions"
    id = Column(Integer, primary_key=True)

    display_name = Column(String(255))
    timeseries = Column(Text, nullable=False)
    boundary_type = Column(IntegerEnum(constants.BoundaryType), nullable=False)
    the_geom = Column(Geometry("LINESTRING"), nullable=False)


class ControlMeasureLocation(Base):
    __tablename__ = "control_measure_location"
    id = Column(Integer, primary_key=True)
    connection_node_id = Column(Integer)
    measure_variable = Column(VarcharEnum(constants.MeasureVariables))
    display_name = Column(Text)
    code = Column(Text)
    geom = Column(Geometry("POINT"), nullable=False)
    tags = Column(Text)


class ControlMeasureMap(Base):
    __tablename__ = "control_measure_map"
    id = Column(Integer, primary_key=True)
    control_measure_location_id = Column(Integer)
    control_type = Column(VarcharEnum(constants.ControlType), nullable=False)
    control_id = Column(Integer)
    weight = Column(Float)
    display_name = Column(Text)
    code = Column(Text)
    geom = Column(Geometry("LINESTRING"), nullable=False)
    tags = Column(Text)


class ControlMemory(Base):
    __tablename__ = "memory_control"
    id = Column(Integer, primary_key=True)
    measure_variable = Column(VarcharEnum(constants.MeasureVariables))
    upper_threshold = Column(Float)
    lower_threshold = Column(Float)
    action_type = Column(VarcharEnum(constants.ControlTableActionTypes))
    action_value_1 = Column(Float)
    action_value_2 = Column(Float)
    target_type = Column(VarcharEnum(constants.StructureControlTypes))
    target_id = Column(Integer)
    is_active = Column(Boolean)
    is_inverse = Column(Boolean)
    display_name = Column(Text)
    code = Column(Text)
    geom = Column(Geometry("POINT"), nullable=False)
    tags = Column(Text)


class ControlTable(Base):
    __tablename__ = "table_control"
    id = Column(Integer, primary_key=True)
    action_table = Column(Text)
    action_type = Column(VarcharEnum(constants.ControlTableActionTypes))
    measure_variable = Column(VarcharEnum(constants.MeasureVariables))
    measure_operator = Column(VarcharEnum(constants.MeasureOperators))
    target_type = Column(VarcharEnum(constants.StructureControlTypes))
    target_id = Column(Integer, nullable=False)
    display_name = Column(Text)
    code = Column(Text)
    geom = Column(Geometry("POINT"), nullable=False)
    tags = Column(Text)


class Floodfill(Base):
    __tablename__ = "v2_floodfill"
    id = Column(Integer, primary_key=True)
    waterlevel = Column(Float)
    the_geom = Column(Geometry("POINT"))


class Interflow(Base):
    __tablename__ = "interflow"
    id = Column(Integer, primary_key=True)
    interflow_type = Column(IntegerEnum(constants.InterflowType))
    porosity = Column(Float)
    porosity_file = Column(String(255))
    porosity_layer_thickness = Column(Float)
    impervious_layer_elevation = Column(Float)
    hydraulic_conductivity = Column(Float)
    hydraulic_conductivity_file = Column(String(255))


class SimpleInfiltration(Base):
    __tablename__ = "simple_infiltration"
    id = Column(Integer, primary_key=True)
    infiltration_rate = Column(Float)
    infiltration_rate_file = Column(String(255))
    infiltration_surface_option = Column(
        IntegerEnum(constants.InfiltrationSurfaceOption)
    )
    max_infiltration_volume = Column(Float)
    max_infiltration_volume_file = Column(Text)

    # Alias needed for API compatibility
    @property
    def max_infiltration_capacity_file(self):
        return self.max_infiltration_volume_file


class SurfaceParameter(Base):
    __tablename__ = "surface_parameters"
    id = Column(Integer, primary_key=True)
    outflow_delay = Column(Float, nullable=False)
    surface_layer_thickness = Column(Float, nullable=False)
    infiltration = Column(Boolean, nullable=False)
    max_infiltration_capacity = Column(Float, nullable=False)
    min_infiltration_capacity = Column(Float, nullable=False)
    infiltration_decay_constant = Column(Float, nullable=False)
    infiltration_recovery_constant = Column(Float, nullable=False)
    tags = Column(Text)
    description = Column(Text)


class Surface(Base):
    __tablename__ = "surface"
    id = Column(Integer, primary_key=True)
    code = Column(String(100))
    display_name = Column(String(255))
    area = Column(Float)
    surface_parameters_id = Column(
        Integer, ForeignKey(SurfaceParameter.__tablename__ + ".id"), nullable=False
    )
    geom = Column(
        Geometry("POLYGON"),
        nullable=True,
    )
    tags = Column(Text)


class DryWeatherFlow(Base):
    __tablename__ = "dry_weather_flow"
    id = Column(Integer, primary_key=True)
    multiplier = Column(Float)
    dry_weather_flow_distribution_id = Column(Text)
    daily_total = Column(Float)
    interpolate = Column(Boolean)
    display_name = Column(String(255))
    code = Column(String(100))
    geom = Column(
        Geometry("POLYGON"),
        nullable=False,
    )
    tags = Column(Text)


class DryWeatherFlowMap(Base):
    __tablename__ = "dry_weather_flow_map"
    id = Column(Integer, primary_key=True)
    connection_node_id = Column(Integer)
    dry_weather_flow_id = Column(Integer)
    display_name = Column(String(255))
    code = Column(String(100))
    geom = Column(
        Geometry("LINESTRING"),
        nullable=False,
    )
    percentage = Column(Float)
    tags = Column(Text)


class DryWeatherFlowDistribution(Base):
    __tablename__ = "dry_weather_flow_distribution"
    id = Column(Integer, primary_key=True)
    description = Column(Text)
    tags = Column(Text)
    distribution = Column(Text)


class GroundWater(Base):
    __tablename__ = "groundwater"
    id = Column(Integer, primary_key=True)

    groundwater_impervious_layer_level = Column(Float)
    groundwater_impervious_layer_level_file = Column(String(255))
    groundwater_impervious_layer_level_aggregation = Column(
        IntegerEnum(constants.InitializationType)
    )
    phreatic_storage_capacity = Column(Float)
    phreatic_storage_capacity_file = Column(String(255))
    phreatic_storage_capacity_aggregation = Column(
        IntegerEnum(constants.InitializationType)
    )
    equilibrium_infiltration_rate = Column(Float)
    equilibrium_infiltration_rate_file = Column(String(255))
    equilibrium_infiltration_rate_aggregation = Column(
        IntegerEnum(constants.InitializationType)
    )
    initial_infiltration_rate = Column(Float)
    initial_infiltration_rate_file = Column(String(255))
    initial_infiltration_rate_aggregation = Column(
        IntegerEnum(constants.InitializationType)
    )
    infiltration_decay_period = Column(Float)
    infiltration_decay_period_file = Column(String(255))
    infiltration_decay_period_aggregation = Column(
        IntegerEnum(constants.InitializationType)
    )
    groundwater_hydraulic_conductivity = Column(Float)
    groundwater_hydraulic_conductivity_file = Column(String(255))
    groundwater_hydraulic_conductivity_aggregation = Column(
        IntegerEnum(constants.InitializationType)
    )
    leakage = Column(Float)
    leakage_file = Column(String(255))

    # Alias needed for API compatibility
    @property
    def groundwater_hydro_connectivity_file(self):
        return self.groundwater_hydraulic_conductivity_file


class GridRefinement(Base):
    __tablename__ = "v2_grid_refinement"
    id = Column(Integer, primary_key=True)

    display_name = Column(String(255))
    refinement_level = Column(Integer, nullable=False)
    the_geom = Column(Geometry("LINESTRING"), nullable=False)
    code = Column(String(100))


class GridRefinementArea(Base):
    __tablename__ = "v2_grid_refinement_area"
    id = Column(Integer, primary_key=True)
    display_name = Column(String(255))
    refinement_level = Column(Integer, nullable=False)
    code = Column(String(100))
    the_geom = Column(Geometry("POLYGON"), nullable=False)


class CrossSectionDefinition(Base):
    __tablename__ = "v2_cross_section_definition"
    id = Column(Integer, primary_key=True)
    width = Column(String(255))
    height = Column(String(255))
    shape = Column(IntegerEnum(constants.CrossSectionShape))
    code = Column(String(100))
    friction_values = Column(String)
    vegetation_stem_densities = Column(String)
    vegetation_stem_diameters = Column(String)
    vegetation_heights = Column(String)
    vegetation_drag_coefficients = Column(String)


class ConnectionNode(Base):
    __tablename__ = "v2_connection_nodes"
    id = Column(Integer, primary_key=True)
    storage_area = Column(Float)
    initial_waterlevel = Column(Float)
    the_geom = Column(Geometry("POINT"), nullable=False)
    code = Column(String(100))

    manholes = relationship("Manhole", back_populates="connection_node")
    boundary_conditions = relationship(
        "BoundaryCondition1D", back_populates="connection_node"
    )
    laterals1d = relationship("Lateral1d", back_populates="connection_node")


class Lateral1d(Base):
    __tablename__ = "v2_1d_lateral"
    id = Column(Integer, primary_key=True)
    connection_node_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    timeseries = Column(Text, nullable=False)
    connection_node = relationship(ConnectionNode, back_populates="laterals1d")


class Manhole(Base):
    __tablename__ = "v2_manhole"

    id = Column(Integer, primary_key=True)
    display_name = Column(String(255))
    code = Column(String(100))
    zoom_category = Column(IntegerEnum(constants.ZoomCategories))
    shape = Column(String(4))
    width = Column(Float)
    length = Column(Float)
    surface_level = Column(Float)
    bottom_level = Column(Float, nullable=False)
    drain_level = Column(Float)
    sediment_level = Column(Float)
    manhole_indicator = Column(Integer)
    calculation_type = Column(IntegerEnum(constants.CalculationTypeNode))
    exchange_thickness = Column(Float)
    hydraulic_conductivity_in = Column(Float)
    hydraulic_conductivity_out = Column(Float)

    connection_node_id = Column(
        Integer,
        ForeignKey(ConnectionNode.__tablename__ + ".id"),
        nullable=False,
        unique=True,
    )
    connection_node = relationship(ConnectionNode, back_populates="manholes")


class NumericalSettings(Base):
    __tablename__ = "numerical_settings"
    id = Column(Integer, primary_key=True)
    cfl_strictness_factor_1d = Column(Float)
    cfl_strictness_factor_2d = Column(Float)
    convergence_cg = Column(Float)
    convergence_eps = Column(Float)
    flow_direction_threshold = Column(Float)
    friction_shallow_water_depth_correction = Column(
        IntegerEnum(constants.FrictionShallowWaterDepthCorrection)
    )
    general_numerical_threshold = Column(Float)
    time_integration_method = Column(IntegerEnum(constants.IntegrationMethod))
    limiter_waterlevel_gradient_1d = Column(IntegerEnum(constants.OffOrStandard))
    limiter_waterlevel_gradient_2d = Column(IntegerEnum(constants.OffOrStandard))
    limiter_slope_crossectional_area_2d = Column(
        IntegerEnum(constants.LimiterSlopeXArea)
    )
    limiter_slope_friction_2d = Column(IntegerEnum(constants.OffOrStandard))
    max_non_linear_newton_iterations = Column(Integer)
    max_degree_gauss_seidel = Column(Integer)
    min_friction_velocity = Column(Float)
    min_surface_area = Column(Float)
    use_preconditioner_cg = Column(IntegerEnum(constants.OffOrStandard))
    preissmann_slot = Column(Float)
    pump_implicit_ratio = Column(Float)
    limiter_slope_thin_water_layer = Column(Float)
    use_of_cg = Column(Integer)
    use_nested_newton = Column(IntegerEnum(constants.OffOrStandard))
    flooding_threshold = Column(Float)


class VegetationDrag(Base):
    __tablename__ = "vegetation_drag_2d"
    id = Column(Integer, primary_key=True)

    vegetation_height = Column(Float)
    vegetation_height_file = Column(String(255))

    vegetation_stem_count = Column(Float)
    vegetation_stem_count_file = Column(String(255))

    vegetation_stem_diameter = Column(Float)
    vegetation_stem_diameter_file = Column(String(255))

    vegetation_drag_coefficient = Column(Float)
    vegetation_drag_coefficient_file = Column(String(255))


class ModelSettings(Base):
    __tablename__ = "model_settings"
    id = Column(Integer, primary_key=True)
    use_2d_flow = Column(Boolean)
    use_1d_flow = Column(Boolean)
    manhole_aboveground_storage_area = Column(Float)
    minimum_cell_size = Column(Float)
    calculation_point_distance_1d = Column(Float)
    nr_grid_levels = Column(Integer)
    minimum_table_step_size = Column(Float)
    maximum_table_step_size = Column(Float)
    dem_file = Column(String(255))
    friction_type = Column(IntegerEnum(constants.FrictionType))
    friction_coefficient = Column(Float)
    friction_coefficient_file = Column(String(255))
    embedded_cutoff_threshold = Column(Float)
    epsg_code = Column(Integer)
    max_angle_1d_advection = Column(Float)
    friction_averaging = Column(IntegerEnum(constants.OffOrStandard))
    table_step_size_1d = Column(Float)
    use_2d_rain = Column(Integer)
    use_interflow = Column(Boolean)
    use_interception = Column(Boolean)
    use_simple_infiltration = Column(Boolean)
    use_groundwater_flow = Column(Boolean)
    use_groundwater_storage = Column(Boolean)
    use_vegetation_drag_2d = Column(Boolean)

    # Alias needed for API compatibility
    @property
    def frict_coef_file(self):
        return self.friction_coefficient_file


class InitialConditions(Base):
    __tablename__ = "initial_conditions"
    id = Column(Integer, primary_key=True)
    initial_groundwater_level = Column(Float)
    initial_groundwater_level_file = Column(String(255))
    initial_groundwater_level_aggregation = Column(
        IntegerEnum(constants.InitializationType)
    )
    initial_water_level = Column(Float)
    initial_water_level_aggregation = Column(IntegerEnum(constants.InitializationType))
    initial_water_level_file = Column(String(255))

    # Alias needed for API compatibility
    @property
    def initial_waterlevel_file(self):
        return self.initial_water_level_file


class Interception(Base):
    __tablename__ = "interception"
    id = Column(Integer, primary_key=True)
    interception = Column(Float)
    interception_file = Column(String(255))


# class PhysicalSettings
class AggregationSettings(Base):
    __tablename__ = "aggregation_settings"
    id = Column(Integer, primary_key=True)
    flow_variable = Column(VarcharEnum(constants.FlowVariable))
    aggregation_method = Column(VarcharEnum(constants.AggregationMethod))
    interval = Column(Integer)


class PhysicalSettings(Base):
    __tablename__ = "physical_settings"
    id = Column(Integer, primary_key=True)
    use_advection_1d = Column(IntegerEnum(constants.OffOrStandard))
    use_advection_2d = Column(IntegerEnum(constants.OffOrStandard))


class SimulationTemplateSettings(Base):
    __tablename__ = "simulation_template_settings"
    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    use_0d_inflow = Column(IntegerEnum(constants.InflowType))
    use_structure_control = Column(Boolean)


class TimeStepSettings(Base):
    __tablename__ = "time_step_settings"
    id = Column(Integer, primary_key=True)
    time_step = Column(Float)
    min_time_step = Column(Float)
    max_time_step = Column(Float)
    output_time_step = Column(Float)
    use_time_step_stretch = Column(Boolean)


class BoundaryCondition1D(Base):
    __tablename__ = "v2_1d_boundary_conditions"

    id = Column(Integer, primary_key=True)
    boundary_type = Column(IntegerEnum(constants.BoundaryType), nullable=False)
    timeseries = Column(Text, nullable=False)

    connection_node_id = Column(
        Integer,
        ForeignKey(ConnectionNode.__tablename__ + ".id"),
        nullable=False,
        unique=True,
    )
    connection_node = relationship(
        ConnectionNode,
        foreign_keys=connection_node_id,
        back_populates="boundary_conditions",
    )


class SurfaceMap(Base):
    __tablename__ = "surface_map"
    id = Column(Integer, primary_key=True)
    surface_id = Column(Integer, nullable=False)
    connection_node_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    percentage = Column(Float)
    geom = Column(Geometry("LINESTRING"), nullable=False)
    tags = Column(Text)
    code = Column(String(100))
    display_name = Column(String(255))


class Channel(Base):
    __tablename__ = "v2_channel"
    id = Column(Integer, primary_key=True)
    display_name = Column(String(255))
    code = Column(String(100))
    calculation_type = Column(IntegerEnum(constants.CalculationType), nullable=False)
    dist_calc_points = Column(Float)
    zoom_category = Column(IntegerEnum(constants.ZoomCategories))
    the_geom = Column(Geometry("LINESTRING"), nullable=False)

    connection_node_start_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node_start = relationship(
        ConnectionNode, foreign_keys=connection_node_start_id
    )
    connection_node_end_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node_end = relationship(
        ConnectionNode, foreign_keys=connection_node_end_id
    )
    cross_section_locations = relationship(
        "CrossSectionLocation", back_populates="channel"
    )
    potential_breaches = relationship("PotentialBreach", back_populates="channel")
    exchange_lines = relationship("ExchangeLine", back_populates="channel")
    exchange_thickness = Column(Float)
    hydraulic_conductivity_in = Column(Float)
    hydraulic_conductivity_out = Column(Float)


class Windshielding(Base):
    __tablename__ = "v2_windshielding"
    id = Column(Integer, primary_key=True)
    north = Column(Float)
    northeast = Column(Float)
    east = Column(Float)
    southeast = Column(Float)
    south = Column(Float)
    southwest = Column(Float)
    west = Column(Float)
    northwest = Column(Float)
    the_geom = Column(Geometry("POINT"))
    channel_id = Column(
        Integer, ForeignKey(Channel.__tablename__ + ".id"), nullable=False
    )


class CrossSectionLocation(Base):
    __tablename__ = "v2_cross_section_location"
    id = Column(Integer, primary_key=True)
    code = Column(String(100))
    reference_level = Column(Float, nullable=False)
    friction_type = Column(IntegerEnum(constants.FrictionType), nullable=False)
    friction_value = Column(Float)
    bank_level = Column(Float)
    vegetation_stem_density = Column(Float)
    vegetation_stem_diameter = Column(Float)
    vegetation_height = Column(Float)
    vegetation_drag_coefficient = Column(Float)
    the_geom = Column(Geometry("POINT"), nullable=False)
    channel_id = Column(
        Integer, ForeignKey(Channel.__tablename__ + ".id"), nullable=False
    )
    channel = relationship(Channel, back_populates="cross_section_locations")
    definition_id = Column(
        Integer,
        ForeignKey(CrossSectionDefinition.__tablename__ + ".id"),
        nullable=False,
    )
    definition = relationship(CrossSectionDefinition)


class Pipe(Base):
    __tablename__ = "v2_pipe"
    id = Column(Integer, primary_key=True)
    display_name = Column(String(255))
    code = Column(String(100))
    profile_num = Column(Integer)
    sewerage_type = Column(IntegerEnum(constants.SewerageType))
    calculation_type = Column(
        IntegerEnum(constants.PipeCalculationType), nullable=False
    )
    invert_level_start_point = Column(Float, nullable=False)
    invert_level_end_point = Column(Float, nullable=False)
    friction_value = Column(Float, nullable=False)
    friction_type = Column(IntegerEnum(constants.FrictionType), nullable=False)
    dist_calc_points = Column(Float)
    material = Column(Integer)
    original_length = Column(Float)
    zoom_category = Column(IntegerEnum(constants.ZoomCategories))

    connection_node_start_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node_start = relationship(
        ConnectionNode, foreign_keys=connection_node_start_id
    )
    connection_node_end_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node_end = relationship(
        ConnectionNode, foreign_keys=connection_node_end_id
    )
    cross_section_definition_id = Column(
        Integer,
        ForeignKey(CrossSectionDefinition.__tablename__ + ".id"),
        nullable=False,
    )
    cross_section_definition = relationship("CrossSectionDefinition")
    exchange_thickness = Column(Float)
    hydraulic_conductivity_in = Column(Float)
    hydraulic_conductivity_out = Column(Float)


class Culvert(Base):
    __tablename__ = "v2_culvert"
    id = Column(Integer, primary_key=True)
    display_name = Column(String(255))
    code = Column(String(100))
    calculation_type = Column(IntegerEnum(constants.CalculationTypeCulvert))
    friction_value = Column(Float, nullable=False)
    friction_type = Column(IntegerEnum(constants.FrictionType), nullable=False)
    dist_calc_points = Column(Float)
    zoom_category = Column(IntegerEnum(constants.ZoomCategories))
    discharge_coefficient_positive = Column(Float)
    discharge_coefficient_negative = Column(Float)
    invert_level_start_point = Column(Float, nullable=False)
    invert_level_end_point = Column(Float, nullable=False)
    the_geom = Column(
        Geometry("LINESTRING"),
    )

    connection_node_start_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node_start = relationship(
        ConnectionNode, foreign_keys=connection_node_start_id
    )
    connection_node_end_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node_end = relationship(
        ConnectionNode, foreign_keys=connection_node_end_id
    )
    cross_section_definition_id = Column(
        Integer,
        ForeignKey(CrossSectionDefinition.__tablename__ + ".id"),
        nullable=False,
    )
    cross_section_definition = relationship(CrossSectionDefinition)


class DemAverageArea(Base):
    __tablename__ = "v2_dem_average_area"
    id = Column(Integer, primary_key=True)
    the_geom = Column(Geometry("POLYGON"), nullable=False)


class Weir(Base):
    __tablename__ = "v2_weir"
    id = Column(Integer, primary_key=True)
    code = Column(String(100))
    display_name = Column(String(255))
    crest_level = Column(Float, nullable=False)
    crest_type = Column(IntegerEnum(constants.CrestType), nullable=False)
    friction_value = Column(Float)
    friction_type = Column(IntegerEnum(constants.FrictionType))
    discharge_coefficient_positive = Column(Float)
    discharge_coefficient_negative = Column(Float)
    sewerage = Column(Boolean)
    external = Column(Boolean)
    zoom_category = Column(IntegerEnum(constants.ZoomCategories))

    connection_node_start_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node_start = relationship(
        ConnectionNode, foreign_keys=connection_node_start_id
    )
    connection_node_end_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node_end = relationship(
        ConnectionNode, foreign_keys=connection_node_end_id
    )
    cross_section_definition_id = Column(
        Integer,
        ForeignKey(CrossSectionDefinition.__tablename__ + ".id"),
        nullable=False,
    )
    cross_section_definition = relationship("CrossSectionDefinition")


class Orifice(Base):
    __tablename__ = "v2_orifice"
    id = Column(Integer, primary_key=True)
    code = Column(String(100))
    display_name = Column(String(255))
    zoom_category = Column(IntegerEnum(constants.ZoomCategories))
    crest_type = Column(IntegerEnum(constants.CrestType), nullable=False)
    crest_level = Column(Float, nullable=False)
    friction_value = Column(Float)
    friction_type = Column(IntegerEnum(constants.FrictionType))
    discharge_coefficient_positive = Column(Float)
    discharge_coefficient_negative = Column(Float)
    sewerage = Column(Boolean)

    connection_node_start_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node_start = relationship(
        ConnectionNode, foreign_keys=connection_node_start_id
    )
    connection_node_end_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node_end = relationship(
        ConnectionNode, foreign_keys=connection_node_end_id
    )
    cross_section_definition_id = Column(
        Integer,
        ForeignKey(CrossSectionDefinition.__tablename__ + ".id"),
        nullable=False,
    )
    cross_section_definition = relationship("CrossSectionDefinition")


class Pumpstation(Base):
    __tablename__ = "v2_pumpstation"
    id = Column(Integer, primary_key=True)
    code = Column(String(100))
    display_name = Column(String(255))
    zoom_category = Column(IntegerEnum(constants.ZoomCategories))
    classification = Column(Integer)
    sewerage = Column(Boolean)
    type_ = Column(
        IntegerEnum(constants.PumpType), name="type", key="type_", nullable=False
    )  # type: ignore[call-overload]
    start_level = Column(Float, nullable=False)
    lower_stop_level = Column(Float, nullable=False)
    upper_stop_level = Column(Float)
    capacity = Column(Float, nullable=False)
    connection_node_start_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node_start = relationship(
        "ConnectionNode", foreign_keys=connection_node_start_id
    )
    connection_node_end_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id")
    )
    connection_node_end = relationship(
        ConnectionNode, foreign_keys=connection_node_end_id
    )


class Obstacle(Base):
    __tablename__ = "v2_obstacle"
    id = Column(Integer, primary_key=True)
    code = Column(String(100))
    crest_level = Column(Float, nullable=False)
    the_geom = Column(Geometry("LINESTRING"), nullable=False)


class PotentialBreach(Base):
    __tablename__ = "v2_potential_breach"
    id = Column(Integer, primary_key=True)
    code = Column(String(100))
    display_name = Column(String(255))
    exchange_level = Column(Float)
    maximum_breach_depth = Column(Float)
    levee_material = Column(IntegerEnum(constants.Material))
    the_geom = Column(Geometry("LINESTRING"), nullable=False)
    channel_id = Column(
        Integer, ForeignKey(Channel.__tablename__ + ".id"), nullable=False
    )
    channel = relationship(
        Channel, foreign_keys=channel_id, back_populates="potential_breaches"
    )


class ExchangeLine(Base):
    __tablename__ = "v2_exchange_line"
    id = Column(Integer, primary_key=True)
    the_geom = Column(Geometry("LINESTRING"), nullable=False)
    channel_id = Column(
        Integer, ForeignKey(Channel.__tablename__ + ".id"), nullable=False
    )
    channel = relationship(
        Channel, foreign_keys=channel_id, back_populates="exchange_lines"
    )
    exchange_level = Column(Float)


class Tags(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    description = Column(Text)


DECLARED_MODELS = [
    AggregationSettings,
    BoundaryCondition1D,
    BoundaryConditions2D,
    Channel,
    ConnectionNode,
    ControlMeasureLocation,
    ControlMeasureMap,
    ControlMemory,
    ControlTable,
    CrossSectionDefinition,
    CrossSectionLocation,
    Culvert,
    DemAverageArea,
    DryWeatherFlow,
    DryWeatherFlowMap,
    DryWeatherFlowDistribution,
    ExchangeLine,
    Floodfill,
    ModelSettings,
    GridRefinement,
    GridRefinementArea,
    GroundWater,
    Interflow,
    Lateral1d,
    Lateral2D,
    Manhole,
    NumericalSettings,
    Obstacle,
    Orifice,
    Pipe,
    PotentialBreach,
    Pumpstation,
    SimpleInfiltration,
    Surface,
    SurfaceMap,
    SurfaceParameter,
    VegetationDrag,
    Weir,
    Windshielding,
]
