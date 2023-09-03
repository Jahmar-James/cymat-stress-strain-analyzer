# app/service_layer/analysis/specimen_analysis_protocol.py

from typing import TYPE_CHECKING, Optional
from typing_extensions import Protocol

from data_layer.IO.specimen_data_manager import SpecimenDataManager
from data_layer.metrics.metrics_factory import SpecimenMetricsFactory
from service_layer.operations.specimen_operations import SpecimenOperations

from ...data_layer import unit_registry
from ...data_layer.metrics import Metric

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

    def get_evaluation_metrics(self, criteria, metrics_factory : Optional['SpecimenMetricsFactory'] = None) -> 'SpecimenMetricsDTO':
        metrics_factory = metrics_factory or SpecimenMetricsFactory()
        return metrics_factory.create_specimen(criteria)
    
    def calculate_general_KPI(self, existing_metrics , key_points: dict, properties: Optional['SpecimenPropertiesDTO']  = None) -> 'SpecimenMetricsDTO':
        """Handle general Key Performance Indicator calculations here."""
        raise NotImplementedError
    
    def get_key_points(self):
        return {
            '20%': 0.2,
            '40%': 0.4,
            '60%': 0.6,
            }
    
class SpecimenAnalysisProtocol(BaseSpecimenAnalysisProtocol):
    """ Perform calculations on specimen data for defualt analysis SpecimenMetricsDTO """
    
    def __init__(self, specimen_properties: 'SpecimenPropertiesDTO',
                 data_manager : 'SpecimenDataManager', 
                 specimen_operations : Optional['SpecimenOperations'] = None) :
        
        self.specimen_properties_dto = specimen_properties
        self.data_manager = data_manager
        self.specimen_operations = specimen_operations or SpecimenOperations()
        
    def calculate_metrics(self, existing_metrics: 'SpecimenMetricsDTO') -> 'SpecimenMetricsDTO':
        """perform analysis specific computation on specimen metrics"""
        if self.data_manager.data is not None:
            start_idx_along_strain, end_idx_along_strain = self.data_manager.points['start_idx_along_strain_youngs_modulus'], self.data_manager.points['end_idx_along_strain_youngs_modulus']
            young_modulus_value = self.specimen_operations.calculate_young_modulus(start_idx_along_strain, end_idx_along_strain, slope_algorithm = None)
            IYS_value = self.specimen_operations.calculate_IY_strength(self.data_manager, index = None)
             
            if young_modulus_value is not None:
                offset = 0.002 # 0.2% offset
                YS_value = self.specimen_operations.calculate_strength(self.data_manager, young_modulus_value, offset = offset ,intercept_algorithm = self.data_manager.PointsOFInterest.intercept_algorithm)
            else:
                YS_value = None
                
            new_metric_values = {'IYS': (IYS_value, unit_registry.megapascal),
                                    'YS': (YS_value, unit_registry.megapascal),
                                    'young_modulus': (young_modulus_value, unit_registry.megapascal)}
          
            return self._create_new_metrics(existing_metrics, new_metric_values)
        else:
            raise ValueError("Data must be loaded before metrics can be calculated")
            return existing_metrics
        
    def calculate_general_KPI(self, existing_metrics: 'SpecimenMetricsDTO', , key_points: dict, properties: Optional['SpecimenPropertiesDTO']  = None) -> 'SpecimenMetricsDTO':
        # Energy absorption at key points
        if self.data_manager.data is not None:
            
            energy_volumetic_KJ_m3 = [ self.specimen_operations.calculate_energy_absorption(self.data_manager.data, value) for value in key_points.values() ]
            
            # check if energy_volumetic_KJ_m3 is not None
            properties = properties or self.specimen_properties_dto
            energy_spcific_kJ_kg = self.specimen_operations.calculate_specific_energy_absorption(energy_volumetic_KJ_m3, properties.density) 
            
            strain_at_key_points = {key: self.specimen_operations.calculate_stress_at_strain(self.data_manager.data, value) for key, value in key_points.items()}
            
            new_metric_values = {'energy_volumetic_KJ_m3': (energy_volumetic_KJ_m3, unit_registry.kilojoule / unit_registry.meter ** 3),
                                 'energy_spcific_kJ_kg': (energy_spcific_kJ_kg, unit_registry.kilojoule / unit_registry.kilogram),
                                 'strain_at_key_points': (strain_at_key_points, unit_registry.dimensionless)}
        
            return self._create_new_metrics(existing_metrics, new_metric_values)
        else:
            raise ValueError("Data must be loaded before metrics can be calculated")
            return existing_metrics
        
    def _create_new_metrics(self, metrics, new_metric_values: dict):
        """Create a new metrics object with updated values."""
        
        # Create a copy of the existing metrics
        new_metrics = metrics.model_copy()
        
        # Update the new metrics with the new values
        for key, (value, unit) in new_metric_values.items():
            setattr(new_metrics, key, Metric(value, unit))
        
        return new_metrics
    
    
        
