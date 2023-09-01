# app/data_layer/metrics/ISO1360_metrics.py

from pydantic import BaseModel

class ISO_1360_SpecimenMetricsDTO(BaseModel):
    """ DTO for a specific analysis type """
    compressive_strength: float = None
    elastic_gradient: float = None