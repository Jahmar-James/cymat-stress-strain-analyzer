from typing import TYPE_CHECKING, Union

import pandas as pd
import pint

from ..properties_calculators.base_standard_operator import BaseStandardOperator
from ..properties_calculators.group_aggeregation_calculator import GroupAggregationOperator
from .properties import PropertyData

if TYPE_CHECKING:
    from ...standard_base.entities.analyzable_entity import AnalyzableEntity
    from ...standard_base.sample_factory import MechanicalTestStandards


class EntityGroupManager:
    """
    Manages a group of entities for analysis.
    """

    @staticmethod
    def validate_samples(samples: list["AnalyzableEntity"], standard: "MechanicalTestStandards") -> None:
        """Validate that all samples conform to the specified standard."""
        for sample in samples:
            if sample.analysis_standard != standard:
                raise ValueError(f"Sample '{sample.name}' does not conform to the group standard '{standard}'.")

    @staticmethod
    def ensure_units_consistent(
        samples: list["AnalyzableEntity"],
        property_name: str,
        target_unit: pint.Unit,
    ) -> list[PropertyData]:
        """Ensure all samples have consistent units for a given property."""
        converted_values = []
        for sample in samples:
            property_data = sample.property_manager.get_property(property_name)
            if property_data is None or property_data.value is None:
                # TODO Skip or log the missing property - continue
                raise ValueError(f"Sample '{sample.name}' is missing property '{property_name}'.")
            if property_data.unit != target_unit:
                converted_value = sample.property_manager.convert_property(property_name)
                converted_values.append(converted_value)
            else:
                converted_values.append(property_data)
        return converted_values

    @staticmethod
    def aggregate_scalar_property(
        samples: list["AnalyzableEntity"],
        property_name: str,
        target_unit: pint.Unit,
        method: str = "mean",
        uncertainty: bool = False,
    ) -> float:
        """Aggregate scalar properties for the group."""
        target_unit = target_unit or samples.internal_units.get(property_name)
        consistant_properties = EntityGroupManager.ensure_units_consistent(samples, property_name, target_unit)

        if uncertainty:
            raise NotImplementedError("Uncertainty aggregation not yet implemented.")
            # Handle uncertainties during aggregation
            uncertainties = [sample.property_manager.get_property(property_name).uncertainty for sample in samples]
            aggregated_uncertainty = GroupAggregationOperator().aggregate_uncertainties(uncertainties, method)

        values = [property_data.value for property_data in consistant_properties]
        assert all(isinstance(value, (int, float)) for value in values), "All values must be numeric."
        return GroupAggregationOperator().aggregate_scalar_properties(values, method)

    @staticmethod
    def aggregate_series_property(
        samples: list["AnalyzableEntity"],
        y_column: str,
        x_column: str,
        internal_units: dict[str, pint.Unit],
        method: str = "mean",
    ) -> Union[pd.Series, pd.DataFrame]:
        """Aggregate series properties for the group."""
        target_y_unit = internal_units.get(y_column)
        target_x_unit = internal_units.get(x_column)

        y_values = EntityGroupManager.ensure_units_consistent(samples, y_column, target_y_unit)
        x_values = EntityGroupManager.ensure_units_consistent(samples, x_column, target_x_unit)

        if method == "mean":
            dfs = []
            for sample, y_value, x_value in zip(samples, y_values, x_values):
                dfs.append(pd.DataFrame({x_column: x_value, y_column: y_value}))

            step_size = GroupAggregationOperator().get_step_size_for_avg_agg(dfs, x_column)
            return BaseStandardOperator.average_dataframes(dfs, y_column, x_column, step_size)
        else:
            raise ValueError(f"Unsupported aggregation method: {method}")
