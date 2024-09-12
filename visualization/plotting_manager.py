from standards.base.analyzable_entity import AnalyzableEntity


class PlotManager:
    """
    Manages plotting and visualization for the entities (samples or sample groups).
    This class provides more control and customization for users who need to go beyond the automated plots.

    Responsibilities:
    - Access the entity data directly for plotting.
    - Allow greater customization of plot styles and content compared to the automated plots provided by `AnalyzableEntity`.
    """

    def __init__(self):
        pass

    def plot_custom(self, entity: AnalyzableEntity):
        """
        Provide a customizable plot for a specific entity (either a single sample or a group of samples).
        This method will allow users to specify plot parameters and customize the visualization.
        """
        pass
        pass
