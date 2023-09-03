# app/service_layer/plotting/sample_group_graph_manager.py

import matplotlib.pyplot as plt
from typing import Optional

from .visualization_service import VisualizationService

from ...data_layer.models.sample_group import SampleGroup
from .sample_group_plotter import SampleGroupPlotter
from .control_chart import ControlChart

class SampleGroupGraphManager(VisualizationService):
    """A service class for all graphical operations related to SampleGroups, including plotting aggregated data or overlaying individual specimen plots."""
    def __init__(self, sample_group: SampleGroup, plotter: Optional['SampleGroupPlotter'] = None, contol_chart: Optional['ControlChart'] = None):
        super().__init__(sample_group)
        self.sample_group = sample_group 
        self.control_chart = contol_chart or ControlChart()
        self.plotter = plotter or  SampleGroupPlotter()

    def generate_sample_group_plot(self):
        """Generate a plot for the average stress-strain curve of the sample group."""
        pass

    def generate_control_charts(self):
        """Generate a control chart for the sample group."""
        pass