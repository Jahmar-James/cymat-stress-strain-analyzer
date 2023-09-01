# app/service_layer/analysis/specimen_analysis_protocol.py

from typing_extensions import Protocol
from data_layer.metrics.metrics_factory import SpecimenMetricsFactory

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
    