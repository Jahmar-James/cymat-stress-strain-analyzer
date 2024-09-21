from abc import ABC, abstractmethod
from typing import Optional, Union, TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pint


from data_extraction import MechanicalTestDataPreprocessor
from visualization.plot_manager import PlotManager
from visualization.plot_config import PlotConfig

from ..base.base_standard_operator import BaseStandardOperator

if TYPE_CHECKING:
    from ..sample_factory import MechanicalTestStandards
    from visualization.plot import Plot 

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
        
    Abstract Methods:
    - Define methods that subclasses must implement, such as plotting or data extraction.
    """

    def __init__(self,
                 name: str,
                 length: Optional[float] = None,
                 width: Optional[float] = None,
                 thickness: Optional[float] = None,
                 mass: Optional[float] = None,
                 area: Optional[float] = None,
                 volume: Optional[float] = None,
                 density: Optional[float] = None,
                 force: Optional[pd.Series] = None,
                 displacement: Optional[pd.Series] = None,
                 stress: Optional[pd.Series] = None,
                 strain: Optional[pd.Series] = None,
                 property_calculator: Optional[BaseStandardOperator] = None,
                 plot_manager: Optional[PlotManager] = None
                 ):
        
        self.name = name
        self.length = length 
        self.width = width
        self.thickness = thickness
        self.mass = mass
        
        self._area = area
        self._volume = volume
        self._density = density
        self._force = force
        self._displacement = displacement
        self._stress = stress
        self._strain = strain
        
        self.is_sample_group: bool = False
        self.samples: list[AnalyzableEntity] = []
        self.analysis_standard: Optional["MechanicalTestStandards"] = None
        
        self.plot_manager = plot_manager or PlotManager()
        self.property_calculator = property_calculator or BaseStandardOperator()
        self.data_preprocessor = MechanicalTestDataPreprocessor()
        self.internal_units : dict[str, pint.Unit] = MechanicalTestDataPreprocessor.EXPECTED_UNITS.copy()
        self.target_units : dict[str, pint.Unit] = {}
        
    def set_target_unit(self, property_name: str, target_unit) -> None:
        """
        Set the target unit for a specific property (e.g., force, displacement, stress).
        :param property_name: Name of the property (e.g., "force", "displacement").
        :param target_unit: The target unit to convert the property into (e.g., kN, mm).
        """
        # Normalize target_unit to pint.Unit
        if isinstance(target_unit, str):
            target_unit = self.data_preprocessor.unit_registry.parse_units(target_unit)
        elif isinstance(target_unit, pint.Quantity):
            target_unit = target_unit.units
        elif not isinstance(target_unit, pint.Unit):
            raise TypeError("target_unit must be a str, pint.Unit, or pint.Quantity.")

        self.target_units[property_name] = target_unit
    
    def reset_target_unit(self, property_name: str) -> any:
        """
        Resets the target unit for a property to the default internal unit.
        :param property_name: Name of the property (e.g., "force", "displacement").
        """
        return self.target_units.pop(property_name, None)
            
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

    def _convert_units(
        self,
        value: Optional[Union[float, pd.Series]],
        current_unit_key: str,
        target_unit_key: Optional[str] = None,
        target_unit: Optional[pint.Unit] = None,
    ) -> Optional[Union[float, pd.Series]]:
        """
        Converts the units of a property value if a target unit is specified.
        """
        if value is not None:
            current_unit = self.internal_units.get(current_unit_key)
            # target_unit protity 1. Explicit units 2. Target unit key 3. Current unit key
            target_unit = target_unit or self.target_units.get(target_unit_key or current_unit_key, current_unit)
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

    def _get_proprety_with_units(self, property_name: str) -> pint.Quantity:
        if hasattr(self, f"_{property_name}") or hasattr(self, property_name):
            units = self.internal_units.get(property_name)
            _property = getattr(property_name)
            if isinstance(_property, (float, int)):
                return getattr(property_name) * units
            else:
                raise ValueError(
                    f"Cannot get the units for {property_name} as of the types {type(_property)} instead of being a number"
                )

    @property
    def area(self) -> Optional[float]:
        # Inital First time calculation
        if self._area is None:
            # Convert width to the same unit as length using a local variable
            length_unit = self.internal_units.get("length")
            width_converted = self._convert_units(value=self.width, current_unit_key="width", target_unit=length_unit)

            # Calculate area
            try:
                self._area = self.property_calculator.calculate_cross_sectional_area(self.length, width_converted)
            except ValueError as e:
                raise ValueError(f"Cannnot calculate area for entity '{self.name}': {str(e)}")

            # Set internal unit for area if not already set
            self.internal_units.setdefault("area", self.internal_units["length"] ** 2)

        # Convert area to target unit if needed
        return self._convert_units(self._area, current_unit_key="area")

    @property
    def volume(self) -> Optional[float]:
        if self.area is not None and self.thickness is not None:
            length_unit = self.internal_units.get("length")
            thickness_converted = self._convert_units(
                self.thickness, current_unit_key="thickness", target_unit=length_unit
            )

            # Calculate volume
            self._volume = self.property_calculator.calculate_volume(area=self.area, thickness=thickness_converted)

            # Set internal unit for volume if not already set
            self.internal_units.setdefault("volume", self.internal_units["area"] * self.internal_units["length"])

        elif self.length is not None and self.width is not None and self.thickness is not None:
            # Convert width and thickness to the same unit as length
            length_unit = self.internal_units.get("length")
            width_converted = self._convert_units(self.width, current_unit_key="width", target_unit=length_unit)
            thickness_converted = self._convert_units(
                self.thickness, current_unit_key="thickness", target_unit_key="length"
            )
            # Calculate volume directly
            self._volume = self.property_calculator.calculate_volume_direct(
                length=self.length, width=width_converted, thickness=thickness_converted
            )
            # Set internal unit for volume if not already set
            self.internal_units.setdefault("volume", self.internal_units["length"] ** 3)
        else:
            raise ValueError("Insufficient data to calculate volume.")

        # Convert volume to target unit if needed
        return self._convert_units(self._volume, current_unit_key="volume")

    @property
    def density(self) -> Optional[float]:
        if self._density is None and self.mass is not None:
            # Calculate density
            try:
                self._density = self.property_calculator.calculate_density(mass=self.mass, volume=self.volume)
            except ValueError as e:
                raise ValueError(f"Cannot calculate density for entity '{self.name}': {str(e)}")

            # Set internal unit for density if not already set
            self.internal_units.setdefault("density", self.internal_units["mass"] / self.internal_units["volume"])

        # Convert density to target unit if needed
        return self._convert_units(self._density, current_unit_key="density")

    @property
    def force(self) -> Optional[pd.Series]:
        return self._convert_units(self._force, current_unit_key="force")

    @property
    def displacement(self) -> Optional[pd.Series]:
        return self._convert_units(self._displacement, current_unit_key="displacement")

    @property
    def strain(self) -> Optional[pd.Series]:
        """
        Calculate and return the strain, converting units if necessary.
        Strain = Displacement / Length, where Length is the initial length of the sample.
        :return: Strain data as a Pandas Series, optionally converted to the target unit.
        """
        if self._strain is None:
            # Calculate strain using the property calculator
            try:
                self._strain = self.property_calculator.calculate_strain(
                    displacement_series=self.displacement, initial_length=self.length
                )
            except ValueError as e:
                raise ValueError(f"Cannot calculate strain for entity '{self.name}': {str(e)}")

            # Set internal unit for strain if not already set
            self.internal_units.setdefault("strain", pint.Unit("dimensionless"))

        return self._convert_units(self._strain, current_unit_key="strain")

    @property
    def stress(self) -> Optional[pd.Series]:
        """
        Calculate and return the stress, converting units if necessary.
        Stress = Force / Area, where Area is calculated as
        :return: Stress data as a Pandas Series, optionally converted to the target unit.
        """
        if self._stress is None:
            # Calculate stress using the property calculator
            try:
                self._stress = self.property_calculator.calculate_stress(force_series=self.force, area=self.area)
            except ValueError as e:
                raise ValueError(f"Cannot calculate stress for entity '{self.name}': {str(e)}")

            # Set internal unit for stress if not already set
            self.internal_units.setdefault("stress", self.internal_units["force"] / self.internal_units["area"])

        return self._convert_units(self._stress, current_unit_key="stress")
    

    # Common Operations        
    def _get_output_units(self, property_name: str) -> pint.Unit:
        """Get output units for a property."""
        # 1. try target units 2. internal units 3. raise error
        return self.target_units.get(property_name, self.internal_units.get(property_name)) or self.internal_units[property_name] 
        
    def plot_stress_strain(self, plot: Optional["Plot"] = None, plot_name: Optional[str] = None, plot_config: Optional["PlotConfig"] = None, update_fig: bool = False) -> "Plot":
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
                xlabel=f"Strain [%]",
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
        ) -> "Plot":
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

    # @abstractmethod
    def plot(self) -> None:
        """
        Plot key performance indicators (KPI) relevant to the standard being used.
        This method must be implemented by subclasses to provide standard-specific views.
        """
        pass



