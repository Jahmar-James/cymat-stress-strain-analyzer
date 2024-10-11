from typing import Optional, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

from .plot_data import (
    AnnotationData,
    Coordinate,
    HorizontalLineData,
    ImageAnnotation,
    PlotData,
    PlotElement,
    ShadedRegionData,
    TextData,
    VerticalLineData,
    ZoomAnnotation,
)
from .plot_utils import load_and_resize_image, update_style_for_plot_object


class PlotState:
    def __init__(self):
        # axis_label -> {element_label: PlotElement}
        self.elements: dict[str, PlotElement] = {}

    def get_element_data_from_plot(self, element_label: str) -> Union[tuple[pd.Series, pd.Series], Coordinate]:
        """
        NOT Needed - if memory becomes an issue, we can use this to get data from the plot
        and remove x and y datd from plot element
        """
        if element_label not in self.elements:
            raise ValueError(f"Cannot get data for element '{element_label}'. Element does not exist.")
        element = self.elements[element_label]
        plot_obj = element.plot_obj
        plot_type = element.plot_type
        try:
            if plot_type in ["line", "scatter", "fill_between", "histogram"]:
                return PlotState.extract_plot_data_from_artist(plot_obj)
            elif plot_type in ["text", "annotation"]:
                return PlotState.extract_annotation_from_artist(plot_obj)
        except Exception as e:
            raise ValueError(f"Cannot extract data from plot element '{element_label}'. {str(e)}")

    @staticmethod
    def extract_from_artist(
        plot_obj: plt.Artist,
        mode: str = "auto",  # "data", "annotation", or "auto"
    ) -> Union[PlotData, TextData, AnnotationData, HorizontalLineData, VerticalLineData, ShadedRegionData, dict, None]:
        """
        Extracts either data or annotation from a matplotlib plot object based on the mode.
        Returns:
            - A dataclass representing the extracted data or annotation.
            - None if the plot object type or mode is not recognized.
        """
        # Check if we should force a specific extraction mode
        if mode == "data":
            return PlotState.extract_plot_data_from_artist(plot_obj)
        elif mode == "annotation":
            return PlotState.extract_annotation_from_artist(plot_obj)

        # Auto mode: try to determine if it's data or annotation
        # Order matters: if an object can be both, "data" check should come first
        data = PlotState.extract_plot_data_from_artist(plot_obj)
        if data is not None:
            return data

        annotation = PlotState.extract_annotation_from_artist(plot_obj)
        return annotation  # Can be None if not an annotation type

    @staticmethod
    def extract_plot_data_from_artist(plot_obj: plt.Artist) -> Optional[Union[PlotData, dict]]:
        # Line2D for line plots
        if isinstance(plot_obj, plt.Line2D):
            label = plot_obj.get_label()
            return PlotData(
                x_data=pd.Series(plot_obj.get_xdata(), name=f"{label}_x_data"),
                y_data=pd.Series(plot_obj.get_ydata(), name=f"{label}_y_data"),
            )

        # PathCollection for scatter plots
        elif isinstance(plot_obj, mpl.collections.PathCollection):
            label = plot_obj.get_label()
            offsets = plot_obj.get_offsets()
            return PlotData(
                x_data=pd.Series(offsets[:, 0], name=f"{label}_x_data"),
                y_data=pd.Series(offsets[:, 1], name=f"{label}_y_data"),
            )

        # PolyCollection for fill_between plots
        elif isinstance(plot_obj, mpl.collections.PolyCollection):
            paths = plot_obj.get_paths()
            vertices = paths[0].vertices
            return PlotData(
                x_data=pd.Series(vertices[:, 0], name="x_data"), y_data=pd.Series(vertices[:, 1], name="y_data")
            )

        # BarContainer for bar plots and histograms
        elif isinstance(plot_obj, mpl.container.BarContainer):
            rects = plot_obj.patches  # The actual bars (Rectangle objects)
            x_data = [rect.get_x() + rect.get_width() / 2 for rect in rects]  # X is the bar center
            y_data = [rect.get_height() for rect in rects]  # Y is the height of the bar
            return PlotData(x_data=pd.Series(x_data, name="x_data"), y_data=pd.Series(y_data, name="y_data"))
        # AxesImage for heatmaps
        elif isinstance(plot_obj, mpl.image.AxesImage):
            data_array = plot_obj.get_array().data
            return {"data_matrix": pd.Series(data_array.flatten(), name="data_matrix")}

        # QuadMesh for pcolormesh
        elif isinstance(plot_obj, mpl.collections.QuadMesh):
            data_array = plot_obj.get_array()
            clim = plot_obj.get_clim()  # Get color limits
            return {
                "grid_data": pd.Series(data_array.flatten(), name="grid_data"),
                "color_limits": pd.Series(clim, name="color_limits"),
            }

        # QuadContourSet for contour plots
        elif isinstance(plot_obj, mpl.contour.QuadContourSet):
            levels = plot_obj.levels

            contour_segments = plot_obj.allsegs  # List of arrays, one per contour level
            x_coords = []
            y_coords = []
            level_list = []
            for level, segments in zip(levels, contour_segments):
                for segment in segments:
                    x_coords.append(pd.Series(segment[:, 0], name="x_coords"))
                    y_coords.append(pd.Series(segment[:, 1], name="y_coords"))
                    level_list.append(level)
            return {
                "levels": pd.Series(levels, name="levels"),
                "x_data": pd.Series(x_coords, name="x_coords"),
                "y_data": pd.Series(y_coords, name="y_coords"),
            }
        else:
            return None

    @staticmethod
    def extract_annotation_from_artist(
        plot_obj: plt.Artist,
    ) -> Optional[Union[TextData, AnnotationData, HorizontalLineData, VerticalLineData, ShadedRegionData]]:
        if isinstance(plot_obj, plt.Text):
            return TextData(
                x=plot_obj.get_position()[0],
                y=plot_obj.get_position()[1],
                text=plot_obj.get_text(),
                fontsize=plot_obj.get_fontsize(),
            )
        elif isinstance(plot_obj, plt.Annotation):
            return AnnotationData(
                x=plot_obj.xy[0],
                y=plot_obj.xy[1],
                text_x=plot_obj.xytext[0],
                text_y=plot_obj.xytext[1],
                text=plot_obj.get_text(),
                arrowprops=plot_obj.arrowprops,
            )
        elif isinstance(plot_obj, plt.Line2D) and "horizontal" in plot_obj.get_label().lower():
            return HorizontalLineData(
                y=plot_obj.get_ydata()[0], color=plot_obj.get_color(), linestyle=plot_obj.get_linestyle()
            )
        elif isinstance(plot_obj, plt.Line2D) and "vertical" in plot_obj.get_label().lower():
            return VerticalLineData(
                x=plot_obj.get_xdata()[0], color=plot_obj.get_color(), linestyle=plot_obj.get_linestyle()
            )
        elif isinstance(plot_obj, mpl.collections.PolyCollection):
            paths = plot_obj.get_paths()
            vertices = paths[0].vertices
            x1, x2 = vertices[0, 0], vertices[-1, 0]
            return ShadedRegionData(x1=x1, x2=x2, color=plot_obj.get_facecolor()[0], alpha=plot_obj.get_alpha())
        elif isinstance(plot_obj, mpl.image.AxesImage):
            return ImageAnnotation(
                cmap=plot_obj.get_cmap().name if plot_obj.get_cmap() else None,
                interpolation=plot_obj.get_interpolation(),
                alpha=plot_obj.get_alpha(),
            )
        else:
            return None

    def get_plot_element_style(self, element_label: str) -> dict:
        """
        Retrieves the current style of the plot element with the given label.
        """
        if element_label not in self.elements:
            raise ValueError(f"Cannot get style for element '{element_label}'. Element does not exist.")
        element = self.elements[element_label]
        plot_obj = element.plot_obj
        style_dict = PlotState._retrieve_style_from_plot_object(plot_obj)
        return style_dict

    @staticmethod
    def _retrieve_style_from_plot_object(plot_obj) -> dict:
        """
        A static method to retrieve the style of a given plot object.
        Returns a dictionary with the style attributes.
        """
        style_dict = {}

        # Handle Line2D objects (used in line plots)
        if isinstance(plot_obj, plt.Line2D):
            style_dict = {
                "color": plot_obj.get_color(),
                "linestyle": plot_obj.get_linestyle(),
                "linewidth": plot_obj.get_linewidth(),
                "alpha": plot_obj.get_alpha(),
                "marker": plot_obj.get_marker(),
                "markerfacecolor": plot_obj.get_markerfacecolor(),
            }

        # Handle PathCollection objects (used in scatter plots)
        elif isinstance(plot_obj, mpl.collections.PathCollection):
            style_dict = {
                "facecolor": plot_obj.get_facecolor(),
                "edgecolor": plot_obj.get_edgecolor(),
                "sizes": plot_obj.get_sizes(),
                "alpha": plot_obj.get_alpha(),
            }

        # Handle BarContainer objects (used in bar plots)
        elif isinstance(plot_obj, mpl.container.BarContainer):
            if plot_obj.patches:
                # Assuming all bars in the container share the same style
                first_bar = plot_obj.patches[0]
                style_dict = {
                    "facecolor": first_bar.get_facecolor(),
                    "edgecolor": first_bar.get_edgecolor(),
                    "linewidth": first_bar.get_linewidth(),
                    "alpha": first_bar.get_alpha(),
                }

        # Handle PolyCollection objects (used in fill_between plots)
        elif isinstance(plot_obj, mpl.collections.PolyCollection):
            style_dict = {
                "facecolor": plot_obj.get_facecolor(),
                "edgecolor": plot_obj.get_edgecolor(),
                "alpha": plot_obj.get_alpha(),
            }

        # Handle AxesImage objects (used for images)
        elif isinstance(plot_obj, mpl.image.AxesImage):
            style_dict = {
                "alpha": plot_obj.get_alpha(),
                "cmap": plot_obj.get_cmap().name if plot_obj.get_cmap() else None,
                "interpolation": plot_obj.get_interpolation(),
            }

        # Handle matplotlib.text.Annotation objects (used for text annotations)
        elif isinstance(plot_obj, mpl.text.Annotation):
            style_dict = {
                "text": plot_obj.get_text(),
                "xy": plot_obj.xy,
                "arrowprops": plot_obj.arrowprops,
                "color": plot_obj.get_color(),
                "fontsize": plot_obj.get_fontsize(),
                "rotation": plot_obj.get_rotation(),
            }

        # Handle matplotlib.text.Text objects (used for text labels)
        elif isinstance(plot_obj, plt.Text):
            x, y = plot_obj.get_position()
            style_dict = {
                "text": plot_obj.get_text(),
                "x": x,
                "y": y,
                "fontsize": plot_obj.get_fontsize(),
                "color": plot_obj.get_color(),
            }

        else:
            raise ValueError(f"'_retrieve_style_from_plot_object' does not support plot object type: {type(plot_obj)}")

        return style_dict

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

    def update_plot_element_style(
        self,
        element_label: str,
        style: Optional[str] = None,
        color: Optional[str] = None,
        alpha: Optional[float] = None,
        linestyle: Optional[str] = None,
        linewidth: Optional[float] = None,
        **kwargs,
    ) -> bool:
        # TODO make sure the the legend is updated too
        if element_label not in self.elements:
            raise ValueError(f"Cannot update style for element '{element_label}'. Element does not exist.")
        element = self.elements[element_label]
        element = self.elements[element_label]
        plot_obj = element.plot_obj

        # Call the singledispatch function for the specific plot object type
        try:
            plot_obj = update_style_for_plot_object(plot_obj, style, color, alpha, linestyle, linewidth, **kwargs)
            # if plot_obj:
            # element.plot_obj = plot_obj
            # I am not sure is I need to update the object or if the object is updated in place from update_style_for_plot_object
            # which would me the plot_obj in the element is the same as the obj on the figure
            return True
        except Exception as e:
            raise ValueError(f"Error updating style for element '{element_label}': {e}")

    def hide_legend(self) -> bool:
        for element in self.elements.values():
            element.plot_obj.set_label("_nolegend_")
        return True

    def show_legend(self) -> bool:
        for element in self.elements.values():
            element.plot_obj.set_label(element.element_label)
        return True

    def add_horizontal_line(
        self, ax: plt.Axes, line_data: HorizontalLineData, element_label: str = "horizontal_line"
    ) -> bool:
        if element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"

        # Line2D object
        line = ax.axhline(y=line_data.y, color=line_data.color, linestyle=line_data.linestyle, label=element_label)
        plot_element = PlotElement(line, entity_name="annotation", element_label=element_label, ax=ax)
        self.elements[element_label] = plot_element
        return True

    def add_vertical_line(
        self, ax: plt.Axes, line_data: VerticalLineData, element_label: str = "vertical_line"
    ) -> bool:
        if element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"

        # Line2D object
        line = ax.axvline(x=line_data.x, color=line_data.color, linestyle=line_data.linestyle, label=element_label)
        plot_element = PlotElement(line, entity_name="annotation", element_label=element_label, ax=ax)
        self.elements[element_label] = plot_element
        return True

    def add_shaded_region(
        self, ax: plt.Axes, region_data: ShadedRegionData, element_label: str = "shaded_region"
    ) -> bool:
        if element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"

        # PolyCollection object
        region = ax.fill_betweenx(
            ax.get_ylim(),
            region_data.x1,
            region_data.x2,
            color=region_data.color,
            alpha=region_data.alpha,
            label=element_label,
        )
        plot_element = PlotElement(region, entity_name="annotation", element_label=element_label, ax=ax)
        self.elements[element_label] = plot_element
        return True

    def add_text_annotation(self, ax: plt.Axes, text_data: TextData, element_label: str = "text_annotation") -> bool:
        if element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"

        # Text object
        text = ax.text(text_data.x, text_data.y, text_data.text, fontsize=text_data.fontsize, label=element_label)
        plot_element = PlotElement(text, entity_name="annotation", element_label=element_label, ax=ax)
        self.elements[element_label] = plot_element
        return True

    def add_arrow(self, ax: plt.Axes, annotation_data: AnnotationData, element_label: str = "arrow") -> bool:
        if element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"

        # Annotation object
        arrow = ax.annotate(
            annotation_data.text,
            xy=(annotation_data.x, annotation_data.y),
            xytext=(annotation_data.text_x, annotation_data.text_y),
            arrowprops=annotation_data.arrowprops or {"facecolor": "black", "shrink": 0.05},
            label=element_label,
        )
        plot_element = PlotElement(arrow, entity_name="annotation", element_label=element_label, ax=ax)
        self.elements[element_label] = plot_element
        return True

    def add_image(self, ax: plt.Axes, annotation_data: ImageAnnotation, element_label: str = "image") -> bool:
        if "image" in element_label and element_label in self.elements:
            element_label = f"{element_label}_{len(self.elements)}"
        # AxesImage object
        plot_element = self.create_image_on_axes(ax, annotation_data.image_path, element_label=element_label)
        self.elements[element_label] = plot_element
        return True

    @staticmethod
    def create_image_on_axes(
        ax: plt.Axes,
        image_path: str,
        resize_factor: Optional[float] = None,
        area_fraction: Optional[float] = 0.05,  # Fraction of the figure area the image should occupy
        position: str = "inside",  # "inside" or "outside"
        element_label: str = "image",
    ) -> ["PlotElement"]:
        # Load the image and resize it

        img_array = load_and_resize_image(image_path, ax, resize_factor, area_fraction)

        # Add image inside the axes (part of the plot)
        if position == "inside":
            plot_obj = ax.imshow(img_array, aspect="auto", zorder=1, alpha=1, label=element_label)
            return PlotElement(plot_obj, entity_name="annotation", element_label=element_label, ax=ax)
        # Add image outside the axes (like a logo) using inset_axes
        elif position == "outside":
            axins = inset_axes(
                ax,
                width="10%",
                height="10%",
                loc="upper left",
                bbox_to_anchor=(-0.16, 0.1, 1, 1),
                bbox_transform=ax.transAxes,
                borderpad=0,
            )
            axins.imshow(img_array)
            axins.axis("off")  # Remove axes for the image
            plot_obj = axins

            return PlotElement(plot_obj, entity_name="annotation", element_label=element_label, ax=ax)

        else:
            raise ValueError(f"Unsupported position '{position}'. Use 'inside' or 'outside'.")

    def add_zoom_inset(
        self,
        ax: plt.Axes,
        annotation_data: ZoomAnnotation,
        element_label: str = "zoom_inset",
        mark_zoom: bool = True,
        bbox_to_anchor: tuple[float, float, float, float] = None,
    ) -> bool:
        """Statful method to add a zoomed-in inset to the plot.
        Automatically updates the plot state with the new zoom element.
        """
        # Use the static method to create the zoom element
        zoom_element = PlotState.create_zoom_element(
            ax,
            annotation_data.xlim,
            annotation_data.ylim,
            annotation_data.position,
            annotation_data.fraction,
            mark_zoom,
            element_label,
            bbox_to_anchor,
        )

        # Add the zoom element to the plot state for future reference
        self.elements[element_label] = zoom_element
        return True

    @staticmethod
    def create_zoom_element(
        ax: plt.Axes,
        xlim: tuple[float, float],
        ylim: tuple[float, float],
        zoom_position: str = "upper right",
        zoom_fraction: float = 0.2,
        mark_zoom: bool = True,
        element_label: str = "zoom_inset",
        bbox_to_anchor: tuple[float, float, float, float] = None,
    ) -> PlotElement:
        """
        Creates a zoomed-in element (axes) in the main plot. Does not directly modify PlotState.

        Args:
            ax (plt.Axes): The main axes to add the zoom inset to.
            xlim (tuple): The x-axis limits for the zoomed region.
            ylim (tuple): The y-axis limits for the zoomed region.
            zoom_position (str): Where to place the zoom inset ('upper right', 'upper left', etc.).
            zoom_fraction (float): Fraction of the figure the zoom inset will occupy.
            mark_zoom (bool): Whether to mark the zoomed region in the main plot.
            element_label (str): Label for the zoomed inset element.
            bbox_to_anchor (tuple): Fine control for inset box placement (optional).

        Returns:
            PlotElement: The created zoom element, ready to be added to the plot state.
        """
        # Create the inset axes
        if bbox_to_anchor:
            axins = inset_axes(
                ax,
                width=f"{zoom_fraction * 100}%",
                height=f"{zoom_fraction * 100}%",
                bbox_to_anchor=bbox_to_anchor,
                bbox_transform=ax.transAxes,
                loc="upper left",
            )
        else:
            axins = inset_axes(ax, width=f"{zoom_fraction * 100}%", height=f"{zoom_fraction * 100}%", loc=zoom_position)

        # Set the zoomed-in limits for the inset plot
        axins.set_xlim(xlim)
        axins.set_ylim(ylim)

        # Optionally mark the zoom region with lines on the main plot
        if mark_zoom:
            mark_inset(ax, axins, loc1=2, loc2=4, fc="none", ec="0.5")

        # Copy the data from the main plot to the inset
        for line in ax.get_lines():
            axins.plot(line.get_xdata(), line.get_ydata(), label=line.get_label(), color=line.get_color())

        # Hide tick labels to keep the inset clean
        axins.set_xticklabels([])
        axins.set_yticklabels([])

        # Create and return a PlotElement for the zoom inset
        zoom_element = PlotElement(plot_obj=axins, entity_name="zoom_inset", element_label=element_label, ax=axins)
        return zoom_element
