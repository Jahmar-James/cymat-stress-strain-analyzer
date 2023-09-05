# app/app_layer/app_state.py

from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from data_layer.models.specimen import Specimen 
    from data_layer.models.sample_group import SampleGroup


class AppState(BaseModel):
    """
    Contain app states
    """
    specimens: List[SampleGroup] = []
    current_specimen: Optional[Specimen] = None
    selected_specimen_indices: List[int] = []
    export_in_progress: bool = False
    analysis_type: Optional[str] = None  # ISO_1360 or DIN_5122
    analysis_parameters: Optional[dict] = None  # parameters for analysis
    analysis_result: Optional[dict] = None  # result of analysis

    def add_specimen(self, specimen: Specimen):
        self.specimens.append(specimen)

    def select_specimens(self, selected_specimen_indices: List[int]) -> List[SampleGroup]:
        self.selected_specimen_indices = selected_specimen_indices
        return [self.specimens[i] for i in selected_specimen_indices]  # Selecting multiple specimens based on indices

    @property
    def current_specimen(self):
        # Your logic here, for example, you might want to return the first selected specimen
        return self.specimens[self.selected_specimen_indices[0]] if self.selected_specimen_indices else None
    