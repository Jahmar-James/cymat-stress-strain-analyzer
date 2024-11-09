from typing import Optional

from standard_base import MechanicalTestStandards
from standard_base.entities.analyzable_entity import AnalyzableEntity, exportable_property
from standard_base.properties_calculators.group_aggeregation_calculator import GroupAggregationOperator
from standard_base.validation.base_standard_validator import BaseStandardValidator


class SampleGenericGroup(AnalyzableEntity):
    """
    A collection of mechanical testing samples.
    This class handles operations and calculations that apply to groups of samples, such as averaging properties.

    Responsibilities:
    - Validate that all samples in the group have compatible properties (e.g., so that average properties can be calculated).
    """

    def __init__(
        self,
        standard: MechanicalTestStandards = MechanicalTestStandards.GENERAL_PRELIMINARY,
        samples: Optional[list[AnalyzableEntity]] = None,
        aggregation_strategy: Optional[dict] = None,
        validator: Optional["BaseStandardValidator"] = None,
        property_calculator: Optional["GroupAggregationOperator"] = None,
    ):
        super().__init__(name="TestSampleGroup")

        self.validator = validator  # TODO GeneralPreliminaryValidator()
        self.standard = standard
        self._samples = []
        self.is_sample_group = True
        self.aggregation_strategy = aggregation_strategy or {}
        self.property_calculator = property_calculator or GroupAggregationOperator()

        if samples:
            for sample in samples:
                self.add_sample(sample)

        # # Aggregate sample properties and data using GroupAggregationOperator.
        # aggregated_properties = self._aggregate_properties()
        # aggregated_data = self._aggregate_data()

        # # Initialize the base class with the aggregated values.
        # super().__init__(
        #     name="SampleGroup",
        #     length=aggregated_properties.get("length"),
        #     width=aggregated_properties.get("width"),
        #     thickness=aggregated_properties.get("thickness"),
        #     mass=aggregated_properties.get("mass"),
        #     area=aggregated_properties.get("area"),
        #     volume=aggregated_properties.get("volume"),
        #     density=aggregated_properties.get("density"),
        #     force=aggregated_data.get("force"),
        #     displacement=aggregated_data.get("displacement"),
        #     stress=aggregated_data.get("stress"),
        #     strain=aggregated_data.get("strain"),
        # )

    @exportable_property(output_name="Samples", category="children")
    def samples(self) -> list[AnalyzableEntity]:
        # List of associated sample entities
        return self._samples

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
        # self._standardize_sample_units(sample)

        self._samples.append(sample)
        # self._update_aggregated_properties()

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

    def _aggregate_properties(self) -> dict:
        raise NotImplementedError("Not implemented yet.")

    def _aggregate_data(self) -> dict:
        raise NotImplementedError("Not implemented yet.")

    def plot(self) -> None:
        """
        Plot key performance indicators (KPI) relevant to the standard being used.
        This method must be implemented by subclasses to provide standard-specific views.
        """
        raise NotImplementedError("Subclasses must implement this method.")
