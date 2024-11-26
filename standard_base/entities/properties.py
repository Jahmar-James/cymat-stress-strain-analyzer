import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Optional, Union

import pandas as pd
import pint

from ..data_extraction import MechanicalTestDataPreprocessor

# DO I plan on make yoy frozen, no? then make it a class
# aadd normalization internal

# Property Data Class -----------------


@dataclass
class PropertyData:
    """Encapsulates property details."""

    value: Union[float, pd.Series, None]  # Property value
    unit: Optional[pint.Unit] = None  # Target unit (output unit) - default is internal unit
    uncertainty: Optional[Union[float, pd.Series]] = None
    _calculator: Optional[Callable[[], Union[float, pd.Series, "PropertyData"]]] = None
    property_id: Optional[str] = None
    metadata: Optional[dict] = None

    def __post_init__(self):
        if self.value is not None and not isinstance(self.value, (int, float, pd.Series)):
            raise ValueError("Property value must be a scalar or pandas Series.")

    def compute(self) -> "PropertyData":
        """Computes the property value using the calculator function."""
        if self._calculator is None:
            raise ValueError("Calculator function not set.")

        calculated_result = self._calculator()

        if isinstance(calculated_result, PropertyData):
            calculated_result = calculated_result.value

        if isinstance(calculated_result, (int, float, pd.Series)):
            self.value = calculated_result
        elif calculated_result is None:
            logging.warning(f"Calculator for '{self.property_id}' returned None.")
            self.value = None
        else:
            if calculated_result:
                setattr(self, "metadata", calculated_result)
        return self


# Property Manager Class -----------------


class PropertyManager:
    def __init__(
        self,
        preprocessor: MechanicalTestDataPreprocessor,
        internal_units: dict[str, pint.Unit] = None,
        uncertainty: dict[str, Union[float, pd.Series]] = None,
    ):
        """
        Manages property operations such as unit conversions and uncertainties.

        Parameters:
        - internal_units (dict): Dictionary of internal units for each property.
        - preprocessor: A preprocessor instance for handling unit conversion.
        """
        self._properties: dict[str, PropertyData] = {}
        self._preprocessor = preprocessor

        internal_units = internal_units or self._preprocessor.EXPECTED_UNITS.copy()
        self._internal_units: dict[str, pint.Unit] = internal_units
        """
        Unit Management:
        - internal_units (dict): Dictionary to store and convert units for each property, using pint units.
            Example: `internal_units['force'] = ureg.newton`
        - target_units (dict): Dictionary for storing target units for conversion purposes.
        """

        self._uncertainty: dict[str, Union[float, pd.Series]] = uncertainty or {}
        """
        Uncertainty Management:
        - Stores uncertainty values for each property.
        - Example: `uncertainty['force'] = {'value': pd.Series, float, str, 'type': 'absolute'}` where type is either
          'relative' or 'absolute'. A string value such as '5%' indicates a relative uncertainty.
        """

        # Key Performance Indicators (KPIs)
        # self._kpis: dict[str, Value] = {}
        """
        Key Performance Indicators (KPIs):
        - Stores custom calculations depending on the applied mechanical test standard.
        - Example: `self._kpis['strength'] = 250` (strength could be a calculated property such as maximum stress).
        """

        # TODO Register dependent properties calling the recalcaulte method

    # Property Management -----------------

    def set_property(
        self,
        name: str,
        value: Union[float, pd.Series],
        target_unit: Optional[pint.Unit] = None,
        internal_unit: Optional[pint.Unit] = None,
        uncertainty: Optional[Union[float, pd.Series]] = None,
    ) -> bool:
        """Sets a property value and its unit."""

        if internal_unit and isinstance(internal_unit, pint.Unit):
            self._internal_units[name] = internal_unit

        if name not in self._internal_units:
            raise ValueError(f"Property '{name}' is not defined in internal units. Cannot set property without a unit.")

        self._properties[name] = PropertyData(
            value=value,
            unit=target_unit or self._internal_units[name],
            property_id=name,
            uncertainty=uncertainty,
        )
        return bool(name in self._properties)

    def get_property(self, name: str) -> PropertyData:
        """Retrieves a property."""
        property_data = self._properties.get(name)
        if not property_data:
            raise KeyError(f"Property '{name}' is not registered.")

        if isinstance(property_data.value, (pd.Series, pd.DataFrame)) and property_data.value.empty:
            property_data.value = None

        # Lazy evaluation
        if property_data.value is None and property_data._calculator:
            property_data.compute()

        if property_data.value is None and property_data._calculator is None:
            logging.warning(f"Property '{name}' has no value or calculator function.")
            return property_data

        return self.convert_property(property_data=property_data)

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

    def get_internal_units(self, name: str = "") -> Union[dict[str, pint.Unit], pint.Unit]:
        """Returns a dictionary of property units."""
        if name in self._internal_units:
            return self._internal_units[name]
        return self._internal_units

    # Unis Management -----------------

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

    def reset_all_target_units(self) -> None:
        """Resets all target units to internal units."""
        for name in self._properties:
            self._properties[name].unit = self._internal_units.get(name)

    def reset_target_unit(self, name: str) -> bool:
        """Resets the target unit to the internal unit."""
        if name in self._properties:
            self._properties[name].unit = self._internal_units.get(name)
        else:
            raise ValueError(f"Property '{name}' not found.")
        return bool(self._properties[name].unit == self._internal_units.get(name))

    def convert_property(
        self, name: str = "", return_value_only: bool = False, property_data: Optional[PropertyData] = None
    ) -> Union[PropertyData, float, pd.Series, None]:
        """Converts a property value to its target unit."""

        if property_data is None:
            if name not in self._properties:
                raise ValueError(f"Property '{name}' not found.")

            property_data = self._properties[name]
            if property_data.value is None:
                return None

        # Copy the data to ensure immutability
        converted_data = deepcopy(property_data)

        if converted_data.value is None:
            return None

        current_unit = self._internal_units.get(name or property_data.property_id)
        target_unit = property_data.unit

        if target_unit and current_unit and target_unit != current_unit:
            conversion_factor = self._preprocessor._get_conversion_factor(current_unit, target_unit)
            if not isinstance(conversion_factor, (float, int)):
                raise ValueError(f"Conversion factor for '{name}' is not a scalar.")

            converted_data.value *= conversion_factor

            if converted_data.uncertainty:
                converted_data.uncertainty *= conversion_factor

        return converted_data if not return_value_only else converted_data.value

    def ensure_properties_same_units(self, properties: list[str], target_unit: pint.Unit) -> dict[str, PropertyData]:
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
                converted_properties[prop] = property_data
        return converted_properties

    # Uncertainty Management -----------------

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


# Decorator for exporting properties -----------------


def exportable_property(unit=None, output_name=None, category="attributes"):
    """
    A decorator to mark properties for export with optional additional metadata.

        This decorator dynamically retrieves the value of the property every time it is accessed.
        This means that the most up-to-date value is fetched whenever the property is called or
        exported, allowing for dynamic data that may change during the object's lifecycle.

        Parameters:
        -----------
        unit: str or None
            Optional unit for the property (e.g., 'cm', 'kg'). Defaults to None if no unit is needed.

        output_name: str, list, or None
            For 'attributes' category:
                - The custom name to be used when exporting the property. If None, the property's
                name is used.
            For 'data' category:
                - A list of column names or the name of the series to be used when exporting
                the `pandas.Series` or `pandas.DataFrame` object.
                - This value defines how the columns or data series are labeled when serialized.
                - Example: ['Force [N]', 'Displacement [mm]', 'Stress [MPa]', 'Strain'] for a
                `pandas.DataFrame`.

        category: str
            The category under which the property should be registered:
            - 'attributes': for simple object properties.
            - 'data': for complex data such as `pandas.Series` or `pandas.DataFrame`.

        Note:
        -----
        - For attributes, `output_name` is used as a display name for serialization.
        - For data (e.g., `pandas.Series` or `pandas.DataFrame`), `output_name` refers to the names of
        the columns or the name of the series when serialized. The data itself is saved in a file
        named "{property_name}_data.csv", and the `output_name` defines the labels used in that file.
    """

    def decorator(func):
        # Attach metadata to the function
        func._is_exportable = True
        func._export_metadata = {
            "unit": unit,
            "output_name": output_name or func.__name__.capitalize(),
            "category": category,
        }
        return property(func)

    return decorator
