# app/data_layer/models/specimen_properties.py

from pydantic import BaseModel

from data_layer import unit_registry
from data_layer.models import Property

# DTO
# Specimen Subclasses

class SpecimenPropertiesDTO(BaseModel):
    """Common properties for all specimen types and analysis types"""
    length: Property
    width: Property
    thickness: Property
    weight: Property

    @property
    def cross_sectional_area(self) -> float:
        return self.length.value * self.width.value

    @property
    def original_length(self) -> float:
        return self.thickness.value

    @property
    def volume(self) -> float:
        return self.length.value * self.width.value * self.thickness.value

    @property
    def density(self) -> float:
        return self.weight.value / self.volume