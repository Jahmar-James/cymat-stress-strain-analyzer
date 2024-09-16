from abc import ABC, abstractmethod
from typing import Optional, Union
import pandas as pd
from ..base.base_standard_operator import BaseStandardOperator
from data_extraction import MechanicalTestDataPreprocessor
import pint

from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np



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
        else:
            raise ValueError(f"Property {property_name} does not exist.")

    def _convert_units(
        self, 
        value: Optional[Union[float, pd.Series]],
        current_unit_key: str,
        target_unit_key: Optional[str] = None
    ) -> Optional[Union[float, pd.Series]]:
        """
        Converts the units of a property value if a target unit is specified.
        """
        if value is not None:
            current_unit = self.internal_units.get(current_unit_key)
            target_unit = self.target_units.get(target_unit_key or current_unit_key, current_unit)
            if target_unit and current_unit != target_unit:
                conversion_factor = self.data_preprocessor._get_conversion_factor(current_unit, target_unit)
                return value * conversion_factor
            else:
                return value
        else:
            return None
    
    
    
    @property
    def area(self) -> Optional[float]:
        # Inital First time calculation
        if self._area is None and self.length and self.width:
                 # Convert width to the same unit as length using a local variable
                width_converted = self._convert_units(
                value=self.width, 
                current_unit_key="width", 
                target_unit_key="length")    

                # Calculate area
                self._area = self.property_calculator.calculate_cross_sectional_area(self.length, width_converted)
                
                # Set internal unit for area if not already set
                self.internal_units.setdefault("area", self.internal_units["length"] ** 2)       
                    
        # Convert area to target unit if needed
        return self._convert_units(self._area, current_unit_key="area")
    
    @property
    def volume(self) -> Optional[float]:
        if self.area is not None and self.thickness is not None:
            thickness_converted = self._convert_units(self.thickness, current_unit_key="thickness", target_unit_key="length")
        
            # Calculate volume
            self._volume = self.property_calculator.calculate_volume(
                area=self.area,
                thickness=thickness_converted
            )
            
            # Set internal unit for volume if not already set
            self.internal_units.setdefault("volume", self.internal_units["area"] * self.internal_units["length"])
        
        elif self.length is not None and self.width is not None and self.thickness is not None:
                # Convert width and thickness to the same unit as length
                width_converted = self._convert_units(
                    self.width, current_unit_key="width", target_unit_key="length"
                )
                thickness_converted = self._convert_units(
                    self.thickness, current_unit_key="thickness", target_unit_key="length"
                )
                # Calculate volume directly
                self._volume = self.property_calculator.calculate_volume_direct(
                    length=self.length,
                    width=width_converted,
                    thickness=thickness_converted
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
            if self.volume is not None:
                
                # Calculate density
                self._density = self.property_calculator.calculate_density(
                    mass=self.mass, 
                    volume=self.volume
                )
                # Set internal unit for density if not already set
                self.internal_units.setdefault("density", self.internal_units["mass"] / self.internal_units["volume"])
            else:
                raise ValueError("Volume data is missing for density calculation.")

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
            if self.displacement is not None and self.length:
                
                # Calculate strain using the property calculator
                self._strain = self.property_calculator.calculate_strain(
                    displacement_series=self.displacement,
                    initial_length=self.length
                )
                 # Set internal unit for strain if not already set
                self.internal_units.setdefault("strain", pint.Unit("dimensionless")) 
            else:
                raise ValueError("Displacement data or length is missing for strain calculation.")
        return self._convert_units(self._strain, current_unit_key="strain")
    
        
    @property
    def stress(self) -> Optional[pd.Series]:
        """
        Calculate and return the stress, converting units if necessary.
        Stress = Force / Area, where Area is calculated as 
        :return: Stress data as a Pandas Series, optionally converted to the target unit.
        """
        if self._stress is None:
            if self.force is not None and self.area:
                 # Calculate stress using the property calculator
                self._stress = self.property_calculator.calculate_stress(
                    force_series=self.force,
                    area=self.area
                )
                # Set internal unit for stress if not already set
                self.internal_units.setdefault("stress", self.internal_units["force"] / self.internal_units["area"])
            else:
                raise ValueError("Force data or area is missing for stress calculation.")
        return self._convert_units(self._stress, current_unit_key="stress")
    

    # Common Operations
    def _plot_data(
        self,
        x_data: Union[pd.Series, np.ndarray],
        y_data: Union[pd.Series, np.ndarray],
        plot_config: Optional["PlotConfig"],
        default_title: str,
        default_xlabel: str,
        default_ylabel: str,
        fig: Optional[plt.Figure] = None,
        ax: Optional[plt.Axes] = None,
        update_fig: bool = True,
        **kwargs
        ) -> tuple[plt.Figure, plt.Axes]:
            # Use default PlotConfig if none provided
        if plot_config is None:
            plot_config = PlotConfig(
                title=default_title,
                xlabel=default_xlabel,
                ylabel=default_ylabel
            )

        # Create figure and axes if not provided
        if ax is None:
            fig, ax = plt.subplots(figsize=plot_config.figsize)
        else:
            if fig is None:
                fig = ax.figure

        # Plot data
        ax.plot(
            x_data,
            y_data,
            plot_config.line_style,
            color=plot_config.color,
            label=plot_config.title,
            **kwargs
        )

        # Update figure elements if required
        if update_fig:
            ax.set_title(plot_config.title)
            ax.set_xlabel(plot_config.xlabel)
            ax.set_ylabel(plot_config.ylabel)
            ax.grid(plot_config.grid)
            ax.legend()

        # Do not show or save the plot here
        # Return the figure and axes for further processing
        return fig, ax
        
        
    def plot_stress_strain(self,
                           plot_config: Optional["PlotConfig"] = None,
                            fig: Optional[plt.Figure] = None,
                            ax: Optional[plt.Axes] = None,
                            update_fig: bool = True,
                            **kwargs
                        ) -> tuple[plt.Figure, plt.Axes]:
                           
        """
        Plot the stress-strain curve for a sample.
        Can be used to provide an automated view of the data, potentially overlayed with other samples.
        """
        if self.stress is None or self.strain is None:
            raise ValueError("Stress or strain data is missing for plotting the stress-strain curve.")
        
        # Default labels with units
        default_title = f"{self.name} Stress-Strain Curve"
        default_xlabel = f"Strain [{self.internal_units.get('strain', '')}]"
        default_ylabel = f"Stress [{self.internal_units.get('stress', '')}]"
        
        # Call the helper method
        return self._plot_data(
            x_data=self.strain,
            y_data=self.stress,
            plot_config=plot_config,
            default_title=default_title,
            default_xlabel=default_xlabel,
            default_ylabel=default_ylabel,
            fig=fig,
            ax=ax,
            update_fig=update_fig,
            **kwargs
        )
        
     
        

    def plot_force_displacement( self,
        plot_config: Optional["PlotConfig"] = None,
        fig: Optional[plt.Figure] = None,
        ax: Optional[plt.Axes] = None,
        update_fig: bool = True,
        **kwargs
        ) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the force-displacement curve for a sample.
        Can be used to provide an automated view of the data, potentially overlayed with other samples.
        """
        if self.force is None or self.displacement is None:
            raise ValueError("Force or displacement data is missing for plotting the force-displacement curve.")
        
        # Default labels with units
        default_title = f"{self.name} Force-Displacement Curve"
        default_xlabel = f"Displacement [{self.internal_units.get('displacement', '')}]"
        default_ylabel = f"Force [{self.internal_units.get('force', '')}]"3
        
        # Call the helper method
        return self._plot_data(
            x_data=self.displacement,
            y_data=self.force,
            plot_config=plot_config,
            default_title=default_title,
            default_xlabel=default_xlabel,
            default_ylabel=default_ylabel,
            fig=fig,
            ax=ax,
            update_fig=update_fig,
            **kwargs
        )


    # Interface - Abstract Methods

    @abstractmethod
    def plot(self) -> None:
        """
        Plot key performance indicators (KPI) relevant to the standard being used.
        This method must be implemented by subclasses to provide standard-specific views.
        """
        pass


