# app/service_layer/plotting/visualization_service.py

from abc import ABC, abstractmethod

from data_layer.models.analyzable_entity import AnalyzableEntity

class VisualizationService(ABC):
    def __init__(self, analysis_entity :'AnalyzableEntity'):
        self.analysis_entity = analysis_entity
  
    @abstractmethod
    def plot_analysis_configuration(self):
        pass
    
    def plot_stress_strain_for_overlay(self, axes, opacity = 0.6) -> 'matplotlib.axes':
        """Plot stress-strain curve for the specimen, Simplfied plot for overlaying multiple specimens."""
        axes.plot(self.analysis_entity.stress, self.analysis_entity.strain, label=self.analysis_entity.name, alpha = opacity)
        return axes
    
    def plot_stress_strain_for_detailed_profile(self) -> ('matplotlib.figure', 'matplotlib.axes'):
        """Plot stress-strain curve for the specimen, Detailed plot for indivdual Examination."""
        figure, axes = plt.subplots()


        figure, axes = self.plot_analysis_configuration(figure, axes)
        return figure, axes


