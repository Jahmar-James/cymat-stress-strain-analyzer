import inspect
import threading
import tkinter as tk
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

import customtkinter as ctk
import pandas as pd
from PIL import Image

from standard_base.data_extraction import MechanicalTestDataPreprocessor

from ..layout_helpers.column_grid_manager import ColumnGridManager
from ..notifications.classes_customtkinter import CustomTkinterToast, CustomTkinterTooltip

# GEAR_ICON_PATH = r"C:\Users\JahmarJames\OneDrive - Cymat Corporation\Documents\Python Scripts\Engineering_concepts\Stress__Strain_GUI_V2\toplevel_create_sample\Gear-icon.png"
# GEAR_ICON_PATH = r"/workspaces/cymat-stress-strain-analyzer/toplevel_create_sample/Gear-icon.png"
GEAR_ICON_PATH = r"O:\Documents\Python_Projects\Stress_Strain_App\decouple\cymat-stress-strain-analyzer\templates\Gear-icon.png"
# GEAR_ICON_PATH = r"C:\Users\JahmarJames\OneDrive - Cymat Corporation\Documents\Python Scripts\Engineering_concepts\SS_Decople\templates\Gear-icon.png"


class FileImportFrame(ttk.Frame, ABC):
    def __init__(
        self,
        parent: tk.Widget,
        data_label: str = "Select Data File",
        valid_file_flag=None,
        filename: Optional[tk.StringVar] = None,
        supported_types: list[tuple[str, str]] = [("All Files", "*.*")],
        do_validation: bool = False,
        do_normalization: bool = True,
        do_cleanup: bool = True,
        multiple_files: bool = False,
        show_notification: bool = True,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.data_label_text = data_label
        self.valid_file_bool = valid_file_flag or tk.BooleanVar(
            value=False
        )  # Flag to indicate if a file has been selected used for validation when submitting sample
        self._file_label = filename or tk.StringVar(value="No file selected")
        self._file_path = []
        self.data = None
        self._supported_types = supported_types
        self._do_validation = do_validation  # tying check and format checks
        self._do_normalization = do_normalization  # normalizing the data into a consistent format
        self._do_cleanup = do_cleanup  # removing any unnecessary data if applicable
        self._multiple_files = multiple_files
        self.grid_manager = ColumnGridManager(self)
        self.show_notification = show_notification

    @property
    def info(self) -> dict[str, any]:
        return {
            "data_label": self.data_label_text,
            "valid_file_bool": self.valid_file_bool,
            "file_label": self._file_label,
            "file_path": self._file_path,
            "data": self.data,
        }

    def create_widgets(self) -> None:
        """Create the widgets for the frame.

        The widgets include:
        label indicating which data type file to import - Top,
        button to open file dialog to select file - Middle,
        label to display the selected file name - Bottom (file_label),
        """
        self.grid_rowconfigure((0, 2), weight=1, uniform="a", minsize=30)  # labels
        self.grid_rowconfigure(1, weight=1, uniform="a", minsize=40)  # button
        self.grid_columnconfigure(0, weight=1, uniform="a")

        self.data_label = ctk.CTkLabel(self, text=self.data_label_text, font=("Helvetica", 10, "bold"))
        self.data_label.grid(row=0, column=0, sticky="ew")

        self.select_file_button = ttk.Button(self, text="Select File", command=self._select_files)
        self.select_file_button.grid(row=1, column=0, sticky="nsew")
        self.select_file_button.bind("<Return>", lambda event: self.select_file_button.invoke())
        self.select_file_button.bind("<space>", lambda event: self.select_file_button.invoke())

        self.file_label = ttk.Label(self, textvariable=self._file_label)
        self.file_label.grid(row=2, column=0)

    def _do_pre_submission_data_checks_and_transformations(self, file_paths: list[str]):
        """Preprocessing Perform data checks (of column names) and transformations (unit conversion) before submission validation."""
        self.valid_file_bool.set(False)
        data_collection = []
        for path in file_paths:
            path_obj = Path(path)

            data = self._process_file_to_data(path_obj)

            # tying check and format checks
            if self._do_validation:
                if self._validate_file(data):
                    pass
                else:
                    print(f"Validation failed for file: {path_obj.name}")
                    CustomTkinterToast(
                        self,
                        title="Validation Error",
                        message=f"Validation failed for file: {path_obj.name}",
                        duration=2000,
                        position=("right", "bottom"),
                        alert=True,
                    ).show_toast()
                    return

            # normalizing the data into a consistent format
            if self._do_normalization:
                data = self._normalize_data_from_file(data)
                if data is None:
                    print(f"Normalization failed for file: {path_obj.name}")
                    CustomTkinterToast(
                        self,
                        title="Normalization Error",
                        message=f"Normalization failed for file: {path_obj.name}",
                        duration=2000,
                        position=("right", "bottom"),
                        alert=True,
                    ).show_toast()
                    return

            # removing any unnecessary data if applicable
            if self._do_cleanup:
                data = self._cleanup_data(data)  # TODO add the file name to the cleanup method
                if data is None:
                    print(f"Cleanup failed for file: {path_obj.name}")
                    CustomTkinterToast(
                        self,
                        title="Cleanup Error",
                        message=f"Cleanup failed for file: {path_obj.name}",
                        duration=2000,
                        position=("right", "bottom"),
                        alert=True,
                    ).show_toast()
                    return

            data_collection.append(data)

        self.data = data_collection if self._multiple_files else data_collection[0]
        self.select_file_button.config(text="File selected", state="normal")
        self.valid_file_bool.set(True)

    def _select_files(self):
        file_paths = (
            filedialog.askopenfilenames(filetypes=self._supported_types)
            if self._multiple_files
            else [filedialog.askopenfilename(filetypes=self._supported_types)]
        )
        if not file_paths or not file_paths[0]:
            self._file_label.set("No file selected")
            self.valid_file_bool.set(False)
            return
        self._manage_ui_for_selection(file_paths)

        thread = threading.Thread(target=self._do_pre_submission_data_checks_and_transformations, args=(file_paths,))
        thread.start()
        # self._do_pre_submission_data_checks_and_transformations(file_paths)
        # print(self.info)

    def _manage_ui_for_selection(self, file_paths):
        self.select_file_button.config(state="disabled", text="Processing...")
        path_objs = [Path(path) for path in file_paths]
        self._file_label.set(", ".join([path.name for path in path_objs]))
        self._file_path.extend(path_objs)

    @abstractmethod
    def _process_file_to_data(self, file_path: Path) -> any:
        """Process the selected file."""
        pass

    @abstractmethod
    def _validate_file(self, data: any) -> bool:
        """Validate the file data."""
        pass

    @abstractmethod
    def _normalize_data_from_file(self, data: any) -> any:
        """Normalize the data after processing."""
        pass

    @abstractmethod
    def _cleanup_data(self, data: any) -> any:
        """Cleanup the data after processing."""
        pass

    def _reset(self):
        """Reset the frame to its initial state."""
        self.valid_file_bool.set(False)
        self.select_file_button.config(state="normal")
        self._file_label.set("No file selected")
        self._file_path = []
        self.data = None


class CompressionDataImportFrame(FileImportFrame):
    def __init__(
        self,
        parent,
        data_label: str = "Select General Data File",
        valid_file_flag=None,
        filename=None,
        supported_types=[("Supported types", "*.dat *.xls *.xlsx *.csv")],
        *args,
        **kwargs,
    ):
        super().__init__(
            parent,
            data_label,
            valid_file_flag,
            filename,
            supported_types,
            *args,
            do_validation=True,
            do_normalization=True,
            do_cleanup=False,
            **kwargs,
        )
        self.data = None
        self._processing_methods: dict[str, Callable[[Path], any]] = {}

        # Map file extensions to processing methods
        self._register_processing_methods([".csv"], self._process_csv)
        self._register_processing_methods([".xls", ".xlsx"], self._process_excel)
        self._register_processing_methods([".dat", ".txt"], self._process_file)

    def _register_processing_methods(self, extensions: list[str], method: Callable[[Path], any]):
        for ext in extensions:
            self._processing_methods[ext] = method

    def create_widgets(self) -> None:
        super().create_widgets()

        # Create a frame to encaplsate the select file button and the advanced options button
        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.grid(row=1, column=0, sticky="nsew")
        self.buttons_frame.grid_rowconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(0, weight=5)  # Left most column for the select file button
        self.buttons_frame.grid_columnconfigure(1, weight=1)  # Right most column for the advanced options icon button

        # override the select file button
        self.select_file_button.grid_forget()
        self.select_file_button = ttk.Button(self.buttons_frame, text=self.data_label_text, command=self._select_files)
        self.select_file_button.grid(row=1, column=0, sticky="nsew")
        self.select_file_button.bind("<Return>", lambda event: self.select_file_button.invoke())
        self.select_file_button.bind("<space>", lambda event: self.select_file_button.invoke())
        if self.show_notification:
            select_file_button_tooltip = CustomTkinterTooltip(
                self.select_file_button, text="Opens a window to select a file for general data", delay=500
            )  # TODO  Refine the tooltip text

        # Add advanced options button with gear icon
        image = ctk.CTkImage(light_image=Image.open(GEAR_ICON_PATH))
        self.gear_icon_label = ctk.CTkLabel(self.buttons_frame, image=image, text="")
        self.gear_icon_label.grid(row=1, column=2)
        self.gear_icon_label.bind("<Button-1>", self.open_advanced_options)  # Bind the click event to the CTkLabel
        if self.show_notification:
            gear_icon_tooltip = CustomTkinterTooltip(
                self.gear_icon_label, text="Open advanced options for the selected file", delay=800
            )

    def open_advanced_options(self, event=None) -> None:
        print("Opening advanced options...")
        from data_advanced_options import AdvancedDataOptions

        self.advanced_window = AdvancedDataOptions(self)

    def _process_file_to_data(self, file_path: Path) -> any:
        processing_method = self.get_processing_method(file_path)
        if processing_method:
            return processing_method(file_path)
        else:
            raise ValueError("Unsupported file type")

    def get_processing_method(self, file_path: Path) -> Optional[Callable]:
        """Get the appropriate processing method based on the file extension."""
        return self._processing_methods.get(file_path.suffix)

    def _process_file(self, file_path):
        def read_raw_data(file_path):
            with open(file_path, "r") as file:
                return file.readlines()

        if file_path:
            # Display file name above the 'Import Data' button
            raw_data = read_raw_data(file_path)
            return raw_data, None

    # TODO add a advanced option when selecting an excel file to select the sheet
    def _process_excel(self, file_path):
        data = pd.read_excel(file_path)
        return data

    def _process_csv(self, file_path):
        import csv

        # Open the file in text mode
        with open(file_path, "r") as file:
            content = file.read()
            # Use Sniffer to check if there is a header
            has_header = csv.Sniffer().has_header(content)
            # Use Sniffer to deduce the dialect (format) of the CSV
            dialect = csv.Sniffer().sniff(content)

        # Read the CSV file using the deduced dialect and header info
        data = pd.read_csv(file_path, dialect=dialect, header=0 if has_header else None)
        return data

    def _validate_file(self, data) -> bool:
        return isinstance(data, (pd.DataFrame, list))

    def _normalize_data_from_file(self, data) -> any:
        preprocessor = MechanicalTestDataPreprocessor()
        data = preprocessor.preprocess_data(data)
        return data

    def _cleanup_data(self, data) -> any:
        # No cleanup needed for general data, no drop colums or clean up needed
        return data


class ImageImportFrame(FileImportFrame):
    def __init__(
        self,
        parent,
        data_label: str = "Select Image Files",
        valid_file_flag=None,
        filename=None,
        supported_types=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")],
        *args,
        **kwargs,
    ):
        super().__init__(
            parent,
            data_label,
            valid_file_flag,
            filename,
            supported_types,
            do_validation=True,
            do_normalization=False,
            do_cleanup=False,
            multiple_files=True,
            *args,
            **kwargs,
        )
        self.images: list[Image.Image] = []

    def create_widgets(self) -> None:
        super().create_widgets()
        if self.show_notification:
            select_file_button_tooltip = CustomTkinterTooltip(
                self.select_file_button, text="Opens a window to select image files", delay=500
            )  # TODO  Refine the tooltip text

    def _process_file_to_data(self, file_path: Path) -> Image.Image:
        return Image.open(file_path)

    def _validate_file(self, data: Image.Image, *args, **kwargs) -> bool:
        """Validate the file by checking if it is an instance of PIL Image."""
        return isinstance(data, Image.Image)

    def _normalize_data_from_file(self, data: Image.Image, *args, **kwargs) -> Image.Image:
        raise NotImplementedError(
            "For ImageImportFrame, the DO_NORMALIZE flag should be set to False. This method should not be called."
        )

    def _cleanup_data(self, data: Image.Image, *args, **kwargs) -> Image.Image:
        raise NotImplementedError(
            "For ImageImportFrame, the DO_CLEANUP flag should be set to False. This method should not be called."
        )


class BatchSpecimenImportFrame(FileImportFrame):
    def __init__(
        self,
        parent,
        data_label="Select Excel File",
        valid_file_flag=None,
        filename=None,
        callback=None,
        show_notification=True,
        *args,
        **kwargs,
    ):
        supported_types = [("Excel Files", "*.xls *.xlsx")]
        super().__init__(
            parent,
            data_label,
            valid_file_flag,
            filename,
            supported_types,
            do_validation=False,
            do_normalization=False,
            do_cleanup=False,
            multiple_files=False,
            *args,
            **kwargs,
        )
        self.update_entries_callback = callback
        self.data_generator = None
        self.current_row = None
        self.remaining_rows = 0
        self.excel_sheet_name = None
        self.show_notification = show_notification
        self.data_validator = MechanicalTestDataPreprocessor()

    def create_widgets(self) -> None:
        """Create widgets specific to selecting an Excel file for specimen batch creation."""
        super().create_widgets()
        self.grid_rowconfigure(
            (0, 1, 2, 3), weight=1, uniform="a", minsize=30
        )  # Add an additional row for the skip button

        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.grid(row=1, column=0, sticky="nsew")
        self.buttons_frame.grid_rowconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="a")

        # override the select file button
        self.select_file_button.grid_forget()
        self.select_file_button = ttk.Button(self.buttons_frame, text=self.data_label_text, command=self._select_files)
        self.select_file_button.config(text="Select Excel File")
        self.select_file_button.grid(row=1, column=0, columnspan=5, sticky="nsew")
        self.select_file_button.bind("<Return>", lambda event: self.select_file_button.invoke())
        self.select_file_button.bind("<space>", lambda event: self.select_file_button.invoke())
        if self.show_notification:
            select_file_button_tooltip = CustomTkinterTooltip(
                self.select_file_button, text="Opens a window to select a file for general data", delay=500
            )  # TODO  Refine the tooltip text

        # Add advanced options button with gear icon
        image = ctk.CTkImage(light_image=Image.open(GEAR_ICON_PATH))
        self.gear_icon_label = ctk.CTkLabel(self.buttons_frame, image=image, text="")
        self.gear_icon_label.grid(row=1, column=5)
        self.gear_icon_label.bind("<Button-1>", self.open_advanced_options)  # Bind the click event to the CTkLabel
        if self.show_notification:
            gear_icon_tooltip = CustomTkinterTooltip(
                self.gear_icon_label, text="Open advanced options for the selected file", delay=800
            )

        self.skip_clear_btns_frame = ttk.Frame(self)  # Side by side buttons in additional 4th row
        self.skip_clear_btns_frame.grid(row=3, column=0, sticky="nsew")
        self.skip_clear_btns_frame.grid_rowconfigure(0, weight=1)
        self.skip_clear_btns_frame.grid_columnconfigure((0, 1), weight=1, uniform="a")

        self.skip_button = ttk.Button(self.skip_clear_btns_frame, text="Skip Row", command=self.process_next_row)
        self.skip_button.grid(row=3, column=0, sticky="nsew", padx=5)
        self.skip_button.config(state="disabled")

        self.clear_button = ttk.Button(self.skip_clear_btns_frame, text="Clear", command=self.reset)
        self.clear_button.grid(row=3, column=1, sticky="nsew", padx=5)

    def open_advanced_options(self, event=None) -> None:
        self.excel_sheet_name = None
        from settings_toplevel_create_sample import TOP_LEVEL_DEFAULTS

        dialog = ctk.CTkInputDialog(
            fg_color=TOP_LEVEL_DEFAULTS["foreground"],
            title="Advanced Options",
            text="Enter the name of the Excel sheet to read from\nSheet Name:",
        )
        self.excel_sheet_name = dialog.get_input()
        if self.excel_sheet_name and self.show_notification:
            CustomTkinterToast(
                self,
                title="Sheet Name",
                message=f"Sheet name set to: {self.excel_sheet_name}",
                duration=2000,
                position=("right", "bottom"),
                alert=False,
            ).show_toast()

    def _process_file_to_data(self, file_path: Path) -> None:
        self.data_generator = self.read_excel_row_by_row(file_path)
        self.skip_button.config(state="normal")
        threading.Thread(target=self.process_next_row).start()

    def read_excel_row_by_row(self, filepath):
        sheet_name = self.excel_sheet_name or 0
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        self.remaining_rows = len(df)

        error_message = MechanicalTestDataPreprocessor.validate_columns(df)

        if error_message:
            CustomTkinterToast(
                self,
                title="Validation Error",
                message=error_message,
                duration=2000,
                position=("right", "bottom"),
                alert=True,
            ).show_toast()
            return
        columns_mapping = MechanicalTestDataPreprocessor.SPECIMEN_COLUMN_MAPPING
        df = MechanicalTestDataPreprocessor.remap_df_columns(df, columns_mapping)
        summary_toast = CustomTkinterToast(
            self,
            title="File Read",
            message=f"File read successfully. {self.remaining_rows} rows found.",
            duration=2000,
            position=("right", "bottom"),
            alert=False,
        ).show_toast()
        for index, row in df.iterrows():
            yield row

    def process_next_row(self) -> None:
        try:
            self.current_row = next(self.data_generator)
            data = self._handle_row(self.current_row)
            self.update_entries_callback(data)
            self.select_file_button.config(text=f"{self.remaining_rows} Samples remaining")
            self.remaining_rows -= 1
        except StopIteration:
            self.reset()
            # messagebox.showinfo("End of Data", "No more rows to process.")
            no_data_to_process_toast = CustomTkinterToast(
                self,
                title="End of Data",
                message="No more rows to process.",
                duration=2000,
                position=("right", "bottom"),
                alert=False,
            ).show_toast()

    def _handle_row(self, row) -> dict:
        data_chuck = row.to_dict()
        if data_chuck:
            message = (
                f"Processed: {data_chuck}"
                if "specimenname" not in data_chuck
                else f"Processed: {data_chuck}".replace("specimenname", "name")
            )
            current_row_toast = CustomTkinterToast(
                self, title="Row Processed", message=message, duration=2000, position=("right", "bottom"), alert=False
            ).show_toast()
            return data_chuck

    @property
    def is_exhausted(self) -> bool:
        if inspect.isgenerator(self.data_generator):
            return False
        # if the generator is exhausted, rest button to select file and return True
        self.reset()
        return True

    def reset(self) -> None:
        super()._reset()
        self.data_generator = None
        self.current_row = None
        self.skip_button.config(state="disabled")
        self.select_file_button.config(text="Select Excel File", state="normal")
        self.excel_sheet_name = None
        self.remaining_rows = 0

    # Placeholder for future validation methods
    def _validate_file(self, data) -> bool:
        raise NotImplementedError(
            "For BatchSpecimenImportFrame, the DO_VALIDATION flag should be set to False. This method should not be called."
        )

    # No normalization necessary
    def _normalize_data_from_file(self, data) -> any:
        raise NotImplementedError(
            "For BatchSpecimenImportFrame, the DO_NORMALIZE flag should be set to False. This method should not be called."
        )

    # No cleanup necessary
    def _cleanup_data(self, data) -> any:
        raise NotImplementedError(
            "For BatchSpecimenImportFrame, the DO_CLEANUP flag should be set to False. This method should not be called."
        )


if __name__ == "__main__":
    root = tk.Tk()
    root.title("File Import Frame Test")
    style = ttk.Style()
    style.theme_use("clam")

    root.geometry("200x400")

    # root.grid_rowconfigure(list(range(3)), weight=1, uniform="a")
    # root.grid_columnconfigure(0, weight=1, uniform="a")

    # Create a frame to import general data
    general_data_frame = CompressionDataImportFrame(root, show_notification=False)
    general_data_frame.create_widgets()
    general_data_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    # Create a frame to import images
    image_frame = ImageImportFrame(root, show_notification=False)
    image_frame.create_widgets()
    image_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    # Create a frame to import batch specimen data
    callback = lambda data: print(f"Data received: {data}")
    batch_specimen_frame = BatchSpecimenImportFrame(root, callback=callback, show_notification=False)
    batch_specimen_frame.create_widgets()
    batch_specimen_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    root.mainloop()
    root.mainloop()
