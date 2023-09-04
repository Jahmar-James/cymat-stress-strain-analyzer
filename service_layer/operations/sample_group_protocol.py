# app/service_layer/analysis/sample_group_analysis_protocol.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data_layer.models.sample_group import SampleGroup

class SampleGroupAnalysisProtocol:
    """A protocol for the analysis of a SampleGroup. It defines the steps of the analysis and the order in which they should be executed."""
    def __init__(self, sample_group: SampleGroup):
        self.sample_group = sample_group

    def execute(self):
        """Execute the analysis protocol to reutrn SampleGroupCharacteristics onto the SampleGroup.characteristics ."""
        pass