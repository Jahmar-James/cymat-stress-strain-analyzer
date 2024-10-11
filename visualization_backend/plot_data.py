from dataclasses import dataclass
from typing import Optional, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

# Data classes for Structure the objects added to the plot class


@dataclass(frozen=True)
class PlotElement:
    plot_obj: Union[
        plt.Line2D,  # For line plots and axhline/axvline
        mpl.collections.PathCollection,  # For scatter plots
        mpl.container.BarContainer,  # For bar plots and histograms
        mpl.collections.PolyCollection,  # For area plots (fill_between)
        mpl.image.AxesImage,  # For heatmaps
        mpl.contour.QuadContourSet,  # For contour plots
        plt.Text,  # For text annotations
        plt.Annotation,
    ]  # For annotated arrows
    entity_name: str  # The name of the entity that provided the data
    element_label: str  # The name of the entity's property being plotted
    ax: plt.Axes  # The axis on which the plot is drawn
    # Additional parameters that can be removed if memory becomes an issue
    x_data: Optional[pd.Series] = None  # The x data for the plot element
    y_data: Optional[pd.Series] = None  # The y data for the plot element
    plot_type: Optional[str] = None  # The type of plot element (line, scatter, bar, etc.)
    annotation_data: Optional[dict[str, Union["TextData", "AnnotationData"]]] = None


# Data classes for plotted Data


@dataclass
class Coordinate:
    x: float
    y: float


@dataclass
class PlotData:
    x_data: pd.Series
    y_data: pd.Series


# Annotation data classes


@dataclass
class TextData:
    x: float  # x-coordinate for the text
    y: float  # y-coordinate for the text
    text: str  # Actual text content
    fontsize: int = 12  # Optional fontsize (default: 12)


@dataclass
class AnnotationData:
    x: float  # x-coordinate of the point to annotate
    y: float  # y-coordinate of the point to annotate
    text_x: float  # x-coordinate where the text will appear
    text_y: float  # y-coordinate where the text will appear
    text: str  # Annotation text
    arrowprops: dict = None  # Optional: arrow properties, default can be set in the add function


@dataclass
class HorizontalLineData:
    y: float
    color: str = "black"
    linestyle: str = "--"


@dataclass
class VerticalLineData:
    x: float
    color: str = "black"
    linestyle: str = "--"


@dataclass
class ShadedRegionData:
    x1: float
    x2: float
    color: str = "gray"
    alpha: float = 0.5


@dataclass
class ImageAnnotation:
    image_path: str
    resize_factor: Optional[float] = None
    area_fraction: Optional[float] = 0.05
    position: str = "inside"
    element_label: str = "image"


@dataclass
class ZoomAnnotation:
    xlim: tuple[float, float]
    ylim: tuple[float, float]
    zoom_position: str = "upper right"
    zoom_fraction: float = 0.2
    element_label: str = "zoom_inset"


# END of Annotation data classes
