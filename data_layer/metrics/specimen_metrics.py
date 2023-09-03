# app/data_layer/metric/specimen_metrics.py

from pydantic import BaseModel, Field

from typing import Optional, Any

from data_layer import unit_registry
from data_layer.metrics import Metric

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
    IYS: Metric = Field(default=Metric(None, unit_registry.megapascal))
    YS: Metric = Field(default=Metric(None, unit_registry.megapascal))
    young_modulus: Metric = Field(default=Metric(None, unit_registry.megapascal))
    strength: Metric = Field(default=Metric(None, unit_registry.megapascal))
    
    def get(self, metric_name: str, default= None) -> Optional[Metric]:
        """
        Gets the value of the specified metric. If the metric does not exist, returns the default value.
        """
        return getattr(self, metric_name, default)
    
    def get_value(self, metric_name: str, default= None) -> Optional[Any]:
        """
        Gets the value of the specified metric. If the metric does not exist, returns the default value.
        """
        metric = getattr(self, metric_name, default)
        return metric.value if metric else default
    


