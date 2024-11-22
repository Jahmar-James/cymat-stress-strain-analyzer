from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Optional, Union

import pandas as pd
import pint

from ..data_extraction import MechanicalTestDataPreprocessor


@dataclass
class PropertyData:
    """Encapsulates property details."""

    value: Union[float, pd.Series, None]  # Property value
    unit: pint.Unit  # Target unit (output unit) - default is internal unit
    uncertainty: Optional[Union[float, pd.Series]] = None
    _calculator: Optional[Callable[[], Union[float, pd.Series]]] = None

    def __post_init__(self):
        if self.value is not None and not isinstance(self.value, (int, float, pd.Series)):
            raise ValueError("Property value must be a scalar or pandas Series.")
        if self.unit is None:
            raise ValueError("Property unit not set.")

    def compute(self) -> Union[float, pd.Series]:
        """Computes the property value using the calculator function."""
        if self._calculator is None:
            raise ValueError("Calculator function not set.")

        value = self._calculator()
        if isinstance(value, (int, float, pd.Series)):
            self.value = value
        elif value is None:
            raise ValueError("Calculator function returned None.")
        else:
            if value:
                setattr(self, "metadata", value)
        return value


class PropertyManager:
    def __init__(self, internal_units: dict[str, pint.Unit], preprocessor: MechanicalTestDataPreprocessor):
        """
        Manages property operations such as unit conversions and uncertainties.

        Parameters:
        - internal_units (dict): Dictionary of internal units for each property.
        - preprocessor: A preprocessor instance for handling unit conversion.
        """
        self._properties: dict[str, PropertyData] = {}
        self._internal_units = internal_units
        self._uncertainty = {}
        self._preprocessor = preprocessor
        # TODO Register dependent properties calling the recalcaulte method

    def set_property(self, name: str, value: Union[float, pd.Series], unit: Optional[pint.Unit] = None) -> bool:
        """Sets a property value and its unit."""
        if name not in self._internal_units:
            raise ValueError(f"Property '{name}' is not defined in internal units.")
        self._properties[name] = PropertyData(value=value, unit=unit or self._internal_units[name])
        return bool(name in self._properties)

    # Gettters

    def get_property(self, name: str) -> PropertyData:
        """Retrieves a property."""
        property_data = self._properties.get(name)
        if not property_data:
            raise KeyError(f"Property '{name}' is not registered.")

        # Lazy evaluation
        if property_data.value is None and property_data._calculator:
            property_data.compute()
        return property_data

    def get_property_with_units_and_uncertainty(
        self,
        name: str,
    ) -> tuple[Union[float, pd.Series, None], pint.Unit, Union[float, pd.Series, None]]:
        """Gets the property value, its unit, and its uncertainty."""
        property_data = self._properties.get(name)
        if not property_data:
            raise KeyError(f"Property '{name}' is not registered.")
        return property_data.value, property_data.unit, property_data.uncertainty

    def list_properties(self) -> list[str]:
        """Lists all properties."""
        return list(self._properties.keys())

    def get_internal_units(self, name) -> Union[dict[str, pint.Unit], pint.Unit]:
        """Returns a dictionary of property units."""
        if name in self._internal_units:
            return self._internal_units[name]
        return self._internal_units

    # Unis Management

    def set_target_unit(self, name: str, target_unit: Union[str, pint.Unit]) -> bool:
        """Sets the target unit for a property."""
        if isinstance(target_unit, str):
            target_unit = self._preprocessor.unit_registry.parse_units(target_unit)
        elif not isinstance(target_unit, pint.Unit):
            raise TypeError("target_unit must be a str or pint.Unit.")
        if name in self._properties:
            self._properties[name].unit = target_unit
        else:
            raise ValueError(f"Property '{name}' not found.")
        return bool(name in self._properties)

    def convert_property(
        self, name: str, return_value_only: bool = False
    ) -> Union[PropertyData, float, pd.Series, None]:
        """Converts a property value to its target unit."""
        if name not in self._properties:
            raise ValueError(f"Property '{name}' not found.")

        property_data = self._properties[name]
        if property_data.value is None:
            return None

        # Copy the data to ensure immutability
        converted_data = deepcopy(property_data)

        if not converted_data.value:
            return None

        current_unit = self._internal_units.get(name)
        target_unit = property_data.unit

        if target_unit and current_unit and target_unit != current_unit:
            conversion_factor = self._preprocessor._get_conversion_factor(current_unit, target_unit)
            if not isinstance(conversion_factor, (float, int)):
                raise ValueError(f"Conversion factor for '{name}' is not a scalar.")

            converted_data.value *= conversion_factor

            if converted_data.uncertainty:
                converted_data.uncertainty *= conversion_factor

        return converted_data if not return_value_only else converted_data.value

    def ensure_properties_same_unit(
        self, properties: list[str], target_unit: pint.Unit
    ) -> dict[str, Union[float, pd.Series]]:
        """Ensures that all properties are in the same unit and returns the converted values."""
        converted_properties = {}
        for prop in properties:
            property_data = self.get_property(prop)
            if property_data is None or property_data.value is None:
                raise ValueError(f"Property '{prop}' is missing or has no value.")
            current_unit = property_data.unit
            if current_unit != target_unit:
                converted_value = self.convert_property(prop, return_value_only=True)
                converted_properties[prop] = converted_value
            else:
                converted_properties[prop] = property_data.value
        return converted_properties

    # Uncertainty Management

    def set_uncertainty(self, name: str, uncertainty: Union[str, float], type_: str = "absolute") -> bool:
        """Sets or updates uncertainty for a property."""
        if name not in self._properties:
            raise ValueError(f"Property '{name}' not found.")

        property_data = self._properties[name]
        if type_ == "relative":
            if property_data.value is None:
                raise ValueError(f"Cannot set relative uncertainty for '{name}' because its value is not set.")
            if isinstance(uncertainty, (int, float)):
                uncertainty = f"{uncertainty}%"
            absolute_uncertainty = property_data.value * (float(uncertainty.strip("%")) / 100)
        elif type_ == "absolute":
            absolute_uncertainty = float(uncertainty)
        else:
            raise ValueError("Uncertainty type must be 'absolute' or 'relative'.")
        # Store internally as absolute
        property_data.uncertainty = absolute_uncertainty
        self._uncertainty[name] = absolute_uncertainty
        return bool(property_data.uncertainty is not None)

    @staticmethod
    def convert_uncertainty(value, uncertainty, conversion_type="absolute"):
        """
        Convert uncertainty between absolute and relative formats.
        """
        if uncertainty is None:
            return None

        if conversion_type == "absolute":
            if isinstance(uncertainty, str) and uncertainty.endswith("%"):
                # Convert relative (e.g., "5%") to absolute
                return (float(uncertainty.strip("%")) / 100) * value
            return uncertainty  # Already absolute
        elif conversion_type == "relative":
            if isinstance(uncertainty, (int, float)):
                # Convert absolute to relative
                return f"{(uncertainty / value) * 100:.2f}%"
            return uncertainty  # Already relative
        else:
            raise ValueError(f"Unsupported conversion type: {conversion_type}")

    @staticmethod
    def attempt_unit_math(expression: Callable, result_unit: Optional[pint.Unit]):
        try:
            return expression()
        except AttributeError:
            # One of the values is None
            return result_unit
        except pint.DimensionalityError:
            # Units are incompatible
            return result_unit

    # Calculators and Caching

    def set_calculator(self, name: str, calculator: Callable[[], Union[float, pd.Series]]) -> bool:
        """Sets a calculator function for a property."""
        if name in self._properties:
            self._properties[name]._calculator = calculator
        else:
            raise ValueError(f"Property '{name}' not found.")
        return bool(name in self._properties)

    def set_calculators(self, calculator_map: dict[str, Callable[[], Union[float, pd.Series]]]) -> None:
        """Sets calculator functions for multiple properties."""
        for name, calculator in calculator_map.items():
            self.set_calculator(name, calculator)

    def invalidate_cache(self, name) -> bool:
        """Invalidates the cache for a property."""
        if name in self._properties:
            self._properties[name].value = None
            return bool(self._properties[name].value is None)
        else:
            raise ValueError(f"Property '{name}' not found.")

    def recalculate_property(self, name: str) -> Optional[PropertyData]:
        """Recomputes a property value using a given function."""
        self.invalidate_cache(name)
        return self.get_property(name)

    def recalculat_all_calculable_properties(self) -> None:
        """Recalculates all properties with calculators."""
        for name in self._properties:
            if self._properties[name]._calculator:
                self.recalculate_property(name)


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
    ) -> list:
        """Ensure all samples have consistent units for a given property."""
        converted_values = []
        for sample in samples:
            property_data = sample.property_manager.get_property(property_name)
            if property_data is None or property_data.value is None:
                # TODO Skip or log the missing property - continue
                raise ValueError(f"Sample '{sample.name}' is missing property '{property_name}'.")
            if property_data.unit != target_unit:
                converted_value = sample.property_manager.convert_property(property_name, return_value_only=True)
                converted_values.append(converted_value)
            else:
                converted_values.append(property_data.value)
        return converted_values

    @staticmethod
    def aggregate_scalar_property(
        samples: list["AnalyzableEntity"],
        property_name: str,
        internal_units: dict[str, pint.Unit],
        method: str = "mean",
        uncertainty: bool = False,
    ) -> float:
        """Aggregate scalar properties for the group."""
        target_unit = internal_units.get(property_name)
        values = EntityGroupManager.ensure_units_consistent(samples, property_name, target_unit)

        if uncertainty:
            raise NotImplementedError("Uncertainty aggregation not yet implemented.")
            # Handle uncertainties during aggregation
            uncertainties = [sample.property_manager.get_property(property_name).uncertainty for sample in samples]
            aggregated_uncertainty = GroupAggregationOperator().aggregate_uncertainties(uncertainties, method)

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


from ..properties_calculators.base_standard_operator import BaseStandardOperator
from ..properties_calculators.group_aggeregation_calculator import GroupAggregationOperator


class AnalyzableEntity:
    def __init__(
        self,
        name: str,
        preprocessor: MechanicalTestDataPreprocessor,
        property_calculator: BaseStandardOperator = BaseStandardOperator(),
        property_calculator_group: GroupAggregationOperator = GroupAggregationOperator(),
        length: Optional[float] = None,
        width: Optional[float] = None,
        thickness: Optional[float] = None,
        mass: Optional[float] = None,
        area: Optional[float] = None,
        volume: Optional[float] = None,
        density: Optional[float] = None,
        force: Optional[pd.Series] = pd.Series(dtype="float64", name="force"),
        displacement: Optional[pd.Series] = pd.Series(dtype="float64", name="displacement"),
        time: Optional[pd.Series] = pd.Series(dtype="float64", name="time"),
        stress: Optional[pd.Series] = pd.Series(dtype="float64", name="stress"),
        strain: Optional[pd.Series] = pd.Series(dtype="float64", name="strain"),
    ) -> None:
        # Typically Required properties
        self.name = name
        self.length = length
        self.width = width
        self.thickness = thickness
        self.mass = mass
        self._force = force
        self._displacement = displacement
        index = pd.Series(range(len(self._force)), name="index")
        self._time = time if (isinstance(time, pd.Series) and not time.empty) else index

        self.group_manager = EntityGroupManager()
        self.is_sample_group: bool = False
        self._samples: list[AnalyzableEntity] = []

        self._internal_units: dict[str, pint.Unit] = MechanicalTestDataPreprocessor.EXPECTED_UNITS.copy()

        self.analysis_standard: Optional[MechanicalTestStandards] = None  # Associated analysis standard

        # Optional properties that can be calculated from the required properties
        self._area = area
        self._volume = volume
        self._density = density
        self._stress = stress
        self._strain = strain

        self.property_manager = PropertyManager(self._internal_units, preprocessor)
        self.property_calculator_individual = property_calculator
        self.property_calculator_group = property_calculator_group

        self._calculator_map = {
            "stress": self._calculate_stress if not self.is_sample_group else self._calculate_stress_strain_group,
            "strain": self._calculate_strain if not self.is_sample_group else self._calculate_stress_strain_group,
        }

        self.set_properties()

    def set_properties(self, calculator_map: dict = {}) -> None:
        internal_units = self._internal_units
        # Register common properties with calculators
        self.property_manager.set_property("force", value=self._force, unit=internal_units["force"])
        self.property_manager.set_property("area", value=self._area, unit=internal_units["area"])
        self.property_manager.set_property("stress", value=self._stress, unit=internal_units.get("stress"))

        calculator_map = calculator_map or self._calculator_map
        self.property_manager.set_calculators(calculator_map)

    # Property calculation methods

    @property
    def stress(self) -> Optional[pd.Series]:
        return self.property_manager.get_property("stress").value

    def _calculate_stress(self):
        """Calculate stress = force / area. For individual samples."""
        force = self.property_manager.get_property("force")
        area = self.property_manager.get_property("area")

        stress_value, stress_uncertainty = self.property_calculator_individual.calculate_stress(
            force_series=force.value,
            area=area.value,
            force_uncertainty=force.uncertainty,
            area_uncertainty=area.uncertainty,
        )

        self.property_manager.set_property(
            "stress",
            value=stress_value,
            unit=self.property_manager.attempt_unit_math(lambda: force.unit / area.unit, None),
        )
        self.property_manager.set_uncertainty("stress", stress_uncertainty, type_="absolute")
        return stress_value

    def _calculate_stress_strain_group(self):
        """Calculate stress = force / area. For sample groups."""
        if not self.is_sample_group:
            raise ValueError("Should not be called for individual samples.")

        interpolated_df = self.group_manager.aggregate_series_property(
            samples=self._samples,
            y_column="stress",
            x_column="strain",
            internal_units=self._internal_units,
            method="mean",
        )

        if interpolated_df is not None and (isinstance(interpolated_df, pd.DataFrame) and not interpolated_df.empty):
            stress_value = interpolated_df["avg_stress"].rename("stress")
            strain_value = interpolated_df["strain"]

            stress_unit = self._samples[0].property_manager.get_internal_units("stress")
            strain_unit = self._samples[0].property_manager.get_internal_units("strain")

            self.property_manager.set_property("stress", value=stress_value, unit=stress_unit)
            self.property_manager.set_property("strain", value=strain_value, unit=strain_unit)

        return interpolated_df

    def _calculate_strain(self):
        """Calculate strain for individual samples."""
        displacement = self.property_manager.get_property("displacement")
        length = self.property_manager.get_property("length")

        strain_value, strain_uncertainty = self.property_calculator_individual.calculate_strain(
            displacement_series=displacement.value,
            initial_length=length.value,
            displacement_uncertainty=displacement.uncertainty,
            length_uncertainty=length.uncertainty,
        )

        self.property_manager.set_property(
            "strain",
            value=strain_value,
            unit=pint.Unit("dimensionless"),
        )
        self.property_manager.set_uncertainty("strain", strain_uncertainty, type_="absolute")
        return strain_value
        return strain_value
