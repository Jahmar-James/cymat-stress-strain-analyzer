# app/data_layer/models/specimen_properties.py

from pydantic import BaseModel

# DTO
# Specimen Subclasses

class SpecimenPropertiesDTO(BaseModel):
    """Common properties for all specimen types and analysis types"""
    length: float
    width: float
    thickness: float
    weight: float

    @property
    def cross_sectional_area(self) -> float:
        return self.length * self.width

    @property
    def original_length(self) -> float:
        return self.thickness

    @property
    def volume(self) -> float:
        return self.length * self.width * self.thickness

    @property
    def density(self) -> float:
        return self.weight / self.volume