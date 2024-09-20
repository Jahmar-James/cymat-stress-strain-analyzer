from typing import Optional

from standards.sample_factory import MechanicalTestStandards, register_sample

from ..base.analyzable_entity import AnalyzableEntity
from ..base.base_standard_io_manager import BaseStandardIOManager
from ..base.base_standard_operator import BaseStandardOperator
from ..base.base_standard_validator import BaseStandardValidator
from .validator import GeneralPreliminaryValidator


@register_sample(MechanicalTestStandards.GENERAL_PRELIMINARY)
class SampleGeneric(AnalyzableEntity):
    """
    A collection of mechanical testing samples.
    This class handles operations and calculations that apply to groups of samples, such as averaging properties.

    Responsibilities:
    - Validate that all samples in the group have compatible properties (e.g., so that average properties can be calculated).
    """

    def __init__(
        self,
        validator: Optional[BaseStandardValidator] = None,
        io_manager: Optional[BaseStandardIOManager] = None,
        property_calculator: Optional[BaseStandardOperator] = None,
    ):
        # Validator to ensure that all samples have the necessary properties to form a group.
        # For example, checks might ensure that samples can be averaged together.
        self.validator = validator or GeneralPreliminaryValidator()
        self.io_manger = io_manager  # or BaseStandardIOManager() not implemented yet
        self.property_calculator = property_calculator or BaseStandardOperator()

    def create_entity(self):
        """
        Method to create a group of samples after validation.
        Can perform calculations such as averaging key properties across the group.
        """
        raise NotImplementedError("Gemeric Sample to be implemented.")

    def plot(self) -> None:
        """
        Plot key performance indicators (KPI) relevant to the standard being used.
        This method must be implemented by subclasses to provide standard-specific views.
        """
        raise NotImplementedError("Subclasses must implement this method.")
