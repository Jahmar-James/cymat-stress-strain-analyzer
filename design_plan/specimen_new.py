# specimen.py

# Rename to sample to be consistent with the rest of the code base
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
    young_modulus: float = None
    strength: float = None
   
class ISO_1360_SpecimenMetricsDTO(BaseModel):
    """ DTO for a specific analysis type """
    compressive_strength: float = None
    elastic_gradient: float = None


class SpecimenMetricsFactory:
    """ 
    Factory to determine specimen creation based on analysis type or program model. 
    Encapsulates the logic for specimen instantiation.
    """
    _registry = {
            "base": SpecimenMetricsDTO,
            "ISO_1360": ISO_1360_SpecimenMetricsDTO
        }

    @staticmethod
    def create_specimen(criteria: str = 'base'):
        if criteria in SpecimenMetricsFactory._registry:
            return SpecimenMetricsFactory._registry[criteria]()
        else:
            raise ValueError(f"Unknown criteria: {criteria}")
        
# Service Classes

class SpecimenGraphManager:
    """ Create figures with desired format and filtering"""
    def __init__(self, specimen_properties_dto, specimen_metrics_dto):
        pass

    def plot_stress_strain(self, ax):
        # Figure 1 Primary plot
        pass

    def plot_stress_strain_for_overlay(self, ax):
        # Figure 2 Secondary plot
        pass

    def get_figures(self) -> (fig, fig):
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
    def __init__(self,specimen_properties_dto):
        pass
    
    def calculate_metrics(self, metrics):
        """perform analysis specific computation on specimen metrics"""
        pass

    def get_evaluation_metrics(criteria, metrics_factory = None):
        if metrics_factory is None:
            metrics_factory = SpecimenMetricsFactory(criteria)
            return metrics_factory.create_specimen()
    
    def calculate_general_KPI(self):
        # Handle KPI calculations here
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
    def from_program_zip_file(cls, path, data_formate:SpecimenIO()) -> Specimen:
        pass
    
# Main Class

unit_registry = UnitRegistry()

def lazy_property(fn):
    """Decorator to turn method into lazy property. Result is cached."""
    attr_name = "_lazy_" + fn.__name__
    
    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazy_property


class Specimen:
    def __init__(self, name, length, width, thickness, weight, data = None, data_formater = None):
        self.name = name
        self.data_manager =  SpecimenDataManager(data, data_formater)
        self.properties = SpecimenPropertiesDTO(length=length, width=width, thickness=thickness, weight=weight)
        self.metrics = None
        self.analysis_protocol = SpecimenAnalysisProtocol(self.properties, self.metrics,)
        self.graph_manager = SpecimenGraphManager(self.properties, self.metrics)



    def calculate_metrics(self, criteria: str = 'base'):
        metrics = self.analysis_protocol.get_specimen_metrics(criteria)
        self.metrics = self.analysis_protocol.calculate_properties(metrics)

        # Reset cached properties when metrics are recalculated
        self._stress_with_unit = None
        self._strain_with_unit = None

        # Reset all lazy properties when metrics are recalculated
        self.reset_lazy_properties()

    def get_plots(self) -> (fig, fig):
        pass

    @lazy_property
    def stress_with_unit(self):
        return [s * unit_registry.pascal for s in self.data_manager.data.get('stress', [])]

    @lazy_property
    def strain_with_unit(self):
        return [s * unit_registry.pascal for s in self.data_manager.data.get('strain', [])]

    def reset_lazy_properties(self, *properties):
        """Reset given lazy properties, or all if none specified."""
        if properties:
            for prop in properties:
                if hasattr(self, "_lazy_" + prop):
                    delattr(self, "_lazy_" + prop)
        else:
            for attr in list(vars(self)):
                if attr.startswith("_lazy_"):
                    delattr(self, attr)

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

  
