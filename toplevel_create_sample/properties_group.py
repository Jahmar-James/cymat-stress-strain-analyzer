import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Union

from settings_toplevel_create_sample import ureg

if TYPE_CHECKING:
    from pint import UnitRegistry


class PropertiesGroup(ttk.Frame):
    """Frame to display the properties of the sample live as the user inputs the values in the entry widgets.

    The properties include:
    - Name(Preview) before submission
    - Dimensions (Length x Width x Thickness)
    - Area (Length * Width)
    - Density (Weight / Volume)
    """

    def __init__(self, parent, entries: list, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.entries = entries
        self.trace_vars = {}
        if entries is None:
            return
        self._formatted_entry_values = {}
        self.processor = SamplePropertiesProcessor()

    def create_widgets(self) -> None:
        self.grid_rowconfigure(0, weight=1, uniform="a", minsize=40)
        self.grid_rowconfigure((1, 2, 3), weight=1, uniform="a", minsize=20)
        self.grid_columnconfigure(0, weight=1, uniform="a")

        self.name_label = ttk.Label(self, text="Sample Name:\nPreview", font=("Helvetica", 10, "bold"))
        self.name_label.grid(row=0, column=0, sticky="ew")

        self.dimensions_label = ttk.Label(self, text="Dimensions: 0 x 0 x 0")
        self.dimensions_label.grid(row=1, column=0, sticky="nsew")

        self.area_label = ttk.Label(self, text="Area: 0 mm^2")
        self.area_label.grid(row=2, column=0, sticky="nsew")

        self.density_label = ttk.Label(self, text="Density: 0 g/cm^3")
        self.density_label.grid(row=3, column=0, sticky="nsew")
        self._configure_traces()

    def _configure_traces(self):
        for entry in self.entries:
            var = tk.StringVar(value=entry.placeholder) if entry.placeholder else tk.StringVar()
            entry.config(textvariable=var)
            self.trace_vars[entry] = var
            var.trace_add("write", self._update_properties)

    def _update_properties(self, *args):
        # Extract and convert values from entry widgets
        name = self._update_sample_name()
        length = self.processor.convert_to_quantity(self.entries[1].get(), self.entries[1].unit)
        width = self.processor.convert_to_quantity(self.entries[2].get(), self.entries[2].unit)
        thickness = self.processor.convert_to_quantity(self.entries[3].get(), self.entries[3].unit)
        weight = self.processor.convert_to_quantity(self.entries[4].get(), self.entries[4].unit)

        # Calculate all properties using the processor
        properties = self.processor.calculate_properties(length, width, thickness, weight)

        # Determine color for dimension label based on magnitude
        dim_color = "red" if any(dim.to("m").magnitude > 1 for dim in [length, width, thickness]) else "black"
        density_color = "red" if properties["density"].to("g/cm^3").magnitude > 10 else "black"

        # Update the UI components with new values
        self.name_label.config(text=f"Sample Name:\n{name}")
        self.dimensions_label.config(
            text=f"Dimensions: {length.magnitude:.2f} x {width.magnitude:.2f} x {thickness.magnitude:.2f}",
            foreground=dim_color,
        )
        self.area_label.config(text=f"Area: {properties['area'].magnitude:.2f} mm^2")
        self.density_label.config(
            text=f"Density: {properties['density'].magnitude:.3f} g/cm^3", foreground=density_color
        )

        # Store formatted values for other uses
        self._formatted_entry_values = {
            "name": name,
            "length": length,
            "width": width,
            "thickness": thickness,
            "weight": weight,
            "area": properties["area"],
            "density": properties["density"],
        }

    def _update_sample_name(self):
        name = self.entries[0].get().strip().replace(" ", "_")
        self.name_label.config(text=f"Sample Name:\n{name}")
        return name

    @property
    def formatted_entry_values(self) -> dict:
        return self._formatted_entry_values

    def reset(self) -> None:
        self.name_label.config(text="Sample Name:'\nPreview")
        self.dimensions_label.config(text="Dimensions: 0 x 0 x 0")
        self.area_label.config(text="Area: 0 mm^2")
        self.density_label.config(text="Density: 0 g/cm^3")
        self._formatted_entry_values = {}


class SamplePropertiesProcessor:
    @staticmethod
    def calculate_properties(
        length: Union[float, "UnitRegistry.Quantity"],
        width: Union[float, "UnitRegistry.Quantity"],
        thickness: Union[float, "UnitRegistry.Quantity"],
        weight: Union[float, "UnitRegistry.Quantity"],
    ) -> dict[str, "UnitRegistry.Quantity"]:
        area = SamplePropertiesProcessor.calculate_area(length, width)
        density = SamplePropertiesProcessor.calculate_density(length, width, thickness, weight)
        return {
            "length": length,
            "width": width,
            "thickness": thickness,
            "weight": weight,
            "area": area,
            "density": density,
        }

    @staticmethod
    def calculate_area(
        length: Union[float, "UnitRegistry.Quantity"],
        width: Union[float, "UnitRegistry.Quantity"],
        area_unit: str = "mm^2",
    ) -> "UnitRegistry.Quantity":
        area = length * width
        if isinstance(area, float):
            area = ureg.Quantity(area, area_unit)  # Assign a default unit if the result is float
        return area.to(area_unit)

    @staticmethod
    def calculate_density(
        length: Union[float, "UnitRegistry.Quantity"],
        width: Union[float, "UnitRegistry.Quantity"],
        thickness: Union[float, "UnitRegistry.Quantity"],
        weight: Union[float, "UnitRegistry.Quantity"],
        density_unit: str = "g/cm^3",
    ) -> "UnitRegistry.Quantity":
        area = SamplePropertiesProcessor.calculate_area(length, width)
        volume = area * thickness
        density = weight / volume if volume else ureg.Quantity(0, density_unit)
        return density.to(density_unit)

    @staticmethod
    def convert_to_quantity(value: str, unit: str) -> "UnitRegistry.Quantity":
        try:
            quantity = ureg(value)
            return quantity.to(unit)
        except Exception:
            try:
                return ureg.Quantity(float(value), unit)
            except ValueError:
                return ureg.Quantity(0, unit)
