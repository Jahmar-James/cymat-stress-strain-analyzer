# app/data_layer/models/sample_group.py

from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Optional

import matplotlib.figure
import numpy as np

from service_layer.plotting.sample_group_graph_manager import \
    SampleGroupGraphManager

from ..IO.group_data_manager import SampleGroupDataManager
from .analyzable_entity import AnalyzableEntity
from .sample_group_characteristics import SampleGroupCharacteristics

if TYPE_CHECKING:
    from data_layer.models.specimen import Specimen


class SampleGroup(AnalyzableEntity):
    """The main class that holds a collection of Specimen objects. Methods might include adding/removing specimens, iterating over specimens, and so on."""
    def __init__(self, data_manager : Optional['SampleGroupDataManager'] = None, graph_manager = None ):
        super().__init__()
        self.specimens = []
        self.type = None
        self.characteristics = None
        self.data_manager = data_manager or  SampleGroupDataManager()
        self.graph_manager = graph_manager or SampleGroupGraphManager()
        self.stress = None
        self.strain = None
        self.custom_name = None
        
    def add_specimen(self, specimen: 'Specimen'):
        self.created_at = datetime.utcnow()
        
        pass
    
    def __iter__(self):
        for specimen in self.specimens:
            yield specimen

    def __repr__(self) -> str:
        return f"<Sample Group({self.type}, {len(self.specimens)} specimens), Analysis type {self.type}>"
    
    def get_plots(self) -> (matplotlib.figure, matplotlib.figure):
        pass
    
    @cached_property
    def _strength(self) -> float:
        return self.characteristics.strength
    
    @cached_property
    def _stress(self) -> np.ndarray:
        return  self.data_manager.data.get('stress', np.array([]))

    @cached_property
    def _strain(self) -> np.ndarray:
        return self.data_manager.data.get('strain', np.array([]))
    
    @property
    def name(self) -> str:
        # use the first specimen's name, type, and dtaetime as the sample group's defualt name otherwise return "Sample Group"
        if len(self.specimens) > 0:
            return f"{self.specimens[0].name} {self.type}  {self.created_at}" if self.custom_name is None else self.custom_name
        else:
            return f"Sample Group"