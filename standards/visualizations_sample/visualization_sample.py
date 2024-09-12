from standards import MechanicalTestStandards, standard_registry
from standards.base.analyzable_entity import AnalyzableEntity


@standard_registry.register_standard(MechanicalTestStandards.VISUALIZATION_SAMPLE)
class VisualizationSample(AnalyzableEntity):
    """
    A collection of mechanical testing samples.
    This class handles operations and calculations that apply to groups of samples, such as averaging properties.

    Responsibilities:
    - Validate that all samples in the group have compatible properties (e.g., so that average properties can be calculated).
    """

    def __init__(self):
        # Validator to ensure that all samples have the necessary properties to form a group.
        # For example, checks might ensure that samples can be averaged together.
        self.validator = None
        self.io_manger = None

    def create_entity(self) -> bool:
        """
        Method to create a group of samples after validation.
        Can perform calculations such as averaging key properties across the group.
        """
        raise NotImplementedError("Visualization Sample to be implemented.")

    def plot(self) -> None:
        """
        Plot key performance indicators (KPI) relevant to the standard being used.
        This method must be implemented by subclasses to provide standard-specific views.
        """
        raise NotImplementedError("Subclasses must implement this method.")
