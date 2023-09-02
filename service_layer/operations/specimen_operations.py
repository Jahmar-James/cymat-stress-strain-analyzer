# app/service_layer/operations/specimen_operations.py

from typing import Callable, TYPE_CHECKING

import numpy as np
import pandas as pd
import scipy

from .data_processing_service import DataProcessingService

if TYPE_CHECKING:
    from data_layer.models.specimen_properties import SpecimenPropertiesDTO
    from data_layer.metrics.specimen_metrics import SpecimenMetricsDTO
    from data_layer.models.specimen import Specimen

class SpecimenOperations(DataProcessingService):
    """ Perform general operations on specimen data"""
    @staticmethod
    def calculate_stress_strain(specimen_properties: 'SpecimenPropertiesDTO', specimen_data : pd.DataFrame) -> pd.DataFrame:
        """Calculate stress and strain from the specimen data."""
        data = specimen_data.copy()
        Area = specimen_properties.cross_sectional_area
        data['Stress'] = specimen_data['Force'] / Area
        data['Strain'] = specimen_data['Displacement'] / specimen_properties.original_length
        return data
        
    @staticmethod
    def deteminine_pts_of_interest(specimen: 'Specimen', func: Callable = None) -> None:
        """Determine the points of interest on the data."""
        pass
    
    @staticmethod
    def zero_strain_data(specimen: 'Specimen', func: Callable = None) -> None:
        """Zero the strain data."""
        pass

    @staticmethod
    def calculate_young_modulus(specimen: 'Specimen', func: Callable = None) -> float:
        """Calculate Young's modulus of the specimen."""
        pass
    
    @staticmethod
    def calculate_strength(specimen: 'Specimen' , func = None) -> float:
        pass

    @staticmethod
    def calculate_energy_absorption(specimen: 'Specimen', strain_precentage: float) -> None:
        """Calculate the energy absorbed by the specimen up to a given strain percentage."""
        pass

    @staticmethod
    def shift_data(specimen: 'Specimen', shift: float) -> None:
        """Shift the data by a specified value."""
        pass
