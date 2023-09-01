# app/data_layer/models/specimen.py

from functools import cached_property

import numpy as np

from data_layer.models import AnalyzableEntity, SpecimenPropertiesDTO, SpecimenMetricsDTO
from data_layer.IO import SpecimenDataManager
from service_layer.analysis import SpecimenAnalysisProtocol

class Specimen(AnalyzableEntity):
    def __init__(self, name, length, width, thickness, weight, data = None, data_formater = None):
        super().__init__()
        self.name = name
        self.data_manager =  SpecimenDataManager(data, data_formater)
        self.properties = SpecimenPropertiesDTO(length=length, width=width, thickness=thickness, weight=weight)
        self.metrics = None
        self.analysis_protocol = SpecimenAnalysisProtocol(self.properties, self.metrics,)

    def calculate_metrics(self, criteria: str = 'base'):
        metrics = self.analysis_protocol.get_specimen_metrics(criteria)
        self.metrics = self.analysis_protocol.calculate_properties(metrics)

        # Reset all lazy properties when metrics are recalculated
        self.reset_cached_properties()

    def get_plots(self) -> (fig, fig):
        pass
    
    @cached_property
    def _strength(self) -> float:
        return self.metrics.strength
    
    @cached_property
    def _stress(self) -> np.ndarray:
        return  self.data_manager.data.get('stress', np.array([]))

    @cached_property
    def _strain(self) -> np.ndarray:
        return self.data_manager.data.get('strain', np.array([]))

