# app/service_layer/plotting/visualization_service.py

from abc import ABC, abstractmethod

from ...data_layer.models.analyzable_entity import AnalysisEntity

class VisualizationService(ABC):
    def __init__(self, analysis_entity :'AnalysisEntity' = None):
        self.analysis_entity = analysis_entity
  
    @abstractmethod
    def plot_analysis_configuration(self):
        pass