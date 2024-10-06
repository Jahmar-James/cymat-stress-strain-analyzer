from typing import Optional

from standards.base.analyzable_entity import AnalyzableEntity

from ..base.base_io_management.ARCHIVE_base_standard_io_manager import BaseStandardIOManager
from ..base.base_standard_validator import BaseStandardValidator
from ..base.properties_calculators.group_aggeregation_calculator import GroupAggregationOperator


class SampleGenericGroup(AnalyzableEntity):
    """
    A collection of mechanical testing samples.
    This class handles operations and calculations that apply to groups of samples, such as averaging properties.

    Responsibilities:
    - Validate that all samples in the group have compatible properties (e.g., so that average properties can be calculated).
    """

    def __init__(
        self,
        standard: str,
        samples: Optional[list[AnalyzableEntity]] = None,
        aggregation_strategy: Optional[dict] = None,
        validator: Optional["BaseStandardValidator"] = None,
        io_manager: Optional["BaseStandardIOManager"] = None,
        property_calculator: Optional["GroupAggregationOperator"] = None,
    ):
        # Validator to ensure that all samples have the necessary properties to form a group.
        # For example, checks might ensure that samples can be averaged together.
        self.validator = validator  # TODO GeneralPreliminaryValidator()
        self.io_manger = io_manager  # or BaseStandardIOManager() not implemented yet
        self.standard = standard
        self.samples = []
        self.aggregation_strategy = aggregation_strategy or {}
        self.property_calculator = property_calculator or GroupAggregationOperator()

        if samples:
            for sample in samples:
                self.add_sample(sample)

        # Aggregate sample properties and data using GroupAggregationOperator.
        aggregated_properties = self._aggregate_properties()
        aggregated_data = self._aggregate_data()

        # Initialize the base class with the aggregated values.
        super().__init__(
            name="SampleGroup",
            length=aggregated_properties.get("length"),
            width=aggregated_properties.get("width"),
            thickness=aggregated_properties.get("thickness"),
            mass=aggregated_properties.get("mass"),
            area=aggregated_properties.get("area"),
            volume=aggregated_properties.get("volume"),
            density=aggregated_properties.get("density"),
            force=aggregated_data.get("force"),
            displacement=aggregated_data.get("displacement"),
            stress=aggregated_data.get("stress"),
            strain=aggregated_data.get("strain"),
        )

    def create_entity(self) -> "SampleGenericGroup":
        """
        Method to create a group of samples after validation.
        Can perform calculations such as averaging key properties across the group.
        """
        pass

    def add_sample(self, sample: AnalyzableEntity) -> None:
        """
        Add a sample to the group if it conforms to the group's standard.

        Parameters:
        - sample: An AnalyzableEntity instance representing a single sample.

        Raises:
        - ValueError if the sample does not conform to the group's standard.
        """
        if sample.analysis_standard != self.standard:
            raise ValueError(f"Sample '{sample.name}' does not conform to the group standard '{self.standard}'.")

        # Convert units of the sample if needed before adding
        self._standardize_sample_units(sample)

        self.samples.append(sample)
        self._update_aggregated_properties()

    def _standardize_sample_units(self, sample: AnalyzableEntity) -> None:
        """
        Ensure that the sample's units match the group's internal units before adding.
        This method converts the sample's properties to the group's internal units.
        """
        for prop in ["length", "width", "thickness", "area", "volume", "density"]:
            internal_unit = self.internal_units.get(prop)
            sample_unit = sample.internal_units.get(prop)
            if internal_unit and sample_unit and internal_unit != sample_unit:
                converted_value = sample._convert_units(
                    value=getattr(sample, f"_{prop}"), current_unit_key=prop, target_unit=internal_unit
                )
                setattr(sample, f"_{prop}", converted_value)

    def _update_aggregated_properties(self) -> None:
        """
        Recalculate and update aggregated properties after adding or modifying samples.
        """
        aggregated_properties = self._aggregate_properties()
        aggregated_data = self._aggregate_data()

        self._area = aggregated_properties.get("area")
        self._volume = aggregated_properties.get("volume")
        self._density = aggregated_properties.get("density")
        self._force = aggregated_data.get("force")
        self._displacement = aggregated_data.get("displacement")
        self._stress = aggregated_data.get("stress")
        self._strain = aggregated_data.get("strain")

    def recalculate_properties(self, property_name: str) -> None:
        """
        Override to handle recalculation of group-level properties.
        """
        if hasattr(self, f"_{property_name}"):
            setattr(self, f"_{property_name}", None)
            self._update_aggregated_properties()
        else:
            raise ValueError(f"Property {property_name} does not exist.")
