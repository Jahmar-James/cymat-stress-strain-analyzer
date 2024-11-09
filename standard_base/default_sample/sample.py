from typing import Optional

from standard_base import MechanicalTestStandards
from standard_base.entities.analyzable_entity import AnalyzableEntity

# from standard_base.io_management.ARCHIVE_base_standard_io_manager import BaseStandardIOManager
# from standard_base.properties_calculators.base_standard_operator import BaseStandardOperator
from standard_base.validation.base_standard_validator import BaseStandardValidator

from .validator import GeneralPreliminaryValidator


class SampleGeneric(AnalyzableEntity):
    """
    A collection of mechanical testing samples.
    This class handles operations and calculations that apply to groups of samples, such as averaging properties.

    Responsibilities:
    - Validate that all samples in the group have compatible properties (e.g., so that average properties can be calculated).
    """

    def __init__(
        self,
        name: str,
        validator: Optional[BaseStandardValidator] = None,
        *args,
        **kwargs,
    ):
        # Validator to ensure that all samples have the necessary properties to form a group.
        # For example, checks might ensure that samples can be averaged together.
        super().__init__(
            name=name,
            *args,
            **kwargs,
        )
        self.validator = validator or GeneralPreliminaryValidator()
        self.analysis_standard = MechanicalTestStandards.GENERAL_PRELIMINARY

    def __repr__(self) -> str:
        return super().__repr__()

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
