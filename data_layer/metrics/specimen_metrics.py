# app/data_layer/metric/specimen_metrics.py

from pydantic import BaseModel
from data_layer.metrics import Metric

from data_layer import unit_registry

"""
Properties that need to be set to specimen must end with '_p' suffix
"""

class SpecimenMetricsDTO(BaseModel):
    """
    For specific analysis properties type and program model.
    Base DTO with some common properties.
    Properties that need to be set to specimen must end with '_p' suffix.

    Metric is a named tuple with value and defualt unit.
    """
    IYS: Metric = None
    YS: Metric = None
    young_modulus: Metric = None
    strength: Metric = None

