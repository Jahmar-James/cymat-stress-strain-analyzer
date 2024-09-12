from standards.base.analyzable_entity import AnalyzableEntity


class SampleGenericGroup(AnalyzableEntity):
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

    def create_entity(self):
        """
        Method to create a group of samples after validation.
        Can perform calculations such as averaging key properties across the group.
        """
        pass
