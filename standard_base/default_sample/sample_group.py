from typing import Optional

import pandas as pd

from standard_base import MechanicalTestStandards
from standard_base.entities.analyzable_entity import AnalyzableEntity, exportable_property
from standard_base.properties_calculators.base_standard_operator import BaseStandardOperator
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
        name: str,
        standard: MechanicalTestStandards = MechanicalTestStandards.GENERAL_PRELIMINARY,
        samples: Optional[list[AnalyzableEntity]] = None,
        aggregation_strategy: Optional[dict] = None,
        validator: Optional["BaseStandardValidator"] = None,
        property_calculator: Optional["GroupAggregationOperator"] = None,
    ):
        super().__init__(name)

        self.validator = validator  # TODO GeneralPreliminaryValidator()
        self.analysis_standard = standard
        self._samples = []
        self.is_sample_group = True
        self.aggregation_strategy = aggregation_strategy or {}
        self.property_calculator = property_calculator or GroupAggregationOperator()

        if samples:
            for sample in samples:
                self.add_sample(sample)

        # Aggregate sample properties and data using GroupAggregationOperator.
        self._aggregated_properties = None
        self._aggregated_data = None

        self.update_aggregated_properties()
        self.update_seralized_attributes()

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
        if sample.analysis_standard != self.analysis_standard:
            raise ValueError(
                f"Sample '{sample.name}' does not conform to the group standard '{self.analysis_standard}'."
            )

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
            internal_unit = self._internal_units.get(prop)
            sample_unit = sample._internal_units.get(prop)
            if internal_unit and sample_unit and internal_unit != sample_unit:
                converted_value = sample._convert_units(
                    value=getattr(sample, f"_{prop}"), current_unit_key=prop, target_unit=internal_unit
                )
                setattr(sample, f"_{prop}", converted_value)

    def update_aggregated_properties(self) -> None:
        """
        Recalculate and update aggregated properties after adding or modifying samples.
        """
        aggregated_properties = self._aggregate_properties()
        self._aggregated_properties = aggregated_properties
        self._area = aggregated_properties.get("area")
        self._volume = aggregated_properties.get("volume")
        self._density = aggregated_properties.get("density")
        self._mass = aggregated_properties.get("mass")

        # independent variables time, displacement, strain (should not be interpolated - select a common axis)
        # dependent variables force, stress (can be interploate if varying sample length or sample rates)
        # time, displacement, force must be supplied
        self.update_force_and_displacement()
        self.update_stress_and_strain()

    def recalculate_properties(self, property_name: str) -> None:
        """
        Override to handle recalculation of group-level properties.
        """
        if hasattr(self, f"_{property_name}"):
            setattr(self, f"_{property_name}", None)
            self.update_aggregated_properties()
        else:
            raise ValueError(f"Property {property_name} does not exist.")

    def _aggregate_properties(self, method="mean") -> dict:
        """
        Aggregate properties of all samples in the group using the specified aggregation strategy.
        """
        aggregated_properties = {}
        if self._aggregated_properties is None:
            for prop in ["length", "width", "thickness", "mass", "area", "volume", "density"]:
                values = [getattr(sample, f"{prop}") for sample in self._samples]
                aggregated_properties[prop] = self.property_calculator.aggregate_scalar_properties(values, method)

        return aggregated_properties

    def update_stress_and_strain(self, step_size=None) -> None:
        dfs = [sample.processed_data for sample in self._samples]
        if all(["stress" in df.columns and "strain" in df.columns for df in dfs]):
            step_size = step_size or self.property_calculator.get_step_size_for_avg_agg(dfs, "strain")
            df = BaseStandardOperator.average_dataframes(
                df_list=dfs,
                avg_columns="stress",
                interp_column="strain",
                step_size=step_size,
            )
            setattr(self, "_stress", df["avg_stress"])
            setattr(self, "_strain", df["strain"])

    def update_force_and_displacement(self, step_size=None) -> None:
        dfs = [sample.processed_data for sample in self._samples]
        if all(["force" in df.columns and "displacement" in df.columns for df in dfs]):
            step_size = step_size or self.property_calculator.get_step_size_for_avg_agg(dfs, "displacement")
            df = BaseStandardOperator.average_dataframes(
                df_list=dfs,
                avg_columns="force",
                interp_column="displacement",
                step_size=step_size,
            )
            setattr(self, "_force", df["avg_force"])
            setattr(self, "_displacement", df["displacement"])

    def _aggergate_tables(self, table_columns: list[str]) -> pd.DataFrame:
        dfs = [sample.processed_data for sample in self._samples]

        table_columns = table_columns or dfs[0].columns
        table_values = {}
        for column in table_columns:
            values_list = [df[column] for df in dfs]
            table_values[column] = pd.DataFrame(values_list, index=[sample.name for sample in self._samples])

        combined_df = pd.concat(table_values.values(), axis=1)
        return combined_df

    def plot(self) -> None:
        """
        Plot key performance indicators (KPI) relevant to the standard being used.
        This method must be implemented by subclasses to provide standard-specific views.
        """
        raise NotImplementedError("Subclasses must implement this method.")
