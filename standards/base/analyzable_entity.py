import datetime
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, TypeAlias, Union

import numpy as np
import pandas as pd
import pint

from data_extraction import MechanicalTestDataPreprocessor
from visualization.plot_config import PlotConfig
from visualization.plot_manager import PlotManager

from .base_io_management.serializer import AttributeField, Serializer
from .properties_calculators.base_standard_operator import BaseStandardOperator

if TYPE_CHECKING:
    from visualization.plot import Plot

    from ..sample_factory import MechanicalTestStandards

Value: TypeAlias = Union[float, int, pd.Series, pd.DataFrame, np.ndarray]
from collections import namedtuple

entity_property = namedtuple("entity_property", ["value", "uncertainty", "unit"])


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


class DataState(Enum):
    RAW = "raw"
    PREPROCESSED = "preprocessed"
    VALIDATED = "validated"
    ANALYZED = "analyzed"


class AnalyzableEntity(ABC):
    """
    Base class for Mechanical Testing sample objects that require data processing and plotting.
    Examples: A single Sample or a Collection of Samples.

    **Responsibilities:**

    - Define a common interface for subclasses, ensuring consistency in accessing key properties and methods.
        - Each subclass should define how key properties and methods are accessed and used.
        - For example, `SampleGeneric` must implement `_Strength` as part of the `AnalyzableEntity` interface.
    - Utilize `BaseStandardOperator` for performing calculations and processing data.
    - Assume that input data has been preprocessed and normalized according to `MechanicalTestDataPreprocessor`.

     Attributes:
    - internal_units (dict[str, pint.Unit]): Stores internal units for each property which all calculations are based on.
        - Example: `internal_units['force'] = ureg.newton`
    - target_units (dict[str, pint.Unit]): Stores the target units for each property, to be set if unit desired is different from internal units.
    - uncertainty (dict[str, Union[float, str]]): Stores uncertainty values for each property.
        - Expected format: `uncertainty['force'] = {'value': pd.Series or float, 'type': 'absolute'}` where type is either "relative" or "absolute".
    - _kpis (dict[str, any]): Stores flexible and custom calculations dependent on the standard (e.g., Strength, Young's Modulus).
    """

    def __init__(
        self,
        name: str,
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
        specialized_data: Optional[dict] = None,
        property_calculator: BaseStandardOperator = BaseStandardOperator(),
        plot_manager: PlotManager = PlotManager(),
        test_metadata: Optional[dict] = None,
        has_hysteresis: bool = False,
        uncertainty: Optional[dict] = None,
    ):
        """
        Initializes the AnalyzableEntity with various attributes for mechanical testing data.


        Parameters:
        - name (str): The name of the sample.
        - length, width, thickness, mass (Optional[float]): Physical properties of the sample.
        - force, displacement, stress, strain (Optional[pd.Series]): Data series related to the sample's performance.
        - property_calculator (Optional[BaseStandardOperator]): A helper class for performing calculations.
        - plot_manager (Optional[PlotManager]): A helper class for plotting results.

        Notes
            _ prefix indicates that the property is cached and can be converted to different units
        """
        # Typically Required properties
        self.name = name
        self.length = length
        self.width = width
        self.thickness = thickness
        self.mass = mass
        # Create Empty Series if None to ensure data aligns for dataframe eg. raw_data which is used for export
        self._force = force
        self._displacement = displacement
        index = pd.Series(range(len(self._force)), name="index")
        self._time = time if (isinstance(time, pd.Series) and not time.empty) else index

        # Optional properties that can be calculated from the required properties
        self._area = area
        self._volume = volume
        self._density = density
        self._stress = stress
        self._strain = strain

        # Hysteresis data | Specialized data
        self.specialized_data = specialized_data or {}

        # TODO: Add a method to update raw data names with units and for exporting
        # dataframe columns will always be lowercase to ensure consistency
        self._raw_data = pd.DataFrame(
            {"force": self._force, "displacement": self._displacement, "stress": self._stress, "strain": self._strain}
        )

        # Entity determination
        self.analysis_standard: Optional["MechanicalTestStandards"] = None  # Associated analysis standard
        self.software_version: str = "1.0"  # Software version used to generate the entity
        self.entity_version: str = "1.0"  # Entity version revision management for entity standard implementation
        self.database_id: Optional[int] = None  # Database identifier (if applicable)
        self.created_at: str = datetime.datetime.now().isoformat()  # ISO 8601 format for creation time
        self.last_modified_at: Optional[str] = None  # Last modified timestamp in ISO 8601 format
        self.data_state: DataState = DataState.RAW  # Current state of the data (raw, preprocessed, validated, etc.)
        self.is_data_valid: bool = False  # Indicates if the data has been validated
        self.is_saved: bool = False  # Indicates if the entity has been saved
        self.has_hysteresis: bool = has_hysteresis  # True if the sample has hysteresis data
        self.is_visualization_only: bool = False  # True if entity is for visualization purposes only
        self.is_sample_group: bool = False  # True if the entity represents a collection of samples
        self.samples: list[AnalyzableEntity] = []  # List of associated sample entities
        self.tags = []  # Tags associated with the entity

        # Dependency inversion class helpers
        self.plot_manager = plot_manager
        self.property_calculator = property_calculator
        self.data_preprocessor = MechanicalTestDataPreprocessor()
        self.serializer = Serializer(tracked_object=self)

        # Test metadata
        self.test_metadata = test_metadata or {}  # e.g. test conditions, operator, machine, etc.

        # Unit Management
        self._internal_units: dict[str, pint.Unit] = MechanicalTestDataPreprocessor.EXPECTED_UNITS.copy()
        self._target_units: dict[str, pint.Unit] = {}
        """
        Unit Management:
        - internal_units (dict): Dictionary to store and convert units for each property, using pint units.
            Example: `internal_units['force'] = ureg.newton`
        - target_units (dict): Dictionary for storing target units for conversion purposes.
        """

        # Uncertainty management
        self._uncertainty: dict[str, Union[float, str]] = uncertainty or {}
        """
        Uncertainty Management:
        - Stores uncertainty values for each property.
        - Example: `uncertainty['force'] = {'value': pd.Series, float, str, 'type': 'absolute'}` where type is either
          'relative' or 'absolute'. A string value such as '5%' indicates a relative uncertainty.
        """

        # Key Performance Indicators (KPIs)
        self._kpis: dict[str, Value] = {}
        """
        Key Performance Indicators (KPIs):
        - Stores custom calculations depending on the applied mechanical test standard.
        - Example: `self._kpis['strength'] = 250` (strength could be a calculated property such as maximum stress).
        """

        # Exportable Fields
        self._exportable_fields: list[AttributeField] = self._initialize_exportable_fields()

        if self.has_hysteresis:
            self._initialize_hysteresis()

        # Register all public attributes for serializatiom ( all attributes not starting with _ ) Exclude blacklisted attributes
        # Reasons for blacklisting: Simple one-time values, Helper classes, and complex data
        black_list = [
            "name",
            "length",
            "width",
            "thickness",
            "mass",
            "plot_manager",
            "property_calculator",
            "data_preprocessor",
            "serializer",
        ]
        self.serializer.register_all_public_attributes(blacklist=black_list)
        self.serializer.register_list(self._exportable_fields)

    def _initialize_hysteresis(self):
        """Initialize and register hysteresis-related data."""
        self.specialized_data["hysteresis_stress"] = pd.Series(dtype="float64", name="hysteresis_stress")
        self.specialized_data["hysteresis_strain"] = pd.Series(dtype="float64", name="hysteresis_strain")
        self.specialized_data["hysteresis_force"] = pd.Series(dtype="float64", name="hysteresis_force")
        self.specialized_data["hysteresis_displacement"] = pd.Series(dtype="float64", name="hysteresis_displacement")

        for key, value in self.specialized_data.items():
            if "hysteresis" in key:
                self._raw_data[key] = value

        # Update the existing _raw_data field in _exportable_fields
        for field in self._exportable_fields:
            if field.attribute_name == "_raw_data":
                field.output_name.extend(
                    [
                        "Hysteresis Stress [MPa]",
                        "Hysteresis Strain",
                        "Hysteresis Force [N]",
                        "Hysteresis Displacement [mm]",
                    ]
                )
                break

    def _initialize_exportable_fields(self) -> list:
        """
        Initialize the list of exportable fields for serialization.

        This method manually registers fields and stores their values at the time of initialization.
        Once the fields are registered, their values are stored statically and will not update unless
        the fields are manually re-registered after their values change.

        Use this method for fields that are unlikely to change frequently or for more complex fields
        (such as data sets or raw data) that may require custom handling.

        Returns:
        --------
        list:
            A list of AttributeField objects, each representing an attribute or data field to be
            serialized. This list is initialized once and should be reinitialized if any attribute
            values need to be updated.

        Note:
        -----
        - For attributes, `output_name` defines a display name for serialization.
        - For data (e.g., `pandas.Series` or `pandas.DataFrame`), `output_name` defines the column
        names or series name. The data will be saved as "{property_name}_data.csv", with
        `output_name` specifying how the data is labeled within the file.
        """
        return [
            AttributeField(
                attribute_name="name", value=self.name, unit=None, output_name="Sample Name", category="attributes"
            ),
            AttributeField(
                attribute_name="length",
                value=self.length,
                unit=self._internal_units.get("length"),
                output_name="Length",
                category="attributes",
            ),
            AttributeField(
                attribute_name="width",
                value=self.width,
                unit=self._internal_units.get("length"),
                output_name="Width",
                category="attributes",
            ),
            AttributeField(
                attribute_name="thickness",
                value=self.thickness,
                unit=self._internal_units.get("length"),
                output_name="Thickness",
                category="attributes",
            ),
            AttributeField(
                attribute_name="_raw_data",
                value=self._raw_data,
                unit=None,
                output_name=["Force [N]", "Displacement [mm]", "Stress [MPa]", "Strain"],
                category="data",
            ),
        ]

    def __repr__(self) -> str:
        """Return a debug-centric string representation of the entity."""
        return f"{self.__class__.__name__}({self.name})V{self.entity_version}_{self.data_state.value}"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the entity."""
        return f"{self.__class__.__name__}({self.name})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, AnalyzableEntity):
            return False

        return bool(
            self.name == other.name
            and self.analysis_standard == other.analysis_standard
            and self.entity_version == other.entity_version
        )

    def __hash__(self) -> int:
        unqiue_id = (self.name, self.analysis_standard, self.entity_version)
        return hash(unqiue_id)

    # Setters & Resetters

    def set_target_unit(self, property_name: str, target_unit) -> None:
        """
        Set the target unit for a specific property (e.g., force, displacement, stress).
        """
        # Normalize target_unit to pint.Unit
        if isinstance(target_unit, str):
            target_unit = self.data_preprocessor.unit_registry.parse_units(target_unit)
        elif isinstance(target_unit, pint.Quantity):
            target_unit = target_unit.units
        elif not isinstance(target_unit, pint.Unit):
            raise TypeError("target_unit must be a str, pint.Unit, or pint.Quantity.")

        self._target_units[property_name] = target_unit

    def reset_target_unit(self, property_name: str) -> Any:
        """
        Resets the target unit for a property to the default internal unit.
        """
        return self._target_units.pop(property_name, None)

    def set_uncertainty(
        self, key: str, value: Union[pd.Series, float, str], uncertainty_type: str = "absolute"
    ) -> bool:
        """Helper method to set the uncertainty for a given property."""
        self._uncertainty[key] = {"value": value, "type": uncertainty_type}
        return bool(key in self._uncertainty)

    def set_kpi(self, key: str, value: Value) -> bool:
        """Helper method to set a custom KPI for the entity."""
        # As the Kpis get more complex, will need this function to enforce a uniform interface
        self._kpis[key] = value
        return bool(key in self._kpis)

    def set_test_metadata(self, key: str, value: Value) -> bool:
        """Helper method to set test metadata for the entity."""
        self.test_metadata[key] = value
        return bool(key in self.test_metadata)

    def register_property(
        self, property_name: str, value: Value, unit: Union[str, pint.Unit, None], output_name: Optional[str] = None
    ) -> None:
        category = "data" if isinstance(value, (pd.Series, pd.DataFrame)) else "attributes"
        data_field = AttributeField(
            attribute_name=property_name,
            value=value,
            unit=unit,
            output_name=output_name or property_name.capitalize(),
            category=category,
        )
        self.serializer.register_field(data_field)

    def recalculate_properties(self, property_name: str) -> None:
        """
        Recalculate a specific property and update the internal value.
        """
        # set the _property to None to force recalculation
        if hasattr(self, f"_{property_name}"):
            setattr(self, f"_{property_name}", None)
            # Trigger the recalculation by accessing the property, ensuring fresh computation
            getattr(self, property_name)
        else:
            raise ValueError(f"Property {property_name} does not exist.")

    # Helper Method

    def _convert_units(
        self,
        value: Optional[Union[float, pd.Series]],
        current_unit_key: str,
        target_unit_key: Optional[str] = None,
        target_unit: Optional[pint.Unit] = None,
    ) -> Union[float, pd.Series, None]:
        """
        Converts the units of a property value if a target unit is specified.
        """
        if value is not None:
            current_unit = self._internal_units.get(current_unit_key)
            # target_unit protity 1. Explicit units 2. Target unit key 3. Current unit key
            target_unit = target_unit or self._target_units.get(target_unit_key or current_unit_key, current_unit)
            if target_unit and current_unit != target_unit:
                try:
                    conversion_factor = self.data_preprocessor._get_conversion_factor(current_unit, target_unit)
                except pint.errors.DimensionalityError as e:
                    raise ValueError(f"Cannot convert entity '{self.name}' to target unit '{target_unit}': {str(e)}")
                except pint.errors.UndefinedUnitError as e:
                    raise ValueError(f"Cannot convert units for property '{current_unit_key}': {str(e)}")
                return value * conversion_factor
            else:
                return value
        else:
            return None

    # Getters

    def get_proprety_with_units(self, property_name: str) -> Optional[pint.Quantity]:
        """
        Get the value and internal units for a property.
        """
        if hasattr(self, f"_{property_name}") or hasattr(self, property_name):
            units = self._internal_units.get(property_name)
            _property = getattr(property_name)
            if isinstance(_property, (float, int)):
                return getattr(property_name) * units
            else:
                raise ValueError(
                    f"Cannot get the units for {property_name} as of the types {type(_property)} instead of being a number"
                )

    def get_property_with_uncertainty(self, property_name: str) -> tuple[Optional[Value], Optional[Value]]:
        """
        Get the value and uncertainty for a property.
        """
        value = getattr(self, f"_{property_name}", None)
        if value is None:
            raise ValueError(f"Property '{property_name}' has no value.")

        uncertainty = self._uncertainty.get(property_name, None)
        return value, uncertainty

    def get_property_with_units_and_uncertainty(self, property_name: str) -> entity_property:
        """
        Get the value, uncertainty, and units for a property.
        """
        value, uncertainty = self.get_property_with_uncertainty(property_name)
        units = self._internal_units.get(property_name)
        return entity_property(value=value, uncertainty=uncertainty, unit=units)

    # Helper  Getters Methods for plotting
    def _get_output_units(self, property_name: str) -> pint.Unit:
        """Get output units for a property."""
        # 1. try target units 2. internal units 3. raise error
        return (
            self._target_units.get(property_name, self._internal_units.get(property_name))
            or self._internal_units[property_name]
        )

    # Properties

    @exportable_property(output_name="Cross-Sectional Area", unit="mm^2")
    def area(self) -> Optional[float]:
        # Inital First time calculation
        if self._area is None:
            # Convert width to the same unit as length using a local variable
            length_unit = self._internal_units.get("length")
            width_converted = self._convert_units(value=self.width, current_unit_key="width", target_unit=length_unit)

            # Calculate area
            try:
                self._area, area_uncertainty = self.property_calculator.calculate_cross_sectional_area(
                    self.length, width_converted
                )
                if area_uncertainty and area_uncertainty > 0:
                    # only store the uncertainty if it should be treated as non exact to save on memory and futher computations
                    self._uncertainty.setdefault("area", area_uncertainty)
            except ValueError as e:
                raise ValueError(f"Cannnot calculate area for entity '{self.name}': {str(e)}")

            # Set internal unit for area if not already set
            self._internal_units.setdefault("area", self._internal_units["length"] ** 2)

        # Convert area to target unit if needed
        _area = self._convert_units(self._area, current_unit_key="area")
        return _area if isinstance(_area, (float, int)) else None

    @property
    def volume(self) -> Optional[float]:
        if self.area is not None and self.thickness is not None:
            length_unit = self._internal_units.get("length")
            thickness_converted = self._convert_units(
                self.thickness, current_unit_key="thickness", target_unit=length_unit
            )

            # Calculate volume
            self._volume, volumne_uncertainty = self.property_calculator.calculate_volume(
                area=self.area, thickness=thickness_converted
            )

            # Set internal unit for volume if not already set
            self._internal_units.setdefault("volume", self._internal_units["area"] * self._internal_units["length"])

            if volumne_uncertainty and volumne_uncertainty > 0:
                # only store the uncertainty if it should be treated as non exact to save on memory and futher computations
                self._uncertainty.setdefault("volume", volumne_uncertainty)

        elif self.length is not None and self.width is not None and self.thickness is not None:
            # Convert width and thickness to the same unit as length
            length_unit = self._internal_units.get("length")
            width_converted = self._convert_units(self.width, current_unit_key="width", target_unit=length_unit)
            thickness_converted = self._convert_units(
                self.thickness, current_unit_key="thickness", target_unit_key="length"
            )
            # Calculate volume directly
            self._volume, volumne_uncertainty = self.property_calculator.calculate_volume_direct(
                length=self.length, width=width_converted, thickness=thickness_converted
            )
            # Set internal unit for volume if not already set
            self._internal_units.setdefault("volume", self._internal_units["length"] ** 3)

            if volumne_uncertainty and volumne_uncertainty > 0:
                # only store the uncertainty if it should be treated as non exact to save on memory and futher computations
                self._uncertainty.setdefault("volume", volumne_uncertainty)
        else:
            raise ValueError("Insufficient data to calculate volume.")

        # Convert volume to target unit if needed
        _volume = self._convert_units(self._volume, current_unit_key="volume")
        return _volume if isinstance(_volume, (float, int)) else None

    @property
    def density(self) -> Optional[float]:
        if self._density is None and self.mass is not None:
            # Calculate density
            try:
                self._density, density_uncertainty = self.property_calculator.calculate_density(
                    mass=self.mass, volume=self.volume
                )
                if density_uncertainty and density_uncertainty > 0:
                    # only store the uncertainty if it should be treated as non exact to save on memory and futher computations
                    self._uncertainty.setdefault("density", density_uncertainty)
            except ValueError as e:
                raise ValueError(f"Cannot calculate density for entity '{self.name}': {str(e)}")

            # Set internal unit for density if not already set
            self._internal_units.setdefault("density", self._internal_units["mass"] / self._internal_units["volume"])

        # Convert density to target unit if needed
        _density = self._convert_units(self._density, current_unit_key="density")
        return _density if isinstance(_density, (float, int)) else None

    @property
    def force(self) -> Optional[pd.Series]:
        _force = self._convert_units(self._force, current_unit_key="force")
        return _force if isinstance(_force, pd.Series) and not _force.empty else None

    @property
    def displacement(self) -> Optional[pd.Series]:
        _displacement = self._convert_units(self._displacement, current_unit_key="displacement")
        return _displacement if isinstance(_displacement, pd.Series) and not _displacement.empty else None

    @property
    def strain(self) -> Optional[pd.Series]:
        """
        Calculate and return the strain, converting units if necessary.
        Strain = Displacement / Length, where Length is the initial length of the sample.
        :return: Strain data as a Pandas Series, optionally converted to the target unit.
        """
        if self._strain is None or (isinstance(self._strain, pd.Series) and self._strain.empty):
            # Calculate strain using the property calculator
            try:
                self._strain, strain_uncertainty = self.property_calculator.calculate_strain(
                    displacement_series=self.displacement, initial_length=self.length
                )

                # Store the uncertainty if meaningfully (1) pd.Series with a value > 0 (absolute value) or (2) str ending with % (relative value)
                if (isinstance(strain_uncertainty, pd.Series) and any(strain_uncertainty > 0)) or (
                    isinstance(strain_uncertainty, str) and strain_uncertainty.endswith("%")
                ):
                    # only store the uncertainty if it should be treated as non exact to save on memory and futher computations
                    self._uncertainty.setdefault("strain", strain_uncertainty)
            except ValueError as e:
                raise ValueError(f"Cannot calculate strain for entity '{self.name}': {str(e)}")

            # Set internal unit for strain if not already set
            self._internal_units.setdefault("strain", pint.Unit("dimensionless"))

        _strain = self._convert_units(self._strain, current_unit_key="strain")
        return _strain if isinstance(_strain, pd.Series) and not _strain.empty else None

    @property
    def stress(self) -> Optional[pd.Series]:
        """
        Calculate and return the stress, converting units if necessary.
        Stress = Force / Area, where Area is calculated as
        :return: Stress data as a Pandas Series, optionally converted to the target unit.
        """
        if self._stress is None or (isinstance(self._stress, pd.Series) and self._stress.empty):
            # Calculate stress using the property calculator
            try:
                self._stress, stress_uncertainty = self.property_calculator.calculate_stress(
                    force_series=self.force, area=self.area
                )

                # Store the uncertainty meaningfully (1) pd.Series with a value > 0 (absolute value) or (2) str ending with % (relative value)
                if (isinstance(stress_uncertainty, pd.Series) and any(stress_uncertainty > 0)) or (
                    isinstance(stress_uncertainty, str) and stress_uncertainty.endswith("%")
                ):
                    # only store the uncertainty if it should be treated as non exact to save on memory and futher computations
                    self._uncertainty.setdefault("stress", stress_uncertainty)
            except ValueError as e:
                raise ValueError(f"Cannot calculate stress for entity '{self.name}': {str(e)}")

            # Set internal unit for stress if not already set
            self._internal_units.setdefault("stress", self._internal_units["force"] / self._internal_units["area"])

        _stress = self._convert_units(self._stress, current_unit_key="stress")
        return _stress if isinstance(_stress, pd.Series) and not _stress.empty else None

    # Plotting Methods

    def plot_stress_strain(self, 
                           plot: Optional["Plot"] = None,
                           plot_name: Optional[str] = None,
                           plot_config: Optional["PlotConfig"] = None,
                           update_fig: bool = False) -> Optional["Plot"]:
        """
        Plot the stress-strain curve for a sample.
        Can be used to provide an automated view of the data, potentially overlayed with other samples.
        """
        if self.stress is None or self.strain is None:
            raise ValueError("Stress or strain data is missing for plotting the stress-strain curve.")

        if plot_name is None:
            plot_name = f"{self.name} Stress-Strain Curve"
            
        if plot_config is None:
            plot_config = PlotConfig(
                title=plot_name,
                xlabel="Strain [%]",
                ylabel=f"Stress [{self._get_output_units('stress')}]",
                x_percent=True,
            )
            
        plot = self.plot_manager.add_entity_to_plot(
            entity=self,
            plot_name=plot_name,
            plot_config=plot_config,
            x_data_key="strain",
            y_data_key="stress",
            plot=plot,
            element_label=f"{self.name}_Stress-Strain",
            plot_type="line",
            update_plot_config=update_fig,
        )
        return plot

        
    def plot_force_displacement( self,
        plot : Optional["Plot"] = None,
        plot_name: Optional[str] = None,
        plot_config: Optional["PlotConfig"] = None,
        update_fig: bool = False,
        ) -> Optional["Plot"]:
        """
        Plot the force-displacement curve for a sample.
        Can be used to provide an automated view of the data, potentially overlayed with other samples.
        """
        if self.force is None or self.displacement is None:
            raise ValueError("Force or displacement data is missing for plotting the force-displacement curve.")
        
        if plot_name is None:
            plot_name = f"{self.name} Force-Displacement Curve"
            
        if plot_config is None:
            plot_config = PlotConfig(
                title=plot_name,
                xlabel=f"Displacement [{self._get_output_units('displacement')}]",
                ylabel=f"Force [{self._get_output_units('force')}]",
            )  
            
            
        plot = self.plot_manager.add_entity_to_plot(
            entity=self,
            plot_name=plot_name,
            plot_config=plot_config,
            x_data_key="displacement",
            y_data_key="force",
            plot=plot,
            element_label=f"{self.name}_Force-Displacement",
            plot_type="line",
            update_plot_config=update_fig,
        )
        return plot
        

    # Interface - Abstract Methods

    @abstractmethod
    def plot(self) -> None:
        """
        Plot key performance indicators (KPI) relevant to the standard being used.
        This method must be implemented by subclasses to provide standard-specific views.
        """
        pass



