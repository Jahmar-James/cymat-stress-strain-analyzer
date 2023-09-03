# app/service_layer/plotting/specimen_graph_manager.py
import matplotlib.pyplot as plt
import matplotlib.axes
import matplotlib.figure


from .visualization_service import VisualizationService
from ...data_layer.models.specimen import Specimen

class SpecimenGraphManager(VisualizationService):
    """
    Plotting service for specimen analysis.

    This service is responsible for plotting the analysis results of a specimen. There are two types of plots: 
    Generation of plots Only, User Customization and Display of plots are handled elsewhere.

    1. Detailed plot for indivdual Examination.
    2. Simplfied plot for overlaying multiple specimens.`
    """
    def __init__(self, analysis_entity: 'Specimen' ):
        super().__init__(analysis_entity)

    def plot_stress_strain_for_overlay(self, axes, opacity = 0.6) -> 'matplotlib.axes':
        """Plot stress-strain curve for the specimen, Simplfied plot for overlaying multiple specimens."""
        axes.plot(self.analysis_entity.stress, self.analysis_entity.strain, label=self.analysis_entity.name, alpha = opacity)
        return axes
    
    def plot_stress_strain_for_detailed_profile(self) -> ('matplotlib.figure', 'matplotlib.axes'):
        """Plot stress-strain curve for the specimen, Detailed plot for indivdual Examination."""
        figure, axes = plt.subplots()


        figure, axes = self.plot_analysis_configuration(figure, axes)
        return figure, axes

    def plot_analysis_configuration(self, figure, axes) -> ('matplotlib.figure', 'matplotlib.axes'):
        """
        Add analysis speificic configuration to the plot.

        Possible configurations:
            - Another data series ie. Hyteresis loop
            - Change Style and labels 
            - Surpress defualt plot_stress_strain_for_detailed_profile and only show analysis specific data
        """

        return figure, axes
        
    
    def display_cross_section(self):
        """Display cross-section of the specimen loaded from data/image.zip."""
        pass

  