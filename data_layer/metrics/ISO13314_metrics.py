# app/data_layer/metrics/ISO1360_metrics.py

from pydantic import BaseModel

from data_layer import unit_registry
from data_layer.metrics import Metric

"""
Properties that need to be set to specimen must end with '_p' suffix
"""

class ISO_13314_SpecimenMetricsDTO(BaseModel):
    """ DTO for a specific analysis type """
    compressive_strength: Metric = None
    elastic_gradient: Metric = None