# app/service_layer/analysis/specimen_analysis_protocol.py

from typing import TYPE_CHECKING, Optional
from typing_extensions import Protocol

from data_layer.IO.specimen_data_manager import SpecimenDataManager
from data_layer.metrics.metrics_factory import SpecimenMetricsFactory
from service_layer.operations.specimen_operations import SpecimenOperations

if TYPE_CHECKING:
    from data_layer.models.specimen_properties import SpecimenPropertiesDTO
    from data_layer.metrics.specimen_metrics import SpecimenMetricsDTO

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
    
    def __init__(self, specimen_properties_dto: 'SpecimenPropertiesDTO', specimen_metrics_dto: 'SpecimenMetricsDTO',
                 data_manager : 'SpecimenDataManager', specimen_operations : Optional['SpecimenOperations'] = None) :
        self.specimen_properties_dto = specimen_properties_dto
        self.specimen_metrics_dto = specimen_metrics_dto
        self.data_manager = data_manager
        self.specimen_operations = specimen_operations or SpecimenOperations()
        
    def calculate_metrics(self, metrics: 'SpecimenMetricsDTO'):
        """perform analysis specific computation on specimen metrics"""
        if self.data_manager.data is not None:
            start_idx_along_strain, end_idx_along_strain = self.data_manager.points['start_idx_along_strain_youngs_modulus'], self.data_manager.points['end_idx_along_strain_youngs_modulus']
            young_modulus = self.specimen_operations.calculate_young_modulus(start_idx_along_strain, end_idx_along_strain, slope_algorithm = None)
            IYS = self.specimen_operations.calculate_IY_strength(self.data_manager, index = None)
            
            if young_modulus is not None:
                offset = 0.002 # 0.2% offset
                YS = self.specimen_operations.calculate_strength(self.data_manager, young_modulus, offset = offset ,intercept_algorithm = self.data_manager.PointsOFInterest.intercept_algorithm)
        else:
            #Data must be loaded before metrics can be calculated
            raise ValueError("Data must be loaded before metrics can be calculated")
        

        
    def calculate_general_KPI(self):
        # Handle KPI calculations here
        pass
    
