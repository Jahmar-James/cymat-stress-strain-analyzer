from functools import singledispatch
from typing import Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import PIL
from matplotlib.collections import (  # For scatter and fill_between plots
    PathCollection,
    PolyCollection,
)
from matplotlib.container import BarContainer  # For bar and histogram plots
from matplotlib.contour import QuadContourSet  # For contour plots
from matplotlib.image import AxesImage  # For images (imshow)
from matplotlib.lines import Line2D  # For line plots

# BEGIN update_style_for_plot_object DISPATCHER


@singledispatch
def update_style_for_plot_object(
    plot_obj,
    style: Optional[str] = None,
    color: Optional[str] = None,
    alpha: Optional[float] = None,
    linestyle: Optional[str] = None,
    linewidth: Optional[float] = None,
    **kwargs,
) -> Optional[plt.Artist]:
    """
    Default function for updating the style of a plot object.
    This is the fallback function and raises an error if the object type is unsupported.
    """
    raise NotImplementedError(f"Unsupported plot object type: {type(plot_obj)}")


@update_style_for_plot_object.register
def _(plot_obj: plt.Line2D, style, color, alpha, linestyle, linewidth, **kwargs):
    """Handle Line2D objects (e.g., line plots)."""
    if color:
        plot_obj.set_color(color)
    if alpha:
        plot_obj.set_alpha(alpha)
    if linestyle:
        plot_obj.set_linestyle(linestyle)
    if linewidth:
        plot_obj.set_linewidth(linewidth)

    # Apply any additional styles via kwargs
    for key, value in kwargs.items():
        if hasattr(plot_obj, f"set_{key}"):
            getattr(plot_obj, f"set_{key}")(value)

    return plot_obj


@update_style_for_plot_object.register
def _(plot_obj: PathCollection, style, color, alpha, linestyle, linewidth, **kwargs):
    """Handle PathCollection objects (e.g., scatter plots)."""
    if color:
        plot_obj.set_facecolor(color)
    if alpha:
        plot_obj.set_alpha(alpha)

    # Apply additional styles via kwargs
    for key, value in kwargs.items():
        if hasattr(plot_obj, f"set_{key}"):
            getattr(plot_obj, f"set_{key}")(value)

    return plot_obj


@update_style_for_plot_object.register
def _(plot_obj: BarContainer, style, color, alpha, linestyle, linewidth, **kwargs):
    """Handle BarContainer objects (e.g., bar plots)."""
    for bar in plot_obj.patches:
        if color:
            bar.set_facecolor(color)
        if alpha:
            bar.set_alpha(alpha)
        if linewidth:
            bar.set_linewidth(linewidth)

    return plot_obj


@update_style_for_plot_object.register
def _(plot_obj: PolyCollection, style, color, alpha, linestyle, linewidth, **kwargs):
    """Handle PolyCollection objects (e.g., fill_between plots)."""
    if color:
        plot_obj.set_facecolor(color)
    if alpha:
        plot_obj.set_alpha(alpha)

    return plot_obj


@update_style_for_plot_object.register
def _(plot_obj: AxesImage, style, color, alpha, linestyle, linewidth, **kwargs):
    """Handle AxesImage objects (e.g., images)."""
    if alpha:
        plot_obj.set_alpha(alpha)
    if "cmap" in kwargs:
        plot_obj.set_cmap(kwargs["cmap"])

    return plot_obj


@update_style_for_plot_object.register
def _(plot_obj: mpl.text.Text, style, color, alpha, linestyle, linewidth, **kwargs):
    """Handle Text objects (e.g., titles, labels)."""
    if color:
        plot_obj.set_color(color)
    if "fontsize" in kwargs:
        plot_obj.set_fontsize(kwargs["fontsize"])
    if "fontweight" in kwargs:
        plot_obj.set_fontweight(kwargs["fontweight"])

        for key, value in kwargs.items():
            if hasattr(plot_obj, f"set_{key}"):
                getattr(plot_obj, f"set_{key}")(value)

    return plot_obj


@update_style_for_plot_object.register
def _(plot_obj: mpl.text.Annotation, style, color, alpha, linestyle, linewidth, **kwargs):
    """Handle Annotation objects (e.g., text annotations)."""
    if color:
        plot_obj.set_color(color)
    if "fontsize" in kwargs:
        plot_obj.set_fontsize(kwargs["fontsize"])
    if "fontweight" in kwargs:
        plot_obj.set_fontweight(kwargs["fontweight"])

        for key, value in kwargs.items():
            if hasattr(plot_obj, f"set_{key}"):
                getattr(plot_obj, f"set_{key}")(value)

    return plot_obj


# END update_style_for_plot_object DISPATCHER

# Image Resizer - Mainly for logos on plots


def load_and_resize_image(
    image_path: str, ax: plt.Axes, resize_factor: Optional[float] = None, area_fraction: Optional[float] = 0.05
) -> np.ndarray:
    """
    Loads and resizes an image either by a factor or based on a fraction of the plot area.
    """
    original_image = PIL.Image.open(image_path)

    if resize_factor is not None:
        return resize_image_by_factor(original_image, resize_factor)
    else:
        return resize_image_by_area(original_image, ax, area_fraction)


def resize_image_by_area(image: "PIL.Image", ax: plt.Axes, area_fraction: float) -> np.ndarray:
    """
    Resize the image based on a fraction of the figure's area.
    """
    # Calculate figure area
    figure_area = ax.figure.bbox.width * ax.figure.bbox.height
    target_area = figure_area * area_fraction

    # Get original dimensions and scaling factor
    orig_width, orig_height = image.size
    scaling_factor = (target_area / (orig_width * orig_height)) ** 0.5

    # Resize the image
    new_width = int(orig_width * scaling_factor)
    new_height = int(orig_height * scaling_factor)
    resized_image = image.resize((new_width, new_height), PIL.Image.LANCZOS)

    # Convert to NumPy array for matplotlib
    return np.asarray(resized_image)


def resize_image_by_factor(image: "PIL.Image", resize_factor: float) -> np.ndarray:
    """
    Resize the image by a given factor.
    """
    orig_width, orig_height = image.size
    new_width = int(orig_width * resize_factor)
    new_height = int(orig_height * resize_factor)
    resized_image = image.resize((new_width, new_height), PIL.LANCZOS)

    return np.asarray(resized_image)
