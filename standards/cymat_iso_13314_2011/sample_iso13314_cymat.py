from ..default_sample.sample import SampleGenericGroup
from .validator import CymatISO133142011Validator


class SampleCymatGroup(SampleGenericGroup):
    """
    A collection of mechanical testing samples.
    This class handles operations and calculations that apply to groups of samples, such as averaging properties.

    Responsibilities:
    - Validate that all samples in the group have compatible properties (e.g., so that average properties can be calculated).
    """

    def __init__(
        self,
        validator: CymatISO133142011Validator = CymatISO133142011Validator(),
    ):
        super().__init__(validator)
        self.validator = validator

    def create_entity(self):
        """
        Method to create a group of samples after validation.
        Can perform calculations such as averaging key properties across the group.
        """
        pass
