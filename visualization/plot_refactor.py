"""
Refactor plot , plot state and plot manager 

PlotManager is the Orchestrator: Handles overall plot management 
and delegates data normalization, configuration, and state tracking to Plot and PlotState

Methods:
    - list_available_plots() -> list[str]:
    - list_plot_elements() -> list[str]:
    - create_or_update_plot() -> Plot:
    - remove_plot() -> bool:
    - get_entity_data() -> pd.Series: [static]
    - get_entity_property() -> Coordinate: [static]
    - get_plot_elements_data() Union[tuple[pd.Series, pd.Series], Coordinate]: [static]
    - get_plot_element_derivative() -> pd.Series: [static] *entity.property_calcuator for computing derivative
    - get_plot_element_integral()-> pd.Series: [static] *entity.property_calcuator for computing integral
    - save_shifted_data_to_entity() -> bool: [static]
    - _normalize_data_for_plotting() -> Union[tuple[pd.Series, pd.Series], tuple[float, float] ]: [static]
    - _generate_element_label() -> str : [static]

Plot Manages the Data (Figure / Plot) and Configuration:
Methods:
    - add_plot_element():
    - set_style():
    - update_plot() -> Plot:
    - add_axis() -> tuple[plt.Figure, plt.Axes]:
    - remove_axis() - > bool:
    - apply_plot_config() -> plt.Axes:
    - save_plot() - > bool:
    - export_plot_data() - > bool:

PlotState Tracks the Plot's State: (Decople state and data)
Responsible for keeping track of elements (lines, scatter points) and ensuring the 
where that data is comes is tracked, by recording (entitty), the properties on which axes
Methods:
    - add_plot_element() - > bool:
    - hide_plot_element() - > bool:
    - show_plot_element() - > bool:
    - remove_plot_element() - > bool:
    - update_plot_element() - > bool:
    - hide_legend() - > bool:
    - show_legend() - > bool:
    - set_active_axis() > plt.Axes:
    - _add_shaded_region( ) -> bool: Artist Patch
    - _add_text_annotation() -> bool: Artist Text
    - _add_arrow() -> bool: Artist 
    - _add_image() -> bool: Artist Image
    - _add_patch() -> bool:

PlotConfig:
    - Stores the configuration of the plot (e.g., colors, labels, line styles)
    - Provides a default configuration if none is provided
    
PlotExporter
    -  Handles saving plots, exporting plot data, and configuration.

dataclass Coordinate:
    - Represents a point in 2D space
    - Used to store x, y coordinates for plotting

dataclass PlotElement:
    - Represents a single element in a plot (e.g., a line, scatter point)
    - Contains the plot object, x and y data, entity name, property name, and axis
"""
from typing import Optional, Union, TYPE_CHECKING
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.collections as mcoll
import datetime
import matplotlib.ticker as mtick
import numpy as np
from dataclasses import dataclass

if TYPE_CHECKING:
    import PIL




@dataclass
class Coordinate:
    x: float
    y: float
    
@dataclass(frozen=True)    
class PlotElement:
    plot_obj: Union[plt.Line2D,          # For line plots and axhline/axvline
                    plt.PathCollection,  # For scatter plots
                    plt.BarContainer,    # For bar plots and histograms
                    plt.PolyCollection,  # For area plots (fill_between)
                    plt.AxesImage,       # For heatmaps
                    plt.QuadContourSet,  # For contour plots
                    plt.Text,            # For text annotations
                    plt.Annotation]      # For annotated arrows
    entity_name: str            # The name of the entity that provided the data
    element_label: str          # The name of the entity's property being plotted
    ax: plt.Axes                # The axis on which the plot is drawn
    # Additional parameters that can be removed if memory becomes an issue
    x_data: Optional[pd.Series] = None  # The x data for the plot element
    y_data: Optional[pd.Series] = None  # The y data for the plot element
    plot_type: Optional[str] = None  # The type of plot element (line, scatter, bar, etc.)
    


    
class PlotManager:
    def __init__(self):
        self.plots: dict[str, "Plot"] = {}
        self.default_plot_config = PlotConfig()
        
    def create_or_update_plot(self, 
                              entity: "AnalyzableEntity", 
                              plot_name: Optional[str] = None,
                              plot : Optional["Plot"] = None,
                              x_data_key: Optional[str] = None, 
                              y_data_key: Optional[str] = None, 
                              data_key: Optional[str] = None,
                              element_label: Optional[str] = None,
                              plot_config: Optional["PlotConfig"] = None, 
                              plot_type: str = 'custom') -> Optional["Plot"]:
        
        plot_config = plot_config or self.default_plot_config  
        plot = self._create_plot_if_none(plot, plot_name, plot_type, plot_config)
        x_data, y_data = self._normalize_data_for_plotting(entity, x_data_key, y_data_key, data_key)
        element_label = self._generate_element_label(element_label, x_data_key, y_data_key, data_key)
        susccess_operation = plot.add_plot_element(entity.name, x_data, y_data, element_label, plot_config)
        
        if susccess_operation:
            return plot
        else:
            return None
        
    def _create_plot_if_none(self, plot: Optional["Plot"], plot_name: Optional[str], plot_type: str, plot_config: "PlotConfig") -> "Plot":
        if plot is None and plot_name is None:
            raise ValueError("Either a plot object or a plot name must be provided.")
        elif plot and plot.name in self.plots:
            if plot.plot_state.elements is self.plots[plot.name].plot_state.elements:
                print("Adding to existing plot, updating type")
                # Update the plot type to ensure the correct plot function is used
                plot.plot_type = plot_type
            else:
                # More infromative than a key error
                raise ValueError(f"Plot '{plot.name}' already exists. , please provide a unique plot name.")
        elif plot:
            self.plots[plot.name] = plot
        elif plot_name not in self.plots and plot_name:
            plot = Plot(plot_name, plot_type, plot_config)
            self.plots[plot_name] = plot
        else:
            plot = self.plots["default_plot"]
        return plot
    
    @staticmethod
    def get_entity_data(entity: "AnalyzableEntity", entity_property_key: str) -> pd.Series:
        try:
            data = getattr(entity, entity_property_key)
            if not isinstance(data, pd.Series):
                raise ValueError(f"Entity data '{entity_property_key}' must be a Pandas Series.")
            return data
        except AttributeError:
            raise AttributeError(f"Entity '{entity.name}' does not have the property '{entity_property_key}'.")
    
    @staticmethod
    def get_entity_property(entity: "AnalyzableEntity", entity_property_key: str) -> Union[Coordinate, float]:
        try:
            data = getattr(entity, entity_property_key)
            if not isinstance(data, (Coordinate, float, int)):
                raise ValueError(f"Entity property '{entity_property_key}' must be a Coordinate or a float.")
            return data
        except AttributeError:
            raise AttributeError(f"Entity '{entity.name}' does not have the property '{entity_property_key}'.")
        
    @staticmethod
    def _normalize_data_for_plotting(entity: "AnalyzableEntity", x_data_key: Optional[str], y_data_key: Optional[str], data_key: Optional[str]) -> Union[tuple[pd.Series, pd.Series], tuple[float, float] ]:
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
    def _generate_element_label(element_label: Optional[str], x_data_key: Optional[str], y_data_key: Optional[str], data_key: Optional[str]) -> str:
        if element_label:
            return element_label
        if data_key:
            return data_key
        if x_data_key and y_data_key:
            return f"{y_data_key} vs {x_data_key}"
        elif x_data_key:
            return x_data_key
        elif y_data_key:
            return y_data_key
        else:
            # data with the time stamp  2021-09-01 12:00:00
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"Data {date}"
        
    def list_available_plots(self) -> list[str]:
        return list(self.plots.keys())
    
    def list_plot_elements(self, plot_name: str) -> list[str]:
        if plot_name not in self.plots:
            raise ValueError(f"Plot '{plot_name}' does not exist.")
        plot = self.plots[plot_name]
        return list(plot.plot_state.elements.keys())
    
    def get_plot_elements_data(self, plot_name: str, element_label: str) -> Union[tuple[pd.Series, pd.Series], Coordinate]:
        if plot_name not in self.plots:
            raise ValueError(f"Cannot get data for plot '{plot_name}'. Plot does not exist.")
        plot = self.plots[plot_name]
        return plot.plot_state.get_element_data(element_label)
    
    @staticmethod
    def save_shifted_data_to_entity(entity: "AnalyzableEntity", property_key: str, updated_x_data: Union[pd.Series,float], updated_y_data: Union[pd.Series,float]) -> bool:
        if not hasattr(entity, property_key):
            raise AttributeError(f"Can not shift, Entity '{entity.name}' does not have the property '{property_key}'.")
        # Get the current data and ensure it of the same type and length
        current_data = getattr(entity, property_key)
        if isinstance(current_data, pd.Series):
            if not isinstance(updated_x_data, pd.Series) or not isinstance(updated_y_data, pd.Series):
                raise ValueError("Updated shift data must be a Pandas Series.")
            if len(updated_x_data) != len(current_data) or len(updated_y_data) != len(current_data):
                raise ValueError("Updated shift data must have the same length as the current data.")
        else:
            if not isinstance(updated_x_data, (float, int)) or not isinstance(updated_y_data, (float, int)):
                raise ValueError("Updated shift data must be a float.")
        for updated_data in [updated_x_data, updated_y_data]:
            setattr(entity, f"{property_key}", updated_data)
            setattr(entity, f"Orignal_{property_key}", updated_data)
        return True
   
        
class Plot:
    def __init__(self, name: str, 
                 plot_type: str, 
                 plot_config: Optional["PlotConfig"] = None,
                 plot_state: Optional["PlotState"] = None,
                 fig : Optional[plt.Figure] = None,
                 axes: Optional[dict[str, plt.Axes]] = None,
                 style: Optional[str] = None
                 ):
        
        # Initialize
        self.name = name
        self.plot_type = plot_type
        self.default_plot_config = PlotConfig(
            title=None, xlabel=None, ylabel=None, figsize=(8, 6),
            line_style='-', color=None, alpha=1.0, grid=True
        )
        self.plot_config : PlotConfig = plot_config or self.default_plot_config
        
        # Don't create the state yet
        self.plot_state = plot_state or PlotState()
        self.fig = fig
        self.axes = axes 
        self.style = style 
        
    def add_plot_element(self,
                         entity_name: str, 
                         x_data: pd.Series, 
                         y_data: pd.Series, 
                         element_label: str, 
                         plot_config: Optional["PlotConfig"] = None,
                         text: Optional[str] = None,
                         annotation: Optional[dict] = None) -> bool:
        if element_label in self.plot_state.elements:
            raise ValueError(f"Element '{element_label}' already exists in plot '{self.name}'.")
    
        fig, ax = self._get_or_create_axes_and_fig()
            
       # Different plot functions based on the plot type
        if self.plot_type in ['line']: # Line2D 
            plot_artist = ax.plot(x_data, y_data, label=element_label)[0]  # Line2D object
        elif self.plot_type == 'scatter': 
            plot_artist = ax.scatter(x_data, y_data, label=element_label)  # PathCollection object
        elif self.plot_type == 'fill_between':
            plot_artist = ax.fill_between(x_data, y_data, label=element_label)  # PolyCollection object
        elif text:
            plot_artist = ax.text(x_data, y_data, text, fontsize=12)  # Text object
        elif self.plot_type == 'histogram': 
            plot_artist = ax.hist(y_data, label=element_label)  # Histogram returns a tuple of objects
        elif annotation:
            plot_artist = ax.annotate(annotation['text'], 
                                    xy=(annotation['x'], annotation['y']), 
                                    xytext=(annotation['text_x'], annotation['text_y']),
                                    arrowprops=dict(facecolor='black', shrink=0.05))  # Annotation object 
        else:
            raise ValueError(f"Invalid plot type '{self.plot_type}'.")
        
        plot_element = PlotElement(
            plot_obj=plot_artist, 
            entity_name=entity_name, 
            element_label=element_label, 
            ax=ax, 
            x_data=x_data, 
            y_data=y_data, 
            plot_type=self.plot_type
        )
        self.plot_state.elements[element_label] = plot_element
        plot_config = plot_config or self.plot_config
        ax = self._apply_plot_config(ax, plot_config)
        return True
        
    def _get_or_create_axes_and_fig(self, ax_key: Optional[str] = None) -> tuple[plt.Figure, plt.Axes]:
        if self.fig is None or self.axes is None:
            self.fig, axes = plt.subplots(nrows=self.plot_config.nrows, ncols=self.plot_config.ncols, figsize=self.plot_config.figsize)

            if self.plot_config.ncols > 1 or self.plot_config.nrows > 1:
                self.axes = {f'ax_{i}': ax for i, ax in enumerate(axes.flatten())}
            else:
                # If single axis, store it as 'main'
                self.axes = {'main': axes}

            for ax in self.axes.values():
                ax = self._apply_plot_config(ax, self.plot_config)

        if len(self.axes) == 1:
            return self.fig, self.axes['main']

        if ax_key is not None:
            if ax_key in self.axes:
                return self.fig, self.axes[ax_key]
            else:
                raise ValueError(f"Axis key '{ax_key}' does not exist in the plot '{self.name}'.")

        return self.fig, self.axes['main']

    def update_plot(self, plot_config: "PlotConfig", ax :Optional[plt.Axes]= None) -> bool:
        if ax is None:
            fig, ax = self._get_or_create_axes_and_fig()
        ax = self._apply_plot_config(ax, plot_config)
        return True
    
    @staticmethod
    def _apply_plot_config(ax: plt.Axes, plot_config: "PlotConfig") -> plt.Axes :
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
    def tranfer_axes_to_new_figure(existing_axes: plt.Axes,
                                   plot_state: "PlotState",
                                   postion: Optional[str] = "below",
                                   plot_config: Optional["PlotConfig"] = None) -> tuple[plt.Figure, plt.Axes]:
       if len(existing_axes)
        
    def add_axis_in_direction( existing_axes: plt.Axes,
                                plot_state: "PlotState",
                                postion: str = "below",
                                plot_config: Optional["PlotConfig"] = None) -> tuple[plt.Figure, plt.Axes]:
        if len(existing_axes) != 1:
            raise ValueError("'add_axis_in_direction' can only be used with a single axis.")
        
        if postion not in ['below', 'above', 'right', 'left']:
            raise ValueError("Invalid position. Must be 'below', 'above', 'right', or 'left'.")
        
        if postion == 'below' or postion == 'above':
            nrows, ncols = 2, 1
        elif postion == 'right' or postion == 'left':
            nrows, ncols = 1, 2
            
        figsize = (existing_axes.get_figure().get_size_inches() * np.array([ncols, nrows])) if plot_config is None else plot_config.figsize
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize)
        plot_elements_in_axes = [element for element in plot_state.elements.values() if element.ax == existing_axes]
        
        for element in plot_elements_in_axes:
            if element.ax == existing_axes:
                entitu_name, x_data, y_data, element_label, plot_type = element.entity_name, element.x_data, element.y_data, element.element_label, element.plot_type     
                # if above transfer the existing plot to the bottom
                plot.add_plot_element(entity_name, x_data, y_data, element_label, plot_config)
                    
                
                # if left transfer the existing plot to the right
        
        
   

class PlotState:
    def __init__(self):
        # axis_label -> {element_label: PlotElement}
        self.elements : dict[str, PlotElement] = {}      
        
    def get_element(self, element_label: str) -> PlotElement:
        if element_label not in self.elements:
            raise ValueError(f"Cannot get element '{element_label}'. Element does not exist.")
        return self.elements[element_label]
    
    def get_element_data_from_plot(self, element_label: str) -> Union[tuple[pd.Series, pd.Series], Coordinate]:
        """
        NOT Needed - if memory becomes an issue, we can use this to get data from the plot
        and remove x and y datd from plot element
        """
        if element_label not in self.elements:
            raise ValueError(f"Cannot get data for element '{element_label}'. Element does not exist.")
        element = self.elements[element_label]
        plot_obj = element.plot_obj
        if isinstance(plot_obj, plt.Line2D):
            label = plot_obj.get_label()
            return pd.Series(plot_obj.get_xdata(), name=f'{label}_x_data'), pd.Series(plot_obj.get_ydata(), name=f'{label}_y_data')
        # PathCollection for scatter ploy
        elif isinstance(plot_obj, plt.PathCollection):
            label = plot_obj.get_label()
            return pd.Series(plot_obj.get_offsets()[:, 0], name=f'{label}_x_data'), pd.Series(plot_obj.get_offsets()[:, 1], name=f'{label}_y_data')
        # PolyCollection for area plots (fill_between)
        elif isinstance(plot_obj, plt.PolyCollection):
            paths = plot_obj.get_paths()  # Get the paths that form the filled area
            vertices = paths[0].vertices  # Get the vertices of the first path
            return pd.Series(vertices[:, 0], name='x_data'), pd.Series(vertices[:, 1], name='y_data') 
        # For text annotations
        elif isinstance(plot_obj, plt.Text):
            return f"Text: {plot_obj.get_text()}"
        # For annotated arrows
        elif isinstance(plot_obj, plt.Annotation): 
            return f"Annotation: {plot_obj.get_text()}"
        # BarContainer for bar plots and histograms
        elif isinstance(plot_obj, plt.BarContainer):
            rects = plot_obj.patches  # The actual bars (Rectangle objects)
            x_data = [rect.get_x() + rect.get_width() / 2 for rect in rects]  # X is the bar center
            y_data = [rect.get_height() for rect in rects]  # Y is the height of the bar
            return pd.Series(x_data, name='x_data'), pd.Series(y_data, name='y_data')
        # For heatmaps (imshow)
        elif isinstance(plot_obj, plt.AxesImage):
            data_array = plot_obj.get_array().data
            return pd.Series(data_array.flatten(), name='data_matrix'), None
        # For heatmaps (pcolormesh)
        elif isinstance(plot_obj, plt.QuadMesh):
            data_array = plot_obj.get_array()
            # Get the limits for the color mapping (clim)
            clim = plot_obj.get_clim()
            return pd.Series(data_array.flatten(), name='grid_data'), pd.Series(clim, name='color_limits')
        # For contour plots
        elif isinstance(plot_obj, plt.QuadContourSet):
            levels = plot_obj.levels
            # Get all line segments for each contour level
            contour_segments = plot_obj.allsegs  # List of arrays, one per contour level
            data = []
            for level, segments in zip(levels, contour_segments):
                for segment in segments:
                    data.append({'level': level, 'x': segment[:, 0], 'y': segment[:, 1]})
            return pd.Series([d['level'] for d in data], name='contour_levels'), pd.Series([d['x'] for d in data], name='x_coords'), pd.Series([d['y'] for d in data], name='y_coords')
                
        else:
            raise ValueError(f"Cannot get data for element '{element_label}'. Invalid plot object type.")
        
    def hide_plot_element(self, element_label: str) -> bool:
        if element_label not in self.elements:
            raise ValueError(f"Cannot hide element '{element_label}'. Element does not exist.")
        element = self.elements[element_label]
        element.plot_obj.set_visible(False)
        return True
    
    def show_plot_element(self, element_label: str) -> bool:
        if element_label not in self.elements:
            raise ValueError(f"Cannot show element '{element_label}'. Element does not exist.")
        element = self.elements[element_label]
        element.plot_obj.set_visible(True)
        return True
       
    def remove_plot_element(self, element_label: str) -> bool:
        if element_label not in self.elements:
            raise ValueError(f"Cannot remove element '{element_label}'. Element does not exist.")
        del self.elements[element_label]
        return True
    
    def update_plot_element_style(self,
                                  element_label: str,
                                  style: Optional[str] = None,
                                    color: Optional[str] = None,
                                    alpha: Optional[float] = None,
                                    linestyle: Optional[str] = None,
                                    linewidth: Optional[float] = None,
    ) -> bool:
        if element_label not in self.elements:
            raise ValueError(f"Cannot update style for element '{element_label}'. Element does not exist.")
        element = self.elements[element_label]
        try:
            if style:
                element.plot_obj.set_linestyle(style)
            if color:
                element.plot_obj.set_color(color)
            if alpha:
                element.plot_obj.set_alpha(alpha)
            if linestyle:
                element.plot_obj.set_linestyle(linestyle)
            if linewidth:
                element.plot_obj.set_linewidth(linewidth)
            return True
        except Exception as e:
            raise ValueError(f"Error updating style for element '{element_label}': {e}")
        
    def hide_legend(self) -> bool:
        for element in self.elements.values():
            element.plot_obj.set_label('_nolegend_')
        return True
    
    def show_legend(self) -> bool:
        for element in self.elements.values():
            element.plot_obj.set_label(element.element_label)
        return True
    
    def add_horizontal_line(self, ax: plt.Axes,  y: float, color: str = 'black', linestyle: str = '--', element_label: str = "horizontal_line") -> bool:
        if "horizontal_line" in element_label and element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"
        # Line2D object
        line = ax.axhline(y=y, color=color, linestyle=linestyle, label=element_label)
        plot_element = PlotElement(line, entity_name="annotation", element_label=element_label, ax=ax)
        self.elements[element_label] = plot_element
        return True
    
    def add_vertical_line(self, ax: plt.Axes, x: float, color: str = 'black', linestyle: str = '--', element_label: str = "vertical_line") -> bool:
        if "vertical_line" in element_label and element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"
        # Line2D object
        line = ax.axvline(x=x, color=color, linestyle=linestyle, label=element_label)
        plot_element = PlotElement(line, entity_name="annotation", element_label=element_label, ax=ax)
        self.elements[element_label] = plot_element
        return True
        
    def add_shaded_region(self, ax: plt.Axes, x1: float, x2: float, color: str = 'gray', alpha: float = 0.5, element_label: str = "shaded_region") -> bool:
        if "shaded_region" in element_label and element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"
        # PolyCollection object
        region = ax.fill_betweenx(ax.get_ylim(), x1, x2, color=color, alpha=alpha, label=element_label)
        plot_element = PlotElement(region, entity_name="annotation", element_label=element_label, ax=ax)
        self.elements[element_label] = plot_element
        return True
    
    def add_text_annotation(self, ax: plt.Axes, x: float, y: float, text: str, fontsize: int = 12, element_label: str = "text_annotation") -> bool:
        if "text_annotation" in element_label and element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"
        # Text object
        text = ax.text(x, y, text, fontsize=fontsize, label=element_label)
        plot_element = PlotElement(text, entity_name="annotation", element_label=element_label, ax=ax)
        self.elements[element_label] = plot_element
        return True
    
    def add_arrow(self, ax: plt.Axes, x: float, y: float, dx: float, dy: float, element_label: str = "arrow") -> bool:
        if "arrow" in element_label and element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"
        # Annotation object
        arrow = ax.annotate("", xy=(x, y), xytext=(x + dx, y + dy), arrowprops=dict(facecolor='black', shrink=0.05), label=element_label)
        plot_element = PlotElement(arrow, entity_name="annotation", element_label=element_label, ax=ax)
        self.elements[element_label] = plot_element
        return True
    
    def add_image(self, ax: plt.Axes, image: "PIL.Image", element_label: str = "image") -> bool:
        if "image" in element_label and element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"
        # AxesImage object
        ax.add_image(image, label=element_label)
        plot_element = PlotElement(image, entity_name="annotation", element_label=element_label, ax=ax)
        self.elements[element_label] = plot_element
        return True


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


class AnalyzableEntity:
    def __init__(self,):
        self.name = "Dummy Entity"
        self._strength = Coordinate(10, 20)
    """Dummy class to represent an entity that can be analyzed."""
    @property
    def stress(self) -> pd.Series:
        return pd.Series([1, 2, 3, 4, 5], name='stress')
    
    @property
    def strain(self) -> pd.Series:
        return pd.Series([1, 4, 9, 16, 25], name='strain')
    
    @property
    def force(self) -> pd.Series:
        return pd.Series([10, 20, 30, 40, 50], name='force')    
    
    @property
    def displacement(self) -> pd.Series:
        return pd.Series([1, 2, 3, 4, 5], name='displacement')  
    
    @property
    def is_sample_group(self) -> bool:
        return False
    
    @property
    def strength(self) -> "Coordinate":
        return self._strength

def cli_frontend() -> None:
    plot_manager = PlotManager()

    # Dummy data for testing
    x_data = np.linspace(0, 10, 100)
    y_data = np.sin(x_data) + random.uniform(-0.5, 0.5)

    # Simulate user choices
    while True:
        print("\n--- Dummy Plot Frontend ---")
        print("1. Create Line Plot")
        print("2. Create Scatter Plot")
        print("3. Display Plot")
        print("4. Exit")
        
        choice = input("Choose an option: ")
        
        entity_instance = AnalyzableEntity()
        plot_manager = PlotManager()
        
        if choice == '1':
            plot_name = input("Enter plot name for plot: ")
            plot =  plot_manager.create_or_update_plot(entity_instance, plot_name, x_data_key='strain', y_data_key='stress', plot_type='line', element_label='stress vs strain')
            plot_manager.create_or_update_plot(entity_instance, plot=plot, x_data_key='displacement', y_data_key='force', plot_type='line') 
            plot_manager.create_or_update_plot(entity_instance, plot=plot, data_key='strength', plot_type='scatter')  
            ax = plot.axes['main']
            ax.set_title("Mixed Plot")  
            print(f"Plot '{plot_name}' created! Polt has these elements: {plot_manager.list_plot_elements(plot_name)}")
            
            plotted_strength = plot_manager.get_plot_elements_data(plot_name,'strength')
            print(f"Plotted strength data is {plotted_strength}")
            
            plotte_stress = plot_manager.get_plot_elements_data(plot_name,'stress vs strain')
            print(f"Plotted stress vs strain data is {plotte_stress}")
            
            print(ax.lines)
       
        elif choice == '2':
            plot_name = input("Enter plot name for scatter plot: ") 
            plot = plot_manager.create_or_update_plot(entity_instance, plot_name= plot_name, data_key='strength', plot_type='scatter')  
            ax = plot.axes['main']
            ax.set_title("Scatter Plot")
            print(f"Scatter plot '{plot_name}' created!")
            
            updated_strength = Coordinate(10, 10)
            v_shifted_data = plot_manager.save_shifted_data_to_entity(entity_instance, 'strength', updated_strength.x, updated_strength.y)
            old_strength = getattr(entity_instance, 'Orignal_strength')
            print(f"Updated strength data saved to entity was {v_shifted_data}. The new strength data is {entity_instance.strength} and the old is {old_strength}.")
            
        elif choice == '3':
            plt.show()
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please select a valid option.")
            
def gui_frontend():
    plot_manager = PlotManager()

    def plot_line():
        x_data = np.linspace(0, 10, 100)
        y_data = np.sin(x_data) + random.uniform(-0.5, 0.5)
        fig, ax = plot_manager.create_or_update_plot("line_plot", x_data, y_data, plot_type='line')
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def plot_scatter():
        x_data = np.linspace(0, 10, 100)
        y_data = np.random.rand(100)
        fig, ax = plot_manager.create_or_update_plot("scatter_plot", x_data, y_data, plot_type='scatter')
        ax.set_title("Scatter Plot")
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    root = Tk()
    root.title("Dummy GUI for PlotManager Testing")

    frame = Frame(root)
    frame.pack()

    btn_line = Button(root, text="Plot Line", command=plot_line)
    btn_line.pack()

    btn_scatter = Button(root, text="Plot Scatter", command=plot_scatter)
    btn_scatter.pack()

                

if __name__ == "__main__":
    import numpy as np
    import random
    from tkinter import Tk, Frame, Button
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    
    cli_frontend()
    
    
   