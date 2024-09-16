from dataclasses import dataclass, asdict, field
from typing import Optional, Union
import yaml
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.collections as mcoll
import pandas as pd
from collections import namedtuple


Coordinate = namedtuple('Coordinate', ['x', 'y'])

@dataclass
class Plot:
    """
    Core class for storing the data, configuration, and state of a plot.
    This class acts as the central container for each plot, keeping track
    of the data, its configuration, plot type, and its visibility state via PlotState.
    
    Figure related elements and methods
    """
    name: str  # Name or identifier for the plot (e.g., 'Stress-Strain Plot')
    plot_type: str  # Type of plot ('line', 'scatter', 'histogram', 'custom')
    x_data: Optional[Union[pd.Series, list["Coordinate"]]] = None  # X-axis data, either pd.Series or a list of Coordinates
    y_data: Optional[Union[pd.Series, list["Coordinate"]]] = None  # Y-axis data, either pd.Series or a list of Coordinates
    plot_config: Optional["PlotConfig"] = None  # The plot configuration (e.g., colors, labels, line styles)
    plot_state: Optional["PlotState"] = None  # The current state of the plot (visibility, elements, etc.)
    plot_elements: dict[str, Union[mlines.Line2D, mcoll.PathCollection]] = field(default_factory=dict)  # Plot elements by label

    def add_plot_element(self, label: str, element: Union[mlines.Line2D, mcoll.PathCollection]):
        self.plot_elements[label] = element


    def hide_plot_element(self, label: str) -> None:
        if label not in self.plot_elements:
            raise ValueError(f"In {self.name} No element with label '{label}' found.")
        self.plot_elements[label].set_visible(False)
        self.plot_state.fig.canvas.draw()
        
    def show_plot_element(self, label: str) -> None:
        if label not in self.plot_elements:
            raise ValueError(f"In {self.name} No element with label '{label}' found.")
        self.plot_elements[label].set_visible(True)
        self.plot_state.fig.canvas.draw()
        
    def remove_plot_element(self, label: str) -> None:
        if label not in self.plot_elements:
            raise ValueError(f"In {self.name} No element with label '{label}' found.")
        self.plot_elements[label].remove()
        del self.plot_elements[label]
        self.plot_state.fig.canvas.draw()
      
    
@dataclass
class PlotState:
    """
    Class to manage the state of the plot, including all plot elements (lines, scatter points, etc.).
    Provides methods to hide, show, and remove individual elements.
    
    Axis related elements and methods are here
    """
    fig: plt.Figure  # The figure object that contains all the axes
    axes: dict[str, plt.Axes]  # Tracks axes by label, e.g., 'ax1', 'ax2', etc.
    elements: dict[str, dict[str, Union[mlines.Line2D, mcoll.PathCollection]]]  # Tracks elements by axis and label
    element_sources: dict[str, dict[str, tuple[str, str]]]  # axis_label -> {element_label: (entity_name, property_name)}
    current_axis: Optional[str] = None  # Tracks which axis is currently active

    def set_active_axis(self, axis_label: str) -> None:
        if axis_label not in self.axes:
            raise ValueError(f"Axis '{axis_label}' does not exist in the plot.")
        self.current_axis = axis_label
    
    def add_axis(self, axis_label: str, ax: plt.Axes) -> None:
        self.axes[axis_label] = ax
        self.elements[axis_label] = {}  # Initialize an empty dict to track elements for this axis
        self.element_sources[axis_label] = {}  # Initialize an empty dict to track sources for this axis
    
    def remove_axis(self, axis_label: str) -> None:
        if axis_label in self.axes:
            self.fig.delaxes(self.axes[axis_label])  # Remove the axis from the figure
            del self.axes[axis_label]  # Remove axis from state
            del self.elements[axis_label]  # Remove associated elements
            del self.element_sources[axis_label]  # Remove associated sources
            if self.current_axis == axis_label:
                self.current_axis = None  # Reset current axis if it was the removed one
        else:
            raise ValueError(f"Axis '{axis_label}' does not exist in the plot.")
    
    def get_active_axis(self) -> Optional[plt.Axes]:
        if self.current_axis:
            return self.axes.get(self.current_axis)
        return None
        
    
@dataclass
class PlotConfig:
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    figsize: tuple[float, float] = (12, 8)
    line_style: str = '-'
    color: Optional[str] = None
    alpha: float = 1.0
    grid: bool = True
    show_origin: bool = False
    x_percent: bool = False  # Format x-axis as percentage
    x_rotation: Optional[float] = None  # Rotation angle for x-axis tick labels
    x_minor_locator: Optional[int] = None  # Number of minor ticks between major ticks on x-axis
    y_minor_locator: Optional[int] = None  # Number of minor ticks between major ticks on y-axis
    legend_position: str = 'best'  # Default legend position
    # Additional parameters can be added as needed
    ncols: int = 1  # Number of columns for subplots
    nrows: int = 1 # Number of rows for subplots

    def to_dict(self) -> dict[str, any]:
        """
        Converts the PlotConfig to a dictionary.
        """
        return asdict(self)
    
    def __str__(self) -> str:
        return str(self.to_dict())
    
    @staticmethod
    def _normalize_path( path: Union[str, Path]) -> Path:
        if isinstance(path, str):
            return Path(path)
        else:
            raise ValueError("Invalid path type. Must be a string or Path object.")
     
    @classmethod
    def from_dict(cls, config_dict: dict[str, any]):
        """
        Creates a PlotConfig instance from a dictionary.
        """
        return cls(**config_dict)

    def to_yaml(self, file_path: Union[str, Path]) -> None:
        """
        Saves the PlotConfig to a YAML file.
        """
        file_path = self._normalize_path(file_path)
        with open(file_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)

    @classmethod
    def from_yaml(cls, file_path: Union[str, Path]):
        """
        Loads the PlotConfig from a YAML file.
        """
        file_path = cls._normalize_path(file_path)
        
        with open(file_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)
