# app/app_layer/managers/graphics_manager.py

from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from data_layer.models.specimen import Specimen
    from data_layer.models.sample_group import SampleGroup
    from service_layer.plotting.specimen_graph_manager import SpecimenGraphManager
    from service_layer.plotting.sample_group_graph_manager import SampleGroupGraphManager

class GraphicsManager:
    """
    Manage all graphics-related services and operations: 
    """    
    def initialize_graphics(self, specimen_graph_manager: Optional['SpecimenGraphManager'] = None, sample_group_graph_manager:  Optional['SampleGroupGraphManager'] = None):
        if specimen_graph_manager is None and sample_group_graph_manager is None:
            raise ValueError("Must provide at least one graph manager")

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
