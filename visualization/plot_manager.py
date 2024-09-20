import datetime
from typing import TYPE_CHECKING, Optional, Union

import pandas as pd

from .plot import Plot
from .plot_config import PlotConfig
from .plot_data import (
    AnnotationData,
    Coordinate,
    HorizontalLineData,
    ImageAnnotation,
    PlotData,
    ShadedRegionData,
    TextData,
    VerticalLineData,
    ZoomAnnotation,
)

if TYPE_CHECKING:
    from standards.base.analyzable_entity import AnalyzableEntity


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
        self.plots: dict[str, "Plot"] = {}
        self.default_plot_config = PlotConfig()

    def add_entity_to_plot(
        self,
        entity: "AnalyzableEntity",
        plot_name: Optional[str] = None,
        plot: Optional["Plot"] = None,
        x_data_key: Optional[str] = None,
        y_data_key: Optional[str] = None,
        propperty_key: Optional[str] = None,
        element_label: Optional[str] = None,
        plot_config: Optional["PlotConfig"] = None,
        plot_type: str = "custom",
    ) -> Optional["Plot"]:
        plot_config = plot_config or self.default_plot_config
        plot = self._create_plot_if_none(plot, plot_name, plot_type, plot_config)
        x_data, y_data = self._normalize_entity_data_for_plotting(entity, x_data_key, y_data_key, propperty_key)
        element_label = self._generate_element_label(element_label, entity.name, x_data_key, y_data_key, propperty_key)
        susccess_operation = plot.add_plot_element(entity.name, x_data, y_data, element_label, plot_config)

        if susccess_operation:
            return plot
        else:
            return None

    def add_annotation_to_plot(
        self,
        plot_name: str,
        annotation: Union[
            "TextData",
            "AnnotationData",
            "HorizontalLineData",
            "VerticalLineData",
            "ShadedRegionData",
            "ZoomAnnotation",
            "ImageAnnotation",
        ],
        element_label: Optional[str] = None,
        axes_key: Optional[str] = None,
    ) -> Optional["Plot"]:
        if plot_name not in self.plots:
            raise ValueError(
                f"Cannot add annotation to plot '{plot_name}'. Plot does not exist. Data should be added before Annotations. You can create a plot using add_entity_to_plot"
            )
        plot = self.plots[plot_name]
        fig, ax = plot._get_or_create_axes_and_fig(axes_key)
        fig.sca(ax)

        # Generate an element label if not provided
        element_label = element_label or f"{type(annotation).__name__}_{len(plot.plot_state.elements) + 1}"
        if isinstance(annotation, TextData):
            plot.plot_state.add_text_annotation(ax, annotation, element_label)

        elif isinstance(annotation, AnnotationData):
            plot.plot_state.add_arrow(ax, annotation, element_label)

        elif isinstance(annotation, HorizontalLineData):
            plot.plot_state.add_horizontal_line(ax, annotation.y, annotation.color, annotation.linestyle, element_label)

        elif isinstance(annotation, VerticalLineData):
            plot.plot_state.add_vertical_line(ax, annotation.x, annotation.color, annotation.linestyle, element_label)

        elif isinstance(annotation, ShadedRegionData):
            plot.plot_state.add_shaded_region(ax, annotation, element_label)
        elif isinstance(annotation, ImageAnnotation):
            plot.plot_state.add_image(ax, annotation, element_label)
        elif isinstance(annotation, ZoomAnnotation):
            plot.plot_state.add_zoom_inset(ax, annotation, element_label)
        else:
            raise ValueError(f"Unsupported annotation type: {type(annotation)}")
        plot._apply_plot_config(ax, plot.plot_config)
        return plot

    def _create_plot_if_none(
        self, plot: Optional["Plot"], plot_name: Optional[str], plot_type: str, plot_config: "PlotConfig"
    ) -> "Plot":
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
                raise ValueError(
                    f"Entity data '{entity_property_key}' must be a Pandas Series. Use get_entity_property for Coordinate or float."
                )
            return data
        except AttributeError:
            raise AttributeError(f"Entity '{entity.name}' does not have the property '{entity_property_key}'.")

    @staticmethod
    def get_entity_property(entity: "AnalyzableEntity", entity_property_key: str) -> Union[Coordinate, float]:
        try:
            data = getattr(entity, entity_property_key)
            if not isinstance(data, (Coordinate, float, int)):
                raise ValueError(
                    f"Entity property '{entity_property_key}' must be a Coordinate or a float. use get_entity_data for pd.Series"
                )
            return data
        except AttributeError:
            raise AttributeError(f"Entity '{entity.name}' does not have the property '{entity_property_key}'.")

    @staticmethod
    def _normalize_entity_data_for_plotting(
        entity: "AnalyzableEntity", x_data_key: Optional[str], y_data_key: Optional[str], propperty_key: Optional[str]
    ) -> Union[tuple[pd.Series, pd.Series], tuple[float, float]]:
        if propperty_key:
            data = PlotManager.get_entity_property(entity, propperty_key)
            if isinstance(data, Coordinate) and entity.is_sample_group is False:
                return data.x, data.y
            elif isinstance(data, pd.Series) and entity.is_sample_group is True and hasattr(entity, "samples"):
                x_data = list(range(len(entity.samples)))
                y_data = data
                return pd.Series(x_data, name=entity.name), y_data
            else:
                raise ValueError(f"Cannot normalize data for plotting. Invalid data type for '{propperty_key}'.")
        else:
            x_data = PlotManager.get_entity_data(entity, x_data_key)
            y_data = PlotManager.get_entity_data(entity, y_data_key)
            return x_data, y_data

    @staticmethod
    def _generate_element_label(
        element_label: Optional[str],
        entity_name: Optional[str],
        x_data_key: Optional[str],
        y_data_key: Optional[str],
        propperty_key: Optional[str],
    ) -> str:
        if element_label:
            return element_label
        if propperty_key:
            return propperty_key
        if x_data_key and y_data_key and entity_name:
            return f"{entity_name}'s {y_data_key} vs {x_data_key}"
        elif x_data_key and y_data_key:
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
            raise ValueError(f"Cannot list plot elements. Plot '{plot_name}' does not exist.")
        plot = self.plots[plot_name]
        return list(plot.plot_state.elements.keys())

    def list_plot_axes(self, plot_name: str) -> list[str]:
        if plot_name not in self.plots:
            raise ValueError(f"Can not list plot axes. Plot '{plot_name}' does not exist.")
        plot = self.plots[plot_name]
        return list(plot.axes.keys())

    def get_plot_elements_data(
        self, plot_name: str, element_label: str
    ) -> Union[tuple[pd.Series, pd.Series], Coordinate]:
        if plot_name not in self.plots:
            raise ValueError(f"Cannot get data for plot '{plot_name}'. Plot does not exist.")
        plot = self.plots[plot_name]
        return plot.plot_state.get_element_data_from_plot(element_label)

    @staticmethod
    def save_shifted_data_to_entity(
        entity: "AnalyzableEntity",
        property_key: str,
        updated_x_data: Union[pd.Series, float],
        updated_y_data: Union[pd.Series, float],
    ) -> bool:
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
