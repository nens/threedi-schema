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


class ControlDelta(Base):
    __tablename__ = "v2_control_delta"
    id = Column(Integer, primary_key=True)
    measure_variable = Column(String(50))
    measure_delta = Column(String(50))
    measure_dt = Column(Float)
    action_type = Column(String(50))
    action_value = Column(String(50))
    action_time = Column(Float)
    target_type = Column(String(100))
    target_id = Column(Integer)


class ControlGroup(Base):
    __tablename__ = "v2_control_group"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(Text)


class ControlMeasureGroup(Base):
    __tablename__ = "v2_control_measure_group"
    id = Column(Integer, primary_key=True)


class ControlMeasureMap(Base):
    __tablename__ = "v2_control_measure_map"
    id = Column(Integer, primary_key=True)
    measure_group_id = Column(
        Integer, ForeignKey(ControlMeasureGroup.__tablename__ + ".id")
    )
    object_type = Column(
        VarcharEnum(constants.MeasureLocationContentTypes), nullable=False
    )
    object_id = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)


class ControlMemory(Base):
    __tablename__ = "v2_control_memory"
    id = Column(Integer, primary_key=True)
    measure_variable = Column(VarcharEnum(constants.MeasureVariables), nullable=False)
    upper_threshold = Column(Float)
    lower_threshold = Column(Float)
    action_type = Column(VarcharEnum(constants.ControlTableActionTypes), nullable=False)
    action_value = Column(String(50), nullable=False)
    target_type = Column(VarcharEnum(constants.StructureControlTypes), nullable=False)
    target_id = Column(Integer, nullable=False)
    is_active = Column(Boolean)
    is_inverse = Column(Boolean)


class ControlPID(Base):
    __tablename__ = "v2_control_pid"
    id = Column(Integer, primary_key=True)
    measure_variable = Column(String(50))
    setpoint = Column(Float)
    kp = Column(Float)
    ki = Column(Float)
    kd = Column(Float)
    action_type = Column(String(50))
    target_type = Column(String(100))
    target_upper_limit = Column(String(50))
    target_lower_limit = Column(String(50))


class ControlTable(Base):
    __tablename__ = "v2_control_table"
    id = Column(Integer, primary_key=True)
    action_table = Column(Text, nullable=False)
    action_type = Column(VarcharEnum(constants.ControlTableActionTypes), nullable=False)
    measure_variable = Column(VarcharEnum(constants.MeasureVariables), nullable=False)
    measure_operator = Column(VarcharEnum(constants.MeasureOperators))
    target_type = Column(VarcharEnum(constants.StructureControlTypes), nullable=False)
    target_id = Column(Integer, nullable=False)


class ControlTimed(Base):
    __tablename__ = "v2_control_timed"
    id = Column(Integer, primary_key=True)
    action_type = Column(VarcharEnum(constants.ControlTableActionTypes), nullable=False)
    action_table = Column(Text, nullable=False)
    target_type = Column(VarcharEnum(constants.StructureControlTypes), nullable=False)
    target_id = Column(Integer, nullable=False)


class Control(Base):
    __tablename__ = "v2_control"
    id = Column(Integer, primary_key=True)
    control_group_id = Column(Integer, ForeignKey(ControlGroup.__tablename__ + ".id"))
    measure_group_id = Column(
        Integer, ForeignKey(ControlMeasureGroup.__tablename__ + ".id")
    )
    control_type = Column(VarcharEnum(constants.ControlType), nullable=False)
    control_id = Column(Integer)
    start = Column(String(50))
    end = Column(String(50))
    measure_frequency = Column(Integer)


class Floodfill(Base):
    __tablename__ = "v2_floodfill"
    id = Column(Integer, primary_key=True)
    waterlevel = Column(Float)
    the_geom = Column(Geometry("POINT"))


class Interflow(Base):
    __tablename__ = "v2_interflow"
    id = Column(Integer, primary_key=True)
    interflow_type = Column(IntegerEnum(constants.InterflowType), nullable=False)
    porosity = Column(Float)
    porosity_file = Column(String(255))
    porosity_layer_thickness = Column(Float)
    impervious_layer_elevation = Column(Float)
    hydraulic_conductivity = Column(Float)
    hydraulic_conductivity_file = Column(String(255))
    display_name = Column(String(255))

    global_settings = relationship("GlobalSetting", back_populates="interflow_settings")


class SimpleInfiltration(Base):
    __tablename__ = "v2_simple_infiltration"
    id = Column(Integer, primary_key=True)
    infiltration_rate = Column(Float)
    infiltration_rate_file = Column(String(255))
    infiltration_surface_option = Column(
        IntegerEnum(constants.InfiltrationSurfaceOption)
    )
    max_infiltration_capacity = Column(Float)
    max_infiltration_capacity_file = Column(Text)
    display_name = Column(String(255))

    global_settings = relationship(
        "GlobalSetting", back_populates="simple_infiltration_settings"
    )


class SurfaceParameter(Base):
    __tablename__ = "v2_surface_parameters"
    id = Column(Integer, primary_key=True)
    outflow_delay = Column(Float, nullable=False)
    surface_layer_thickness = Column(Float, nullable=False)
    infiltration = Column(Boolean, nullable=False)
    max_infiltration_capacity = Column(Float, nullable=False)
    min_infiltration_capacity = Column(Float, nullable=False)
    infiltration_decay_constant = Column(Float, nullable=False)
    infiltration_recovery_constant = Column(Float, nullable=False)

    surface = relationship(
        "Surface",
        back_populates="surface_parameters",
    )


class Surface(Base):
    __tablename__ = "v2_surface"
    id = Column(Integer, primary_key=True)
    display_name = Column(String(255))
    code = Column(String(100))
    zoom_category = Column(IntegerEnum(constants.ZoomCategories))
    nr_of_inhabitants = Column(Float)
    dry_weather_flow = Column(Float)
    function = Column(String(64))
    area = Column(Float)
    surface_parameters_id = Column(
        Integer, ForeignKey(SurfaceParameter.__tablename__ + ".id"), nullable=False
    )
    the_geom = Column(
        Geometry("GEOMETRY"),
        nullable=True,
    )
    surface_parameters = relationship(
        SurfaceParameter, foreign_keys=surface_parameters_id, back_populates="surface"
    )


class GroundWater(Base):
    __tablename__ = "v2_groundwater"
    id = Column(Integer, primary_key=True)

    groundwater_impervious_layer_level = Column(Float)
    groundwater_impervious_layer_level_file = Column(String(255))
    groundwater_impervious_layer_level_type = Column(
        IntegerEnum(constants.InitializationType)
    )
    phreatic_storage_capacity = Column(Float)
    phreatic_storage_capacity_file = Column(String(255))
    phreatic_storage_capacity_type = Column(IntegerEnum(constants.InitializationType))
    equilibrium_infiltration_rate = Column(Float)
    equilibrium_infiltration_rate_file = Column(String(255))
    equilibrium_infiltration_rate_type = Column(
        IntegerEnum(constants.InitializationType)
    )
    initial_infiltration_rate = Column(Float)
    initial_infiltration_rate_file = Column(String(255))
    initial_infiltration_rate_type = Column(IntegerEnum(constants.InitializationType))
    infiltration_decay_period = Column(Float)
    infiltration_decay_period_file = Column(String(255))
    infiltration_decay_period_type = Column(IntegerEnum(constants.InitializationType))
    groundwater_hydro_connectivity = Column(Float)
    groundwater_hydro_connectivity_file = Column(String(255))
    groundwater_hydro_connectivity_type = Column(
        IntegerEnum(constants.InitializationType)
    )
    display_name = Column(String(255))
    leakage = Column(Float)
    leakage_file = Column(String(255))

    global_settings = relationship(
        "GlobalSetting", back_populates="groundwater_settings"
    )


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
    impervious_surface_maps = relationship(
        "ImperviousSurfaceMap", back_populates="connection_node"
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
    __tablename__ = "v2_numerical_settings"
    id = Column(Integer, primary_key=True)
    cfl_strictness_factor_1d = Column(Float)
    cfl_strictness_factor_2d = Column(Float)
    convergence_cg = Column(Float)
    convergence_eps = Column(Float)
    flow_direction_threshold = Column(Float)
    frict_shallow_water_correction = Column(
        IntegerEnum(constants.FrictionShallowWaterDepthCorrection)
    )
    general_numerical_threshold = Column(Float)
    integration_method = Column(IntegerEnum(constants.IntegrationMethod))
    limiter_grad_1d = Column(IntegerEnum(constants.OffOrStandard))
    limiter_grad_2d = Column(IntegerEnum(constants.OffOrStandard))
    limiter_slope_crossectional_area_2d = Column(
        IntegerEnum(constants.LimiterSlopeXArea)
    )
    limiter_slope_friction_2d = Column(IntegerEnum(constants.OffOrStandard))
    max_nonlin_iterations = Column(Integer)
    max_degree = Column(Integer)
    minimum_friction_velocity = Column(Float)
    minimum_surface_area = Column(Float)
    precon_cg = Column(IntegerEnum(constants.OffOrStandard))
    preissmann_slot = Column(Float)
    pump_implicit_ratio = Column(Float)
    thin_water_layer_definition = Column(Float)
    use_of_cg = Column(Integer)
    use_of_nested_newton = Column(IntegerEnum(constants.OffOrStandard))

    global_settings = relationship("GlobalSetting", back_populates="numerical_settings")


class VegetationDrag(Base):
    __tablename__ = "v2_vegetation_drag"
    id = Column(Integer, primary_key=True)
    display_name = Column(String(255))

    vegetation_height = Column(Float)
    vegetation_height_file = Column(String(255))

    vegetation_stem_count = Column(Float)
    vegetation_stem_count_file = Column(String(255))

    vegetation_stem_diameter = Column(Float)
    vegetation_stem_diameter_file = Column(String(255))

    vegetation_drag_coefficient = Column(Float)
    vegetation_drag_coefficient_file = Column(String(255))

    global_settings = relationship(
        "GlobalSetting", back_populates="vegetation_drag_settings"
    )


class GlobalSetting(Base):
    __tablename__ = "v2_global_settings"
    id = Column(Integer, primary_key=True)
    use_2d_flow = Column(Boolean, nullable=False)
    use_1d_flow = Column(Boolean, nullable=False)
    manhole_storage_area = Column(Float)
    name = Column(String(128))
    sim_time_step = Column(Float, nullable=False)
    output_time_step = Column(Float, nullable=False)
    nr_timesteps = Column(Integer)
    start_time = Column(Text)
    start_date = Column(Text)
    grid_space = Column(Float, nullable=False)
    dist_calc_points = Column(Float, nullable=False)
    kmax = Column(Integer, nullable=False)
    guess_dams = Column(Integer)
    table_step_size = Column(Float, nullable=False)
    maximum_table_step_size = Column(Float)
    flooding_threshold = Column(Float, nullable=False)
    advection_1d = Column(IntegerEnum(constants.OffOrStandard), nullable=False)
    advection_2d = Column(IntegerEnum(constants.OffOrStandard), nullable=False)
    dem_file = Column(String(255))
    frict_type = Column(IntegerEnum(constants.FrictionType), nullable=False)
    frict_coef = Column(Float, nullable=False)
    frict_coef_file = Column(String(255))
    water_level_ini_type = Column(IntegerEnum(constants.InitializationType))
    initial_waterlevel = Column(Float, nullable=False)
    initial_waterlevel_file = Column(String(255))
    interception_global = Column(Float)
    interception_file = Column(String(255))
    dem_obstacle_detection = Column(Boolean, nullable=False)
    dem_obstacle_height = Column(Float)
    embedded_cutoff_threshold = Column(Float)
    epsg_code = Column(Integer)
    timestep_plus = Column(Boolean, nullable=False)
    max_angle_1d_advection = Column(Float)
    minimum_sim_time_step = Column(Float, nullable=False)
    maximum_sim_time_step = Column(Float)
    frict_avg = Column(IntegerEnum(constants.OffOrStandard), nullable=False)
    wind_shielding_file = Column(String(255))
    use_0d_inflow = Column(IntegerEnum(constants.InflowType), nullable=False)
    table_step_size_1d = Column(Float)
    use_2d_rain = Column(Integer, nullable=False)
    initial_groundwater_level = Column(Float)
    initial_groundwater_level_file = Column(String(255))
    initial_groundwater_level_type = Column(IntegerEnum(constants.InitializationType))

    numerical_settings_id = Column(
        Integer, ForeignKey(NumericalSettings.__tablename__ + ".id"), nullable=False
    )
    numerical_settings = relationship(
        NumericalSettings,
        foreign_keys=numerical_settings_id,
        back_populates="global_settings",
    )
    interflow_settings_id = Column(Integer, ForeignKey(Interflow.__tablename__ + ".id"))
    interflow_settings = relationship(
        Interflow,
        foreign_keys=interflow_settings_id,
        back_populates="global_settings",
    )
    control_group_id = Column(Integer, ForeignKey(ControlGroup.__tablename__ + ".id"))
    simple_infiltration_settings_id = Column(
        Integer, ForeignKey(SimpleInfiltration.__tablename__ + ".id")
    )
    simple_infiltration_settings = relationship(
        SimpleInfiltration,
        foreign_keys=simple_infiltration_settings_id,
        back_populates="global_settings",
    )
    groundwater_settings_id = Column(
        Integer, ForeignKey(GroundWater.__tablename__ + ".id")
    )
    groundwater_settings = relationship(
        GroundWater,
        foreign_keys=groundwater_settings_id,
        back_populates="global_settings",
    )
    vegetation_drag_settings_id = Column(
        Integer, ForeignKey(VegetationDrag.__tablename__ + ".id")
    )
    vegetation_drag_settings = relationship(
        VegetationDrag,
        foreign_keys=vegetation_drag_settings_id,
        back_populates="global_settings",
    )


class AggregationSettings(Base):
    __tablename__ = "v2_aggregation_settings"
    id = Column(Integer, primary_key=True)

    global_settings_id = Column(
        Integer, ForeignKey(GlobalSetting.__tablename__ + ".id")
    )

    var_name = Column(String(100), nullable=False)
    flow_variable = Column(VarcharEnum(constants.FlowVariable), nullable=False)
    aggregation_method = Column(
        VarcharEnum(constants.AggregationMethod), nullable=False
    )
    timestep = Column(Integer, nullable=False)


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
    __tablename__ = "v2_surface_map"
    id = Column(Integer, primary_key=True)
    surface_id = Column(Integer, nullable=False)
    connection_node_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    percentage = Column(Float)


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


class ImperviousSurface(Base):
    __tablename__ = "v2_impervious_surface"
    id = Column(Integer, primary_key=True)
    code = Column(String(100))
    display_name = Column(String(255))
    surface_inclination = Column(
        VarcharEnum(constants.SurfaceInclinationType), nullable=False
    )
    surface_class = Column(VarcharEnum(constants.SurfaceClass), nullable=False)
    surface_sub_class = Column(String(128))
    zoom_category = Column(IntegerEnum(constants.ZoomCategories))
    nr_of_inhabitants = Column(Float)
    area = Column(Float)
    dry_weather_flow = Column(Float)
    the_geom = Column(
        Geometry("GEOMETRY"),
        nullable=True,
    )
    impervious_surface_maps = relationship(
        "ImperviousSurfaceMap", back_populates="impervious_surface"
    )


class ImperviousSurfaceMap(Base):
    __tablename__ = "v2_impervious_surface_map"
    id = Column(Integer, primary_key=True)
    percentage = Column(Float, nullable=False)
    impervious_surface_id = Column(
        Integer, ForeignKey(ImperviousSurface.__tablename__ + ".id"), nullable=False
    )
    impervious_surface = relationship(
        ImperviousSurface, back_populates="impervious_surface_maps"
    )
    connection_node_id = Column(
        Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"), nullable=False
    )
    connection_node = relationship(
        ConnectionNode, back_populates="impervious_surface_maps"
    )


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


DECLARED_MODELS = [
    AggregationSettings,
    BoundaryCondition1D,
    BoundaryConditions2D,
    Channel,
    ConnectionNode,
    Control,
    ControlDelta,
    ControlGroup,
    ControlMeasureGroup,
    ControlMeasureMap,
    ControlMemory,
    ControlPID,
    ControlTable,
    ControlTimed,
    CrossSectionDefinition,
    CrossSectionLocation,
    Culvert,
    DemAverageArea,
    ExchangeLine,
    Floodfill,
    GlobalSetting,
    GridRefinement,
    GridRefinementArea,
    GroundWater,
    ImperviousSurface,
    ImperviousSurfaceMap,
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
