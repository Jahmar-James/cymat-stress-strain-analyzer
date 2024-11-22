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

        # update public attributes to be serialized
        black_list = ["validator"]
        self.update_seralized_attributes(additional_attributes=black_list)

    def __repr__(self) -> str:
        return super().__repr__()


    def create_entity(self):
        """
        Method to create a group of samples after validation.
        Can perform calculations such as averaging key properties across the group.
        """
        raise NotImplementedError("Gemeric Sample to be implemented.")

    def plot(self, plot=None, plot_name="") -> None:
        """
        Plot key performance indicators (KPI) relevant to the standard being used.
        This method must be implemented by subclasses to provide standard-specific views.
        """
        if self.plot_manager is None:
            raise AttributeError(
                f"Cannot create plot: {self} is missing the subclass 'plot_manger'",
                "Asign an 'plot manger or use datat directly",
            )

        if (self.stress is None) or (self.strain is None):
            raise ValueError(
                f"Cannot create plot: {self}'s Stress or Strain is None.",
                f"Thus Standard Plot Method for {self.analysis_standard.value} is unavailable",
            )

        if isinstance(plot_name, str) and plot_name == "":
            plot_name = f"Stress Strain - {self.name}"

        plot = self.plot_manager.add_entity_to_plot(
            self,
            plot_name,
            x_data_key="strain",
            y_data_key="stress",
            plot_type="line",
            element_label="stress vs strain",
        )
        from visualization_backend.plot_config import PlotConfig

        return plot
        return plot
