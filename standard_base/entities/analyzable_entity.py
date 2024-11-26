import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeAlias, Union

import numpy as np
import pandas as pd
import pint

from utlils.contract_validators import ContractValidators
from visualization_backend.plot_config import PlotConfig
from visualization_backend.plot_manager import PlotManager

from ..data_extraction import MechanicalTestDataPreprocessor
from ..io_management.serializer import AttributeField, Serializer
from ..properties_calculators.base_standard_operator import BaseStandardOperator
from ..properties_calculators.group_aggeregation_calculator import GroupAggregationOperator
from .entity_group_manager import EntityGroupManager
from .properties import PropertyData, PropertyManager, exportable_property

if TYPE_CHECKING:
    from visualization_backend.plot import Plot

    from ..sample_factory import MechanicalTestStandards

Value: TypeAlias = Union[float, int, pd.Series, pd.DataFrame, np.ndarray]


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
        preprocessor: MechanicalTestDataPreprocessor = MechanicalTestDataPreprocessor(),
        property_calculator: BaseStandardOperator = BaseStandardOperator(),
        property_calculator_group: GroupAggregationOperator = GroupAggregationOperator(),
        plot_manager: PlotManager = PlotManager(),
        test_metadata: Optional[dict] = None,
        has_hysteresis: bool = False,
        uncertainty: Optional[dict] = None,
    ):
        """
        Initializes the AnalyzableEntity with various attributes for mechanical testing data.
        """
        self.name = name

        # General Entity determination
        self.analysis_standard: Optional[MechanicalTestStandards] = None  # Associated analysis standard
        self._mechanical_test_procudure = (
            None  # Compression or tensile (from analysis_standard or Compressive if end stress is maxium)
        )
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
        self.tags = []  # Tags associated with the entity

        # Test metadata
        self.test_metadata = test_metadata or {}  # e.g. test conditions, operator, machine, etc.

        # Shift applied to data for zeroing ( in internal units )
        self._shift_appiled_to_force = 0
        self._shift_appiled_to_displacement = 0
        self._shift_appiled_to_stress = 0
        self._shift_appiled_to_strain = 0
        self.apply_zero_shift = False

        # Helpper classes
        self.plot_manager = plot_manager
        self.serializer = Serializer(tracked_object=self)
        self.data_preprocessor = preprocessor

        # Sample Group Management
        self.is_sample_group: bool = False  # True if the entity represents a collection of samples
        self._samples: list[AnalyzableEntity] = []  # List of associated sample entities
        self.group_manager = EntityGroupManager()  # Helper class for managing sample groups

        # Sample Property Management
        self.property_manager = PropertyManager(preprocessor, uncertainty=uncertainty)
        self.property_calculator_individual = property_calculator
        self.property_calculator_group = property_calculator_group

        # TODO: Add a method to update raw data names with units and for exporting
        # dataframe columns will always be lowercase to ensure consistency

        self._raw_data = pd.DataFrame(
            {
                "time": time,
                "force": force,
                "displacement": displacement,
                "stress": stress,
                "strain": strain,
            }
        ).reset_index(drop=True)

        internal_units = self.property_manager._internal_units
        self.property_manager.set_property("length", length)
        self.property_manager.set_property("width", width)
        self.property_manager.set_property("thickness", thickness)
        self.property_manager.set_property("mass", mass)

        self.property_manager.set_property("time", time, internal_unit=pint.Unit("s"))
        self.property_manager.set_property("force", force)
        self.property_manager.set_property("displacement", displacement)

        self.property_manager.set_property("area", area, internal_unit=internal_units.get("length") ** 2)
        self.property_manager.set_property("volume", volume, internal_unit=internal_units.get("length") ** 3)
        self.property_manager.set_property(
            "density", density, internal_unit=internal_units.get("mass") / internal_units.get("length") ** 3
        )
        self.property_manager.set_property(
            "stress", stress, internal_unit=internal_units.get("force") / internal_units.get("length") ** 2
        )
        self.property_manager.set_property("strain", strain, internal_unit=pint.Unit("dimensionless"))

        self._calculator_map = {
            "area": self._calculate_area if not self.is_sample_group else self._calculate_area_group,
            "volume": self._calculate_volumne if not self.is_sample_group else self._calculate_volumne_group,
            "density": self._calculate_density if not self.is_sample_group else self._calculate_density_group,
            "stress": self._calculate_stress if not self.is_sample_group else self._calculate_stress_strain_group,
            "strain": self._calculate_strain if not self.is_sample_group else self._calculate_stress_strain_group,
        }
        """
        Defualt map to set method to calculate properties
        """
        self.property_manager.set_calculators(self._calculator_map)

        # Hysteresis data | Specialized data
        self.specialized_data = specialized_data or {}
        """
        Specialized Data:
        Flexible storage for additional data that may be specific to the sample standard or test.
        """

        # # Key Performance Indicators (KPIs)
        # self._kpis: dict[str, Value] = {}
        # """
        # Key Performance Indicators (KPIs):
        # - Stores custom calculations depending on the applied mechanical test standard.
        # - Example: `self._kpis['strength'] = 250` (strength could be a calculated property such as maximum stress).
        # """

        # Exportable Fields
        self._exportable_fields: list[AttributeField] = self._initialize_exportable_fields()

        if self.has_hysteresis:
            self._initialize_hysteresis()

        # Register all public attributes for serializatiom ( all attributes not starting with _ ) Exclude blacklisted attributes
        # Reasons for blacklisting: Simple one-time values, Helper classes, and complex data
        self._public_registry_black_list = [
            "name",
            "plot_manager",
            "property_calculator",
            "data_preprocessor",
            "serializer",
        ]
        self.serializer.register_all_public_attributes(blacklist=self._public_registry_black_list)
        self.serializer.register_list(self._exportable_fields)

    # Dunder for (hashing, string representation, equality) -------------------------

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

    # Setters for late assignment of properties -----------------------------------

    def set_kpi(self, key: str, value: Value) -> bool:
        """Helper method to set a custom KPI for the entity."""
        # As the Kpis get more complex, will need this function to enforce a uniform interface
        self._kpis[key] = value
        return bool(key in self._kpis)

    # Test Metadata --------------------------------------------------------------

    def set_test_metadata(self, key: str, value: Value) -> bool:
        """Helper method to set test metadata for the entity."""
        self.test_metadata[key] = value
        return bool(key in self.test_metadata)

    # Binding for calculating properties ------------------------------------------

    def attach_property_calcullators(self, calculator_map: Optional[dict[str, Callable]] = None) -> None:
        calculator_map = calculator_map or self._calculator_map
        self.property_manager.set_calculators(calculator_map)

    # Exportable Fields -----------------------------------------------------------

    def register_property_for_export(
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
                unit=self.internal_units.get("length"),
                output_name="Length",
                category="attributes",
            ),
            AttributeField(
                attribute_name="width",
                value=self.width,
                unit=self.internal_units.get("length"),
                output_name="Width",
                category="attributes",
            ),
            AttributeField(
                attribute_name="thickness",
                value=self.thickness,
                unit=self.internal_units.get("length"),
                output_name="Thickness",
                category="attributes",
            ),
            AttributeField(
                attribute_name="_raw_data",
                value=self._raw_data,
                unit=None,
                output_name=["Time [s]", "Force [N]", "Displacement [mm]", "Stress [MPa]", "Strain"],
                category="data",
            ),
        ]

    def update_seralized_attributes(self, additional_attributes: Optional[list[str]] = None) -> None:
        black_list = self._public_registry_black_list

        if additional_attributes:
            black_list += additional_attributes

        self.serializer.register_all_public_attributes(black_list)

    # Sample Properties -----------------------------------------------------------

    # Scalars
    @property
    def width(self) -> Optional[float]:
        return self.property_manager._properties["width"].value

    @width.setter
    def width(self, value) -> None:
        self.property_manager._properties["width"].value = value

    @property
    def length(self) -> Optional[float]:
        return self.property_manager._properties["length"].value

    @length.setter
    def length(self, value) -> None:
        self.property_manager._properties["length"].value = value

    @property
    def thickness(self) -> Optional[float]:
        return self.property_manager._properties["thickness"].value

    @thickness.setter
    def thickness(self, value) -> None:
        self.property_manager._properties["thickness"].value = value

    @property
    def mass(self) -> Optional[float]:
        return self.property_manager._properties["mass"].value

    @mass.setter
    def mass(self, value) -> None:
        self.property_manager._properties["mass"].value = value

    # Vectors

    @property
    def time(self) -> Optional[pd.Series]:
        try:
            _time = self.property_manager.get_property("time").value
            return _time if isinstance(_time, pd.Series) and not _time.empty else None
        except (ValueError, KeyError):
            raise ValueError(f"Cannot access 'time' data for entity '{self.name}', was not assigned.")

    @property
    def force(self) -> Optional[pd.Series]:
        try:
            _force = self.property_manager.get_property("force").value
            return _force if isinstance(_force, pd.Series) and not _force.empty else None
        except (ValueError, KeyError):
            raise ValueError(f"Cannot access 'force' data for entity '{self.name}', was not assigned.")

    @exportable_property(unit="N", output_name="Force_Shift")
    def shift_appiled_to_force(self) -> float:
        return self._shift_appiled_to_force

    @shift_appiled_to_force.setter
    def shift_appiled_to_force(self, value: float) -> None:
        self._shift_appiled_to_force = value

    @property
    def force_shifted(self) -> Optional[pd.Series]:
        return self.force + self._shift_appiled_to_force

    @property
    def displacement(self) -> Optional[pd.Series]:
        try:
            _displacement = self.property_manager.get_property("displacement").value
            return _displacement if isinstance(_displacement, pd.Series) and not _displacement.empty else None
        except (ValueError, KeyError):
            raise ValueError(f"Cannot access 'displacement' data for entity '{self.name}', was not assigned.")

    @exportable_property(unit="mm", output_name="Displacement_Shift")
    def shift_appiled_to_displacement(self) -> float:
        return self._shift_appiled_to_displacement

    @shift_appiled_to_displacement.setter
    def shift_appiled_to_displacement(self, value: float) -> None:
        self._shift_appiled_to_displacement = value

    @property
    def displacement_shifted(self) -> Optional[pd.Series]:
        return self.displacement + self._shift_appiled_to_displacement

    # Calculated Properties --------------------------------------------------------

    @exportable_property(output_name="Cross-Sectional Area", unit="mm^2")
    def area(self) -> Optional[float]:
        """Calculates and returns the cross-sectional area in the target unit."""
        try:
            _area = self.property_manager.get_property("area").value
            return _area if isinstance(_area, (int, float)) else None
        except (ValueError, KeyError) as e:
            raise ValueError(f"Cannot calculate area for entity '{self.name}': {str(e)}")

    def _calculate_area(self):
        """Calculate the cross-sectional area of the sample."""
        if self.is_sample_group:
            raise ValueError("Should not calculate area for a sample group, Register '_calculate_area_group' instead.")

        converted_properties = self.property_manager.ensure_properties_same_units(
            ["length", "width"], self.internal_units["length"]
        )

        area_value, area_uncertainty = self.property_calculator_individual.calculate_cross_sectional_area(
            converted_properties["length"].value,
            converted_properties["width"].value,
            length_uncertainty=converted_properties["length"].uncertainty,
            width_uncertainty=converted_properties["width"].uncertainty,
        )

        self.property_manager.set_property(
            "area", area_value, uncertainty=area_uncertainty, internal_unit=self.internal_units["length"] ** 2
        )

        return area_value

    def _calculate_area_group(self):
        """Calculate the cross-sectional area for a sample group."""
        if not self.is_sample_group:
            raise ValueError("Should not calculate area for a single sample, Register '_calculate_area' instead.")

        # TODO: Add a mechanism for seting aggregated startegy (mean, median, etc.)
        _area = self.group_manager.aggregate_scalar_property(self._samples, "area", self.internal_units, method="mean")
        return _area

    @exportable_property(output_name="Volume", unit="mm^3")
    def volume(self) -> Optional[float]:
        """Calculates and returns the volume in the target unit."""
        try:
            _volume = self.property_manager.get_property("volume").value
            return _volume if isinstance(_volume, (float, int)) else None
        except (ValueError, KeyError) as e:
            raise ValueError(f"Cannot calculate volume for entity '{self.name}': {str(e)}")

    def _calculate_volumne(self):
        if self.is_sample_group:
            raise ValueError(
                "Should not calculate stress for a sample group, Register '_calculate_volumne_group' instead."
            )

        converted_properties = self.property_manager.ensure_properties_same_units(
            ["length", "width", "thickness"], self.internal_units["length"]
        )

        volumne_value, volumne_uncertainty = self.property_calculator_individual.calculate_volume_direct(
            converted_properties["length"].value,
            converted_properties["width"].value,
            converted_properties["thickness"].value,
            length_uncertainty=converted_properties["length"].uncertainty,
            width_uncertainty=converted_properties["width"].uncertainty,
            thickness_uncertainty=converted_properties["thickness"].uncertainty,
        )

        self.property_manager.set_property(
            "volume", volumne_value, uncertainty=volumne_uncertainty, internal_unit=self.internal_units["length"] ** 3
        )

        return volumne_value

    def _calculate_volumne_group(self):
        """Calculate the volume for a sample group."""
        if not self.is_sample_group:
            raise ValueError("Should not calculate volume for a single sample, Register '_calculate_volume' instead.")

        _volume = self.group_manager.aggregate_scalar_property(
            self._samples, "volume", self.internal_units, method="mean"
        )
        return _volume

    @exportable_property(output_name="Density", unit="g/cm^3")
    def density(self) -> Optional[float]:
        """Calculates and returns the density in the target unit."""
        try:
            _density = self.property_manager.get_property("density").value
            return _density if isinstance(_density, (float, int)) else None
        except (ValueError, KeyError) as e:
            raise ValueError(f"Cannot calculate density for entity '{self.name}': {str(e)}")

    def _calculate_density(self):
        """Calculate the density of the sample."""
        if self.is_sample_group:
            raise ValueError(
                "Should not calculate density for a sample group, Register '_calculate_density_group' instead."
            )
        mass = self.property_manager.get_property("mass")
        volume = self.property_manager.get_property("volume")

        density_value, density_uncertainty = self.property_calculator_individual.calculate_density(
            mass.value,
            volume.value,
            mass_uncertainty=mass.uncertainty,
            volume_uncertainty=volume.uncertainty,
        )

        self.property_manager.set_property(
            "density",
            density_value,
            uncertainty=density_uncertainty,
            internal_unit=self.internal_units["mass"] / self.internal_units["length"] ** 3,
        )

        return density_value

    def _calculate_density_group(self):
        """Calculate the density for a sample group."""
        if not self.is_sample_group:
            raise ValueError("Should not calculate density for a single sample, Register '_calculate_density' instead.")

        _density = self.group_manager.aggregate_scalar_property(
            self._samples, "density", self.internal_units, method="mean"
        )
        return _density

    # Stress and Strain Calculation ------------------------------------------------

    @property
    def stress(self) -> Optional[pd.Series]:
        """
        Calculate and return the stress, converting units if necessary.
        Stress = Force / Area, where Area is calculated as
        :return: Stress data as a Pandas Series, optionally converted to the target unit.
        """
        _stress = self.property_manager.get_property("stress").value
        return _stress if isinstance(_stress, pd.Series) and not _stress.empty else None

    @exportable_property(unit="MPa", output_name="Stress_Shift")
    def shift_appiled_to_stress(self) -> float:
        return self._shift_appiled_to_stress

    @shift_appiled_to_stress.setter
    def shift_appiled_to_stress(self, value: float) -> None:
        self._shift_appiled_to_stress = value

    @property
    def stress_shifted(self) -> Optional[pd.Series]:
        return self.stress + self._shift_appiled_to_stress

    def _calculate_stress(self):
        """Calculate stress = force / area. For individual samples."""
        if self.is_sample_group:
            raise ValueError(
                "Should not calculate stress for a sample group, Register '_calculate_stress_strain_group' instead."
            )

        force = self.property_manager.get_property("force")
        area = self.property_manager.get_property("area")

        stress_value, stress_uncertainty = self.property_calculator_individual.calculate_stress(
            force_series=force.value,
            area=area.value,
            force_uncertainty=force.uncertainty,
            area_uncertainty=area.uncertainty,
        )

        self.property_manager.set_property(
            "stress", stress_value, uncertainty=stress_uncertainty, internal_unit=force.unit / area.unit
        )

        return stress_value

    @property
    def strain(self) -> Optional[pd.Series]:
        """
        Calculate and return the strain, converting units if necessary.
        Strain = Displacement / Length, where Length is the initial length of the sample.
        :return: Strain data as a Pandas Series, optionally converted to the target unit.
        """
        try:
            _strain = self.property_manager.get_property("strain").value
            return _strain if isinstance(_strain, pd.Series) and not _strain.empty else None
        except (ValueError, KeyError):
            raise ValueError(
                f"Cannot calculate 'strain' data for entity '{self.name}', was not assigned, or depends other invalid properties."
            )

    @exportable_property(unit="mm", output_name="Strain_Shift")
    def shift_appiled_to_strain(self) -> float:
        return self._shift_appiled_to_strain

    @shift_appiled_to_strain.setter
    def shift_appiled_to_strain(self, value: float) -> None:
        self._shift_appiled_to_strain = value

    @property
    def strain_shifted(self) -> Optional[pd.Series]:
        return self.strain + self._shift_appiled_to_strain

    # Calculate strain for individual samples

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
            "strain", value=strain_value, uncertainty=strain_uncertainty, internal_unit=pint.Unit("dimensionless")
        )

        return strain_value

    # Calculate stress and strain for sample groups

    def _calculate_stress_strain_group(self):
        """Calculate stress = force / area. For sample groups."""
        if not self.is_sample_group:
            raise ValueError("Should not be called for individual samples.")

        interpolated_df = self.group_manager.aggregate_series_property(
            samples=self._samples,
            y_column="stress",
            x_column="strain",
            internal_units=self.internal_units,
            method="mean",
        )

        if interpolated_df is not None and (isinstance(interpolated_df, pd.DataFrame) and not interpolated_df.empty):
            stress_value = interpolated_df["avg_stress"].rename("stress")
            strain_value = interpolated_df["strain"]

            stress_unit = self._samples[0].property_manager.get_internal_units("stress")
            strain_unit = self._samples[0].property_manager.get_internal_units("strain")

            self.property_manager.set_property("stress", value=stress_value, internal_unit=stress_unit)
            self.property_manager.set_property("strain", value=strain_value, internal_unit=strain_unit)

        return interpolated_df

    # Hysteresis Data ----------------------------------------------------------

    def _initialize_hysteresis(self):
        """Initialize and register hysteresis-related data."""
        self.specialized_data["hysteresis_time"] = pd.Series(dtype="float64", name="hysteresis_time")
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
                        "Hysteresis Time [s]",
                        "Hysteresis Stress [MPa]",
                        "Hysteresis Strain",
                        "Hysteresis Force [N]",
                        "Hysteresis Displacement [mm]",
                    ]
                )
                break

    # Untility Properties -----------------------------------------------------------

    @property
    def internal_units(self) -> dict[str, pint.Unit]:
        units = self.property_manager.get_internal_units()
        assert isinstance(units, dict), "Internal units must be a dictionary."
        return units

    # DataFrame Properties ------------------------------------------------

    @property
    def raw_data(self) -> pd.DataFrame:
        return self._raw_data

    @exportable_property(
        output_name=["Force [N]", "Displacement [mm]", "Stress [MPa]", "Strain"],
        unit=None,
        category="data",
    )
    def processed_data(self) -> pd.DataFrame:
        time = self.time
        force = self.force
        displacement = self.displacement
        stress = self.stress
        strain = self.strain

        if self.apply_zero_shift:
            force += self.shift_appiled_to_force
            displacement += self.shift_appiled_to_displacement
            stress += self.shift_appiled_to_stress
            strain += self.shift_appiled_to_strain

        # interal standard names (lowercase, no spaces, no units)
        data_dict = {
            "time": time,
            "force": force,
            "displacement": displacement,
            "stress": stress,
            "strain": strain,
        }
        return pd.DataFrame(data_dict)

    @exportable_property(
        output_name=[
            "Hysteresis Time [s]",
            "Hysteresis Force [N]",
            "Hysteresis Displacement [mm]",
            "Hysteresis Stress [MPa]",
            "Hysteresis Strain",
        ],
        unit=None,
        category="data",
    )
    def processed_data_hysteresis(self) -> pd.DataFrame:
        data_dict = {
            "hysteresis_time": self.specialized_data.get("processed_hysteresis_time", None),
            "hysteresis_force": self.specialized_data.get("processed_hysteresis_force", None),
            "hysteresis_displacement": self.specialized_data.get("processed_hysteresis_displacement", None),
            "hysteresis_stress": self.specialized_data.get("processed_hysteresis_stress", None),
            "hysteresis_strain": self.specialized_data.get("processed_hysteresis_strain", None),
        }
        # If using all scalar values, you must pass an index
        if all(data is None for data in data_dict.values()):
            return pd.DataFrame(data_dict, index=[0])
        return pd.DataFrame(data_dict)

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
