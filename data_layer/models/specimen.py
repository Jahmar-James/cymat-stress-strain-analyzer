# app/data_layer/models/specimen.py

from functools import cached_property
from typing import TYPE_CHECKING, Optional

import numpy as np
from pydantic import BaseModel

from data_layer.IO import SpecimenDataManager
from ..IO.cross_section_manager import CrossSectionManager
from data_layer.models.analyzable_entity import AnalyzableEntity
from data_layer.models.specimen_properties import (Property, SpecimenPropertiesDTO)
from service_layer.analysis import SpecimenAnalysisProtocol
from ...service_layer.plotting.specimen_graph_manager import SpecimenGraphManager


if TYPE_CHECKING:
    from data_layer.metrics import Metric, SpecimenMetricsDTO
    import matplotlib.figure

class Specimen(AnalyzableEntity):
    def __init__(self, name : str, length : Property, width : Property, thickness : Property, weight : Property, data = None, data_formater = None):
        super().__init__()
        self.name = name
        self.data_manager =  SpecimenDataManager(data, data_formater)
        self.properties = SpecimenPropertiesDTO(length=length, width=width, thickness=thickness, weight=weight)
        self.metrics = SpecimenMetricsDTO
        self.analysis_protocol = SpecimenAnalysisProtocol(self.properties, self.metrics, self.data_manager)

    def calculate_metrics(self, criteria: str = 'base'):
        metrics = self.analysis_protocol.get_specimen_metrics(criteria)
        self.metrics = self.analysis_protocol.calculate_properties(metrics)
        self._set_metric_properties(self.metrics)

        # Reset all lazy properties when metrics are recalculated
        self.reset_cached_properties()

    def _set_metric_properties(self, metrics: BaseModel):
        """Set specimen properties based on metrics analysis results"""
        dynamic_prop_names = []
        new_unit_map = {}
        for metric_name, metric_tuple in metrics.dict().items():  # type: str, Metric
            if metric_name.endswith('_p'):
                specimen_property_name = metric_name[:-2] # Remove '_p' from metric name
                setattr(self, f"_{specimen_property_name}", metric_tuple.value)
                dynamic_prop_names.append(specimen_property_name)
                
                new_unit_map[specimen_property_name] = metric_tuple.default_unit
                
        # Register anlaysis specific properties with Analyzable Entity and update unit mapping        
        self._register_dynamic_properties(dynamic_prop_names)
        self._set_unit_mapping(new_unit_map)

    def analyze_cross_section(self,  image_path: str, cross_section_manager: Optional['CrossSectionManager'] =  None):
        """Analyze the cross-section of the specimen."""
        self.cross_section_manager = cross_section_manager or CrossSectionManager(image_path)
        self.cross_section_manager.analyze_image()

    def get_plots(self,graph_mangaer: Optional['SpecimenGraphManager'] = None) -> ('matplotlib.figure', 'matplotlib.figure'):
        self.graph_mangaer = graph_mangaer or SpecimenGraphManager(self)
    
    @cached_property
    def _strength(self) -> float:
        return self.metrics.strength
    
    @cached_property
    def _stress(self) -> np.ndarray:
        return  self.data_manager.data.get('stress', np.array([]))

    @cached_property
    def _strain(self) -> np.ndarray:
        return self.data_manager.data.get('strain', np.array([]))
    
    @cached_property
    def _cross_section_analysis(self) -> dict:
        return self.cross_section_manager.analysis_results if self.cross_section_manager else None

