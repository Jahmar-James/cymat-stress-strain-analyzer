from typing import Optional

from standards.sample_factory import MechanicalTestStandards, register_sample

from ..default_sample.sample import SampleGeneric
from .validator import CymatISO133142011Validator


@register_sample(MechanicalTestStandards.CYMAT_ISO13314_2011)
class SampleCymat(SampleGeneric):
    """
    A collection of mechanical testing samples.
    This class handles operations and calculations that apply to groups of samples, such as averaging properties.

    Responsibilities:
    - Validate that all samples in the group have compatible properties (e.g., so that average properties can be calculated).
    """

    def __init__(
        self,
        validator: Optional[CymatISO133142011Validator] = None,
    ):
        super().__init__(validator)
        self.validator = validator or CymatISO133142011Validator()

    def create_entity(self) -> "SampleCymat":
        """
        Method to create a group of samples after validation.
        Can perform calculations such as averaging key properties across the group.
        """
        raise NotImplementedError("Cymat Sample to be implemented.")

    def plot(self) -> None:
        """
        Plot key performance indicators (KPI) relevant to the standard being used.
        """
        raise NotImplementedError("Subclasses must implement this method.")
