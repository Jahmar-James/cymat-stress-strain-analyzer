# app/app_layer/managers/graphics_manager.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data_layer.models.specimen import Specimen
    from data_layer.models.sample_group import SampleGroup
    from service_layer.plotting.specimen_graph_manager import SpecimenGraphManager
    from service_layer.plotting.sample_group_graph_manager import SampleGroupGraphManager

class GraphicsManager:
    """
    Manage all graphics-related services and operations: 
    """
    def __init__(self, specimen_graph_manager: 'SpecimenGraphManager', sample_group_graph_manager: 'SampleGroupGraphManager'):
        self.specimen_graph_manager = specimen_graph_manager
        self.sample_group_graph_manager = sample_group_graph_manager
    
    def plot_current_specimen(self) -> None:
        # Plot the current specimen
        pass

    def plot_all_specimens(self) -> None:
        # overaly all specimen in the sample group from selected tab
        pass

    def plot_average(self) -> None:
        # average all specimen in the sample group from selected tab
        pass

    def _filter(self):
        # filter specimen based on selected criteria
        pass

    def _set_plotting_parameters(self):
        # set plotting parameters. Interanl vs external plot presentation
        pass
