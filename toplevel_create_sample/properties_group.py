import tkinter as tk
from tkinter import ttk

from pint import UnitRegistry
from settings_toplevel_create_sample import ureg


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
        name = self._update_sample_name()
        length, width, thickness = self._update_dimensions()
        area = self._calculate_and_display_area(length=length, width=width)
        weight = self._attempt_to_convert_to_quantity(self.entries[4].get(), self.entries[4].unit)
        density = self._calculate_and_display_density(
            length=length, width=width, thickness=thickness, area=area, weight=weight
        )

        self._formatted_entry_values = {
            "name": name,
            "length": length,
            "width": width,
            "thickness": thickness,
            "weight": weight,
            "area": area,
            "density": density,
        }

    def _update_sample_name(self):
        name = self.entries[0].get().strip().replace(" ", "_")
        self.name_label.config(text=f"Sample Name:\n{name}")
        return name

    def _update_dimensions(self):
        length = self._attempt_to_convert_to_quantity(self.entries[1].get(), self.entries[1].unit)
        width = self._attempt_to_convert_to_quantity(self.entries[2].get(), self.entries[2].unit)
        thickness = self._attempt_to_convert_to_quantity(self.entries[3].get(), self.entries[3].unit)

        color = "red" if any(dim.to("m").magnitude > 1 for dim in [length, width, thickness]) else "black"
        self.dimensions_label.config(
            text=f"Dimensions (mm): {length.magnitude} x {width.magnitude} x {thickness.magnitude}",
            foreground=color,
        )
        return length, width, thickness

    def _calculate_and_display_area(self, length=None, width=None):
        if not length or not width:
            length, width = self._update_dimensions()[:2]
        area = length * width
        if area.magnitude:
            area = area.to("mm^2")
            self.area_label.config(text=f"Area: {area.magnitude:.2f} mm^2")
        else:
            self.area_label.config(text="Area: 0 mm^2")
        return area

    def _calculate_and_display_density(self, length=None, width=None, thickness=None, area=None, weight=None):
        if not area or not thickness:
            length, width, thickness = self._update_dimensions()
            area = self._calculate_and_display_area(length, width)
        weight = self._attempt_to_convert_to_quantity(self.entries[4].get(), self.entries[4].unit)
        density = weight / (area * thickness) if area.magnitude and thickness.magnitude else 0
        if isinstance(density, UnitRegistry.Quantity) and density.magnitude:
            density = density.to("g/cm^3")
            color = "red" if density.magnitude > 10 else "black"
            self.density_label.config(text=f"Density: {density.magnitude:.3f} g/cm^3", foreground=color)
        else:
            self.density_label.config(text="Density: 0 g/cm^3")

    def _attempt_to_convert_to_quantity(self, value: str, default_unit: str) -> UnitRegistry.Quantity:
        """Attempts to convert the value to a quantity with the given unit."""
        if isinstance(default_unit, str):
            default_unit = default_unit.strip().lower()
        try:
            quantity = ureg(value)
            return quantity.to(default_unit)
        except Exception:
            try:
                return ureg.Quantity(float(value), default_unit)
            except ValueError:
                return ureg.Quantity(0, default_unit)

    @property
    def formatted_entry_values(self) -> dict:
        return self._formatted_entry_values

    def reset(self) -> None:
        self.name_label.config(text="Sample Name:'\nPreview")
        self.dimensions_label.config(text="Dimensions: 0 x 0 x 0")
        self.area_label.config(text="Area: 0 mm^2")
        self.density_label.config(text="Density: 0 g/cm^3")
        self._formatted_entry_values = {}
