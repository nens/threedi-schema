from .domain import constants, models

"""
Put features in beta development in these lists to prevent users from using them, in the SQLAlchemy format used in the schema.
"""
"""This list contains beta columns, e.g. models.SomeTable.some_column"""
BETA_COLUMNS = [
    models.VegetationDrag.id,
    models.Manhole.exchange_thickness,
    models.Manhole.hydraulic_conductivity_in,
    models.Manhole.hydraulic_conductivity_out,
    models.Channel.exchange_thickness,
    models.Channel.hydraulic_conductivity_in,
    models.Channel.hydraulic_conductivity_out,
    models.Pipe.exchange_thickness,
    models.Pipe.hydraulic_conductivity_in,
    models.Pipe.hydraulic_conductivity_out,
]
"""
This list contains dicts with lists of beta values for columns, where the dict has the format:
{
    "columns": [
        models.SomeTable.some_column,
        models.SomeTable.some_other_column,
    ],
    "values": [
        constants.SomeConstantsClass.SOMEENUMVALUE,
        "or just some random string",
    ]
}
The modelchecker will go through each column and give an error when a beta value is used for its associated column.
"""
BETA_VALUES = [
    {
        "columns": [
            models.BoundaryCondition1D.boundary_type,
            models.BoundaryConditions2D.boundary_type,
        ],
        "values": [
            constants.BoundaryType.GROUNDWATERLEVEL,
            constants.BoundaryType.GROUNDWATERDISCHARGE,
        ],
    }
]
