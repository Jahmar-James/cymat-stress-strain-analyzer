from standards.base.analyzable_entity import AnalyzableEntity
from typing import Optional, Annotated, Union
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd 

import seaborn as sns
from .plot import Plot, PlotState, PlotConfig, Coordinate
import matplotlib.pyplot as plt
from pathlib import Path
import datetime



class PlotManager:
    """
    Manages plotting and visualization for the entities (samples or sample groups).
    This class provides customizable control over data visualization, allowing users to select data, update plots, 
    and apply transformations for detailed analysis of mechanical test data.

    Key Responsibilities:
    - Dynamically select data to plot on the x and y axes (e.g., stress, strain, force, displacement, time).
    - Allow users to customize plot properties such as titles, axis labels, colors, markers, and styles.
    - Handle data transformations (e.g., shifting data) for alignment and comparison purposes.
    - Provide plotting options for line plots, scatter plots, bar charts, and more.
    - Support advanced plotting features such as adding region markers (e.g., plastic region indicators) and shaded regions to show variability.
    - Plot derivatives of series for advanced analysis (e.g., strain rate, yield point determination) using derivative methods from `BaseStandardOperator`.
    - Compare metrics across multiple samples using bar plots or histograms.
    - Save and export plots in various formats (PNG, SVG, etc.).
    
    This class is designed for users who need to go beyond basic automated plotting, offering more control and 
    customization for detailed analysis and comparison of mechanical test data.
    """

    def __init__(self):
        self.plots: dict[str, Plot] = {}
        # Default plot configuration
        self.default_plot_config = PlotConfig(
            title=None,
            xlabel=None,
            ylabel=None,
            figsize=(8, 6),
            line_style='-',
            color=None,  # Let Matplotlib auto-generate a color if not provided
            alpha=1.0,
            grid=True,
            show_origin=False,
            x_percent=False,
            x_rotation=None,
            x_minor_locator=None,
            y_minor_locator=None,
        ) 
        
    def list_available_plots(self) -> list[str]:
        return list(self.plots.keys())
    
    def list_plot_elements(self, plot_name: str) -> list[str]:
        if plot_name not in self.plots:
            raise ValueError(f"Plot '{plot_name}' does not exist.")
        plot = self.plots[plot_name]
        return list(plot.plot_state.elements.keys())
    
    def get_plot_elements_data(self, plot_name: str, element_label: str) -> plot_series:
        if plot_name not in self.plots:
            raise ValueError(f"Plot '{plot_name}' does not exist.")
        plot = self.plots[plot_name]
        if element_label not in plot.plot_state.elements:
            raise ValueError(f"Element '{element_label}' does not exist in plot '{plot_name}'.")
        element = plot.plot_state.elements[element_label]
        return element.get_data()
        
    def create_or_update_plot(self, 
                              entity: AnalyzableEntity, 
                              plot_name: str, 
                              x_data_key: Optional[str] = None, 
                              y_data_key: Optional[str] = None, 
                              data_key: Optional[str] = None,
                              element_label: Optional[str] = None,
                              plot_config: Optional[PlotConfig] = None, 
                              plot_type: str = 'custom') -> Optional[Plot]:
        
        """Add data to an existing or new plot"""
        plot_config = plot_config or self.default_plot_config
        plot, plot_state = self._create_plot_if_none(plot_name, plot_type, plot_config)
        
        x_data, y_data = self._normalize_data_for_plotting(entity, x_data_key, y_data_key, data_key)
        
        element_label = self._generate_element_label(element_label, x_data_key, y_data_key)
        plot = self._add_data_to_plot(plot, plot_type, plot_state, x_data, y_data, element_label)
        plot_state.ax = self._apply_plot_config(plot_state.ax, plot_config)
        plot_state.ax.legend()

        return plot
    
    def _create_plot_if_none(self, plot_name: str, plot_type: str, plot_config: PlotConfig) -> tuple[Optional[Plot], PlotState]:
        if plot_name not in self.plots:
            fig, ax = plt.subplots(figsize=plot_config.figsize)
            plot_state = PlotState(fig=fig, ax=ax, elements={})
            return None, plot_state
        else:
            return self.plots[plot_name], self.plots[plot_name].plot_state
     
     # Stateless API
        
    @staticmethod
    def _normalize_data_for_plotting(entity: AnalyzableEntity, x_data_key: Optional[str], y_data_key: Optional[str], data_key: Optional[str]) -> Union[tuple[pd.Series, pd.Series], tuple[float, float] ]:
        if data_key:
            data = PlotManager.get_entity_property(entity, data_key)
            if isinstance(data, Coordinate) and entity.is_sample_group is False:
                return data.x, data.y
            elif isinstance(data, pd.Series) and entity.is_sample_group is True and hasattr(entity, 'samples'):
                x_data = list(range(len(entity.samples)))
                y_data = data
                return pd.Series(x_data, name=entity.name), y_data
            else:
                raise ValueError(f"Cannot normalize data for plotting. Invalid data type for '{data_key}'.")
        else:
            x_data = PlotManager.get_entity_data(entity, x_data_key)
            y_data = PlotManager.get_entity_data(entity, y_data_key)
            return x_data, y_data
    
    @staticmethod
    def _generate_element_label(element_label: Optional[str], x_data_key: Optional[str], y_data_key: Optional[str]) -> str:
        if element_label:
            return element_label
        if x_data_key and y_data_key:
            return f"{x_data_key} vs {y_data_key}"
        elif x_data_key:
            return x_data_key
        elif y_data_key:
            return y_data_key
        else:
            # data with the time stamp  2021-09-01 12:00:00
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"Data {date}"
   
    @staticmethod 
    def _add_data_to_plot(plot: Plot, plot_type: str, plot_state: PlotState, x_data: pd.Series, y_data: pd.Series, element_label: str) -> Optional[Plot]:
        if plot_type == 'line':
            line, = plot_state.ax.plot(x_data, y_data, label=element_label, linestyle=plot.plot_config.line_style, color=plot.plot_config.color)
            plot_state.elements[element_label] = line
            return plot
        elif plot_type == 'scatter':
            scatter = plot_state.ax.scatter(x_data, y_data, label=element_label, color=plot.plot_config.color)
            plot_state.elements[element_label] = scatter  # Track the scatter points
            return plot
        elif plot_type == 'histogram':
            plot_state.ax.hist(y_data, label=element_label, color=plot.plot_config.color)
            return plot  
        elif plot_type == 'custom':
            # depending on the data type, add the data to the plot.
            raise NotImplementedError("Custom plot type not implemented yet.")
        else:
            raise ValueError(f"Invalid plot type '{plot_type}'. Must be 'line', 'scatter', 'histogram', or 'custom'.")
    
    @staticmethod
    def add_region_marker():
        raise NotImplementedError("PlotManager's add_region_marker is not implemented yet.")
    
    
    def save_shifted_data_to_entity( self, plot_name: str, element_label: str, shifted_x_data: pd.Series, shifted_y_data: pd.Series) -> None:
        if plot_name not in self.plots:
            raise ValueError(f"Plot '{plot_name}' does not exist.")
        
        plot = self.plots[plot_name]
        plot_state = plot.plot_state
        
        if element_label not in plot_state.element_sources:
            raise ValueError(f"Element '{element_label}' does not exist in plot '{plot_name}'.")
        
        entity_name, property_name = plot_state.element_sources[element_label]
        entitiy = self.get_entity_by_name(entity_name)
        
        if hasattr(entity, property_name):
            setattr(entity, property_name, (shifted_x_data, shifted_y_data))
            
        
        raise NotImplementedError("PlotManager's shift_data is not implemented yet.")
    
    @staticmethod
    def add_shaded_region():
        raise NotImplementedError("PlotManager's add_shaded_region is not implemented yet.")
    
    @staticmethod
    def add_patch():
        raise NotImplementedError("PlotManager's add_patch is not implemented yet.")
    
    @staticmethod
    def add_derivative():
        raise NotImplementedError("PlotManager's add_derivative is not implemented yet.")
    
    @staticmethod
    def set_style( plot: Plot,style: str) -> None:
        # style can be 'seaborn', 'ggplot', 'classic', etc.
        raise NotImplementedError("PlotManager's set_style is not implemented yet.")

    # Persisting and Exporting Plots
    
    @staticmethod
    def save_plot( plot: Plot, file_path: Union[str, Path], file_format: str = 'png') -> bool:
        raise NotImplementedError("PlotManager's save_plot is not implemented yet.")
    
    @staticmethod
    def save_config( config: PlotConfig, file_path: Union[str, Path], file_format: str = 'json') -> bool:
        raise NotImplementedError("PlotManager's save_config is not implemented yet.")
    @staticmethod
    def export_plot_data( plot: Plot, file_path: Union[str, Path], file_format: str = 'csv') -> bool:
        raise NotImplementedError("PlotManager's export_plot_data is not implemented yet.")
    
    @staticmethod
    def get_entity_data(entity: AnalyzableEntity, entity_property_key: str) -> pd.Series:
        try:
            data = getattr(entity, entity_property_key)
            if not isinstance(data, pd.Series):
                raise ValueError(f"Entity data '{entity_property_key}' must be a Pandas Series.")
            return data
        except AttributeError:
            raise AttributeError(f"Entity '{entity.name}' does not have the property '{entity_property_key}'.")
    
    @staticmethod
    def get_entity_property(entity: AnalyzableEntity, entity_property_key: str) -> Union[Coordinate, float]:
        try:
            data = getattr(entity, entity_property_key)
            if not isinstance(data, (Coordinate, float, int)):
                raise ValueError(f"Entity property '{entity_property_key}' must be a Coordinate or a float.")
            return data
        except AttributeError:
            raise AttributeError(f"Entity '{entity.name}' does not have the property '{entity_property_key}'.")
    
    @staticmethod
    def _apply_plot_config(ax: plt.Axes, plot_config: PlotConfig) -> plt.Axes :
        """
        Applies the plot configuration to the given Axes object.
        """
        if plot_config.title:
            ax.set_title(plot_config.title)
        if plot_config.xlabel:
            ax.set_xlabel(plot_config.xlabel)
        if plot_config.ylabel:
            ax.set_ylabel(plot_config.ylabel)
        if plot_config.grid:
            ax.grid(True)
        if plot_config.show_origin:
            ax.axhline(0, color='black', linestyle='--')
            ax.axvline(0, color='black', linestyle='--')
        if plot_config.x_percent:
            ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
        if plot_config.x_rotation is not None:
            ax.tick_params(axis='x', rotation=plot_config.x_rotation)
        if plot_config.x_minor_locator is not None:
            ax.xaxis.set_minor_locator(mtick.AutoMinorLocator(plot_config.x_minor_locator))
        if plot_config.y_minor_locator is not None:
            ax.yaxis.set_minor_locator(mtick.AutoMinorLocator(plot_config.y_minor_locator))
        if plot_config.legend_position:
            ax.legend(loc=plot_config.legend_position)
            
        return ax   


    @staticmethod      
    def plot_derivative( entity: AnalyzableEntity, series_key: str, derivative_type: str = 'first', plot_config: Optional[PlotConfig] = None) -> tuple[plt.Figure, plt.Axes]:
        # Retrieve the required data series from the entity (e.g., stress or strain)
        data_series = getattr(entity, series_key, None)
        if data_series is None:
            raise ValueError(f"The entity does not have a series with the key '{series_key}'.")

        # Calculate the derivative using the entity's property_calculator
        if derivative_type == 'first':
            derivative_series = entity.property_calculator.calculate_first_derivative(data_series)
        elif derivative_type == 'second':
            derivative_series = entity.property_calculator.calculate_second_derivative(data_series)
        else:
            raise ValueError("Invalid derivative type. Must be 'first' or 'second'.")

        # Create a plot for the derivative
        fig, ax = plt.subplots(figsize=plot_config.figsize if plot_config else (8, 6))
        ax.plot(data_series.index, derivative_series, linestyle=plot_config.line_style if plot_config else '-', color=plot_config.color if plot_config else 'blue')

        # Apply the plot configuration (title, labels, etc.)
        if plot_config:
            PlotManager._apply_plot_config(ax, plot_config)

        return fig, ax