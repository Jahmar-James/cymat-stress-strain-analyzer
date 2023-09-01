# app/data_layer/metric/specimen_metrics.py

from pydantic import BaseModel

class SpecimenMetricsDTO(BaseModel):
    """ 
    For specifc analysis propeties type and program model
    Base DTO with some common properties
    """
    IYS: float = None
    YS: float = None
    young_modulus: float = None
    strength: float = None