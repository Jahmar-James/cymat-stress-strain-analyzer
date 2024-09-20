import tkinter as tk
from functools import cached_property
from tkinter import ttk
from typing import Callable, Optional

import customtkinter as ctk

from standards.sample_factory import MechanicalTestStandards
from tkinter_frontend.core.widget_manager import PlaceholderEntry, PlaceholderEntryWithUnit

from ..layout_helpers.column_grid_manager import ColumnGridManager
from ..notifications.classes_customtkinter import CustomTkinterToast, CustomTkinterTooltip
from .file_import_frames import BatchSpecimenImportFrame, CompressionDataImportFrame, ImageImportFrame
from .properties_group import PropertiesGroup
from .settings_toplevel_create_sample import *
from .toplevel_validator import ToplevelValidator

# from standard_validator import MechanicalTestStandards


class CreateSampleWindow(ctk.CTkToplevel):
    def __init__(
        self,
        parent: Optional[tk.Tk] = None,
        submission_callback: Optional[Callable] = None,
        geometry=None,
        supported_data_file_types: list[tuple[str, str]] = [],
        supported_image_file_types: list[tuple[str, str]] = [],
    ) -> None:
        super().__init__(
            parent,
        )
        self.title("Create Sample Window")
        self.configure(fg_color=TOP_LEVEL_DEFAULTS["foreground"])
        print(f"Top level defaults: {TOP_LEVEL_DEFAULTS} the assigned value is: {self.cget('fg_color')}")
        self.deiconify()
        self.recalculate_toggle_var = tk.BooleanVar(
            value=True
        )  # When True, will recalclate stress and strain data using force, displacement, area and cross section length (thicknkess)
        self.visualize_specimen_toggle_var = tk.BooleanVar(
            value=False
        )  # When True, will skip dims and weight and pass idenitfer for plot. Still Require name and data with atleast stress and strian
        self.close_on_submission_toggle_var = tk.BooleanVar(value=False)

        # File importer
        self.general_data_is_vaild = tk.BooleanVar(value=False)  # Linked variable to general data file import widget
        self.hysteresis_data_is_vaild = tk.BooleanVar(
            value=False
        )  # Linked variable to hysteresi data file import widget
        self.image_data_is_vaild = tk.BooleanVar(value=False)  # Linked variable to image data file import widget
        self.batch_data_is_vaild = tk.BooleanVar(value=False)  # Linked variable to batch data file import widget

        self.always_on_top_toggle_var = tk.BooleanVar(value=False)
        self.always_on_top_toggle_var.trace_add("write", self.always_on_top_toggle)

        self.disable_auto_validation_toggle_var = tk.BooleanVar(
            value=False
        )  # When True, will overide the import file widget preprocess and validation methods
        self.filepaths: list[tuple[str, list]] = []
        self.callback = submission_callback

        self.SUPPORTED_DATA_FILE_TYPES = (
            supported_data_file_types
            if supported_data_file_types
            else [("Supported types", "*.dat *.xls *.xlsx *.csv"), ("All files", "*.*")]
        )
        self.SUPPORTED_IMAGE_FILE_TYPES = (
            supported_image_file_types if supported_image_file_types else [("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )

        self.validator = ToplevelValidator(self)
        if geometry is not None:
            self.geometry(geometry)
        else:
            self.geometry(f"{TOP_LEVEL_DEFAULTS['Size'].width}x{TOP_LEVEL_DEFAULTS['Size'].height}")

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the widgets for the window

        The left column will be a group on entry widgets inside a frame.
        The middle column will file imports and live updates of the sample properties inside a frame.
        The right column will have toggle buttons to recalculate stress and strain, a dropdown (combobox)
        to select the calculation standards, and a button to submit the sample for calculation and to the main window.
        """
        self.grid_rowconfigure(list(range(4)), weight=1, uniform="a")
        self.grid_columnconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="nsew")

        # Configure rows and columns
        grid: tuple = (1, 3)
        rows, cols = grid
        if isinstance(rows, int):
            self.main_frame.grid_rowconfigure(list(range(rows)), weight=1, uniform="a")
        if isinstance(cols, int):
            self.main_frame.grid_columnconfigure(list(range(cols)), weight=1, uniform="a")

        col_min_size = 200

        # Left Column
        labels_texts = [
            ("Specimen Name:", ""),
            ("Length:", "mm"),
            ("Width:", "mm"),
            ("Thickness:", "mm"),
            ("Weight:", "grams"),
        ]
        left_frame = LeftFrame_EntryGroup(
            self.main_frame,
            entries_data=labels_texts,
            show_labels=True,
            minsize_col=col_min_size,
        )
        left_frame.grid(
            row=0,
            column=0,
            padx=10,
        )
        left_frame.create_widgets()
        self._map_entries(labels_texts, left_frame.entries)
        self.left_frame = left_frame

        # Middle Column
        # Reminder - Left Frame Entries are used in the properties group to calculate the properties of the sample.
        # Must be created before the properties group inside the middle frame.
        middle_frame = MiddleFrame_FileGroup(self.main_frame, toplevel_window=self, minsize_col=col_min_size)
        middle_frame.grid(
            row=0,
            column=1,
            padx=10,
        )
        middle_frame.create_widgets()
        self.middle_frame = middle_frame

        # Right Column
        right_frame = RightFrame_CalculationGroup(self.main_frame, toplevel_window=self, minsize_col=col_min_size)
        right_frame.grid(
            row=0,
            column=2,
            padx=10,
        )
        right_frame.create_widgets()
        self.right_frame = right_frame

        # Comment Box
        comment_box_frame = CommentBoxGroup(self)
        comment_box_frame.grid(row=3, column=0, rowspan=1, sticky="nsew")
        comment_box_frame.create_widgets()
        self.comment_box_frame = comment_box_frame

    def always_on_top_toggle(self, *args) -> None:
        self.attributes("-topmost", self.always_on_top_toggle_var.get())

    @cached_property
    def entries(self) -> list:
        return self.left_frame.entries

    @property
    def entries_values(self) -> list:
        return [entry.get() for entry in self.entries]

    @property
    def standard(self) -> str:
        return self.middle_frame.standards_combobox.get()

    @property
    def sample_properties(self) -> dict:
        return self.middle_frame.properties_frame.formatted_entry_values

    @property
    def comment(self) -> str:
        return self.comment_box_frame.comment

    @property
    def general_data(self) -> dict:
        return self.middle_frame.general_data_frame.info

    @property
    def hysteresis_data(self) -> dict:
        return self.middle_frame.hysteresis_data_frame.info

    @property
    def image_data(self) -> dict:
        return self.right_frame.image_import_frame.info

    @property
    def batch_data(self) -> dict:
        return self.right_frame.batch_specimen_import_frame.info

    def _map_entries(self, labels_texts, entries):
        """Establish a mapping from data keys to entry widgets based on dynamic input."""
        self.data_key_to_entry_widget = {}
        for (label, _), entry in zip(labels_texts, entries):
            key = self._extract_key_from_label(label)  # Method to parse the key from the label
            self.data_key_to_entry_widget[key] = entry
            setattr(self, f"{key}_entry", entry)  # Dynamically create attributes for each entry

    def _extract_key_from_label(self, label):
        """Extract a simple key from the label text for mapping purposes."""
        # Remove non-alphanumeric characters and convert to lower case
        return "".join(filter(str.isalnum, label)).lower()

    def update_entries(self, data: dict):
        """Update entry widgets based on data from a processed Excel row."""
        for key, entry_widget in self.data_key_to_entry_widget.items():
            if key in data:
                entry_widget.set(data[key])  # Set data if available
            else:
                entry_widget.set("")  # Clear entry if data is missing

    def reset_window(self):
        self.left_frame.clear_entries()
        self.middle_frame.general_data_frame._reset()
        self.middle_frame.hysteresis_data_frame._reset()
        self.middle_frame.properties_frame.reset()
        self.comment_box_frame.comment_box.delete("0.0", "end")
        self.close_on_submission_toggle_var.set(False)
        print("Window entries cleared.")


class LeftFrame_EntryGroup(ttk.Frame):
    def __init__(
        self,
        parent=None,
        entries_data=None,
        show_labels=False,
        minsize_col=None,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.entries_data = entries_data or []
        self.entries = []
        self.labels = []
        self.show_labels: bool = show_labels
        self.grid_rowconfigure(0, weight=1, uniform="a")
        self.grid_columnconfigure(0, weight=1, uniform="a", minsize=minsize_col)

    def create_widgets(self) -> None:
        self.entries_frame = ttk.Frame(self)
        self.entries_frame.grid(row=0, column=0, sticky="nsew")
        rows = tuple(range(len(self.entries_data) * 2)) if self.show_labels else tuple(range(len(self.entries_data)))
        self.entries_frame.grid_rowconfigure(rows, weight=1, uniform="a", minsize=30)
        self.entries_frame.grid_columnconfigure(0, weight=1, uniform="a")
        next_row = self._create_entries(self.entries_frame)

    def _create_entries(self, frame=None) -> int:
        master = self.entries_frame if frame is None else frame
        for i, (label_text, unit) in enumerate(self.entries_data):
            if self.show_labels:
                label = ttk.Label(master, text=label_text)
                self.labels.append(label)
                label.grid(row=i * 2, column=0, padx=15, pady=4, sticky="w")

            if unit:
                entry = PlaceholderEntryWithUnit(master, placeholder=label_text, unit=unit)
            else:
                entry = PlaceholderEntry(master, placeholder=label_text)
            self.entries.append(entry)
            entry_row = i * 2 + 1 if self.show_labels else i
            entry.grid(row=entry_row, column=0, padx=15, pady=4, sticky="nsew") if self.show_labels else entry.grid(
                row=entry_row, column=0, padx=15, pady=8, sticky="nsew"
            )
        return entry_row + 1  # The next row to be used for the next widget

    def clear_entries(self) -> None:
        for entry in self.entries:
            entry.delete(0, "end")
            entry.on_focusout(None)


class MiddleFrame_FileGroup(ttk.Frame):
    def __init__(
        self,
        parent,
        toplevel_window: "CreateSampleWindow",
        rows: tuple = (1, 2),
        minsize_col=None,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.grid_columnconfigure(0, weight=1, uniform="a", minsize=minsize_col)
        self.minsize_col = minsize_col
        self.grid_manager = ColumnGridManager(self)
        self.toplevel_window = toplevel_window
        self.general_data_is_vaild = toplevel_window.general_data_is_vaild
        self.hysteresis_data_is_valid = toplevel_window.hysteresis_data_is_vaild
        self.supported_data_file_types = toplevel_window.SUPPORTED_DATA_FILE_TYPES
        self.stanadrds = [standard.value for standard in MechanicalTestStandards]

    def create_widgets(self) -> None:
        self.general_data_frame = CompressionDataImportFrame(
            self,
            data_label="Select General Data File",
            valid_file_flag=self.general_data_is_vaild,
            supported_types=self.supported_data_file_types,
        )
        self.general_data_frame.create_widgets()

        self.hysteresis_data_frame = CompressionDataImportFrame(
            self,
            data_label="Select Hysteresis Data File",
            valid_file_flag=self.hysteresis_data_is_valid,
            supported_types=self.supported_data_file_types,
        )
        self.hysteresis_data_frame.create_widgets()

        self.properties_frame = PropertiesGroup(self, self.toplevel_window.entries)
        self.properties_frame.create_widgets()

        self.standards_combobox = ttk.Combobox(self, values=self.stanadrds, state="readonly")
        self.standards_combobox.current(1)  # The second item corresponds MechanicalTestStandards.CYMAT

        self.submit_button = ttk.Button(
            self,
            text="Submit Sample",
            command=self.toplevel_window.validator.validate_all,
        )

        # The order will be the sqeuence on which the widgets are added to the gridmanager
        self.grid_manager.add_widget(widget=self.properties_frame, rowspan=3, sticky="ew")
        self.grid_manager.add_widget(
            widget=self.general_data_frame,
            rowspan=2,
        )
        self.grid_manager.add_widget(
            widget=self.hysteresis_data_frame,
            rowspan=2,
        )
        self.grid_manager.add_widget(widget=self.standards_combobox, sticky="ew")
        self.grid_manager.add_widget(widget=self.submit_button, sticky="ew")
        self.grid_manager.apply_layout(col_minsize=self.minsize_col, row_minsize=40)


class RightFrame_CalculationGroup(ttk.Frame):
    def __init__(
        self,
        parent,
        toplevel_window: "CreateSampleWindow",
        minsize_col=None,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.toplevel_window = toplevel_window
        self.recalculate_SS_toggle_var = toplevel_window.recalculate_toggle_var
        self.visualize_specimen_toggle_var = toplevel_window.visualize_specimen_toggle_var
        self.close_on_submission_toggle_var = toplevel_window.close_on_submission_toggle_var
        self.grid_manager = ColumnGridManager(self)

    def create_widgets(self) -> None:
        self.close_on_submission_button = ttk.Checkbutton(
            self,
            text="Close on Submission",
            variable=self.close_on_submission_toggle_var,
            onvalue=True,
            offvalue=False,
        )
        on_close_tooltip = CustomTkinterTooltip(
            self.close_on_submission_button,
            text="When True the window will close on a successful submission",
            delay=500,
        )

        self.visualize_specimen_button = ttk.Checkbutton(
            self,
            text="Visualize Specimen",
            variable=self.visualize_specimen_toggle_var,
            onvalue=True,
            offvalue=False,
        )
        on_visualize_tooltip = CustomTkinterTooltip(
            self.visualize_specimen_button,
            text="When True there is no validation, used to compare given x and y data against samples",
            delay=500,
        )

        self.recalculate_button = ttk.Checkbutton(
            self,
            text="Recalculate Stress/Strain",
            variable=self.recalculate_SS_toggle_var,
            onvalue=True,
            offvalue=False,
        )
        on_recalculate_tooltip = CustomTkinterTooltip(
            self.recalculate_button,
            text="When True the stress and strain values will be recalculated\nEven if provided",
            delay=500,
        )

        self.always_on_top_button = ttk.Checkbutton(
            self,
            text="Always on Top",
            variable=self.toplevel_window.always_on_top_toggle_var,
            onvalue=True,
            offvalue=False,
        )

        self.disable_auto_validation_button = ttk.Checkbutton(
            self,
            text="Disable Auto Validation",
            variable=self.toplevel_window.disable_auto_validation_toggle_var,
            onvalue=True,
            offvalue=False,
        )

        self.close_button = ttk.Button(self, text="Close", command=self.toplevel_window.destroy)

        self.image_import_frame = ImageImportFrame(
            self,
            data_label="Select Images",
            supported_types=self.toplevel_window.SUPPORTED_IMAGE_FILE_TYPES,
            valid_file_flag=self.toplevel_window.image_data_is_vaild,
        )
        self.image_import_frame.create_widgets()

        self.batch_specimen_import_frame = BatchSpecimenImportFrame(
            self,
            callback=self.toplevel_window.update_entries,
            valid_file_flag=self.toplevel_window.batch_data_is_vaild,
        )
        self.batch_specimen_import_frame.create_widgets()

        self.clear_button = ttk.Button(self, text="Clear Entries", command=self.toplevel_window.reset_window)

        # Order of the widgets to be added to the grid manager
        self.grid_manager.add_widget(widget=self.close_on_submission_button, sticky="w")
        self.grid_manager.add_widget(widget=self.visualize_specimen_button, sticky="w")
        self.grid_manager.add_widget(widget=self.recalculate_button, sticky="w")
        self.grid_manager.add_widget(widget=self.always_on_top_button, sticky="w")
        self.grid_manager.add_widget(widget=self.disable_auto_validation_button, sticky="w")
        self.grid_manager.add_widget(
            widget=self.image_import_frame,
            rowspan=2,
        )
        self.grid_manager.add_widget(widget=self.batch_specimen_import_frame, rowspan=2, pady=10)
        self.grid_manager.add_widget(widget=self.clear_button, sticky=None)
        self.grid_manager.add_widget(widget=self.close_button, sticky=None)

        self.grid_manager.apply_layout(col_minsize=200, row_minsize=30)


class CommentBoxGroup(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.grid_rowconfigure(0, weight=1, uniform="a", minsize=10)
        self.grid_rowconfigure((1, 2, 3, 4), weight=2, uniform="a")
        self.grid_columnconfigure(0, weight=1)

    def create_widgets(self) -> None:
        self.comment_label = ctk.CTkLabel(self, text="Comments:", font=("Helvetica", 10, "bold"))
        self.comment_label.grid(row=0, column=0, sticky="nw", padx=10)

        self.comment_box = ctk.CTkTextbox(
            self,
            wrap="word",
            font=("Helvetica", 9),
            height=60,
        )
        self.comment_box.grid(row=1, column=0, rowspan=4, sticky="nsew", padx=10, pady=10)

    @property
    def comment(self) -> str:
        return self.comment_box.get("0.0", "end")  # get text from line 0, char 0 to end

    @comment.setter
    def comment(self, value):
        self.comment_box.delete("0.0", "end")
        self.comment_box.insert("0.0", value)
        self.comment_box.insert("0.0", value)
        self.comment_box.insert("0.0", value)
        self.comment_box.insert("0.0", value)
