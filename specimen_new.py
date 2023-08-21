# specimen.py
# DTOs

from pydantic import BaseModel
from typing import List
import numpy as np
import pandas as pd
from pint import UnitRegistry
from typing_extensions import Protocol


# DAO
class SpecimenRepository:
    """Handle save and creation of specimen class from db"""
    @staticmethod
    def save_to_db(specimen: SpecimenFromDB()):
        # Placeholder database save operation
        pass

    @staticmethod
    def fetch_from_db(db_id: int) -> SpecimenFromDB():
        # Placeholder database fetch operation
        return SpecimenFromDB()

class SpecimenIO:
    """Handle save and creation of specimen class from zip files"""

# DTOs Subclasses
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

class SpecimenMetricsDTO(BaseModel):
    """ 
    For specifc analysis propeties type and program model
    Base DTO with some common properties
    """
    IYS: float = None
    YS: float = None
    youung_modulus: float = None
    strength: float = None
    strain_at_break: float = None
    stress_at_break: float = None

   
class ISO_1360_SpecimenMetricsDTO(BaseModel):
    """ DTO for a specific analysis type """
    compressive_strength: float = None
    elastic_gradient: float = None


class SpecimenMetricsFactory:
    """ 
    Factory to determine specimen creation based on analysis type or program model. 
    Encapsulates the logic for specimen instantiation.
    """
    
    @staticmethod
    def create_specimen(criteria: str = 'base'):
        if criteria == "base":
            return SpecimenMetricsDTO()
        elif criteria == "analysis_type":
            return ISO_1360_SpecimenMetricsDTO()
        else:
            raise ValueError(f"Unknown criteria: {criteria}")

# Service Classes

class SpecimenGraphManager:
    """ Create figures with desired format and filtering"""
    def __init__(self, specimen_properties_dto, specimen_metrics_dto):
        pass

    def plot_stress_strain(self, ax):
        # Handle plotting here
        pass

class SpecimenDataOperations:
    """ Perform general operations on specimen data"""
    @staticmethod
    def calculate_strength(specimen: Specimen) -> float:
        return specimen.metrics.YS
    
    @staticmethod
    def calculate_young_modulus(specimen: Specimen) -> float:
        pass

    @staticmethod
    def shift_data(specimen: Specimen, shift: float):
        pass

    @staticmethod
    def zero_strain_data(specimen: Specimen):
        # shited_strain 
        pass

    @staticmethod
    def deteminine_pts_of_interest(specimen: Specimen):
        pass

    @staticmethod
    def calculate_energy_absorption(specimen: Specimen,  strain_precentage: float):
        pass


class SpecimenAnalysisProtocol(Protocol):
    """ Perform calculations on specimen data depending on the desire analysis / ISO Standard"""
    def __init__(self, specimen_properties_dto, SpecimenMetricsFactory):
        pass

    def calculate_properties(self):
        # Handle properties calculation here
        pass

    def _get_specimen_metrics(self):
        # Handle metrics calculations here
        pass

class SpecimenDataManager:
    """ Manage import and export of specimen class from different sources"""
    def __init__(self, data, data_formater, repositorty):
        self.data = data
        self.data_formater = data_formater or SpecimenIO()
        self.repositorty  =  repositorty or SpecimenRepository() 

    @classmethod
    def from_database(cls, id,  repository_instance:SpecimenRepository) -> Specimen: 
        specimen = repository_instance.get(id)
        return 
    
    @classmethod
    def from_program_zip_file(cls, path) -> Specimen:
        pass
    
# Main Class

class Specimen:
    def __init__(self, name, length, width, thickness, weight, data = None, data_formater = None):
        self.name = name
        self.data_manager =  SpecimenDataManager(data, data_formater)
        self.properties = SpecimenPropertiesDTO(length=length, width=width, thickness=thickness, weight=weight)
        self.metrics = SpecimenMetricsDTO()
        self.graph_manager = SpecimenGraphManager(self.properties, self.metrics)
        self.analysis_service = SpecimenAnalysisService(self.properties, self.metrics)
        self.unit_registry = UnitRegistry()

        # ...

        # Pint-powered properties for stress and strain with units.
    @property
    def stress_with_unit(self):
        return [s * unit_registry.pascal for s in self.data_manager.data.get('stress', [])]

    @property
    def strain_with_unit(self):
        return [s * unit_registry.pascal for s in self.data_manager.data.get('strain', [])]
    

class SpecimenFromDB(Specimen):
    def __init__(self, name, data, length, width, thickness, weight, id):
        super().__init__(name, data, length, width, thickness, weight)
        self.id = id

    def _retrieve_properties_from_db(self):
        pass

    def _retrieve_metrics_from_db(self):
        pass

    def save(self):
        self.data_manager.save_to_db(self)
    
    @classmethod
    def load(cls, id):
        return cls.from_database(id, SpecimenRepository())

  