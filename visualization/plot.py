from typing import TYPE_CHECKING, Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

from visualization.plot_config import PlotConfig

from .plot_data import PlotElement
from .plot_state import PlotState

if TYPE_CHECKING:
    from .plot_data import AnnotationData, TextData


class Plot:
    def __init__(
        self,
        name: str,
        plot_type: str,
        plot_config: Optional["PlotConfig"] = None,
        plot_state: Optional["PlotState"] = None,
        fig: Optional[plt.Figure] = None,
        axes: Optional[dict[str, plt.Axes]] = None,
        style: Optional[str] = None,
    ):
        # Initialize
        self.name = name
        self.plot_type = plot_type
        self.default_plot_config = PlotConfig(
            title=None, xlabel=None, ylabel=None, figsize=(8, 6), line_style="-", color=None, alpha=1.0, grid=True
        )
        self.plot_config: PlotConfig = plot_config or self.default_plot_config

        # Don't create the state yet
        self.plot_state = plot_state or PlotState()
        self.fig = fig
        self.axes = axes
        self.style = style

    def add_plot_element(
        self,
        entity_name: str,
        x_data: pd.Series,
        y_data: pd.Series,
        element_label: str,
        plot_config: Optional["PlotConfig"] = None,
        axes_key: Optional[str] = None,
        text: Optional["TextData"] = None,
        annotation: Optional["AnnotationData"] = None,
    ) -> tuple[plt.Figure, plt.Axes]:
        if element_label in self.plot_state.elements:
            raise ValueError(
                f"Cannot add plot element. Element '{element_label}' already exists in plot '{self.name}'."
            )

        fig, ax = self._get_or_create_axes_and_fig(axes_key)
        fig.sca(ax)  # Set the current Axes to the one we want to plot on

        # Different plot functions based on the plot type
        plot_artist = self._add_plot_artist(
            ax, self.plot_type, x_data, y_data, element_label, text=text, annotation_data=annotation
        )

        plot_element = PlotElement(
            plot_obj=plot_artist,
            entity_name=entity_name,
            element_label=element_label,
            ax=ax,
            x_data=x_data,
            y_data=y_data,
            plot_type=self.plot_type,
            annotation_data=text or annotation,
        )
        self.plot_state.elements[element_label] = plot_element
        plot_config = plot_config or self.plot_config
        ax = self._apply_plot_config(ax, plot_config)
        return fig, ax

    def _get_or_create_axes_and_fig(self, ax_key: Optional[str] = None) -> tuple[plt.Figure, plt.Axes]:
        # Inital State, No figure or axes
        if self.fig is None or self.axes is None:
            self.fig, axes = plt.subplots(
                nrows=self.plot_config.nrows, ncols=self.plot_config.ncols, figsize=self.plot_config.figsize
            )
            # Store the axes in a dictionary for easy access
            if self.plot_config.ncols > 1 or self.plot_config.nrows > 1:
                self.axes = {f"ax_{i}": ax for i, ax in enumerate(axes.flatten())}
            else:
                # If single axis, store it as 'main'
                self.axes = {"main": axes}
            # Might not need to apply the plot config here
            # as applied at end of add_plot_element FUNC
            for ax in self.axes.values():
                ax = self._apply_plot_config(ax, self.plot_config)

        # After the initial state, we can return the existing figure and axes
        if len(self.axes) == 1:
            return self.fig, self.axes["main"]

        if ax_key is not None:
            if ax_key in self.axes:
                return self.fig, self.axes[ax_key]
            else:
                raise ValueError(f"Axis key '{ax_key}' does not exist in the plot '{self.name}'.")

        return self.fig, self.axes["main"]

    @staticmethod
    def _apply_plot_config(ax: plt.Axes, plot_config: "PlotConfig") -> plt.Axes:
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
            ax.axhline(0, color="black", linestyle="--")
            ax.axvline(0, color="black", linestyle="--")
        if plot_config.x_percent:
            ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
        if plot_config.x_rotation is not None:
            ax.tick_params(axis="x", rotation=plot_config.x_rotation)
        if plot_config.x_minor_locator is not None:
            ax.xaxis.set_minor_locator(mtick.AutoMinorLocator(plot_config.x_minor_locator))
        if plot_config.y_minor_locator is not None:
            ax.yaxis.set_minor_locator(mtick.AutoMinorLocator(plot_config.y_minor_locator))
        if plot_config.legend_position:
            ax.legend(loc=plot_config.legend_position)
        return ax

    def add_axis_in_direction(self, position: str = "below", share_axes: bool = False) -> tuple[plt.Figure, plt.Axes]:
        existing_axes = self.axes

        if len(existing_axes) != 1:
            raise ValueError("'add_axis_in_direction' can only be used with a single axis.")

        old_ax = self.axes.pop("main")

        if position not in ["below", "above", "right", "left", "top", "bottom"]:
            raise ValueError("Invalid position. Must be 'below', 'above', 'right', or 'left'.")

        if position in ["top", "above"]:
            nrows, ncols = 2, 1
            axes_keys = ["top", "bottom"]
        elif position in ["right", "left"]:
            nrows, ncols = 1, 2
            axes_keys = ["left", "right"]

        figsize = self.plot_config.figsize

        # Create a new figure and add subplots based on direction

        if position == "left":
            fig, (new_ax, old_ax_new) = plt.subplots(
                nrows, ncols, gridspec_kw={"width_ratios": [1, 1]}, figsize=figsize
            )
        elif position == "right":
            fig, (old_ax_new, new_ax) = plt.subplots(
                nrows, ncols, gridspec_kw={"width_ratios": [1, 1]}, figsize=figsize
            )
        elif position in ["top", "above"]:
            fig, (new_ax, old_ax_new) = plt.subplots(
                nrows, ncols, gridspec_kw={"height_ratios": [1, 1]}, figsize=figsize
            )
        elif position in ["bottom", "below"]:
            fig, (old_ax_new, new_ax) = plt.subplots(
                nrows, ncols, gridspec_kw={"height_ratios": [1, 1]}, figsize=figsize
            )
        else:
            raise ValueError(f"Invalid direction '{position}'. Must be 'left', 'right', 'top', or 'bottom'.")

        for element_label, plot_element in self.plot_state.elements.items():
            if plot_element.ax == old_ax:
                self._transfer_plot_element_to_new_axes(plot_element, new_ax, self.plot_state, None)

        # Update the plot state with the new axes
        self.fig = fig  # Replace the old figure with the new one
        self.axes = {axes_keys[0]: new_ax, axes_keys[1]: old_ax_new}
        return fig, new_ax  # Return the new figure and axis

    @staticmethod
    def _add_plot_artist(ax: plt.Axes, plot_type: str, x_data, y_data, element_label: str, **kwargs) -> plt.Artist:
        """Static helper function to add plot artist based on the plot type."""
        if plot_type == "line":
            lines = ax.plot(x_data, y_data, label=element_label)
            return lines[0]  # LinencolsD object, usually first item
        elif plot_type == "scatter":
            return ax.scatter(x_data, y_data, label=element_label)  # PathCollection object
        elif plot_type == "fill_between":
            return ax.fill_between(x_data, y_data, label=element_label)  # PolyCollection object
        elif plot_type == "histogram":
            # For histogram, we return the third element, which are the Patch objects (bars)
            n, bins, patches = ax.hist(y_data, label=element_label)
            return patches  # Return patches (bars)
        elif plot_type == "text":
            # Expecting TextData object passed via kwargs
            text_data: TextData = kwargs["text_data"]
            return ax.text(text_data.x, text_data.y, text_data.text, fontsize=text_data.fontsize)
        elif plot_type == "annotation":
            # Expecting AnnotationData object passed via kwargs
            annotation_data: AnnotationData = kwargs["annotation_data"]
            return ax.annotate(
                annotation_data.text,
                xy=(annotation_data.x, annotation_data.y),
                xytext=(annotation_data.text_x, annotation_data.text_y),
                arrowprops=annotation_data.arrowprops or {"facecolor": "black", "shrink": 0.05},
            )
        else:
            raise ValueError(f"Invalid plot type '{plot_type}'.")

    @staticmethod
    def _transfer_plot_element_to_new_axes(
        plot_element: PlotElement, new_ax: plt.Axes, old_plot_state: "PlotState", new_plot_state: Optional["PlotState"]
    ) -> None:
        """Static helper function to transfer a plot element to a new axes."""
        if plot_element not in old_plot_state.elements.values():
            raise ValueError("Cannot transfer plot element. Element does not exist in the plot state.")

        # If new plot state is not provided, then transfer the element within the same plot
        # Must remove the element + element_label from the old plot state
        if new_plot_state is None:
            old_plot_element = old_plot_state.elements.pop(plot_element.element_label, None)
            x_data, y_data = old_plot_element.x_data, old_plot_element.y_data
            x_data_plot, y_data_plot = old_plot_state.get_element_data_from_plot(plot_element.element_label)
            if x_data != x_data_plot or y_data != y_data_plot:
                raise ValueError("Data mismatch between plot element and plot state.")

        plot_artist = plot_element.plot_obj

        if isinstance(plot_artist, plt.Line2D):
            new_plot_obj = new_ax.plot(x_data, y_data, label=plot_element.element_label)
        elif isinstance(plot_artist, mpl.collections.PathCollection):
            new_plot_obj = new_ax.scatter(
                x_data,
                y_data,
                label=plot_element.element_label,
            )
        elif isinstance(plot_artist, mpl.container.BarContainer):
            new_plot_obj = new_ax.fill_between(x_data, y_data, label=plot_element.element_label)
        elif isinstance(plot_artist, plt.Text):
            new_plot_obj = new_ax.text(x_data, y_data, plot_artist.get_text())
        elif isinstance(plot_artist, plt.Annotation):
            annotation = plot_artist
            new_plot_obj = new_ax.annotate(
                annotation.get_text(), xy=annotation.xy, xytext=annotation.xytext, arrowprops=annotation.arrowprops
            )
        else:
            raise ValueError(f"Unsupported plot element type: {type(plot_artist)}")

        new_plot_element = PlotElement(
            plot_obj=new_plot_obj,
            entity_name=plot_element.entity_name,
            element_label=plot_element.element_label,
            ax=new_ax,
            x_data=plot_element.x_data,
            y_data=plot_element.y_data,
            plot_type=plot_element.plot_type,
            annotation_data=plot_element.annotation_data,
        )
        if new_plot_state is not None:
            new_plot_state.elements[plot_element.element_label] = new_plot_element
        else:
            old_plot_state.elements[plot_element.element_label] = new_plot_element
        return new_plot_element
