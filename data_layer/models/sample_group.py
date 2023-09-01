# app/data_layer/models/sample_group.py

from functools import cached_property
from typing import TYPE_CHECKING

import matplotlib.figure
import numpy as np

from data_layer.models import AnalyzableEntity
from data_layer.models.sample_group_characteristics import SampleGroupCharacteristics

if TYPE_CHECKING:

    from data_layer.models.specimen import Specimen


class SampleGroup(AnalyzableEntity):
    """The main class that holds a collection of Specimen objects. Methods might include adding/removing specimens, iterating over specimens, and so on."""
    def __init__(self, characteristics: SampleGroupCharacteristics = None, data_manager = None, graph_manager = None ):
        super().__init__()
        self.specimens = []
        self.type = None
        self.characteristics = characteristics
        self.data_manager = data_manager or  SampleGroupDataManager()
        self.graph_manager = graph_manager or SampleGroupGraphManager()
        self.stress = None
        self.strain = None

    def __iter__(self):
        for specimen in self.specimens:
            yield specimen

    def __repr__(self) -> str:
        pass
    
    def get_plots(self) -> (matplotlib.figure, matplotlib.figure):
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