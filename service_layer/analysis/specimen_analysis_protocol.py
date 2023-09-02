# app/service_layer/analysis/specimen_analysis_protocol.py

from typing import TYPE_CHECKING
from typing_extensions import Protocol

from data_layer.IO.specimen_data_manager import SpecimenDataManager
from data_layer.metrics.metrics_factory import SpecimenMetricsFactory
from service_layer.operations.specimen_operations import SpecimenOperations

if TYPE_CHECKING:
    from data_layer.models.specimen_properties import SpecimenPropertiesDTO
    from data_layer.metrics.specimen_metrics import SpecimenMetricsDTO
    from pydantic import BaseModel

class BaseSpecimenAnalysisProtocol(Protocol):
    """ Perform calculations on specimen data depending on the desire analysis / ISO Standard"""
    def __init__(self):
        pass
    
    def calculate_metrics(self, metrics):
        """perform analysis specific computation on specimen metrics"""
        raise NotImplementedError

    def get_evaluation_metrics(self, criteria, metrics_factory = None) -> 'SpecimenMetricsDTO':
        if metrics_factory is None:
            metrics_factory = SpecimenMetricsFactory(criteria)
            return metrics_factory.create_specimen()
        
    
    def calculate_general_KPI(self):
        """Handle general Key Performance Indicator calculations here."""
        raise NotImplementedError
    
class SpecimenAnalysisProtocol(BaseSpecimenAnalysisProtocol):
    """ Perform calculations on specimen data for defualt analysis SpecimenMetricsDTO """
    
    def __init__(self, specimen_properties_dto: 'SpecimenPropertiesDTO', specimen_metrics_dto: 'SpecimenMetricsDTO', data_manager : 'SpecimenDataManager') :
        self.specimen_properties_dto = specimen_properties_dto
        self.specimen_metrics_dto = specimen_metrics_dto
        self.data_manager = data_manager
        
    def calculate_metrics(self, metrics: 'SpecimenMetricsDTO'):
        """perform analysis specific computation on specimen metrics"""
        offset = 0.002 # 0.2% offset
        start_idx_along_strain, end_idx_along_strain = self.data_manager.points_of_interest['start_idx_along_strain_youngs_modulus'], self.data_manager.points_of_interest['end_idx_along_strain_youngs_modulus']
        young_modulus = SpecimenOperations.calculate_young_modulus(start_idx_along_strain, end_idx_along_strain, slope_algorithm)
        IYS = SpecimenOperations.calculate_IY_strength(self.data_manager.data, young_modulus, self.data_manager.PointsOFInterest.intercept_algorithm)
        YS = SpecimenOperations.calculate_Y_strength(self.data_manager.data, young_modulus, offset ,self.data_manager.PointsOFInterest.intercept_algorithm)
        strength = SpecimenOperations.calculate_strength(self.data_manager.data, young_modulus, offset, scipy_local_minima_algorithm)
        
    def calculate_general_KPI(self):
        # Handle KPI calculations here
        pass
    
